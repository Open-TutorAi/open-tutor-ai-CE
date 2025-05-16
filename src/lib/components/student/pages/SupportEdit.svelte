<!-- student/support/[id]/edit/+page.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getSupportById, updateSupport } from '$lib/apis/supports';
	import type { Writable } from 'svelte/store';
	import { browser } from '$app/environment';

	// Get i18n from context with proper typing
	interface I18n {
		t: (key: string) => string;
	}
	const i18n = getContext<Writable<I18n>>('i18n');

	// Extract support ID from URL
	$: supportId = $page.params.id;

	// Support data
	let support: any = null;
	let loading = true;
	let error: string | null = null;
	let isSubmitting = false;

	// Form data
	let supportTitle = '';
	let shortDescription = '';
	let selectedSubject = '';
	let customSubject = '';
	let selectedCourse = '';
	let learningObjective = '';
	let selectedLearningType: string | null = null;
	let selectedLevel = '';
	let contentLanguage = 'English';
	let estimatedDuration = '30min';
	let accessType = 'Private';
	let keywords: string[] = [];
	let keywordInput = '';
	let startDate = '';
	let endDate = '';

	// Learning types
	const learningTypes = [
		{ id: 'exam', name: "I'm preparing for an exam", icon: '📝' },
		{ id: 'course', name: "I'm reviewing a course", icon: '📚' },
		{ id: 'skill', name: 'I want to build a new skill', icon: '🚀' }
	];

	// Learning levels
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

	// Content languages
	const languages = ['English', 'French', 'Arabic', 'Spanish', 'German'];

	// Duration options
	const durations = ['15min', '30min', '45min', '1h', '1h30min', '2h'];

	// Access types
	const accessTypes = ['Private', 'Public', 'Shared'];

	// Predefined subjects
	const subjects = [
		{ id: 'mathematics', name: 'Mathematics', icon: '📊' },
		{ id: 'science', name: 'Science', icon: '🔬' },
		{ id: 'history', name: 'History', icon: '🏛️' },
		{ id: 'computer-science', name: 'Computer Science', icon: '💻' },
		{ id: 'english', name: 'English', icon: '📚' },
		{ id: 'Geography', name: 'Geography', icon: '🌍' },
		{ id: 'Chemistry', name: 'Chemistry', icon: '🔬' },
		{ id: 'Biology', name: 'Biology', icon: '🌿' },
		{ id: 'Physics', name: 'Physics', icon: '⚛️' },
		{ id: 'Other', name: 'Other', icon: '❓' }
	];

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

	// Load support data
	onMount(async () => {
		if (!browser) return;

		try {
			const token = localStorage.getItem('token');
			if (!token) {
				error = $i18n.t('Authentication required');
				loading = false;
				return;
			}

			if (!supportId) {
				error = $i18n.t('Support ID is required');
				loading = false;
				return;
			}

			console.log(`Loading support with ID: ${supportId}`);
			support = await getSupportById(token, supportId);
			console.log('Support data loaded:', support);

			// Populate form fields with existing data
			supportTitle = support.title || '';
			shortDescription = support.short_description || '';
			selectedSubject = support.subject || '';
			customSubject = support.custom_subject || '';
			selectedCourse = support.course_id || '';
			learningObjective = support.learning_objective || '';
			selectedLearningType = support.learning_type || null;
			selectedLevel = support.level || '';
			contentLanguage = support.content_language || 'English';
			estimatedDuration = support.estimated_duration || '30min';
			accessType = support.access_type || 'Private';
			keywords = support.keywords || [];
			startDate = support.start_date || '';
			endDate = support.end_date || '';
		} catch (err: any) {
			console.error('Error loading support:', err);
			error = err?.message || $i18n.t('Failed to load support details');
		} finally {
			loading = false;
		}
	});

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

	// Update support in database
	async function updateSupportInDatabase() {
		if (!supportId || !browser) return;

		const token = localStorage.getItem('token');
		if (!token) {
			toast.error($i18n.t('You must be logged in to update a support'));
			return;
		}

		isSubmitting = true;

		try {
			const supportDetails = {
				title: supportTitle,
				short_description: shortDescription || undefined,
				subject: selectedSubject || customSubject,
				custom_subject: customSubject || undefined,
				course_id: selectedCourse || undefined,
				learning_objective: learningObjective || undefined,
				learning_type: selectedLearningType || undefined,
				level: selectedLevel || undefined,
				content_language: contentLanguage || undefined,
				estimated_duration: estimatedDuration || undefined,
				access_type: accessType || undefined,
				keywords: keywords.length > 0 ? keywords : undefined,
				start_date: startDate || undefined,
				end_date: endDate || undefined,
				avatar_id: support?.avatar_id || undefined
			};

			console.log(`Updating support with ID: ${supportId}`);
			console.log('Update data:', JSON.stringify(supportDetails));

			const updateResponse = await updateSupport(token, supportId, supportDetails);
			console.log('Update response:', updateResponse);

			toast.success($i18n.t('Support updated successfully!'));

			// Navigate back to support details
			goto(`/student/support/${supportId}`);
		} catch (error: any) {
			console.error('Error updating support:', error);
			toast.error(
				`${$i18n.t('An error occurred')}: ${error?.message || $i18n.t('Failed to update support')}`
			);
		} finally {
			isSubmitting = false;
		}
	}

	// Validation
	$: isTitleValid = supportTitle.trim().length > 0;
	$: isSubjectSelected = selectedSubject || customSubject.trim().length > 0;
	$: canUpdate = isTitleValid && isSubjectSelected && !isSubmitting;
</script>

