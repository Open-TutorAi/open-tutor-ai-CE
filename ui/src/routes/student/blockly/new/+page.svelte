<script lang="ts">
	import { onMount, onDestroy, tick, afterUpdate } from 'svelte';
	import { browser } from '$app/environment';
	import * as Blockly from 'blockly/core';
	import * as BlocklyBlocks from 'blockly/blocks';
	import { pythonGenerator } from 'blockly/python';
	import { inject } from 'blockly/core';
	import * as En from 'blockly/msg/en';
	import { getContext } from 'svelte';
	import {
		executeCode,
		submitSolution,
		generateExercise,
		saveWorkspace,
		loadWorkspace,
		parseSSE,
		normalizeExercise
	} from '$lib/apis/blockly';

	const _i18n: any = getContext('i18n');
    const i18n = {
         t: (s: string) => {
        try { return _i18n?.t?.(s) ?? s; }
        catch { return s; }
        }
    };

	// ── Types ──────────────────────────────────────────────────────────────────
	interface Exercise {
		title: string;
		description: string;
		test_cases: { expected_output: string }[];
		hints: string[];
	}

	// ── Constantes ─────────────────────────────────────────────────────────────
	const LEVELS = ['beginner', 'intermediate', 'advanced'] as const;
	type Level = (typeof LEVELS)[number];

	const LEVEL_CONFIG: Record<Level, { label: string; emoji: string }> = {
		beginner: { label: 'Débutant', emoji: '🌱' },
		intermediate: { label: 'Intermédiaire', emoji: '🔥' },
		advanced: { label: 'Avancé', emoji: '⚡' }
	};

	// ── État ───────────────────────────────────────────────────────────────────
	let ctx = {
		course: '',
		objectives: '',
		prerequisites: '',
		level: 'beginner' as Level
	};

	let exercise: Exercise | null = null;
	let generatingExercise = false;
	let generateError = '';

	let blocklyDiv: HTMLDivElement;
	let workspace: Blockly.WorkspaceSvg | null = null;
	let generatedCode = '';
	let blocklyInitialized = false;

	let consoleOutput = '';
	let running = false;

	let feedback = '';
	let score: number | null = null;
	let submitting = false;

	let consecutiveSuccesses = 0;
	let levelUpMessage = '';
	let assignmentId = '';

	// ── Auth ───────────────────────────────────────────────────────────────────
	function getToken(): string {
		return localStorage.getItem('token') ?? '';
	}

	// ── Cycle de vie ───────────────────────────────────────────────────────────
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
			try {
				workspace.dispose();
			} catch {}
			workspace = null;
		}
	});

	// afterUpdate : initialise Blockly dès que le div est dans le DOM
	afterUpdate(() => {
		if (blocklyDiv && !workspace && !blocklyInitialized) {
			blocklyInitialized = true;
			initBlockly();
		}
	});

	// ── US-B02 : Génération exercice ───────────────────────────────────────────
	async function loadExercise() {
		generatingExercise = true;
		generateError = '';
		exercise = null;
		score = null;
		feedback = '';
		consoleOutput = '';
		generatedCode = '';
		assignmentId = '';

		// Réinitialiser Blockly pour le prochain exercice
		if (workspace) {
			workspace.dispose();
			workspace = null;
		}
		blocklyInitialized = false;

		let fullJson = '';

		try {
			const response = await generateExercise(getToken(), ctx);

			for await (const ev of parseSSE(response)) {
				if (ev.type === 'chunk' && ev.content) {
					fullJson += ev.content;
				} else if (ev.type === 'done') {
					assignmentId = ev.assignment_id ?? '';
				} else if (ev.type === 'error') {
					throw new Error(ev.message ?? 'Erreur génération');
				}
			}

			// Nettoyer les backticks markdown qu'Ollama peut ajouter
			const cleanJson = fullJson
				.replace(/^```json\s*/i, '')
				.replace(/^```\s*/i, '')
				.replace(/```\s*$/i, '')
				.trim();

			const raw = JSON.parse(cleanJson);
			exercise = normalizeExercise(raw);

		} catch (e: unknown) {
			generateError = e instanceof Error ? e.message : String(e);
		} finally {
			generatingExercise = false;
		}
	}

	// ── US-B03 : Éditeur Blockly ───────────────────────────────────────────────
	async function initBlockly() {
		await tick();
		await new Promise((r) => setTimeout(r, 100));

		if (!blocklyDiv || workspace) return;

		blocklyDiv.style.position = 'relative';
		blocklyDiv.style.height = '100%';
		blocklyDiv.style.width = '100%';
        Blockly.setLocale(En);
		workspace = inject(blocklyDiv, {
			toolbox: {
        kind: 'categoryToolbox',
        contents: [
            { kind: 'category', name: '🔢 Variables', colour: '#555', custom: 'VARIABLE' },
            {
                kind: 'category', name: '➕ Math', colour: '#555',
                contents: [
                    { kind: 'block', type: 'math_number' },
                    { kind: 'block', type: 'math_arithmetic' },
                    { kind: 'block', type: 'math_round' },
                    { kind: 'block', type: 'math_single' },
                    { kind: 'block', type: 'math_random_int' }
                ]
            },
            {
                kind: 'category', name: '📝 Text', colour: '#555',
                contents: [
                    { kind: 'block', type: 'text_print' },
                    { kind: 'block', type: 'text' }
                ]
            },
            {
                kind: 'category', name: '⚡ Logic', colour: '#555',
                contents: [
                    { kind: 'block', type: 'controls_if' },
                    { kind: 'block', type: 'logic_compare' },
                    { kind: 'block', type: 'logic_operation' },
                    { kind: 'block', type: 'logic_negate' },
                    { kind: 'block', type: 'logic_boolean' }
                ]
            },
            {
                kind: 'category', name: '🔄 Loops', colour: '#555',
                contents: [
                    { kind: 'block', type: 'controls_repeat_ext' },
                    { kind: 'block', type: 'controls_whileUntil' },
                    { kind: 'block', type: 'controls_for' },
                    { kind: 'block', type: 'controls_forEach' }
                ]
            },
            {
                kind: 'category', name: '📋 Lists', colour: '#555',
                contents: [
                    { kind: 'block', type: 'lists_create_empty' },
                    { kind: 'block', type: 'lists_create_with' },
                    { kind: 'block', type: 'lists_length' },
                    { kind: 'block', type: 'lists_getIndex' },
                    { kind: 'block', type: 'lists_setIndex' }
                ]
            },
            { kind: 'category', name: '🔧 Functions', colour: '#555', custom: 'PROCEDURE' }
        ]
    },
    grid: { spacing: 20, length: 3, colour: '#ddd', snap: true },
    zoom: { controls: true, wheel: true, startScale: 1.0, maxScale: 3, minScale: 0.3 },
    trashcan: true,
    sounds: false,
    move: { scrollbars: true, drag: true, wheel: true }
});

		// Générer le code Python à chaque changement de workspace
		workspace.addChangeListener(() => {
			try {
				generatedCode = pythonGenerator.workspaceToCode(workspace!);
			} catch {
				// ignorer les erreurs de génération temporaires
			}
		});

		// Charger le workspace sauvegardé si disponible
		if (assignmentId) {
			try {
				const xml = await loadWorkspace(getToken(), assignmentId);
				if (xml) {
					const dom = Blockly.utils.xml.textToDom(xml);
					Blockly.Xml.domToWorkspace(dom, workspace);
				}
			} catch {
				// pas de workspace sauvegardé, c'est normal
			}
		}
	}

	function resetWorkspace() {
		if (!workspace) return;
		workspace.clear();
		generatedCode = '';
		consoleOutput = '';
		score = null;
		feedback = '';
	}

	// ── US-B04 : Exécution ─────────────────────────────────────────────────────
	async function runCode() {
		if (!generatedCode.trim() || running) return;
		running = true;
		consoleOutput = '';

		try {
			const result = await executeCode(getToken(), generatedCode);
			if (result.error) {
				consoleOutput = `❌ ${result.error}`;
			} else {
				consoleOutput = result.stdout ?? '(aucune sortie)';
			}
		} catch (e: unknown) {
			consoleOutput = `Erreur réseau : ${e instanceof Error ? e.message : String(e)}`;
		} finally {
			running = false;
		}
	}

	// ── US-B05 : Soumission ────────────────────────────────────────────────────
	async function submitCode() {
		if (!generatedCode.trim() || submitting) return;
		submitting = true;
		feedback = '';
		score = null;

		try {
			const response = await submitSolution(
				getToken(),
				generatedCode,
				ctx.level,
				assignmentId
			);

			for await (const ev of parseSSE(response)) {
				if (ev.type === 'score' && ev.value !== undefined) {
					score = ev.value;
				} else if (ev.type === 'feedback' && ev.content) {
					feedback += ev.content;
				}
			}

			// US-B06 : progression automatique
			if (score !== null && score >= 70) {
				consecutiveSuccesses += 1;
				if (consecutiveSuccesses >= 2) {
					const idx = LEVELS.indexOf(ctx.level);
					if (idx < LEVELS.length - 1) {
						ctx.level = LEVELS[idx + 1];
						consecutiveSuccesses = 0;
						levelUpMessage = `🎉 Niveau suivant : ${LEVEL_CONFIG[ctx.level].label} !`;
						setTimeout(() => (levelUpMessage = ''), 4000);
					}
				}
			} else {
				consecutiveSuccesses = 0;
			}

			// Sauvegarder le workspace après soumission
			if (workspace && assignmentId) {
				try {
					const xml = Blockly.Xml.workspaceToDom(workspace);
					const xmlText = Blockly.utils.xml.domToText(xml);
					await saveWorkspace(getToken(), assignmentId, xmlText);
				} catch {
					// sauvegarde optionnelle, ignorer les erreurs
				}
			}
		} catch (e: unknown) {
			feedback = `Erreur : ${e instanceof Error ? e.message : String(e)}`;
		} finally {
			submitting = false;
		}
	}
</script>

{#if generatingExercise}
	<!-- ── Chargement ─────────────────────────────────────────────────────────── -->
	<div class="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
		<div class="flex flex-col items-center gap-4 text-center">
			<div
				class="h-10 w-10 animate-spin rounded-full border-4
				border-gray-300 border-t-gray-800
				dark:border-gray-700 dark:border-t-gray-100"
			></div>
			<p class="text-sm font-medium text-gray-600 dark:text-gray-400">
				{i18n.t('The AI is preparing your exercise...')}
			</p>
		</div>
	</div>

{:else if generateError}
	<!-- ── Erreur de génération ───────────────────────────────────────────────── -->
	<div class="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-950 p-8">
		<div
			class="max-w-md rounded-xl border border-gray-200 dark:border-gray-700
			bg-white dark:bg-gray-900 p-6 text-center"
		>
			<p class="mb-2 text-sm font-semibold text-gray-800 dark:text-gray-100">
				{i18n.t('Generation failed')}
			</p>
			<p class="mb-4 font-mono text-xs text-gray-500 dark:text-gray-400">
				{generateError}
			</p>
			<button
				on:click={loadExercise}
				class="rounded-lg bg-gray-900 px-4 py-2 text-sm font-semibold
				text-white transition hover:bg-gray-700
				dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-300"
			>
				↺ {i18n.t('Retry')}
			</button>
		</div>
	</div>

{:else if exercise}
	<!-- ── Interface principale ──────────────────────────────────────────────── -->
	<div class="flex h-screen flex-col bg-gray-50 dark:bg-gray-950 overflow-hidden">

		<!-- Header -->
		<header
			class="flex flex-shrink-0 items-center justify-between
			border-b border-gray-200 dark:border-gray-800
			bg-white dark:bg-gray-900 px-4 py-2"
		>
			<div class="flex items-center gap-3">
				<span
					class="rounded-full border border-gray-200 dark:border-gray-700
					bg-gray-100 dark:bg-gray-800
					px-2.5 py-0.5 text-xs font-semibold
					text-gray-700 dark:text-gray-300"
				>
					{LEVEL_CONFIG[ctx.level].emoji}
					{LEVEL_CONFIG[ctx.level].label}
				</span>
				<h1 class="truncate text-sm font-semibold text-gray-800 dark:text-gray-100">
					{exercise.title}
				</h1>
			</div>

			<div class="flex items-center gap-2">
				{#if levelUpMessage}
					<span class="text-xs font-semibold text-gray-700 dark:text-gray-300 animate-pulse">
						{levelUpMessage}
					</span>
				{/if}
				<button
					on:click={loadExercise}
					class="rounded-full border border-gray-200 dark:border-gray-700
					bg-gray-100 dark:bg-gray-800
					px-3 py-1.5 text-xs font-semibold
					text-gray-700 dark:text-gray-300
					transition hover:bg-gray-200 dark:hover:bg-gray-700"
				>
					🔄 {i18n.t('New exercise')}
				</button>
			</div>
		</header>

		<!-- Corps : 2 colonnes -->
		<main class="flex flex-1 overflow-hidden">

			<!-- ── Colonne gauche : énoncé + Blockly ──────────────────────────── -->
			<section
				class="flex flex-col overflow-hidden
				border-r border-gray-200 dark:border-gray-800"
				style="width: 50%;"
			>
				<!-- Énoncé -->
				<div
					class="flex-shrink-0 border-b border-gray-200 dark:border-gray-700
					bg-gray-50 dark:bg-gray-900 px-4 py-3"
				>
					<p class="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
						{exercise.description}
					</p>
					{#if exercise.hints?.length}
						<details class="mt-2">
							<summary
								class="cursor-pointer text-xs font-medium
								text-gray-500 dark:text-gray-400 select-none"
							>
								💡 {i18n.t('Hints')}
							</summary>
							<ul class="mt-1 space-y-0.5 pl-2">
								{#each exercise.hints as h}
									<li class="text-xs text-gray-500 dark:text-gray-400">• {h}</li>
								{/each}
							</ul>
						</details>
					{/if}
				</div>

				<!-- Workspace Blockly -->
				<div
					class="flex-1 overflow-hidden bg-white dark:bg-gray-800"
					bind:this={blocklyDiv}
				></div>
			</section>

			<!-- ── Colonne droite : code + console + feedback ─────────────────── -->
			<section class="flex flex-col overflow-hidden" style="width: 50%;">

				<!-- Code Python généré -->
				<div
					class="flex flex-shrink-0 flex-col border-b border-gray-700"
					style="height: 35%;"
				>
					<div
						class="flex flex-shrink-0 items-center justify-between
						bg-gray-900 px-3 py-2"
					>
						<span class="font-mono text-xs text-gray-400">
							{i18n.t('Generated Python')}
						</span>
						<button
							on:click={resetWorkspace}
							class="text-xs text-gray-500 transition hover:text-gray-200"
							title="Réinitialiser le workspace"
						>
							🗑 {i18n.t('Reset')}
						</button>
					</div>
					<pre
						class="flex-1 overflow-auto whitespace-pre-wrap
						bg-gray-900 p-3 font-mono text-xs
						leading-relaxed text-gray-100 select-all"
					>{generatedCode || '# ' + i18n.t('Drag blocks to generate Python code...')}</pre>
				</div>

				<!-- Console -->
				<div
					class="flex flex-shrink-0 flex-col border-b border-gray-700"
					style="height: 25%;"
				>
					<div
						class="flex flex-shrink-0 items-center justify-between
						bg-gray-800 px-3 py-2"
					>
						<span class="flex items-center gap-1.5 text-xs font-semibold text-gray-300">
							<span
								class="inline-block h-2 w-2 rounded-full
								{running ? 'bg-gray-400 animate-pulse' : 'bg-gray-500'}"
							></span>
							{i18n.t('Console')}
						</span>
						<div class="flex gap-2">
							<button
								on:click={runCode}
								disabled={running || !generatedCode.trim()}
								class="flex items-center gap-1 rounded-full px-3 py-1
								text-xs font-bold transition
								{running || !generatedCode.trim()
									? 'cursor-not-allowed bg-gray-700 text-gray-500'
									: 'bg-gray-600 text-gray-100 hover:bg-gray-500'}"
							>
								{#if running}
									<div
										class="h-3 w-3 animate-spin rounded-full
										border border-current border-t-transparent"
									></div>
								{:else}
									▶
								{/if}
								{i18n.t('Run')}
							</button>
							<button
								on:click={() => (consoleOutput = '')}
								class="px-1 text-xs text-gray-400 transition hover:text-white"
								title="Vider la console"
							>✕</button>
						</div>
					</div>
					<pre
						class="flex-1 overflow-auto whitespace-pre-wrap
						bg-gray-800 p-3 font-mono text-xs text-gray-100"
					>{consoleOutput || '// ' + i18n.t('Click ▶ to run your code')}</pre>
				</div>

				<!-- Feedback IA -->
				<div class="flex flex-1 flex-col overflow-hidden bg-white dark:bg-gray-900">
					<div
						class="flex flex-shrink-0 items-center justify-between
						border-b border-gray-100 dark:border-gray-800 px-3 py-2"
					>
						<span class="flex items-center gap-2 text-xs font-semibold text-gray-700 dark:text-gray-300">
							🤖 {i18n.t('AI Feedback')}
							{#if score !== null}
								<span
									class="rounded-full border border-gray-200 dark:border-gray-700
									bg-gray-100 dark:bg-gray-800
									px-2 py-0.5 font-mono text-xs font-bold
									text-gray-700 dark:text-gray-300"
								>
									{score >= 70 ? '✅' : '❌'} {score}/100
								</span>
							{/if}
						</span>

						<button
							on:click={submitCode}
							disabled={submitting || !generatedCode.trim()}
							class="flex items-center gap-1.5 rounded-full px-3 py-1.5
							text-xs font-bold transition
							{submitting || !generatedCode.trim()
								? 'cursor-not-allowed bg-gray-200 text-gray-400 dark:bg-gray-800 dark:text-gray-600'
								: 'bg-gray-900 text-white hover:bg-gray-700 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-300'}"
						>
							{#if submitting}
								<div
									class="h-3 w-3 animate-spin rounded-full
									border border-current border-t-transparent"
								></div>
								{i18n.t('Analysing...')}
							{:else}
								📤 {i18n.t('Submit')}
							{/if}
						</button>
					</div>

					<div class="flex-1 overflow-auto p-4">
						{#if submitting && !feedback}
							<div class="flex items-center gap-2 text-gray-400 dark:text-gray-500">
								<div
									class="h-4 w-4 animate-spin rounded-full
									border-2 border-gray-300 border-t-gray-700"
								></div>
								<span class="text-xs">{i18n.t('Analysing...')}</span>
							</div>
						{:else if feedback}
							<div
								class="rounded-xl border border-gray-100 dark:border-gray-800
								bg-gray-50 dark:bg-gray-800 p-3"
							>
								<p
									class="whitespace-pre-wrap text-xs leading-relaxed
									text-gray-700 dark:text-gray-300"
								>
									{feedback}
								</p>
							</div>
						{:else}
							<p
								class="mt-8 text-center text-xs italic
								text-gray-400 dark:text-gray-600"
							>
								{i18n.t('Drag blocks → ▶ Run → 📤 Submit to get AI feedback')}
							</p>
						{/if}
					</div>
				</div>
			</section>
		</main>
	</div>
{/if}