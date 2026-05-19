<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import { blocklyStore } from '$lib/stores/blockly';
  import { submitBlocklyCode, testBlocklyCode } from '$lib/api/blockly';

  export let assignmentId;
  export let allowedBlocks = null;
  export let exerciseTitle = 'Exercice Blockly';
  export let description = '';
  export let hints = [];

  const dispatch = createEventDispatcher();

  let blocklyDiv;
  let workspace;
  let Blockly;
  let pythonGenerator;
  let pythonCode = '';
  let isLoading = true;
  let isTesting = false;
  let isSubmitting = false;
  let testResult = null;
  let feedback = '';
  let feedbackStreaming = false;
  let score = null;
  let showHint = false;
  let currentHintIndex = 0;
  let error = null;

  const toolboxConfig = {
    kind: 'categoryToolbox',
    contents: [
      { kind: 'category', name: '🔢 Variables', colour: '#F9A825', custom: 'VARIABLE' },
      {
        kind: 'category', name: '➕ Math', colour: '#1565C0',
        contents: [
          { kind: 'block', type: 'math_number' },
          { kind: 'block', type: 'math_arithmetic' },
          { kind: 'block', type: 'math_modulo' },
          { kind: 'block', type: 'math_round' },
          { kind: 'block', type: 'math_single' },
        ],
      },
      {
        kind: 'category', name: '📝 Texte', colour: '#00897B',
        contents: [
          { kind: 'block', type: 'text' },
          { kind: 'block', type: 'text_print' },
          { kind: 'block', type: 'text_join' },
          { kind: 'block', type: 'text_length' },
        ],
      },
      {
        kind: 'category', name: '⚡ Logique', colour: '#E53935',
        contents: [
          { kind: 'block', type: 'controls_if' },
          { kind: 'block', type: 'logic_compare' },
          { kind: 'block', type: 'logic_operation' },
          { kind: 'block', type: 'logic_negate' },
          { kind: 'block', type: 'logic_boolean' },
        ],
      },
      {
        kind: 'category', name: '🔄 Boucles', colour: '#7B1FA2',
        contents: [
          { kind: 'block', type: 'controls_repeat_ext' },
          { kind: 'block', type: 'controls_whileUntil' },
          { kind: 'block', type: 'controls_for' },
          { kind: 'block', type: 'controls_forEach' },
        ],
      },
      {
        kind: 'category', name: '📋 Listes', colour: '#558B2F',
        contents: [
          { kind: 'block', type: 'lists_create_empty' },
          { kind: 'block', type: 'lists_create_with' },
          { kind: 'block', type: 'lists_length' },
          { kind: 'block', type: 'lists_getIndex' },
          { kind: 'block', type: 'lists_setIndex' },
        ],
      },
      { kind: 'category', name: '🔧 Fonctions', colour: '#FF6F00', custom: 'PROCEDURE' },
    ],
  };

  onMount(async () => {
    try {
      const BlocklyModule = await import('blockly');
      Blockly = BlocklyModule;
      const pythonModule = await import('blockly/python');
      pythonGenerator = pythonModule.pythonGenerator || BlocklyModule.Python;

      await new Promise(r => setTimeout(r, 150));

      workspace = Blockly.inject(blocklyDiv, {
        toolbox: toolboxConfig,
        grid: { spacing: 20, length: 3, colour: '#e8eaf6', snap: true },
        zoom: { controls: true, wheel: true, startScale: 1.0, maxScale: 3, minScale: 0.3 },
        trashcan: true,
        scrollbars: true,
        sounds: false,
        move: { scrollbars: true, drag: true, wheel: true },
      });

      window.dispatchEvent(new Event('resize'));

      const saved = localStorage.getItem(`blockly_workspace_${assignmentId}`);
      if (saved) {
        try {
          const xml = new DOMParser().parseFromString(saved, 'text/xml').documentElement;
          Blockly.Xml.domToWorkspace(xml, workspace);
        } catch (e) {
          localStorage.removeItem(`blockly_workspace_${assignmentId}`);
        }
      }

      workspace.addChangeListener(() => {
        generatePython();
        saveWorkspaceLocally();
      });

      generatePython();
      isLoading = false;

      setTimeout(() => {
        if (workspace && Blockly) Blockly.svgResize(workspace);
      }, 300);

    } catch (err) {
      error = `Erreur chargement Blockly: ${err.message}`;
      isLoading = false;
    }
  });

  onDestroy(() => { if (workspace) workspace.dispose(); });

  function generatePython() {
    if (!workspace) return;
    try {
      pythonCode = pythonGenerator
        ? pythonGenerator.workspaceToCode(workspace)
        : Blockly?.Python?.workspaceToCode(workspace) || '';
      blocklyStore.update(s => ({ ...s, pythonCode, blocksJson: getWorkspaceXml() }));
    } catch (err) {
      pythonCode = `# Erreur: ${err.message}`;
    }
  }

  function getWorkspaceXml() {
    if (!Blockly || !workspace) return null;
    try {
      return Blockly.Xml.domToText(Blockly.Xml.workspaceToDom(workspace));
    } catch (e) { return null; }
  }

  function saveWorkspaceLocally() {
    const xml = getWorkspaceXml();
    if (xml) localStorage.setItem(`blockly_workspace_${assignmentId}`, xml);
  }

  function resetWorkspace() {
    if (!workspace || !confirm('Réinitialiser le workspace ?')) return;
    workspace.clear();
    localStorage.removeItem(`blockly_workspace_${assignmentId}`);
    pythonCode = ''; testResult = null; feedback = ''; score = null;
  }

  async function handleTest() {
    if (!pythonCode.trim()) { testResult = { error: "Ajoutez des blocs d'abord." }; return; }
    isTesting = true; testResult = null;
    try {
      testResult = await testBlocklyCode({
        python_code: pythonCode, assignment_id: assignmentId, blocks_json: getWorkspaceXml(),
      });
    } catch (err) {
      testResult = { error: err.message };
    } finally { isTesting = false; }
  }

  async function handleSubmit() {
    if (!pythonCode.trim()) { alert('Ajoutez des blocs !'); return; }
    if (!confirm('Soumettre pour évaluation ?')) return;

    isSubmitting = true; feedback = ''; score = null; feedbackStreaming = true;

    try {
      const response = await fetch('/api/blockly/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          assignment_id: assignmentId,
          python_code: pythonCode,
          blocks_json: getWorkspaceXml(),
        }),
      });

      if (!response.ok) throw new Error(`Erreur ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of decoder.decode(value).split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'score') score = data.value;
              else if (data.type === 'feedback') feedback += data.content;
            } catch {}
          }
        }
      }

      // ── Émettre le score vers la page parente (progression automatique) ──
      // On attend que feedbackStreaming soit terminé avant de dispatcher
      dispatch('submit', { score: score ?? 0 });

    } catch (err) {
      feedback = `Erreur : ${err.message}`;
      dispatch('submit', { score: 0 });
    } finally {
      isSubmitting = false;
      feedbackStreaming = false;
    }
  }

  function copyPython() { navigator.clipboard.writeText(pythonCode); }
  function nextHint() { if (currentHintIndex < hints.length - 1) currentHintIndex++; }
</script>

<svelte:window on:resize={() => { if (workspace && Blockly) Blockly.svgResize(workspace); }} />

<div class="blockly-page">

  <!-- ── En-tête exercice ───────────────────────────────────────────────── -->
  <div class="exercise-header">
    <div class="exercise-info">
      <h1 class="exercise-title">{exerciseTitle}</h1>
      <p class="exercise-description">{description}</p>
    </div>
    {#if score !== null}
      <div class="score-badge" class:score-great={score >= 80} class:score-ok={score >= 50 && score < 80} class:score-low={score < 50}>
        <span class="score-value">{score}</span>
        <span class="score-label">/100</span>
      </div>
    {/if}
  </div>

  <!-- ── Zone de travail ────────────────────────────────────────────────── -->
  <div class="workspace-container">

    <!-- Panneau Blockly (gauche) -->
    <div class="blockly-panel">
      <div class="panel-header">
        <span class="panel-title">🧩 Éditeur Blockly</span>
        <div class="panel-actions">
          {#if hints.length > 0}
            <button class="hint-btn" on:click={() => (showHint = !showHint)}>
              💡 Indice {currentHintIndex + 1}/{hints.length}
            </button>
          {/if}
          <button class="reset-btn" on:click={resetWorkspace}>🗑️ Réinitialiser</button>
        </div>
      </div>

      {#if showHint && hints.length > 0}
        <div class="hint-box">
          <p>{hints[currentHintIndex]}</p>
          {#if hints.length > 1}
            <button class="hint-next-btn" on:click={nextHint} disabled={currentHintIndex === hints.length - 1}>
              Indice suivant →
            </button>
          {/if}
        </div>
      {/if}

      {#if error}
        <div class="error-box">{error}</div>
      {/if}

      {#if isLoading}
        <div class="loading-overlay">
          <div class="spinner"></div>
          <p>Chargement de l'éditeur…</p>
        </div>
      {/if}

      <div bind:this={blocklyDiv} class="blockly-workspace"></div>
    </div>

    <!-- Panneau sortie (droite) -->
    <div class="output-panel">

      <!-- Code Python -->
      <div class="python-section">
        <div class="panel-header">
          <span class="panel-title">🐍 Code Python généré</span>
          <button class="copy-btn" on:click={copyPython} title="Copier">📋</button>
        </div>
        <pre class="python-code">{pythonCode || '# Glissez des blocs pour générer le code Python…'}</pre>
      </div>

      <!-- Console de test -->
      {#if testResult}
        <div class="console-section">
          <div class="panel-header">
            <span class="panel-title">🖥️ Console</span>
          </div>
          <div class="console-output" class:console-error={testResult.error}>
            {#if testResult.error}
              <span class="error-prefix">❌ Erreur : </span>{testResult.error}
            {:else}
              <span class="success-prefix">✅ Sortie : </span>
              <pre>{testResult.stdout || '(aucune sortie)'}</pre>
              {#if testResult.test_results}
                <div class="test-cases">
                  {#each testResult.test_results as tc}
                    <div class="test-case" class:passed={tc.passed} class:failed={!tc.passed}>
                      {tc.passed ? '✅' : '❌'} Test {tc.index} :
                      {tc.passed ? 'Réussi' : `Échec — attendu : "${tc.expected}", obtenu : "${tc.got}"`}
                    </div>
                  {/each}
                </div>
              {/if}
            {/if}
          </div>
        </div>
      {/if}

      <!-- ── Feedback IA (conservé tel quel, re-habillé Open TutorAI) ── -->
      {#if feedback || feedbackStreaming}
        <div class="feedback-section">
          <div class="panel-header">
            <span class="panel-title">
              <span class="ai-dot"></span>
              Feedback IA
            </span>
            {#if feedbackStreaming}
              <span class="streaming-indicator">⟳ En cours…</span>
            {/if}
          </div>
          <div class="feedback-content">
            {feedback}{#if feedbackStreaming}<span class="cursor-blink">|</span>{/if}
          </div>
        </div>
      {/if}

    </div>
  </div>

  <!-- ── Barre d'actions ────────────────────────────────────────────────── -->
  <div class="action-bar">
    <button
      class="btn btn-test"
      on:click={handleTest}
      disabled={isTesting || isSubmitting || !pythonCode.trim()}
    >
      {isTesting ? '⟳ Test en cours…' : '▶️ Tester'}
    </button>
    <button
      class="btn btn-submit"
      on:click={handleSubmit}
      disabled={isSubmitting || isTesting || !pythonCode.trim()}
    >
      {isSubmitting ? '⟳ Soumission…' : '🚀 Soumettre pour évaluation'}
    </button>
  </div>
</div>

<style>
  /* ── Reset global ── */
  :global(body) { margin: 0; padding: 0; overflow: hidden; }

  /* ── Variables Open TutorAI ── */
  :root {
    --ot-black:   #1a1a1a;
    --ot-lime:    #c8f07a;
    --ot-cream:   #f7f5f0;
    --ot-border:  #e8e5de;
    --ot-muted:   #888;
    --ot-panel:   #f0ede6;
  }

  /* ── Page ── */
  .blockly-page {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--ot-cream);
    font-family: 'DM Sans', 'Segoe UI', sans-serif;
    overflow: hidden;
  }

  /* ── Header ── */
  .exercise-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 24px;
    background: #fff;
    border-bottom: 2px solid var(--ot-border);
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    flex-shrink: 0;
  }

  .exercise-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.15rem;
    font-weight: 400;
    font-style: italic;
    color: var(--ot-black);
    margin: 0 0 2px 0;
    letter-spacing: -0.2px;
  }
  .exercise-description { color: var(--ot-muted); font-size: 0.85rem; margin: 0; }

  /* Score badge */
  .score-badge {
    display: flex;
    align-items: baseline;
    gap: 3px;
    padding: 8px 16px;
    border-radius: 12px;
    border: 2px solid var(--ot-border);
    background: var(--ot-cream);
  }
  .score-badge.score-great { background: #e8f5e9; border-color: #4caf50; }
  .score-badge.score-ok    { background: #fff8e1; border-color: #ff9800; }
  .score-badge.score-low   { background: #fce4ec; border-color: #f44336; }
  .score-value {
    font-family: 'DM Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--ot-black);
  }
  .score-label { font-size: 0.9rem; color: var(--ot-muted); }

  /* ── Layout ── */
  .workspace-container { display: flex; flex: 1; overflow: hidden; }

  /* Panneau Blockly */
  .blockly-panel {
    flex: 0 0 60%;
    display: flex;
    flex-direction: column;
    border-right: 2px solid var(--ot-border);
    background: #fff;
    position: relative;
    overflow: hidden;
  }

  /* Panneau sortie */
  .output-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    background: var(--ot-cream);
  }

  /* Panel header — thème unifié */
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    background: var(--ot-panel);
    border-bottom: 1px solid var(--ot-border);
    flex-shrink: 0;
  }
  .panel-title {
    font-weight: 600;
    color: var(--ot-black);
    font-size: 0.88rem;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  /* Workspace Blockly */
  .blockly-workspace {
    position: absolute;
    top: 40px;
    left: 0; right: 0; bottom: 0;
  }

  /* ── Code Python ── */
  .python-section { border-bottom: 1px solid var(--ot-border); flex-shrink: 0; }
  .python-code {
    background: #1a1a1a;         /* noir Open TutorAI */
    color: var(--ot-lime);       /* vert citron Open TutorAI */
    font-family: 'DM Mono', 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.83rem;
    padding: 16px;
    margin: 0;
    min-height: 130px;
    max-height: 190px;
    overflow: auto;
    line-height: 1.65;
  }

  /* ── Console ── */
  .console-section, .feedback-section { border-bottom: 1px solid var(--ot-border); }
  .console-output {
    padding: 12px 16px;
    font-family: 'DM Mono', monospace;
    font-size: 0.84rem;
    background: #1a1a1a;
    color: #eceff1;
    min-height: 80px;
  }
  .console-output.console-error { color: #ef9a9a; }
  .error-prefix  { color: #ef5350; font-weight: 700; }
  .success-prefix { color: var(--ot-lime); font-weight: 700; }
  .test-cases { margin-top: 8px; }
  .test-case { padding: 3px 0; font-size: 0.81rem; }
  .test-case.passed { color: #a5d6a7; }
  .test-case.failed { color: #ef9a9a; }

  /* ── Feedback IA — thème Open TutorAI ── */
  .feedback-section { background: #fff; }

  /* Petit point animé "IA active" */
  .ai-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--ot-lime);
    border: 1.5px solid var(--ot-black);
    flex-shrink: 0;
  }

  .feedback-content {
    padding: 16px 20px;
    font-size: 0.92rem;
    line-height: 1.75;
    color: #37474f;
    background: #fff;
    min-height: 80px;
    white-space: pre-wrap;
  }

  .cursor-blink {
    color: var(--ot-black);
    animation: blink 0.8s infinite;
    font-weight: 700;
  }
  @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

  .streaming-indicator {
    font-size: 0.74rem;
    color: var(--ot-muted);
    animation: pulse 1.2s infinite;
  }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

  /* ── Barre d'actions ── */
  .action-bar {
    display: flex;
    gap: 12px;
    padding: 10px 24px;
    background: #fff;
    border-top: 2px solid var(--ot-border);
    flex-shrink: 0;
    align-items: center;
  }

  .btn {
    padding: 9px 22px;
    border: none;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s, transform 0.1s, box-shadow 0.1s;
  }
  .btn:disabled { opacity: 0.45; cursor: not-allowed; }

  /* Tester — contour sobre */
  .btn-test {
    background: var(--ot-cream);
    color: var(--ot-black);
    border: 1.5px solid var(--ot-black);
  }
  .btn-test:hover:not(:disabled) {
    background: var(--ot-black);
    color: var(--ot-lime);
  }

  /* Soumettre — noir + lime, signature Open TutorAI */
  .btn-submit {
    background: var(--ot-black);
    color: var(--ot-lime);
    flex: 1;
    max-width: 300px;
  }
  .btn-submit:hover:not(:disabled) {
    background: #333;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(26,26,26,0.2);
  }
  .btn-submit:active:not(:disabled) { transform: translateY(0); }

  /* ── Indices ── */
  .hint-box {
    background: #fffbeb;
    border-left: 3px solid #f59e0b;
    padding: 10px 16px;
    font-size: 0.88rem;
    color: #78350f;
    flex-shrink: 0;
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }
  .hint-box p { margin: 0; flex: 1; line-height: 1.6; }
  .hint-next-btn {
    background: none;
    border: 1px solid #d97706;
    color: #b45309;
    padding: 3px 10px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.78rem;
    white-space: nowrap;
    flex-shrink: 0;
    margin-top: 2px;
  }

  /* Boutons de panneau */
  .hint-btn {
    background: #fffbeb;
    border: 1px solid #f59e0b;
    color: #b45309;
    padding: 4px 10px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.78rem;
  }
  .reset-btn {
    background: #fce4ec;
    border: 1px solid #f48fb1;
    color: #880e4f;
    padding: 4px 10px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.78rem;
  }
  .copy-btn {
    background: none;
    border: 1px solid var(--ot-border);
    color: var(--ot-muted);
    padding: 2px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.78rem;
  }
  .copy-btn:hover { border-color: var(--ot-black); color: var(--ot-black); }

  /* ── Chargement / Erreur ── */
  .loading-overlay {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: absolute;
    inset: 40px 0 0 0;
    background: rgba(255,255,255,0.95);
    z-index: 10;
    color: var(--ot-muted);
    gap: 12px;
  }
  .loading-overlay p { font-size: 0.9rem; margin: 0; }

  .spinner {
    width: 36px;
    height: 36px;
    border: 3px solid var(--ot-border);
    border-top-color: var(--ot-black);
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .error-box {
    background: #fce4ec;
    color: #b71c1c;
    padding: 10px 16px;
    margin: 10px;
    border-radius: 8px;
    border: 1px solid #ef9a9a;
    flex-shrink: 0;
    font-size: 0.88rem;
  }

  /* ── Panel actions ── */
  .panel-actions { display: flex; gap: 8px; }
</style>