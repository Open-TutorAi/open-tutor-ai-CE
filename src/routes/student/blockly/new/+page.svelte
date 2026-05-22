<script>
  import { onMount } from "svelte";
  import BlocklyEditor from "$lib/components/blockly/BlocklyEditor.svelte";

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

  const PASS_THRESHOLD = 2;
  const PASS_SCORE = 70;

  let phase = "loading";
  let currentLevelIndex = 0;
  let consecutiveSuccesses = 0;
  let totalExercisesDone = 0;
  let lastScore = 0;
  let errorMessage = "";
  let streamedText = "";
  let generationProgress = 0;
  let exercise = null;
  let assignmentId = null;
  let progressHistory = [];

  $: currentLevel = LEVELS[currentLevelIndex];
  $: isLastLevel = currentLevelIndex === LEVELS.length - 1;
  $: progressPct = Math.round(
    ((currentLevelIndex * PASS_THRESHOLD + Math.min(consecutiveSuccesses, PASS_THRESHOLD)) /
    (LEVELS.length * PASS_THRESHOLD)) * 100
  );

  onMount(async () => {
    const saved = localStorage.getItem("blockly_student_progress");
    if (saved) {
      try {
        const data = JSON.parse(saved);
        currentLevelIndex    = data.levelIndex  ?? 0;
        consecutiveSuccesses = data.successes   ?? 0;
        progressHistory      = data.history     ?? [];
        totalExercisesDone   = data.total       ?? 0;
      } catch {}
    }
    await generateExercise();
  });

  function saveProgress() {
    localStorage.setItem("blockly_student_progress", JSON.stringify({
      levelIndex: currentLevelIndex,
      successes:  consecutiveSuccesses,
      history:    progressHistory,
      total:      totalExercisesDone,
    }));
  }

  async function generateExercise() {
    phase = "loading"; streamedText = ""; exercise = null;
    assignmentId = null; errorMessage = ""; generationProgress = 0;

    const themes = THEMES_BY_LEVEL[currentLevel];
    const theme  = themes[Math.floor(Math.random() * themes.length)];
    const objective = OBJECTIVES_BY_LEVEL[currentLevel];

    try {
      const res = await fetch("/api/blockly/generate/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({
          theme, level: currentLevel, objective,
          num_test_cases: currentLevel === "avancé" ? 4 : 3,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erreur serveur ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = ""; let fullJson = "";

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
          } else if (event.type === "done") {
            assignmentId = event.assignment_id ?? crypto.randomUUID();
            try { exercise = JSON.parse(fullJson); } catch { exercise = null; }
            generationProgress = 100;
            phase = "exercise";
          } else if (event.type === "error") {
            throw new Error(event.message);
          }
        }
      }

      if (phase === "loading" && fullJson) {
        try { exercise = JSON.parse(fullJson); } catch { exercise = null; }
        phase = exercise ? "exercise" : "error";
        errorMessage = exercise ? "" : "L'IA n'a pas pu générer un exercice valide.";
      }
    } catch (e) {
      errorMessage = e.message; phase = "error";
    }
  }

  function handleSubmit(event) {
    const { score } = event.detail ?? event;
    lastScore = score ?? 0;
    totalExercisesDone += 1;
    const passed = lastScore >= PASS_SCORE;

    progressHistory = [...progressHistory, {
      level: currentLevel, title: exercise?.title ?? "Exercice",
      score: lastScore, passed,
    }];

    if (passed) { consecutiveSuccesses += 1; }
    else        { consecutiveSuccesses = 0; }

    saveProgress();

    if (consecutiveSuccesses >= PASS_THRESHOLD) {
      consecutiveSuccesses = 0;
      phase = isLastLevel ? "finished" : "levelUp";
    } else {
      phase = "success";
    }
  }

  async function continueAfterSuccess()  { await generateExercise(); }
  async function continueAfterLevelUp()  { currentLevelIndex += 1; saveProgress(); await generateExercise(); }

  function resetProgress() {
    currentLevelIndex = 0; consecutiveSuccesses = 0;
    totalExercisesDone = 0; lastScore = 0; progressHistory = [];
    localStorage.removeItem("blockly_student_progress");
    generateExercise();
  }

  function authHeaders() {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  const LEVEL_CFG = {
    "débutant":      { icon:"🌱", label:"Débutant",      color:"#10B981", bg:"#ECFDF5", border:"#6EE7B7" },
    "intermédiaire": { icon:"🔥", label:"Intermédiaire", color:"#F59E0B", bg:"#FFFBEB", border:"#FDE68A" },
    "avancé":        { icon:"⚡", label:"Avancé",        color:"#EF4444", bg:"#FEF2F2", border:"#FECACA" },
  };
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --white:  #FFFFFF;
  --bg:     #F0F4FF;
  --border: #E0E7FF;
  --bd2:    #C7D2FE;
  --ink:    #0F172A;
  --ink2:   #1E293B;
  --ink3:   #475569;
  --ink4:   #94A3B8;
  --indigo: #4F46E5;
  --violet: #7C3AED;
  --green:  #10B981;
  --amber:  #F59E0B;
  --red:    #EF4444;
  --ff: 'Nunito', sans-serif;
  --fm: 'JetBrains Mono', monospace;
  --r: 14px;
}

