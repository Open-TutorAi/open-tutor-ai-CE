<script>
  import { onMount, onDestroy } from 'svelte';
  import { blocklyStore } from '$lib/stores/blockly';
  import { submitBlocklyCode, testBlocklyCode } from '$lib/api/blockly';

  export let assignmentId;
  export let allowedBlocks = null;
  export let exerciseTitle = 'Exercice Blockly';
  export let description = '';
  export let hints = [];

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
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
        body: JSON.stringify({ assignment_id: assignmentId, python_code: pythonCode, blocks_json: getWorkspaceXml() }),
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
    } catch (err) {
      feedback = `Erreur : ${err.message}`;
    } finally { isSubmitting = false; feedbackStreaming = false; }
  }

  function copyPython() { navigator.clipboard.writeText(pythonCode); }
  function nextHint() { if (currentHintIndex < hints.length - 1) currentHintIndex++; }
</script>

<svelte:window on:resize={() => { if (workspace && Blockly) Blockly.svgResize(workspace); }} />

<div class="blockly-page">
  <div class="exercise-header">
    <div class="exercise-info">
      <h1 class="exercise-title">{exerciseTitle}</h1>
      <p class="exercise-description">{description}</p>
    </div>
    {#if score !== null}
      <div class="score-badge" class:score-great={score>=80} class:score-ok={score>=50&&score<80} class:score-low={score<50}>
        <span class="score-value">{score}</span><span class="score-label">/100</span>
      </div>
    {/if}
  </div>

  <div class="workspace-container">
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
            <button on:click={nextHint} disabled={currentHintIndex === hints.length - 1}>Indice suivant →</button>
          {/if}
        </div>
      {/if}

      {#if error}<div class="error-box">{error}</div>{/if}

      {#if isLoading}
        <div class="loading-overlay">
          <div class="spinner"></div>
          <p>Chargement de l'éditeur...</p>
        </div>
      {/if}

      <div bind:this={blocklyDiv} class="blockly-workspace"></div>
    </div>

    <div class="output-panel">
      <div class="python-section">
        <div class="panel-header">
          <span class="panel-title">🐍 Code Python généré</span>
          <button class="copy-btn" on:click={copyPython}>📋</button>
        </div>
        <pre class="python-code">{pythonCode || '# Glissez des blocs pour générer le code Python...'}</pre>
      </div>

      {#if testResult}
        <div class="console-section">
          <div class="panel-header"><span class="panel-title">🖥️ Console</span></div>
          <div class="console-output" class:console-error={testResult.error}>
            {#if testResult.error}
              <span class="error-prefix">❌ Erreur: </span>{testResult.error}
            {:else}
              <span class="success-prefix">✅ Sortie: </span>
              <pre>{testResult.stdout || '(aucune sortie)'}</pre>
              {#if testResult.test_results}
                <div class="test-cases">
                  {#each testResult.test_results as tc}
                    <div class="test-case" class:passed={tc.passed} class:failed={!tc.passed}>
                      {tc.passed ? '✅' : '❌'} Test {tc.index}: {tc.passed ? 'Réussi' : `Échec (attendu: "${tc.expected}", obtenu: "${tc.got}")`}
                    </div>
                  {/each}
                </div>
              {/if}
            {/if}
          </div>
        </div>
      {/if}

      {#if feedback || feedbackStreaming}
        <div class="feedback-section">
          <div class="panel-header">
            <span class="panel-title">🤖 Feedback IA</span>
            {#if feedbackStreaming}<span class="streaming-indicator">⟳ En cours...</span>{/if}
          </div>
          <div class="feedback-content">
            {feedback}{#if feedbackStreaming}<span class="cursor-blink">|</span>{/if}
          </div>
        </div>
      {/if}
    </div>
  </div>

  <div class="action-bar">
    <button class="btn btn-test" on:click={handleTest} disabled={isTesting||isSubmitting||!pythonCode.trim()}>
      {isTesting ? '⟳ Test en cours...' : '▶️ Tester'}
    </button>
    <button class="btn btn-submit" on:click={handleSubmit} disabled={isSubmitting||isTesting||!pythonCode.trim()}>
      {isSubmitting ? '⟳ Soumission...' : '🚀 Soumettre pour évaluation'}
    </button>
  </div>
</div>

<style>
  :global(body) { margin: 0; padding: 0; overflow: hidden; }

  .blockly-page {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: #f8f9fa;
    font-family: 'Segoe UI', sans-serif;
    overflow: hidden;
  }

  .exercise-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 24px;
    background: white;
    border-bottom: 2px solid #e3f2fd;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    flex-shrink: 0;
  }

  .exercise-title { font-size: 1.2rem; font-weight: 700; color: #1a237e; margin: 0 0 2px 0; }
  .exercise-description { color: #546e7a; font-size: 0.85rem; margin: 0; }

  .score-badge { display: flex; align-items: baseline; gap: 4px; padding: 8px 16px; border-radius: 12px; background: #e8f5e9; border: 2px solid #4caf50; }
  .score-badge.score-great { background: #e8f5e9; border-color: #4caf50; }
  .score-badge.score-ok { background: #fff8e1; border-color: #ff9800; }
  .score-badge.score-low { background: #fce4ec; border-color: #f44336; }
  .score-value { font-size: 1.8rem; font-weight: 800; color: #2e7d32; }
  .score-label { font-size: 0.9rem; color: #546e7a; }

  .workspace-container {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  .blockly-panel {
    flex: 0 0 60%;
    display: flex;
    flex-direction: column;
    border-right: 2px solid #e8eaf6;
    background: white;
    position: relative;
    overflow: hidden;
  }

  .output-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    background: #fafafa;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    background: #e8eaf6;
    border-bottom: 1px solid #c5cae9;
    flex-shrink: 0;
  }

  .panel-title { font-weight: 600; color: #283593; font-size: 0.9rem; }
  .panel-actions { display: flex; gap: 8px; }

  /* CLÉ : position absolute pour que Blockly remplisse tout l'espace */
  .blockly-workspace {
    position: absolute;
    top: 40px;
    left: 0;
    right: 0;
    bottom: 0;
  }

  .python-section { border-bottom: 1px solid #e0e0e0; flex-shrink: 0; }
  .python-code {
    background: #1e1e2e;
    color: #a6e3a1;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.85rem;
    padding: 16px;
    margin: 0;
    min-height: 140px;
    max-height: 200px;
    overflow: auto;
    line-height: 1.6;
  }

  .console-section, .feedback-section { border-bottom: 1px solid #e0e0e0; }
  .console-output {
    padding: 12px 16px;
    font-family: monospace;
    font-size: 0.85rem;
    background: #263238;
    color: #eceff1;
    min-height: 80px;
  }
  .console-output.console-error { color: #ef9a9a; }
  .error-prefix { color: #ef5350; font-weight: bold; }
  .success-prefix { color: #66bb6a; font-weight: bold; }
  .test-case { padding: 4px 0; font-size: 0.82rem; }
  .test-case.passed { color: #a5d6a7; }
  .test-case.failed { color: #ef9a9a; }

  .feedback-content { padding: 16px; font-size: 0.9rem; line-height: 1.7; color: #37474f; background: white; min-height: 80px; }
  .cursor-blink { animation: blink 0.8s infinite; color: #5c6bc0; }
  @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
  .streaming-indicator { font-size: 0.75rem; color: #7986cb; animation: pulse 1s infinite; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

  .action-bar {
    display: flex;
    gap: 12px;
    padding: 10px 24px;
    background: white;
    border-top: 2px solid #e3f2fd;
    flex-shrink: 0;
    align-items: center;
  }

  .btn { padding: 8px 20px; border: none; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.2s; }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-test { background: #e3f2fd; color: #1565c0; border: 2px solid #1565c0; }
  .btn-test:hover:not(:disabled) { background: #1565c0; color: white; }
  .btn-submit { background: #1a237e; color: white; flex: 1; max-width: 280px; }
  .btn-submit:hover:not(:disabled) { background: #283593; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(26,35,126,0.3); }

  .hint-box { background: #fff8e1; border-left: 4px solid #ffc107; padding: 10px 16px; font-size: 0.9rem; color: #5d4037; flex-shrink: 0; }
  .hint-btn { background: #fff8e1; border: 1px solid #ffc107; color: #f57f17; padding: 4px 10px; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
  .reset-btn { background: #fce4ec; border: 1px solid #e91e63; color: #c2185b; padding: 4px 10px; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
  .copy-btn { background: none; border: 1px solid #7986cb; color: #5c6bc0; padding: 2px 8px; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }

  .loading-overlay { display: flex; flex-direction: column; align-items: center; justify-content: center; position: absolute; inset: 40px 0 0 0; background: white; z-index: 10; color: #5c6bc0; }
  .spinner { width: 40px; height: 40px; border: 4px solid #e8eaf6; border-top-color: #5c6bc0; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 16px; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .error-box { background: #fce4ec; color: #c62828; padding: 12px 16px; margin: 12px; border-radius: 8px; border: 1px solid #ef9a9a; flex-shrink: 0; }
</style>