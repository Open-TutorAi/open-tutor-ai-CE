<script>
  import { onMount } from "svelte";
  import { get } from "svelte/store";
  import BlocklyEditor from "$lib/components/blockly/BlocklyEditor.svelte";

  // ─── Niveaux de progression ──────────────────────────────────────────────
  const LEVELS = ["débutant", "intermédiaire", "avancé"];

  const THEMES_BY_LEVEL = {
    "débutant":      ["affichage", "variables", "opérations mathématiques"],
    "intermédiaire": ["boucles", "conditions", "listes"],
    "avancé":        ["fonctions", "algorithmes", "récursivité"],
  };

  const OBJECTIVES_BY_LEVEL = {
    "débutant":      "créer un programme simple avec des variables et des opérations de base",
    "intermédiaire": "utiliser des boucles et des conditions pour résoudre un problème",
    "avancé":        "implémenter un algorithme complet avec des fonctions",
  };

  // Nombre d'exercices réussis consécutivement avant de passer au niveau suivant
  const PASS_THRESHOLD = 2;
  // Score minimum pour considérer un exercice "réussi"
  const PASS_SCORE = 70;

  // ─── État global ─────────────────────────────────────────────────────────
  let phase = "loading"; // loading | exercise | success | levelUp | finished | error

  let currentLevelIndex = 0;           // 0=débutant 1=intermédiaire 2=avancé
  let consecutiveSuccesses = 0;        // réussites consécutives au niveau courant
  let totalExercisesDone = 0;
  let lastScore = 0;
  let errorMessage = "";
  let streamedText = "";
  let generationProgress = 0;

  // L'exercice courant généré par l'IA
  let exercise = null;         // { title, description, difficulty, allowed_blocks, test_cases, hints }
  let assignmentId = null;     // ID retourné après génération

  // Historique de progression pour afficher le parcours
  let progressHistory = [];    // [{ level, title, score, passed }]

  $: currentLevel = LEVELS[currentLevelIndex];
  $: isLastLevel = currentLevelIndex === LEVELS.length - 1;
  $: progressPct = Math.round(
    ((currentLevelIndex * PASS_THRESHOLD + Math.min(consecutiveSuccesses, PASS_THRESHOLD)) /
    (LEVELS.length * PASS_THRESHOLD)) * 100
  );

  // ─── Démarrage automatique ───────────────────────────────────────────────
  onMount(async () => {
    // Essayer de récupérer le niveau sauvegardé (localStorage)
    const saved = localStorage.getItem("blockly_student_progress");
    if (saved) {
      try {
        const data = JSON.parse(saved);
        currentLevelIndex   = data.levelIndex   ?? 0;
        consecutiveSuccesses = data.successes    ?? 0;
        progressHistory     = data.history       ?? [];
        totalExercisesDone  = data.total         ?? 0;
      } catch {
        // Ignorer si corrompu
      }
    }
    await generateExercise();
  });

  // ─── Sauvegarder la progression ──────────────────────────────────────────
  function saveProgress() {
    localStorage.setItem("blockly_student_progress", JSON.stringify({
      levelIndex: currentLevelIndex,
      successes:  consecutiveSuccesses,
      history:    progressHistory,
      total:      totalExercisesDone,
    }));
  }

  // ─── Générer un exercice pour le niveau courant ──────────────────────────
  async function generateExercise() {
    phase         = "loading";
    streamedText  = "";
    exercise      = null;
    assignmentId  = null;
    errorMessage  = "";
    generationProgress = 0;

    const themes   = THEMES_BY_LEVEL[currentLevel];
    const theme    = themes[Math.floor(Math.random() * themes.length)];
    const objective = OBJECTIVES_BY_LEVEL[currentLevel];

    try {
      const res = await fetch("/api/blockly/generate/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({
          theme,
          level:          currentLevel,
          objective,
          num_test_cases: currentLevel === "avancé" ? 4 : 3,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erreur serveur ${res.status}`);
      }

      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer   = "";
      let fullJson = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          let event;
          try { event = JSON.parse(line.slice(6)); } catch { continue; }

          if (event.type === "chunk") {
            fullJson += event.content;
            streamedText = fullJson;
            generationProgress = Math.min(95, Math.round((fullJson.length / 800) * 100));
          }  else if (event.type === "done") {
                assignmentId = event.assignment_id ?? crypto.randomUUID();
            try { exercise = JSON.parse(fullJson); } catch { exercise = null; }
            generationProgress = 100;
            phase = "exercise";
          } else if (event.type === "error") {
            throw new Error(event.message);
          }
        }
      }

      // Fallback si le serveur ne renvoie pas d'event "done"
      if (phase === "loading" && fullJson) {
        try { exercise = JSON.parse(fullJson); } catch { exercise = null; }
        phase = exercise ? "exercise" : "error";
        errorMessage = exercise ? "" : "L'IA n'a pas pu générer un exercice valide.";
      }

    } catch (e) {
      errorMessage = e.message;
      phase = "error";
    }
  }

  // ─── Callback quand l'élève soumet son code ───────────────────────────────
  // BlocklyEditor appelle onSubmit({ score, passed }) quand il reçoit le résultat
  function handleSubmit(event) {
    const { score } = event.detail ?? event;
    lastScore = score ?? 0;
    totalExercisesDone += 1;

    const passed = lastScore >= PASS_SCORE;

    // Enregistrer dans l'historique
    progressHistory = [...progressHistory, {
      level:  currentLevel,
      title:  exercise?.title ?? "Exercice",
      score:  lastScore,
      passed,
    }];

    if (passed) {
      consecutiveSuccesses += 1;
    } else {
      // Un échec réinitialise le compteur de réussites consécutives
      consecutiveSuccesses = 0;
    }

    saveProgress();

    // Vérifier si l'élève passe au niveau suivant
    if (consecutiveSuccesses >= PASS_THRESHOLD) {
      consecutiveSuccesses = 0;
      if (isLastLevel) {
        phase = "finished";
      } else {
        phase = "levelUp";
      }
    } else {
      phase = "success";
    }
  }

  // ─── Continuer après l'affichage du résultat ─────────────────────────────
  async function continueAfterSuccess() {
    await generateExercise();
  }

  async function continueAfterLevelUp() {
    currentLevelIndex += 1;
    saveProgress();
    await generateExercise();
  }

  function resetProgress() {
    currentLevelIndex    = 0;
    consecutiveSuccesses = 0;
    totalExercisesDone   = 0;
    lastScore            = 0;
    progressHistory      = [];
    localStorage.removeItem("blockly_student_progress");
    generateExercise();
  }

  // ─── Auth helper ─────────────────────────────────────────────────────────
  function authHeaders() {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // ─── Couleurs par niveau ──────────────────────────────────────────────────
  const levelColors = {
    "débutant":      { bg: "#e8f5e9", text: "#2e7d32", border: "#a5d6a7", accent: "#4caf50" },
    "intermédiaire": { bg: "#fff3e0", text: "#e65100", border: "#ffcc80", accent: "#ff9800" },
    "avancé":        { bg: "#fce4ec", text: "#880e4f", border: "#f48fb1", accent: "#e91e63" },
  };

  const levelIcons = { "débutant": "🌱", "intermédiaire": "🔥", "avancé": "⚡" };
  const levelLabels = { "débutant": "Débutant", "intermédiaire": "Intermédiaire", "avancé": "Avancé" };
</script>

<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

  * { box-sizing: border-box; }

  .page {
    font-family: 'DM Sans', sans-serif;
    background: #f7f5f0;
    min-height: 100vh;
    padding: 0;
    color: #1a1a1a;
  }

  /* ── Header barre de progression ── */
  .progress-header {
    background: #fff;
    border-bottom: 1px solid #e8e5de;
    padding: 14px 32px;
    display: flex;
    align-items: center;
    gap: 20px;
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .level-steps {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .level-step {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .step-dot {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    border: 2px solid #e0ddd6;
    background: #f7f5f0;
    color: #bbb;
    font-weight: 600;
    transition: all 0.3s;
  }
  .step-dot.done   { background: #1a1a1a; border-color: #1a1a1a; color: #c8f07a; }
  .step-dot.active { background: #fff; border-color: #1a1a1a; color: #1a1a1a; box-shadow: 0 0 0 3px rgba(26,26,26,0.1); }

  .step-label {
    font-size: 12px;
    color: #aaa;
    font-weight: 500;
  }
  .step-label.active { color: #1a1a1a; }
  .step-label.done   { color: #666; }

  .step-arrow { color: #ddd; font-size: 12px; }

  .header-right {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .mini-progress {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .mini-bar {
    width: 100px;
    height: 6px;
    background: #e8e5de;
    border-radius: 99px;
    overflow: hidden;
  }
  .mini-bar-fill {
    height: 100%;
    background: #1a1a1a;
    border-radius: 99px;
    transition: width 0.5s ease;
  }
  .mini-pct { font-size: 12px; color: #888; font-weight: 500; }

  .successes-pips {
    display: flex;
    gap: 4px;
    align-items: center;
  }
  .pip {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    border: 1.5px solid #ccc;
    background: #f0f0f0;
    transition: all 0.2s;
  }
  .pip.filled { background: #4caf50; border-color: #4caf50; }

  /* ── Contenu principal ── */
  .main {
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 24px;
  }

  /* ── Écran de chargement ── */
  .loading-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 100px 40px;
    gap: 28px;
    text-align: center;
  }

  .ai-orb {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: conic-gradient(#c8f07a, #1a1a1a, #c8f07a);
    animation: spin 2s linear infinite;
    position: relative;
  }
  .ai-orb::after {
    content: "";
    position: absolute;
    inset: 6px;
    background: #f7f5f0;
    border-radius: 50%;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .loading-title {
    font-family: 'DM Serif Display', serif;
    font-size: 26px;
    font-style: italic;
  }
  .loading-sub { font-size: 14px; color: #888; max-width: 300px; line-height: 1.7; }

  .gen-bar-wrap {
    width: 260px;
    height: 4px;
    background: #e0ddd6;
    border-radius: 99px;
    overflow: hidden;
  }
  .gen-bar-fill {
    height: 100%;
    background: #1a1a1a;
    border-radius: 99px;
    transition: width 0.4s ease;
  }

  /* ── Exercice ── */
  .exercise-section {
    display: flex;
    flex-direction: column;
    gap: 20px;
    animation: fadeUp 0.5s ease;
  }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .ex-header {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .level-badge {
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    border: 1.5px solid;
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .ex-num {
    font-size: 13px;
    color: #aaa;
    margin-left: auto;
  }

  .ex-card {
    background: #fff;
    border: 1px solid #e8e5de;
    border-radius: 16px;
    overflow: hidden;
  }
  .ex-card-top {
    padding: 28px 32px 22px;
    border-bottom: 1px solid #f0ede6;
  }
  .ex-title {
    font-family: 'DM Serif Display', serif;
    font-size: 24px;
    margin-bottom: 10px;
    letter-spacing: -0.3px;
  }
  .ex-desc { font-size: 15px; color: #444; line-height: 1.75; }

  .ex-card-body {
    padding: 24px 32px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .section-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #aaa;
    margin-bottom: 10px;
  }

  .blocks-wrap { display: flex; flex-wrap: wrap; gap: 6px; }
  .block-chip {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    background: #f7f5f0;
    border: 1px solid #e8e5de;
    border-radius: 6px;
    padding: 4px 10px;
    color: #555;
  }

  .tests { display: flex; flex-direction: column; gap: 8px; }
  .test-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    background: #f7f5f0;
    border-radius: 10px;
    padding: 12px 16px;
  }
  .test-num { font-family: 'DM Mono', monospace; font-size: 11px; color: #bbb; padding-top: 2px; }
  .test-body { display: flex; flex-direction: column; gap: 4px; }
  .test-desc { font-size: 13px; color: #666; }
  .test-output {
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    background: #1a1a1a;
    color: #c8f07a;
    padding: 3px 10px;
    border-radius: 5px;
    display: inline-block;
  }

  .hints { display: flex; flex-direction: column; gap: 8px; }
  .hint-row { display: flex; align-items: flex-start; gap: 10px; }
  .hint-dot {
    width: 22px; height: 22px;
    border-radius: 50%;
    background: #f0ede6;
    border: 1.5px solid #e0ddd6;
    font-family: 'DM Mono', monospace;
    font-size: 11px; color: #999;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 2px;
  }
  .hint-text { font-size: 14px; color: #555; line-height: 1.6; }

  /* Blockly editor placeholder */
  .editor-placeholder {
    background: #fff;
    border: 1px solid #e8e5de;
    border-radius: 16px;
    padding: 32px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    align-items: center;
    justify-content: center;
    min-height: 300px;
    color: #999;
    font-size: 14px;
  }

  /* ── Écran résultat (succès / échec) ── */
  .result-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 24px;
    padding: 60px 40px;
    text-align: center;
    animation: fadeUp 0.4s ease;
  }

  .result-icon { font-size: 64px; }

  .result-title {
    font-family: 'DM Serif Display', serif;
    font-size: 30px;
    font-style: italic;
  }
  .result-sub { font-size: 16px; color: #666; max-width: 380px; line-height: 1.7; }

  .score-ring {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    border: 6px solid #e8e5de;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
  }
  .score-ring.passed { border-color: #4caf50; }
  .score-ring.failed { border-color: #ef5350; }
  .score-num { font-family: 'DM Mono', monospace; font-size: 26px; font-weight: 600; }
  .score-label { font-size: 10px; color: #aaa; margin-top: 2px; }

  .btn-continue {
    padding: 14px 32px;
    background: #1a1a1a;
    color: #c8f07a;
    border: none;
    border-radius: 10px;
    font-family: 'DM Sans', sans-serif;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s, transform 0.1s;
  }
  .btn-continue:hover { background: #333; transform: translateY(-1px); }
  .btn-continue:active { transform: translateY(0); }

  /* ── Level Up ── */
  .levelup-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 28px;
    padding: 60px 40px;
    text-align: center;
    animation: fadeUp 0.5s ease;
  }

  .levelup-badge {
    padding: 10px 24px;
    border-radius: 99px;
    font-size: 15px;
    font-weight: 600;
    border: 2px solid;
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .levelup-title {
    font-family: 'DM Serif Display', serif;
    font-size: 36px;
    font-style: italic;
    line-height: 1.2;
  }
  .levelup-sub { font-size: 16px; color: #666; max-width: 380px; line-height: 1.7; }

  .next-level-preview {
    background: #fff;
    border: 1px solid #e8e5de;
    border-radius: 14px;
    padding: 20px 28px;
    display: flex;
    align-items: center;
    gap: 16px;
    max-width: 340px;
    width: 100%;
  }
  .next-icon { font-size: 32px; }
  .next-info { text-align: left; }
  .next-label { font-size: 11px; color: #aaa; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px; }
  .next-name { font-size: 18px; font-weight: 600; color: #1a1a1a; }

  /* ── Fini ── */
  .finished-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 24px;
    padding: 60px 40px;
    text-align: center;
    animation: fadeUp 0.5s ease;
  }

  .trophy { font-size: 80px; }

  .history-list {
    width: 100%;
    max-width: 500px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    text-align: left;
  }
  .history-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: #fff;
    border: 1px solid #e8e5de;
    border-radius: 10px;
    font-size: 13px;
  }
  .history-item .h-icon { font-size: 16px; }
  .history-item .h-level {
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 10px;
    font-weight: 600;
    border: 1px solid;
    flex-shrink: 0;
  }
  .history-item .h-title { flex: 1; color: #444; }
  .history-item .h-score { font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 600; }
  .history-item .h-score.passed { color: #4caf50; }
  .history-item .h-score.failed { color: #ef5350; }

  .btn-restart {
    padding: 12px 28px;
    background: #f7f5f0;
    color: #1a1a1a;
    border: 1.5px solid #e8e5de;
    border-radius: 10px;
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
  }
  .btn-restart:hover { background: #eee; }

  /* ── Erreur ── */
  .error-wrap {
    background: #fff5f5;
    border: 1px solid #fecaca;
    border-radius: 12px;
    padding: 28px 32px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
    margin: 40px auto;
    max-width: 520px;
  }
  .error-title { font-size: 16px; font-weight: 600; color: #991b1b; }
  .error-msg { font-family: 'DM Mono', monospace; font-size: 13px; color: #b91c1c; line-height: 1.6; }
  .btn-retry {
    padding: 10px 20px;
    background: #1a1a1a;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
  }
  .btn-retry:hover { background: #333; }
</style>

<div class="page">

  <!-- ═══════════════════════════════════════════════════════════════════════ -->
  <!-- Header : barre de progression sticky                                   -->
  <!-- ═══════════════════════════════════════════════════════════════════════ -->
  <div class="progress-header">
    <div class="level-steps">
      {#each LEVELS as lvl, i}
        <div class="level-step">
          <div class="step-dot {i < currentLevelIndex ? 'done' : i === currentLevelIndex ? 'active' : ''}">
            {#if i < currentLevelIndex}✓{:else}{levelIcons[lvl]}{/if}
          </div>
          <span class="step-label {i < currentLevelIndex ? 'done' : i === currentLevelIndex ? 'active' : ''}">
            {levelLabels[lvl]}
          </span>
        </div>
        {#if i < LEVELS.length - 1}
          <span class="step-arrow">›</span>
        {/if}
      {/each}
    </div>

    <div class="header-right">
      <!-- Pip indicators pour réussites consécutives -->
      {#if phase === "exercise" || phase === "success"}
        <div class="successes-pips">
          {#each Array(PASS_THRESHOLD) as _, i}
            <div class="pip {i < consecutiveSuccesses ? 'filled' : ''}"></div>
          {/each}
        </div>
      {/if}

      <div class="mini-progress">
        <div class="mini-bar">
          <div class="mini-bar-fill" style="width: {progressPct}%"></div>
        </div>
        <span class="mini-pct">{progressPct}%</span>
      </div>
    </div>
  </div>

  <div class="main">

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- CHARGEMENT : L'IA génère l'exercice                                -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    {#if phase === "loading"}
      <div class="loading-wrap">
        <div class="ai-orb"></div>
        <div class="loading-title">L'IA prépare ton exercice…</div>
        <div class="loading-sub">
          Niveau <strong>{currentLevel}</strong> — adapté à ta progression.
          Quelques secondes suffisent.
        </div>
        <div class="gen-bar-wrap">
          <div class="gen-bar-fill" style="width: {generationProgress}%"></div>
        </div>
      </div>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- EXERCICE : afficher l'exercice + l'éditeur Blockly                 -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    {:else if phase === "exercise" && exercise}
      <div class="exercise-section">

        <!-- En-tête -->
        <div class="ex-header">
          <span
            class="level-badge"
            style="
              background: {levelColors[currentLevel].bg};
              color: {levelColors[currentLevel].text};
              border-color: {levelColors[currentLevel].border};
            "
          >
            {levelIcons[currentLevel]} {levelLabels[currentLevel]}
          </span>
          <span class="ex-num">Exercice #{totalExercisesDone + 1}</span>
        </div>

        <!-- Carte de l'exercice -->
        <div class="ex-card">
          <div class="ex-card-top">
            <div class="ex-title">{exercise.title}</div>
            <div class="ex-desc">{exercise.description}</div>
          </div>

          <div class="ex-card-body">

            {#if exercise.allowed_blocks?.length}
              <div>
                <div class="section-label">Blocs disponibles</div>
                <div class="blocks-wrap">
                  {#each exercise.allowed_blocks as block}
                    <span class="block-chip">{block}</span>
                  {/each}
                </div>
              </div>
            {/if}

            {#if exercise.test_cases?.length}
              <div>
                <div class="section-label">{exercise.test_cases.length} cas de test à réussir</div>
                <div class="tests">
                  {#each exercise.test_cases as tc, i}
                    <div class="test-row">
                      <span class="test-num">#{i + 1}</span>
                      <div class="test-body">
                        {#if tc.description}
                          <span class="test-desc">{tc.description}</span>
                        {/if}
                        <span class="test-output">{tc.expected_output}</span>
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

            {#if exercise.hints?.length}
              <div>
                <div class="section-label">Indices si tu bloques</div>
                <div class="hints">
                  {#each exercise.hints as hint, i}
                    <div class="hint-row">
                      <span class="hint-dot">{i + 1}</span>
                      <span class="hint-text">{hint}</span>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

          </div>
        </div>

        <!-- Éditeur Blockly — passe l'assignmentId et écoute l'événement submit -->
        {#if assignmentId}
          <BlocklyEditor
            assignmentId={assignmentId}
            exerciseTitle={exercise.title}
            description={exercise.description}
            hints={exercise.hints ?? []}
            on:submit={handleSubmit}
          />
        {:else}
          <!--
            Fallback si le backend ne renvoie pas d'assignment_id dans l'event "done" :
            on crée un exercice virtuel côté client pour que l'élève puisse quand même coder.
            Dans ce cas, handleSubmit sera appelé avec le score retourné par BlocklyEditor.
          -->
          <div class="editor-placeholder">
            <span style="font-size:32px">🧩</span>
            <span>Éditeur Blockly en attente de l'ID d'exercice…</span>
          </div>
        {/if}

      </div>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- RÉSULTAT : après soumission, avant le prochain exercice            -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    {:else if phase === "success"}
      <div class="result-screen">
        <div class="result-icon">{lastScore >= PASS_SCORE ? "🎉" : "💪"}</div>

        <div class="score-ring {lastScore >= PASS_SCORE ? 'passed' : 'failed'}">
          <span class="score-num">{lastScore}</span>
          <span class="score-label">/ 100</span>
        </div>

        {#if lastScore >= PASS_SCORE}
          <div class="result-title">Bien joué !</div>
          <div class="result-sub">
            Tu as réussi cet exercice avec {lastScore}/100.
            {#if consecutiveSuccesses < PASS_THRESHOLD}
              Encore {PASS_THRESHOLD - consecutiveSuccesses} réussite{PASS_THRESHOLD - consecutiveSuccesses > 1 ? 's' : ''}
              pour passer au niveau suivant.
            {/if}
          </div>
        {:else}
          <div class="result-title">Continue !</div>
          <div class="result-sub">
            Tu as obtenu {lastScore}/100. Il faut {PASS_SCORE} minimum pour valider.
            Un nouvel exercice t'attend — tu vas y arriver !
          </div>
        {/if}

        <button class="btn-continue" on:click={continueAfterSuccess}>
          Exercice suivant →
        </button>
      </div>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- LEVEL UP : passage au niveau supérieur                             -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    {:else if phase === "levelUp"}
      {@const nextLevel = LEVELS[currentLevelIndex + 1]}
      <div class="levelup-screen">
        <div style="font-size: 72px">🚀</div>

        <span
          class="levelup-badge"
          style="
            background: {levelColors[currentLevel].bg};
            color: {levelColors[currentLevel].text};
            border-color: {levelColors[currentLevel].border};
          "
        >
          {levelIcons[currentLevel]} Niveau {levelLabels[currentLevel]} validé !
        </span>

        <div class="levelup-title">Tu montes de niveau !</div>
        <div class="levelup-sub">
          Félicitations ! Tu as maîtrisé le niveau {currentLevel}.
          Tu passes maintenant au niveau <strong>{nextLevel}</strong>.
        </div>

        <div class="next-level-preview">
          <span class="next-icon">{levelIcons[nextLevel]}</span>
          <div class="next-info">
            <div class="next-label">Prochain niveau</div>
            <div class="next-name">{levelLabels[nextLevel]}</div>
          </div>
        </div>

        <button class="btn-continue" on:click={continueAfterLevelUp}>
          Commencer {levelLabels[nextLevel]} →
        </button>
      </div>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- FINISHED : tous les niveaux complétés                              -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    {:else if phase === "finished"}
      <div class="finished-screen">
        <div class="trophy">🏆</div>
        <div class="result-title" style="font-size:34px">
          Félicitations, tu as tout maîtrisé !
        </div>
        <div class="result-sub">
          Tu as complété les 3 niveaux ({totalExercisesDone} exercices au total).
          Tu es prêt pour des défis encore plus grands !
        </div>

        {#if progressHistory.length > 0}
          <div class="history-list">
            {#each progressHistory as item}
              <div class="history-item">
                <span class="h-icon">{item.passed ? "✅" : "❌"}</span>
                <span
                  class="h-level"
                  style="
                    background: {levelColors[item.level]?.bg ?? '#f5f5f5'};
                    color: {levelColors[item.level]?.text ?? '#333'};
                    border-color: {levelColors[item.level]?.border ?? '#ddd'};
                  "
                >
                  {levelIcons[item.level]} {item.level}
                </span>
                <span class="h-title">{item.title}</span>
                <span class="h-score {item.passed ? 'passed' : 'failed'}">{item.score}/100</span>
              </div>
            {/each}
          </div>
        {/if}

        <button class="btn-restart" on:click={resetProgress}>
          ↺ Recommencer depuis le début
        </button>
      </div>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- ERREUR                                                              -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    {:else if phase === "error"}
      <div class="error-wrap">
        <div class="error-title">La génération a échoué</div>
        <div class="error-msg">{errorMessage}</div>
        <button class="btn-retry" on:click={generateExercise}>
          ↺ &nbsp;Réessayer
        </button>
      </div>
    {/if}

  </div>
</div>