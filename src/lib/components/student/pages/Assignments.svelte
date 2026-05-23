<script lang="ts">
	import { getContext, onMount, onDestroy } from 'svelte';
	import { fade, fly } from 'svelte/transition';

	const i18n = getContext('i18n');

	// --- Student Taking States ---
	let state: 'code_entry' | 'taking' | 'completed' = 'code_entry';

	// 1. Code Entry state
	let quizCode: string = '';
	let isJoining: boolean = false;
	let joinError: string = '';

	// 2. Quiz Active state
	let quizData: any = null; // { id, title, time_limit, limit_date, questions: [] }
	let currentQuestionIndex: number = 0;
	let answers: Record<string, string> = {}; // { question_id: selected_answer }
	let isSubmitting: boolean = false;

	// Timer variables
	let timeLeftSeconds: number = 0;
	let timerInterval: any = null;

	// 3. Quiz Completed state
	let scoreResult: any = null; // { score, total, submission_id, submitted_at }

	// Format code automatically
	function handleCodeInput(e: Event) {
		const target = e.target as HTMLInputElement;
		quizCode = target.value.toUpperCase().slice(0, 6).replace(/[^A-Z0-9]/g, '');
	}

	// Action: Join Quiz
	async function joinQuiz() {
		if (quizCode.length !== 6) {
			joinError = $i18n.t('Le code doit comporter exactement 6 caractères.');
			return;
		}
		isJoining = true;
		joinError = '';

		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`/api/v1/quizzes/join/${quizCode}`, {
				headers: { Authorization: `Bearer ${token}` }
			});

			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? $i18n.t('Code invalide ou quiz introuvable'));
			}

			quizData = await res.json();
			state = 'taking';
			currentQuestionIndex = 0;
			answers = {};

			// Setup timer if time limit exists
			if (quizData.time_limit) {
				timeLeftSeconds = quizData.time_limit * 60;
				startTimer();
			}
		} catch (e: any) {
			joinError = e.message;
		} finally {
			isJoining = false;
		}
	}

	// Countdown Timer Logic
	function startTimer() {
		if (timerInterval) clearInterval(timerInterval);
		timerInterval = setInterval(() => {
			if (timeLeftSeconds <= 1) {
				clearInterval(timerInterval);
				timeLeftSeconds = 0;
				autoSubmit();
			} else {
				timeLeftSeconds -= 1;
			}
		}, 1000);
	}

	// Format time as MM:SS
	function formatTime(seconds: number): string {
		const m = Math.floor(seconds / 60);
		const s = seconds % 60;
		return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
	}

	// Select option in QCM/True-False
	function selectOption(questionId: string, option: string) {
		answers[questionId] = option;
		answers = { ...answers }; // Svelte trigger reactivity
	}

	// Next Question Navigation
	function nextQuestion() {
		if (currentQuestionIndex < quizData.questions.length - 1) {
			currentQuestionIndex += 1;
		}
	}

	// Back Question Navigation
	function prevQuestion() {
		if (currentQuestionIndex > 0) {
			currentQuestionIndex -= 1;
		}
	}

	// Action: Submit Quiz
	async function submitQuiz() {
		isSubmitting = true;
		if (timerInterval) clearInterval(timerInterval);

		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`/api/v1/quizzes/submit/${quizData.id}`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`
				},
				body: JSON.stringify({ answers })
			});

			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? $i18n.t('Erreur de soumission'));
			}

			scoreResult = await res.json();
			state = 'completed';
		} catch (e: any) {
			alert(e.message ?? $i18n.t('Une erreur est survenue lors de l\'envoi.'));
		} finally {
			isSubmitting = false;
		}
	}

	// Auto submit when time limit expires
	async function autoSubmit() {
		alert($i18n.t('Temps écoulé ! Votre quiz a été soumis automatiquement.'));
		await submitQuiz();
	}

	// Reset to take another quiz
	function resetQuiz() {
		state = 'code_entry';
		quizCode = '';
		quizData = null;
		scoreResult = null;
		currentQuestionIndex = 0;
	}

	// Clean up timer interval on destroy
	onDestroy(() => {
		if (timerInterval) clearInterval(timerInterval);
	});
</script>

<div class="min-h-screen bg-[#F8FAFC] dark:bg-[#090D1A] flex flex-col justify-center py-8 font-sans text-slate-800 dark:text-slate-100 transition-colors duration-300">
	<div class="max-w-2xl mx-auto w-full px-6">
		
		{#if state === 'code_entry'}
			<!-- ── SCREEN 1: CODE ENTRY ── -->
			<div in:fade={{ duration: 250 }} class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-[36px] shadow-2xl p-8 space-y-8 relative overflow-hidden text-center">
				<div class="absolute inset-x-0 top-0 h-2 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>

				<div class="space-y-3">
					<div class="w-14 h-14 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 rounded-2xl flex items-center justify-center text-2xl mx-auto shadow-md">
						📝
					</div>
					<h2 class="text-2xl font-black tracking-tight">{$i18n.t('Rejoindre une Évaluation')}</h2>
					<p class="text-xs text-slate-400 max-w-sm mx-auto">{$i18n.t('Saisissez le code à 6 caractères partagé par votre enseignant pour débuter le quiz.')}</p>
				</div>

				<div class="space-y-4 max-w-xs mx-auto">
					<div class="space-y-1">
						<input
							type="text"
							placeholder="EX: A1B2C3"
							value={quizCode}
							on:input={handleCodeInput}
							class="w-full text-center px-6 py-4 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/80 rounded-2xl outline-none font-mono text-3xl font-black uppercase tracking-wider text-indigo-600 dark:text-indigo-400 focus:ring-4 focus:ring-indigo-500/10 transition-all shadow-inner"
						/>
					</div>

					{#if joinError}
						<div in:fly={{ y: -5, duration: 150 }} class="text-xs text-rose-500 font-bold bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/20 py-2.5 px-4 rounded-xl">
							⚠️ {joinError}
						</div>
					{/if}

					<button
						type="button"
						class="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-2xl text-xs font-black uppercase tracking-widest flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 active:scale-95 transition-all disabled:opacity-50"
						on:click={joinQuiz}
						disabled={isJoining || quizCode.length !== 6}
					>
						{#if isJoining}
							<svg class="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
							</svg>
							{$i18n.t('Vérification...')}
						{:else}
							{$i18n.t('Commencer')}
							<span>➡️</span>
						{/if}
					</button>
				</div>
			</div>

		{:else if state === 'taking'}
			<!-- ── SCREEN 2: ACTIVE TAKING FLOW ── -->
			<div in:fade={{ duration: 200 }} class="space-y-6">
				
				<!-- Header Info (Progress & Timer) -->
				<div class="flex items-center justify-between bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 px-6 py-4 rounded-2xl shadow-sm">
					<div class="space-y-1">
						<span class="text-[9px] font-black uppercase tracking-widest text-indigo-500">{$i18n.t('Évaluation en cours')}</span>
						<h3 class="text-sm font-black truncate max-w-[280px] sm:max-w-md">{quizData.title}</h3>
					</div>

					{#if quizData.time_limit}
						<!-- Floating countdown timer -->
						<div class="flex items-center gap-2 px-3.5 py-2 bg-rose-50 dark:bg-rose-950/20 border border-rose-100/50 dark:border-rose-900/20 text-rose-600 dark:text-rose-400 rounded-xl text-xs font-black tracking-wider">
							<span>⏱️</span>
							<span>{formatTime(timeLeftSeconds)}</span>
						</div>
					{/if}
				</div>

				<!-- Slide progress indicators -->
				<div class="space-y-1">
					<div class="flex justify-between text-[10px] font-black text-slate-400 uppercase tracking-widest">
						<span>{$i18n.t('Progression')}</span>
						<span>{currentQuestionIndex + 1} / {quizData.questions.length}</span>
					</div>
					<div class="h-2 bg-slate-100 dark:bg-slate-900 border border-slate-200/40 dark:border-slate-800 rounded-full overflow-hidden">
						<div class="h-full bg-gradient-to-r from-indigo-500 to-purple-600 transition-all duration-300" style="width: {((currentQuestionIndex + 1) / quizData.questions.length) * 100}%"></div>
					</div>
				</div>

				<!-- Focused Single Question Card -->
				{@const q = quizData.questions[currentQuestionIndex]}
				<div in:fly={{ x: 12, duration: 250 }} class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 rounded-[32px] p-6 md:p-8 shadow-sm space-y-6">
					
					<div class="space-y-3">
						<span class="text-xs font-black bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 px-3 py-1.5 rounded-full uppercase tracking-wider">
							{q.question_type}
						</span>
						<h2 class="text-lg font-bold leading-relaxed">{q.question_text}</h2>
					</div>

					{#if q.question_type === 'QCM'}
						<!-- Premium Choice Grid -->
						<div class="grid grid-cols-1 gap-3 pt-2">
							{#each q.options as opt}
								<button
									type="button"
									class="flex items-center gap-4 text-left px-5 py-4 border rounded-2xl transition-all duration-200 hover:scale-[1.01] hover:border-indigo-500/20 {answers[q.id] === opt ? 'bg-indigo-50/50 dark:bg-indigo-950/40 border-indigo-500/40 text-indigo-600 dark:text-indigo-400 shadow-sm' : 'border-slate-100 dark:border-slate-800 bg-slate-50/30 dark:bg-slate-950/10'}"
									on:click={() => selectOption(q.id, opt)}
								>
									<span class="w-6 h-6 border-2 rounded-full flex items-center justify-center text-xs font-bold transition-all {answers[q.id] === opt ? 'bg-indigo-600 border-indigo-600 text-white' : 'border-slate-200 dark:border-slate-800 text-transparent'}">
										✓
									</span>
									<span class="text-sm font-semibold">{opt}</span>
								</button>
							{/each}
						</div>
					{:else if q.question_type === 'True/False'}
						<!-- True or False options -->
						<div class="grid grid-cols-2 gap-4 pt-2">
							{#each ['Vrai', 'Faux'] as opt}
								<button
									type="button"
									class="flex flex-col items-center justify-center p-6 border rounded-2xl transition-all duration-200 hover:scale-[1.01] hover:border-indigo-500/20 {answers[q.id] === opt ? 'bg-indigo-50/50 dark:bg-indigo-950/40 border-indigo-500/40 text-indigo-600 dark:text-indigo-400 shadow-sm font-bold' : 'border-slate-100 dark:border-slate-800 bg-slate-50/30 dark:bg-slate-950/10 font-semibold'}"
									on:click={() => selectOption(q.id, opt)}
								>
									<span class="text-xl mb-1">{opt === 'Vrai' ? '🟢' : '🔴'}</span>
									<span class="text-sm">{$i18n.t(opt)}</span>
								</button>
							{/each}
						</div>
					{:else}
						<!-- Short Answer Text Area -->
						<div class="pt-2">
							<textarea
								bind:value={answers[q.id]}
								placeholder={$i18n.t('Rédigez votre réponse courte ici...')}
								rows="4"
								class="w-full p-4 bg-slate-50 dark:bg-slate-950 border border-slate-250/60 dark:border-slate-800/80 rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500/10 text-sm font-semibold"
							></textarea>
						</div>
					{/if}
				</div>

				<!-- Navigation Footer Controls -->
				<div class="flex justify-between items-center pt-2">
					<button
						type="button"
						class="px-5 py-3 border border-slate-200 dark:border-slate-850 rounded-xl text-xs font-black uppercase tracking-wider hover:bg-slate-100/50 dark:hover:bg-slate-900 disabled:opacity-30 disabled:pointer-events-none transition-all"
						on:click={prevQuestion}
						disabled={currentQuestionIndex === 0}
					>
						⬅️ {$i18n.t('Retour')}
					</button>

					{#if currentQuestionIndex < quizData.questions.length - 1}
						<button
							type="button"
							class="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-black uppercase tracking-wider shadow-lg shadow-indigo-500/15"
							on:click={nextQuestion}
						>
							{$i18n.t('Suivant')} ➡️
						</button>
					{:else}
						<button
							type="button"
							class="px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white rounded-xl text-xs font-black uppercase tracking-wider shadow-lg shadow-emerald-500/15 disabled:opacity-50"
							on:click={submitQuiz}
							disabled={isSubmitting}
						>
							{#if isSubmitting}
								<svg class="animate-spin h-3.5 w-3.5 text-white inline mr-1" viewBox="0 0 24 24" fill="none">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
								</svg>
								{$i18n.t('Soumission...')}
							{:else}
								<span>🚀</span>
								{$i18n.t('Terminer & Soumettre')}
							{/if}
						</button>
					{/if}
				</div>
			</div>

		{:else if state === 'completed'}
			<!-- ── SCREEN 3: COMPLETION & SCORE DISPLAY ── -->
			<div in:fly={{ y: 20, duration: 400 }} class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-[36px] shadow-2xl p-8 text-center space-y-6 relative overflow-hidden max-w-md mx-auto">
				<div class="absolute inset-x-0 top-0 h-2 bg-gradient-to-r from-emerald-400 to-teal-500"></div>

				<div class="w-16 h-16 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 rounded-2xl flex items-center justify-center text-3xl mx-auto shadow-md">
					🎓
				</div>

				<div class="space-y-2">
					<h2 class="text-2xl font-black text-slate-855 dark:text-slate-50">{$i18n.t('Quiz Terminé !')}</h2>
					<p class="text-xs text-slate-400">{$i18n.t('Félicitations, vos réponses ont été enregistrées et notées instantanément.')}</p>
				</div>

				<!-- Scoring Visual Card -->
				<div class="bg-slate-50 dark:bg-slate-950/80 border border-slate-200/50 dark:border-slate-800 rounded-3xl p-6 space-y-2 shadow-inner">
					<span class="text-[10px] font-black uppercase tracking-widest text-slate-400">{$i18n.t('Votre Score Final')}</span>
					<div class="flex items-baseline justify-center gap-1.5 pt-1">
						<span class="text-5xl font-black text-emerald-600 dark:text-emerald-400">{scoreResult.score}</span>
						<span class="text-lg text-slate-400 font-bold">/ {scoreResult.total}</span>
					</div>
					<div class="text-[11px] font-bold text-slate-400 pt-1">
						{Math.round((scoreResult.score / scoreResult.total) * 100)} % {$i18n.t('de bonnes réponses')}
					</div>
				</div>

				<button
					type="button"
					class="w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl text-xs font-black uppercase tracking-wider shadow-lg shadow-indigo-500/20 active:scale-95 transition-all"
					on:click={resetQuiz}
				>
					{$i18n.t('Retour aux Évaluations')}
				</button>
			</div>
		{/if}

	</div>
</div>
