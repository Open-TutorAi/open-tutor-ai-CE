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
  let blockCount = 0;
  let activeTab = 'code'; // 'code' | 'console' | 'feedback'
  let copied = false;
  let showSuccessToast = false;

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
        blockCount = workspace.getAllBlocks(false).length;
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
    pythonCode = ''; testResult = null; feedback = ''; score = null; blockCount = 0;
  }

  async function handleTest() {
    if (!pythonCode.trim()) { testResult = { error: "Ajoutez des blocs d'abord." }; activeTab = 'console'; return; }
    isTesting = true; testResult = null; activeTab = 'console';
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
    isSubmitting = true; feedback = ''; score = null; feedbackStreaming = true; activeTab = 'feedback';
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
              if (data.type === 'score') {
                score = data.value;
                if (score >= 80) { showSuccessToast = true; setTimeout(() => showSuccessToast = false, 4000); }
              }
              else if (data.type === 'feedback') feedback += data.content;
            } catch {}
          }
        }
      }
    } catch (err) {
      feedback = `Erreur : ${err.message}`;
    } finally { isSubmitting = false; feedbackStreaming = false; }
<<<<<<< HEAD
  }

  async function copyPython() {
    await navigator.clipboard.writeText(pythonCode);
    copied = true; setTimeout(() => copied = false, 2000);
=======
>>>>>>> c5702ac (fix merge conflict in BlocklyEditor)
  }

  function nextHint() { if (currentHintIndex < hints.length - 1) currentHintIndex++; }

  $: scoreStyle = score === null ? null
    : score >= 80 ? { color: '#059669', bg: '#ECFDF5', border: '#6EE7B7', label: 'Excellent ! 🎉' }
    : score >= 50 ? { color: '#D97706', bg: '#FFFBEB', border: '#FDE68A', label: 'Bien joué ! 👍' }
    :               { color: '#DC2626', bg: '#FEF2F2', border: '#FECACA', label: 'Continue ! 💪' };

  $: progressWidth = Math.min(blockCount * 12, 100);
</script>

<svelte:window on:resize={() => { if (workspace && Blockly) Blockly.svgResize(workspace); }} />

