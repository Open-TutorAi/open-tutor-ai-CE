<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import * as Blockly from 'blockly';
  import { pythonGenerator } from 'blockly/python';
  import 'blockly/blocks';

  let context = { course: '', objectives: '', prerequisites: '', level: 'beginner' };
  let exercise: any = null;
  let generatingExercise = false;
  let generateError = '';
  let showBlockly = false;

  let blocklyDiv: HTMLDivElement;
  let workspace: any = null;
  let generatedCode = '';

  let consoleOutput = '';
  let running = false;
  let feedback = '';
  let score: number | null = null;
  let submitting = false;

  const LEVELS = ['beginner', 'intermediate', 'advanced'];
  const LEVEL_LABELS: Record<string, string> = {
    beginner: '🌱 Débutant',
    intermediate: '🔥 Intermédiaire',
    advanced: '⚡ Avancé'
  };
  let consecutiveSuccesses = 0;
  let levelUpMessage = '';

  onMount(async () => {
    if (browser) {
      const saved = localStorage.getItem('blocklyContext');
      if (saved) try { context = JSON.parse(saved); } catch {}
      await generateExercise();
    }
  });

  onDestroy(() => { if (workspace) try { workspace.dispose(); } catch {} });

  function normalizeExercise(raw: any) {
    return {
      title: raw.title || raw.titre || raw.Titre || 'Exercice Python',
      description: raw.description || raw.Description || '',
      test_cases: raw.test_cases || raw.testing_cases || [],
      hints: raw.hints || raw.indices || []
    };
  }

  async function generateExercise() {
    generatingExercise = true;
    generateError = '';
    exercise = null;
    showBlockly = false;
    score = null; feedback = ''; consoleOutput = ''; generatedCode = '';
    try {
      const res = await fetch('/api/blockly/generate/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level: context.level, course: context.course, objectives: context.objectives, prerequisites: context.prerequisites })
      });
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of decoder.decode(value).split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              if (event.type === 'chunk') buffer += event.content;
              if (event.type === 'done') {
                const match = buffer.match(/\{[\s\S]*\}/);
                if (match) exercise = normalizeExercise(JSON.parse(match[0]));
              }
            } catch {}
          }
        }
      }
      if (!exercise) generateError = 'Impossible de générer. Réessayez.';
    } catch { generateError = 'Erreur réseau.'; }
    generatingExercise = false;
  }

  async function startBlockly() {
    showBlockly = true;
    await new Promise(r => setTimeout(r, 200));
    initWorkspace();
  }

  function getToolbox(level: string) {
    return {
      kind: 'categoryToolbox',
      contents: [
        {
          kind: 'category', name: 'Logique', colour: '#5C81A6',
          contents: [
            { kind: 'block', type: 'controls_if' },
            { kind: 'block', type: 'logic_compare' },
            { kind: 'block', type: 'logic_operation' },
            { kind: 'block', type: 'logic_boolean' },
            { kind: 'block', type: 'logic_negate' },
          ]
        },
        {
          kind: 'category', name: 'Boucles', colour: '#5CA65C',
          contents: [
            { kind: 'block', type: 'controls_repeat_ext' },
            { kind: 'block', type: 'controls_whileUntil' },
            { kind: 'block', type: 'controls_for' },
          ]
        },
        {
          kind: 'category', name: 'Maths', colour: '#5C68A6',
          contents: [
            { kind: 'block', type: 'math_number' },
            { kind: 'block', type: 'math_arithmetic' },
            { kind: 'block', type: 'math_modulo' },
            { kind: 'block', type: 'math_round' },
          ]
        },
        {
          kind: 'category', name: 'Texte', colour: '#5CA68D',
          contents: [
            { kind: 'block', type: 'text' },
            { kind: 'block', type: 'text_print' },
            { kind: 'block', type: 'text_join' },
          ]
        },
        { kind: 'category', name: 'Variables', colour: '#A65C81', custom: 'VARIABLE' },
        ...(level !== 'beginner' ? [{
          kind: 'category', name: 'Listes', colour: '#745CA6',
          contents: [
            { kind: 'block', type: 'lists_create_with' },
            { kind: 'block', type: 'lists_length' },
            { kind: 'block', type: 'lists_getIndex' },
            { kind: 'block', type: 'lists_setIndex' },
          ]
        }] : []),
        ...(level === 'advanced' ? [
          { kind: 'category', name: 'Fonctions', colour: '#9A5CA6', custom: 'PROCEDURE' }
        ] : []),
      ]
    };
  }

  function initWorkspace() {
    if (!blocklyDiv) return;
    if (workspace) { workspace.dispose(); workspace = null; }

    workspace = Blockly.inject(blocklyDiv, {
      toolbox: getToolbox(context.level),
      grid: { spacing: 20, length: 3, colour: '#e0e0e0', snap: true },
      zoom: { controls: true, wheel: true, startScale: 1.0, maxScale: 2, minScale: 0.5 },
      trashcan: true,
      scrollbars: true,
    });

    workspace.addChangeListener(() => {
      try {
        generatedCode = pythonGenerator.workspaceToCode(workspace) || '';
      } catch {}
    });
  }

  async function runCode() {
    if (!generatedCode.trim()) { consoleOutput = '⚠️ Glissez des blocs d\'abord !'; return; }
    running = true; consoleOutput = '⏳ Exécution...';
    try {
      const res = await fetch('/api/blockly/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ python_code: generatedCode })
      });
      const data = await res.json();
      consoleOutput = data.timed_out ? '⏰ Délai dépassé !' :
        (data.stdout || '') + (data.stderr ? '\n⚠️ ' + data.stderr : '') ||
        (data.error ? '❌ ' + data.error : '(aucune sortie)');
    } catch { consoleOutput = '❌ Erreur réseau'; }
    running = false;
  }

  async function submitCode() {
    if (!generatedCode.trim()) { consoleOutput = '⚠️ Ajoutez des blocs !'; return; }
    submitting = true; feedback = ''; score = null;
    try {
      const res = await fetch('/api/blockly/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ python_code: generatedCode, level: context.level })
      });
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of decoder.decode(value).split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              if (event.type === 'score') {
                score = event.value;
                if (score !== null && score >= 70) { consecutiveSuccesses++; if (consecutiveSuccesses >= 2) checkLevelUp(); }
                else consecutiveSuccesses = 0;
              }
              if (event.type === 'feedback') feedback += event.content;
            } catch {}
          }
        }
      }
    } catch { feedback = 'Erreur soumission.'; }
    submitting = false;
  }

  function checkLevelUp() {
    const idx = LEVELS.indexOf(context.level);
    if (idx < LEVELS.length - 1) {
      context.level = LEVELS[idx + 1];
      consecutiveSuccesses = 0;
      levelUpMessage = `🎉 Niveau suivant : ${LEVEL_LABELS[context.level]} !`;
      if (browser) {
        const ctx = JSON.parse(localStorage.getItem('blocklyContext') || '{}');
        ctx.level = context.level;
        localStorage.setItem('blocklyContext', JSON.stringify(ctx));
      }
      if (workspace) workspace.updateToolbox(getToolbox(context.level));
      setTimeout(() => { levelUpMessage = ''; generateExercise(); }, 3000);
    } else {
      levelUpMessage = '🏆 Niveau maximum ! Expert !';
      setTimeout(() => levelUpMessage = '', 5000);
    }
  }

  function resetWorkspace() {
    if (workspace) workspace.clear();
    generatedCode = ''; consoleOutput = '';
  }
