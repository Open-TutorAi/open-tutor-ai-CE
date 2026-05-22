<script lang="ts">
  import { onMount, getContext, createEventDispatcher } from 'svelte';
  import { user } from '$lib/stores';
  import { TUTOR_API_BASE_URL } from '$lib/constants';

  const dispatch = createEventDispatcher<{
    explain: { code: string; output: string; error: string; prompt: string };
  }>();

  const i18n = getContext('i18n');

  // ─── État ────────────────────────────────────────────────────────────────────

  let code = `# 🐍 Éditeur Python interactif
# Ctrl+Entrée pour exécuter

def fibonacci(n: int) -> list[int]:
    """Retourne les n premiers nombres de Fibonacci."""
    if not isinstance(n, int) or n < 0:
        raise ValueError(f"n doit être un entier positif, reçu : {n!r}")
    seq = []
    a, b = 0, 1
    for _ in range(n):
        seq.append(a)
        a, b = b, a + b
    return seq

fib = fibonacci(10)
print("Fibonacci:", fib)
print(f"Somme: {sum(fib)}")
print(f"Pairs: {[x for x in fib if x % 2 == 0]}")
`;

  let terminalLines: TerminalLine[] = [];
  let isRunning = false;
  let lastExecTime = '';
  let cursorLine = 1;
  let cursorCol = 1;
  let statusState: 'idle' | 'running' | 'success' | 'error' = 'idle';

  // ─── Stdin ───────────────────────────────────────────────────────────────────

  // Inputs détectés dans le code (ex: name = input("Ton nom : "))
  type DetectedInput = { prompt: string; value: string };
  let detectedInputs: DetectedInput[] = [];
  let showInputPanel = false;

  /** Scanne le code pour trouver tous les appels input(...) */
  function detectInputs(src: string): DetectedInput[] {
    const results: DetectedInput[] = [];
    // Matches: input(), input("prompt"), input('prompt'), input(f"..."), variable = input(...)
    const re = /input\s*\(\s*(?:f?["'`]([^"'`]*?)["'`])?\s*\)/g;
    let m: RegExpExecArray | null;
    while ((m = re.exec(src)) !== null) {
      const prompt = m[1] ?? '';
      results.push({ prompt: prompt.trim(), value: '' });
    }
    return results;
  }

  function openInputPanel() {
    detectedInputs = detectInputs(code);
    if (detectedInputs.length === 0) {
      // Aucun input() détecté — on ajoute quand même un champ libre
      detectedInputs = [{ prompt: '', value: '' }];
    }
    showInputPanel = true;
  }

  function closeInputPanel() {
    showInputPanel = false;
  }

  function addInputRow() {
    detectedInputs = [...detectedInputs, { prompt: '', value: '' }];
  }

  function removeInputRow(i: number) {
    detectedInputs = detectedInputs.filter((_, idx) => idx !== i);
  }

  /** Construit la chaîne stdin à envoyer (une valeur par ligne) */
  function buildStdin(): string {
    return detectedInputs.map(d => d.value).join('\n');
  }

  // ─── Types ───────────────────────────────────────────────────────────────────

  type TerminalLine = {
    text: string;
    type: 'output' | 'error' | 'info' | 'success' | 'meta' | 'prompt' | 'blank';
  };

  // ─── Refs DOM ────────────────────────────────────────────────────────────────

  let textareaEl: HTMLTextAreaElement;
  let highlightEl: HTMLDivElement;
  let lineNumsEl: HTMLDivElement;
  let terminalEl: HTMLDivElement;
  let codeScrollEl: HTMLDivElement;

  // ─── Syntaxe ─────────────────────────────────────────────────────────────────

  const KEYWORDS = new Set([
    'False','None','True','and','as','assert','async','await','break',
    'class','continue','def','del','elif','else','except','finally',
    'for','from','global','if','import','in','is','lambda','nonlocal',
    'not','or','pass','raise','return','try','while','with','yield'
  ]);
  const BUILTINS = new Set([
    'print','range','len','type','int','float','str','list','dict',
    'set','tuple','bool','sum','min','max','abs','round','sorted',
    'enumerate','zip','map','filter','input','open','format','repr',
    'id','isinstance','hasattr','getattr','setattr','ValueError',
    'TypeError','IndexError','KeyError','Exception'
  ]);

  function esc(s: string): string {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function tokenizeLine(line: string): string {
    const out: string[] = [];
    let i = 0;
    const n = line.length;
    while (i < n) {
      // Commentaire
      if (line[i] === '#') {
        out.push(`<span class="cm">${esc(line.slice(i))}</span>`);
        break;
      }
      // String
      if (line[i] === '"' || line[i] === "'") {
        const q = line[i];
        const triple = line.slice(i, i + 3) === q.repeat(3);
        let j = triple ? i + 3 : i + 1;
        if (triple) {
          while (j < n && line.slice(j, j + 3) !== q.repeat(3)) j++;
          j += 3;
        } else {
          while (j < n && line[j] !== q) j++;
          j++;
        }
        // f-string ?
        const raw = line.slice(i, j);
        const cls = (i > 0 && (line[i - 1] === 'f' || line[i - 1] === 'F')) ? 'fs' : 'st';
        out.push(`<span class="${cls}">${esc(raw)}</span>`);
        i = j;
        continue;
      }
      // f"..." prefix
      if ((line[i] === 'f' || line[i] === 'F') && (line[i + 1] === '"' || line[i + 1] === "'")) {
        out.push(`<span class="fs">f</span>`);
        i++;
        continue;
      }
      // Nombre
      const numM = line.slice(i).match(/^\d+\.?\d*/);
      if (numM && (i === 0 || !/\w/.test(line[i - 1]))) {
        out.push(`<span class="nm">${esc(numM[0])}</span>`);
        i += numM[0].length;
        continue;
      }
      // Mot
      const wM = line.slice(i).match(/^\w+/);
      if (wM) {
        const w = wM[0];
        if (KEYWORDS.has(w)) out.push(`<span class="kw">${w}</span>`);
        else if (BUILTINS.has(w)) out.push(`<span class="bi">${w}</span>`);
        else if (line[i + w.length] === '(') out.push(`<span class="fn">${w}</span>`);
        else if (w === 'self' || w === 'cls') out.push(`<span class="sp">${w}</span>`);
        else out.push(esc(w));
        i += w.length;
        continue;
      }
      // Opérateurs
      if ('=+-*/%<>!&|^~'.includes(line[i])) {
        out.push(`<span class="op">${esc(line[i])}</span>`);
      } else {
        out.push(esc(line[i]));
      }
      i++;
    }
    return out.join('');
  }

  function updateHighlight() {
    if (!highlightEl) return;
    const lines = code.split('\n');
    highlightEl.innerHTML = lines.map(l => tokenizeLine(l) + '\n').join('');
  }

  function updateLineNumbers() {
    if (!lineNumsEl) return;
    const count = code.split('\n').length;
    lineNumsEl.innerHTML = Array.from({ length: count }, (_, i) =>
      `<span class="lnum">${i + 1}</span>`
    ).join('');
  }

  function updateCursor() {
    if (!textareaEl) return;
    const before = code.substring(0, textareaEl.selectionStart);
    const lines = before.split('\n');
    cursorLine = lines.length;
    cursorCol = lines[lines.length - 1].length + 1;
  }

  function syncScroll() {
    if (!highlightEl || !codeScrollEl || !lineNumsEl) return;
    highlightEl.style.transform = `translateY(-${codeScrollEl.scrollTop}px)`;
    lineNumsEl.scrollTop = codeScrollEl.scrollTop;
  }

  function handleInput() {
    updateHighlight();
    updateLineNumbers();
    updateCursor();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Tab') {
      e.preventDefault();
      const s = textareaEl.selectionStart;
      const end = textareaEl.selectionEnd;
      code = code.substring(0, s) + '    ' + code.substring(end);
      setTimeout(() => {
        textareaEl.selectionStart = textareaEl.selectionEnd = s + 4;
        updateHighlight();
        updateLineNumbers();
      }, 0);
      return;
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      runCode();
      return;
    }
    setTimeout(updateCursor, 0);
  }

  // ─── Terminal ────────────────────────────────────────────────────────────────

  function termAdd(text: string, type: TerminalLine['type'] = 'output') {
    terminalLines = [...terminalLines, { text, type }];
    setTimeout(() => {
      if (terminalEl) terminalEl.scrollTop = terminalEl.scrollHeight;
    }, 0);
  }

  function termClear() {
    terminalLines = [];
  }

  // ─── Exécution ───────────────────────────────────────────────────────────────

  async function runCode() {
    if (isRunning || !code.trim()) return;
    if (code.length > 5000) {
      termAdd('⚠ Code trop long (max 5000 caractères)', 'error');
      return;
    }

    isRunning = true;
    statusState = 'running';
    termClear();
    termAdd('$ python main.py', 'prompt');

    const t0 = performance.now();

    try {
      const res = await fetch(`${TUTOR_API_BASE_URL}/python/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${$user?.token ?? ''}`
        },
        body: JSON.stringify({
          code,
          timeout: 30,
          stdin: detectedInputs.length > 0 ? buildStdin() : undefined
        })
      });

      const elapsed = ((performance.now() - t0) / 1000).toFixed(2);

      if (!res.ok) {
        let detail = 'Erreur serveur';
        try {
          const err = await res.json();
          detail = err.detail ?? detail;
        } catch (_) {}
        if (res.status === 400 && detail.includes('Import')) {
          termAdd('', 'blank');
          termAdd(`⛔ Sécurité : ${detail}`, 'error');
        } else if (res.status === 408) {
          termAdd('', 'blank');
          termAdd('⏱ Timeout — exécution > 30s', 'error');
        } else {
          termAdd('', 'blank');
          termAdd(`✗ Erreur ${res.status} : ${detail}`, 'error');
        }
        statusState = 'error';
        lastExecTime = '';
      } else {
        const data = await res.json();
        if (data.output) {
          data.output.split('\n').forEach((l: string) =>
            termAdd(l || '', l ? 'output' : 'blank')
          );
        }
        if (data.error) {
          termAdd('', 'blank');
          data.error.split('\n').filter(Boolean).forEach((l: string) =>
            termAdd(l, 'error')
          );
          statusState = 'error';
          lastExecTime = '';
        } else {
          termAdd('', 'blank');
          termAdd(`✓ Terminé en ${elapsed}s`, 'success');
          statusState = 'success';
          lastExecTime = `${elapsed}s`;
          setTimeout(() => { if (statusState === 'success') statusState = 'idle'; }, 3000);
        }
      }
    } catch (err) {
      const elapsed = ((performance.now() - t0) / 1000).toFixed(2);
      termAdd('', 'blank');
      termAdd('⚠ Backend non disponible — vérifie que le serveur FastAPI tourne', 'info');
      termAdd('→ Lance : uvicorn main:app --reload', 'meta');
      statusState = 'error';
      lastExecTime = '';
    } finally {
      isRunning = false;
    }
  }

  async function explainCode() {
    if (!code.trim() || isRunning) return;

    isRunning = true;
    statusState = 'running';
    termAdd('$ ⚡ Envoi au tuteur IA...', 'prompt');

    const currentOutput = terminalLines
      .filter(l => l.type === 'output')
      .map(l => l.text)
      .join('\n');
    const currentError = terminalLines
      .filter(l => l.type === 'error')
      .map(l => l.text)
      .join('\n') || null;

    try {
      const res = await fetch(`${TUTOR_API_BASE_URL}/python/explain`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${$user?.token ?? ''}`
        },
        body: JSON.stringify({ code, output: currentOutput, error: currentError })
      });

      if (!res.ok) {
        let detail = 'Erreur serveur';
        try { const e = await res.json(); detail = e.detail ?? detail; } catch (_) {}
        termAdd(`✗ Erreur ${res.status} : ${detail}`, 'error');
        statusState = 'error';
        return;
      }

      const data = await res.json();

      // Le backend renvoie { prompt, explanation, status }
      // On dispatche vers le composant parent (chat) avec le prompt prêt
      dispatch('explain', {
        code,
        output: currentOutput,
        error: currentError ?? '',
        prompt: data.prompt
      });

      termAdd('✓ Envoyé au tuteur IA — réponse dans le chat', 'success');
      statusState = 'success';
      setTimeout(() => { if (statusState === 'success') statusState = 'idle'; }, 3000);

    } catch (_) {
      termAdd('⚠ Backend non disponible — vérifie que le serveur FastAPI tourne', 'info');
      termAdd('→ Lance : uvicorn main:app --reload', 'meta');
      statusState = 'error';
    } finally {
      isRunning = false;
    }
  }

  function clearAll() {
    code = '';
    termClear();
    termAdd('Terminal effacé', 'meta');
    statusState = 'idle';
    lastExecTime = '';
    updateHighlight();
    updateLineNumbers();
  }

  // ─── Lifecycle ───────────────────────────────────────────────────────────────

  onMount(() => {
    updateHighlight();
    updateLineNumbers();
  });

  // Réactif : recalcule highlight/lines quand `code` change via bind:value
  $: if (highlightEl) updateHighlight();
  $: if (lineNumsEl) updateLineNumbers();

  $: charCount = code.length;
  $: lineCount = code.split('\n').length;
