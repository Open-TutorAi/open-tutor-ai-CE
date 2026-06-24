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
	// Use null to represent "all" — avoids language-change comparison bugs
	let selectedSubject: string | null = null;
	let selectedStatusKey: string | null = null; // null='all', 'pending', 'completed'
	let showSubjectDropdown = false;
	let showStatusDropdown = false;

	// Reactive labels (update automatically when language changes)
	$: labelAllSubjects = $i18n.t('All Subjects');
	$: labelAllStatus = $i18n.t('All Status');
	$: labelPending = $i18n.t('Pending');
	$: labelCompleted = $i18n.t('Completed');
	$: statusLabel = selectedStatusKey === 'pending' ? labelPending
		: selectedStatusKey === 'completed' ? labelCompleted
		: labelAllStatus;

	function clickOutside(node: HTMLElement, callback: () => void) {
		function handleClick(e: MouseEvent) {
			if (!node.contains(e.target as Node)) callback();
		}
		document.addEventListener('mousedown', handleClick);
		return { destroy() { document.removeEventListener('mousedown', handleClick); } };
	}

	// Reactive filtered assignments based on selected filters
	$: filteredAssignments = assignments.filter(a => {
	  const subjectMatch = selectedSubject === null || a.course === selectedSubject;
	  const statusMatch = selectedStatusKey === null || a.status === selectedStatusKey;
	  return subjectMatch && statusMatch;
	});

	async function fetchAssignments() {
		const token = localStorage.getItem('token') ?? '';
		let joinedCodes: string[] = [];
		try {
			const userId = $user?.id || 'anonymous';
			joinedCodes = JSON.parse(localStorage.getItem(`joined_quiz_codes_${userId}`) || '[]');
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

			// ✅ NOUVEAU: Ouvrir directement le popup de code si demandé depuis Dashboard
			const openCodeParam = $page.url.searchParams.get('openCode');
			if (openCodeParam === '1' && state === 'dashboard') {
				state = 'code_entry';
				goto('/student/assignments', { replaceState: true });
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
					const userId = $user?.id || 'anonymous';
					joinedCodes = JSON.parse(localStorage.getItem(`joined_quiz_codes_${userId}`) || '[]');
					if (!joinedCodes.includes(newAssignment.quiz_code)) {
						joinedCodes.push(newAssignment.quiz_code);
						localStorage.setItem(`joined_quiz_codes_${userId}`, JSON.stringify(joinedCodes));
					}
				} catch (e) {}
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

	// Remove quiz access (student removes quiz from their list)
	let quizToRemove: any = null;

	async function removeAssignment() {
		if (!quizToRemove) return;
		const quizId = quizToRemove.id ?? quizToRemove.quiz_id;
		const token = localStorage.getItem('token') ?? '';
		try {
			await fetch(`/api/v1/student/assignments/${quizId}`, {
				method: 'DELETE',
				headers: { Authorization: `Bearer ${token}` }
			});
			assignments = assignments.filter((a: any) => (a.id ?? a.quiz_id) !== quizId);
		} catch (e) {
			toast.error($i18n.t('Error removing quiz'));
		} finally {
			quizToRemove = null;
		}
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

	// Auto-join if quiz code is passed in URL query param
	onMount(async () => {
		const params = new URLSearchParams(window.location.search);
		const codeParam = params.get('code');
		if (codeParam && codeParam.length === 6) {
			quizCode = codeParam.toUpperCase();
			await joinQuiz();
		}
	});

	// Clean up timer interval on destroy
	onDestroy(() => {
		if (timerInterval) clearInterval(timerInterval);
	});
</script>

{#if state === 'dashboard'}
<div class="asgn-page">
<div class="asgn-wrapper">

	<!-- Hero Banner -->
	<div class="asgn-hero">
		<div class="asgn-hero-inner">
			<div class="asgn-hero-icon">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="24" height="24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
				</svg>
			</div>
			<div>
				<h1 class="asgn-hero-title">{$i18n.t('Welcome back')}, {username}!</h1>
				<p class="asgn-hero-sub">{$i18n.t('You have {{count}} upcoming deadlines this week. Stay focused and keep learning !', { count: upcomingDeadlines })}</p>
			</div>
		</div>
		<div class="asgn-hero-stat">
			<span class="asgn-stat-num">{upcomingDeadlines}</span>
			<span class="asgn-stat-label">{$i18n.t('à rendre')}</span>
		</div>
	</div>

	<!-- Main panel -->
	<div class="asgn-panel">

		<!-- Toolbar -->
		<div class="asgn-toolbar">
			<div class="asgn-toolbar-left">
				<div class="asgn-panel-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="20" height="20">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
					</svg>
				</div>
				<div>
					<h2 class="asgn-panel-title">{$i18n.t('My Assignments')}</h2>
					<p class="asgn-panel-sub">{filteredAssignments.length} {$i18n.t('assignments')}</p>
				</div>
			</div>
			<div class="flex flex-wrap items-center gap-3">
				<!-- Subject filter -->
				<div class="relative" use:clickOutside={() => showSubjectDropdown = false}>
					<button
						on:click={() => { showSubjectDropdown = !showSubjectDropdown; showStatusDropdown = false; }}
						class="flex items-center gap-2 py-2 pl-4 pr-3 rounded-full text-sm shadow-sm transition-all border
							{selectedSubject !== null
								? 'bg-blue-50 dark:bg-blue-900/30 border-blue-400 text-blue-600 dark:text-blue-300'
								: 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:shadow'}"
					>
						<svg class="w-4 h-4 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
						</svg>
						<span class="max-w-[120px] truncate">{selectedSubject ?? labelAllSubjects}</span>
						{#if selectedSubject !== null}
							<button on:click|stopPropagation={() => selectedSubject = null} class="ml-0.5 text-blue-400 hover:text-blue-600">
								<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/></svg>
							</button>
						{:else}
							<svg class="w-4 h-4 transition-transform duration-200 {showSubjectDropdown ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
							</svg>
						{/if}
					</button>

					{#if showSubjectDropdown}
						<div transition:fly={{ y: -6, duration: 150 }} class="absolute left-0 top-full mt-2 min-w-[180px] bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-100 dark:border-gray-700 overflow-hidden z-50 py-1">
							<button
								on:click={() => { selectedSubject = null; showSubjectDropdown = false; }}
								class="w-full text-left px-4 py-2.5 text-sm transition-colors flex items-center gap-2
									{selectedSubject === null ? 'text-blue-600 dark:text-blue-400 font-semibold bg-blue-50 dark:bg-blue-900/20' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}"
							>
								{#if selectedSubject === null}<svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>{:else}<span class="w-3.5 h-3.5 inline-block"/>{/if}
								{labelAllSubjects}
							</button>
							{#each Array.from(new Set(assignments.map(a => a.course))) as subj}
								<button
									on:click={() => { selectedSubject = subj; showSubjectDropdown = false; }}
									class="w-full text-left px-4 py-2.5 text-sm transition-colors flex items-center gap-2
										{selectedSubject === subj ? 'text-blue-600 dark:text-blue-400 font-semibold bg-blue-50 dark:bg-blue-900/20' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}"
								>
									{#if selectedSubject === subj}<svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>{:else}<span class="w-3.5 h-3.5 inline-block"/>{/if}
									{subj}
								</button>
							{/each}
						</div>
					{/if}
				</div>

				<!-- Status filter -->
				<div class="relative" use:clickOutside={() => showStatusDropdown = false}>
					<button
						on:click={() => { showStatusDropdown = !showStatusDropdown; showSubjectDropdown = false; }}
						class="flex items-center gap-2 py-2 pl-4 pr-3 rounded-full text-sm shadow-sm transition-all border
							{selectedStatusKey !== null
								? 'bg-violet-50 dark:bg-violet-900/30 border-violet-400 text-violet-600 dark:text-violet-300'
								: 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:shadow'}"
					>
						{#if selectedStatusKey === 'pending'}
							<span class="w-2 h-2 rounded-full bg-yellow-400 flex-shrink-0"></span>
						{:else if selectedStatusKey === 'completed'}
							<span class="w-2 h-2 rounded-full bg-green-400 flex-shrink-0"></span>
						{:else}
							<svg class="w-4 h-4 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
							</svg>
						{/if}
						<span>{statusLabel}</span>
						{#if selectedStatusKey !== null}
							<button on:click|stopPropagation={() => selectedStatusKey = null} class="ml-0.5 text-violet-400 hover:text-violet-600">
								<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/></svg>
							</button>
						{:else}
							<svg class="w-4 h-4 transition-transform duration-200 {showStatusDropdown ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
							</svg>
						{/if}
					</button>

					{#if showStatusDropdown}
						<div transition:fly={{ y: -6, duration: 150 }} class="absolute left-0 top-full mt-2 w-44 bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-100 dark:border-gray-700 overflow-hidden z-50 py-1">
							{#each [
								{ key: null, label: labelAllStatus, dot: null },
								{ key: 'pending', label: labelPending, dot: 'bg-yellow-400' },
								{ key: 'completed', label: labelCompleted, dot: 'bg-green-400' }
							] as opt}
								<button
									on:click={() => { selectedStatusKey = opt.key; showStatusDropdown = false; }}
									class="w-full text-left px-4 py-2.5 text-sm transition-colors flex items-center gap-2.5
										{selectedStatusKey === opt.key ? 'text-violet-600 dark:text-violet-400 font-semibold bg-violet-50 dark:bg-violet-900/20' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}"
								>
									{#if opt.dot}
										<span class="w-2 h-2 rounded-full {opt.dot} flex-shrink-0"></span>
									{:else}
										<svg class="w-3.5 h-3.5 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
									{/if}
									{opt.label}
									{#if selectedStatusKey === opt.key}
										<svg class="w-3.5 h-3.5 ml-auto" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
									{/if}
								</button>
							{/each}
						</div>
					{/if}
				</div>

				<button
					on:click={() => { state = 'code_entry'; }}
					class="bg-blue-500 text-white py-2 px-6 rounded-full hover:bg-blue-600 shadow-sm shadow-blue-500/30 transition-colors text-sm font-medium"
				>
					{$i18n.t('Enter Quiz Code')} 🚀
				</button>
			</div>
		</div>
		<div class="asgn-divider"></div>

		<!-- Grid -->
		{#if filteredAssignments.length > 0}
			<div class="asgn-grid">
				{#each filteredAssignments as assignment (assignment.id)}
					<div class="asgn-card">
						<!-- Top colored bar -->
						<div class="h-3 w-full {getTopBorderColor(assignment.status)}"></div>
						
						<div class="p-6 flex flex-col flex-1">
							<!-- Subject & Points -->
							<div class="flex justify-between items-center mb-4">
								<span class="bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 text-xs font-medium px-3 py-1 rounded-md">
									{assignment.course}
								</span>
								<div class="flex items-center gap-2">
									<span class="text-gray-400 dark:text-gray-500 text-xs font-medium">
										{assignment.points} {$i18n.t('points')}
									</span>
									<button
										class="w-6 h-6 flex items-center justify-center rounded-full text-gray-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
										on:click|stopPropagation={() => (quizToRemove = assignment)}
										title={$i18n.t('Remove')}
									>
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="12" height="12">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/>
										</svg>
									</button>
								</div>
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

										<!-- Best score (highlighted) -->
										<div class="flex flex-col col-span-2">
											<span class="text-[9px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black">{$i18n.t('Best score')}</span>
											<span class="font-extrabold text-[15px] text-emerald-600 dark:text-emerald-400 mt-0.5">
												{assignment.best_score ?? assignment.score}/{assignment.total}
											</span>
										</div>

										<!-- Individual attempts -->
										{#if assignment.attempts && assignment.attempts.length > 0}
											{#each assignment.attempts as attempt}
												<div class="flex flex-col col-span-2 border-t border-slate-100 dark:border-slate-800 pt-2">
													<span class="text-[9px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black">
														{$i18n.t('Attempt')} {attempt.attempt}
													</span>
													<div class="flex justify-between items-center mt-0.5">
														<span class="font-semibold text-[12px] {attempt.score === (assignment.best_score ?? assignment.score) && assignment.attempts.length > 1 ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-700 dark:text-slate-200'}">
															{attempt.score}/{attempt.total}
															{#if attempt.score === (assignment.best_score ?? assignment.score) && assignment.attempts.length > 1}
																<span class="text-[9px] bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 px-1.5 py-0.5 rounded-full ml-1">{$i18n.t('Best')}</span>
															{/if}
														</span>
														<span class="text-[10px] text-slate-400">{formatDate(attempt.submitted_at)}</span>
													</div>
												</div>
											{/each}
										{:else}
											<!-- Fallback for old data without attempts array -->
											<div class="flex flex-col">
												<span class="text-[9px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black">Temps passé</span>
												<span class="font-semibold text-slate-700 dark:text-slate-200 mt-0.5">{assignment.time_spent || '1'} min</span>
											</div>
											<div class="flex flex-col col-span-2 border-t border-slate-100 dark:border-slate-800 pt-2">
												<span class="text-[9px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black">Date d'accès</span>
												<span class="font-semibold text-slate-700 dark:text-slate-200 mt-0.5">Fait le: {formatDate(assignment.submitted_at)}</span>
											</div>
										{/if}

										<div class="flex flex-col col-span-2 border-t border-slate-100 dark:border-slate-800 pt-2">
											<span class="text-[9px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black">Limite</span>
											<span class="font-semibold text-slate-500 dark:text-slate-400 mt-0.5">
												Dernier délai: {assignment.due || 'Pas de date limite'}
											</span>
										</div>
									</div>
								</div>

								<!-- Retake button: only if failed AND only 1 attempt done -->
								{#if assignment.score !== null && assignment.score !== undefined && assignment.score < assignment.total && (assignment.submission_count ?? 1) < 2}
									<button
										on:click={async () => {
											await goto(`/student/assignments?take=${assignment.quiz_code}`);
											await startQuizTakingFlow(assignment.quiz_code);
										}}
										class="retake-btn"
									>
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5">
											<path d="M1 4v6h6M23 20v-6h-6"/>
											<path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
										</svg>
										{$i18n.t('Retake Quiz')}
									</button>
								{/if}
							{/if}
						</div>
					</div>
				{/each}
			</div>

			{:else}
			<div class="asgn-empty">
				<div class="asgn-empty-icon">
					<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="28" height="28">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
					</svg>
				</div>
				<h3 class="asgn-empty-title">{$i18n.t('No assignments right now')}</h3>
				<p class="asgn-empty-sub">{$i18n.t('You are all caught up! Enable demo mode to see sample assignments or check back later.')}</p>
			</div>
		{/if}

	</div><!-- /asgn-panel -->
</div><!-- /asgn-wrapper -->
</div><!-- /asgn-page -->
{:else}
<div class="min-h-screen bg-[#F8FAFC] dark:bg-[#090D1A] flex flex-col justify-center py-8 font-sans text-slate-800 dark:text-slate-100 transition-colors duration-300">
	<div class="max-w-2xl mx-auto w-full px-6">
		
		{#if state === 'code_entry'}
			<!-- ── SCREEN 1: CODE ENTRY ── -->
			<div in:fade={{ duration: 250 }} class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-lg shadow-sm p-8 space-y-8 relative overflow-hidden text-center">
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
					<div in:fly={{ x: 12, duration: 250 }} class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 rounded-lg p-6 md:p-8 shadow-sm space-y-6">
						
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
			<div in:fly={{ y: 20, duration: 400 }} class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-lg shadow-sm p-8 text-center space-y-6 relative overflow-hidden max-w-md mx-auto">
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
					<div class="bg-slate-50 dark:bg-slate-950/80 border border-slate-200/50 dark:border-slate-800 rounded-lg p-6 space-y-2 shadow-inner">
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

{#if quizToRemove}
	<div
		class="asgn-modal-overlay"
		role="button"
		tabindex="0"
		on:click={() => (quizToRemove = null)}
		on:keydown={(e) => e.key === 'Escape' && (quizToRemove = null)}
		in:fade={{ duration: 150 }}
		out:fade={{ duration: 100 }}
	>
		<div
			class="asgn-delete-modal"
			role="dialog"
			aria-modal="true"
			on:click|stopPropagation
			on:keydown|stopPropagation
			in:fly={{ y: 16, duration: 220 }}
		>
			<div class="asgn-delete-icon">
				<svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" width="22" height="22">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
				</svg>
			</div>
			<h3 class="asgn-delete-title">{$i18n.t('Remove this quiz?')}</h3>
			<p class="asgn-delete-name">«{quizToRemove.title}»</p>
			<div class="asgn-delete-actions">
				<button class="asgn-delete-cancel" on:click={() => (quizToRemove = null)}>
					{$i18n.t('Cancel')}
				</button>
				<button class="asgn-delete-confirm" on:click={removeAssignment}>
					{$i18n.t('Remove')}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

	/* ── Remove quiz modal ── */
	.asgn-modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(15, 23, 42, 0.6);
		backdrop-filter: blur(6px);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 10000;
	}
	.asgn-delete-modal {
		background: white;
		border-radius: 1.5rem;
		padding: 2rem 1.75rem;
		max-width: 360px;
		width: 92%;
		box-shadow: 0 24px 48px -8px rgba(0,0,0,0.22), 0 0 0 1px rgba(0,0,0,0.04);
		text-align: center;
	}
	:global(.dark) .asgn-delete-modal {
		background: #1e293b;
		border: 1px solid #334155;
	}
	.asgn-delete-icon {
		width: 52px;
		height: 52px;
		background: #fef2f2;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto 1.25rem;
	}
	:global(.dark) .asgn-delete-icon { background: rgba(239,68,68,0.12); }
	.asgn-delete-title {
		font-size: 1rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 .5rem;
	}
	:global(.dark) .asgn-delete-title { color: #f1f5f9; }
	.asgn-delete-name {
		font-size: .83rem;
		color: #64748b;
		margin: 0 0 1.5rem;
	}
	.asgn-delete-actions {
		display: flex;
		gap: .75rem;
	}
	.asgn-delete-cancel,
	.asgn-delete-confirm {
		flex: 1;
		padding: .65rem 1rem;
		border-radius: .75rem;
		font-size: .875rem;
		font-weight: 600;
		cursor: pointer;
		white-space: nowrap;
		transition: background .15s;
	}
	.asgn-delete-cancel {
		background: white;
		border: 1px solid #e2e8f0;
		color: #64748b;
	}
	:global(.dark) .asgn-delete-cancel {
		background: #1e293b;
		border-color: #334155;
		color: #94a3b8;
	}
	.asgn-delete-cancel:hover { background: #f8fafc; }
	:global(.dark) .asgn-delete-cancel:hover { background: #273549; }
	.asgn-delete-confirm {
		background: #ef4444;
		border: none;
		color: white;
	}
	.asgn-delete-confirm:hover { background: #dc2626; }

	/* ── Retake button ── */
	.retake-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: .45rem;
		width: 100%;
		margin-top: .75rem;
		padding: .6rem 1rem;
		border-radius: .875rem;
		background: linear-gradient(135deg, #f59e0b, #d97706);
		color: white;
		font-size: .8125rem;
		font-weight: 700;
		border: none;
		cursor: pointer;
		transition: opacity .15s, transform .12s;
		white-space: nowrap;
	}
	.retake-btn:hover { opacity: .88; transform: translateY(-1px); }
	.retake-btn:active { transform: translateY(0); opacity: 1; }

	/* ── Page wrapper ── */
	.asgn-page {
		font-family: 'Plus Jakarta Sans', sans-serif;
		max-width: 1100px;
		margin: 0 auto;
		padding: 1.5rem;
		min-height: 100%;
	}
	.asgn-wrapper {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	/* ── Hero banner ── */
	.asgn-hero {
		background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
		border-radius: 1.5rem;
		padding: 1.75rem 2rem;
		color: white;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		position: relative;
		overflow: hidden;
	}
	.asgn-hero::after {
		content: '';
		position: absolute;
		top: -60px; right: -60px;
		width: 200px; height: 200px;
		background: rgba(255,255,255,0.07);
		border-radius: 50%;
	}
	.asgn-hero-inner {
		display: flex;
		align-items: center;
		gap: 1rem;
		position: relative;
		z-index: 1;
	}
	.asgn-hero-icon {
		width: 52px; height: 52px;
		background: rgba(255,255,255,0.15);
		border-radius: 1rem;
		display: flex; align-items: center; justify-content: center;
		flex-shrink: 0;
		backdrop-filter: blur(4px);
	}
	.asgn-hero-title {
		font-size: 1.5rem;
		font-weight: 700;
		margin: 0 0 0.25rem;
		color: white;
	}
	.asgn-hero-sub {
		font-size: 0.85rem;
		color: rgba(255,255,255,0.75);
		margin: 0;
	}
	.asgn-hero-stat {
		display: flex;
		flex-direction: column;
		align-items: center;
		background: rgba(255,255,255,0.15);
		border-radius: 1rem;
		padding: 0.75rem 1.25rem;
		backdrop-filter: blur(4px);
		flex-shrink: 0;
		position: relative;
		z-index: 1;
	}
	.asgn-stat-num {
		font-size: 2rem;
		font-weight: 800;
		line-height: 1;
		color: white;
	}
	.asgn-stat-label {
		font-size: 0.7rem;
		color: rgba(255,255,255,0.75);
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-top: 0.2rem;
	}

	/* ── Main panel ── */
	.asgn-panel {
		background: white;
		border-radius: 1.5rem;
		border: 1px solid #e2e8f0;
		box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
		overflow: visible;
	}
	:global(.dark) .asgn-panel { background: #1e293b; border-color: #334155; }

	/* ── Toolbar ── */
	.asgn-toolbar {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		padding: 1.5rem 2rem;
	}
	.asgn-toolbar-left {
		display: flex;
		align-items: center;
		gap: 0.875rem;
	}
	.asgn-panel-icon {
		width: 44px; height: 44px;
		background: #eef2ff;
		color: #2563eb;
		border-radius: 0.875rem;
		display: flex; align-items: center; justify-content: center;
		flex-shrink: 0;
	}
	:global(.dark) .asgn-panel-icon { background: #1e3a8a; color: #93c5fd; }
	.asgn-panel-title {
		font-size: 1.1rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.15rem;
	}
	:global(.dark) .asgn-panel-title { color: white; }
	.asgn-panel-sub {
		font-size: 0.78rem;
		color: #94a3b8;
		margin: 0;
	}

	.asgn-divider { height: 1px; background: #f1f5f9; margin: 0 2rem; }
	:global(.dark) .asgn-divider { background: #334155; }

	/* ── Cards grid ── */
	.asgn-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
		gap: 1.25rem;
		padding: 1.5rem 2rem 2rem;
	}
	.asgn-card {
		background: white;
		border-radius: 0.5rem;
		border: 1px solid #e2e8f0;
		box-shadow: 0 1px 3px rgba(0,0,0,0.05);
		overflow: hidden;
		display: flex;
		flex-direction: column;
		transition: transform 0.2s ease, box-shadow 0.2s ease;
		min-height: 280px;
		padding-bottom: 1.25rem;
	}
	.asgn-card:hover {
		transform: translateY(-3px);
		box-shadow: 0 10px 28px rgba(0,0,0,0.09);
	}
	:global(.dark) .asgn-card { background: #0f172a; border-color: #1e293b; }

	/* ── Empty state ── */
	.asgn-empty {
		padding: 3.5rem 2rem;
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
	}
	.asgn-empty-icon {
		width: 60px; height: 60px;
		background: #f1f5f9;
		border-radius: 1.25rem;
		display: flex; align-items: center; justify-content: center;
		color: #94a3b8;
		margin-bottom: 1rem;
	}
	:global(.dark) .asgn-empty-icon { background: #334155; }
	.asgn-empty-title {
		font-size: 1.1rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.5rem;
	}
	:global(.dark) .asgn-empty-title { color: white; }
	.asgn-empty-sub {
		font-size: 0.875rem;
		color: #94a3b8;
		max-width: 360px;
		margin: 0;
		line-height: 1.6;
	}

	/* ── Responsive ── */
	@media (max-width: 640px) {
		.asgn-page { padding: 1rem; }
		.asgn-hero { flex-direction: column; align-items: flex-start; padding: 1.25rem; }
		.asgn-hero-title { font-size: 1.2rem; }
		.asgn-hero-stat { align-self: stretch; flex-direction: row; justify-content: center; gap: 0.5rem; }
		.asgn-toolbar { padding: 1.25rem; }
		.asgn-divider { margin: 0 1.25rem; }
		.asgn-grid { grid-template-columns: 1fr; padding: 1.25rem; }
	}
</style>
