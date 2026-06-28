<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import type { Writable } from 'svelte/store';
	import { config, models } from '$lib/stores';
	import {
		generateDiagnostic,
		submitDiagnostic,
		getDiagnosticBySupport,
		type DiagnosticResult,
		type DiagnosticQuestion,
		type DiagnosticAnswer
	} from '$lib/apis/diagnostics';

	interface I18n {
		t: (key: string) => string;
	}
	const i18n = getContext<Writable<I18n>>('i18n');

	$: supportId = $page.params.id ?? '';

	// ── State ──────────────────────────────────────────────────────────────────

	let diagnostic: DiagnosticResult | null = null;
	let loading = true;
	let generating = false;
	let submitting = false;
	let error: string | null = null;

	let selectedModelId: string = '';
	$: if (!selectedModelId) {
		const defaults = $config?.default_models ?? '';
		const first = defaults.split(',')[0]?.trim();
		selectedModelId = first || $models[0]?.id || '';
	}

	// Step-by-step navigation
	let currentStep = 0;
	let answers: Record<number, string> = {};

	function selectAnswer(questionId: number, choice: string) {
		answers = { ...answers, [questionId]: choice };
	}

	// ── Lifecycle ──────────────────────────────────────────────────────────────

	onMount(async () => {
		const token = localStorage.getItem('token');
		if (!token) {
			error = $i18n.t('Authentication required');
			loading = false;
			return;
		}

		try {
			diagnostic = await getDiagnosticBySupport(token, supportId);
			if (diagnostic?.status === 'pending' && diagnostic.questions) {
				currentStep = 0;
			}
		} catch (err: any) {
			error = err?.message ?? $i18n.t('Failed to load diagnostic');
		} finally {
			loading = false;
		}
	});

	// ── Helpers ────────────────────────────────────────────────────────────────

	function getModelId(): string | null {
		return selectedModelId || null;
	}

	$: questions = (diagnostic?.questions ?? []) as DiagnosticQuestion[];
	$: totalSteps = questions.length;
	$: currentQuestion = questions[currentStep] ?? null;
	$: allAnswered = totalSteps > 0 && Object.keys(answers).length === totalSteps;

	// ── Actions ────────────────────────────────────────────────────────────────

	async function handleGenerate() {
		const token = localStorage.getItem('token');
		if (!token) {
			toast.error($i18n.t('Authentication required'));
			return;
		}

		const modelId = getModelId();
		if (!modelId) {
			toast.error($i18n.t('No model configured. Please set a default model in settings.'));
			return;
		}

		generating = true;
		try {
			diagnostic = await generateDiagnostic(token, supportId, modelId);
			currentStep = 0;
			answers = {};
			toast.success($i18n.t('Diagnostic generated'));
		} catch (err: any) {
			toast.error(err?.message ?? $i18n.t('Failed to generate diagnostic'));
		} finally {
			generating = false;
		}
	}

	async function handleSubmit() {
		if (!diagnostic) return;
		const token = localStorage.getItem('token');
		if (!token) {
			toast.error($i18n.t('Authentication required'));
			return;
		}

		const payload: DiagnosticAnswer[] = Object.entries(answers).map(([qId, ans]) => ({
			question_id: Number(qId),
			answer: ans
		}));

		submitting = true;
		try {
			diagnostic = await submitDiagnostic(token, diagnostic.id, payload);
			toast.success($i18n.t('Diagnostic completed'));
		} catch (err: any) {
			toast.error(err?.message ?? $i18n.t('Failed to submit diagnostic'));
		} finally {
			submitting = false;
		}
	}

	function handleStartChat() {
		localStorage.setItem(
			'pendingSupportData',
			JSON.stringify({ id: supportId, timestamp: Date.now(), attempts: 0 })
		);
		goto('/student/chat');
	}

	function levelColor(level: string | null) {
		if (level === 'avancé') return 'bg-green-100 text-green-800';
		if (level === 'intermédiaire') return 'bg-yellow-100 text-yellow-800';
		return 'bg-red-100 text-red-800';
	}

	$: answersMap = diagnostic?.answers
		? Object.fromEntries(
				(diagnostic.answers as any[]).map((a: any) => [String(a.question_id), a.answer])
			)
		: {};