<<<<<<< HEAD
<!-- ══ SUCCESS TOAST ══ -->
{#if showSuccessToast}
  <div class="toast">🏆 Bravo ! {score}/100 — {scoreStyle?.label}</div>
{/if}

<div class="bk-root">

  <!-- ══════════════ LAYOUT 3 COLONNES ══════════════ -->
  <div class="bk-layout">

    <!-- ─── COL 1 : CARTE EXERCICE ─── -->
    <aside class="col-ex">
      <div class="ex-stripe"></div>
      <div class="ex-scroll">

        <!-- Badge + titre -->
        <div class="ex-top">
          <div class="ex-icon-wrap">🎯</div>
          <span class="ex-tag">Mission</span>
          <h2 class="ex-title">{exerciseTitle}</h2>
          {#if description}
            <p class="ex-desc">{description}</p>
          {/if}
        </div>

        <div class="ex-sep"></div>

        <!-- Blocs disponibles -->
        <div class="ex-section">
          <div class="ex-sec-label">Blocs disponibles</div>
          <div class="ex-chips">
            <span class="ex-chip" style="--c:#F9A825">🔢 Var.</span>
            <span class="ex-chip" style="--c:#1565C0">➕ Math</span>
            <span class="ex-chip" style="--c:#00897B">📝 Texte</span>
            <span class="ex-chip" style="--c:#E53935">⚡ Logique</span>
            <span class="ex-chip" style="--c:#7B1FA2">🔄 Boucle</span>
            <span class="ex-chip" style="--c:#558B2F">📋 Liste</span>
            <span class="ex-chip" style="--c:#FF6F00">🔧 Fn</span>
          </div>
        </div>

        <div class="ex-sep"></div>

        <!-- Progression -->
        <div class="ex-prog-card">
          <div class="ep-row">
            <span class="ep-lbl">Progression</span>
            <span class="ep-val">{blockCount} bloc{blockCount !== 1 ? 's' : ''}</span>
          </div>
          <div class="ep-track"><div class="ep-fill" style="width:{progressWidth}%"></div></div>
          <p class="ep-hint">
            {#if blockCount === 0}✏️ Glisse ton premier bloc !
            {:else if blockCount < 3}🌱 Bon début, continue !
            {:else if blockCount < 6}🔥 Ça prend forme !
            {:else}⚡ Prêt à tester !{/if}
          </p>
        </div>

        <!-- Score si disponible -->
        {#if score !== null}
          <div class="ex-sep"></div>
          <div class="ex-score-card" style="background:{scoreStyle.bg};border-color:{scoreStyle.border}">
            <svg class="score-svg" viewBox="0 0 60 60">
              <circle cx="30" cy="30" r="24" fill="none" stroke="#E5E7EB" stroke-width="5"/>
              <circle cx="30" cy="30" r="24" fill="none" stroke="{scoreStyle.color}" stroke-width="5"
                stroke-dasharray="{(score/100)*150.8} 150.8"
                stroke-dashoffset="37.7" stroke-linecap="round"/>
              <text x="30" y="35" text-anchor="middle" font-size="13" font-weight="900"
                fill="{scoreStyle.color}" font-family="sans-serif">{score}</text>
            </svg>
            <div class="esc-info">
              <span class="esc-pts" style="color:{scoreStyle.color}">{score}/100</span>
              <span class="esc-msg">{scoreStyle.label}</span>
            </div>
          </div>
        {/if}

        <!-- Indices -->
        {#if hints.length > 0}
          <div class="ex-sep"></div>
          <div class="ex-section">
            <div class="ex-sec-label">Indices si tu bloques</div>
            <button class="hint-toggle" on:click={() => showHint = !showHint}>
              💡 {showHint ? 'Masquer' : 'Voir un indice'}
              <span class="ht-badge">{currentHintIndex + 1}/{hints.length}</span>
            </button>
            {#if showHint}
              <div class="hint-box">
                <p class="hint-text">{hints[currentHintIndex]}</p>
                {#if currentHintIndex < hints.length - 1}
                  <button class="hint-next" on:click={nextHint}>Suivant →</button>
                {/if}
              </div>
            {/if}
          </div>
        {/if}

=======
<div class="blockly-page">
  <div class="exercise-header">
    <div class="exercise-info">
      <h1 class="exercise-title">{exerciseTitle}</h1>
      <p class="exercise-description">{description}</p>
    </div>
    {#if score !== null}
      <div class="score-badge" class:score-great={score>=80} class:score-ok={score>=50&&score<80} class:score-low={score<50}>
        <span class="score-value">{score}</span><span class="score-label">/100</span>
>>>>>>> c5702ac (fix merge conflict in BlocklyEditor)
      </div>
    </aside>

<<<<<<< HEAD
    <!-- ─── COL 2 : BLOCKLY (GRAND) ─── -->
    <main class="col-bk">
      <!-- Header Blockly -->
      <div class="bk-header">
        <div class="bk-header-left">
          <span class="bk-live-dot"></span>
          <span class="bk-header-title">🧩 Éditeur Blockly</span>
          <span class="bk-header-sub">Glisse et emboîte les blocs pour programmer</span>
        </div>
        <div class="bk-header-right">
          <div class="bk-block-count" class:bk-count-active={blockCount > 0}>
            🧱 <strong>{blockCount}</strong> bloc{blockCount !== 1 ? 's' : ''}
          </div>
=======
  <div class="workspace-container">
    <div class="blockly-panel">
      <div class="panel-header">
        <span class="panel-title">🧩 Éditeur Blockly</span>
        <div class="panel-actions">
>>>>>>> c5702ac (fix merge conflict in BlocklyEditor)
          {#if hints.length > 0}
            <button class="bk-hint-btn" on:click={() => showHint = !showHint}>
              💡 Indice <span class="bhb-badge">{currentHintIndex+1}/{hints.length}</span>
            </button>
          {/if}
          <button class="bk-reset-btn" on:click={resetWorkspace} title="Réinitialiser">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.86"/></svg>
          </button>
        </div>
      </div>

      <!-- Hint banner inline -->
      {#if showHint && hints.length > 0}
        <div class="bk-hint-banner">
          <span>💡</span>
          <p>{hints[currentHintIndex]}</p>
<<<<<<< HEAD
          <div style="display:flex;gap:6px;flex-shrink:0">
            {#if currentHintIndex < hints.length - 1}
              <button class="hbb-next" on:click={nextHint}>Suivant →</button>
            {/if}
            <button class="hbb-close" on:click={() => showHint = false}>✕</button>
          </div>
        </div>
      {/if}

      {#if error}
        <div class="bk-error">⚠️ {error}</div>
      {/if}

      {#if isLoading}
        <div class="bk-loading">
          <div class="bk-spinner"></div>
          <p class="bkl-t">Chargement de l'éditeur…</p>
          <p class="bkl-s">Quelques secondes ✨</p>
=======
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
>>>>>>> c5702ac (fix merge conflict in BlocklyEditor)
        </div>
      {/if}

      <div bind:this={blocklyDiv} class="bk-workspace"></div>
    </main>

<<<<<<< HEAD
    <!-- ─── COL 3 : RÉSULTATS ─── -->
    <aside class="col-res">
      <!-- Tabs -->
      <div class="res-tabs">
        <button class="rtab" class:rtab-on={activeTab==='code'} on:click={() => activeTab='code'}>
          🐍 Code
        </button>
        <button class="rtab" class:rtab-on={activeTab==='console'} on:click={() => activeTab='console'}>
          🖥️ Console
          {#if testResult}
            <span class="rtab-dot" style="background:{testResult?.error ? '#EF4444' : '#10B981'}"></span>
          {/if}
        </button>
        <button class="rtab" class:rtab-on={activeTab==='feedback'} on:click={() => activeTab='feedback'}>
          🤖 IA
          {#if feedbackStreaming}<span class="rtab-pulse"></span>{/if}
        </button>
      </div>

      <div class="res-body">

        <!-- ── CODE ── -->
        {#if activeTab === 'code'}
          <div class="code-pane">
            <div class="code-topbar">
              <div class="mac-dots">
                <span style="background:#FF5F57"></span>
                <span style="background:#FEBC2E"></span>
                <span style="background:#28C840"></span>
              </div>
              <span class="code-lang-tag">python</span>
              <button class="btn-copy" on:click={copyPython}>{copied ? '✅' : '📋'}</button>
            </div>
            {#if pythonCode.trim()}
              <pre class="code-pre">{pythonCode}</pre>
            {:else}
              <div class="res-empty">
                <div class="re-icon">🐍</div>
                <p class="re-t">Pas encore de code</p>
                <p class="re-s">Ajoute des blocs pour voir le Python apparaître ici.</p>
              </div>
            {/if}
          </div>
        {/if}

        <!-- ── CONSOLE ── -->
        {#if activeTab === 'console'}
          <div class="console-pane">
            {#if !testResult && !isTesting}
              <div class="res-empty">
                <div class="re-icon">▶️</div>
                <p class="re-t">Rien à afficher</p>
                <p class="re-s">Clique sur <strong>Tester</strong> pour voir le résultat.</p>
              </div>
            {:else if isTesting}
              <div class="res-running">
                <div class="run-ring"></div>
                <p>Exécution en cours…</p>
              </div>
            {:else if testResult?.error}
              <div class="res-card res-card-err">
                <div class="rc-head rc-head-err">❌ Erreur d'exécution</div>
                <pre class="rc-pre rc-err">{testResult.error}</pre>
                <p class="rc-tip">💡 Vérifie tes blocs et réessaie.</p>
              </div>
            {:else}
              <div class="res-card res-card-ok">
                <div class="rc-head rc-head-ok">✅ Exécution réussie !</div>
                {#if testResult?.stdout}
                  <div class="rc-section">
                    <p class="rc-sec-lbl">Sortie</p>
                    <pre class="rc-out">{testResult.stdout}</pre>
                  </div>
                {/if}
                {#if testResult?.test_results?.length}
                  <div class="rc-section">
                    <p class="rc-sec-lbl">Tests</p>
                    {#each testResult.test_results as tc, i}
                      <div class="tc-row" class:tc-ok={tc.passed} class:tc-ko={!tc.passed}>
                        <span>{tc.passed ? '✅' : '❌'}</span>
                        <span class="tc-n">Test {i+1}</span>
                        <span class="tc-d">{tc.passed ? 'Réussi' : `"${tc.expected}" ≠ "${tc.got}"`}</span>
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/if}

        <!-- ── FEEDBACK IA ── -->
        {#if activeTab === 'feedback'}
          <div class="fb-pane">
            {#if !feedback && !feedbackStreaming}
              <div class="res-empty">
                <div class="re-icon">🤖</div>
                <p class="re-t">Pas de feedback</p>
                <p class="re-s">Soumets ton exercice pour recevoir une analyse IA.</p>
              </div>
            {:else}
              {#if score !== null}
                <div class="fb-score-bar" style="border-color:{scoreStyle.border};background:{scoreStyle.bg}">
                  <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                    <span class="fbs-lbl">Score</span>
                    <span class="fbs-val" style="color:{scoreStyle.color}">{score}/100</span>
                  </div>
                  <div class="fbs-track">
                    <div class="fbs-fill" style="width:{score}%;background:{scoreStyle.color}"></div>
                  </div>
=======
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
>>>>>>> c5702ac (fix merge conflict in BlocklyEditor)
                </div>
              {/if}
              <div class="fb-bubble">
                <div class="fb-av">🤖</div>
                <div class="fb-msg-wrap">
                  <span class="fb-from">Tuteur IA</span>
                  <p class="fb-msg">{feedback}{#if feedbackStreaming}<span class="fb-cur">|</span>{/if}</p>
                  {#if feedbackStreaming}<span class="fb-gen">⟳ Génération…</span>{/if}
                </div>
              </div>
            {/if}
          </div>
        {/if}

<<<<<<< HEAD
      </div>
    </aside>
  </div>

  <!-- ══ FOOTER ══ -->
  <footer class="bk-footer">
    <div class="ft-left">
      <div class="ft-prog-track"><div class="ft-prog-fill" style="width:{progressWidth}%"></div></div>
      <span class="ft-msg">
        {#if blockCount === 0}Glisse tes premiers blocs !
        {:else if blockCount < 4}Bon début, continue !
        {:else}Prêt à tester 🚀{/if}
      </span>
=======
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
>>>>>>> c5702ac (fix merge conflict in BlocklyEditor)
    </div>
    <div class="ft-btns">
      <button class="btn-test" on:click={handleTest}
        disabled={isTesting || isSubmitting || !pythonCode.trim()}>
        {#if isTesting}<span class="spin">⟳</span> Test…{:else}▶ Tester{/if}
      </button>
      <button class="btn-submit" on:click={handleSubmit}
        disabled={isSubmitting || isTesting || !pythonCode.trim()}>
        {#if isSubmitting}<span class="spin">⟳</span> Envoi…{:else}🚀 Soumettre pour évaluation{/if}
      </button>
    </div>
  </footer>

<<<<<<< HEAD
</div>

<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── TOKENS ── */
:root {
  --white:  #FFFFFF;
  --bg:     #F0F4FF;
  --bg2:    #F5F7FF;
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
  --r:  12px;
}

:global(body) { margin:0; padding:0; overflow:hidden; background:var(--bg); }
* { box-sizing:border-box; }

/* ── TOAST ── */
.toast {
  position: fixed; top: 66px; left: 50%; transform: translateX(-50%);
  background: linear-gradient(135deg, #10B981, #059669);
  color: #fff; font-family: var(--ff); font-weight: 900; font-size: .9rem;
  padding: 10px 26px; border-radius: 40px; z-index: 9999;
  box-shadow: 0 8px 28px rgba(16,185,129,.4); white-space: nowrap;
  animation: t-in .4s cubic-bezier(.34,1.56,.64,1) both, t-out .3s ease 3.5s both;
}
@keyframes t-in  { from{transform:translateX(-50%) translateY(-16px);opacity:0} }
@keyframes t-out { to  {transform:translateX(-50%) translateY(-16px);opacity:0} }

/* ── ROOT ── */
.bk-root {
  display: flex; flex-direction: column;
  height: 100vh; overflow: hidden;
  font-family: var(--ff); color: var(--ink);
  background: var(--bg);
}

/* ── LAYOUT ── */
.bk-layout {
  display: grid;
  grid-template-columns: 260px 1fr 285px;
  flex: 1;
  overflow: hidden;
}

/* ════════════════════════════
   COL 1 — EXERCICE
════════════════════════════ */
.col-ex {
  border-right: 2px solid var(--border);
  background: var(--white);
  display: flex; flex-direction: column;
  overflow: hidden;
}

.ex-stripe {
  height: 5px; flex-shrink: 0;
  background: linear-gradient(90deg, #4F46E5, #7C3AED, #EC4899, #F59E0B, #10B981);
}

.ex-scroll {
  flex: 1; overflow-y: auto; padding: 18px 16px 24px;
  display: flex; flex-direction: column; gap: 0;
  scrollbar-width: thin; scrollbar-color: var(--bd2) transparent;
}

.ex-top { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }

.ex-icon-wrap {
  width: 48px; height: 48px; border-radius: 14px;
  background: linear-gradient(135deg, #EEF2FF, #E0E7FF);
  border: 2px solid var(--bd2);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem;
  box-shadow: 0 4px 12px rgba(79,70,229,.12);
}

.ex-tag {
  font-size: .6rem; font-weight: 900; text-transform: uppercase;
  letter-spacing: .1em; color: var(--indigo);
}

.ex-title {
  font-size: 1.05rem; font-weight: 900; color: var(--ink); margin: 0;
  line-height: 1.35;
}

.ex-desc {
  font-size: .78rem; color: var(--ink3); line-height: 1.65; margin: 0;
}

.ex-sep { height: 1px; background: var(--border); margin: 14px 0; }

.ex-section { display: flex; flex-direction: column; gap: 8px; margin-bottom: 4px; }

.ex-sec-label {
  font-size: .6rem; font-weight: 900; text-transform: uppercase;
  letter-spacing: .08em; color: var(--ink4);
}

.ex-chips { display: flex; flex-wrap: wrap; gap: 5px; }

.ex-chip {
  padding: 3px 9px; border-radius: 20px; font-size: .68rem; font-weight: 800;
  background: color-mix(in srgb, var(--c) 10%, white);
  border: 2px solid color-mix(in srgb, var(--c) 25%, white);
  color: var(--c);
  transition: transform .12s;
}
.ex-chip:hover { transform: scale(1.06); }

/* Progression */
.ex-prog-card {
  background: var(--bg); border: 2px solid var(--border);
  border-radius: var(--r); padding: 11px 12px; margin-bottom: 4px;
}
.ep-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.ep-lbl { font-size: .6rem; font-weight: 900; color: var(--ink4); text-transform: uppercase; letter-spacing: .08em; }
.ep-val { font-size: .8rem; font-weight: 900; color: var(--indigo); }
.ep-track { height: 7px; background: var(--border); border-radius: 20px; overflow: hidden; }
.ep-fill {
  height: 100%; border-radius: 20px;
  background: linear-gradient(90deg, var(--indigo), #EC4899);
  transition: width .5s cubic-bezier(.34,1.1,.64,1);
}
.ep-hint { margin: 6px 0 0; font-size: .7rem; color: var(--ink3); font-weight: 700; }

/* Score card */
.ex-score-card {
  display: flex; align-items: center; gap: 12px;
  border: 2px solid; border-radius: var(--r); padding: 10px 12px;
  animation: pop-in .5s cubic-bezier(.34,1.56,.64,1) both;
}
@keyframes pop-in { from{transform:scale(.6);opacity:0} }
.score-svg { width: 52px; height: 52px; flex-shrink: 0; transform: rotate(-90deg); }
.esc-info { display: flex; flex-direction: column; gap: 2px; }
.esc-pts { font-size: .9rem; font-weight: 900; }
.esc-msg { font-size: .72rem; font-weight: 700; color: var(--ink3); }

/* Hint toggle */
.hint-toggle {
  display: flex; align-items: center; justify-content: space-between;
  width: 100%; padding: 8px 11px; border-radius: var(--r);
  background: #FFFBEB; border: 2px solid #FDE68A;
  color: #92400E; font-family: var(--ff); font-size: .75rem; font-weight: 800;
  cursor: pointer; transition: background .15s;
}
.hint-toggle:hover { background: #FEF3C7; }
.ht-badge { background: #FCD34D; color: #78350F; padding: 1px 7px; border-radius: 20px; font-size: .6rem; font-weight: 900; }

.hint-box {
  background: #FFFBEB; border: 2px solid #FDE68A; border-radius: var(--r);
  padding: 10px 12px; display: flex; flex-direction: column; gap: 8px;
}
.hint-text { font-size: .75rem; color: #78350F; line-height: 1.6; margin: 0; font-weight: 600; }
.hint-next {
  align-self: flex-start; background: #FCD34D; border: none; color: #78350F;
  padding: 3px 10px; border-radius: 8px; font-size: .7rem; font-weight: 900;
  font-family: var(--ff); cursor: pointer;
}

/* ════════════════════════════
   COL 2 — BLOCKLY
════════════════════════════ */
.col-bk {
  display: flex; flex-direction: column;
  overflow: hidden; background: #FAFBFF; position: relative;
}

.bk-header {
  height: 46px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 14px; gap: 10px;
  background: var(--white); border-bottom: 2px solid var(--border);
}

.bk-header-left { display: flex; align-items: center; gap: 8px; }

.bk-live-dot {
  width: 8px; height: 8px; border-radius: 50%; background: var(--green); flex-shrink: 0;
  box-shadow: 0 0 0 3px rgba(16,185,129,.2);
  animation: live-pulse 2.5s ease-in-out infinite;
}
@keyframes live-pulse {
  0%,100% { box-shadow: 0 0 0 3px rgba(16,185,129,.2); }
  50%      { box-shadow: 0 0 0 7px rgba(16,185,129,.05); }
}

.bk-header-title { font-size: .82rem; font-weight: 900; color: var(--ink); }
.bk-header-sub   { font-size: .66rem; color: var(--ink4); }

.bk-header-right { display: flex; align-items: center; gap: 7px; }

.bk-block-count {
  display: flex; align-items: center; gap: 5px;
  padding: 4px 10px; border-radius: 20px;
  background: var(--bg); border: 2px solid var(--border);
  font-size: .72rem; color: var(--ink3); font-weight: 700; white-space: nowrap;
  transition: all .2s;
}
.bk-block-count.bk-count-active { border-color: var(--indigo); color: var(--indigo); background: #EEF2FF; }

.bk-hint-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 4px 11px; border-radius: 20px;
  background: #FFFBEB; border: 2px solid #FDE68A;
  color: #92400E; font-family: var(--ff); font-size: .72rem; font-weight: 800;
  cursor: pointer; white-space: nowrap;
}
.bhb-badge { background: #FCD34D; color: #78350F; padding: 1px 5px; border-radius: 20px; font-size: .58rem; font-weight: 900; }

.bk-reset-btn {
  width: 30px; height: 30px; border-radius: 8px;
  background: var(--bg); border: 2px solid var(--border);
  color: var(--ink4); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
.bk-reset-btn:hover { border-color: var(--red); color: var(--red); background: #FEF2F2; }

.bk-hint-banner {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 14px; flex-shrink: 0;
  background: linear-gradient(90deg, #FFFBEB, #FEF9C3);
  border-bottom: 2px solid #FDE68A; font-size: .8rem;
  color: #78350F; font-weight: 600;
}
.bk-hint-banner p { flex: 1; margin: 0; line-height: 1.5; }
.hbb-next { background: #FCD34D; border: none; color: #78350F; padding: 3px 9px; border-radius: 7px; font-family: var(--ff); font-size: .7rem; font-weight: 900; cursor: pointer; }
.hbb-close { background: none; border: 2px solid #FDE68A; color: #92400E; padding: 3px 7px; border-radius: 7px; font-family: var(--ff); font-size: .7rem; cursor: pointer; }

.bk-error {
  padding: 8px 14px; font-size: .78rem; flex-shrink: 0;
  background: #FEF2F2; border-bottom: 1px solid #FECACA; color: #B91C1C;
}

.bk-loading {
  position: absolute; inset: 46px 0 0 0; z-index: 20;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: #FAFBFF; gap: 10px;
}
.bk-spinner {
  width: 40px; height: 40px;
  border: 4px solid var(--border); border-top-color: var(--indigo);
  border-radius: 50%; animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.bkl-t { font-weight: 900; font-size: .88rem; color: var(--ink2); margin: 0; }
.bkl-s { font-size: .72rem; color: var(--ink4); margin: 0; }

.bk-workspace {
  position: absolute;
  top: 46px; left: 0; right: 0; bottom: 0;
}

/* ════════════════════════════
   COL 3 — RÉSULTATS
════════════════════════════ */
.col-res {
  border-left: 2px solid var(--border);
  background: var(--white);
  display: flex; flex-direction: column; overflow: hidden;
}

.res-tabs {
  display: flex; border-bottom: 2px solid var(--border);
  background: var(--bg2); padding: 0 6px; flex-shrink: 0;
}

.rtab {
  display: flex; align-items: center; gap: 4px;
  padding: 9px 11px; border: none; background: none;
  border-bottom: 3px solid transparent; margin-bottom: -2px;
  font-family: var(--ff); font-size: .73rem; font-weight: 800;
  color: var(--ink4); cursor: pointer; transition: color .15s; white-space: nowrap; position: relative;
}
.rtab:hover { color: var(--ink2); }
.rtab-on { color: var(--indigo) !important; border-bottom-color: var(--indigo); }
.rtab-dot { width: 6px; height: 6px; border-radius: 50%; }
.rtab-pulse { width: 6px; height: 6px; border-radius: 50%; background: var(--indigo); animation: rpulse 1s ease-in-out infinite; }
@keyframes rpulse { 0%,100%{box-shadow:0 0 0 0 rgba(79,70,229,.5)} 50%{box-shadow:0 0 0 4px rgba(79,70,229,0)} }

.res-body { flex: 1; overflow: hidden; display: flex; flex-direction: column; }

/* Code pane */
.code-pane { display: flex; flex-direction: column; height: 100%; }
.code-topbar {
  display: flex; align-items: center; gap: 7px;
  padding: 7px 11px; background: #F8FAFE; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.mac-dots { display: flex; gap: 4px; }
.mac-dots span { width: 10px; height: 10px; border-radius: 50%; display: block; }
.code-lang-tag { flex: 1; font-family: var(--fm); font-size: .6rem; color: var(--ink4); }
.btn-copy {
  background: var(--white); border: 2px solid var(--border); color: var(--ink3);
  padding: 2px 9px; border-radius: 7px; font-family: var(--ff); font-size: .68rem; font-weight: 800;
  cursor: pointer; transition: all .15s;
}
.btn-copy:hover { border-color: var(--indigo); color: var(--indigo); background: #EEF2FF; }
.code-pre {
  flex: 1; overflow: auto; margin: 0; padding: 13px 14px;
  font-family: var(--fm); font-size: .72rem; line-height: 1.8;
  color: #1E3A5F; background: #F8FAFE;
  white-space: pre-wrap; word-break: break-word;
}

/* Empty state */
.res-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  flex: 1; height: 100%; padding: 28px 18px; text-align: center; gap: 4px;
}
.re-icon { font-size: 2.2rem; margin-bottom: 10px; }
.re-t { font-size: .84rem; font-weight: 900; color: var(--ink2); margin: 0 0 4px; }
.re-s { font-size: .72rem; color: var(--ink4); margin: 0; line-height: 1.65; }

/* Console pane */
.console-pane { display: flex; flex-direction: column; height: 100%; overflow-y: auto; }
.res-running { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 10px; color: var(--ink3); font-size: .82rem; font-weight: 700; }
.run-ring { width: 28px; height: 28px; border: 3px solid var(--border); border-top-color: var(--green); border-radius: 50%; animation: spin .6s linear infinite; }

.res-card { margin: 12px; border-radius: var(--r); border: 2px solid; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.05); }
.res-card-err { border-color: #FECACA; }
.res-card-ok  { border-color: #BBF7D0; }
.rc-head { padding: 8px 11px; font-size: .78rem; font-weight: 900; }
.rc-head-err { background: #FEF2F2; color: var(--red); border-bottom: 1px solid #FECACA; }
.rc-head-ok  { background: #F0FDF4; color: var(--green); border-bottom: 1px solid #BBF7D0; }
.rc-pre { margin: 0; padding: 9px 11px; font-family: var(--fm); font-size: .7rem; white-space: pre-wrap; }
.rc-err { color: #B91C1C; background: #FFF5F5; }
.rc-tip { margin: 0; padding: 7px 11px; font-size: .7rem; color: #92400E; background: #FFFBEB; border-top: 1px solid #FDE68A; }
.rc-section { padding: 8px 11px; border-top: 1px solid var(--border); }
.rc-sec-lbl { font-size: .58rem; font-weight: 900; color: var(--ink4); text-transform: uppercase; letter-spacing: .08em; margin: 0 0 5px; }
.rc-out { margin: 0; font-family: var(--fm); font-size: .7rem; color: #065F46; background: #F0FDF4; padding: 6px 9px; border-radius: 7px; }
.tc-row { display: flex; align-items: center; gap: 5px; padding: 4px 8px; border-radius: 7px; margin: 2px 0; background: var(--bg2); font-size: .7rem; }
.tc-ok { border-left: 3px solid var(--green); }
.tc-ko { border-left: 3px solid var(--red); }
.tc-n { font-weight: 900; color: var(--ink2); min-width: 42px; font-size: .66rem; }
.tc-d { color: var(--ink3); font-size: .65rem; }

/* Feedback pane */
.fb-pane { display: flex; flex-direction: column; height: 100%; overflow-y: auto; padding: 12px; gap: 10px; }
.fb-score-bar { border: 2px solid; border-radius: var(--r); padding: 10px 12px; flex-shrink: 0; }
.fbs-lbl { font-size: .58rem; font-weight: 900; color: var(--ink4); text-transform: uppercase; letter-spacing: .08em; }
.fbs-val { font-size: .78rem; font-weight: 900; }
.fbs-track { height: 6px; background: var(--border); border-radius: 20px; overflow: hidden; }
.fbs-fill { height: 100%; border-radius: 20px; transition: width 1.2s cubic-bezier(.34,1.1,.64,1); }

.fb-bubble { display: flex; gap: 8px; align-items: flex-start; }
.fb-av {
  width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, var(--indigo), var(--violet));
  display: flex; align-items: center; justify-content: center; font-size: .9rem;
  box-shadow: 0 3px 10px rgba(79,70,229,.22);
}
.fb-msg-wrap {
  flex: 1; background: var(--bg2); border: 2px solid var(--border);
  border-radius: 0 14px 14px 14px; padding: 10px 12px;
}
.fb-from { display: block; font-size: .6rem; font-weight: 900; color: var(--indigo); margin-bottom: 4px; text-transform: uppercase; letter-spacing: .06em; }
.fb-msg { font-size: .76rem; color: var(--ink2); line-height: 1.8; white-space: pre-wrap; margin: 0; }
.fb-cur { animation: blink .8s step-end infinite; color: var(--indigo); font-weight: 900; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.fb-gen { display: block; margin-top: 4px; font-size: .62rem; color: var(--indigo); font-weight: 700; }

/* ── FOOTER ── */
.bk-footer {
  height: 54px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 18px; gap: 14px;
  background: var(--white); border-top: 2px solid var(--border);
  box-shadow: 0 -2px 8px rgba(0,0,0,.04);
}

.ft-left { display: flex; align-items: center; gap: 9px; flex: 1; }
.ft-prog-track { width: 90px; height: 6px; background: var(--border); border-radius: 20px; overflow: hidden; flex-shrink: 0; }
.ft-prog-fill { height: 100%; background: linear-gradient(90deg, var(--indigo), #EC4899); border-radius: 20px; transition: width .5s ease; }
.ft-msg { font-size: .72rem; color: var(--ink4); font-weight: 700; }

.ft-btns { display: flex; gap: 8px; }

.btn-test {
  padding: 8px 18px; border-radius: var(--r);
  background: #EEF2FF; border: 2px solid var(--indigo); color: var(--indigo);
  font-family: var(--ff); font-size: .8rem; font-weight: 900;
  cursor: pointer; transition: all .15s; white-space: nowrap; min-width: 88px;
}
.btn-test:hover:not(:disabled) { background: var(--indigo); color: #fff; box-shadow: 0 4px 14px rgba(79,70,229,.3); }
.btn-test:disabled { opacity: .4; cursor: not-allowed; }

.btn-submit {
  padding: 8px 20px; border-radius: var(--r);
  background: linear-gradient(135deg, var(--indigo), var(--violet));
  border: none; color: #fff;
  font-family: var(--ff); font-size: .8rem; font-weight: 900;
  cursor: pointer; transition: all .15s; white-space: nowrap; min-width: 115px;
  box-shadow: 0 3px 10px rgba(79,70,229,.28);
}
.btn-submit:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 7px 20px rgba(79,70,229,.38); }
.btn-submit:disabled { opacity: .4; cursor: not-allowed; transform: none; }

.spin { display: inline-block; animation: spin .6s linear infinite; }
=======
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
>>>>>>> c5702ac (fix merge conflict in BlocklyEditor)
</style>