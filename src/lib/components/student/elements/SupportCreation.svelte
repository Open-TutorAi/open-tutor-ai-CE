<!-- src/lib/components/student/elements/SupportCreation.svelte -->
<script lang="ts">
	import { getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { user } from '$lib/stores';
	import { createSupport, uploadSupportFile, updateSupportChatId } from '$lib/apis/supports';
	import { createNewChat } from '$lib/apis/chats';
	import { v4 as uuidv4 } from 'uuid';
	import type { Writable } from 'svelte/store';
	import { get } from 'svelte/store';
	import { settings, models as globalModelsStore, chatId as storeChatId } from '$lib/stores';
	import { onMount, afterUpdate, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { browser } from '$app/environment';

	// i18n
	interface I18n {
		t: (key: string) => string;
	}
	const i18n = getContext<Writable<I18n>>('i18n');

	// ------------------------------------------------------------
	// Logique de liaison de chat (originale, inchangée)
	// ------------------------------------------------------------
	let currentPath = '';
	let chatIdFromURL = '';
	let pendingSupportId = '';
	let chatIdSubscription: Function;
	let urlCheckInterval: ReturnType<typeof setInterval>;

	if (browser && !window.openTutorEvents) {
		window.openTutorEvents = new EventTarget();
	}

	onMount(async () => {
		if (browser) {
			console.log('SupportCreation component mounted');
			try {
				const pendingSupportData = localStorage.getItem('pendingSupportData');
				if (pendingSupportData) {
					const supportData = JSON.parse(pendingSupportData);
					const currentTime = Date.now();
					const supportTimestamp = supportData.timestamp || 0;
					const MAX_SUPPORT_AGE_MS = 30 * 60 * 1000;
					if (currentTime - supportTimestamp < MAX_SUPPORT_AGE_MS) {
						pendingSupportId = supportData.id || '';
					} else {
						localStorage.removeItem('pendingSupportData');
						pendingSupportId = '';
					}
				} else {
					pendingSupportId = '';
				}
			} catch (error) {
				console.error('Error parsing pendingSupportData:', error);
				localStorage.removeItem('pendingSupportData');
				pendingSupportId = '';
			}

			window.openTutorEvents.addEventListener('chatCreated', ((event: CustomEvent) => {
				const newChatId = event.detail?.chatId;
				if (newChatId && pendingSupportId) {
					updateSupportWithChatId(pendingSupportId, newChatId);
				}
			}) as EventListener);

			chatIdSubscription = storeChatId.subscribe((newChatId) => {
				if (newChatId && newChatId !== 'local' && pendingSupportId) {
					updateSupportWithChatId(pendingSupportId, newChatId);
				}
			});

			urlCheckInterval = setInterval(() => {
				try {
					const pendingSupportData = localStorage.getItem('pendingSupportData');
					if (!pendingSupportData) {
						clearInterval(urlCheckInterval);
						return;
					}
					const supportData = JSON.parse(pendingSupportData);
					const currentTime = Date.now();
					const supportTimestamp = supportData.timestamp || 0;
					const MAX_SUPPORT_AGE_MS = 30 * 60 * 1000;
					if (currentTime - supportTimestamp >= MAX_SUPPORT_AGE_MS) {
						localStorage.removeItem('pendingSupportData');
						clearInterval(urlCheckInterval);
						return;
					}
					const currentURL = window.location.pathname;
					if (currentURL.startsWith('/student/c/')) {
						const newChatId = currentURL.split('/student/c/')[1].split('/')[0];
						if (newChatId && supportData.id) {
							updateSupportWithChatId(supportData.id, newChatId);
						}
					}
				} catch (error) {
					localStorage.removeItem('pendingSupportData');
					clearInterval(urlCheckInterval);
				}
			}, 1000);
		}
	});

	onDestroy(() => {
		if (browser) {
			window.openTutorEvents.removeEventListener('chatCreated', (() => {}) as EventListener);
			if (chatIdSubscription) chatIdSubscription();
			if (urlCheckInterval) clearInterval(urlCheckInterval);
		}
	});

	$: if ($page && $page.url && browser) {
		currentPath = $page.url.pathname || '';
		if (currentPath.startsWith('/student/c/')) {
			chatIdFromURL = currentPath.replace('/student/c/', '').split('/')[0];
			if (chatIdFromURL && localStorage.getItem('pendingSupportData')) {
				try {
					const supportData = JSON.parse(localStorage.getItem('pendingSupportData') || '{}');
					const supportId = supportData.id;
					const currentTime = Date.now();
					const supportTimestamp = supportData.timestamp || 0;
					const MAX_SUPPORT_AGE_MS = 30 * 60 * 1000;
					if (supportId && currentTime - supportTimestamp < MAX_SUPPORT_AGE_MS) {
						updateSupportWithChatId(supportId, chatIdFromURL);
					} else if (currentTime - supportTimestamp >= MAX_SUPPORT_AGE_MS) {
						localStorage.removeItem('pendingSupportData');
					}
				} catch (error) {
					localStorage.removeItem('pendingSupportData');
				}
			}
		}
	}

	async function updateSupportWithChatId(supportId: string, chatId: string) {
		if (!supportId || !chatId || !browser || chatId === 'local' || chatId === 'undefined') return;
		let pendingSupportData;
		try {
			pendingSupportData = localStorage.getItem('pendingSupportData');
			if (!pendingSupportData) return;
			const supportData = JSON.parse(pendingSupportData);
			if (supportData.id !== supportId) return;
			const currentTime = Date.now();
			const supportTimestamp = supportData.timestamp || 0;
			const MAX_SUPPORT_AGE_MS = 30 * 60 * 1000;
			if (currentTime - supportTimestamp >= MAX_SUPPORT_AGE_MS) {
				localStorage.removeItem('pendingSupportData');
				return;
			}
		} catch (error) {
			localStorage.removeItem('pendingSupportData');
			return;
		}
		try {
			const token = localStorage.getItem('token');
			if (!token) return;
			await updateSupportChatId(token, supportId, chatId);
			localStorage.removeItem('pendingSupportData');
			pendingSupportId = '';
		} catch (error) {
			console.error("Failed to update support with chat ID:", error);
			try {
				const supportData = JSON.parse(pendingSupportData || '{}');
				const attemptCount = (supportData.attempts || 0) + 1;
				if (attemptCount >= 3) {
					localStorage.removeItem('pendingSupportData');
				} else {
					supportData.attempts = attemptCount;
					localStorage.setItem('pendingSupportData', JSON.stringify(supportData));
				}
			} catch (parseError) {
				localStorage.removeItem('pendingSupportData');
			}
		}
	}

	// ------------------------------------------------------------
	// Données du formulaire
	// ------------------------------------------------------------
	const steps = ['Subject', 'Course', 'Objectives', 'Level', 'Details', 'Avatar', 'Review'];
	let currentStep = 0;
	let isSubmitting = false;

	let supportTitle = '';
	let shortDescription = '';
	let selectedSubject = '';
	let customSubject = '';
	let uploadedFiles: File[] = [];

	let learningObjective = '';
	let selectedLearningType: string | null = null;
	const learningTypes = [
		{ id: 'exam', name: 'I\'m preparing for an exam', icon: '📝' },
		{ id: 'course', name: 'I\'m reviewing a course', icon: '📚' },
		{ id: 'skill', name: 'I want to build a new skill', icon: '🚀' }
	];

	let selectedLevel = '';
	const learningLevels = [
		{ id: 'primary', name: 'Primary school', description: 'Foundational learning for young minds', color: 'green' },
		{ id: 'middle', name: 'Middle school', description: 'Building critical thinking', color: 'yellow' },
		{ id: 'high', name: 'High school', description: 'Preparing students for advanced studies', color: 'orange' },
		{ id: 'university', name: 'University', description: 'Expert-level guidance', color: 'red' }
	];

	let contentLanguage = 'English';
	let estimatedDuration = '30min';
	let accessType = 'Private';
	let keywords: string[] = [];
	let keywordInput = '';
	let startDate = '';
	let endDate = '';

	const languages = ['English', 'French', 'Arabic', 'Spanish', 'German'];
	const durations = ['15min', '30min', '45min', '1h', '1h30min', '2h'];
	const accessTypes = ['Private', 'Public', 'Shared'];

	function addKeyword() {
		const keyword = keywordInput.trim();
		if (keyword && !keywords.includes(keyword)) {
			keywords = [...keywords, keyword];
			keywordInput = '';
		}
	}
	function removeKeyword(keyword: string) {
		keywords = keywords.filter(k => k !== keyword);
	}
	function handleKeyDown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			event.preventDefault();
			addKeyword();
		}
	}

	const subjects = [
		{ id: 'Mathematics', name: 'Mathematics', icon: '📊' },
		{ id: 'Science', name: 'Science', icon: '🔬' },
		{ id: 'History', name: 'History', icon: '🏛️' },
		{ id: 'Computer-science', name: 'Computer Science', icon: '💻' },
		{ id: 'English', name: 'English', icon: '📚' },
		{ id: 'Geography', name: 'Geography', icon: '🌍' },
		{ id: 'Chemistry', name: 'Chemistry', icon: '🔬' },
		{ id: 'Biology', name: 'Biology', icon: '🌿' },
		{ id: 'Physics', name: 'Physics', icon: '⚛️' },
		{ id: 'Other', name: 'Other', icon: '❓' }
	];

	let subjectPageIndex = 0;
	const subjectsPerPage = 4;
	$: totalSubjectPages = Math.ceil(subjects.length / subjectsPerPage);
	$: visibleSubjects = subjects.slice(subjectPageIndex * subjectsPerPage, (subjectPageIndex + 1) * subjectsPerPage);
	function prevSubjectPage() { if (subjectPageIndex > 0) subjectPageIndex--; }
	function nextSubjectPage() { if (subjectPageIndex < totalSubjectPages - 1) subjectPageIndex++; }

	function handleFileChange(event: Event) {
		const files = (event.target as HTMLInputElement).files;
		if (files && files.length) uploadedFiles = Array.from(files);
	}
	function handleFileDrop(event: DragEvent) {
		event.preventDefault();
		if (event.dataTransfer?.files) uploadedFiles = Array.from(event.dataTransfer.files);
	}
	function preventDefaults(event: Event) {
		event.preventDefault();
		event.stopPropagation();
	}

	async function saveSupportToDatabase() {
		const token = localStorage.getItem('token');
		if (!token) {
			toast.error($i18n.t('You must be logged in to create a support request'));
			return;
		}
		isSubmitting = true;
		try {
			const supportDetails = {
				title: supportTitle,
				short_description: shortDescription || undefined,
				subject: selectedSubject || customSubject,
				custom_subject: customSubject || undefined,
				learning_objective: learningObjective || undefined,
				learning_type: selectedLearningType || undefined,
				level: selectedLevel || undefined,
				content_language: contentLanguage || undefined,
				estimated_duration: estimatedDuration || undefined,
				access_type: accessType || undefined,
				keywords: keywords.length ? keywords : undefined,
				start_date: startDate || undefined,
				end_date: endDate || undefined,
				avatar_id: undefined
			};
			const supportResponse = await createSupport(token, supportDetails);
			if (supportResponse && supportResponse.id) {
				localStorage.removeItem('pendingSupportData');
				const supportData = { id: supportResponse.id, timestamp: Date.now(), attempts: 0 };
				localStorage.setItem('pendingSupportData', JSON.stringify(supportData));
				pendingSupportId = supportResponse.id;
				toast.success($i18n.t('Support created successfully!'));
				if (uploadedFiles.length) {
					for (const file of uploadedFiles) {
						await uploadSupportFile(token, supportResponse.id, file);
					}
					toast.success($i18n.t(`Uploaded ${uploadedFiles.length} file(s)`));
				}
				storeChatId.set('');
				goto('/student/chat');
			} else {
				toast.error($i18n.t('Failed to save support request.'));
			}
		} catch (error: any) {
			toast.error(`${$i18n.t('An error occurred')}: ${error?.message}`);
		} finally {
			isSubmitting = false;
		}
	}

	function nextStep() {
		if (currentStep < steps.length - 1) currentStep++;
		else saveSupportToDatabase();
	}
	function prevStep() {
		if (currentStep > 0) currentStep--;
	}

	$: isTitleValid = supportTitle.trim().length > 0;
	$: isSubjectSelected = selectedSubject || customSubject.trim().length > 0;
	$: isLearningTypeSelected = selectedLearningType !== null;
	$: isLevelSelected = selectedLevel.trim().length > 0;
	$: canProceed =
		currentStep === 0 ? isTitleValid && isSubjectSelected :
		currentStep === 1 ? true :
		currentStep === 2 ? isLearningTypeSelected :
		currentStep === 3 ? isLevelSelected : true;

	let showChatInterface = false;
