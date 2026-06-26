
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import * as Blockly from 'blockly';
  import { pythonGenerator } from 'blockly/python';
  import 'blockly/blocks';

  // ── Types ─────────────────────────────────────────────────
  interface Exercise {
    title: string;
    description: string;
    test_cases: { expected_output: string }[];
    hints: string[];
  }

  // ── Constantes ────────────────────────────────────────────
  const LEVELS = ['beginner', 'intermediate', 'advanced'] as const;
  type Level = typeof LEVELS[number];

  const LEVEL_CONFIG: Record<Level, { label: string; emoji: string; colorClass: string }> = {
    beginner:     { label: 'Débutant',      emoji: '🌱', colorClass: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' },
    intermediate: { label: 'Intermédiaire', emoji: '🔥', colorClass: 'bg-orange-100  text-orange-700  dark:bg-orange-900/30  dark:text-orange-300'  },
    advanced:     { label: 'Avancé',        emoji: '⚡', colorClass: 'bg-purple-100  text-purple-700  dark:bg-purple-900/30  dark:text-purple-300'  },
  };

  // ── État global ───────────────────────────────────────────
  let ctx = {
    course:        '',
    objectives:    '',
    prerequisites: '',
    level:         'beginner' as Level,
  };

  // Vue active
  let view: 'card' | 'editor' = 'card';

  // Exercice
  let exercise: Exercise | null = null;
  let generatingExercise = false;
  let generateError = '';

  // Blockly
  let blocklyDiv: HTMLDivElement;
  let workspace: Blockly.WorkspaceSvg | null = null;
  let generatedCode = '';

  // Console
  let consoleOutput = '';
  let running = false;

  // Feedback
  let feedback = '';
  let score: number | null = null;
  let submitting = false;

  // Progression (US-B06)
  let consecutiveSuccesses = 0;
  let levelUpMessage = '';

  // ── Cycle de vie ──────────────────────────────────────────
  onMount(async () => {
    if (!browser) return;
    const saved = localStorage.getItem('blocklyContext');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        ctx = { ...ctx, ...parsed };
      } catch {}
    }
    await loadExercise();
  });

  onDestroy(() => {
    if (workspace) {
      try { workspace.dispose(); } catch {}
    }
  });

  // ── Normalisation JSON Ollama ─────────────────────────────
  function normalizeExercise(raw: Record<string, unknown>): Exercise {
    return {
      title:       String(raw.title || raw.titre || 'Exercice Python'),
      description: String(raw.description || ''),
      test_cases:  Array.isArray(raw.test_cases)   ? raw.test_cases   :
                   Array.isArray(raw.testing_cases) ? raw.testing_cases : [],
      hints:       Array.isArray(raw.hints)   ? raw.hints   :
                   Array.isArray(raw.indices) ? raw.indices : [],
    };
  }

  // ── US-B02 : Génération exercice ─────────────────────────
  async function loadExercise() {
    generatingExercise = true;
    generateError = '';
    exercise = null;
    view = 'card';
    score = null;
    feedback = '';
    consoleOutput = '';
    generatedCode = '';

    try {
      const res = await fetch('/api/blockly/generate/stream', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          level:         ctx.level,
          course:        ctx.course,
          objectives:    ctx.objectives,
          prerequisites: ctx.prerequisites,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader  = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        for (const line of decoder.decode(value, { stream: true }).split('\n')) {
          if (!line.startsWith('data: ')) continue;
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

      if (!exercise) generateError = 'Impossible de générer. Réessayez.';

    } catch {
      generateError = 'Erreur réseau. Vérifiez que le backend tourne sur :8080.';
    }

    generatingExercise = false;
  }

  // ── US-B03 : Ouvrir l'éditeur Blockly ────────────────────
  async function openEditor() {
    view = 'editor';
    await new Promise(r => setTimeout(r, 150));
    initWorkspace();
  }

  function getToolbox(level: Level): object {
    const base = [
      {
        kind: 'category', name: 'Logique', colour: '#4F87C4',
        contents: [
          { kind: 'block', type: 'controls_if' },
          { kind: 'block', type: 'controls_ifelse' },
          { kind: 'block', type: 'logic_compare' },
          { kind: 'block', type: 'logic_operation' },
          { kind: 'block', type: 'logic_boolean' },
          { kind: 'block', type: 'logic_negate' },
        ],
      },
      {
        kind: 'category', name: 'Boucles', colour: '#5BA55B',
        contents: [
          {
            kind: 'block', type: 'controls_repeat_ext',
            inputs: { TIMES: { block: { type: 'math_number', fields: { NUM: 10 } } } },
          },
          { kind: 'block', type: 'controls_whileUntil' },
          {
            kind: 'block', type: 'controls_for',
            inputs: {
              FROM: { block: { type: 'math_number', fields: { NUM: 1  } } },
              TO:   { block: { type: 'math_number', fields: { NUM: 10 } } },
              BY:   { block: { type: 'math_number', fields: { NUM: 1  } } },
            },
          },
        ],
      },
      {
        kind: 'category', name: 'Maths', colour: '#5B67A5',
        contents: [
          { kind: 'block', type: 'math_number',     fields: { NUM: 0 } },
          { kind: 'block', type: 'math_arithmetic' },
          { kind: 'block', type: 'math_single'     },
          { kind: 'block', type: 'math_modulo'     },
          { kind: 'block', type: 'math_round'      },
        ],
      },
      {
        kind: 'category', name: 'Texte', colour: '#5BA58C',
        contents: [
          { kind: 'block', type: 'text',       fields: { TEXT: 'bonjour' } },
          { kind: 'block', type: 'text_print'  },
          { kind: 'block', type: 'text_join'   },
          { kind: 'block', type: 'text_length' },
        ],
      },
      { kind: 'category', name: 'Variables', colour: '#A55B80', custom: 'VARIABLE' },
    ];

    const lists = level !== 'beginner'
      ? [{
          kind: 'category', name: 'Listes', colour: '#745CA6',
          contents: [
            { kind: 'block', type: 'lists_create_with' },
            { kind: 'block', type: 'lists_repeat'      },
            { kind: 'block', type: 'lists_length'      },
            { kind: 'block', type: 'lists_getIndex'    },
            { kind: 'block', type: 'lists_setIndex'    },
          ],
        }]
      : [];

    const functions = level === 'advanced'
      ? [{ kind: 'category', name: 'Fonctions', colour: '#9A5CA6', custom: 'PROCEDURE' }]
      : [];

    return { kind: 'categoryToolbox', contents: [...base, ...lists, ...functions] };
  }

  function initWorkspace() {
    if (!blocklyDiv) return;
    if (workspace) { workspace.dispose(); workspace = null; }

    workspace = Blockly.inject(blocklyDiv, {
      toolbox:    getToolbox(ctx.level),
      grid:       { spacing: 20, length: 3, colour: '#e5e7eb', snap: true },
      zoom:       { controls: true, wheel: true, startScale: 1.0, maxScale: 2.5, minScale: 0.4 },
      trashcan:   true,
      scrollbars: true,
      sounds:     false,
    });

    workspace.addChangeListener(() => {
      try {
        generatedCode = pythonGenerator.workspaceToCode(workspace!) || '';
      } catch {}
    });
  }

  // ── US-B04 : Exécuter le code ─────────────────────────────
  async function runCode() {
    if (!generatedCode.trim()) {
      consoleOutput = '⚠️ Glissez des blocs depuis la toolbox !';
      return;
    }
    running = true;
    consoleOutput = '⏳ Exécution...';

    try {
      const res = await fetch('/api/blockly/execute', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ python_code: generatedCode }),
      });
      const data = await res.json();

      if (data.timed_out) {
        consoleOutput = '⏰ Délai dépassé (boucle infinie ?)';
      } else if (data.error && !data.stdout) {
        consoleOutput = `❌ Erreur :\n${data.error}`;
      } else {
        consoleOutput = data.stdout || '(aucune sortie)';
        if (data.stderr) consoleOutput += `\n⚠️ ${data.stderr}`;
      }
    } catch {
      consoleOutput = '❌ Service indisponible';
    }

    running = false;
  }

  // ── US-B05 : Soumettre + feedback ────────────────────────
  async function submitCode() {
    if (!generatedCode.trim()) {
      consoleOutput = '⚠️ Ajoutez des blocs avant de soumettre !';
      return;
    }
    submitting = true;
    feedback = '';
    score   = null;

    try {
      const res = await fetch('/api/blockly/submit', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ python_code: generatedCode, level: ctx.level }),
      });

      const reader  = res.body!.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        for (const line of decoder.decode(value, { stream: true }).split('\n')) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === 'score') {
              score = event.value;
              handleScore(score!);
            }
            if (event.type === 'feedback') feedback += event.content;
          } catch {}
        }
      }
    } catch {
      feedback = 'Erreur lors de la soumission.';
    }

    submitting = false;
  }

  // ── US-B06 : Progression ─────────────────────────────────
  function handleScore(s: number) {
    if (s >= 70) {
      consecutiveSuccesses += 1;
      if (consecutiveSuccesses >= 2) checkLevelUp();
    } else {
      consecutiveSuccesses = 0;
    }
  }

  function checkLevelUp() {
    const idx = LEVELS.indexOf(ctx.level);
    if (idx < LEVELS.length - 1) {
      const next = LEVELS[idx + 1];
      ctx.level = next;
      consecutiveSuccesses = 0;
      levelUpMessage = `🎉 Niveau suivant : ${LEVEL_CONFIG[next].emoji} ${LEVEL_CONFIG[next].label} !`;

      if (browser) {
        const saved = JSON.parse(localStorage.getItem('blocklyContext') || '{}');
        saved.level = next;
        localStorage.setItem('blocklyContext', JSON.stringify(saved));
      }

      if (workspace) workspace.updateToolbox(getToolbox(next));

      setTimeout(() => {
        levelUpMessage = '';
        loadExercise();
      }, 3500);
    } else {
      levelUpMessage = '🏆 Niveau maximum atteint ! Vous êtes expert Python !';
      setTimeout(() => { levelUpMessage = ''; }, 5000);
    }
  }

  function resetWorkspace() {
    if (workspace) workspace.clear();
    generatedCode = '';
    consoleOutput = '';
  }

  // ── Réactivité ────────────────────────────────────────────
  $: currentLvl = LEVEL_CONFIG[ctx.level];
