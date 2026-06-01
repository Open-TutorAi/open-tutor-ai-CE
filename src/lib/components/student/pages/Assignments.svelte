<script lang="ts">
	import { getContext, onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { fade, fly } from 'svelte/transition';
	import { isDemo, demoData, user } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// --- Student States ---
	let state: 'dashboard' | 'code_entry' | 'taking' | 'completed' = 'dashboard';

	// 1. Dashboard / Assignments list state
	let assignments: any[] = [];
	let selectedSubject: string = $i18n.t('All Subjects');
	let selectedStatus: string = $i18n.t('All Status');

	// Reactive filtered assignments based on selected filters
	$: filteredAssignments = assignments.filter(a => {
	  const subjectMatch = selectedSubject === $i18n.t('All Subjects') || a.course === selectedSubject;
	  const statusMatch = selectedStatus === $i18n.t('All Status') || a.status === selectedStatus.toLowerCase();
	  return subjectMatch && statusMatch;
	});

	async function fetchAssignments() {
		const token = localStorage.getItem('token') ?? '';
		let joinedCodes: string[] = [];
		try {
			joinedCodes = JSON.parse(localStorage.getItem('joined_quiz_codes') || '[]');
		} catch (e) {}
		const codesParam = joinedCodes.join(',');

		try {
			const res = await fetch(`/api/v1/student/assignments?codes=${codesParam}`, {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				assignments = await res.json();
			} else {
				const err = await res.json().catch(() => ({}));
				toast.error(err.detail || $i18n.t('Failed to load assignments'));
			}
		} catch (e: any) {
			toast.error(e.message || $i18n.t('Network error while loading assignments'));
		}
	}

	onMount(async () => {
		await fetchAssignments();
	});

	let lastJoinedCode = '';
	let lastTakenCode = '';
	$: if ($page && $page.url) {
		const codeParam = $page.url.searchParams.get('code');
		if (codeParam && codeParam.length === 6 && codeParam !== lastJoinedCode) {
			lastJoinedCode = codeParam;
			quizCode = codeParam.toUpperCase();
			joinQuiz();
		}

		const takeParam = $page.url.searchParams.get('take');
		if (takeParam && takeParam.length === 6 && takeParam !== lastTakenCode) {
			lastTakenCode = takeParam;
			startQuizTakingFlow(takeParam.toUpperCase());
		}
	}

	$: upcomingDeadlines = assignments.filter(a => ['pending', 'in-progress', 'overdue'].includes(a.status)).length;
	$: username = $user?.name ? $user.name.split(' ')[0] : 'Student';

	function getTopBorderColor(status: string) {
		switch (status) {
			case 'completed': return 'bg-green-500';
			case 'in-progress': return 'bg-blue-500';
			case 'overdue': return 'bg-red-500';
			case 'pending':
			default: return 'bg-gray-400';
		}
	}
	
	function getButtonProps(status: string) {
		switch (status) {
			case 'completed': 
				return { text: 'View Feedback', class: 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 shadow-sm' };
			case 'in-progress': 
				return { text: 'Continue', class: 'bg-blue-500 text-white hover:bg-blue-600 shadow-sm shadow-blue-500/30' };
			case 'overdue': 
				return { text: 'Submit Late', class: 'bg-blue-500 text-white hover:bg-blue-600 shadow-sm shadow-blue-500/30' };
			case 'pending':
			default: 
				return { text: 'Start', class: 'bg-blue-500 text-white hover:bg-blue-600 shadow-sm shadow-blue-500/30' };
		}
	}
	
	async function handleSubmit(assignment: any) {
		if (assignment.quiz_code) {
			await startQuizTakingFlow(assignment.quiz_code);
		} else {
			if ($isDemo) {
				toast.info($i18n.t('Submissions are disabled in demo mode'));
			} else {
				toast.info($i18n.t('Submission functionality coming soon'));
			}
		}
	}

	async function startQuizTakingFlow(code: string) {
		isJoining = true;
		joinError = '';

		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`/api/v1/quizzes/join/${code}`, {
				headers: { Authorization: `Bearer ${token}` }
			});

			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? $i18n.t('Code de quiz invalide ou expiré'));
			}

			quizData = await res.json();
			state = 'taking';
			startTime = Date.now();
			currentQuestionIndex = 0;
			answers = {};

			// Setup timer if time limit exists
			if (quizData.time_limit) {
				timeLeftSeconds = quizData.time_limit * 60;
				startTimer();
			}
		} catch (e: any) {
			joinError = e.message;
			toast.error(joinError);
		} finally {
			isJoining = false;
		}
	}

	// 2. Code Entry state
	let quizCode: string = '';
	let isJoining: boolean = false;
	let joinError: string = '';

	// 3. Quiz Active state
	let quizData: any = null; // { id, title, time_limit, limit_date, questions: [] }
	let currentQuestionIndex: number = 0;
	let answers: Record<string, string> = {}; // { question_id: selected_answer }
	let isSubmitting: boolean = false;
	let startTime: number = 0;

	// Timer variables
	let timeLeftSeconds: number = 0;
	let timerInterval: any = null;

	// 4. Quiz Completed state
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
			const res = await fetch(`/api/v1/student/assignments/join-by-code`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`
				},
				body: JSON.stringify({ code: quizCode })
			});

			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? $i18n.t('Code de quiz invalide ou expiré'));
			}

			const newAssignment = await res.json();
			
			if (newAssignment.quiz_code) {
				let joinedCodes: string[] = [];
				try {
					joinedCodes = JSON.parse(localStorage.getItem('joined_quiz_codes') || '[]');
				} catch (e) {}
				if (!joinedCodes.includes(newAssignment.quiz_code)) {
					joinedCodes.push(newAssignment.quiz_code);
					localStorage.setItem('joined_quiz_codes', JSON.stringify(joinedCodes));
				}
			}

			await fetchAssignments();
			toast.success($i18n.t('Évaluation rejointe avec succès !'));
			
			// Transition back to dashboard so the card is rendered
			state = 'dashboard';
			goto('/student/assignments', { replaceState: true });
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

		let timeSpentMinutes = 1;
		if (startTime > 0) {
			const elapsedSeconds = (Date.now() - startTime) / 1000;
			timeSpentMinutes = Math.max(1, Math.ceil(elapsedSeconds / 60));
		}
		if (quizData && quizData.time_limit) {
			const calculatedMinutes = Math.max(1, Math.ceil(((quizData.time_limit * 60) - timeLeftSeconds) / 60));
			timeSpentMinutes = Math.min(quizData.time_limit, calculatedMinutes);
		}
		answers['__time_spent__'] = String(timeSpentMinutes);

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
	async function resetQuiz() {
		state = 'dashboard';
		quizCode = '';
		quizData = null;
		scoreResult = null;
		currentQuestionIndex = 0;
		goto('/student/assignments', { replaceState: true });
		await fetchAssignments();
	}

	function formatDate(dateStr: string) {
		if (!dateStr) return '';
		try {
			const d = new Date(dateStr);
			const day = d.getDate();
			const months = [
				'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
				'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
			];
			const month = months[d.getMonth()];
			const year = d.getFullYear();
			return `${day} ${month} ${year}`;
		} catch (e) {
			return dateStr;
		}
	}

	// Clean up timer interval on destroy
	onDestroy(() => {
		if (timerInterval) clearInterval(timerInterval);
	});
</script>

{#if state === 'dashboard'}
<div class="h-full flex flex-col p-4 md:p-0">
	<div class="bg-white dark:bg-gray-900 md:rounded-[2rem] p-8 md:p-10 shadow-sm flex-1 max-w-[1400px] w-full mx-auto flex flex-col border border-gray-100 dark:border-gray-800">
		
		<!-- Welcome Section -->
		<div class="mb-10 text-center md:text-left">
			<h1 class="text-[2rem] font-medium text-slate-700 dark:text-white mb-2 tracking-tight">
				{$i18n.t('Welcome back')}, {username}!
			</h1>
			<p class="text-slate-500 dark:text-gray-400 text-[15px]">
				{$i18n.t('You have {{count}} upcoming deadlines this week. Stay focused and keep learning !', { count: upcomingDeadlines })}
			</p>
		</div>

		<!-- Filters & Title -->
		<div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
			<h2 class="text-xl font-medium text-slate-700 dark:text-white tracking-tight">{$i18n.t('My Assignments')}</h2>
			
			<div class="flex flex-wrap items-center gap-3 w-full md:w-auto">
				<div class="relative flex-1 md:flex-none">
					<select bind:value={selectedSubject} class="w-full appearance-none bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 py-2 pl-4 pr-10 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm shadow-sm transition-shadow hover:shadow">
						<option>{$i18n.t('All Subjects')}</option>
						{#each Array.from(new Set(assignments.map(a => a.course))) as subj}
							<option>{subj}</option>
						{/each}
					</select>
					<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-400">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
					</div>
				</div>

				<div class="relative flex-1 md:flex-none">
					<select bind:value={selectedStatus} class="w-full appearance-none bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 py-2 pl-4 pr-10 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm shadow-sm transition-shadow hover:shadow">
						<option>{$i18n.t('All Status')}</option>
						<option>{$i18n.t('Pending')}</option>
						<option>{$i18n.t('Completed')}</option>
					</select>
					<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-400">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
					</div>
				</div>

				<button class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 py-2 px-6 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm shadow-sm hover:shadow">
					{$i18n.t('Filter')}
				</button>

				<button 
					on:click={() => { state = 'code_entry'; }}
					class="bg-blue-500 text-white py-2 px-6 rounded-full hover:bg-blue-600 shadow-sm shadow-blue-500/30 transition-colors text-sm font-medium"
				>
					{$i18n.t('Enter Quiz Code')} 🚀
				</button>
			</div>
		</div>

		<!-- Grid -->
		{#if filteredAssignments.length > 0}
			<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mb-10">
				{#each filteredAssignments as assignment (assignment.id)}
					<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.06)] overflow-hidden flex flex-col min-h-[300px] pb-5 relative border border-gray-100 dark:border-gray-700 transition-transform hover:-translate-y-1 duration-300">
						<!-- Top colored bar -->
						<div class="h-3 w-full {getTopBorderColor(assignment.status)}"></div>
						
						<div class="p-6 flex flex-col flex-1">
							<!-- Subject & Points -->
							<div class="flex justify-between items-center mb-4">
								<span class="bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 text-xs font-medium px-3 py-1 rounded-md">
									{assignment.course}
								</span>
								<span class="text-gray-400 dark:text-gray-500 text-xs font-medium">
									{assignment.points} {$i18n.t('points')}
								</span>
							</div>

							<!-- Title -->
							<h3 class="text-slate-700 dark:text-gray-100 font-semibold text-[15px] mb-2 line-clamp-1">
								{assignment.title}
							</h3>
							
							{#if !assignment.score && assignment.score !== 0}
								<!-- Pending / Uncompleted state -->
								<p class="text-gray-500 dark:text-gray-400 text-[13px] leading-relaxed line-clamp-3 mb-4 flex-1">
									{assignment.description}
								</p>

								<!-- Footer separator -->
								<div class="w-full h-px bg-gray-100 dark:bg-gray-700 mt-auto mb-4"></div>

								<!-- Due Date Footer -->
								<div class="flex justify-between items-center mt-auto">
									<span class="text-gray-400 dark:text-gray-500 text-xs">
										{#if assignment.status === 'overdue'}
											{$i18n.t('Due')}: {assignment.due} ({$i18n.t('Late')})
										{:else}
											{$i18n.t('Due')}: {assignment.due}
										{/if}
									</span>
								</div>

								<!-- Action Button -->
								<button 
									on:click={async () => {
										await goto(`/student/assignments?take=${assignment.quiz_code}`);
										await startQuizTakingFlow(assignment.quiz_code);
									}}
									class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl py-3 text-center transition-colors mt-4"
								>
									{$i18n.t('Start Quiz')}
								</button>
							{:else}
								<!-- Completed state statistics -->
								<div class="bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800 rounded-xl p-4 mt-2 space-y-2 flex-1">
									<div class="grid grid-cols-2 gap-3 text-xs text-slate-600 dark:text-slate-350">
										<div class="flex flex-col">
											<span class="text-[9px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black">Score</span>
											<span class="font-extrabold text-[13px] text-emerald-600 dark:text-emerald-400 mt-0.5">
												Score: {assignment.score}/{assignment.total}
											</span>
										</div>
										<div class="flex flex-col">
											<span class="text-[9px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black">Temps passé</span>
											<span class="font-semibold text-slate-700 dark:text-slate-200 mt-0.5">
												Temps passé: {assignment.time_spent || '1'} min
											</span>
										</div>
										<div class="flex flex-col col-span-2 border-t border-slate-100 dark:border-slate-800 pt-2">
											<span class="text-[9px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black">Date d'accès</span>
											<span class="font-semibold text-slate-700 dark:text-slate-200 mt-0.5">
												Fait le: {formatDate(assignment.submitted_at)}
											</span>
										</div>
										<div class="flex flex-col col-span-2">
											<span class="text-[9px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black">Limite</span>
											<span class="font-semibold text-slate-500 dark:text-slate-400 mt-0.5">
												Dernier délai: {assignment.due || 'Pas de date limite'}
											</span>
										</div>
									</div>
								</div>
							{/if}
						</div>
					</div>
				{/each}
			</div>

			<!-- Pagination -->
			<div class="flex justify-between items-center mt-auto pt-4 pb-2 px-2">
				<button class="text-gray-300 dark:text-gray-600 text-sm font-medium hover:text-gray-500 transition-colors" disabled>
					{$i18n.t('Back')}
				</button>
				<button class="text-gray-300 dark:text-gray-600 text-sm font-medium hover:text-gray-500 transition-colors" disabled>
					{$i18n.t('Next')}
				</button>
			</div>
		{:else}
			<div class="bg-gray-50 dark:bg-gray-800/50 rounded-2xl border border-dashed border-gray-200 dark:border-gray-700 p-12 text-center mt-6 flex-1 flex flex-col justify-center items-center">
				<div class="w-16 h-16 bg-white dark:bg-gray-700 rounded-full flex items-center justify-center mb-4 shadow-sm">
					<svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path></svg>
				</div>
				<h3 class="text-lg font-medium text-slate-700 dark:text-white mb-2">{$i18n.t('No assignments right now')}</h3>
				<p class="text-gray-500 dark:text-gray-400 max-w-sm mb-6">
					{$i18n.t('You are all caught up! Enable demo mode to see sample assignments or check back later.')}
				</p>
			</div>
		{/if}
	</div>
</div>
{:else}
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

					<button
						type="button"
						class="w-full py-2.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold transition-all"
						on:click={() => { state = 'dashboard'; }}
					>
						{$i18n.t('Annuler')}
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
						<div class="flex items-center gap-2 px-3.5 py-2 bg-rose-50 dark:bg-rose-950/20 border border-rose-100/50 dark:border-rose-900/20 text-rose-600 dark:text-rose-400 rounded-xl text-xs font-black tracking-wider font-mono">
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
				{#if quizData.questions[currentQuestionIndex]}
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
				{/if}
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
				{#if scoreResult}
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
				{/if}

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
{/if}