</script>

<!-- ─── TEMPLATE ──────────────────────────────────────────────────────────────── -->

<div class="page">

  <!-- En-tête page -->
  <header class="page-header">
    <div class="page-title">
      <span class="page-icon">🐍</span>
      <div>
        <h1>{$i18n?.t('Python Editor') ?? 'Python Editor'}</h1>
        <p class="page-subtitle">{$i18n?.t('Write, run, and understand Python') ?? 'Écris, exécute et comprends du Python'}</p>
      </div>
    </div>
    <div class="header-actions">
      <button class="btn btn-ghost btn-sm" on:click={clearAll} title="Effacer tout">
        🗑 {$i18n?.t('Clear') ?? 'Effacer'}
      </button>
      <button
        class="btn btn-input btn-sm"
        on:click={openInputPanel}
        title="Gérer les entrées input()"
      >
        ⌨ {$i18n?.t('Inputs') ?? 'Inputs'}
        {#if detectedInputs.length > 0 && showInputPanel === false}
          <span class="input-badge">{detectedInputs.length}</span>
        {/if}
      </button>
      <button
        class="btn btn-explain btn-sm"
        on:click={explainCode}
        disabled={!code.trim() || isRunning}
        title="Expliquer avec l'IA"
      >
        ⚡ {$i18n?.t('Explain') ?? 'Expliquer'}
      </button>
      <button
        class="btn btn-run"
        on:click={runCode}
        disabled={isRunning || !code.trim()}
        title="Ctrl+Entrée"
      >
        {#if isRunning}
          <span class="spin">⟳</span> {$i18n?.t('Running...') ?? 'Exécution...'}
        {:else}
          ▶ {$i18n?.t('Execute') ?? 'Exécuter'}
        {/if}
      </button>
    </div>
  </header>

  <!-- Corps principal -->
  <div class="editor-layout">

    <!-- ── Éditeur ── -->
    <div class="editor-panel">
      <div class="panel-header">
        <span class="panel-label">main.py</span>
        <span class="char-counter" class:over={charCount > 5000}>
          {charCount} / 5000
        </span>
      </div>

      <div class="editor-body">
        <!-- Numéros de ligne -->
        <div class="line-numbers" bind:this={lineNumsEl}></div>

        <!-- Zone de code -->
        <div
          class="code-scroll"
          bind:this={codeScrollEl}
          on:scroll={syncScroll}
        >
          <div class="highlight-layer" bind:this={highlightEl}></div>
          <textarea
            bind:this={textareaEl}
            bind:value={code}
            class="code-textarea"
            spellcheck="false"
            autocomplete="off"
            autocorrect="off"
            autocapitalize="off"
            on:input={handleInput}
            on:keydown={handleKeydown}
            on:click={updateCursor}
            on:select={updateCursor}
          ></textarea>
        </div>
      </div>

      <!-- Barre de statut éditeur -->
      <div class="editor-statusbar">
        <span class="lang-badge">Python 3</span>
        <span>Ln {cursorLine}, Col {cursorCol}</span>
        <span>{lineCount} lignes</span>
        <span class="shortcut-hint"><kbd>Ctrl</kbd>+<kbd>↵</kbd> pour exécuter</span>
      </div>
    </div>

    <!-- ── Terminal ── -->
    <div class="terminal-panel">
      <div class="panel-header">
        <span class="panel-label">terminal</span>
        {#if lastExecTime}
          <span class="exec-badge">⚡ {lastExecTime}</span>
        {/if}
      </div>

      <div class="terminal-body" bind:this={terminalEl}>
        {#if terminalLines.length === 0}
          <div class="terminal-empty">
            <span class="terminal-empty-icon">▶</span>
            <span>Lance le code pour voir les résultats</span>
          </div>
        {:else}
          {#each terminalLines as line}
            {#if line.type === 'blank'}
              <div class="t-blank">&nbsp;</div>
            {:else}
              <div class="t-line t-{line.type}">{line.text}</div>
            {/if}
          {/each}
          <div class="t-cursor"></div>
        {/if}
      </div>

      <!-- Barre de statut terminal -->
      <div class="terminal-statusbar" class:running={statusState === 'running'} class:success={statusState === 'success'} class:error={statusState === 'error'}>
        {#if statusState === 'running'}
          <span class="spin">⟳</span> exécution en cours…
        {:else if statusState === 'success'}
          ✓ terminé avec succès
        {:else if statusState === 'error'}
          ✗ erreur détectée
        {:else}
          prêt
        {/if}
      </div>
    </div>

  </div>

  <!-- Panneau stdin -->
  {#if showInputPanel}
    <div class="stdin-panel">
      <div class="stdin-header">
        <span class="stdin-title">⌨ Valeurs pour <code>input()</code></span>
        <div style="display:flex;gap:6px;align-items:center">
          <button class="btn btn-sm" on:click={addInputRow}>+ Ajouter</button>
          <button class="btn btn-sm" on:click={() => { detectedInputs = detectInputs(code); }}>↺ Scanner</button>
          <button class="btn btn-ghost btn-sm" on:click={closeInputPanel}>✕ Fermer</button>
        </div>
      </div>
      <div class="stdin-body">
        {#if detectedInputs.length === 0}
          <p class="stdin-empty">Aucun <code>input()</code> détecté — clique sur "Scanner" ou "+ Ajouter"</p>
        {:else}
          {#each detectedInputs as inp, i}
            <div class="stdin-row">
              <span class="stdin-order">#{i + 1}</span>
              {#if inp.prompt}
                <span class="stdin-prompt-label">{inp.prompt}</span>
              {:else}
                <input
                  type="text"
                  class="stdin-prompt-edit"
                  bind:value={inp.prompt}
                  placeholder="Libellé (optionnel)"
                />
              {/if}
              <span class="stdin-arrow">→</span>
              <input
                type="text"
                class="stdin-value"
                bind:value={inp.value}
                placeholder="Valeur à injecter..."
                on:keydown={(e) => e.key === 'Enter' && runCode()}
              />
              <button class="stdin-del" on:click={() => removeInputRow(i)} title="Supprimer">✕</button>
            </div>
          {/each}
        {/if}
      </div>
      <div class="stdin-footer">
        <span class="stdin-hint">
          Les valeurs sont injectées dans l'ordre des appels <code>input()</code> via stdin.
        </span>
        <button class="btn btn-run btn-sm" on:click={() => { closeInputPanel(); runCode(); }}>
          ▶ Exécuter avec ces valeurs
        </button>
      </div>
    </div>
  {/if}

  <!-- Note backend -->
  <div class="backend-notice">
    <span class="notice-icon">✓</span>
    <span>
      Backend local : <code>http://localhost:8000/api/v1/python</code> —
      assure-toi que <code>TUTOR_API_BASE_URL = "http://localhost:8000/api/v1"</code> dans <code>$lib/constants.ts</code>
      et que le CORS autorise ton frontend (voir ci-dessous)
    </span>
  </div>

</div>

<!-- ─── STYLES ─────────────────────────────────────────────────────────────────── -->
<style>
  /* ── Variables ── */
  :root {
    --ed-bg: #0d1117;
    --ed-bg2: #161b22;
    --ed-bg3: #21262d;
    --ed-bg4: #30363d;
    --ed-border: #30363d;
    --ed-border2: #484f58;
    --ed-text: #e6edf3;
    --ed-text2: #8b949e;
    --ed-text3: #6e7681;
    --ed-green: #3fb950;
    --ed-green-bg: #238636;
    --ed-green-dk: #1a7f37;
    --ed-blue: #58a6ff;
    --ed-blue-bg: #1f6feb;
    --ed-red: #f85149;
    --ed-red-dk: #da3633;
    --ed-yellow: #e3b341;
    --ed-purple: #bc8cff;
    --ed-cyan: #79c0ff;
    --ed-orange: #ffa657;
    --ed-pink: #ff7b72;
    --line-h: 20px;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  }

  /* ── Page ── */
  .page {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--ed-bg);
    color: var(--ed-text);
    font-family: var(--font-mono);
    overflow: hidden;
  }

  /* ── Header ── */
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    height: 60px;
    background: var(--ed-bg2);
    border-bottom: 1px solid var(--ed-border);
    flex-shrink: 0;
  }

  .page-title {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .page-icon {
    font-size: 24px;
  }

  .page-title h1 {
    font-size: 15px;
    font-weight: 600;
    color: var(--ed-text);
    margin: 0;
    line-height: 1;
  }

  .page-subtitle {
    font-size: 11px;
    color: var(--ed-text3);
    margin: 2px 0 0;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* ── Boutons ── */
  .btn {
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 500;
    padding: 6px 14px;
    border-radius: 6px;
    border: 1px solid var(--ed-border2);
    cursor: pointer;
    transition: all 0.15s;
    background: var(--ed-bg3);
    color: var(--ed-text2);
    line-height: 1;
  }
  .btn:hover:not(:disabled) {
    background: var(--ed-bg4);
    color: var(--ed-text);
    border-color: var(--ed-text3);
  }
  .btn:active:not(:disabled) { transform: scale(0.97); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-sm { padding: 5px 11px; font-size: 11px; }

  .btn-run {
    background: var(--ed-green-bg);
    border-color: var(--ed-green-dk);
    color: #fff;
  }
  .btn-run:hover:not(:disabled) {
    background: var(--ed-green-dk);
    border-color: var(--ed-green);
  }

  .btn-explain {
    color: var(--ed-purple);
    border-color: #6e40c9;
  }
  .btn-explain:hover:not(:disabled) {
    background: #1c1240;
    border-color: var(--ed-purple);
    color: var(--ed-purple);
  }

  .btn-ghost { color: var(--ed-red); border-color: var(--ed-red-dk); }
  .btn-ghost:hover:not(:disabled) {
    background: #2d1b1b;
    border-color: var(--ed-red);
    color: var(--ed-red);
  }

  /* ── Layout ── */
  .editor-layout {
    display: flex;
    flex: 1;
    overflow: hidden;
    min-height: 0;
  }

  .editor-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--ed-border);
    min-width: 0;
    overflow: hidden;
  }

  .terminal-panel {
    width: 40%;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    background: var(--ed-bg);
    min-width: 280px;
    overflow: hidden;
  }

  /* ── Panel headers ── */
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 14px;
    height: 34px;
    background: var(--ed-bg2);
    border-bottom: 1px solid var(--ed-border);
    flex-shrink: 0;
  }

  .panel-label {
    font-size: 11px;
    color: var(--ed-text3);
    text-transform: uppercase;
    letter-spacing: 0.8px;
  }

  .char-counter {
    font-size: 11px;
    color: var(--ed-text3);
  }
  .char-counter.over { color: var(--ed-red); }

  .exec-badge {
    font-size: 11px;
    color: var(--ed-green);
    background: #0d2818;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid var(--ed-green-dk);
  }

  /* ── Éditeur ── */
  .editor-body {
    flex: 1;
    display: flex;
    overflow: hidden;
    background: var(--ed-bg);
  }

  .line-numbers {
    width: 46px;
    flex-shrink: 0;
    padding: 12px 0;
    text-align: right;
    background: var(--ed-bg);
    border-right: 1px solid var(--ed-border);
    overflow: hidden;
    color: var(--ed-text3);
    font-size: 13px;
    line-height: var(--line-h);
    user-select: none;
  }

  :global(.lnum) {
    display: block;
    height: var(--line-h);
    padding-right: 10px;
  }

  .code-scroll {
    flex: 1;
    overflow: auto;
    position: relative;
  }

  .code-scroll::-webkit-scrollbar { width: 8px; height: 8px; }
  .code-scroll::-webkit-scrollbar-track { background: var(--ed-bg); }
  .code-scroll::-webkit-scrollbar-thumb { background: var(--ed-bg4); border-radius: 4px; }
  .code-scroll::-webkit-scrollbar-thumb:hover { background: var(--ed-border2); }

  .highlight-layer {
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    min-height: 100%;
    padding: 12px 14px;
    font-family: var(--font-mono);
    font-size: 13px;
    line-height: var(--line-h);
    white-space: pre;
    pointer-events: none;
    z-index: 1;
    overflow: hidden;
    color: var(--ed-text);
  }

  .code-textarea {
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    min-height: 100%;
    padding: 12px 14px;
    background: transparent;
    color: transparent;
    caret-color: var(--ed-text);
    font-family: var(--font-mono);
    font-size: 13px;
    line-height: var(--line-h);
    border: none;
    outline: none;
    resize: none;
    white-space: pre;
    overflow: hidden;
    tab-size: 4;
    z-index: 2;
  }

  /* ── Barre de statut éditeur ── */
  .editor-statusbar {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 0 14px;
    height: 28px;
    background: var(--ed-bg2);
    border-top: 1px solid var(--ed-border);
    font-size: 11px;
    color: var(--ed-text3);
    flex-shrink: 0;
  }

  .lang-badge {
    background: var(--ed-blue-bg);
    color: var(--ed-blue);
    padding: 1px 7px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.3px;
  }

  .shortcut-hint {
    margin-left: auto;
  }

  kbd {
    background: var(--ed-bg4);
    border: 1px solid var(--ed-border2);
    border-radius: 3px;
    padding: 0 4px;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--ed-text2);
  }

  /* ── Terminal ── */
  .terminal-body {
    flex: 1;
    overflow-y: auto;
    padding: 12px 14px;
    font-size: 12.5px;
    line-height: 1.65;
    min-height: 0;
  }

  .terminal-body::-webkit-scrollbar { width: 6px; }
  .terminal-body::-webkit-scrollbar-track { background: transparent; }
  .terminal-body::-webkit-scrollbar-thumb { background: var(--ed-bg4); border-radius: 3px; }

  .terminal-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 8px;
    color: var(--ed-text3);
    font-size: 12px;
  }

  .terminal-empty-icon {
    font-size: 28px;
    opacity: 0.3;
  }

  .t-line { white-space: pre-wrap; word-break: break-all; }
  .t-blank { height: var(--line-h); }
  .t-prompt { color: var(--ed-green); user-select: none; }
  .t-output { color: var(--ed-text); }
  .t-error { color: var(--ed-red); }
  .t-info { color: var(--ed-text2); }
  .t-success { color: var(--ed-green); }
  .t-meta { color: var(--ed-text3); font-size: 11px; }

  .t-cursor {
    display: inline-block;
    width: 7px; height: 14px;
    background: var(--ed-green);
    vertical-align: -3px;
    animation: blink 1.1s step-end infinite;
  }

  @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

  /* ── Barre de statut terminal ── */
  .terminal-statusbar {
    padding: 0 14px;
    height: 28px;
    display: flex;
    align-items: center;
    font-size: 11px;
    background: var(--ed-bg3);
    border-top: 1px solid var(--ed-border);
    color: var(--ed-text3);
    flex-shrink: 0;
    transition: background 0.2s, color 0.2s;
  }
  .terminal-statusbar.running {
    background: var(--ed-blue-bg);
    color: #fff;
  }
  .terminal-statusbar.success {
    background: var(--ed-green-bg);
    color: #fff;
  }
  .terminal-statusbar.error {
    background: var(--ed-red-dk);
    color: #fff;
  }

  /* ── Notice backend ── */
  .backend-notice {
    padding: 7px 20px;
    background: #111820;
    border-top: 1px solid var(--ed-border);
    font-size: 11px;
    color: var(--ed-text3);
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .notice-icon {
    color: var(--ed-blue);
  }

  code {
    background: var(--ed-bg3);
    padding: 1px 5px;
    border-radius: 3px;
    color: var(--ed-cyan);
    font-family: var(--font-mono);
  }

  /* ── Coloration syntaxique ── */
  :global(.kw) { color: var(--ed-pink); }
  :global(.bi) { color: var(--ed-orange); }
  :global(.st) { color: var(--ed-green); }
  :global(.fs) { color: #89d185; }
  :global(.nm) { color: var(--ed-cyan); }
  :global(.cm) { color: var(--ed-text3); font-style: italic; }
  :global(.fn) { color: var(--ed-blue); }
  :global(.sp) { color: var(--ed-yellow); }
  :global(.op) { color: var(--ed-text2); }

  .btn-input {
    color: var(--ed-cyan);
    border-color: #1a4a6b;
    position: relative;
  }
  .btn-input:hover:not(:disabled) {
    background: #0d2233;
    border-color: var(--ed-cyan);
  }

  .input-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--ed-cyan);
    color: var(--ed-bg);
    font-size: 9px;
    font-weight: 700;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    margin-left: 4px;
  }

  /* ── Panneau stdin ── */
  .stdin-panel {
    background: var(--ed-bg2);
    border-top: 1px solid var(--ed-border);
    border-bottom: 1px solid var(--ed-border);
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    max-height: 220px;
  }

  .stdin-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    border-bottom: 1px solid var(--ed-border);
    background: var(--ed-bg3);
  }

  .stdin-title {
    font-size: 12px;
    font-weight: 500;
    color: var(--ed-cyan);
  }

  .stdin-body {
    flex: 1;
    overflow-y: auto;
    padding: 10px 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .stdin-body::-webkit-scrollbar { width: 4px; }
  .stdin-body::-webkit-scrollbar-thumb { background: var(--ed-bg4); border-radius: 2px; }

  .stdin-empty {
    font-size: 12px;
    color: var(--ed-text3);
    text-align: center;
    padding: 8px 0;
  }

  .stdin-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .stdin-order {
    font-size: 10px;
    color: var(--ed-text3);
    min-width: 20px;
    text-align: right;
  }

  .stdin-prompt-label {
    font-size: 12px;
    color: var(--ed-yellow);
    min-width: 120px;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    background: var(--ed-bg3);
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid var(--ed-border);
  }

  .stdin-prompt-edit {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--ed-yellow);
    background: var(--ed-bg3);
    border: 1px solid var(--ed-border2);
    border-radius: 4px;
    padding: 4px 8px;
    width: 160px;
    outline: none;
  }
  .stdin-prompt-edit:focus { border-color: var(--ed-yellow); }

  .stdin-arrow {
    color: var(--ed-text3);
    font-size: 12px;
  }

  .stdin-value {
    flex: 1;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--ed-text);
    background: var(--ed-bg);
    border: 1px solid var(--ed-border2);
    border-radius: 4px;
    padding: 4px 10px;
    outline: none;
    transition: border-color 0.15s;
  }
  .stdin-value:focus { border-color: var(--ed-cyan); }
  .stdin-value::placeholder { color: var(--ed-text3); }

  .stdin-del {
    background: none;
    border: none;
    color: var(--ed-text3);
    cursor: pointer;
    font-size: 12px;
    padding: 2px 4px;
    border-radius: 3px;
    line-height: 1;
    transition: color 0.1s;
  }
  .stdin-del:hover { color: var(--ed-red); }

  .stdin-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    border-top: 1px solid var(--ed-border);
    background: var(--ed-bg3);
  }

  .stdin-hint {
    font-size: 10px;
    color: var(--ed-text3);
  }

  /* ── Spinner ── */
  .spin {
    display: inline-block;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>