:global(body) { margin:0; padding:0; background:var(--bg); font-family:var(--ff); color:var(--ink); }

/* ── PAGE ── */
.page { display:flex; flex-direction:column; min-height:100vh; }

/* ── TOPBAR ── */
.topbar {
  height: 54px;
  background: var(--white); border-bottom: 2px solid var(--border);
  display: flex; align-items: center; padding: 0 24px; gap: 16px;
  position: sticky; top: 0; z-index: 20;
  box-shadow: 0 2px 8px rgba(15,23,42,.05);
  flex-shrink: 0;
}

.tb-brand { display:flex; align-items:center; gap:9px; flex-shrink:0; }
.tb-logo {
  width:34px; height:34px; border-radius:10px;
  background:linear-gradient(135deg,var(--indigo),var(--violet));
  display:flex; align-items:center; justify-content:center;
  font-size:.95rem; box-shadow:0 3px 10px rgba(79,70,229,.3);
}
.tb-name { font-size:1rem; font-weight:900; color:var(--indigo); letter-spacing:-.02em; }
.tb-tag {
  font-size:.6rem; font-weight:900; text-transform:uppercase; letter-spacing:.05em;
  background:linear-gradient(135deg,var(--indigo),#EC4899); color:#fff;
  padding:2px 9px; border-radius:20px;
}

/* Level steps */
.tb-levels { display:flex; align-items:center; gap:6px; flex:1; justify-content:center; }
.lv-step { display:flex; align-items:center; gap:5px; }
.lv-dot {
  width:30px; height:30px; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  font-size:.8rem; font-weight:700; border:2px solid var(--border);
  background:var(--bg); color:var(--ink4); transition:all .25s;
}
.lv-dot.done   { background:var(--indigo); border-color:var(--indigo); color:#fff; }
.lv-dot.active { background:var(--white); border-color:var(--indigo); color:var(--indigo); box-shadow:0 0 0 3px rgba(79,70,229,.15); }
.lv-name { font-size:.74rem; font-weight:700; color:var(--ink4); transition:color .2s; }
.lv-name.active { color:var(--indigo); }
.lv-name.done   { color:var(--ink3); }
.lv-arrow { color:var(--border); font-size:.8rem; }

.tb-right { display:flex; align-items:center; gap:10px; flex-shrink:0; }

/* Progress mini */
.prog-mini { display:flex; align-items:center; gap:7px; }
.pm-bar { width:80px; height:6px; background:var(--border); border-radius:20px; overflow:hidden; }
.pm-fill { height:100%; background:linear-gradient(90deg,var(--indigo),#EC4899); border-radius:20px; transition:width .6s ease; }
.pm-pct { font-size:.7rem; font-weight:800; color:var(--ink3); }

/* Pips */
.pips { display:flex; gap:5px; align-items:center; }
.pip { width:10px; height:10px; border-radius:50%; border:2px solid var(--border); background:var(--bg); transition:all .2s; }
.pip.on { background:var(--green); border-color:var(--green); }

/* ── MAIN CONTENT ── */
.main { flex:1; display:flex; flex-direction:column; }

/* ─────────────────────────────────
   LOADING
───────────────────────────────── */
.loading-screen {
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  flex:1; gap:24px; padding:60px 20px; text-align:center;
}
.ai-orb {
  width:72px; height:72px; border-radius:50%; position:relative;
  background:conic-gradient(var(--indigo),var(--violet),#EC4899,var(--indigo));
  animation:orb-spin 2s linear infinite;
  box-shadow:0 0 32px rgba(79,70,229,.3);
}
.ai-orb::after {
  content:""; position:absolute; inset:6px;
  background:var(--bg); border-radius:50%;
}
@keyframes orb-spin { to{transform:rotate(360deg)} }
.loading-title { font-size:1.4rem; font-weight:900; color:var(--ink); }
.loading-sub { font-size:.85rem; color:var(--ink3); max-width:300px; line-height:1.7; }
.gen-track { width:240px; height:5px; background:var(--border); border-radius:20px; overflow:hidden; }
.gen-fill { height:100%; background:linear-gradient(90deg,var(--indigo),#EC4899); border-radius:20px; transition:width .4s ease; }

/* ─────────────────────────────────
   EXERCISE PHASE — full height layout
───────────────────────────────── */
.exercise-phase {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: fade-up .4s ease both;
}
@keyframes fade-up { from{opacity:0;transform:translateY(12px)} }

/* Sub-header: niveau badge + exercice num */
.ex-subheader {
  display:flex; align-items:center; gap:10px;
  padding:10px 20px; background:var(--white);
  border-bottom:2px solid var(--border); flex-shrink:0;
}
.lv-badge {
  display:inline-flex; align-items:center; gap:5px;
  padding:4px 13px; border-radius:20px; font-size:.72rem; font-weight:800;
  border:2px solid;
}
.ex-num-txt { font-size:.72rem; color:var(--ink4); font-weight:700; margin-left:auto; }

/* BlocklyEditor takes all remaining space */
.editor-wrap { flex:1; overflow:hidden; display:flex; flex-direction:column; }

/* ─────────────────────────────────
   RESULT SCREEN
───────────────────────────────── */
.result-screen {
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  flex:1; gap:22px; padding:60px 24px; text-align:center;
  animation:fade-up .4s ease both;
}
.res-emoji { font-size:3.5rem; }
.res-ring {
  width:90px; height:90px; border-radius:50%; border:6px solid var(--border);
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  position:relative;
}
.res-ring.pass { border-color:var(--green); }
.res-ring.fail { border-color:var(--red); }
.res-score { font-size:1.7rem; font-weight:900; font-family:var(--fm); }
.res-denom { font-size:.72rem; color:var(--ink4); }
.res-title { font-size:1.4rem; font-weight:900; color:var(--ink); }
.res-sub { font-size:.85rem; color:var(--ink3); max-width:360px; line-height:1.7; }
.btn-continue {
  padding:11px 28px; background:linear-gradient(135deg,var(--indigo),var(--violet));
  border:none; color:#fff; border-radius:var(--r);
  font-family:var(--ff); font-size:.88rem; font-weight:900;
  cursor:pointer; transition:all .15s;
  box-shadow:0 4px 14px rgba(79,70,229,.3);
}
.btn-continue:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(79,70,229,.4); }

/* ─────────────────────────────────
   LEVEL UP
───────────────────────────────── */
.levelup-screen {
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  flex:1; gap:24px; padding:60px 24px; text-align:center;
  animation:fade-up .4s ease both;
}
.lu-rocket { font-size:4rem; animation:rocket-bounce .6s ease-in-out infinite alternate; }
@keyframes rocket-bounce { from{transform:translateY(0)} to{transform:translateY(-12px)} }
.lu-title { font-size:1.8rem; font-weight:900; color:var(--ink); }
.lu-sub { font-size:.88rem; color:var(--ink3); max-width:360px; line-height:1.7; }
.lu-next-card {
  background:var(--white); border:2px solid var(--border); border-radius:var(--r);
  padding:18px 24px; display:flex; align-items:center; gap:14px;
  min-width:280px; box-shadow:0 4px 16px rgba(0,0,0,.06);
}
.lu-next-icon { font-size:2rem; }
.lu-next-info { text-align:left; }
.lu-next-lbl { font-size:.6rem; font-weight:900; text-transform:uppercase; letter-spacing:.08em; color:var(--ink4); margin-bottom:4px; }
.lu-next-name { font-size:1rem; font-weight:900; color:var(--ink); }

/* ─────────────────────────────────
   FINISHED
───────────────────────────────── */
.finished-screen {
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  flex:1; gap:22px; padding:60px 24px; text-align:center;
  animation:fade-up .4s ease both;
}
.trophy { font-size:5rem; animation:trophy-spin 1s ease .2s both; }
@keyframes trophy-spin { from{transform:rotateY(-90deg);opacity:0} to{transform:rotateY(0);opacity:1} }
.fin-title { font-size:1.6rem; font-weight:900; color:var(--ink); }
.fin-sub { font-size:.85rem; color:var(--ink3); max-width:380px; line-height:1.7; }

.history-list { display:flex; flex-direction:column; gap:6px; width:100%; max-width:460px; text-align:left; }
.hist-item {
  display:flex; align-items:center; gap:10px;
  padding:10px 13px; background:var(--white);
  border:2px solid var(--border); border-radius:var(--r);
  font-size:.78rem;
}
.hist-lv-badge { padding:2px 9px; border-radius:20px; font-size:.62rem; font-weight:800; border:2px solid; flex-shrink:0; }
.hist-title { flex:1; color:var(--ink3); }
.hist-score { font-family:var(--fm); font-size:.75rem; font-weight:700; }
.hist-score.pass { color:var(--green); }
.hist-score.fail { color:var(--red); }

.btn-restart {
  padding:10px 24px; background:var(--bg); border:2px solid var(--border);
  color:var(--ink2); border-radius:var(--r); font-family:var(--ff);
  font-size:.84rem; font-weight:700; cursor:pointer; transition:all .15s;
}
.btn-restart:hover { border-color:var(--indigo); color:var(--indigo); background:#EEF2FF; }

/* ─────────────────────────────────
   ERROR
───────────────────────────────── */
.error-card {
  margin:40px auto; max-width:480px;
  background:#FEF2F2; border:2px solid #FECACA; border-radius:var(--r);
  padding:24px 28px; display:flex; flex-direction:column; gap:12px;
}
.err-title { font-size:.92rem; font-weight:900; color:var(--red); }
.err-msg { font-family:var(--fm); font-size:.78rem; color:#B91C1C; line-height:1.65; }
.btn-retry {
  align-self:flex-start; padding:8px 18px; background:var(--red); border:none;
  color:#fff; border-radius:var(--r); font-family:var(--ff); font-size:.8rem;
  font-weight:800; cursor:pointer; transition:all .15s;
}
.btn-retry:hover { background:#DC2626; }
</style>

<div class="page">

  <!-- ══ TOPBAR ══ -->
  <header class="topbar">
    <div class="tb-brand">
      <div class="tb-logo">🧩</div>
      <span class="tb-name">OpenTutorAI</span>
      <span class="tb-tag">Blockly</span>
    </div>

    <!-- Niveau steps -->
    <div class="tb-levels">
      {#each LEVELS as lvl, i}
        <div class="lv-step">
          <div class="lv-dot {i < currentLevelIndex ? 'done' : i === currentLevelIndex ? 'active' : ''}">
            {#if i < currentLevelIndex}✓{:else}{LEVEL_CFG[lvl].icon}{/if}
          </div>
          <span class="lv-name {i < currentLevelIndex ? 'done' : i === currentLevelIndex ? 'active' : ''}">
            {LEVEL_CFG[lvl].label}
          </span>
        </div>
        {#if i < LEVELS.length - 1}<span class="lv-arrow">›</span>{/if}
      {/each}
    </div>

    <div class="tb-right">
      {#if phase === "exercise" || phase === "success"}
        <div class="pips">
          {#each Array(PASS_THRESHOLD) as _, i}
            <div class="pip {i < consecutiveSuccesses ? 'on' : ''}"></div>
          {/each}
        </div>
      {/if}
      <div class="prog-mini">
        <div class="pm-bar"><div class="pm-fill" style="width:{progressPct}%"></div></div>
        <span class="pm-pct">{progressPct}%</span>
      </div>
    </div>
  </header>

  <div class="main">

    <!-- ══ LOADING ══ -->
    {#if phase === "loading"}
      <div class="loading-screen">
        <div class="ai-orb"></div>
        <p class="loading-title">L'IA prépare ton exercice…</p>
        <p class="loading-sub">Niveau <strong>{currentLevel}</strong> — adapté à ta progression.</p>
        <div class="gen-track"><div class="gen-fill" style="width:{generationProgress}%"></div></div>
      </div>

    <!-- ══ EXERCISE ══ -->
    {:else if phase === "exercise" && exercise}
      <div class="exercise-phase">
        <!-- Sub-header -->
        <div class="ex-subheader">
          <span class="lv-badge" style="
            background:{LEVEL_CFG[currentLevel].bg};
            color:{LEVEL_CFG[currentLevel].color};
            border-color:{LEVEL_CFG[currentLevel].border}">
            {LEVEL_CFG[currentLevel].icon} {LEVEL_CFG[currentLevel].label}
          </span>
          <span class="ex-num-txt">Exercice #{totalExercisesDone + 1}</span>
        </div>

        <!-- BlocklyEditor occupe tout l'espace restant -->
        <div class="editor-wrap">
          {#if assignmentId}
            <BlocklyEditor
              assignmentId={assignmentId}
              exerciseTitle={exercise.title}
              description={exercise.description}
              hints={exercise.hints ?? []}
              on:submit={handleSubmit}
            />
          {/if}
        </div>
      </div>

    <!-- ══ RESULT ══ -->
    {:else if phase === "success"}
      <div class="result-screen">
        <div class="res-emoji">{lastScore >= PASS_SCORE ? "🎉" : "💪"}</div>
        <div class="res-ring {lastScore >= PASS_SCORE ? 'pass' : 'fail'}">
          <span class="res-score">{lastScore}</span>
          <span class="res-denom">/100</span>
        </div>
        <h2 class="res-title">{lastScore >= PASS_SCORE ? "Bien joué !" : "Continue !"}</h2>
        <p class="res-sub">
          {#if lastScore >= PASS_SCORE}
            Tu as réussi avec {lastScore}/100.
            {#if consecutiveSuccesses < PASS_THRESHOLD}
              Encore {PASS_THRESHOLD - consecutiveSuccesses} réussite{PASS_THRESHOLD - consecutiveSuccesses > 1 ? 's' : ''} pour passer au niveau suivant.
            {/if}
          {:else}
            Tu as obtenu {lastScore}/100. Il faut {PASS_SCORE} minimum. Un nouvel exercice t'attend !
          {/if}
        </p>
        <button class="btn-continue" on:click={continueAfterSuccess}>Exercice suivant →</button>
      </div>

    <!-- ══ LEVEL UP ══ -->
    {:else if phase === "levelUp"}
      {@const nextLevel = LEVELS[currentLevelIndex + 1]}
      <div class="levelup-screen">
        <div class="lu-rocket">🚀</div>
        <span class="lv-badge" style="
          background:{LEVEL_CFG[currentLevel].bg};
          color:{LEVEL_CFG[currentLevel].color};
          border-color:{LEVEL_CFG[currentLevel].border};
          font-size:.8rem;padding:6px 16px">
          {LEVEL_CFG[currentLevel].icon} Niveau {LEVEL_CFG[currentLevel].label} validé !
        </span>
        <h2 class="lu-title">Tu montes de niveau !</h2>
        <p class="lu-sub">Félicitations ! Tu passes au niveau <strong>{nextLevel}</strong>.</p>
        <div class="lu-next-card">
          <span class="lu-next-icon">{LEVEL_CFG[nextLevel].icon}</span>
          <div class="lu-next-info">
            <div class="lu-next-lbl">Prochain niveau</div>
            <div class="lu-next-name">{LEVEL_CFG[nextLevel].label}</div>
          </div>
        </div>
        <button class="btn-continue" on:click={continueAfterLevelUp}>
          Commencer {LEVEL_CFG[nextLevel].label} →
        </button>
      </div>

    <!-- ══ FINISHED ══ -->
    {:else if phase === "finished"}
      <div class="finished-screen">
        <div class="trophy">🏆</div>
        <h2 class="fin-title">Félicitations, tu as tout maîtrisé !</h2>
        <p class="fin-sub">Tu as complété les 3 niveaux ({totalExercisesDone} exercices). Tu es prêt pour des défis encore plus grands !</p>

        {#if progressHistory.length > 0}
          <div class="history-list">
            {#each progressHistory as item}
              <div class="hist-item">
                <span>{item.passed ? "✅" : "❌"}</span>
                <span class="hist-lv-badge" style="
                  background:{LEVEL_CFG[item.level]?.bg};
                  color:{LEVEL_CFG[item.level]?.color};
                  border-color:{LEVEL_CFG[item.level]?.border}">
                  {LEVEL_CFG[item.level]?.icon} {item.level}
                </span>
                <span class="hist-title">{item.title}</span>
                <span class="hist-score {item.passed ? 'pass' : 'fail'}">{item.score}/100</span>
              </div>
            {/each}
          </div>
        {/if}
        <button class="btn-restart" on:click={resetProgress}>↺ Recommencer depuis le début</button>
      </div>

    <!-- ══ ERROR ══ -->
    {:else if phase === "error"}
      <div class="error-card">
        <div class="err-title">La génération a échoué</div>
        <div class="err-msg">{errorMessage}</div>
        <button class="btn-retry" on:click={generateExercise}>↺ Réessayer</button>
      </div>
    {/if}

  </div>
</div>