</script>

<div class="bg-gray-50 dark:bg-gray-900 min-h-screen px-4 py-8">
	<div class="max-w-2xl mx-auto">
		<!-- Header -->
		<div class="mb-6">
			<button
				on:click={() => goto(`/student/support/${supportId}`)}
				class="inline-flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-4"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5 mr-2"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
						clip-rule="evenodd"
					/>
				</svg>
				{$i18n.t('Back')}
			</button>
			<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
				{$i18n.t('Level Diagnostic')}
			</h1>
			<p class="text-gray-500 dark:text-gray-400 mt-1">
				{$i18n.t('Answer the questions to determine your level before starting.')}
			</p>
		</div>

		<!-- Loading -->
		{#if loading}
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow p-8 animate-pulse">
				<div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
			</div>

			<!-- Error -->
		{:else if error}
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow p-8 text-center">
				<p class="text-red-500">{error}</p>
			</div>

			<!-- No diagnostic yet -->
		{:else if !diagnostic}
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow p-8 text-center">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-14 w-14 text-blue-400 mx-auto mb-4"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="1.5"
						d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
					/>
				</svg>
				<h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
					{$i18n.t('Start the Diagnostic Test')}
				</h2>
				<p class="text-gray-500 dark:text-gray-400 mb-6">
					{$i18n.t('The AI will generate questions adapted to your subject to assess your level.')}
				</p>

				{#if $models.length > 0}
					<div class="mb-6 text-left max-w-sm mx-auto">
						<label
							for="diagnostic-model"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
						>
							{$i18n.t('AI Model')}
						</label>
						<select
							id="diagnostic-model"
							bind:value={selectedModelId}
							class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
						>
							{#each $models as model}
								<option value={model.id}>{model.name ?? model.id}</option>
							{/each}
						</select>
					</div>
				{/if}

				<button
					on:click={handleGenerate}
					disabled={generating || !selectedModelId}
					class="px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-60 transition-colors"
				>
					{generating ? $i18n.t('Generating...') : $i18n.t('Start Diagnostic')}
				</button>
			</div>

			<!-- Result -->
		{:else if diagnostic.status === 'completed'}
			<div class="space-y-4">
				<!-- Score card -->
				<div class="bg-white dark:bg-gray-800 rounded-xl shadow p-8 text-center">
					<div class="text-5xl font-bold text-blue-600 mb-2">{diagnostic.score}%</div>
					<p class="text-gray-500 dark:text-gray-400 mb-4">{$i18n.t('Your score')}</p>
					<span
						class="inline-block px-4 py-1.5 rounded-full text-sm font-semibold mb-6 {levelColor(
							diagnostic.determined_level
						)}"
					>
						{$i18n.t('Level')}: {diagnostic.determined_level}
					</span>
					<p class="text-gray-600 dark:text-gray-400 mb-8">
						{$i18n.t('Your level has been recorded. The tutor will adapt to it.')}
					</p>
					<button
						on:click={handleStartChat}
						class="px-6 py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors"
					>
						{$i18n.t('Start Support Chat')}
					</button>
				</div>

				<!-- Answers review with explanations -->
				{#if diagnostic.questions && diagnostic.answers}
					<div class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
						<h3 class="text-base font-semibold text-gray-800 dark:text-white mb-4">
							{$i18n.t('Review')}
						</h3>
						<div class="space-y-4">
							{#each diagnostic.questions as q, idx}
								{@const userAnswer = answersMap[String(q.id)]}
								{@const isCorrect = userAnswer === q.correct_answer}
								<div
									class="p-4 rounded-lg border {isCorrect
										? 'border-green-200 bg-green-50 dark:bg-green-900/20 dark:border-green-800'
										: 'border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800'}"
								>
									<p class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
										<span class="mr-2 font-bold">{idx + 1}.</span>{q.question}
									</p>
									<p class="text-sm mb-1">
										<span
											class="font-medium {isCorrect
												? 'text-green-700 dark:text-green-300'
												: 'text-red-700 dark:text-red-300'}"
										>
											{isCorrect ? '✓' : '✗'}
											{$i18n.t('Your answer')}:
										</span>
										<span class="text-gray-700 dark:text-gray-300 ml-1">{userAnswer}</span>
									</p>
									{#if !isCorrect}
										<p class="text-sm mb-1">
											<span class="font-medium text-green-700 dark:text-green-300"
												>{$i18n.t('Correct answer')}:</span
											>
											<span class="text-gray-700 dark:text-gray-300 ml-1">{q.correct_answer}</span>
										</p>
									{/if}
									{#if q.explanation}
										<p class="text-xs text-gray-500 dark:text-gray-400 mt-2 italic">
											{q.explanation}
										</p>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>

			<!-- Questions (step by step) -->
		{:else if diagnostic.status === 'pending' && currentQuestion}
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow p-8">
				<!-- Progress bar -->
				<div class="mb-6">
					<div class="flex justify-between text-sm text-gray-500 dark:text-gray-400 mb-1">
						<span>{$i18n.t('Question')} {currentStep + 1} / {totalSteps}</span>
						<span>{Math.round(((currentStep + 1) / totalSteps) * 100)}%</span>
					</div>
					<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
						<div
							class="bg-blue-600 h-2 rounded-full transition-all duration-300"
							style="width: {((currentStep + 1) / totalSteps) * 100}%"
						></div>
					</div>
				</div>

				<!-- Question -->
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
					{currentQuestion.question}
				</h2>

				<!-- Choices -->
				<div class="space-y-3 mb-8">
					{#each currentQuestion.choices as choice, idx}
						{@const selected = answers[currentQuestion.id] === choice}
						<button
							type="button"
							on:click={() => selectAnswer(currentQuestion.id, choice)}
							class="w-full flex items-center gap-4 p-4 rounded-xl border-2 text-left cursor-pointer transition-all
                                {selected
								? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
								: 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 bg-white dark:bg-gray-800'}"
						>
							<span
								class="w-8 h-8 flex items-center justify-center rounded-full border-2 text-sm font-bold shrink-0
                                {selected
									? 'border-blue-500 bg-blue-500 text-white'
									: 'border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400'}"
							>
								{String.fromCharCode(65 + idx)}
							</span>
							<span class="text-gray-800 dark:text-gray-200 text-sm leading-snug">{choice}</span>
							{#if selected}
								<svg
									class="ml-auto shrink-0 h-5 w-5 text-blue-500"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2.5"
										d="M5 13l4 4L19 7"
									/>
								</svg>
							{/if}
						</button>
					{/each}
				</div>

				<!-- Navigation -->
				<div class="flex justify-between">
					<button
						on:click={() => (currentStep = Math.max(0, currentStep - 1))}
						disabled={currentStep === 0}
						class="px-4 py-2 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 transition-colors"
					>
						{$i18n.t('Previous')}
					</button>

					{#if currentStep < totalSteps - 1}
						<button
							on:click={() => (currentStep = currentStep + 1)}
							disabled={!answers[currentQuestion.id]}
							class="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-40 transition-colors"
						>
							{$i18n.t('Next')}
						</button>
					{:else}
						<button
							on:click={handleSubmit}
							disabled={!allAnswered || submitting}
							class="px-6 py-2 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 disabled:opacity-40 transition-colors"
						>
							{submitting ? $i18n.t('Submitting...') : $i18n.t('Submit')}
						</button>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>
