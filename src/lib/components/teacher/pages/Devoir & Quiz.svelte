<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount, getContext } from 'svelte';
	import { browser } from '$app/environment';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { fade, fly } from 'svelte/transition';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// --- Tabs & Steps ---
	let activeTab: 'create' | 'analytics' = 'create';
	let step: number = 1; // 1: Form, 2: Review, 3: Success

	// --- Dynamic Inputs from API ---
	let courses: any[] = [];
	let selectedCourse: string = '';
	let models: any[] = [];
	let selectedModel: string = 'gpt-4o-mini';

	// --- Step 1 Quiz State ---
	let quizTitle: string = '';
	let aiPrompt: string = '';
	let selectedQuestionTypes: string[] = ['QCM']; // default selection
	let totalQuestions: number = 5;
	let limitTime: boolean = true;
	let timeMinutes: number = 20;
	let dueDate: string = '';

	// --- Step 2 Editing & Review ---
	let generatedQuizId: string = '';
	let questions: any[] = [];
	let isGenerating: boolean = false;
	let isPublishing: boolean = false;

	// --- Step 3 Success ---
	let publishedCode: string = '';
	let copied: boolean = false;

	// --- Analytics State ---
	let teacherQuizzes: any[] = [];
	let selectedQuizForAnalytics: string = '';
	let analyticsData: any = null;
	let isLoadingAnalytics: boolean = false;

	// On Mount: Load Courses and Models
	onMount(async () => {
		const token = localStorage.getItem('token') ?? '';
		dueDate = new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0]; // Default 7 days from now
		quizTitle = $i18n.t('Quiz hebdomadaire');
		aiPrompt = $i18n.t('');

		await fetchCourses(token);
		await fetchModels(token);
		await fetchTeacherQuizzes(token);
	});

	// Reactively fetch analytics when the selected quiz changes
	$: if (selectedQuizForAnalytics) {
		fetchAnalytics(selectedQuizForAnalytics);
	}

	async function fetchCourses(token: string) {
		try {
			const res = await fetch('/api/v1/teacher/courses/', {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				courses = await res.json();
				if (courses.length > 0) {
					selectedCourse = courses[0].id;
				}
			}
		} catch (e) {
			console.error('Error fetching courses:', e);
		}
	}

	async function fetchModels(token: string) {
		try {
			const res = await fetch('/api/v1/teacher/courses/models/available', {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				const data = await res.json();
				if (data.status === 'ok') {
					models = data.data;
					const hasMini = models.find((m) => m.id === 'gpt-4o-mini');
					selectedModel = hasMini ? 'gpt-4o-mini' : (models[0]?.id ?? 'gpt-4o-mini');
				}
			}
		} catch (e) {
			console.error('Error fetching models:', e);
		}
	}

	async function fetchTeacherQuizzes(token: string) {
		try {
			const res = await fetch('/api/v1/quizzes/teacher', {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				teacherQuizzes = await res.json();
				const publishedOnly = teacherQuizzes.filter((q) => q.status === 'published');
				if (publishedOnly.length > 0) {
					selectedQuizForAnalytics = publishedOnly[0].id;
				}
			}
		} catch (e) {
			console.error('Error fetching teacher quizzes:', e);
		}
	}

	async function fetchAnalytics(quizId: string) {
		isLoadingAnalytics = true;
		analyticsData = null;
		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`/api/v1/quizzes/teacher/analytics/${quizId}`, {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				analyticsData = await res.json();
			}
		} catch (e) {
			console.error('Error fetching analytics:', e);
		} finally {
			isLoadingAnalytics = false;
		}
	}

	// Toggle Question Types
	function toggleQuestionType(type: string) {
		if (selectedQuestionTypes.includes(type)) {
			selectedQuestionTypes = selectedQuestionTypes.filter((t) => t !== type);
		} else {
			selectedQuestionTypes = [...selectedQuestionTypes, type];
		}
	}

	// Action: Generate Quiz via LLM
	async function handleGenerate() {
		if (!aiPrompt.trim()) {
			alert($i18n.t('Veuillez saisir un sujet ou une consigne pour le quiz.'));
			return;
		}
		if (selectedQuestionTypes.length === 0) {
			alert($i18n.t('Veuillez sélectionner au moins un type de question.'));
			return;
		}

		isGenerating = true;
		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch('/api/v1/quizzes/generate', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`
				},
				body: JSON.stringify({
					title: quizTitle,
					topic: aiPrompt,
					question_types: selectedQuestionTypes,
					total_questions: totalQuestions,
					model: selectedModel,
					time_limit: limitTime ? timeMinutes : null,
					limit_date: dueDate || null,
					course_id: selectedCourse || null
				})
			});

			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? 'Erreur lors de la génération');
			}

			const data = await res.json();
			generatedQuizId = data.id;
			questions = data.questions;
			step = 2; // Move to Review Screen
		} catch (e: any) {
			alert(e.message ?? $i18n.t('Erreur de génération avec le LLM'));
		} finally {
			isGenerating = false;
		}
	}

	// Action: Publish Quiz and Get Code
	async function handlePublish() {
		isPublishing = true;
		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`/api/v1/quizzes/publish/${generatedQuizId}`, {
				method: 'POST',
				headers: { Authorization: `Bearer ${token}` }
			});

			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? 'Erreur lors de la publication');
			}

			const data = await res.json();
			publishedCode = data.quiz_code;
			step = 3; // Success screen

			// Refresh teacher quizzes in background for analytics
			fetchTeacherQuizzes(token);
		} catch (e: any) {
			alert(e.message ?? $i18n.t('Erreur lors de la publication'));
		} finally {
			isPublishing = false;
		}
	}

	// Add manual blank question in review step
	let manualQuestionType: string = 'QCM';

	function addManualQuestion() {
		const isQCM = manualQuestionType === 'QCM';
		questions = [
			...questions,
			{
				id: 'manual_' + Math.random().toString(36).substr(2, 9),
				question_type: manualQuestionType,
				question_text: $i18n.t('Nouvelle question'),
				options: isQCM ? [$i18n.t('Option A'), $i18n.t('Option B')] : [],
				correct_answer: isQCM ? $i18n.t('Option A') : ''
			}
		];
	}

	// Delete question in review step
	function deleteQuestion(index: number) {
		questions = questions.filter((_, i) => i !== index);
	}

	// Clipboard Copy Helper
	async function copyCodeToClipboard() {
		await navigator.clipboard.writeText(publishedCode);
		copied = true;
		setTimeout(() => (copied = false), 2500);
	}

	function resetQuizCreator() {
		step = 1;
		quizTitle = $i18n.t('Quiz');
		aiPrompt = '';
		questions = [];
		publishedCode = '';
	}
</script>

<div
	class="min-h-screen bg-[#F8FAFC] dark:bg-[#090D1A] overflow-y-auto font-sans text-slate-800 dark:text-slate-100 transition-colors duration-300"
>
	<div class="max-w-6xl mx-auto p-6 md:p-8 space-y-8">
		<!-- ── HEADER ── -->
		<div
			class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-100 dark:border-slate-800/80 pb-6"
		>
			<div>
				<h1
					class="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-600 bg-clip-text text-transparent"
				>
					{$i18n.t('Assignments & Quizzes')}
				</h1>
				<p class="text-sm text-slate-400 dark:text-slate-500 mt-1 font-medium">
					{$i18n.t(
						"Générez des évaluations intelligentes avec l'IA et suivez la réussite des étudiants."
					)}
				</p>
			</div>

			<!-- Tab Controls -->
			<div
				class="flex bg-slate-100 dark:bg-slate-900/60 p-1.5 rounded-2xl border border-slate-200/50 dark:border-slate-800/30"
			>
				<button
					class="px-5 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200 {activeTab ===
					'create'
						? 'bg-white dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 shadow-sm'
						: 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}"
					on:click={() => (activeTab = 'create')}
				>
					{$i18n.t('Créer un Quiz')}
				</button>
				<button
					class="px-5 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200 {activeTab ===
					'analytics'
						? 'bg-white dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 shadow-sm'
						: 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}"
					on:click={() => (activeTab = 'analytics')}
				>
					{$i18n.t('Analyses & Stats')}
				</button>
			</div>
		</div>

		{#if activeTab === 'create'}
			<!-- ── TAB: CREATE QUIZ ── -->
			{#if step === 1}
				<!-- Screen 1: Config Form -->
				<div in:fade={{ duration: 200 }} class="grid grid-cols-1 lg:grid-cols-3 gap-8">
					<!-- Main Inputs -->
					<div class="lg:col-span-2 space-y-6">
						<div
							class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 rounded-3xl p-6 md:p-8 shadow-sm space-y-6"
						>
							<div class="space-y-2">
								<label
									for="quiz-title"
									class="text-xs font-black uppercase tracking-widest text-slate-400"
									>{$i18n.t("Titre de l'évaluation")}</label
								>
								<input
									id="quiz-title"
									type="text"
									bind:value={quizTitle}
									placeholder={$i18n.t('Ex:')}
									class="w-full px-5 py-3.5 bg-slate-50 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800/60 rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500/20 dark:text-slate-100 transition-all font-semibold"
								/>
							</div>

							<div class="space-y-2">
								<label
									for="course-select"
									class="text-xs font-black uppercase tracking-widest text-slate-400"
								>
									{$i18n.t('Associer à un Cours')}
								</label>
								<select
									id="course-select"
									bind:value={selectedCourse}
									class="w-full px-5 py-3.5 bg-slate-50 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800/60 rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500/20 dark:text-slate-100 transition-all font-semibold"
								>
									{#if courses.length === 0}
										<option value="">{$i18n.t('Aucun cours disponible')}</option>
									{:else}
										{#each courses as c}
											<option value={c.id}>{c.title}</option>
										{/each}
									{/if}
								</select>
							</div>

							<!-- AI Prompt Instruction Box -->
							<div
								class="bg-gradient-to-br from-indigo-50/50 via-purple-50/30 to-indigo-50/20 dark:from-indigo-950/20 dark:to-purple-950/10 p-6 rounded-3xl border border-indigo-100/50 dark:border-indigo-900/30 space-y-4"
							>
								<div class="flex items-center gap-3">
									<span class="text-2xl">✨</span>
									<div>
										<h3 class="font-bold text-slate-800 dark:text-slate-200 text-sm">
											{$i18n.t('Générateur Intelligent de Quiz')}
										</h3>
										<p class="text-xs text-slate-400 dark:text-slate-500">
											{$i18n.t("Décrivez le sujet ci-dessous, le LLM s'occupe du reste.")}
										</p>
									</div>
								</div>

								<textarea
									bind:value={aiPrompt}
									rows="4"
									placeholder={$i18n.t('Décrivez le sujet précis et les notions clés à tester...')}
									class="w-full p-4 bg-white dark:bg-slate-950 border border-slate-200/40 dark:border-slate-800/40 rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500/20 dark:text-slate-100 transition-all resize-none text-sm font-medium"
								></textarea>
							</div>
						</div>
					</div>

					<!-- Sidebar Config Options -->
					<div class="space-y-6">
						<div
							class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 rounded-3xl p-6 md:p-8 shadow-sm space-y-6"
						>
							<h3
								class="text-xs font-black uppercase tracking-widest text-slate-400 border-b border-slate-100 dark:border-slate-800 pb-3"
							>
								{$i18n.t('Paramètres et Formats')}
							</h3>

							<!-- Question Types Multi-Select Buttons -->
							<div class="space-y-3">
								<span class="text-xs font-bold text-slate-400">{$i18n.t('Types de Questions')}</span
								>
								<div class="flex flex-col gap-2">
									{#each ['QCM', 'True/False', 'Short Answer'] as qType}
										<button
											type="button"
											class="flex items-center justify-between px-4 py-3 rounded-xl border text-xs font-bold transition-all {selectedQuestionTypes.includes(
												qType
											)
												? 'bg-indigo-50 dark:bg-indigo-950/40 border-indigo-500/30 text-indigo-600 dark:text-indigo-400 shadow-sm'
												: 'border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-400 bg-slate-50/50 dark:bg-slate-950/20'}"
											on:click={() => toggleQuestionType(qType)}
										>
											<span>{$i18n.t(qType)}</span>
											<span>{selectedQuestionTypes.includes(qType) ? '🟢' : '⚪'}</span>
										</button>
									{/each}
								</div>
							</div>

							<!-- Total Questions Selection Slider -->
							<div class="space-y-2">
								<div class="flex justify-between text-xs font-bold">
									<span class="text-slate-400">{$i18n.t('Nombre de Questions')}</span>
									<span class="text-indigo-600 dark:text-indigo-400">{totalQuestions}</span>
								</div>
								<input
									type="range"
									min="5"
									max="20"
									bind:value={totalQuestions}
									class="w-full accent-indigo-600 dark:accent-indigo-500"
								/>
							</div>

							<!-- Time limit checkbox and numerical inputs -->
							<div class="space-y-3 border-t border-slate-100 dark:border-slate-800/80 pt-4">
								<label class="flex items-center justify-between cursor-pointer">
									<span class="text-xs font-bold text-slate-400">{$i18n.t('Limite de temps')}</span>
									<input
										type="checkbox"
										bind:checked={limitTime}
										class="w-4 h-4 rounded text-indigo-600 accent-indigo-600"
									/>
								</label>
								{#if limitTime}
									<div
										class="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-800/80"
									>
										<input
											type="number"
											bind:value={timeMinutes}
											class="w-16 p-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm text-center font-bold text-indigo-600 dark:text-indigo-400 outline-none"
										/>
										<span class="text-[10px] uppercase font-black tracking-widest text-slate-400"
											>{$i18n.t('Minutes')}</span
										>
									</div>
								{/if}
							</div>

							<!-- Date Picker -->
							<div class="space-y-2">
								<label for="due-date" class="text-xs font-bold text-slate-400"
									>{$i18n.t('Date limite de rendu')}</label
								>
								<input
									id="due-date"
									type="date"
									bind:value={dueDate}
									class="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800 rounded-xl outline-none text-xs font-semibold"
								/>
							</div>

							<!-- Model Target Dropdown -->
							<div class="space-y-2">
								<label for="model-select" class="text-xs font-bold text-slate-400"
									>{$i18n.t('Modèle LLM cible')}</label
								>
								<select
									id="model-select"
									bind:value={selectedModel}
									class="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800 rounded-xl outline-none text-xs font-semibold"
								>
									{#each models as m}
										<option value={m.id}>{m.name}</option>
									{/each}
								</select>
							</div>

							<!-- Generate Action Button -->
							<button
								type="button"
								class="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-2xl text-xs font-black uppercase tracking-widest flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 active:scale-95 transition-all disabled:opacity-50"
								on:click={handleGenerate}
								disabled={isGenerating}
							>
								{#if isGenerating}
									<svg class="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
										<circle
											class="opacity-25"
											cx="12"
											cy="12"
											r="10"
											stroke="currentColor"
											stroke-width="4"
										></circle>
										<path
											class="opacity-75"
											fill="currentColor"
											d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
										></path>
									</svg>
									{$i18n.t('Génération en cours...')}
								{:else}
									<span>✨</span>
									{$i18n.t("Générer avec l'IA")}
								{/if}
							</button>
						</div>
					</div>
				</div>
			{/if}

			{#if step === 2}
				<!-- Screen 2: Review Draft and Edit Questions -->
				<div in:fade={{ duration: 200 }} class="space-y-6">
					<div
						class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 p-6 rounded-3xl shadow-sm"
					>
						<div>
							<span
								class="text-xs font-black bg-purple-100 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 px-3 py-1.5 rounded-full uppercase tracking-wider"
							>
								{$i18n.t('Brouillon généré')}
							</span>
							<h2 class="text-xl font-bold mt-2">{quizTitle}</h2>
							<p class="text-xs text-slate-400 mt-1">
								{$i18n.t("Vérifiez et modifiez les questions générées par l'IA avant de publier.")}
							</p>
						</div>
						<div class="flex items-center gap-3">
							<select
								bind:value={manualQuestionType}
								class="px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200/50 dark:border-slate-800 rounded-xl text-xs font-black uppercase tracking-wider text-slate-600 dark:text-slate-400 outline-none focus:ring-2 focus:ring-indigo-500/10 transition-all font-bold"
							>
								<option value="QCM">QCM</option>
								<option value="Short Answer">Short Answer</option>
								<option value="CODE_SANDBOX">Code Sandbox</option>
							</select>
							<button
								type="button"
								class="px-5 py-3 bg-slate-50 dark:bg-slate-950 hover:bg-slate-100 border border-slate-200/50 dark:border-slate-800 rounded-xl text-xs font-black uppercase tracking-wider text-slate-600 dark:text-slate-400"
								on:click={addManualQuestion}
							>
								{$i18n.t('+ Ajouter')}
							</button>
							<button
								type="button"
								class="px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white rounded-xl text-xs font-black uppercase tracking-wider flex items-center gap-2 shadow-lg shadow-emerald-500/10 disabled:opacity-50"
								on:click={handlePublish}
								disabled={isPublishing || questions.length === 0}
							>
								{#if isPublishing}
									<svg class="animate-spin h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="none">
										<circle
											class="opacity-25"
											cx="12"
											cy="12"
											r="10"
											stroke="currentColor"
											stroke-width="4"
										></circle>
										<path
											class="opacity-75"
											fill="currentColor"
											d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
										></path>
									</svg>
									{$i18n.t('Publication...')}
								{:else}
									<span>🚀</span>
									{$i18n.t('Valider & Publier')}
								{/if}
							</button>
						</div>
					</div>

					<!-- Interactive Editable Questions Grid -->
					<div class="space-y-6 pb-12">
						{#each questions as q, idx (q.id || idx)}
							<div
								class="bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800/80 shadow-sm overflow-hidden transition-all duration-200 hover:border-indigo-500/20"
							>
								<div
									class="px-6 py-4 bg-slate-50/50 dark:bg-slate-950/20 border-b border-slate-100 dark:border-slate-800/80 flex justify-between items-center"
								>
									<div class="flex items-center gap-3">
										<span
											class="text-xs font-black bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 px-3 py-1.5 rounded-full uppercase tracking-wider"
											>{q.question_type}</span
										>
										<span class="text-xs font-bold text-slate-400"
											>{$i18n.t('Question')} {idx + 1}</span
										>
									</div>
									<button
										class="text-slate-300 hover:text-red-500 p-2 rounded-lg transition-colors"
										on:click={() => deleteQuestion(idx)}
									>
										🗑️
									</button>
								</div>

								<div class="p-6 md:p-8 space-y-6">
									<div class="space-y-2">
										<label class="text-[10px] font-black uppercase tracking-wider text-slate-400"
											>{$i18n.t('Énoncé de la question')}</label
										>
										<textarea
											bind:value={q.question_text}
											rows="3"
											class="w-full p-4 bg-slate-50 dark:bg-slate-950 border border-slate-200/50 dark:border-slate-800/60 rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500/10 text-sm font-semibold"
										></textarea>
									</div>

									{#if q.question_type === 'QCM'}
										<!-- Editable Options for QCM -->
										<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
											{#each q.options as opt, optIdx}
												<div class="space-y-1">
													<label
														class="text-[9px] font-bold text-slate-400 uppercase tracking-widest"
														>{$i18n.t('Option')} {optIdx + 1}</label
													>
													<div class="flex gap-2">
														<input
															type="text"
															bind:value={q.options[optIdx]}
															class="flex-1 px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200/50 dark:border-slate-800/60 rounded-xl outline-none text-xs font-semibold"
														/>
														<button
															type="button"
															class="px-3 rounded-xl border text-[10px] font-bold {q.correct_answer ===
															opt
																? 'bg-emerald-500 text-white border-emerald-500'
																: 'border-slate-100 dark:border-slate-800 text-slate-400'}"
															on:click={() => (q.correct_answer = opt)}
														>
															✓
														</button>
													</div>
												</div>
											{/each}
										</div>
									{:else}
										<!-- Correct Answer Input -->
										<div class="space-y-2">
											<label class="text-[10px] font-black uppercase tracking-wider text-slate-400"
												>{$i18n.t('Réponse attendue')}</label
											>
											<input
												type="text"
												bind:value={q.correct_answer}
												class="w-full px-5 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200/50 dark:border-slate-800/60 rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500/10 text-xs font-bold text-emerald-600 dark:text-emerald-400"
											/>
										</div>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			{#if step === 3}
				<!-- Screen 3: Published Success & Shared Code -->
				<div in:fly={{ y: 20, duration: 400 }} class="max-w-xl mx-auto py-12">
					<div
						class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-[36px] shadow-2xl p-8 text-center space-y-6 relative overflow-hidden"
					>
						<!-- Confetti design -->
						<div
							class="absolute inset-x-0 top-0 h-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500"
						></div>

						<div
							class="w-16 h-16 bg-emerald-100 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 rounded-2xl flex items-center justify-center text-3xl mx-auto shadow-lg shadow-emerald-500/10"
						>
							🎉
						</div>

						<div class="space-y-2">
							<h2 class="text-2xl font-black text-slate-850 dark:text-slate-50">
								{$i18n.t('Quiz Publié avec Succès !')}
							</h2>
							<p class="text-sm text-slate-400 dark:text-slate-500">
								{$i18n.t(
									"Partagez le code ci-dessous avec vos étudiants pour qu'ils rejoignent l'épreuve instantanément."
								)}
							</p>
						</div>

						<!-- Shared Code Box -->
						<div
							class="bg-slate-50 dark:bg-slate-950/80 border border-slate-200/50 dark:border-slate-800 rounded-3xl p-6 space-y-3 shadow-inner"
						>
							<span class="text-[10px] font-black uppercase tracking-widest text-slate-400"
								>{$i18n.t('Code Unique de Partage')}</span
							>
							<div
								class="text-4xl md:text-5xl font-black font-mono tracking-wider text-indigo-600 dark:text-indigo-400"
							>
								{publishedCode}
							</div>
							<button
								type="button"
								class="px-5 py-2.5 rounded-full text-xs font-black uppercase tracking-widest flex items-center gap-2 mx-auto border transition-all {copied
									? 'bg-emerald-500 border-emerald-500 text-white shadow-lg'
									: 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-indigo-600'}"
								on:click={copyCodeToClipboard}
							>
								{copied ? $i18n.t('Copié !') : $i18n.t('Copier le Code')}
							</button>
						</div>

						<div class="flex gap-4 pt-4 border-t border-slate-100 dark:border-slate-800/80">
							<button
								type="button"
								class="flex-1 py-3.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200/80 dark:hover:bg-slate-700 rounded-2xl text-xs font-black uppercase tracking-wider text-slate-600 dark:text-slate-300"
								on:click={resetQuizCreator}
							>
								{$i18n.t('Nouveau Quiz')}
							</button>
							<button
								type="button"
								class="flex-1 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl text-xs font-black uppercase tracking-wider shadow-lg shadow-indigo-500/20"
								on:click={() => {
									activeTab = 'analytics';
									selectedQuizForAnalytics = generatedQuizId;
									step = 1;
								}}
							>
								{$i18n.t("Voir l'Évaluation")}
							</button>
						</div>
					</div>
				</div>
			{/if}
		{:else}
			<!-- ── TAB: STATS & ANALYTICS ── -->
			<div in:fade={{ duration: 200 }} class="space-y-6">
				<!-- Analytics Filter Selector -->
				<div
					class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 p-6 rounded-3xl shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
				>
					<div>
						<h2 class="text-lg font-bold">{$i18n.t("Sélection de l'Évaluation")}</h2>
						<p class="text-xs text-slate-400 mt-1">
							{$i18n.t(
								"Sélectionnez un quiz publié pour afficher son tableau de bord d'analytics."
							)}
						</p>
					</div>

					<select
						bind:value={selectedQuizForAnalytics}
						class="w-full md:w-80 px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800/60 rounded-xl outline-none text-sm font-bold text-slate-700 dark:text-slate-200"
					>
						{#if teacherQuizzes.filter((q) => q.status === 'published').length === 0}
							<option value="">{$i18n.t('Aucun quiz publié disponible')}</option>
						{:else}
							{#each teacherQuizzes.filter((q) => q.status === 'published') as quiz}
								<option value={quiz.id}>{quiz.title} ({quiz.quiz_code})</option>
							{/each}
						{/if}
					</select>
				</div>

				{#if isLoadingAnalytics}
					<div class="flex flex-col items-center justify-center py-16 gap-3">
						<svg class="animate-spin h-8 w-8 text-indigo-500" viewBox="0 0 24 24" fill="none">
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							></circle>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
							></path>
						</svg>
						<p class="text-xs text-slate-400">
							{$i18n.t('Chargement des analyses de réussite...')}
						</p>
					</div>
				{:else if analyticsData}
					<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
						<!-- Metric Cards -->
						<div
							class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 p-6 rounded-3xl shadow-sm text-center"
						>
							<span class="text-[10px] font-black uppercase tracking-widest text-slate-400"
								>{$i18n.t('Participants')}</span
							>
							<h3 class="text-4xl font-extrabold text-indigo-600 dark:text-indigo-400 mt-2">
								{analyticsData.total_participants}
							</h3>
						</div>

						<div
							class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 p-6 rounded-3xl shadow-sm text-center"
						>
							<span class="text-[10px] font-black uppercase tracking-widest text-slate-400"
								>{$i18n.t('Moyenne')}</span
							>
							<h3 class="text-4xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-2">
								{analyticsData.average_score}
							</h3>
						</div>

						<div
							class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 p-6 rounded-3xl shadow-sm text-center"
						>
							<span class="text-[10px] font-black uppercase tracking-widest text-slate-400"
								>{$i18n.t('Score Maximal')}</span
							>
							<h3 class="text-4xl font-extrabold text-purple-600 dark:text-purple-400 mt-2">
								{analyticsData.high_score}
							</h3>
						</div>

						<div
							class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 p-6 rounded-3xl shadow-sm text-center"
						>
							<span class="text-[10px] font-black uppercase tracking-widest text-slate-400"
								>{$i18n.t('Score Minimal')}</span
							>
							<h3 class="text-4xl font-extrabold text-rose-600 dark:text-rose-400 mt-2">
								{analyticsData.low_score}
							</h3>
						</div>
					</div>

					<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
						<!-- Submissions Roster -->
						<div
							class="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 rounded-[32px] p-6 shadow-sm space-y-4"
						>
							<h3 class="font-bold text-slate-800 dark:text-slate-100 text-sm">
								{$i18n.t('Scores Individuels')}
							</h3>

							{#if analyticsData.submissions.length === 0}
								<div class="text-center py-12">
									<p class="text-slate-400 text-xs">
										{$i18n.t('Aucune soumission reçue pour le moment.')}
									</p>
								</div>
							{:else}
								<div class="overflow-x-auto">
									<table class="w-full text-left text-xs border-collapse">
										<thead>
											<tr class="border-b border-slate-100 dark:border-slate-800/80">
												<th class="py-3 font-black text-slate-400 uppercase tracking-widest"
													>{$i18n.t('Étudiant')}</th
												>
												<th
													class="py-3 font-black text-slate-400 uppercase tracking-widest text-center"
													>{$i18n.t('Score')}</th
												>
												<th
													class="py-3 font-black text-slate-400 uppercase tracking-widest text-right"
													>{$i18n.t('Rendu')}</th
												>
											</tr>
										</thead>
										<tbody>
											{#each analyticsData.submissions as sub}
												<tr
													class="border-b border-slate-50 dark:border-slate-800/20 hover:bg-slate-50/50 dark:hover:bg-slate-950/20 transition-colors"
												>
													<td class="py-4 font-bold text-slate-700 dark:text-slate-350"
														>{sub.student_name}</td
													>
													<td
														class="py-4 font-black text-indigo-650 dark:text-indigo-400 text-center text-sm"
														>{sub.score}</td
													>
													<td class="py-4 text-slate-400 text-right font-medium"
														>{new Date(sub.submitted_at).toLocaleDateString() +
															' ' +
															new Date(sub.submitted_at).toLocaleTimeString([], {
																hour: '2-digit',
																minute: '2-digit'
															})}</td
													>
												</tr>
											{/each}
										</tbody>
									</table>
								</div>
							{/if}
						</div>

						<!-- Score Distribution Bar Chart -->
						<div
							class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 rounded-[32px] p-6 shadow-sm space-y-4"
						>
							<h3 class="font-bold text-slate-800 dark:text-slate-100 text-sm">
								{$i18n.t('Répartition des Notes')}
							</h3>

							{#if analyticsData.total_participants === 0}
								<p class="text-xs text-slate-400 italic">
									{$i18n.t('Pas de données disponibles.')}
								</p>
							{:else}
								<div class="space-y-3.5 pt-2">
									{#each Object.entries(analyticsData.distribution) as [score, count]}
										{@const percent = (count / analyticsData.total_participants) * 100}
										<div class="space-y-1">
											<div class="flex justify-between text-[11px] font-bold text-slate-500">
												<span>{$i18n.t('Score')} {score}</span>
												<span
													>{count} {count <= 1 ? $i18n.t('étudiant') : $i18n.t('étudiants')}</span
												>
											</div>
											<div
												class="h-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800/40 rounded-full overflow-hidden"
											>
												<div
													class="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full"
													style="width: {percent}%"
												></div>
											</div>
										</div>
									{/each}
								</div>
							{/if}
						</div>
					</div>
				{:else}
					<div
						class="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 p-12 text-center rounded-[32px]"
					>
						<p class="text-xs text-slate-400 font-medium">
							{$i18n.t('Sélectionnez une évaluation publiée pour charger ses données.')}
						</p>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	input[type='range'] {
		background: #cbd5e1;
		height: 6px;
		border-radius: 9999px;
	}
	:global(.dark) input[type='range'] {
		background: #334155;
	}
</style>