<div class="bg-gray-50 dark:bg-gray-900 min-h-screen px-4 py-8">
	<div class="max-w-4xl mx-auto">
		<!-- Header with back button -->
		<div class="mb-6">
			<button
				on:click={() => goto(`/student/support/${supportId}`)}
				class="inline-flex items-center text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white mb-4"
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
				{$i18n.t('Back to Support Details')}
			</button>

			<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
				{$i18n.t('Edit Support')}
			</h1>
		</div>

		{#if loading}
			<!-- Loading skeleton -->
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 animate-pulse">
				<div class="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-6"></div>

				<div class="grid grid-cols-1 gap-6">
					<div class="h-24 bg-gray-200 dark:bg-gray-700 rounded w-full mb-4"></div>
					<div class="h-24 bg-gray-200 dark:bg-gray-700 rounded w-full mb-4"></div>
				</div>
			</div>
		{:else if error}
			<!-- Error state -->
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
				<div class="text-center py-8">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-12 w-12 text-red-500 mx-auto mb-4"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
					<h3 class="text-xl font-medium text-gray-900 dark:text-white mb-2">
						{$i18n.t('Error Loading Support')}
					</h3>
					<p class="text-gray-600 dark:text-gray-400">{error}</p>

					<button
						on:click={() => goto('/student/supports')}
						class="mt-6 inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
					>
						{$i18n.t('Return to Support List')}
					</button>
				</div>
			</div>
		{:else}
			<!-- Edit form -->
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 sm:p-8">
				<!-- Basic Information section -->
				<div class="space-y-8 mb-8">
					<div>
						<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
							{$i18n.t('Basic Information')}
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
								placeholder={$i18n.t('Enter a title for your support')}
								class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors duration-200"
							/>
							<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
								{$i18n.t('Choose a clear, descriptive title that reflects your learning goal')}
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
								placeholder={$i18n.t('Briefly describe what you want to learn...')}
								class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white h-24 resize-none"
							></textarea>
							<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
								{$i18n.t('A brief overview helps us tailor the learning experience to your needs')}
							</p>
						</div>
					</div>

					<div
						class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700"
					>
						<label class="block text-gray-800 dark:text-gray-200 font-medium mb-4 text-sm">
							{$i18n.t("Choose a subject you'd like to study")}
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

				<!-- Learning Objectives section -->
				<div class="space-y-8 mb-8">
					<div>
						<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
							{$i18n.t('Learning Objectives')}
						</h3>

						<div
							class="mb-8 bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700"
						>
							<label
								for="learningObjective"
								class="block text-gray-700 dark:text-gray-200 font-medium text-sm mb-2"
							>
								{$i18n.t('What do you want to explore?')}
							</label>

							<p class="text-sm text-gray-600 dark:text-gray-400 mb-2">
								{$i18n.t('Be specific about what you hope to achieve by the end of this support')}
							</p>

							<textarea
								id="learningObjective"
								bind:value={learningObjective}
								placeholder={$i18n.t('By the end of this support, I should be able to...')}
								class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white h-32 resize-none"
							></textarea>
						</div>

						<div
							class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700"
						>
							<div class="mb-4">
								<label class="block text-gray-700 dark:text-gray-200 font-medium text-sm">
									{$i18n.t('How can I support you?')}
								</label>
								<p class="text-sm text-gray-600 dark:text-gray-400 mt-1 mb-4">
									{$i18n.t('Select the option that best describes your learning goal')}
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

				<!-- Learning Level section -->
				<div class="space-y-8 mb-8">
					<div>
						<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
							{$i18n.t('Learning Level')}
						</h3>

						<p class="text-gray-600 dark:text-gray-400 mb-6">
							{$i18n.t('Select the appropriate learning level for this material')}
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

				<!-- Additional Details section -->
				<div class="space-y-8 mb-8">
					<div>
						<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
							{$i18n.t('Additional Details')}
						</h3>

						<div
							class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700 mb-8"
						>
							<div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
								<!-- Content Language -->
								<div>
									<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2 text-sm">
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
										{$i18n.t('Select the language you want your content delivered in')}
									</p>
								</div>

								<!-- Estimated Duration -->
								<div>
									<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2 text-sm">
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
										{$i18n.t('How long do you expect to spend on this support?')}
									</p>
								</div>
							</div>
						</div>

						<!-- Keywords -->
						<div
							class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700 mb-8"
						>
							<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2 text-sm">
								{$i18n.t('Keywords (for search & recommendations)')}
							</label>
							<p class="mb-4 text-sm text-gray-600 dark:text-gray-400">
								{$i18n.t('Add relevant keywords to help find this support later')}
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

						<!-- Availability -->
						<div
							class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700"
						>
							<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2 text-sm">
								{$i18n.t('Availability')}
							</label>
							<p class="mb-4 text-sm text-gray-600 dark:text-gray-400">
								{$i18n.t('Set when this support should be available (optional)')}
							</p>

							<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
								<div class="relative">
									<label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
										{$i18n.t('Start Date')}
									</label>
									<input
										type="date"
										bind:value={startDate}
										class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
									/>
								</div>
								<div class="relative">
									<label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
										{$i18n.t('End Date')}
									</label>
									<input
										type="date"
										bind:value={endDate}
										class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
									/>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Form actions -->
				<div class="flex justify-end space-x-4 border-t border-gray-200 dark:border-gray-700 pt-6">
					<button
						on:click={() => goto(`/student/support/${supportId}`)}
						class="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
					>
						{$i18n.t('Cancel')}
					</button>

					<button
						on:click={updateSupportInDatabase}
						class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
						disabled={!canUpdate}
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
							{$i18n.t('Updating...')}
						{:else}
							{$i18n.t('Update Support')}
						{/if}
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>