</script>

<!--
  ════════════════════════════════════════════════════
  VUE 1 — Carte exercice
  ════════════════════════════════════════════════════
-->
{#if view === 'card'}
<div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50
            dark:from-gray-900 dark:to-gray-800
            flex items-start justify-center pt-10 px-4">

  <div class="w-full max-w-2xl">

    <!-- Navigation -->
    <div class="flex items-center gap-3 mb-6">
      <button
        on:click={() => goto('/student/dashboard')}
        class="p-2 rounded-xl bg-white dark:bg-gray-800 shadow
               hover:shadow-md transition text-gray-500 hover:text-gray-800
               dark:text-gray-400 dark:hover:text-white border
               border-gray-100 dark:border-gray-700"
        aria-label="Retour"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5"
             fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round"
                stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>
      <div>
        <h1 class="text-xl font-bold text-gray-900 dark:text-white">
          🧩 {ctx.course || 'Exercice Blockly'}
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Programmation visuelle Python
        </p>
      </div>
    </div>

    <!-- Carte principale -->
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden
                border border-gray-100 dark:border-gray-700">

      <!-- Barre de couleur niveau -->
      <div class="h-1.5 {
        ctx.level === 'beginner'
          ? 'bg-gradient-to-r from-emerald-400 to-teal-400'
          : ctx.level === 'intermediate'
          ? 'bg-gradient-to-r from-orange-400 to-amber-400'
          : 'bg-gradient-to-r from-purple-500 to-indigo-500'
      }"></div>

      <div class="p-6">

        <!-- Chargement -->
        {#if generatingExercise}
          <div class="flex flex-col items-center py-14 gap-4">
            <div class="w-12 h-12 border-4 border-blue-500
                        border-t-transparent rounded-full animate-spin"></div>
            <p class="font-semibold text-gray-700 dark:text-gray-200 text-lg">
              L'IA génère votre exercice...
            </p>
            <p class="text-sm text-gray-400">📚 {ctx.course || 'Python'}</p>
          </div>

        <!-- Erreur -->
        {:else if generateError}
          <div class="text-center py-10">
            <p class="text-4xl mb-4">😕</p>
            <p class="text-red-500 dark:text-red-400 mb-6 font-medium">
              {generateError}
            </p>
            <button
              on:click={loadExercise}
              class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700
                     text-white font-semibold rounded-xl transition shadow-sm"
            >
              🔄 Réessayer
            </button>
          </div>

        <!-- Exercice prêt -->
        {:else if exercise}

          <!-- Titre + badge -->
          <div class="flex items-start justify-between gap-4 mb-4">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
              {exercise.title}
            </h2>
            <span class="flex-shrink-0 px-3 py-1 rounded-full
                         text-xs font-bold {currentLvl.colorClass}">
              {currentLvl.emoji} {currentLvl.label}
            </span>
          </div>

          <!-- Description -->
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 mb-4">
            <p class="text-gray-700 dark:text-gray-200 leading-relaxed text-sm">
              {exercise.description}
            </p>
          </div>

          <!-- Objectifs -->
          {#if ctx.objectives}
            <div class="bg-blue-50 dark:bg-blue-900/20
                        border border-blue-100 dark:border-blue-800
                        rounded-xl p-3 mb-4">
              <p class="text-xs font-bold text-blue-700 dark:text-blue-300 mb-1">
                🎯 Objectifs
              </p>
              <p class="text-xs text-blue-600 dark:text-blue-400">
                {ctx.objectives}
              </p>
            </div>
          {/if}

          <!-- Indices -->
          {#if exercise.hints?.length}
            <details class="mb-6 bg-amber-50 dark:bg-amber-900/20
                           border border-amber-100 dark:border-amber-800
                           rounded-xl overflow-hidden">
              <summary class="px-4 py-3 cursor-pointer select-none
                             text-sm font-semibold
                             text-amber-700 dark:text-amber-300
                             hover:bg-amber-100 dark:hover:bg-amber-900/30
                             transition">
                💡 Indices ({exercise.hints.length})
              </summary>
              <ul class="px-4 pb-3 space-y-1.5">
                {#each exercise.hints as hint, i}
                  <li class="text-sm text-amber-600 dark:text-amber-400">
                    {i + 1}. {hint}
                  </li>
                {/each}
              </ul>
            </details>
          {/if}

          <!-- Boutons -->
          <div class="flex gap-3">
            <button
              on:click={openEditor}
              class="flex-1 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600
                     hover:from-blue-700 hover:to-indigo-700
                     text-white font-bold rounded-xl shadow-md
                     hover:shadow-lg transition-all
                     flex items-center justify-center gap-2"
            >
              🧩 Ouvrir l'éditeur Blockly
            </button>
            <button
              on:click={loadExercise}
              class="px-5 py-3.5 bg-gray-100 dark:bg-gray-700
                     hover:bg-gray-200 dark:hover:bg-gray-600
                     text-gray-700 dark:text-gray-300
                     font-semibold rounded-xl transition"
            >
              🔄 Autre
            </button>
          </div>

        {/if}
      </div>
    </div>
  </div>
</div>

<!--
  ════════════════════════════════════════════════════
  VUE 2 — Éditeur Blockly complet
  ════════════════════════════════════════════════════
-->
{:else}
<div class="flex flex-col h-screen overflow-hidden
            bg-gray-50 dark:bg-gray-900">

  <!-- ── Barre de navigation éditeur ── -->
  <header class="flex items-center justify-between px-4 py-2.5
                 bg-white dark:bg-gray-800
                 border-b border-gray-200 dark:border-gray-700
                 shadow-sm flex-shrink-0">

    <div class="flex items-center gap-3">
      <button
        on:click={() => (view = 'card')}
        class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700
               transition text-gray-500 dark:text-gray-400"
        aria-label="Retour"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5"
             fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round"
                stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>
      <div>
        <p class="font-bold text-gray-900 dark:text-white text-sm leading-tight">
          {exercise?.title || 'Exercice'}
        </p>
        <p class="text-xs text-gray-500 dark:text-gray-400">
          {ctx.course || 'Python'}
        </p>
      </div>
    </div>

    <div class="flex items-center gap-2">

      <!-- Message de niveau -->
      {#if levelUpMessage}
        <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400
                     bg-emerald-50 dark:bg-emerald-900/30 px-3 py-1
                     rounded-full border border-emerald-200
                     dark:border-emerald-800 animate-pulse">
          {levelUpMessage}
        </span>
      {/if}

      <!-- Indicateur de progression (points) -->
      <div class="flex items-center gap-1" aria-label="Progression">
        {#each LEVELS as lvl}
          <div class="rounded-full transition-all {
            ctx.level === lvl
              ? 'w-3 h-3 bg-blue-600'
              : LEVELS.indexOf(lvl) < LEVELS.indexOf(ctx.level)
              ? 'w-2 h-2 bg-blue-300'
              : 'w-2 h-2 bg-gray-300 dark:bg-gray-600'
          }"></div>
        {/each}
      </div>

      <!-- Badge niveau -->
      <span class="text-xs font-semibold px-2.5 py-1
                   rounded-full {currentLvl.colorClass}">
        {currentLvl.emoji} {currentLvl.label}
      </span>

      <!-- Succès consécutifs -->
      {#if consecutiveSuccesses > 0}
        <span class="text-xs font-semibold text-orange-600 dark:text-orange-400
                     bg-orange-50 dark:bg-orange-900/20 px-2 py-1
                     rounded-full border border-orange-200 dark:border-orange-800">
          🔥 {consecutiveSuccesses}/2
        </span>
      {/if}

      <!-- Nouvel exercice -->
      <button
        on:click={loadExercise}
        class="px-3 py-1.5 text-xs font-bold
               bg-gradient-to-r from-blue-600 to-indigo-600
               hover:from-blue-700 hover:to-indigo-700
               text-white rounded-full transition shadow-sm"
      >
        🔄 Nouvel exercice
      </button>
    </div>
  </header>

  <!-- ── Corps principal : 2 colonnes ── -->
  <main class="flex flex-1 overflow-hidden">

    <!-- ── COLONNE GAUCHE : Énoncé + Blockly ── -->
    <section class="flex flex-col w-1/2 border-r
                    border-gray-200 dark:border-gray-700 overflow-hidden">

      <!-- Énoncé compact -->
      <div class="px-4 py-3 flex-shrink-0
                  bg-blue-50 dark:bg-blue-900/20
                  border-b border-blue-100 dark:border-blue-800">
        <div class="flex items-start gap-2">
          <span class="text-lg mt-0.5 flex-shrink-0">📝</span>
          <div class="min-w-0">
            <p class="text-sm font-bold text-blue-900 dark:text-blue-100 truncate">
              {exercise?.title}
            </p>
            <p class="text-xs text-blue-700 dark:text-blue-300
                      mt-0.5 leading-relaxed line-clamp-2">
              {exercise?.description}
            </p>
            {#if exercise?.hints?.length}
              <details class="mt-1">
                <summary class="text-xs text-amber-600 dark:text-amber-400
                               cursor-pointer font-medium">
                  💡 Indices
                </summary>
                <ul class="mt-1 space-y-0.5">
                  {#each exercise.hints as h}
                    <li class="text-xs text-amber-600 dark:text-amber-400">
                      • {h}
                    </li>
                  {/each}
                </ul>
              </details>
            {/if}
          </div>
        </div>
      </div>

      <!-- Workspace Blockly (US-B03) -->
      <div class="flex-1 overflow-hidden bg-white dark:bg-gray-800"
           bind:this={blocklyDiv}>
      </div>
    </section>

    <!-- ── COLONNE DROITE : Code + Console + Feedback ── -->
    <section class="flex flex-col w-1/2 overflow-hidden">

      <!-- Code Python généré (US-B03) -->
      <div class="flex flex-col border-b border-gray-700" style="height:35%">
        <div class="flex items-center justify-between px-3 py-2
                    bg-gray-800 dark:bg-gray-900 flex-shrink-0">
          <div class="flex items-center gap-2">
            <!-- macOS dots -->
            <div class="flex gap-1.5">
              <div class="w-2.5 h-2.5 rounded-full bg-red-400"></div>
              <div class="w-2.5 h-2.5 rounded-full bg-yellow-400"></div>
              <div class="w-2.5 h-2.5 rounded-full bg-green-400"></div>
            </div>
            <span class="text-xs text-gray-400 font-mono ml-1">
              Python généré
            </span>
          </div>
          <button
            on:click={resetWorkspace}
            class="text-xs text-gray-500 hover:text-gray-200 transition"
          >
            🗑 Reset
          </button>
        </div>
        <pre class="flex-1 overflow-auto p-3 text-xs font-mono
                    bg-gray-900 text-green-300 leading-relaxed whitespace-pre-wrap"
        >{generatedCode || '# Glissez des blocs depuis la toolbox gauche...'}</pre>
      </div>

      <!-- Console d'exécution (US-B04) -->
      <div class="flex flex-col border-b border-gray-700" style="height:25%">
        <div class="flex items-center justify-between px-3 py-2
                    bg-gray-700 dark:bg-gray-800 flex-shrink-0">
          <span class="text-xs font-semibold text-gray-300
                       flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full inline-block {
              running ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'
            }"></span>
            Console
          </span>
          <div class="flex gap-2">
            <button
              on:click={runCode}
              disabled={running}
              class="px-3 py-1 text-xs font-bold rounded-full
                     transition flex items-center gap-1 {
                running
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white'
              }"
            >
              {#if running}
                <div class="w-3 h-3 border border-white
                            border-t-transparent rounded-full animate-spin">
                </div>
              {:else}▶{/if}
              Exécuter
            </button>
            <button
              on:click={() => (consoleOutput = '')}
              class="text-xs text-gray-400 hover:text-white transition px-1"
            >✕</button>
          </div>
        </div>
        <pre class="flex-1 overflow-auto p-3 text-xs font-mono
                    bg-gray-800 text-gray-100 whitespace-pre-wrap"
        >{consoleOutput || '// Cliquez ▶ pour exécuter votre code'}</pre>
      </div>

      <!-- Feedback IA (US-B05) -->
      <div class="flex flex-col flex-1 overflow-hidden
                  bg-white dark:bg-gray-800">

        <div class="flex items-center justify-between px-3 py-2
                    border-b border-gray-100 dark:border-gray-700
                    flex-shrink-0">

          <span class="text-xs font-semibold text-gray-700 dark:text-gray-300
                       flex items-center gap-2">
            🤖 Feedback IA
            {#if score !== null}
              <span class="px-2 py-0.5 rounded-full text-xs font-bold {
                score >= 70
                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
                  : 'bg-red-100    text-red-700    dark:bg-red-900/30    dark:text-red-300'
              }">
                {score >= 70 ? '✅' : '❌'} {score}/100
              </span>
            {/if}
          </span>

          <button
            on:click={submitCode}
            disabled={submitting}
            class="px-3 py-1.5 text-xs font-bold rounded-full
                   transition shadow-sm flex items-center gap-1.5 {
              submitting
                ? 'bg-gray-200 text-gray-400 dark:bg-gray-700 dark:text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white'
            }"
          >
            {#if submitting}
              <div class="w-3 h-3 border border-current
                          border-t-transparent rounded-full animate-spin">
              </div>
              Analyse...
            {:else}
              📤 Soumettre
            {/if}
          </button>
        </div>

        <div class="flex-1 overflow-auto p-4">
          {#if submitting && !feedback}
            <div class="flex items-center gap-2 text-gray-400 dark:text-gray-500">
              <div class="w-4 h-4 border-2 border-blue-500
                          border-t-transparent rounded-full animate-spin">
              </div>
              <span class="text-xs">Analyse de votre code...</span>
            </div>
          {:else if feedback}
            <div class="bg-blue-50 dark:bg-blue-900/20
                        border border-blue-100 dark:border-blue-800
                        rounded-xl p-3">
              <p class="text-xs text-gray-700 dark:text-gray-300
                        leading-relaxed whitespace-pre-wrap">{feedback}</p>
            </div>
          {:else}
            <p class="text-xs text-gray-400 dark:text-gray-500
                      italic text-center mt-8">
              Glissez des blocs → ▶ Exécutez → 📤 Soumettez<br>
              pour recevoir un feedback personnalisé de l'IA
            </p>
          {/if}
        </div>
      </div>

    </section>
  </main>
</div>
{/if}
