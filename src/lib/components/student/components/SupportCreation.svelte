<!-- student/support/+page.svelte -->
<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	// Step Navigation
	const steps = [
		{ id: 'subject', label: 'Subject' },
		{ id: 'course', label: 'Course' },
		{ id: 'objectives', label: 'Objectives' },
		{ id: 'level', label: 'Level' },
		{ id: 'details', label: 'Details' },
		{ id: 'avatar', label: 'Avatar' },
		{ id: 'review', label: 'Review' }
	];

	let currentStep = 0;

	// Form data
	let supportTitle = '';
	let shortDescription = '';
	let selectedSubject = '';
	let customSubject = '';
	let selectedCourse = '';
	let uploadedFiles: File[] = [];

	// Learning objectives data
	let learningObjective = '';
	let selectedLearningType: string[] = [];
	const learningTypes = [
		{ id: 'conceptual', name: 'Conceptual', icon: '🧠' },
		{ id: 'practical', name: 'Practical', icon: '🔧' },
		{ id: 'analytical', name: 'Analytical', icon: '📊' },
		{ id: 'problem-solving', name: 'Problem Solving', icon: '💡' }
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
			id: 'algo101',
			title: 'Introduction to Algorithmic',
			image: '/images/courses/algorithmic.jpg',
			instructor: { name: 'Samia AHMED', avatar: '/images/avatars/samia.jpg' },
			level: 'Beginner'
		},
		{
			id: 'islam101',
			title: 'The rise and explanation of Islam',
			image: '/images/courses/islam.jpg',
			instructor: { name: 'Ibrahim AMINE', avatar: '/images/avatars/ibrahim.jpg' },
			level: 'Advanced'
		},
		{
			id: 'math101',
			title: 'Number Sense and Calculations',
			image: '/images/courses/math.jpg',
			instructor: { name: 'Ahmed SAMI', avatar: '/images/avatars/ahmed.jpg' },
			level: 'Intermediate'
		},
		{
			id: 'physics101',
			title: 'Introduction to Physics',
			image: '/images/courses/physics.jpg',
			instructor: { name: 'Maria JOHNSON', avatar: '/images/avatars/maria.jpg' },
			level: 'Beginner'
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
		{ id: 'Physics', name: 'Physics', icon: '⚛️' }
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

	// Navigation functions
	function nextStep() {
		if (currentStep < steps.length - 1) {
			currentStep++;
		} else {
			// Last step - start the chat
			showChatInterface = true;
		}
	}

	function prevStep() {
		if (currentStep > 0) {
			currentStep--;
		}
	}

	// Validation
	$: isTitleValid = supportTitle.trim().length > 0;
	$: isSubjectSelected = selectedSubject || customSubject.trim().length > 0;
	$: isCourseSelected = selectedCourse || uploadedFiles.length > 0;
	$: isObjectiveValid = learningObjective.trim().length > 0;
	$: isLearningTypeSelected = selectedLearningType.length > 0;
	$: isLevelSelected = selectedLevel.trim().length > 0;
	$: canProceed =
		currentStep === 0
			? isTitleValid && isSubjectSelected
			: currentStep === 1
				? true
				: currentStep === 2
					? true
					: currentStep === 3
						? isLevelSelected
						: true;

	// When complete, show the chat interface
	let showChatInterface = false;
</script>

<div class="h-full">
	{#if !showChatInterface}
		<!-- Wizard interface -->
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-5xl mx-auto">
			<!-- Steps progress indicator -->
			<div class="mb-6 sm:mb-8 lg:mb-10 px-2 sm:px-4">
				<div class="flex items-center">
					{#each steps as step, index}
						{#if index > 0}
							<div class="flex-grow h-px bg-gray-200 dark:bg-gray-600 relative mx-1 sm:mx-2">
								{#if index <= currentStep}
									<div
										class="absolute inset-0 bg-blue-600 dark:bg-blue-500 transition-all duration-300"
										style="width: 100%;"
									></div>
								{/if}
							</div>
						{/if}

						<!-- Step circle -->
						<div class="flex-shrink-0 relative">
							<div
								class={`w-6 h-6 sm:w-8 sm:h-8 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${index < currentStep ? 'bg-blue-600 border-blue-600 text-white' : index === currentStep ? 'bg-white dark:bg-gray-800 border-blue-600 text-blue-600 dark:text-blue-400' : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-400 dark:text-gray-500'}`}
							>
								{#if index < currentStep}
									<!-- Check icon for completed steps -->
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-3 w-3 sm:h-4 sm:w-4"
										viewBox="0 0 20 20"
										fill="currentColor"
									>
										<path
											fill-rule="evenodd"
											d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
											clip-rule="evenodd"
										/>
									</svg>
								{:else if index === currentStep}
									<!-- Current step has a filled center dot -->
									<span class="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-current"></span>
								{:else}
									<!-- Future steps have empty circles -->
									<span class="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-transparent"></span>
								{/if}
							</div>
							<span
								class="absolute top-full mt-1 sm:mt-2 left-1/2 transform -translate-x-1/2 text-[10px] sm:text-xs font-medium whitespace-nowrap max-w-[80px] sm:max-w-none text-center leading-tight sm:leading-normal"
								class:text-blue-600={index === currentStep}
								class:dark:text-blue-400={index === currentStep}
								class:text-gray-500={index !== currentStep}
								class:dark:text-gray-400={index !== currentStep}
							>
								{$i18n.t(step.label)}
							</span>
						</div>
					{/each}
				</div>
			</div>

			<!-- Step content -->
			<div class="mb-8 mt-12">
				{#if currentStep === 0}
					<!-- Subject step -->
					<div class="space-y-6">
						<div>
							<label
								for="supportTitle"
								class="block text-gray-800 dark:text-gray-200 font-medium mb-2"
							>
								{$i18n.t('Support Title')} <span class="text-red-500">*</span>
							</label>
							<input
								type="text"
								id="supportTitle"
								bind:value={supportTitle}
								placeholder={$i18n.t('e.g., Solving Linear Equations')}
								class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
							/>
						</div>

						<div>
							<label
								for="shortDescription"
								class="block text-gray-800 dark:text-gray-200 font-medium mb-2"
							>
								{$i18n.t('Short Description')}
							</label>
							<textarea
								id="shortDescription"
								bind:value={shortDescription}
								placeholder={$i18n.t(
									'This support covers the basics of solving linear equations...'
								)}
								class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white h-24"
							></textarea>
						</div>

						<div>
							<label class="block text-gray-800 dark:text-gray-200 font-medium mb-4">
								{$i18n.t("Choose a subject you'd like to study")}
								<span class="text-red-500">*</span>
							</label>

							<div class="relative">
								<!-- Left arrow -->
								<button
									class="absolute left-0 top-1/2 transform -translate-y-1/2 -translate-x-6 p-2 sm:p-3 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-opacity min-w-[2.5rem] min-h-[2.5rem] flex items-center justify-center"
									style={subjectPageIndex === 0
										? 'opacity: 0.5; cursor: not-allowed;'
										: 'opacity: 1;'}
									on:click={prevSubjectPage}
									disabled={subjectPageIndex === 0}
								>
									<span class="sr-only">{$i18n.t('Previous subjects')}</span>
									&lt;
								</button>

								<!-- Subject cards -->
								<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
									{#each visibleSubjects as subject}
										<button
											class={`flex flex-col items-center justify-center p-4 sm:p-6 border rounded-md hover:shadow-md transition-all ${selectedSubject === subject.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-700'}`}
											on:click={() => (selectedSubject = subject.id)}
										>
											<span class="text-3xl sm:text-4xl mb-2">{subject.icon}</span>
											<span class="text-xs sm:text-sm text-gray-800 dark:text-gray-200"
												>{$i18n.t(subject.name)}</span
											>
										</button>
									{/each}
								</div>

								<!-- Right arrow -->
								<button
									class="absolute right-0 top-1/2 transform -translate-y-1/2 translate-x-6 p-2 sm:p-3 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-opacity min-w-[2.5rem] min-h-[2.5rem] flex items-center justify-center"
									style={subjectPageIndex >= totalSubjectPages - 1
										? 'opacity: 0.5; cursor: not-allowed;'
										: 'opacity: 1;'}
									on:click={nextSubjectPage}
									disabled={subjectPageIndex >= totalSubjectPages - 1}
								>
									<span class="sr-only">{$i18n.t('More subjects')}</span>
									&gt;
								</button>
							</div>
						</div>

						<div>
							<p class="text-gray-700 dark:text-gray-300 mb-2">
								{$i18n.t("Don't see your subject? you can create a custom one")}
							</p>
							<input
								type="text"
								bind:value={customSubject}
								placeholder={$i18n.t('Enter the subject you want to study')}
								class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
							/>
						</div>
					</div>
				{:else if currentStep === 1}
					<!-- Course step  -->
					<div class="space-y-6">
						<h3 class="text-xl font-medium text-gray-800 dark:text-gray-200">
							{$i18n.t('Select Your Base Course')}
						</h3>

						<div class="relative">
							<!-- Left arrow -->
							<button
								class="absolute left-0 top-1/2 transform -translate-y-1/2 -translate-x-6 p-1 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-opacity"
								style={coursePageIndex === 0 ? 'opacity: 0.5; cursor: not-allowed;' : 'opacity: 1;'}
								on:click={prevCoursePage}
								disabled={coursePageIndex === 0}
							>
								<span class="sr-only">{$i18n.t('Previous courses')}</span>
								&lt;
							</button>

							<!-- Course cards -->
							<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5 py-4">
								{#each visibleCourses as course}
									<div
										class={`rounded-lg shadow-md overflow-hidden transition-all ${selectedCourse === course.id ? 'border-2 border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border border-transparent bg-white dark:bg-gray-700'}`}
									>
										<!-- Course Image -->
										<div class="h-32 bg-gray-300 dark:bg-gray-600 relative">
											<!-- Placeholder image with gradient until real images are available -->
											<div
												class="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-500"
											></div>

											<!-- Instructor info -->
											<div class="absolute bottom-3 left-3 flex items-center">
												<div
													class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-500 flex items-center justify-center overflow-hidden border-2 border-white"
												>
													<!-- Placeholder avatar -->
													<span class="text-xs font-bold"
														>{course.instructor.name.substring(0, 2)}</span
													>
												</div>
												<span class="ml-2 text-xs text-white font-medium"
													>{course.instructor.name}</span
												>
											</div>
										</div>

										<!-- Course details -->
										<div class="p-4">
											<h4 class="text-gray-800 dark:text-gray-100 font-medium mb-2">
												{course.title}
											</h4>

											<div class="flex items-center justify-between mt-3">
												<span
													class={`text-xs px-2 py-1 rounded-full ${course.level === 'Beginner' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : course.level === 'Intermediate' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'}`}
												>
													{course.level}
												</span>

												<button
													class={`text-xs sm:text-sm px-3 sm:px-4 py-1.5 sm:py-2 rounded-md transition-colors ${selectedCourse === course.id ? 'bg-green-500 hover:bg-green-600' : 'bg-blue-500 hover:bg-blue-600'} text-white min-w-[4rem] sm:min-w-[5rem]`}
													on:click={() => (selectedCourse = course.id)}
												>
													{selectedCourse === course.id ? $i18n.t('Selected') : $i18n.t('Select')}
												</button>
											</div>
										</div>
									</div>
								{/each}
							</div>

							<!-- Right arrow -->
							<button
								class="absolute right-0 top-1/2 transform -translate-y-1/2 translate-x-6 p-1 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-opacity"
								style={coursePageIndex >= totalCoursePages - 1
									? 'opacity: 0.5; cursor: not-allowed;'
									: 'opacity: 1;'}
								on:click={nextCoursePage}
								disabled={coursePageIndex >= totalCoursePages - 1}
							>
								<span class="sr-only">{$i18n.t('More courses')}</span>
								&gt;
							</button>
						</div>

						<div class="mt-8">
							<h4 class="text-gray-700 dark:text-gray-300 mb-4">
								{$i18n.t('Or Attach Any course Materiel')}
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
						</div>
					</div>
				{:else if currentStep === 2}
					<!-- Objectives step -->
					<div class="space-y-6">
						<div>
							<div class="flex items-center justify-between mb-2">
								<label
									for="learningObjective"
									class="block text-gray-800 dark:text-gray-200 font-medium"
								>
									{$i18n.t("What do you want to explore today? Let's make learning fun!")}
								</label>
								<!-- Edit icon -->
								<button
									class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-5 w-5"
										viewBox="0 0 20 20"
										fill="#FFD700"
									>
										<path
											d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm4 10a1 1 0 011 1v1h1a1 1 0 110 2h-1v1a1 1 0 11-2 0v-1H7a1 1 0 110-2h1v-1a1 1 0 011-1zm7-10a1 1 0 01.707.293l.707.707L10 10.414 8.586 9l7.707-7.707a1 1 0 011.414 0z"
										/>
									</svg>
								</button>
							</div>
							<textarea
								id="learningObjective"
								bind:value={learningObjective}
								placeholder={$i18n.t('By the end of this support, I should be able to...')}
								class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white h-32"
							></textarea>
						</div>

						<div>
							<div class="flex items-center justify-between mb-4">
								<label class="block text-gray-800 dark:text-gray-200 font-medium">
									{$i18n.t('What Type of Learning is This?')}
								</label>
								<!-- Edit icon -->
								<button
									class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-5 w-5"
										viewBox="0 0 20 20"
										fill="#FFD700"
									>
										<path
											d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm4 10a1 1 0 011 1v1h1a1 1 0 110 2h-1v1a1 1 0 11-2 0v-1H7a1 1 0 110-2h1v-1a1 1 0 011-1zm7-10a1 1 0 01.707.293l.707.707L10 10.414 8.586 9l7.707-7.707a1 1 0 011.414 0z"
										/>
									</svg>
								</button>
							</div>

							<div class="flex flex-wrap gap-3">
								{#each learningTypes as type}
									<button
										class={`flex items-center px-5 py-2 rounded-full transition-colors ${selectedLearningType.includes(type.id) ? 'bg-blue-500 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}`}
										on:click={() => {
											if (selectedLearningType.includes(type.id)) {
												selectedLearningType = selectedLearningType.filter((id) => id !== type.id);
											} else {
												selectedLearningType = [...selectedLearningType, type.id];
											}
										}}
									>
										<span class="mr-2">{type.icon}</span>
										{$i18n.t(type.name)}
									</button>
								{/each}
							</div>
						</div>
					</div>
				{:else if currentStep === 3}
					<!-- Level step -->
					<div class="space-y-6">
						<h3 class="text-gray-800 dark:text-gray-200 font-medium">
							{$i18n.t('Choose the appropriate learning level for this support material')}
							<span class="text-red-500">*</span>
						</h3>

						<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
							{#each learningLevels as level}
								<button
									class={`flex items-center p-4 border rounded-lg transition-all ${selectedLevel === level.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-700'}`}
									on:click={() => (selectedLevel = level.id)}
								>
									<span
										class={`w-4 h-4 rounded-full mr-3 ${level.color === 'green' ? 'bg-green-500' : level.color === 'red' ? 'bg-red-500' : level.color === 'orange' ? 'bg-orange-500' : 'bg-yellow-500'}`}
									></span>
									<div class="text-left">
										<h4 class="font-medium text-gray-800 dark:text-gray-200">
											{$i18n.t(level.name)}
										</h4>
										<p class="text-sm text-gray-500 dark:text-gray-400">
											{$i18n.t(level.description)}
										</p>
									</div>
								</button>
							{/each}
						</div>
					</div>
				{:else if currentStep === 4}
					<!-- Details step -->
					<div class="space-y-6">
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
							<!-- Content Language -->
							<div>
								<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2">
									{$i18n.t('Content Language')}
								</label>
								<div class="relative">
									<select
										bind:value={contentLanguage}
										class="appearance-none w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white pr-8"
									>
										{#each languages as language}
											<option value={language}>{$i18n.t(language)}</option>
										{/each}
									</select>
								</div>
							</div>

							<!-- Estimated Duration -->
							<div>
								<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2">
									{$i18n.t('Estimated Duration')}
								</label>
								<div class="relative">
									<select
										bind:value={estimatedDuration}
										class="appearance-none w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white pr-8"
									>
										{#each durations as duration}
											<option value={duration}>{duration}</option>
										{/each}
									</select>
								</div>
							</div>

							<!-- Who Can Access -->
						</div>

						<!-- Keywords -->
						<div class="mt-4 sm:mt-6">
							<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2">
								{$i18n.t('Keywords (for search & recommendations)')}
							</label>
							<div class="flex flex-col sm:flex-row gap-2 sm:gap-0">
								<input
									type="text"
									bind:value={keywordInput}
									on:keydown={handleKeyDown}
									placeholder={$i18n.t('Add keywords...')}
									class="w-full sm:flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md sm:rounded-r-none focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white text-sm sm:text-base"
								/>
								<button
									on:click={addKeyword}
									class="w-full sm:w-auto px-4 py-3 bg-blue-500 text-white rounded-md sm:rounded-l-none hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors min-h-[44px] text-sm sm:text-base font-medium flex items-center justify-center"
								>
									<span class="hidden sm:inline">{$i18n.t('Add')}</span>
									<span class="sm:hidden">{$i18n.t('Add')}</span>
								</button>
							</div>

							<!-- Keywords display -->
							<div class="flex flex-wrap gap-2 mt-3">
								{#each keywords as keyword}
									<div
										class="bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-100 px-3 py-2 rounded-full text-sm flex items-center gap-2 hover:bg-blue-200 dark:hover:bg-blue-700 transition-colors"
									>
										{keyword}
										<button
											on:click={() => removeKeyword(keyword)}
											class="p-1 hover:bg-blue-200 dark:hover:bg-blue-600 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
											aria-label="Remove keyword"
										>
											<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
												<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
											</svg>
										</button>
									</div>
								{/each}
							</div>
						</div>

						<!-- Availability -->
						<div class="mt-4 sm:mt-6">
							<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2">
								{$i18n.t('Availability')}
							</label>
							<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
								<div class="relative">
									<input
										type="date"
										bind:value={startDate}
										placeholder={$i18n.t('Start Date')}
										class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
									/>
								</div>
								<div class="relative">
									<input
										type="date"
										bind:value={endDate}
										placeholder={$i18n.t('End Date')}
										class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
									/>
								</div>
							</div>
						</div>
					</div>
				{:else if currentStep === 5}
					<!-- Avatar step placeholder -->
					<div class="text-gray-800 dark:text-gray-200">
						<h3 class="text-xl font-semibold mb-4">{$i18n.t('Choose Your Avatar')}</h3>
						<p>{$i18n.t('This step would allow selecting a tutor avatar.')}</p>
					</div>
				{:else if currentStep === 6}
					<!-- Review step placeholder -->
					<div class="text-gray-800 dark:text-gray-200">
						<h3 class="text-xl font-semibold mb-4">{$i18n.t('Review Your Setup')}</h3>
						<p>{$i18n.t('This step would show a summary of all selections.')}</p>
					</div>
				{/if}
			</div>

			<!-- Navigation buttons -->
			<div class="flex justify-between mt-8">
				<button
					on:click={() => {
						if (currentStep === 0) {
							window.location.href = '/student/dashboard';
						} else {
							prevStep();
						}
					}}
					class="px-4 sm:px-6 py-2 sm:py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full hover:bg-gray-300 dark:hover:bg-gray-600 text-sm sm:text-base min-w-[5rem] sm:min-w-[6rem]"
				>
					{$i18n.t('Back')}
				</button>

				<button
					on:click={nextStep}
					class="px-4 sm:px-6 py-2 sm:py-2.5 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base min-w-[5rem] sm:min-w-[6rem]"
					disabled={!canProceed}
				>
					{currentStep === steps.length - 1 ? $i18n.t('Start') : $i18n.t('Next')}
				</button>
			</div>
		</div>
	{:else}
		<!-- Chat interface -->
		<h1 class="text-2xl font-bold text-gray-800 dark:text-white mb-4">
			{$i18n.t('Personalized Support')}
		</h1>
		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-0 h-[calc(100vh-12rem)] overflow-hidden"
		></div>
	{/if}
</div>