</script>

{#if !showBlockly}
<div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
  <div class="w-full max-w-2xl">
    <div class="flex items-center gap-3 mb-6">
      <button on:click={() => goto('/student/dashboard')} class="p-2 rounded-full bg-white dark:bg-gray-700 shadow hover:shadow-md transition text-gray-500 hover:text-gray-800 dark:hover:text-white">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
      </button>
      <div>
        <h1 class="text-xl font-bold text-gray-900 dark:text-white">🧩 {context.course || 'Exercice Blockly'}</h1>
        <p class="text-sm text-gray-500">{LEVEL_LABELS[context.level]}</p>
      </div>
    </div>
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
      <div class="h-2 {context.level === 'beginner' ? 'bg-gradient-to-r from-emerald-400 to-teal-500' : context.level === 'intermediate' ? 'bg-gradient-to-r from-orange-400 to-amber-500' : 'bg-gradient-to-r from-purple-500 to-indigo-600'}"></div>
      <div class="p-6">
        {#if generatingExercise}
          <div class="flex flex-col items-center py-12 gap-4">
            <div class="w-14 h-14 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <p class="text-gray-600 dark:text-gray-300 font-semibold text-lg">L'IA génère votre exercice...</p>
            <p class="text-sm text-gray-400">📚 <strong>{context.course}</strong></p>
          </div>
        {:else if generateError}
          <div class="text-center py-8">
            <p class="text-red-500 mb-4">{generateError}</p>
            <button on:click={generateExercise} class="px-6 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition font-semibold">🔄 Réessayer</button>
          </div>
        {:else if exercise}
          <div class="flex items-start justify-between gap-4 mb-4">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{exercise.title}</h2>
            <span class="flex-shrink-0 px-3 py-1 text-xs font-bold rounded-full {context.level === 'beginner' ? 'bg-emerald-100 text-emerald-700' : context.level === 'intermediate' ? 'bg-orange-100 text-orange-700' : 'bg-purple-100 text-purple-700'}">
              {LEVEL_LABELS[context.level]}
            </span>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 mb-4">
            <p class="text-gray-700 dark:text-gray-200 leading-relaxed">{exercise.description}</p>
          </div>
          {#if context.objectives}
          <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 rounded-xl p-3 mb-4">
            <p class="text-xs font-bold text-blue-700 mb-1">🎯 Objectifs</p>
            <p class="text-sm text-blue-600">{context.objectives}</p>
          </div>
          {/if}
          {#if exercise.hints?.length}
          <details class="mb-6 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 rounded-xl overflow-hidden">
            <summary class="px-4 py-3 cursor-pointer text-sm font-semibold text-amber-700 select-none">💡 Indices ({exercise.hints.length})</summary>
            <ul class="px-4 pb-3 space-y-1">
              {#each exercise.hints as hint, i}<li class="text-sm text-amber-600">{i+1}. {hint}</li>{/each}
            </ul>
          </details>
          {/if}
          <div class="flex gap-3">
            <button on:click={startBlockly} class="flex-1 py-3.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold rounded-xl shadow-md transition-all flex items-center justify-center gap-2">
              🧩 Ouvrir l'éditeur Blockly
            </button>
            <button on:click={generateExercise} class="px-5 py-3.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 text-gray-700 dark:text-gray-300 font-semibold rounded-xl transition">
              🔄 Autre
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>

{:else}
<div class="flex flex-col h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">
  <div class="flex items-center justify-between px-4 py-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm flex-shrink-0">
    <div class="flex items-center gap-3">
      <button on:click={() => showBlockly = false} class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition text-gray-500">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
      </button>
      <div>
        <h1 class="font-bold text-gray-900 dark:text-white text-sm">{exercise?.title}</h1>
        <p class="text-xs text-gray-500">{LEVEL_LABELS[context.level]}</p>
      </div>
    </div>
    <div class="flex items-center gap-2">
      {#if levelUpMessage}<span class="text-xs font-bold text-emerald-500 animate-pulse">{levelUpMessage}</span>{/if}
      <div class="flex items-center gap-1">
        {#each LEVELS as lvl}
          <div class="rounded-full transition-all {context.level === lvl ? 'w-3 h-3 bg-emerald-500' : LEVELS.indexOf(lvl) < LEVELS.indexOf(context.level) ? 'w-2 h-2 bg-emerald-300' : 'w-2 h-2 bg-gray-300'}"></div>
        {/each}
      </div>
      <span class="text-xs px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full font-medium">{LEVEL_LABELS[context.level]}</span>
      <button on:click={generateExercise} class="px-3 py-1.5 text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition">🔄 Nouvel exercice</button>
    </div>
  </div>

  <div class="flex flex-1 overflow-hidden">
    <div class="flex flex-col w-1/2 border-r border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-b border-blue-100 flex-shrink-0">
        <div class="flex items-start gap-2">
          <span class="text-lg">📝</span>
          <div>
            <p class="text-sm font-bold text-blue-900 dark:text-blue-100">{exercise?.title}</p>
            <p class="text-xs text-blue-700 dark:text-blue-300 mt-0.5 leading-relaxed">{exercise?.description}</p>
            {#if exercise?.hints?.length}
            <details class="mt-1">
              <summary class="text-xs text-amber-600 cursor-pointer font-medium">💡 Indices</summary>
              <ul class="mt-1">{#each exercise.hints as h}<li class="text-xs text-amber-500">• {h}</li>{/each}</ul>
            </details>
            {/if}
          </div>
        </div>
      </div>
      <div class="flex-1 overflow-hidden" bind:this={blocklyDiv}></div>
    </div>

    <div class="flex flex-col w-1/2 overflow-hidden">
      <div class="flex flex-col border-b border-gray-700" style="height:35%">
        <div class="flex items-center justify-between px-3 py-1.5 bg-gray-800 flex-shrink-0">
          <span class="text-xs font-semibold text-gray-300 flex items-center gap-1.5"><span class="w-2 h-2 bg-yellow-400 rounded-full inline-block"></span>Python généré</span>
          <button on:click={resetWorkspace} class="text-xs text-gray-400 hover:text-red-400 transition">🗑 Reset</button>
        </div>
        <pre class="flex-1 overflow-auto p-3 text-xs font-mono bg-gray-900 text-green-300 leading-relaxed whitespace-pre-wrap">{generatedCode || '# Glissez des blocs depuis la gauche...'}</pre>
      </div>

      <div class="flex flex-col border-b border-gray-700" style="height:25%">
        <div class="flex items-center justify-between px-3 py-1.5 bg-gray-700 flex-shrink-0">
          <span class="text-xs font-semibold text-gray-300 flex items-center gap-1.5"><span class="w-2 h-2 bg-green-400 rounded-full inline-block"></span>Console</span>
          <div class="flex gap-2">
            <button on:click={runCode} disabled={running} class="px-3 py-1 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded transition disabled:opacity-60 flex items-center gap-1">
              {#if running}<div class="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>{:else}▶{/if} Exécuter
            </button>
            <button on:click={() => consoleOutput = ''} class="text-xs text-gray-400 hover:text-white px-1">✕</button>
          </div>
        </div>
        <pre class="flex-1 overflow-auto p-3 text-xs font-mono bg-gray-800 text-gray-100 whitespace-pre-wrap">{consoleOutput || '// Cliquez ▶ pour exécuter'}</pre>
      </div>

      <div class="flex flex-col flex-1 overflow-hidden bg-white dark:bg-gray-800">
        <div class="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <span class="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
            🤖 Feedback IA
            {#if score !== null}
              <span class="px-2 py-0.5 rounded-full text-xs font-bold {score >= 70 ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}">{score}/100</span>
            {/if}
          </span>
          <button on:click={submitCode} disabled={submitting} class="px-3 py-1.5 text-xs font-bold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg transition disabled:opacity-60 flex items-center gap-1.5">
            {#if submitting}<div class="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>Analyse...{:else}📤 Soumettre{/if}
          </button>
        </div>
        <div class="flex-1 overflow-auto p-3">
          {#if submitting && !feedback}
            <div class="flex items-center gap-2 text-gray-400"><div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div><span class="text-xs">Analyse en cours...</span></div>
          {:else if feedback}
            <div class="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-3"><p class="text-xs text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">{feedback}</p></div>
          {:else}
            <p class="text-xs text-gray-400 italic text-center mt-4">Glissez des blocs → Exécutez → Soumettez</p>
          {/if}
        </div>
      </div>
    </div>
  </div>
</div>
{/if}
