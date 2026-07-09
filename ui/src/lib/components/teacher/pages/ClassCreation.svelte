<!-- teacher/pages/ClassCreation.svelte — carbon-copied from the student Create-new-support wizard -->
<script lang="ts">
	import { getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { browser } from '$app/environment';
	import { createClassroom, createInvitation } from '$lib/apis/classrooms';
	import type { Writable } from 'svelte/store';

	// Get i18n from context with proper typing
	interface I18n {
		t: (key: string) => string;
	}
	const i18n = getContext<Writable<I18n>>('i18n');

	// Step Navigation
	const steps = ['Subject', 'Course', 'Objectives', 'Level', 'Details', 'Students', 'Review'];

	let currentStep = 0;
	let isSubmitting = false;

	// Form data
	let supportTitle = '';
	let shortDescription = '';
	let selectedSubject = '';
	let customSubject = '';
	let selectedCourse = '';
	let uploadedFiles: File[] = [];

	// Learning objectives data
	let learningObjective = '';
	let selectedLearningType: string | null = null;

	// Teacher-specific: targeted competencies (chips, like keywords)
	let competencies: string[] = [];
	let competencyInput = '';
	function addCompetency() {
		const c = competencyInput.trim();
		if (c && !competencies.includes(c)) competencies = [...competencies, c];
		competencyInput = '';
	}
	function removeCompetency(c: string) {
		competencies = competencies.filter((x) => x !== c);
	}

	// Teacher-specific: capacity + weekly meeting days (term dates reuse startDate/endDate)
	let capacity: number | null = null;
	const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
	let meetingDays: string[] = [];
	function toggleDay(d: string) {
		meetingDays = meetingDays.includes(d)
			? meetingDays.filter((x) => x !== d)
			: [...meetingDays, d];
	}

	// Teacher-specific: invite students by email at creation (chips)
	let studentEmails: string[] = [];
	let studentEmailInput = '';
	function addStudentEmail() {
		const e = studentEmailInput.trim().toLowerCase();
		const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e);
		if (ok && !studentEmails.includes(e)) studentEmails = [...studentEmails, e];
		studentEmailInput = '';
	}
	function removeStudentEmail(e: string) {
		studentEmails = studentEmails.filter((x) => x !== e);
	}
	const learningTypes = [
		{ id: 'exam', name: 'Prepare students for an exam', icon: '📝' },
		{ id: 'course', name: 'Cover or review a course', icon: '📚' },
		{ id: 'skill', name: 'Build a new skill', icon: '🚀' }
	];

	// Learning level data
	let selectedLevel = '';
	const learningLevels = [
		{
			id: 'primary',
			name: 'Primary school',
			description: 'Foundational learning for young minds',
			color: 'green'
		},
		{
			id: 'middle',
			name: 'Middle school',
			description: 'Building critical thinking',
			color: 'yellow'
		},
		{
			id: 'high',
			name: 'High school',
			description: 'Preparing students for advanced studies',
			color: 'orange'
		},
		{ id: 'university', name: 'University', description: 'Expert-level guidance', color: 'red' }
	];

	// Details data
	let contentLanguage = 'English';
	let estimatedDuration = '30min';
	let accessType = 'Private';
	let keywords: string[] = [];
	let keywordInput = '';
	let startDate = '';
	let endDate = '';

	// Content languages
	const languages = ['English', 'French', 'Arabic', 'Spanish', 'German'];

	// Duration options
	const durations = ['15min', '30min', '45min', '1h', '1h30min', '2h'];

	// Access types
	const accessTypes = ['Private', 'Public', 'Shared'];

	// Add keyword
	function addKeyword() {
		const keyword = keywordInput.trim();
		if (keyword && !keywords.includes(keyword)) {
			keywords = [...keywords, keyword];
			keywordInput = '';
		}
	}

	// Remove keyword
	function removeKeyword(keyword: string) {
		keywords = keywords.filter((k) => k !== keyword);
	}

	// Handle enter key in keyword input
	function handleKeyDown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			event.preventDefault();
			addKeyword();
		}
	}

	// Sample course data
	const courses = [
		{
			id: 'physics101',
			title: 'Introduction to Physics',
			image: '/images/courses/physics.jpg',
			instructor: { name: 'Maria JOHNSON', avatar: '/images/avatars/maria.jpg' },
			level: 'Beginner'
		},
		{
			id: 'chemistry101',
			title: 'Introduction to Chemistry',
			image: '/images/courses/chemistry.jpg',
			instructor: { name: 'David ROBERTS', avatar: '/images/avatars/david.jpg' },
			level: 'Beginner'
		},
		{
			id: 'biology101',
			title: 'Fundamentals of Biology',
			image: '/images/courses/biology.jpg',
			instructor: { name: 'Sarah WONG', avatar: '/images/avatars/sarah.jpg' },
			level: 'Intermediate'
		}
	];

	// Course pagination
	let coursePageIndex = 0;
	const coursesPerPage = 3;
	$: totalCoursePages = Math.ceil(courses.length / coursesPerPage);

	// Get current page of courses
	$: visibleCourses = courses.slice(
		coursePageIndex * coursesPerPage,
		(coursePageIndex + 1) * coursesPerPage
	);

	// Navigate through course pages
	function prevCoursePage() {
		if (coursePageIndex > 0) {
			coursePageIndex--;
		}
	}

	function nextCoursePage() {
		if (coursePageIndex < totalCoursePages - 1) {
			coursePageIndex++;
		}
	}

	// Key for storing custom subjects in localStorage
	const CUSTOM_SUBJECTS_KEY = 'customSubjects';

	// Built-in subjects shipped with the app
	const defaultSubjects = [
		{ id: 'mathematics', name: 'Mathematics', icon: '📊' },
		{ id: 'science', name: 'Science', icon: '🔬' },
		{ id: 'history', name: 'History', icon: '🏛️' },
		{ id: 'computer-science', name: 'Computer Science', icon: '💻' },
		{ id: 'english', name: 'English', icon: '📚' },
		{ id: 'geography', name: 'Geography', icon: '🌍' },
		{ id: 'chemistry', name: 'Chemistry', icon: '🔬' },
		{ id: 'biology', name: 'Biology', icon: '🌿' },
		{ id: 'physics', name: 'Physics', icon: '⚛️' }
	];

	// Reactive list that will include any custom subjects read from localStorage
	let subjects = [...defaultSubjects];

	// Load custom subjects once on component load (browser-only)
	if (browser) {
		try {
			const saved = localStorage.getItem(CUSTOM_SUBJECTS_KEY);
			if (saved) {
				const parsed = JSON.parse(saved);
				if (Array.isArray(parsed)) {
					parsed.forEach((subj: any) => {
						if (subj && subj.id && !subjects.some((s) => s.id === subj.id)) {
							subjects.push(subj);
						}
					});
				}
			}
		} catch (e) {
			console.error('Failed to load custom subjects from localStorage', e);
		}
	}

	// Subject pagination
	let subjectPageIndex = 0;
	const subjectsPerPage = 4;
	$: totalSubjectPages = Math.ceil(subjects.length / subjectsPerPage);

	// Get current page of subjects
	$: visibleSubjects = subjects.slice(
		subjectPageIndex * subjectsPerPage,
		(subjectPageIndex + 1) * subjectsPerPage
	);

	// Navigate through subject pages
	function prevSubjectPage() {
		if (subjectPageIndex > 0) {
			subjectPageIndex--;
		}
	}

	function nextSubjectPage() {
		if (subjectPageIndex < totalSubjectPages - 1) {
			subjectPageIndex++;
		}
	}

	// File upload handling
	function handleFileChange(event: Event) {
		const files = (event.target as HTMLInputElement).files;
		if (files && files.length > 0) {
			uploadedFiles = Array.from(files);
		}
	}

	function handleFileDrop(event: DragEvent) {
		event.preventDefault();
		if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
			uploadedFiles = Array.from(event.dataTransfer.files);
		}
	}

	function preventDefaults(event: Event) {
		event.preventDefault();
		event.stopPropagation();
	}

	// Save support data to database
	async function saveSupportToDatabase() {
		const token = localStorage.getItem('token');
		if (!token) {
			toast.error($i18n.t('You must be logged in to create a class'));
			return;
		}

		isSubmitting = true;

		try {
			const created = await createClassroom(token, {
				name: supportTitle.trim(),
				short_description: shortDescription.trim(),
				subject: selectedSubject || customSubject.trim(),
				custom_subject: customSubject.trim() || undefined,
				course: selectedCourse.trim(),
				learning_objective: learningObjective.trim(),
				competencies: competencies.join(', '),
				learning_type: selectedLearningType || '',
				level: selectedLevel || '',
				content_language: contentLanguage || '',
				estimated_duration: estimatedDuration.trim(),
				keywords,
				capacity: capacity ?? undefined,
				term_start: startDate || undefined,
				term_end: endDate || undefined,
				meeting_days: meetingDays.length ? meetingDays : undefined
			});

			toast.success($i18n.t('Class created successfully!'));

			// Invite the students the teacher added (best-effort; report failures).
			if (studentEmails.length && created?.id) {
				let invited = 0;
				for (const email of studentEmails) {
					try {
						await createInvitation(token, created.id, email, 'student');
						invited++;
					} catch (e) {
						console.error('Invite failed for', email, e);
					}
				}
				if (invited > 0) {
					toast.success(
						$i18n.t('Invited {{count}} student(s)').replace('{{count}}', String(invited))
					);
				}
				if (invited < studentEmails.length) {
					toast.error($i18n.t('Some invitations could not be sent.'));
				}
			}

			goto('/teacher/classes');
		} catch (error: any) {
			console.error('Error creating class:', error);
			toast.error(
				`${$i18n.t('An error occurred')}: ${typeof error === 'string' ? error : error?.message || $i18n.t('Failed to create the class. Please try again.')}`
			);
		} finally {
			isSubmitting = false;
		}
	}

	// Helper: persist a custom subject typed by the user
	function addCustomSubjectIfNeeded() {
		const name = customSubject.trim();
		if (!name) return;

		// Avoid duplicates (case-insensitive)
		if (!subjects.some((s) => s.name.toLowerCase() === name.toLowerCase())) {
			const id = name.toLowerCase().replace(/\s+/g, '-');
			const newSubject = { id, name, icon: '⭐️', custom: true };
			subjects = [...subjects, newSubject];

			// Persist to localStorage for future sessions
			if (browser) {
				try {
					const existing = localStorage.getItem(CUSTOM_SUBJECTS_KEY);
					const list = existing ? JSON.parse(existing) : [];
					if (Array.isArray(list)) {
						list.push(newSubject);
						localStorage.setItem(CUSTOM_SUBJECTS_KEY, JSON.stringify(list));
					} else {
						localStorage.setItem(CUSTOM_SUBJECTS_KEY, JSON.stringify([newSubject]));
					}
				} catch (e) {
					console.error('Failed to persist custom subject', e);
				}
			}
		}
	}

	// Navigation functions
	function nextStep() {
		// If we are exiting the Subject step, store any custom subject the user typed
		if (currentStep === 0) {
			addCustomSubjectIfNeeded();
		}
		// Exiting Objectives: commit a competency the user typed but didn't press Enter on.
		if (currentStep === 2) {
			addCompetency();
		}
		// Exiting Details: commit a keyword the user typed but didn't add.
		if (currentStep === 4) {
			addKeyword();
		}

		if (currentStep < steps.length - 1) {
			const contentEl = document.querySelector('.step-content-enter');
			if (contentEl) {
				contentEl.classList.remove('step-content-enter');
				contentEl.classList.add('step-content-exit');
				setTimeout(() => {
					currentStep++;
				}, 300);
			} else {
				currentStep++;
			}
		} else {
			// Last step - save the data and start the chat
			saveSupportToDatabase();
		}
	}

	function prevStep() {
		if (currentStep > 0) {
			// Add transition direction class for content
			const contentEl = document.querySelector('.step-content-enter');
			if (contentEl) {
				contentEl.classList.remove('step-content-enter');
				contentEl.classList.add('step-content-exit');

				// Use a timeout to allow animation to complete before changing step
				setTimeout(() => {
					currentStep--;
				}, 300);
			} else {
				currentStep--;
			}
		}
	}

	// Validation
	$: isTitleValid = supportTitle.trim().length > 0;
	$: isDescriptionValid = shortDescription.trim().length > 0;
	$: isSubjectSelected = selectedSubject || customSubject.trim().length > 0;
	$: isCourseSelected = uploadedFiles.length > 0 || true; // Make this always return true since we're not requiring course selection anymore
	$: isObjectiveValid = learningObjective.trim().length > 0;
	$: isLearningTypeSelected = selectedLearningType !== null;
	$: isLevelSelected = selectedLevel.trim().length > 0;
	$: canProceed =
		currentStep === 0
			? isTitleValid && isDescriptionValid && isSubjectSelected
			: currentStep === 1
				? selectedCourse.trim().length > 0
				: currentStep === 2
					? isObjectiveValid &&
						selectedLearningType !== null &&
						(competencies.length > 0 || competencyInput.trim().length > 0)
					: currentStep === 3
						? isLevelSelected
						: currentStep === 4
							? keywords.length > 0 || keywordInput.trim().length > 0
							: true;

	// When complete, show the chat interface
	let showChatInterface = false;

	// Format date for display
	function formatDate(dateString: string): string {
		if (!dateString) return '';
		try {
			const date = new Date(dateString);
			return new Intl.DateTimeFormat(navigator.language || 'en-US', {
				year: 'numeric',
				month: 'short',
				day: 'numeric'
			}).format(date);
		} catch (error) {
			console.error('Error formatting date:', error);
			return dateString;
		}
	}

	// Function to get icon based on file extension
	function getFileIcon(filename: string): string {
		const extension = filename.split('.').pop()?.toLowerCase() || '';
		switch (extension) {
			case 'pdf':
				return 'picture_as_pdf';
			case 'doc':
			case 'docx':
				return 'description';
			case 'ppt':
			case 'pptx':
				return 'slideshow';
			case 'mp4':
			case 'avi':
			case 'mov':
				return 'movie';
			case 'jpg':
			case 'jpeg':
			case 'png':
			case 'gif':
				return 'image';
			default:
				return 'insert_drive_file';
		}
	}

	// Subject icons mapping
	const subjectIcons: Record<string, string> = {
		mathematics: 'functions',
		science: 'science',
		history: 'history_edu',
		literature: 'menu_book',
		geography: 'public',
		art: 'palette',
		music: 'music_note',
		physical_education: 'fitness_center',
		computer_science: 'computer',
		languages: 'translate',
		business: 'business',
		philosophy: 'psychology'
	};
