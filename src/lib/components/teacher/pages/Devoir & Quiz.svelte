<script lang="ts">
	import { onMount, getContext, tick } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { derived } from 'svelte/store';
	const i18n: any = getContext('i18n');
	const _ = derived(i18n, ($i18n: any) => (key: string, options?: any) => $i18n.t(key, options));

	// ── UI state ──────────────────────────────────────────────────────────────
	let activeTab: 'create' | 'analytics' = 'create';
	let step: number = 1;

	// ── Data ──────────────────────────────────────────────────────────────────
	let courses: any[] = [];
	let selectedCourse: string = '';
	let models: any[] = [];
	let selectedModel: string = 'gpt-4o-mini';

	// ── Quiz creation form fields ─────────────────────────────────────────────
	let quizTitle: string = '';
	let selectedQuestionTypes: string[] = ['QCM'];
	let totalQuestions: number = 10;
	let limitTime: boolean = true;
	let timeMinutes: number = 20;
	let dueDate: string = '';

	// ── Generated quiz state ──────────────────────────────────────────────────
	let generatedQuizId: string = '';
	let questions: any[] = [];
	let isGenerating: boolean = false;
	let isPublishing: boolean = false;

	// ── Published quiz state ──────────────────────────────────────────────────
	let publishedCode: string = '';
	let copied: boolean = false;

	// ── Analytics state ───────────────────────────────────────────────────────
	let teacherQuizzes: any[] = [];
	let selectedQuizForAnalytics: string = '';
	let analyticsData: any = null;
	let isLoadingAnalytics: boolean = false;

	// ── Manual question addition ──────────────────────────────────────────────
	let manualQuestionType: string = 'QCM';
	let questionsContainer: HTMLDivElement;

	// ── Lifecycle ─────────────────────────────────────────────────────────────
	onMount(async () => {
		const token = localStorage.getItem('token') ?? '';
		dueDate = new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0];
		quizTitle = $i18n.t('Weekly Quiz');
		await fetchCourses(token);
		await fetchModels(token);
		await fetchTeacherQuizzes(token);
	});

	// Fetch analytics whenever the selected quiz changes
	$: if (selectedQuizForAnalytics) fetchAnalytics(selectedQuizForAnalytics);

	// ── Derived counts for header stats ──────────────────────────────────────
	$: totalQuizzesCreated = teacherQuizzes.length;
	$: totalPublished = teacherQuizzes.filter((q) => q.status === 'published').length;
	$: totalDrafts = teacherQuizzes.filter((q) => q.status === 'draft').length;

	// ── API helpers ───────────────────────────────────────────────────────────

	async function fetchCourses(token: string) {
		try {
			const res = await fetch('/api/v1/teacher/courses/', {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				courses = await res.json();
				if (courses.length > 0) selectedCourse = courses[0].id;
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
					const hasMini = models.find((m: any) => m.id === 'gpt-4o-mini');
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
				const published = teacherQuizzes.filter((q) => q.status === 'published');
				if (published.length > 0) selectedQuizForAnalytics = published[0].id;
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
			if (res.ok) analyticsData = await res.json();
		} catch (e) {
			console.error('Error fetching analytics:', e);
		} finally {
			isLoadingAnalytics = false;
		}
	}

	// ── Question type toggle ──────────────────────────────────────────────────
	function toggleQuestionType(type: string) {
		// Keep at least one type selected at all times
		if (selectedQuestionTypes.includes(type)) {
			if (selectedQuestionTypes.length === 1) return;
			selectedQuestionTypes = selectedQuestionTypes.filter((t) => t !== type);
		} else {
			selectedQuestionTypes = [...selectedQuestionTypes, type];
		}
	}

	// ── Quiz generation (Step 1 → Step 2) ────────────────────────────────────
	async function handleGenerate() {
		if (!selectedCourse) {
			alert($i18n.t('Please associate this quiz with a course.'));
			return;
		}
		isGenerating = true;
		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch('/api/v1/quizzes/generate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
				body: JSON.stringify({
					title: quizTitle,
					topic: quizTitle.trim() || 'General Quiz',
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
				throw new Error(err.detail ?? 'Error during generation');
			}
			const data = await res.json();
			generatedQuizId = data.id;
			questions = data.questions;
			step = 2;
		} catch (e: any) {
			alert(e.message ?? $i18n.t('Generation error with LLM'));
		} finally {
			isGenerating = false;
		}
	}

	// ── Quiz publish (Step 2 → Step 3) ───────────────────────────────────────
	async function handlePublish() {
		isPublishing = true;
		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`/api/v1/quizzes/publish/${generatedQuizId}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
				body: JSON.stringify({ questions })
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? 'Error during publication');
			}
			const data = await res.json();
			publishedCode = data.quiz_code;
			step = 3;
			fetchTeacherQuizzes(token);
		} catch (e: any) {
			alert(e.message ?? $i18n.t('Error during publication'));
		} finally {
			isPublishing = false;
		}
	}

	// ── Manual question addition ──────────────────────────────────────────────
	function addManualQuestion() {
		const isQCM = manualQuestionType === 'QCM';
		const newQuestion = {
			id: 'manual_' + Math.random().toString(36).substr(2, 9),
			question_type: manualQuestionType,
			question_text: $i18n.t('New question'),
			options: isQCM ? [$i18n.t('Option A'), $i18n.t('Option B')] : [],
			correct_answer: isQCM ? $i18n.t('Option A') : ''
		};
		questions = [...questions, newQuestion];

		// Auto-scroll to the newly added question
		tick().then(() => {
			if (questionsContainer) {
				const lastQuestion = questionsContainer.lastElementChild;
				if (lastQuestion) {
					lastQuestion.scrollIntoView({ behavior: 'smooth', block: 'center' });
				}
			}
		});
	}

	// ── Question / option management ──────────────────────────────────────────
	function deleteQuestion(index: number) {
		questions = questions.filter((_, i) => i !== index);
	}

	function addOption(questionIndex: number) {
		questions[questionIndex].options = [...questions[questionIndex].options, $i18n.t('New choice')];
		questions = questions; // trigger reactivity
	}

	function removeOption(questionIndex: number, optionIndex: number) {
		// MCQ must keep at least 2 options
		if (questions[questionIndex].options.length <= 2) {
			alert($i18n.t('A multiple choice question must have at least 2 options'));
			return;
		}
		// If the removed option was the correct answer, fall back to the first option
		if (questions[questionIndex].correct_answer === questions[questionIndex].options[optionIndex]) {
			questions[questionIndex].correct_answer = questions[questionIndex].options[0];
		}
		questions[questionIndex].options = questions[questionIndex].options.filter(
			(_: any, i: number) => i !== optionIndex
		);
		questions = questions; // trigger reactivity
	}

	// ── Clipboard helper ──────────────────────────────────────────────────────
	async function copyCodeToClipboard() {
		await navigator.clipboard.writeText(publishedCode);
		copied = true;
		setTimeout(() => (copied = false), 2500);
	}

	// ── Reset to Step 1 ───────────────────────────────────────────────────────
	function resetQuizCreator() {
		step = 1;
		quizTitle = $i18n.t('Weekly Quiz');
		questions = [];
		publishedCode = '';
	}
</script>

<div class="page">
	<!-- ── PAGE HEADER ── -->
	<div class="page-header" in:fade={{ duration: 250 }}>
		<div>
			<h1 class="page-title">{$i18n.t('Quizzes & Assessments')}</h1>
			<p class="page-sub">
				{$i18n.t('Create personalized quizzes with AI and track performance')}
			</p>
		</div>

		<!-- Summary stats (total / published / drafts) -->
		<div class="stats-row">
			<div class="stat-chip">
				<span class="val val-blue">{totalQuizzesCreated}</span>
				<span>{$i18n.t('Total')}</span>
			</div>
			<div class="stat-chip">
				<span class="val val-green">{totalPublished}</span>
				<span>{$i18n.t('Published')}</span>
			</div>
			<div class="stat-chip">
				<span class="val val-amber">{totalDrafts}</span>
				<span>{$i18n.t('Drafts')}</span>
			</div>
		</div>
	</div>

	<!-- ── TAB BAR ── -->
	<div class="tabs" in:fade={{ duration: 250, delay: 60 }}>
		<button class="tab" class:on={activeTab === 'create'} on:click={() => (activeTab = 'create')}>
			<svg
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				width="14"
				height="14"
				aria-hidden="true"
			>
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			{$i18n.t('Create a quiz')}
		</button>
		<button
			class="tab"
			class:on={activeTab === 'analytics'}
			on:click={() => (activeTab = 'analytics')}
		>
			<svg
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				width="14"
				height="14"
				aria-hidden="true"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
				/>
			</svg>
			{$i18n.t('Analytics & stats')}
		</button>
	</div>

	<!-- ══ CREATE TAB ══ -->
	{#if activeTab === 'create'}
		<!-- Wizard step indicator (1 → 2 → 3) -->
		<div class="steps" in:fade={{ duration: 200 }}>
			<div class="step-item" class:active={step === 1} class:done={step > 1}>
				<div class="step-dot">
					{#if step > 1}
						<svg
							viewBox="0 0 12 12"
							fill="none"
							stroke="currentColor"
							width="10"
							height="10"
							aria-hidden="true"
						>
							<path d="M10 2.5L4.5 8.5 2 6" stroke-width="1.8" stroke-linecap="round" />
						</svg>
					{:else}1{/if}
				</div>
				<span>{$i18n.t('Configuration')}</span>
			</div>
			<div class="step-line" class:done={step > 1}></div>
			<div class="step-item" class:active={step === 2} class:done={step > 2}>
				<div class="step-dot">
					{#if step > 2}
						<svg
							viewBox="0 0 12 12"
							fill="none"
							stroke="currentColor"
							width="10"
							height="10"
							aria-hidden="true"
						>
							<path d="M10 2.5L4.5 8.5 2 6" stroke-width="1.8" stroke-linecap="round" />
						</svg>
					{:else}2{/if}
				</div>
				<span>{$i18n.t('Review')}</span>
			</div>
			<div class="step-line" class:done={step > 2}></div>
			<div class="step-item" class:active={step === 3}>
				<div class="step-dot">3</div>
				<span>{$i18n.t('Published')}</span>
			</div>
		</div>

		<!-- ── STEP 1 : Configuration ── -->
		{#if step === 1}
			<!-- Single column: "General info" on top, "Configuration" below -->
			<div class="single-col" in:fade={{ duration: 200 }}>
				<!-- General info card (title + associated course) -->
				<div class="card">
					<div class="card-head">
						<h3>{$i18n.t('General Information')}</h3>
						<p>{$i18n.t('Define the basics of your assessment')}</p>
					</div>
					<div class="card-body">
						<div class="field">
							<label class="label" for="quiz-title">
								{$i18n.t('Assessment title')}
								<span class="req">*</span>
							</label>
							<input
								id="quiz-title"
								type="text"
								class="inp"
								bind:value={quizTitle}
								placeholder={$i18n.t('e.g., JavaScript Variables Quiz')}
							/>
							<span class="hint"
								>{$i18n.t('A clear title helps your students identify the quiz')}</span
							>
						</div>
						<div class="field">
							<label class="label" for="course-sel">
								{$i18n.t('Associated course')}
								<span class="req">*</span>
							</label>
							<select id="course-sel" class="inp" bind:value={selectedCourse}>
								{#if courses.length === 0}
									<option value="">{$i18n.t('No courses available')}</option>
								{:else}
									{#each courses as course}
										<option value={course.id}>{course.title}</option>
									{/each}
								{/if}
							</select>
							<span class="hint"
								>{$i18n.t('The AI will use the course content to generate questions')}</span
							>
						</div>
					</div>
				</div>

				<!-- Generation settings card (question types, count, time, date, model) -->
				<div class="card">
					<div class="card-head">
						<h3>{$i18n.t('Configuration')}</h3>
						<p>{$i18n.t('Generation parameters')}</p>
					</div>
					<div class="card-body">
						<!-- Question type multi-select -->
						<div class="field">
							<label class="label">{$i18n.t('Question types')}</label>
							<div class="type-list">
								{#each [{ id: 'QCM', label: $i18n.t('Multiple Choice') }, { id: 'True/False', label: $i18n.t('True / False') }, { id: 'Short Answer', label: $i18n.t('Short Answer') }] as type}
									<button
										type="button"
										class="type-opt"
										class:on={selectedQuestionTypes.includes(type.id)}
										on:click={() => toggleQuestionType(type.id)}
									>
										<span class="type-check" aria-hidden="true">
											{#if selectedQuestionTypes.includes(type.id)}
												<svg
													viewBox="0 0 12 12"
													fill="none"
													stroke="currentColor"
													width="10"
													height="10"
												>
													<path d="M10 2.5L4.5 8.5 2 6" stroke-width="1.8" stroke-linecap="round" />
												</svg>
											{/if}
										</span>
										{type.label}
									</button>
								{/each}
							</div>
						</div>

						<!-- Question count slider (5–20) -->
						<div class="field">
							<div class="field-row">
								<label class="label">{$i18n.t('Number of questions')}</label>
								<span class="badge-num">{totalQuestions}</span>
							</div>
							<input type="range" min="5" max="20" bind:value={totalQuestions} class="slider" />
							<div class="range-labels"><span>5</span><span>20</span></div>
						</div>

						<!-- Time limit toggle + custom number spinner -->
						<div class="field">
							<div class="field-row">
								<label class="label">{$i18n.t('Time limit')}</label>
								<label class="toggle" aria-label={$i18n.t('Enable time limit')}>
									<input type="checkbox" bind:checked={limitTime} />
									<span class="tog-track"></span>
								</label>
							</div>

							{#if limitTime}
								<div class="time-row" in:fly={{ y: -4, duration: 150 }}>
									<div class="custom-number-wrapper">
										<input
											type="number"
											class="time-num"
											bind:value={timeMinutes}
											min="1"
											max="180"
										/>
										<!-- Custom up/down buttons replacing native browser spinners -->
										<div class="spinner-buttons">
											<button
												type="button"
												class="spinner-btn up"
												on:click={() => {
													if (timeMinutes < 180) timeMinutes++;
												}}
												tabindex="-1"
											>
												<svg viewBox="0 0 24 24" fill="currentColor" width="12" height="12">
													<path d="M7 14l5-5 5 5H7z" />
												</svg>
											</button>
											<button
												type="button"
												class="spinner-btn down"
												on:click={() => {
													if (timeMinutes > 1) timeMinutes--;
												}}
												tabindex="-1"
											>
												<svg viewBox="0 0 24 24" fill="currentColor" width="12" height="12">
													<path d="M7 10l5 5 5-5H7z" />
												</svg>
											</button>
										</div>
									</div>
									<span class="time-unit">{$i18n.t('minutes')}</span>
								</div>
							{/if}
						</div>

						<!-- Due date picker -->
						<div class="field">
							<label class="label" for="due-date">{$i18n.t('Due date')}</label>
							<input id="due-date" type="date" class="inp" bind:value={dueDate} />
						</div>

						<!-- AI model selector -->
						<div class="field">
							<label class="label" for="model-sel">{$i18n.t('AI Model')}</label>
							<select id="model-sel" class="inp" bind:value={selectedModel}>
								{#each models as model}
									<option value={model.id}>{model.name}</option>
								{/each}
							</select>
						</div>

						<!-- Generate / compile button -->
						<button class="btn-primary" on:click={handleGenerate} disabled={isGenerating}>
							{#if isGenerating}
								<svg
									class="spin"
									viewBox="0 0 24 24"
									fill="none"
									width="14"
									height="14"
									aria-hidden="true"
								>
									<circle
										cx="12"
										cy="12"
										r="9"
										stroke="currentColor"
										stroke-width="2.5"
										stroke-dasharray="30 20"
									/>
								</svg>
								{$i18n.t('Generating...')}
							{:else}
								<svg
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									width="14"
									height="14"
									aria-hidden="true"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2.5"
										d="M13 10V3L4 14h7v7l9-11h-7z"
									/>
								</svg>
								{$i18n.t('Generate')}
							{/if}
						</button>
					</div>
				</div>
			</div>
		{/if}

		<!-- ── STEP 2 : Review & edit questions ── -->
		{#if step === 2}
			<div in:fade={{ duration: 200 }}>
				<!-- Top bar: quiz title, add-question controls, publish button -->
				<div class="review-bar">
					<div>
						<span class="badge-draft">{$i18n.t('Draft')}</span>
						<h2 class="review-title">{quizTitle}</h2>
						<p class="review-meta">
							{questions.length}
							{$i18n.t('questions')} · {$i18n.t('Review before publishing')}
						</p>
					</div>
					<div class="review-actions">
						<select class="inp inp-sm" bind:value={manualQuestionType}>
							<option value="QCM">{$i18n.t('Multiple Choice')}</option>
							<option value="Short Answer">{$i18n.t('Short Answer')}</option>
							<option value="True/False">{$i18n.t('True/False')}</option>
						</select>
						<button class="btn-secondary" on:click={addManualQuestion}>
							<svg
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								width="13"
								height="13"
								aria-hidden="true"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2.5"
									d="M12 4v16m8-8H4"
								/>
							</svg>
							{$i18n.t('Add')}
						</button>
						<button
							class="btn-green"
							on:click={handlePublish}
							disabled={isPublishing || questions.length === 0}
						>
							{#if isPublishing}
								<svg
									class="spin"
									viewBox="0 0 24 24"
									fill="none"
									width="13"
									height="13"
									aria-hidden="true"
								>
									<circle
										cx="12"
										cy="12"
										r="9"
										stroke="currentColor"
										stroke-width="2.5"
										stroke-dasharray="30 20"
									/>
								</svg>
								{$i18n.t('Publishing...')}
							{:else}
								<svg
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									width="13"
									height="13"
									aria-hidden="true"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M5 13l4 4L19 7"
									/>
								</svg>
								{$i18n.t('Publish quiz')}
							{/if}
						</button>
					</div>
				</div>

				<!-- Scrollable list of editable question cards -->
				<div class="questions-list" bind:this={questionsContainer}>
					{#each questions as question, index (question.id || index)}
						<div class="q-card" in:fly={{ y: 6, duration: 180, delay: index * 25 }}>
							<!-- Question header: number, type badge, delete button -->
							<div class="q-head">
								<div class="q-meta">
									<span class="q-num">#{index + 1}</span>
									<span class="q-type">{question.question_type}</span>
								</div>
								<button
									class="btn-del"
									on:click={() => deleteQuestion(index)}
									aria-label={$i18n.t('Delete question')}
								>
									<svg
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										width="13"
										height="13"
										aria-hidden="true"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
										/>
									</svg>
								</button>
							</div>

							<!-- Question body: text + answer section -->
							<div class="q-body">
								<div class="field">
									<label class="label-sm">{$i18n.t('Question text')}</label>
									<textarea class="inp" bind:value={question.question_text} rows="2"></textarea>
								</div>

								{#if question.question_type === 'QCM'}
									<!-- MCQ: clickable option markers + inline text inputs -->
									<div class="field">
										<label class="label-sm"
											>{$i18n.t('Options')} · {$i18n.t('Click to mark the correct answer')}</label
										>
										<div class="opt-list">
											{#each question.options as option, oi}
												<div class="opt-row">
													<!-- Click to set as correct answer -->
													<button
														type="button"
														class="opt-mark"
														class:correct={question.correct_answer === option}
														on:click={() => (question.correct_answer = option)}
														aria-label="{$i18n.t('Mark as correct')} {String.fromCharCode(65 + oi)}"
													>
														{#if question.correct_answer === option}
															<svg
																viewBox="0 0 12 12"
																fill="none"
																stroke="currentColor"
																width="10"
																height="10"
																aria-hidden="true"
															>
																<path
																	d="M10 2.5L4.5 8.5 2 6"
																	stroke-width="1.8"
																	stroke-linecap="round"
																/>
															</svg>
														{:else}
															{String.fromCharCode(65 + oi)}
														{/if}
													</button>
													<input
														type="text"
														class="inp inp-sm"
														bind:value={question.options[oi]}
														placeholder="{$i18n.t('Option')} {String.fromCharCode(65 + oi)}"
													/>
													<!-- Remove this option -->
													<button
														type="button"
														class="btn-remove-option"
														on:click={() => removeOption(index, oi)}
														aria-label={$i18n.t('Remove this choice')}
														title={$i18n.t('Remove this choice')}
													>
														<svg
															viewBox="0 0 24 24"
															fill="none"
															stroke="currentColor"
															width="14"
															height="14"
															aria-hidden="true"
														>
															<path
																stroke-linecap="round"
																stroke-linejoin="round"
																stroke-width="2"
																d="M6 18L18 6M6 6l12 12"
															/>
														</svg>
													</button>
												</div>
											{/each}
											<!-- Add a new option -->
											<button
												type="button"
												class="btn-add-option"
												on:click={() => addOption(index)}
											>
												<svg
													viewBox="0 0 24 24"
													fill="none"
													stroke="currentColor"
													width="13"
													height="13"
													aria-hidden="true"
												>
													<path
														stroke-linecap="round"
														stroke-linejoin="round"
														stroke-width="2.5"
														d="M12 4v16m8-8H4"
													/>
												</svg>
												{$i18n.t('Add a choice')}
											</button>
										</div>
									</div>
								{:else}
									<!-- Short Answer / True-False: single correct answer field -->
									<div class="field">
										<label class="label-sm">{$i18n.t('Correct answer')}</label>
										<input
											type="text"
											class="inp inp-sm correct-inp"
											bind:value={question.correct_answer}
											placeholder={$i18n.t('Enter expected answer')}
										/>
									</div>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- ── STEP 3 : Published success screen ── -->
		{#if step === 3}
			<div class="success-wrap" in:fly={{ y: 12, duration: 280 }}>
				<div class="card success-card">
					<!-- Success checkmark icon -->
					<div class="success-icon" aria-hidden="true">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="26" height="26">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2.5"
								d="M5 13l4 4L19 7"
							/>
						</svg>
					</div>
					<h2>{$i18n.t('Quiz published successfully!')}</h2>
					<p>{$i18n.t('Share this code with your students so they can access the quiz')}</p>

					<!-- Shareable quiz code display -->
					<div class="code-box">
						<span class="code-lbl">{$i18n.t('Sharing code')}</span>
						<span class="code-val">{publishedCode}</span>
						<button class="btn-copy" class:copied on:click={copyCodeToClipboard}>
							{#if copied}
								<svg
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									width="12"
									height="12"
									aria-hidden="true"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2.5"
										d="M5 13l4 4L19 7"
									/>
								</svg>
								{$i18n.t('Copied!')}
							{:else}
								<svg
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									width="12"
									height="12"
									aria-hidden="true"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
									/>
								</svg>
								{$i18n.t('Copy code')}
							{/if}
						</button>
					</div>

					<!-- Post-publish actions -->
					<div class="success-btns">
						<button class="btn-secondary" on:click={resetQuizCreator}>
							{$i18n.t('New quiz')}
						</button>
						<button
							class="btn-primary"
							on:click={() => {
								activeTab = 'analytics';
								selectedQuizForAnalytics = generatedQuizId;
								step = 1;
							}}
						>
							{$i18n.t('View statistics')}
							<svg
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								width="13"
								height="13"
								aria-hidden="true"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M13 7l5 5m0 0l-5 5m5-5H6"
								/>
							</svg>
						</button>
					</div>
				</div>
			</div>
		{/if}

		<!-- ══ ANALYTICS TAB ══ -->
	{:else}
		<div class="analytics-wrap" in:fade={{ duration: 200 }}>
			<!-- Quiz selector card -->
			<div class="card">
				<div class="card-body analytics-sel-row">
					<div>
						<h3 class="sel-title">{$i18n.t('Select a quiz')}</h3>
						<p class="sel-sub">{$i18n.t('View statistics for published assessments')}</p>
					</div>
					<select class="inp sel-inp" bind:value={selectedQuizForAnalytics}>
						{#if teacherQuizzes.filter((q) => q.status === 'published').length === 0}
							<option value="">{$i18n.t('No published quizzes')}</option>
						{:else}
							{#each teacherQuizzes.filter((q) => q.status === 'published') as quiz}
								<option value={quiz.id}>{quiz.title} · {quiz.quiz_code}</option>
							{/each}
						{/if}
					</select>
				</div>
			</div>

			{#if isLoadingAnalytics}
				<!-- Loading spinner while fetching analytics -->
				<div class="loading-state">
					<svg
						class="spin"
						viewBox="0 0 24 24"
						fill="none"
						width="22"
						height="22"
						style="color:#2563eb"
						aria-hidden="true"
					>
						<circle
							cx="12"
							cy="12"
							r="9"
							stroke="currentColor"
							stroke-width="2.5"
							stroke-dasharray="30 20"
						/>
					</svg>
					<p>{$i18n.t('Loading statistics…')}</p>
				</div>
			{:else if analyticsData}
				<!-- KPI metric cards: participants, avg, high, low scores -->
				<div class="metrics">
					<div class="metric m-blue">
						<div class="metric-val">{analyticsData.total_participants}</div>
						<div class="metric-lbl">{$i18n.t('Participants')}</div>
					</div>
					<div class="metric m-green">
						<div class="metric-val">{analyticsData.average_score}</div>
						<div class="metric-lbl">{$i18n.t('Average')}</div>
					</div>
					<div class="metric m-purple">
						<div class="metric-val">{analyticsData.high_score}</div>
						<div class="metric-lbl">{$i18n.t('Max score')}</div>
					</div>
					<div class="metric m-red">
						<div class="metric-val">{analyticsData.low_score}</div>
						<div class="metric-lbl">{$i18n.t('Min score')}</div>
					</div>
				</div>

				<!-- Student submissions list -->
				<div class="card">
					<div class="card-head">
						<h3>{$i18n.t('Student submissions')}</h3>
						<p>{$i18n.t('Detailed scores per student')}</p>
					</div>
					<div class="card-body">
						{#if !analyticsData.submissions?.length}
							<div class="empty-content">
								<p>{$i18n.t('No submissions received yet')}</p>
							</div>
						{:else}
							<div class="sub-list">
								{#each analyticsData.submissions as sub}
									<div class="sub-row {sub.submission_count > 1 ? 'sub-row--retried' : ''}">
										<div class="avatar">{sub.student_name?.charAt(0)?.toUpperCase() ?? '?'}</div>
										<div class="sub-info">
											<div class="sub-name">{sub.student_name}</div>
											{#if sub.attempts && sub.attempts.length > 1}
												<div class="sub-attempts">
													{#each sub.attempts as att}
														<span class="sub-attempt-chip {att.score === sub.best_score ? 'best' : ''}">
															T{att.attempt}: {att.score}/{sub.attempts[0]?.total ?? att.score}
															{#if att.score === sub.best_score}<span class="chip-star">★</span>{/if}
														</span>
													{/each}
												</div>
											{:else}
												<div class="sub-date">
													{sub.attempts?.[0]?.submitted_at
														? new Date(sub.attempts[0].submitted_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
														: new Date(sub.submitted_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })}
												</div>
											{/if}
										</div>
										<div class="sub-score-wrap">
											<div class="sub-score">{sub.best_score ?? sub.score}</div>
											{#if sub.submission_count > 1}
												<div class="sub-best-label">{$i18n.t('Best')}</div>
											{/if}
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			{:else}
				<!-- Empty state: no quiz selected or no data yet -->
				<div class="card empty-card">
					<svg
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						width="28"
						height="28"
						style="color:#94a3b8;margin:0 auto 1rem;display:block"
						aria-hidden="true"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="1.5"
							d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
						/>
					</svg>
					<p class="empty-title">{$i18n.t('No data to display')}</p>
					<p class="empty-sub">
						{$i18n.t('Select a published quiz to view its detailed statistics')}
					</p>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	/* ============================================================
	   1. RESET & BASE
	   ============================================================ */
	*,
	*::before,
	*::after {
		box-sizing: border-box;
	}

	.page {
		padding: 1.75rem 1.5rem;
		max-width: 1400px;
		margin: 0 auto;
		font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
		font-size: 15px;
		color: #1e293b;
	}
	:global(.dark) .page {
		color: #e2e8f0;
	}

	/* ============================================================
	   2. PAGE HEADER
	   ============================================================ */
	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 1.5rem;
		margin-bottom: 2.25rem;
		padding-bottom: 1.5rem;
		border-bottom: 1px solid rgba(226, 232, 240, 0.6);
	}
	:global(.dark) .page-header {
		border-color: rgba(51, 65, 85, 0.6);
	}

	.page-title {
		font-size: 26px;
		font-weight: 700;
		color: #0f172a;
		margin: 0 0 6px;
		letter-spacing: -0.025em;
		line-height: 1.1;
	}
	:global(.dark) .page-title {
		color: #f8fafc;
	}

	.page-sub {
		font-size: 13.5px;
		color: #64748b;
		margin: 0;
		line-height: 1.5;
		max-width: 520px;
	}
	:global(.dark) .page-sub {
		color: #94a3b8;
	}

	/* ── Header stat chips ── */
	.stats-row {
		display: flex;
		gap: 16px;
		flex-wrap: wrap;
		align-items: stretch;
	}

	.stat-chip {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 1px;
		flex: 1;
		min-width: 110px;
		padding: 12px 18px;
		background: #fff;
		border: 1px solid #e2e8f0;
		border-radius: 12px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
		transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
	}
	.stat-chip:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px -6px rgba(0, 0, 0, 0.04);
	}
	:global(.dark) .stat-chip {
		background: #1e293b;
		border-color: #334155;
		box-shadow: none;
	}

	.stat-chip .val {
		font-size: 22px;
		font-weight: 700;
		line-height: 1;
		letter-spacing: -0.015em;
	}
	.stat-chip span:not(.val) {
		font-size: 11px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: #7f8fa4;
	}
	:global(.dark) .stat-chip span:not(.val) {
		color: #a1b0c0;
	}

	/* Colored chip variants */
	.val-blue {
		color: #2563eb;
	}
	.stat-chip:has(.val-blue) {
		background: #f1f6ff;
		border-color: #e0e9fe;
	}
	:global(.dark) .stat-chip:has(.val-blue) {
		background: rgba(37, 99, 235, 0.1);
		border-color: rgba(37, 99, 235, 0.3);
	}

	.val-green {
		color: #10a34a;
	}
	.stat-chip:has(.val-green) {
		background: #f1fdf4;
		border-color: #dcfce7;
	}
	:global(.dark) .stat-chip:has(.val-green) {
		background: rgba(16, 163, 74, 0.1);
		border-color: rgba(16, 163, 74, 0.3);
	}

	.val-amber {
		color: #d97706;
	}
	.stat-chip:has(.val-amber) {
		background: #fffbef;
		border-color: #fef3c7;
	}
	:global(.dark) .stat-chip:has(.val-amber) {
		background: rgba(217, 119, 6, 0.1);
		border-color: rgba(217, 119, 6, 0.3);
	}

	/* ============================================================
	   3. TAB BAR
	   ============================================================ */
	.tabs {
		display: flex;
		border-bottom: 1px solid #e2e8f0;
		margin-bottom: 1.5rem;
	}
	:global(.dark) .tabs {
		border-color: #334155;
	}

	.tab {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 8px 14px;
		background: none;
		border: none;
		border-bottom: 2px solid transparent;
		margin-bottom: -1px;
		font-size: 13px;
		font-weight: 500;
		color: #64748b;
		cursor: pointer;
		transition: color 0.15s;
		font-family: inherit;
	}
	.tab:hover {
		color: #1e293b;
	}
	:global(.dark) .tab:hover {
		color: #e2e8f0;
	}
	.tab.on {
		color: #2563eb;
		border-bottom-color: #2563eb;
	}
	:global(.dark) .tab.on {
		color: #93c5fd;
		border-bottom-color: #93c5fd;
	}

	/* ============================================================
	   4. WIZARD STEP INDICATOR
	   ============================================================ */
	.steps {
		display: flex;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.step-item {
		display: flex;
		align-items: center;
		gap: 7px;
		font-size: 12px;
		color: #94a3b8;
	}

	.step-dot {
		width: 22px;
		height: 22px;
		border-radius: 50%;
		border: 1.5px solid #e2e8f0;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 11px;
		font-weight: 600;
		background: white;
		flex-shrink: 0;
		transition: all 0.2s;
	}
	:global(.dark) .step-dot {
		background: #1e293b;
		border-color: #475569;
	}

	.step-item.active {
		color: #1e293b;
	}
	:global(.dark) .step-item.active {
		color: #f1f5f9;
	}
	.step-item.active .step-dot {
		border-color: #2563eb;
		color: #2563eb;
	}
	.step-item.done .step-dot {
		background: #2563eb;
		border-color: #2563eb;
		color: white;
	}

	.step-line {
		flex: 1;
		height: 1px;
		background: #e2e8f0;
		margin: 0 8px;
		min-width: 16px;
		transition: background 0.2s;
	}
	:global(.dark) .step-line {
		background: #334155;
	}
	.step-line.done {
		background: #2563eb;
	}

	/* ============================================================
	   5. STEP 1 LAYOUT — single column (top: info, bottom: config)
	   ============================================================ */
	.single-col {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
		max-width: 100%;
	}

	/* ============================================================
	   6. CARDS
	   ============================================================ */
	.card {
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 12px;
	}
	:global(.dark) .card {
		background: #1e293b;
		border-color: #334155;
	}

	.card-head {
		padding: 1.25rem 1.5rem 1rem;
		border-bottom: 1px solid #f1f5f9;
	}
	:global(.dark) .card-head {
		border-color: #334155;
	}
	.card-head h3 {
		font-size: 13px;
		font-weight: 600;
		color: #0f172a;
		margin: 0 0 2px;
	}
	:global(.dark) .card-head h3 {
		color: #f1f5f9;
	}
	.card-head p {
		font-size: 12px;
		color: #94a3b8;
		margin: 0;
	}

	.card-body {
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	/* ============================================================
	   7. FORM ELEMENTS
	   ============================================================ */
	.field {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.field-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.label {
		font-size: 12px;
		font-weight: 600;
		color: #475569;
	}
	:global(.dark) .label {
		color: #94a3b8;
	}
	.label-sm {
		font-size: 11px;
		font-weight: 600;
		color: #94a3b8;
	}
	.req {
		color: #ef4444;
	}
	.hint {
		font-size: 11px;
		color: #94a3b8;
	}

	/* Standard text / select / textarea inputs */
	.inp {
		width: 100%;
		padding: 7px 10px;
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 7px;
		font-size: 13px;
		color: #0f172a;
		outline: none;
		transition:
			border-color 0.15s,
			box-shadow 0.15s;
		font-family: inherit;
	}
	.inp:hover {
		border-color: #cbd5e1;
	}
	.inp:focus {
		border-color: #2563eb;
		box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
	}
	:global(.dark) .inp {
		background: #0f172a;
		border-color: #334155;
		color: #e2e8f0;
	}
	:global(.dark) .inp:focus {
		border-color: #93c5fd;
		box-shadow: 0 0 0 3px rgba(147, 197, 253, 0.1);
	}

	/* Select: hide native arrow, inject custom chevron */
	select.inp {
		appearance: none;
		cursor: pointer;
		padding-right: 28px;
		background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2'%3E%3Cpath d='M19 9l-7 7-7-7'/%3E%3C/svg%3E");
		background-repeat: no-repeat;
		background-position: right 10px center;
	}
	textarea.inp {
		resize: vertical;
		min-height: 56px;
	}
	.inp-sm {
		padding: 5px 8px;
		font-size: 12px;
	}
	.correct-inp {
		color: #059669;
		border-color: rgba(5, 150, 105, 0.25);
	}

	/* ============================================================
	   8. QUESTION TYPE TOGGLE BUTTONS
	   ============================================================ */
	.type-list {
		display: flex;
		flex-direction: column;
		gap: 5px;
	}

	.type-opt {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 8px 10px;
		border: 1px solid #e2e8f0;
		border-radius: 7px;
		cursor: pointer;
		transition: all 0.15s;
		font-size: 13px;
		font-weight: 500;
		color: #475569;
		background: white;
		text-align: left;
		font-family: inherit;
	}
	.type-opt:hover {
		border-color: #bfdbfe;
		background: #eff6ff;
	}
	:global(.dark) .type-opt {
		background: #0f172a;
		border-color: #334155;
		color: #94a3b8;
	}
	:global(.dark) .type-opt:hover {
		background: #1e293b;
	}
	.type-opt.on {
		border-color: #2563eb;
		background: #eff6ff;
		color: #1d4ed8;
	}
	:global(.dark) .type-opt.on {
		background: rgba(37, 99, 235, 0.1);
		color: #bfdbfe;
	}

	.type-check {
		width: 16px;
		height: 16px;
		border-radius: 4px;
		border: 1.5px solid #e2e8f0;
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.15s;
	}
	.type-opt.on .type-check {
		background: #2563eb;
		border-color: #2563eb;
		color: white;
	}

	/* ── Question count badge ── */
	.badge-num {
		font-size: 12px;
		font-weight: 600;
		color: #2563eb;
		background: #eff6ff;
		padding: 2px 8px;
		border-radius: 20px;
	}
	:global(.dark) .badge-num {
		background: rgba(37, 99, 235, 0.15);
		color: #bfdbfe;
	}

	/* ── Slider ── */
	.slider {
		width: 100%;
		height: 4px;
		appearance: none;
		background: #e2e8f0;
		border-radius: 4px;
		outline: none;
		cursor: pointer;
	}
	:global(.dark) .slider {
		background: #334155;
	}
	.slider::-webkit-slider-thumb {
		appearance: none;
		width: 18px;
		height: 18px;
		background: #2563eb;
		border-radius: 50%;
		border: 2px solid white;
		box-shadow: 0 0 0 1.5px #2563eb;
		cursor: pointer;
	}
	.range-labels {
		display: flex;
		justify-content: space-between;
		font-size: 11px;
		color: #94a3b8;
		margin-top: 2px;
	}

	/* ── Toggle switch ── */
	.toggle {
		position: relative;
		display: inline-block;
		width: 36px;
		height: 20px;
		cursor: pointer;
	}
	.toggle input {
		opacity: 0;
		width: 0;
		height: 0;
		position: absolute;
	}
	.tog-track {
		position: absolute;
		inset: 0;
		background: #cbd5e1;
		border-radius: 10px;
		transition: background 0.2s;
	}
	.tog-track::after {
		content: '';
		position: absolute;
		width: 16px;
		height: 16px;
		left: 2px;
		top: 2px;
		background: white;
		border-radius: 50%;
		transition: transform 0.2s;
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
	}
	.toggle input:checked ~ .tog-track {
		background: #2563eb;
	}
	.toggle input:checked ~ .tog-track::after {
		transform: translateX(16px);
	}

	/* ============================================================
	   9. CUSTOM NUMBER SPINNER (time limit input)
	   ============================================================ */
	/* Hide native browser spin buttons */
	.time-num::-webkit-outer-spin-button,
	.time-num::-webkit-inner-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}
	.time-num {
		-moz-appearance: textfield;
	}

	.custom-number-wrapper {
		position: relative;
		display: inline-flex;
		align-items: center;
	}

	.time-num {
		width: 70px;
		height: 40px;
		padding: 0 24px 0 12px;
		font-size: 18px;
		font-weight: 700;
		color: #2563eb;
		background-color: #fff;
		border: 1px solid #e2e8f0;
		border-radius: 8px;
		outline: none;
		text-align: left;
		transition: all 0.2s;
		font-family: inherit;
	}
	.time-num:focus {
		border-color: #3b82f6;
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}
	:global(.dark) .time-num {
		background: #1e293b;
		border-color: #475569;
		color: #93c5fd;
	}

	.spinner-buttons {
		position: absolute;
		right: 6px;
		display: flex;
		flex-direction: column;
		height: 32px;
		justify-content: space-between;
	}

	.spinner-btn {
		background: none;
		border: none;
		padding: 0;
		margin: 0;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #888;
		height: 14px;
		width: 16px;
		transition:
			color 0.1s,
			transform 0.1s;
	}
	.spinner-btn:hover {
		color: #2563eb;
	}
	.spinner-btn:active {
		transform: scale(0.9);
	}

	.time-row {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-top: 6px;
	}
	.time-unit {
		font-size: 14px;
		color: #64748b;
		font-weight: 500;
	}

	/* ============================================================
	   10. BUTTONS
	   ============================================================ */
	.btn-primary {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		padding: 8px 16px;
		background: #2563eb;
		color: white;
		border: none;
		border-radius: 7px;
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
		transition:
			background 0.15s,
			transform 0.1s;
		font-family: inherit;
		width: 100%;
	}
	.btn-primary:hover:not(:disabled) {
		background: #1d4ed8;
	}
	.btn-primary:active:not(:disabled) {
		transform: scale(0.99);
	}
	.btn-primary:disabled {
		opacity: 0.45;
		cursor: not-allowed;
	}

	.btn-secondary {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 6px 12px;
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 7px;
		font-size: 12px;
		font-weight: 500;
		color: #475569;
		cursor: pointer;
		transition: all 0.15s;
		font-family: inherit;
	}
	.btn-secondary:hover {
		background: #f8fafc;
		border-color: #cbd5e1;
	}
	:global(.dark) .btn-secondary {
		background: #1e293b;
		border-color: #334155;
		color: #94a3b8;
	}
	:global(.dark) .btn-secondary:hover {
		background: #334155;
	}

	.btn-green {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 6px 14px;
		background: #059669;
		color: white;
		border: none;
		border-radius: 7px;
		font-size: 12px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.15s;
		font-family: inherit;
	}
	.btn-green:hover:not(:disabled) {
		background: #047857;
	}
	.btn-green:disabled {
		opacity: 0.45;
		cursor: not-allowed;
	}

	/* Delete (trash) icon button */
	.btn-del {
		width: 28px;
		height: 28px;
		border: none;
		background: none;
		color: #94a3b8;
		cursor: pointer;
		border-radius: 6px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.15s;
	}
	.btn-del:hover {
		background: #fef2f2;
		color: #dc2626;
	}

	/* Remove an MCQ option */
	.btn-remove-option {
		width: 28px;
		height: 28px;
		flex-shrink: 0;
		border: 1px solid #e2e8f0;
		background: white;
		color: #94a3b8;
		cursor: pointer;
		border-radius: 6px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.15s;
	}
	.btn-remove-option:hover {
		background: #fef2f2;
		border-color: #fecaca;
		color: #dc2626;
	}
	:global(.dark) .btn-remove-option {
		background: #1e293b;
		border-color: #334155;
	}
	:global(.dark) .btn-remove-option:hover {
		background: rgba(220, 38, 38, 0.15);
		border-color: rgba(220, 38, 38, 0.3);
		color: #fca5a5;
	}

	/* Add a new MCQ option */
	.btn-add-option {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 6px 12px;
		background: #f0f9ff;
		border: 1px dashed #bfdbfe;
		border-radius: 7px;
		font-size: 12px;
		font-weight: 500;
		color: #2563eb;
		cursor: pointer;
		transition: all 0.15s;
		font-family: inherit;
		margin-top: 4px;
		width: 100%;
		justify-content: center;
	}
	.btn-add-option:hover {
		background: #eff6ff;
		border-style: solid;
		border-color: #2563eb;
	}
	:global(.dark) .btn-add-option {
		background: rgba(37, 99, 235, 0.08);
		border-color: rgba(37, 99, 235, 0.25);
		color: #93c5fd;
	}
	:global(.dark) .btn-add-option:hover {
		background: rgba(37, 99, 235, 0.15);
		border-color: rgba(147, 197, 253, 0.5);
	}

	/* Copy-to-clipboard button */
	.btn-copy {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 5px 14px;
		border: 1px solid #e2e8f0;
		border-radius: 20px;
		background: white;
		font-size: 12px;
		color: #2563eb;
		cursor: pointer;
		transition: all 0.15s;
		font-family: inherit;
	}
	.btn-copy:hover {
		background: #eff6ff;
		border-color: #bfdbfe;
	}
	.btn-copy.copied {
		background: #ecfdf5;
		border-color: #a7f3d0;
		color: #059669;
	}
	:global(.dark) .btn-copy {
		background: #1e293b;
		border-color: #334155;
	}

	/* ============================================================
	   11. REVIEW BAR (Step 2 header)
	   ============================================================ */
	.review-bar {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
		padding: 1rem 1.25rem;
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 10px;
		margin-bottom: 1.25rem;
		flex-wrap: wrap;
	}
	:global(.dark) .review-bar {
		background: #1e293b;
		border-color: #334155;
	}

	.badge-draft {
		display: inline-block;
		padding: 2px 8px;
		background: #eff6ff;
		color: #2563eb;
		border-radius: 4px;
		font-size: 11px;
		font-weight: 600;
		margin-bottom: 4px;
	}
	:global(.dark) .badge-draft {
		background: rgba(37, 99, 235, 0.15);
		color: #bfdbfe;
	}

	.review-title {
		font-size: 16px;
		font-weight: 600;
		color: #0f172a;
		margin: 0 0 2px;
	}
	:global(.dark) .review-title {
		color: #f1f5f9;
	}
	.review-meta {
		font-size: 12px;
		color: #94a3b8;
		margin: 0;
	}

	.review-actions {
		display: flex;
		gap: 10px;
		align-items: center;
		flex-wrap: nowrap;
	}
	.review-actions select {
		width: 110px;
		min-width: 110px;
		flex-shrink: 0;
	}
	.review-actions button {
		white-space: nowrap;
		flex-shrink: 0;
		display: inline-flex;
		align-items: center;
		gap: 4px;
	}

	/* ============================================================
	   12. QUESTION CARDS (Step 2)
	   ============================================================ */
	.questions-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.q-card {
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 10px;
		overflow: hidden;
	}
	:global(.dark) .q-card {
		background: #1e293b;
		border-color: #334155;
	}

	.q-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.625rem 1rem;
		background: #f8fafc;
		border-bottom: 1px solid #f1f5f9;
	}
	:global(.dark) .q-head {
		background: #0f172a;
		border-color: #334155;
	}

	.q-meta {
		display: flex;
		align-items: center;
		gap: 7px;
	}
	.q-num {
		font-size: 12px;
		font-weight: 700;
		color: #2563eb;
	}
	:global(.dark) .q-num {
		color: #93c5fd;
	}

	.q-type {
		font-size: 11px;
		padding: 2px 6px;
		background: #eff6ff;
		color: #1d4ed8;
		border-radius: 4px;
		font-weight: 600;
	}
	:global(.dark) .q-type {
		background: rgba(37, 99, 235, 0.15);
		color: #bfdbfe;
	}

	.q-body {
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.875rem;
	}

	/* MCQ option row */
	.opt-list {
		display: flex;
		flex-direction: column;
		gap: 5px;
	}
	.opt-row {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	/* Correct-answer marker button */
	.opt-mark {
		width: 28px;
		height: 28px;
		flex-shrink: 0;
		border: 1.5px solid #e2e8f0;
		border-radius: 6px;
		font-size: 11px;
		font-weight: 600;
		color: #94a3b8;
		background: white;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.15s;
	}
	:global(.dark) .opt-mark {
		background: #0f172a;
		border-color: #334155;
	}
	.opt-mark:hover {
		border-color: #2563eb;
		color: #2563eb;
	}
	.opt-mark.correct {
		background: #059669;
		border-color: #059669;
		color: white;
	}

	/* ============================================================
	   13. SUCCESS SCREEN (Step 3)
	   ============================================================ */
	.success-wrap {
		max-width: 420px;
		margin: 1.5rem auto;
	}
	.success-card {
		padding: 2.25rem 1.75rem;
		text-align: center;
	}

	.success-icon {
		width: 52px;
		height: 52px;
		border-radius: 50%;
		background: #ecfdf5;
		color: #059669;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto 1.25rem;
	}
	.success-card h2 {
		font-size: 17px;
		font-weight: 600;
		color: #0f172a;
		margin: 0 0 6px;
	}
	:global(.dark) .success-card h2 {
		color: #f1f5f9;
	}
	.success-card > p {
		font-size: 13px;
		color: #64748b;
		margin: 0 0 1.5rem;
		line-height: 1.5;
	}

	.code-box {
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		border-radius: 9px;
		padding: 1.25rem;
		margin-bottom: 1.5rem;
		text-align: center;
	}
	:global(.dark) .code-box {
		background: #0f172a;
		border-color: #334155;
	}

	.code-lbl {
		display: block;
		font-size: 10px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: #94a3b8;
		margin-bottom: 6px;
	}
	.code-val {
		display: block;
		font-family: 'JetBrains Mono', 'Courier New', monospace;
		font-size: 2rem;
		font-weight: 700;
		letter-spacing: 0.3em;
		color: #2563eb;
		margin-bottom: 1rem;
	}
	:global(.dark) .code-val {
		color: #93c5fd;
	}

	.success-btns {
		display: flex;
		gap: 0.625rem;
		padding-top: 1.25rem;
		border-top: 1px solid #f1f5f9;
	}
	:global(.dark) .success-btns {
		border-color: #334155;
	}
	.success-btns .btn-secondary {
		flex: 1;
		justify-content: center;
	}
	.success-btns .btn-primary {
		flex: 1;
		width: auto;
	}

	/* ============================================================
	   14. ANALYTICS TAB
	   ============================================================ */
	.analytics-wrap {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.analytics-sel-row {
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 1rem;
	}
	.sel-title {
		font-size: 13px;
		font-weight: 600;
		color: #0f172a;
		margin: 0 0 2px;
	}
	:global(.dark) .sel-title {
		color: #f1f5f9;
	}
	.sel-sub {
		font-size: 12px;
		color: #94a3b8;
		margin: 0;
	}
	.sel-inp {
		max-width: 300px;
		min-width: 200px;
	}

	/* KPI metric grid */
	.metrics {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
		gap: 0.75rem;
	}

	.metric {
		background: white;
		border: 1px solid #e2e8f0;
		border-left: 3px solid transparent;
		border-radius: 9px;
		padding: 1rem 1.25rem;
	}
	:global(.dark) .metric {
		background: #1e293b;
		border-color: #334155;
	}

	.m-blue {
		border-left-color: #2563eb;
	}
	.m-green {
		border-left-color: #059669;
	}
	.m-purple {
		border-left-color: #7c3aed;
	}
	.m-red {
		border-left-color: #dc2626;
	}

	.metric-val {
		font-size: 22px;
		font-weight: 600;
		line-height: 1;
		margin-bottom: 4px;
	}
	.m-blue .metric-val {
		color: #2563eb;
	}
	.m-green .metric-val {
		color: #059669;
	}
	.m-purple .metric-val {
		color: #7c3aed;
	}
	.m-red .metric-val {
		color: #dc2626;
	}
	.metric-lbl {
		font-size: 11px;
		color: #94a3b8;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	/* Student submission rows */
	.sub-list {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.sub-row {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.625rem 0.875rem;
		background: #f8fafc;
		border-radius: 7px;
		transition: background 0.12s;
	}
	.sub-row:hover {
		background: #f1f5f9;
	}
	:global(.dark) .sub-row {
		background: #0f172a;
	}
	:global(.dark) .sub-row:hover {
		background: #1e293b;
	}

	.avatar {
		width: 32px;
		height: 32px;
		border-radius: 50%;
		background: #eff6ff;
		color: #2563eb;
		font-size: 12px;
		font-weight: 600;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}
	.sub-info {
		flex: 1;
	}
	.sub-name {
		font-size: 13px;
		font-weight: 500;
		color: #0f172a;
	}
	:global(.dark) .sub-name {
		color: #f1f5f9;
	}
	.sub-date {
		font-size: 11px;
		color: #94a3b8;
	}
	.sub-score {
		font-size: 14px;
		font-weight: 600;
		color: #2563eb;
	}
	:global(.dark) .sub-score {
		color: #93c5fd;
	}
	/* Retake support */
	.sub-row--retried {
		border-left: 3px solid #f59e0b;
	}
	.sub-score-wrap {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 2px;
	}
	.sub-best-label {
		font-size: 9px;
		font-weight: 700;
		color: #10b981;
		text-transform: uppercase;
		letter-spacing: .05em;
	}
	.sub-attempts {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		margin-top: 3px;
	}
	.sub-attempt-chip {
		display: inline-flex;
		align-items: center;
		gap: 2px;
		font-size: 10px;
		font-weight: 600;
		padding: 1px 6px;
		border-radius: 999px;
		background: #e2e8f0;
		color: #475569;
	}
	:global(.dark) .sub-attempt-chip { background: #334155; color: #94a3b8; }
	.sub-attempt-chip.best {
		background: #d1fae5;
		color: #065f46;
	}
	:global(.dark) .sub-attempt-chip.best { background: rgba(16,185,129,.18); color: #6ee7b7; }
	.chip-star { font-size: 9px; }

	/* ============================================================
	   15. EMPTY & LOADING STATES
	   ============================================================ */
	.empty-card {
		padding: 2.5rem 2rem;
		text-align: center;
	}
	.empty-title {
		font-size: 14px;
		font-weight: 600;
		color: #0f172a;
		margin: 0 0 4px;
	}
	:global(.dark) .empty-title {
		color: #f1f5f9;
	}
	.empty-sub {
		font-size: 13px;
		color: #64748b;
		margin: 0;
	}
	.empty-content {
		text-align: center;
		padding: 1.5rem;
		color: #94a3b8;
		font-size: 13px;
	}

	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 2.5rem;
		gap: 0.625rem;
		color: #94a3b8;
		font-size: 13px;
	}

	/* ============================================================
	   16. SPINNER ANIMATION
	   ============================================================ */
	.spin {
		animation: sp 0.7s linear infinite;
	}
	@keyframes sp {
		to {
			transform: rotate(360deg);
		}
	}

	/* ============================================================
	   17. RESPONSIVE — mobile breakpoint
	   ============================================================ */
	@media (max-width: 600px) {
		.page {
			padding: 1rem;
		}
		.page-header {
			flex-direction: column;
		}
		.stats-row {
			width: 100%;
		}
		.stat-chip {
			flex: 1;
			justify-content: center;
		}
		.review-bar {
			flex-direction: column;
		}
		.review-actions {
			width: 100%;
		}
		.metrics {
			grid-template-columns: 1fr 1fr;
		}
		.success-wrap {
			margin: 1rem auto;
		}
		.single-col {
			max-width: 100%;
		}
	}
</style>