</script>

<div class="bg-gray-50 dark:bg-gray-900 min-h-screen px-4 py-8">
	<div class="max-w-4xl mx-auto">
		{#if !showChatInterface}
			<!-- Stepper (inchangé) -->
			<div class="mb-8">
				<ol class="flex items-center w-full">
					{#each steps as step, index}
						<li class={`flex items-center ${index < steps.length - 1 ? 'w-full' : ''}`}>
							<div class="relative flex items-center justify-center w-10 h-10 rounded-full transition-all duration-500 shrink-0 border-2 step-circle cursor-pointer"
								class:bg-blue-600={currentStep >= index}
								class:border-blue-600={currentStep >= index}
								class:text-white={currentStep >= index}
								class:bg-white={currentStep < index}
								class:border-gray-300={currentStep < index}
								class:dark:bg-gray-700={currentStep < index}
								class:scale-110={currentStep === index}
								on:click={() => { if (index <= currentStep) currentStep = index; }}>
								{#if currentStep > index}
									<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
									</svg>
								{:else}
									<span>{index + 1}</span>
								{/if}
								<div class="absolute -bottom-7 w-max text-center">
									<span class="text-sm font-medium transition-all duration-500 cursor-pointer step-name"
										class:text-blue-600={currentStep >= index}
										class:text-gray-500={currentStep < index}>{$i18n.t(step)}</span>
								</div>
							</div>
							{#if index < steps.length - 1}
								<div class="w-full h-0.5 mx-2 sm:mx-4 bg-gray-300 dark:bg-gray-600"></div>
							{/if}
						</li>
					{/each}
				</ol>
			</div>

			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 sm:p-8">
				<!-- Étape 0 : Informations de base -->
				{#if currentStep === 0}
					<div class="space-y-8">
						<div>
							<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">{$i18n.t('Tell us about your learning needs')}</h3>
							<div class="mb-6">
								<label for="supportTitle" class="block text-gray-700 dark:text-gray-200 font-medium mb-2 text-sm" title="Ex: 'Understanding Python loops' – be specific">
									{$i18n.t('Title')} <span class="text-red-500 ml-1">*</span>
								</label>
								<input id="supportTitle" type="text" bind:value={supportTitle}
									placeholder={$i18n.t('Enter a title for your support')}
									class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700" />
								<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Choose a clear, descriptive title that reflects your learning goal')}</p>
							</div>
							<div class="mb-8">
								<label for="shortDescription" class="block text-gray-700 dark:text-gray-200 font-medium mb-2 text-sm" title="Describe what you want to learn, not what you already know">
									{$i18n.t('Short Description')}
								</label>
								<textarea id="shortDescription" bind:value={shortDescription}
									placeholder={$i18n.t('Briefly describe what you want to learn...')}
									class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 h-24 resize-none"></textarea>
								<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{$i18n.t('A brief overview helps us tailor the learning experience to your needs')}</p>
							</div>
						</div>
						<div class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700">
							<label class="block text-gray-800 dark:text-gray-200 font-medium mb-4 text-sm" title="Select the subject you want to study">
								{$i18n.t("Choose a subject you'd like to study")} <span class="text-red-500 ml-1">*</span>
							</label>
							<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
								{#each visibleSubjects as subject}
									<button
										title="Click to select this subject"
										class={`flex flex-col items-center justify-center p-4 sm:p-5 border-2 rounded-lg hover:shadow-md transition-all ${
											selectedSubject === subject.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-700'
										}`}
										on:click={() => selectedSubject = subject.id}>
										<span class="text-3xl sm:text-4xl mb-3">{subject.icon}</span>
										<span class="text-sm font-medium text-gray-800 dark:text-gray-200">{$i18n.t(subject.name)}</span>
									</button>
								{/each}
							</div>
							<div class="flex justify-center mt-5 gap-2">
								<button title="Previous page of subjects" on:click={prevSubjectPage} disabled={subjectPageIndex === 0}
									class="p-2 rounded-full bg-white dark:bg-gray-700 shadow-sm border border-gray-200 dark:border-gray-600 disabled:opacity-50">←</button>
								<span class="text-sm text-gray-600 dark:text-gray-400">{subjectPageIndex + 1} / {totalSubjectPages}</span>
								<button title="Next page of subjects" on:click={nextSubjectPage} disabled={subjectPageIndex >= totalSubjectPages - 1}
									class="p-2 rounded-full bg-white dark:bg-gray-700 shadow-sm border border-gray-200 dark:border-gray-600 disabled:opacity-50">→</button>
							</div>
							<div class="mt-5">
								<p class="text-gray-700 dark:text-gray-300 text-sm mb-2">{$i18n.t("Don't see your subject? Create a custom one")}</p>
								<input type="text" bind:value={customSubject} placeholder={$i18n.t('Enter your custom subject')}
									title="If your subject is not listed, enter it here"
									class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700" />
							</div>
						</div>
					</div>

				<!-- Étape 1 : Documents -->
				{:else if currentStep === 1}
					<div class="space-y-6">
						<h3 class="text-xl font-medium text-gray-800 dark:text-gray-200">{$i18n.t('Course Materials')}</h3>
						<div>
							<h4 class="text-gray-700 dark:text-gray-300 mb-6">{$i18n.t('Attach Course Materials')}</h4>
							<div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50"
								title="Drop your files here (PDF, DOCX, PPTX, MP4 – max 50MB)"
								on:click={() => document.getElementById('file-upload')?.click()}
								on:dragover={preventDefaults}
								on:dragenter={preventDefaults}
								on:drop={handleFileDrop}>
								<input type="file" id="file-upload" class="hidden" multiple on:change={handleFileChange} accept=".pdf,.doc,.docx,.pptx,.mp4" />
								<div class="flex flex-col items-center">
									<svg class="h-12 w-12 text-blue-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
									</svg>
									<p class="text-gray-600 dark:text-gray-300 mb-1">{$i18n.t('Click to upload or drag and drop files')}</p>
									<p class="text-gray-500 dark:text-gray-400 text-xs">{$i18n.t('PDF, DOCX, PPTX, MP4 (max 50MB)')}</p>
									{#if uploadedFiles.length > 0}
										<div class="mt-4 p-2 bg-blue-50 dark:bg-blue-900/20 rounded w-full max-w-md">
											<p class="text-sm text-blue-700 dark:text-blue-300 font-medium">{uploadedFiles.length} {$i18n.t('file(s) selected')}</p>
										</div>
									{/if}
								</div>
							</div>
							<p class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Upload your course materials to get personalized learning assistance')}</p>
						</div>
					</div>

				<!-- Étape 2 : Objectifs d'apprentissage -->
				{:else if currentStep === 2}
					<div class="space-y-8">
						<div>
							<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">{$i18n.t('Define your learning objectives')}</h3>
							<div class="mb-8 bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700">
								<div class="flex items-center justify-between mb-3">
									<label for="learningObjective" class="block text-gray-700 dark:text-gray-200 font-medium text-sm" title="What specific outcome do you want?">
										{$i18n.t("What do you want to explore today?")}
									</label>
									<button class="p-2 rounded-full bg-yellow-100 dark:bg-yellow-900 text-yellow-600 dark:text-yellow-300 hover:bg-yellow-200" title="AI can help you craft personalized learning objectives">✨</button>
								</div>
								<p class="text-sm text-gray-600 dark:text-gray-400 mb-2">{$i18n.t('Be specific about what you hope to achieve by the end of this support')}</p>
								<textarea id="learningObjective" bind:value={learningObjective}
									placeholder={$i18n.t('By the end of this support, I should be able to...')}
									title="Example: 'I will be able to sort a list using merge sort'"
									class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 h-32 resize-none"></textarea>
							</div>
							<div class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700">
								<div class="mb-4">
									<label class="block text-gray-700 dark:text-gray-200 font-medium text-sm" title="Choose the main reason for your support request">
										{$i18n.t('How can I support you today?')} <span class="text-red-500 ml-1">*</span>
									</label>
									<p class="text-sm text-gray-600 dark:text-gray-400 mt-1 mb-4">{$i18n.t('Select the option that best describes your learning goal')}</p>
								</div>
								<div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
									{#each learningTypes as type}
										<button title={type.id === 'exam' ? 'Prepare for an exam' : type.id === 'course' ? 'Review a course' : 'Learn a new skill from scratch'}
											class={`flex items-center p-4 rounded-lg border-2 transition-all ${
												selectedLearningType === type.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-700'
											}`}
											on:click={() => selectedLearningType = selectedLearningType === type.id ? null : type.id}>
											<span class="text-2xl mr-3">{type.icon}</span>
											<span class="text-sm font-medium text-gray-800 dark:text-gray-200">{$i18n.t(type.name)}</span>
										</button>
									{/each}
								</div>
							</div>
						</div>
					</div>

				<!-- Étape 3 : Niveau -->
				{:else if currentStep === 3}
					<div class="space-y-8">
						<div>
							<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">{$i18n.t('Choose your learning level')}</h3>
							<p class="text-gray-600 dark:text-gray-400 mb-6">{$i18n.t('Select the appropriate learning level for this material to ensure the content matches your needs')} <span class="text-red-500 ml-1">*</span></p>
							<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
								{#each learningLevels as level}
									<button title={level.description}
										class={`flex items-start p-5 border-2 rounded-lg transition-all ${
											selectedLevel === level.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-700'
										}`}
										on:click={() => selectedLevel = level.id}>
										<div class="flex items-center">
											<div class="w-12 h-12 rounded-full flex items-center justify-center mr-4 bg-gray-100 dark:bg-gray-600">📚</div>
											<div class="text-left">
												<h4 class="font-medium text-gray-800 dark:text-gray-200 text-lg mb-1">{$i18n.t(level.name)}</h4>
												<p class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t(level.description)}</p>
											</div>
										</div>
									</button>
								{/each}
							</div>
						</div>
					</div>

				<!-- Étape 4 : Détails -->
				{:else if currentStep === 4}
					<div class="space-y-8">
						<div>
							<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">{$i18n.t('Fine-tune your learning experience')}</h3>
							<p class="text-gray-600 dark:text-gray-400 mb-8">{$i18n.t('These additional details help us personalize your support experience')}</p>
							<div class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700 mb-8">
								<div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
									<div>
										<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2 text-sm" title="Language in which you want the content delivered">{$i18n.t('Content Language')}</label>
										<select bind:value={contentLanguage} class="w-full px-4 py-3 border rounded-lg bg-white dark:bg-gray-700">
											{#each languages as l}<option>{l}</option>{/each}
										</select>
										<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Select the language you want your content delivered in')}</p>
									</div>
									<div>
										<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2 text-sm" title="How long you expect to spend on this support">{$i18n.t('Estimated Duration')}</label>
										<select bind:value={estimatedDuration} class="w-full px-4 py-3 border rounded-lg bg-white dark:bg-gray-700">
											{#each durations as d}<option>{d}</option>{/each}
										</select>
										<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{$i18n.t('How long do you expect to spend on this support?')}</p>
									</div>
								</div>
							</div>

							<div class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700 mb-8">
								<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2 text-sm" title="Add keywords like 'python', 'exam', 'algorithms' for better search">{$i18n.t('Keywords (for search & recommendations)')}</label>
								<p class="mb-4 text-sm text-gray-600 dark:text-gray-400">{$i18n.t('Add relevant keywords to help find this support later')}</p>
								<div class="flex flex-col sm:flex-row gap-2 sm:gap-0">
									<input type="text" bind:value={keywordInput} on:keydown={handleKeyDown}
										placeholder={$i18n.t('Add keywords...')}
										title="Add keywords like 'python', 'exam', 'algorithms' for better search"
										class="w-full sm:flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg sm:rounded-r-none focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700" />
									<button on:click={addKeyword} title="Add this keyword"
										class="w-full sm:w-auto px-4 py-3 bg-blue-500 text-white rounded-lg sm:rounded-l-none hover:bg-blue-600">{$i18n.t('Add')}</button>
								</div>
								{#if keywords.length > 0}
									<div class="flex flex-wrap gap-2 mt-4 p-3 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
										{#each keywords as kw}
											<span class="bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-100 px-3 py-1.5 rounded-full text-sm flex items-center gap-2">
												{kw}
												<button on:click={() => removeKeyword(kw)} title="Remove this keyword" class="hover:text-red-600">✕</button>
											</span>
										{/each}
									</div>
								{:else}
									<div class="mt-4 p-3 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 text-sm text-gray-500 italic">{$i18n.t('No keywords added yet')}</div>
								{/if}
							</div>

							<div class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700">
								<label class="block text-gray-800 dark:text-gray-200 font-medium mb-2 text-sm" title="Set when this support should be available (optional)">{$i18n.t('Availability')}</label>
								<p class="mb-4 text-sm text-gray-600 dark:text-gray-400">{$i18n.t('Set when this support should be available (optional)')}</p>
								<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
									<div>
										<label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">{$i18n.t('Start Date')}</label>
										<input type="date" bind:value={startDate} title="Date from which the support will be available"
											class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700" />
									</div>
									<div>
										<label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">{$i18n.t('End Date')}</label>
										<input type="date" bind:value={endDate} title="Date when the support will no longer be available"
											class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700" />
									</div>
								</div>
							</div>
						</div>
					</div>

				<!-- Étape 5 : Avatar (placeholder) -->
				{:else if currentStep === 5}
					<div class="space-y-6 step-content-enter">
						<div class="text-gray-800 dark:text-gray-200">
							<h3 class="text-xl font-semibold mb-4">{$i18n.t('Choose Your Avatar')}</h3>
							<p>{$i18n.t('This step would allow selecting a tutor avatar.')}</p>
						</div>
					</div>

				<!-- Étape 6 : Revue -->
				{:else if currentStep === 6}
					<div class="space-y-8">
						<div>
							<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">{$i18n.t('Review your support')}</h3>
							<p class="text-gray-600 dark:text-gray-400 mb-8">{$i18n.t('Verify all details before creating your support')}</p>
							<div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden border border-gray-200 dark:border-gray-700">
								<div class="bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-5 flex items-center justify-between">
									<div class="flex-1">
										<h4 class="text-lg font-bold text-white">{supportTitle || $i18n.t('Untitled')}</h4>
										{#if selectedSubject}
											<div class="flex items-center mt-2">
												<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-white/20 text-white">
													{selectedSubject ? subjects.find(s => s.id === selectedSubject)?.name || customSubject : customSubject}
												</span>
											</div>
										{/if}
									</div>
								</div>
								<div class="p-0">
									<div class="px-6 py-5 border-b border-gray-200 dark:border-gray-700 grid grid-cols-1 md:grid-cols-2 gap-6">
										<div class="space-y-5">
											{#if shortDescription}
												<div>
													<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">{$i18n.t('Description')}</h5>
													<p class="text-gray-800 dark:text-gray-200">{shortDescription}</p>
												</div>
											{/if}
											{#if learningObjective}
												<div>
													<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">{$i18n.t('Learning Objectives')}</h5>
													<p class="text-gray-800 dark:text-gray-200">{learningObjective}</p>
												</div>
											{/if}
										</div>
										<div class="space-y-5">
											<div>
												<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">{$i18n.t('Learning Type')}</h5>
												{#if selectedLearningType}
													<div class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-200">
														{learningTypes.find(lt => lt.id === selectedLearningType)?.name || selectedLearningType}
													</div>
												{:else}
													<p class="text-gray-400 dark:text-gray-500 italic text-sm">Not specified</p>
												{/if}
											</div>
											<div>
												<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">{$i18n.t('Learning Level')}</h5>
												{#if selectedLevel}
													<div class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200">
														{learningLevels.find(ll => ll.id === selectedLevel)?.name || selectedLevel}
													</div>
												{:else}
													<p class="text-gray-400 dark:text-gray-500 italic text-sm">Not specified</p>
												{/if}
											</div>
											<div>
												<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">{$i18n.t('Content Details')}</h5>
												<div class="flex items-center text-gray-700 dark:text-gray-300 space-x-4">
													<div class="flex items-center"><span class="text-sm">{contentLanguage}</span></div>
													<div class="flex items-center"><span class="text-sm">{estimatedDuration}</span></div>
												</div>
											</div>
										</div>
									</div>
									{#if keywords.length > 0 || (uploadedFiles && uploadedFiles.length > 0) || startDate || endDate}
										<div class="px-6 py-5 border-b border-gray-200 dark:border-gray-700">
											{#if keywords.length > 0}
												<div class="mb-4">
													<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">{$i18n.t('Keywords')}</h5>
													<div class="flex flex-wrap gap-2">
														{#each keywords as kw}
															<span class="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200">{kw}</span>
														{/each}
													</div>
												</div>
											{/if}
											{#if uploadedFiles && uploadedFiles.length > 0}
												<div class="mb-4">
													<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">{$i18n.t('Uploaded Files')}</h5>
													<ul class="space-y-1.5">
														{#each uploadedFiles as file}
															<li class="flex items-center text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700/50 px-3 py-2 rounded-md">
																<span class="text-sm truncate">{file.name}</span>
															</li>
														{/each}
													</ul>
												</div>
											{/if}
											{#if startDate || endDate}
												<div>
													<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">{$i18n.t('Availability')}</h5>
													<div class="flex items-center gap-4">
														{#if startDate}
															<div class="flex items-center text-gray-700 dark:text-gray-300">
																<span class="text-sm">{$i18n.t('From')}: {startDate}</span>
															</div>
														{/if}
														{#if endDate}
															<div class="flex items-center text-gray-700 dark:text-gray-300">
																<span class="text-sm">{$i18n.t('To')}: {endDate}</span>
															</div>
														{/if}
													</div>
												</div>
											{/if}
										</div>
									{/if}
									<div class="px-6 py-5 bg-gray-50 dark:bg-gray-750">
										<div class="flex items-center text-gray-700 dark:text-gray-300">
											<p class="text-sm">{$i18n.t('Click "Start Learning" below to create your support and begin your personalized learning experience.')}</p>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				{/if}

				<!-- Boutons de navigation -->
				<div class="flex justify-between mt-10 pt-6 border-t border-gray-100 dark:border-gray-700">
					<button on:click={() => currentStep === 0 ? goto('/student/dashboard') : prevStep()}
						title="Go back to previous step or cancel"
						class="px-6 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 flex items-center"
						disabled={isSubmitting}>
						← {currentStep === 0 ? $i18n.t('Cancel') : $i18n.t('Back')}
					</button>
					<button on:click={nextStep}
						title={currentStep === steps.length - 1 ? 'Create support and start learning' : 'Proceed to next step'}
						class="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
						disabled={!canProceed || isSubmitting}>
						{#if isSubmitting}
							<span class="animate-spin">⏳</span> {$i18n.t('Processing...')}
						{:else}
							{currentStep === steps.length - 1 ? $i18n.t('Start Learning') : $i18n.t('Continue')} →
						{/if}
					</button>
				</div>
			</div>
		{:else}
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
				<div class="mb-6 flex justify-center">
					<div class="w-20 h-20 rounded-full bg-green-100 dark:bg-green-800 flex items-center justify-center">✓</div>
				</div>
				<h2 class="text-2xl font-bold mb-3">{$i18n.t('Support Created!')}</h2>
				<p class="text-gray-600 dark:text-gray-300 mb-8 max-w-md mx-auto">{$i18n.t('Your support has been successfully created. Get ready for a personalized learning experience!')}</p>
				<button on:click={() => goto('/student/dashboard')} class="px-8 py-3 bg-blue-600 text-white rounded-lg">{$i18n.t('Return to Dashboard')}</button>
			</div>
		{/if}
	</div>
</div>

<style>
  .step-circle { transition: all 0.3s ease; }
  .step-circle:hover { transform: scale(1.05); }
  .step-name { transition: all 0.3s ease; }
  .step-name:hover { transform: scale(1.05); }
</style>