</script>

<div class="bg-gray-50 dark:bg-gray-900 min-h-screen px-4 py-8">
	<div class="max-w-4xl mx-auto">
		{#if !showChatInterface}
			<!-- Enhanced header with progress stepper -->
			<div class="mb-8">
				<!-- Custom stepper with connecting lines -->
				<ol class="flex items-center w-full">
					{#each steps as step, index}
						<li class={`flex items-center ${index < steps.length - 1 ? 'w-full' : ''}`}>
							<!-- Step circle with number or checkmark -->
							<div
								class="relative flex items-center justify-center w-10 h-10 rounded-full transition-all duration-500 shrink-0 border-2 step-circle cursor-pointer"
								class:bg-blue-600={currentStep >= index}
								class:border-blue-600={currentStep >= index}
								class:text-white={currentStep >= index}
								class:bg-white={currentStep < index}
								class:border-gray-300={currentStep < index}
								class:dark:border-gray-600={currentStep < index}
								class:dark:bg-gray-700={currentStep < index}
								class:text-gray-500={currentStep < index}
								class:dark:text-gray-300={currentStep < index}
								class:scale-110={currentStep === index}
								class:z-10={currentStep === index}
								class:shadow-lg={currentStep === index}
								on:click={() => {
									// Only allow going back to previous steps or current step
									if (index <= currentStep) {
										currentStep = index;
									}
								}}
								on:keypress={(e) => {
									if (e.key === 'Enter' && index <= currentStep) {
										currentStep = index;
									}
								}}
								tabindex="0"
								aria-label={`Go to ${$i18n.t(steps[index])} step`}
							>
								{#if currentStep > index}
									<!-- Animated checkmark for completed steps -->
									<svg
										class="w-5 h-5"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
										xmlns="http://www.w3.org/2000/svg"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 13l4 4L19 7"
											class="checkmark-appear"
										></path>
									</svg>
								{:else}
									<!-- Step number -->
									<span>{index + 1}</span>
								{/if}

								<!-- Step name with improved animation -->
								<div class="absolute -bottom-7 w-max text-center">
									<span
										class="text-sm font-medium transition-all duration-500 cursor-pointer step-name"
										class:text-blue-600={currentStep >= index}
										class:dark:text-blue-400={currentStep >= index}
										class:text-gray-500={currentStep < index}
										class:dark:text-gray-400={currentStep < index}
										class:scale-110={currentStep === index}
										on:click={() => {
											// Only allow going back to previous steps or current step
											if (index <= currentStep) {
												currentStep = index;
											}
										}}
										tabindex="0"
										aria-label={`Go to ${$i18n.t(steps[index])} step`}
									>
										{$i18n.t(step)}
									</span>
								</div>
							</div>

							<!-- Connecting line (omit for last item) -->
							{#if index < steps.length - 1}
								<div
									class="w-full h-0.5 mx-2 sm:mx-4 relative cursor-pointer connecting-line"
									on:click={() => {
										// If the current step is the one before this line,
										// and we can proceed, go to the next step
										if (currentStep === index && canProceed) {
											nextStep();
										}
										// If we're already past this line, go to the next step
										else if (currentStep > index) {
											currentStep = index + 1;
										}
									}}
									tabindex="0"
									aria-label={`Go to ${$i18n.t(steps[index + 1])} step if available`}
									on:keypress={(e) => {
										if (e.key === 'Enter') {
											if (currentStep === index && canProceed) {
												nextStep();
											} else if (currentStep > index) {
												currentStep = index + 1;
											}
										}
									}}
								>
									<!-- Background line (gray) -->
									<div class="h-full bg-gray-300 dark:bg-gray-600"></div>
									<!-- Progress line (blue) with improved animation -->
									{#if currentStep > index}
										<div
											class="absolute top-0 left-0 h-full bg-blue-600 line-progress"
											style="width: 100%; transition-delay: {index * 0.1}s;"
										></div>
									{/if}
								</div>
							{/if}
						</li>
					{/each}
				</ol>
			</div>

			<!-- Enhanced content container with better styling -->
			<div
				class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 sm:p-8 transition-all duration-300"
			>
				<!-- Step content with improved styling -->
				<div class="min-h-[400px] transition-all duration-300">
					{#if currentStep === 0}
						<!-- Basic Information step - Enhanced UI -->
						<div class="space-y-8 step-content-enter">
							<div>
								<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
									{$i18n.t('Tell us about your class')}
								</h3>

								<div class="mb-6">
									<label
										for="supportTitle"
										class="block text-gray-700 dark:text-gray-200 font-medium mb-2 text-sm"
									>
										{$i18n.t('Title')}
										<span class="text-red-500 ml-1">*</span>
									</label>
									<input
										id="supportTitle"
										type="text"
										bind:value={supportTitle}
										placeholder={$i18n.t('Enter a name for your class')}
										class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors duration-200"
									/>
									<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
										{$i18n.t(
											'Choose a clear, descriptive name that reflects what the class teaches'
										)}
									</p>
								</div>

								<div class="mb-8">
									<label
										for="shortDescription"
										class="block text-gray-700 dark:text-gray-200 font-medium mb-2 text-sm"
									>
										{$i18n.t('Short Description')}
									</label>
									<textarea
										id="shortDescription"
										bind:value={shortDescription}
										placeholder={$i18n.t('Briefly describe what this class covers...')}
										class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white h-24 resize-none"
									></textarea>
									<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
										{$i18n.t('A brief overview helps students know what the class is about')}
									</p>
								</div>
							</div>

							<div
								class="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg border border-gray-100 dark:border-gray-700"
							>
								<label class="block text-gray-800 dark:text-gray-200 font-medium mb-4 text-sm">
									{$i18n.t('Choose the subject this class teaches')}
									<span class="text-red-500 ml-1">*</span>
								</label>

								<div class="relative">
									<!-- Subject cards with improved styling -->
									<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
										{#each visibleSubjects as subject}
											<button
												class={`flex flex-col items-center justify-center p-4 sm:p-5 border-2 rounded-lg hover:shadow-md transition-all ${
													selectedSubject === subject.id
														? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-sm'
														: 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
												}`}
												on:click={() => (selectedSubject = subject.id)}
											>
												<span class="text-3xl sm:text-4xl mb-3">{subject.icon}</span>
												<span class="text-sm text-gray-800 dark:text-gray-200 font-medium"
													>{$i18n.t(subject.name)}</span
												>
											</button>
										{/each}
									</div>

									<!-- Pager controls with better design -->
									<div class="flex justify-center mt-5 gap-2">
										<button
											class="p-2 rounded-full bg-white dark:bg-gray-700 shadow-sm border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
											on:click={prevSubjectPage}
											disabled={subjectPageIndex === 0}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												class="h-5 w-5"
												viewBox="0 0 20 20"
												fill="currentColor"
											>
												<path
													fill-rule="evenodd"
													d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
													clip-rule="evenodd"
												/>
											</svg>
										</button>

										<span class="text-sm text-gray-600 dark:text-gray-400 self-center">
											{subjectPageIndex + 1} / {totalSubjectPages}
										</span>

										<button
											class="p-2 rounded-full bg-white dark:bg-gray-700 shadow-sm border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
											on:click={nextSubjectPage}
											disabled={subjectPageIndex >= totalSubjectPages - 1}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												class="h-5 w-5"
												viewBox="0 0 20 20"
												fill="currentColor"
											>
												<path
													fill-rule="evenodd"
													d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
													clip-rule="evenodd"
												/>
											</svg>
										</button>
									</div>
								</div>

								<div class="mt-5">
									<p class="text-gray-700 dark:text-gray-300 text-sm mb-2">
										{$i18n.t("Don't see your subject? Create a custom one")}
									</p>
									<div class="flex">
										<input
											type="text"
											bind:value={customSubject}
											placeholder={$i18n.t('Enter your custom subject')}
											class="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
										/>
									</div>
								</div>
							</div>
						</div>
					{:else if currentStep === 1}
						<!-- Course Selection step -->
						<div class="space-y-6 step-content-enter">
							<h3 class="text-xl font-medium text-gray-800 dark:text-gray-200">
								{$i18n.t('Course')}
							</h3>

							<div>
								<label
									for="cc-course"
									class="block text-gray-700 dark:text-gray-300 font-medium text-sm mb-2"
								>
									{$i18n.t('Course / programme name')}
									<span class="text-red-500 ml-1">*</span>
								</label>
								<input
									id="cc-course"
									bind:value={selectedCourse}
									placeholder={$i18n.t('e.g. National curriculum — Grade 6 Math')}
									class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
								/>
							</div>

							<div class="mt-2">
								<h4 class="text-gray-700 dark:text-gray-300 mb-6">
									{$i18n.t('Attach Course Materials')}
								</h4>

								<!-- File upload area -->
								<div
									class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
									on:click={() => document.getElementById('file-upload')?.click()}
									on:dragover={preventDefaults}
									on:dragenter={preventDefaults}
									on:drop={handleFileDrop}
								>
									<input
										type="file"
										id="file-upload"
										class="hidden"
										multiple
										on:change={handleFileChange}
										accept=".pdf,.doc,.docx,.pptx,.mp4"
									/>

									<div class="flex flex-col items-center">
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="h-12 w-12 text-blue-500 mb-3"
											fill="none"
											viewBox="0 0 24 24"
											stroke="currentColor"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
											/>
										</svg>

										<p class="text-gray-600 dark:text-gray-300 mb-1">
											{$i18n.t('Click to upload or drag and drop files')}
										</p>
										<p class="text-gray-500 dark:text-gray-400 text-xs">
											{$i18n.t('PDF, DOCX, PPTX, MP4 (max 50MB)')}
										</p>

										{#if uploadedFiles.length > 0}
											<div class="mt-4 p-2 bg-blue-50 dark:bg-blue-900/20 rounded w-full max-w-md">
												<p class="text-sm text-blue-700 dark:text-blue-300 font-medium">
													{uploadedFiles.length}
													{$i18n.t('file(s) selected')}
												</p>
												<ul class="text-xs text-left mt-1 max-h-16 overflow-y-auto">
													{#each uploadedFiles as file}
														<li class="truncate text-gray-600 dark:text-gray-300">{file.name}</li>
													{/each}
												</ul>
											</div>
										{/if}
									</div>
								</div>

								<p class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
									{$i18n.t('Upload materials for this class (optional)')}
								</p>
							</div>
						</div>
					{:else if currentStep === 2}
						<!-- Objectives step - Enhanced UI -->
						<div class="space-y-8 step-content-enter">
							<div>
								<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
									{$i18n.t('Define the class objectives')}
								</h3>

								<div
									class="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg border border-gray-100 dark:border-gray-700"
								>
									<div class="flex items-center justify-between mb-3">
										<label
											for="learningObjective"
											class="block text-gray-700 dark:text-gray-200 font-medium text-sm"
										>
											{$i18n.t('What will students explore in this class?')}
										</label>
										<!-- AI-Assistant icon with tooltip -->
										<div class="relative group">
											<button
												class="p-2 rounded-full bg-yellow-100 dark:bg-yellow-900 text-yellow-600 dark:text-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-800 transition-colors"
											>
												<svg
													xmlns="http://www.w3.org/2000/svg"
													class="h-5 w-5"
													viewBox="0 0 20 20"
													fill="currentColor"
												>
													<path
														d="M11 17a1 1 0 001.447.894l4-2A1 1 0 0017 15V9.236a1 1 0 00-1.447-.894l-4 2a1 1 0 00-.553.894V17zM15.211 6.276a1 1 0 000-1.788l-4.764-2.382a1 1 0 00-.894 0L4.789 4.488a1 1 0 000 1.788l4.764 2.382a1 1 0 00.894 0l4.764-2.382zM4.447 8.342A1 1 0 003 9.236V15a1 1 0 00.553.894l4 2A1 1 0 009 17v-5.764a1 1 0 00-.553-.894l-4-2z"
													/>
												</svg>
											</button>
											<div
												class="absolute z-10 right-0 w-64 p-3 bg-white dark:bg-gray-800 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 text-sm border border-gray-200 dark:border-gray-700 mt-2"
											>
												{$i18n.t('AI can help you craft clear learning objectives for your class')}
											</div>
										</div>
									</div>

									<p class="text-sm text-gray-600 dark:text-gray-400 mb-2">
										{$i18n.t(
											'Be specific about what students should achieve by the end of this class'
										)}
									</p>

									<textarea
										id="learningObjective"
										bind:value={learningObjective}
										placeholder={$i18n.t('By the end of this class, students should be able to...')}
										class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white h-32 resize-none"
									></textarea>
								</div>

								<!-- Teacher: targeted competencies (chips) -->
								<div
									class="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg border border-gray-100 dark:border-gray-700"
								>
									<label class="block text-gray-700 dark:text-gray-200 font-medium text-sm">
										{$i18n.t('Targeted competencies')}
										<span class="text-red-500 ml-1">*</span>
									</label>
									<p class="text-sm text-gray-600 dark:text-gray-400 mt-1 mb-3">
										{$i18n.t('The skills students should master in this class')}
									</p>
									<div class="flex flex-col sm:flex-row gap-2 sm:gap-0">
										<input
											bind:value={competencyInput}
											placeholder={$i18n.t('Add a competency...')}
											class="w-full sm:flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg sm:rounded-r-none focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
											on:keydown={(e) => {
												if (e.key === 'Enter') {
													e.preventDefault();
													addCompetency();
												}
											}}
										/>
										<button
											type="button"
											on:click={addCompetency}
											class="w-full sm:w-auto px-4 py-3 bg-blue-500 text-white rounded-lg sm:rounded-l-none hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors font-medium flex items-center justify-center"
										>
											<span>{$i18n.t('Add')}</span>
										</button>
									</div>
									{#if competencies.length}
										<div class="flex flex-wrap gap-2 mt-3">
											{#each competencies as c}
												<span
													class="inline-flex items-center gap-1 text-sm bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-3 py-1 rounded-full"
												>
													{c}
													<button
														type="button"
														class="hover:text-blue-900"
														on:click={() => removeCompetency(c)}>×</button
													>
												</span>
											{/each}
										</div>
									{/if}
								</div>

								<div
									class="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg border border-gray-100 dark:border-gray-700"
								>
									<div class="mb-4">
										<label class="block text-gray-700 dark:text-gray-200 font-medium text-sm">
											{$i18n.t('What is the teaching approach?')}
											<span class="text-red-500 ml-1">*</span>
										</label>
										<p class="text-sm text-gray-600 dark:text-gray-400 mt-1 mb-4">
											{$i18n.t('Select the approach that best fits this class')}
										</p>
									</div>

									<div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
										{#each learningTypes as type}
											<button
												class={`flex items-center p-4 rounded-lg border-2 transition-all ${
													selectedLearningType === type.id
														? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-sm'
														: 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
												}`}
												on:click={() => {
													selectedLearningType = selectedLearningType === type.id ? null : type.id;
												}}
											>
												<span class="text-2xl mr-3">{type.icon}</span>
												<span class="text-sm font-medium text-gray-800 dark:text-gray-200"
													>{$i18n.t(type.name)}</span
												>
											</button>
										{/each}
									</div>
								</div>
							</div>
						</div>
					{:else if currentStep === 3}
						<!-- Level step - Enhanced UI -->
						<div class="space-y-8 step-content-enter">
							<div>
								<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
									{$i18n.t('Choose the class level')}
								</h3>

								<p class="text-gray-600 dark:text-gray-400 mb-6">
									{$i18n.t('Select the level of the students this class is for')}
									<span class="text-red-500 ml-1">*</span>
								</p>

								<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
									{#each learningLevels as level}
										<button
											class={`flex items-start p-5 border-2 rounded-lg transition-all ${
												selectedLevel === level.id
													? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-sm'
													: 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
											}`}
											on:click={() => (selectedLevel = level.id)}
										>
											<div class="flex items-center">
												<div
													class={`w-12 h-12 rounded-full flex items-center justify-center mr-4 ${
														level.color === 'green'
															? 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-300'
															: level.color === 'red'
																? 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-300'
																: level.color === 'orange'
																	? 'bg-orange-100 text-orange-600 dark:bg-orange-900 dark:text-orange-300'
																	: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900 dark:text-yellow-300'
													}`}
												>
													<svg
														xmlns="http://www.w3.org/2000/svg"
														class="h-6 w-6"
														fill="none"
														viewBox="0 0 24 24"
														stroke="currentColor"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
														/>
													</svg>
												</div>
												<div class="text-left">
													<h4 class="font-medium text-gray-800 dark:text-gray-200 text-lg mb-1">
														{$i18n.t(level.name)}
													</h4>
													<p class="text-sm text-gray-500 dark:text-gray-400">
														{$i18n.t(level.description)}
													</p>
												</div>
											</div>
										</button>
									{/each}
								</div>
							</div>
						</div>
					{:else if currentStep === 4}
						<!-- Details step - Enhanced UI -->
						<div class="space-y-8 step-content-enter">
							<div>
								<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
									{$i18n.t('Fine-tune your class settings')}
								</h3>

								<p class="text-gray-600 dark:text-gray-400 mb-8">
									{$i18n.t('These additional details help us personalize your class')}
								</p>

								<div
									class="bg-gray-50 dark:bg-gray-700 p-6 rounded-lg border border-gray-100 dark:border-gray-700 mb-8"
								>
									<div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
										<!-- Content Language -->
										<div>
											<label
												class="block text-gray-800 dark:text-gray-200 font-medium mb-2 text-sm"
											>
												{$i18n.t('Content Language')}
											</label>
											<div class="relative">
												<select
													bind:value={contentLanguage}
													class="appearance-none w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white pr-8"
												>
													{#each languages as language}
														<option value={language}>{$i18n.t(language)}</option>
													{/each}
												</select>
												<div
													class="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none"
												>
													<svg
														class="w-5 h-5 text-gray-500 dark:text-gray-400"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M19 9l-7 7-7-7"
														></path>
													</svg>
												</div>
											</div>
											<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
												{$i18n.t('Select the language your class is delivered in')}
											</p>
										</div>

										<!-- Estimated Duration -->
										<div>
											<label
												class="block text-gray-800 dark:text-gray-200 font-medium mb-2 text-sm"
											>
												{$i18n.t('Estimated Duration')}
											</label>
											<div class="relative">
												<select
													bind:value={estimatedDuration}
													class="appearance-none w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white pr-8"
												>
													{#each durations as duration}
														<option value={duration}>{duration}</option>
													{/each}
												</select>
												<div
													class="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none"
												>
													<svg
														class="w-5 h-5 text-gray-500 dark:text-gray-400"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M19 9l-7 7-7-7"
														></path>
													</svg>
												</div>
											</div>
											<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
												{$i18n.t('How long will this class run?')}
											</p>
										</div>
									</div>
								</div>

								<!-- Keywords -->
								<div
									class="bg-gray-50 dark:bg-gray-700 p-6 rounded-lg border border-gray-100 dark:border-gray-700 mb-8"
								>
									<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2 text-sm">
										{$i18n.t('Keywords (for search & recommendations)')}
									</label>
									<p class="mb-4 text-sm text-gray-600 dark:text-gray-400">
										{$i18n.t('Add relevant keywords to help find this class later')}
									</p>

									<div class="flex flex-col sm:flex-row gap-2 sm:gap-0">
										<input
											type="text"
											bind:value={keywordInput}
											on:keydown={handleKeyDown}
											placeholder={$i18n.t('Add keywords...')}
											class="w-full sm:flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg sm:rounded-r-none focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
										/>
										<button
											on:click={addKeyword}
											class="w-full sm:w-auto px-4 py-3 bg-blue-500 text-white rounded-lg sm:rounded-l-none hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors font-medium flex items-center justify-center"
										>
											<span>{$i18n.t('Add')}</span>
										</button>
									</div>

									<!-- Keywords display -->
									{#if keywords.length > 0}
										<div
											class="flex flex-wrap gap-2 mt-4 p-3 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600"
										>
											{#each keywords as keyword}
												<div
													class="bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-100 px-3 py-1.5 rounded-full text-sm flex items-center gap-2 hover:bg-blue-200 dark:hover:bg-blue-700 transition-colors"
												>
													{keyword}
													<button
														on:click={() => removeKeyword(keyword)}
														class="p-1 hover:bg-blue-200 dark:hover:bg-blue-600 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
														aria-label="Remove keyword"
													>
														<svg
															xmlns="http://www.w3.org/2000/svg"
															class="h-4 w-4"
															viewBox="0 0 20 20"
															fill="currentColor"
														>
															<path
																fill-rule="evenodd"
																d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
																clip-rule="evenodd"
															/>
														</svg>
													</button>
												</div>
											{/each}
										</div>
									{:else}
										<div
											class="mt-4 p-3 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 text-sm text-gray-500 dark:text-gray-400 italic"
										>
											{$i18n.t('No keywords added yet')}
										</div>
									{/if}
								</div>

								<!-- Schedule & capacity (teacher) -->
								<div
									class="bg-gray-50 dark:bg-gray-700 p-6 rounded-lg border border-gray-100 dark:border-gray-700"
								>
									<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2 text-sm">
										{$i18n.t('Schedule & capacity')}
									</label>
									<p class="mb-4 text-sm text-gray-600 dark:text-gray-400">
										{$i18n.t('Set the class term, meeting days and a student cap (all optional)')}
									</p>

									<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
										<div class="relative">
											<label
												class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1"
											>
												{$i18n.t('Term start')}
											</label>
											<input
												type="date"
												bind:value={startDate}
												class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
											/>
										</div>
										<div class="relative">
											<label
												class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1"
											>
												{$i18n.t('Term end')}
											</label>
											<input
												type="date"
												bind:value={endDate}
												class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
											/>
										</div>
									</div>

									<!-- Weekly meeting days -->
									<div class="mt-4">
										<label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
											{$i18n.t('Weekly meeting days')}
										</label>
										<div class="flex flex-wrap gap-2">
											{#each weekdays as d}
												<button
													type="button"
													class={`px-3 py-1.5 rounded-full text-sm border transition ${
														meetingDays.includes(d)
															? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
															: 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-blue-300'
													}`}
													on:click={() => toggleDay(d)}
												>
													{$i18n.t(d)}
												</button>
											{/each}
										</div>
									</div>

									<!-- Capacity -->
									<div class="mt-4">
										<label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
											{$i18n.t('Max students (capacity)')}
										</label>
										<input
											type="number"
											min="1"
											bind:value={capacity}
											placeholder={$i18n.t('Leave empty for unlimited')}
											class="w-full sm:w-48 px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
										/>
									</div>
								</div>
							</div>
						</div>
						<!-- {:else if currentStep === 5} -->
						<!-- Avatar step placeholder -->
						<!-- <div class="space-y-6 step-content-enter">
					<div class="text-gray-800 dark:text-gray-200">
						<h3 class="text-xl font-semibold mb-4">{$i18n.t('Choose Your Avatar')}</h3>
						<p>{$i18n.t('This step would allow selecting a tutor avatar.')}</p>
						</div>
					</div> -->
					{:else if currentStep === 5}
						<!-- Students step: invite by email -->
						<div class="space-y-8 step-content-enter">
							<div>
								<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
									{$i18n.t('Invite students')}
								</h3>
								<p class="text-gray-600 dark:text-gray-400 mb-6">
									{$i18n.t(
										'Add the emails of students to invite. They get a join link by invitation — you can always add more later.'
									)}
								</p>

								<div
									class="bg-gray-50 dark:bg-gray-700 p-6 rounded-lg border border-gray-100 dark:border-gray-700"
								>
									<div class="flex flex-col sm:flex-row gap-2 sm:gap-0">
										<input
											type="email"
											bind:value={studentEmailInput}
											on:keydown={(e) => {
												if (e.key === 'Enter') {
													e.preventDefault();
													addStudentEmail();
												}
											}}
											placeholder={$i18n.t('student@example.com')}
											class="w-full sm:flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg sm:rounded-r-none focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
										/>
										<button
											type="button"
											on:click={addStudentEmail}
											class="w-full sm:w-auto px-4 py-3 bg-blue-500 text-white rounded-lg sm:rounded-l-none hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors font-medium flex items-center justify-center"
										>
											<span>{$i18n.t('Add')}</span>
										</button>
									</div>

									{#if studentEmails.length > 0}
										<div
											class="flex flex-wrap gap-2 mt-4 p-3 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600"
										>
											{#each studentEmails as email}
												<div
													class="inline-flex items-center gap-1 text-sm bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-3 py-1 rounded-full"
												>
													{email}
													<button
														type="button"
														class="hover:text-blue-900"
														on:click={() => removeStudentEmail(email)}>×</button
													>
												</div>
											{/each}
										</div>
									{:else}
										<p class="mt-4 text-sm text-gray-500 dark:text-gray-400">
											{$i18n.t("No students added yet — that's fine, you can invite them anytime.")}
										</p>
									{/if}
								</div>
							</div>
						</div>
					{:else if currentStep === 6}
						<!-- Review step - Clean, professional design -->
						<div class="space-y-8 step-content-enter">
							<div>
								<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
									{$i18n.t('Review your class')}
								</h3>

								<p class="text-gray-600 dark:text-gray-400 mb-8">
									{$i18n.t('Verify all details before creating your class')}
								</p>

								<div
									class="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden border border-gray-200 dark:border-gray-700"
								>
									<!-- Title and subject header -->
									<div
										class="bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-5 flex items-center justify-between"
									>
										<div class="flex-1">
											<h4 class="text-lg font-bold text-white">{supportTitle}</h4>
											{#if selectedSubject || customSubject}
												<div class="flex items-center mt-2">
													<span
														class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-white/20 text-white"
													>
														{selectedSubject
															? (subjects.find((s) => s.id === selectedSubject)?.name ??
																selectedSubject)
															: customSubject}
													</span>
												</div>
											{/if}
										</div>
									</div>

									<!-- Content sections -->
									<div class="p-0">
										<!-- Summary Info -->
										<div
											class="px-6 py-5 border-b border-gray-200 dark:border-gray-700 grid grid-cols-1 md:grid-cols-2 gap-6"
										>
											<!-- Left column -->
											<div class="space-y-5">
												{#if shortDescription}
													<div>
														<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">
															{$i18n.t('Description')}
														</h5>
														<p class="text-gray-800 dark:text-gray-200">{shortDescription}</p>
													</div>
												{/if}

												{#if learningObjective}
													<div>
														<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">
															{$i18n.t('Learning Objectives')}
														</h5>
														<p class="text-gray-800 dark:text-gray-200">{learningObjective}</p>
													</div>
												{/if}
											</div>

											<!-- Right column -->
											<div class="space-y-5">
												<div>
													<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">
														{$i18n.t('Learning Type')}
													</h5>
													{#if selectedLearningType}
														<div
															class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-200"
														>
															{learningTypes.find((lt) => lt.id === selectedLearningType)?.name ||
																selectedLearningType}
														</div>
													{:else}
														<p class="text-gray-400 dark:text-gray-500 italic text-sm">
															Not specified
														</p>
													{/if}
												</div>

												<div>
													<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">
														{$i18n.t('Learning Level')}
													</h5>
													{#if selectedLevel}
														<div
															class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200"
														>
															{learningLevels.find((ll) => ll.id === selectedLevel)?.name ||
																selectedLevel}
														</div>
													{:else}
														<p class="text-gray-400 dark:text-gray-500 italic text-sm">
															Not specified
														</p>
													{/if}
												</div>

												<div>
													<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">
														{$i18n.t('Content Details')}
													</h5>
													<div class="flex items-center text-gray-700 dark:text-gray-300 space-x-4">
														<div class="flex items-center">
															<svg
																xmlns="http://www.w3.org/2000/svg"
																class="h-4 w-4 text-gray-500 dark:text-gray-400 mr-1.5"
																fill="none"
																viewBox="0 0 24 24"
																stroke="currentColor"
															>
																<path
																	stroke-linecap="round"
																	stroke-linejoin="round"
																	stroke-width="2"
																	d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"
																/>
															</svg>
															<span class="text-sm">{contentLanguage}</span>
														</div>
														<div class="flex items-center">
															<svg
																xmlns="http://www.w3.org/2000/svg"
																class="h-4 w-4 text-gray-500 dark:text-gray-400 mr-1.5"
																fill="none"
																viewBox="0 0 24 24"
																stroke="currentColor"
															>
																<path
																	stroke-linecap="round"
																	stroke-linejoin="round"
																	stroke-width="2"
																	d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
																/>
															</svg>
															<span class="text-sm">{estimatedDuration}</span>
														</div>
													</div>
												</div>
											</div>
										</div>

										<!-- Additional Information -->
										{#if keywords.length > 0 || (uploadedFiles && uploadedFiles.length > 0) || startDate || endDate}
											<div class="px-6 py-5 border-b border-gray-200 dark:border-gray-700">
												<!-- Keywords -->
												{#if keywords.length > 0}
													<div class="mb-4">
														<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
															{$i18n.t('Keywords')}
														</h5>
														<div class="flex flex-wrap gap-2">
															{#each keywords as keyword}
																<span
																	class="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200"
																>
																	{keyword}
																</span>
															{/each}
														</div>
													</div>
												{/if}

												<!-- Files -->
												{#if uploadedFiles && uploadedFiles.length > 0}
													<div class="mb-4">
														<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
															{$i18n.t('Uploaded Files')}
														</h5>
														<ul class="space-y-1.5">
															{#each uploadedFiles as file}
																<li
																	class="flex items-center text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700/50 px-3 py-2 rounded-md"
																>
																	<svg
																		xmlns="http://www.w3.org/2000/svg"
																		class="h-4 w-4 text-gray-500 dark:text-gray-400 mr-2"
																		fill="none"
																		viewBox="0 0 24 24"
																		stroke="currentColor"
																	>
																		<path
																			stroke-linecap="round"
																			stroke-linejoin="round"
																			stroke-width="2"
																			d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
																		/>
																	</svg>
																	<span class="text-sm truncate">{file.name}</span>
																</li>
															{/each}
														</ul>
													</div>
												{/if}

												<!-- Availability -->
												{#if startDate || endDate}
													<div>
														<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
															{$i18n.t('Availability')}
														</h5>
														<div class="flex items-center gap-4">
															{#if startDate}
																<div class="flex items-center text-gray-700 dark:text-gray-300">
																	<svg
																		xmlns="http://www.w3.org/2000/svg"
																		class="h-4 w-4 text-gray-500 dark:text-gray-400 mr-1.5"
																		fill="none"
																		viewBox="0 0 24 24"
																		stroke="currentColor"
																	>
																		<path
																			stroke-linecap="round"
																			stroke-linejoin="round"
																			stroke-width="2"
																			d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
																		/>
																	</svg>
																	<span class="text-sm"
																		>{$i18n.t('From')}: {formatDate(startDate)}</span
																	>
																</div>
															{/if}
															{#if endDate}
																<div class="flex items-center text-gray-700 dark:text-gray-300">
																	<svg
																		xmlns="http://www.w3.org/2000/svg"
																		class="h-4 w-4 text-gray-500 dark:text-gray-400 mr-1.5"
																		fill="none"
																		viewBox="0 0 24 24"
																		stroke="currentColor"
																	>
																		<path
																			stroke-linecap="round"
																			stroke-linejoin="round"
																			stroke-width="2"
																			d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
																		/>
																	</svg>
																	<span class="text-sm">{$i18n.t('To')}: {formatDate(endDate)}</span
																	>
																</div>
															{/if}
														</div>
													</div>
												{/if}
											</div>
										{/if}

										<!-- Confirmation Message -->
										<div class="px-6 py-5 bg-gray-50 dark:bg-gray-700">
											<div class="flex items-center text-gray-700 dark:text-gray-300">
												<svg
													xmlns="http://www.w3.org/2000/svg"
													class="h-5 w-5 text-blue-500 mr-2"
													fill="none"
													viewBox="0 0 24 24"
													stroke="currentColor"
												>
													<path
														stroke-linecap="round"
														stroke-linejoin="round"
														stroke-width="2"
														d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
													/>
												</svg>
												<p class="text-sm">
													{$i18n.t(
														'Click "Create class" below to create your class and invite the students you added.'
													)}
												</p>
											</div>
										</div>
									</div>
								</div>
							</div>
						</div>
					{/if}
				</div>

				<!-- Enhanced navigation buttons -->
				<div class="flex justify-between mt-10 pt-6 border-t border-gray-100 dark:border-gray-700">
					<button
						on:click={() => {
							if (currentStep === 0) {
								window.location.href = '/student/dashboard';
							} else {
								prevStep();
							}
						}}
						class="px-6 py-2.5 text-sm font-semibold bg-gray-100 text-gray-800 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600 rounded-full transition-colors duration-200 flex items-center"
						disabled={isSubmitting}
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
						{currentStep === 0 ? $i18n.t('Cancel') : $i18n.t('Back')}
					</button>

					<button
						on:click={nextStep}
						class="px-6 py-2.5 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white dark:bg-gradient-to-r dark:from-blue-600 dark:to-indigo-600 dark:hover:from-blue-700 dark:hover:to-indigo-700 rounded-full disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 flex items-center shadow-sm"
						disabled={!canProceed || isSubmitting}
					>
						{#if isSubmitting}
							<svg
								class="animate-spin -ml-1 mr-2 h-5 w-5 text-white"
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
							>
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
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								></path>
							</svg>
							{$i18n.t('Processing...')}
						{:else}
							{currentStep === steps.length - 1 ? $i18n.t('Create class') : $i18n.t('Continue')}
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5 ml-2"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
									clip-rule="evenodd"
								/>
							</svg>
						{/if}
					</button>
				</div>
			</div>
		{:else}
			<!-- Success screen -->
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center animate-fadeIn">
				<div class="mb-6 flex justify-center">
					<div
						class="w-20 h-20 rounded-full bg-green-100 dark:bg-green-800 flex items-center justify-center"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-10 w-10 text-green-600 dark:text-green-300"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M5 13l4 4L19 7"
							/>
						</svg>
					</div>
				</div>

				<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-3">
					{$i18n.t('Class Created!')}
				</h2>
				<p class="text-gray-600 dark:text-gray-300 mb-8 max-w-md mx-auto">
					{$i18n.t('Your class has been successfully created. Add students to get started!')}
				</p>

				<button
					on:click={() => goto('/teacher/classes')}
					class="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium"
				>
					{$i18n.t('View my classes')}
				</button>
			</div>
		{/if}
	</div>
</div>

<style>
	/* Enhanced animation classes */
	.animate-fadeIn {
		animation: fadeIn 0.4s ease-out;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	/* Step circle animations */
	.step-circle {
		transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); /* Bouncy effect */
	}

	.step-circle:hover {
		transform: scale(1.1);
		box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
	}

	.step-name {
		transition: all 0.3s ease;
	}

	.step-name:hover {
		transform: scale(1.05);
	}

	/* Connecting line animation */
	.line-progress {
		transition:
			width 0.5s ease-out,
			background-color 0.5s ease-out;
	}

	/* Step content slide animations */
	.step-content-enter {
		animation: slideIn 0.5s ease-out forwards;
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateX(30px);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}

	.step-content-exit {
		animation: slideOut 0.3s ease-in forwards;
	}

	@keyframes slideOut {
		from {
			opacity: 1;
			transform: translateX(0);
		}
		to {
			opacity: 0;
			transform: translateX(-30px);
		}
	}

	/* Checkmark animation */
	.checkmark-appear {
		stroke-dasharray: 100;
		stroke-dashoffset: 100;
		animation: drawCheck 0.6s ease-in-out forwards;
	}

	@keyframes drawCheck {
		from {
			stroke-dashoffset: 100;
		}
		to {
			stroke-dashoffset: 0;
		}
	}

	/* Connecting line animation */
	.connecting-line {
		position: relative;
		overflow: hidden;
	}

	.connecting-line:hover::after {
		content: '';
		position: absolute;
		top: -5px;
		left: 0;
		right: 0;
		height: 10px;
		background-color: rgba(37, 99, 235, 0.1);
		border-radius: 5px;
	}
</style>
