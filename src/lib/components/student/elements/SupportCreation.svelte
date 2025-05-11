<!-- student/support/+page.svelte -->
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

	// Get i18n from context with proper typing 
	interface I18n {
		t: (key: string) => string;
	}
	const i18n = getContext<Writable<I18n>>('i18n');

	// For checking chat ID creation
	let currentPath = '';
	let chatIdFromURL = '';
	let pendingSupportId = '';
	let chatIdSubscription: Function;
	let urlCheckInterval: ReturnType<typeof setInterval>; 

	// Create a global event handler for chat creation that can be triggered from any component
	if (browser && !window.openTutorEvents) {
		window.openTutorEvents = new EventTarget();
	}

	// Check for chat creation and URL changes
	onMount(() => {
		if (browser) {
			console.log('SupportCreation component mounted');
			// Get any pending support ID from localStorage with timestamp validation
			try {
				const pendingSupportData = localStorage.getItem('pendingSupportData');
				if (pendingSupportData) {
					const supportData = JSON.parse(pendingSupportData);
					
					// Check if the support request is not expired (30 minutes max)
					const currentTime = Date.now();
					const supportTimestamp = supportData.timestamp || 0;
					const MAX_SUPPORT_AGE_MS = 30 * 60 * 1000; // 30 minutes
					
					if (currentTime - supportTimestamp < MAX_SUPPORT_AGE_MS) {
						pendingSupportId = supportData.id || '';
						console.log('Found valid pendingSupportId:', pendingSupportId, 'created', 
							Math.round((currentTime - supportTimestamp)/1000), 'seconds ago');
					} else {
						// Support request too old - clear it and ignore
						console.log('Clearing expired pendingSupportId (older than 30 minutes)');
						localStorage.removeItem('pendingSupportData');
						pendingSupportId = '';
					}
				} else {
					pendingSupportId = '';
				}
			} catch (error) {
				// If any parsing error occurs, reset the state
				console.error('Error parsing pendingSupportData:', error);
				localStorage.removeItem('pendingSupportData');
				pendingSupportId = '';
			}
			
			// Add global event listener for chat creation
			window.openTutorEvents.addEventListener('chatCreated', ((event: CustomEvent) => {
				const newChatId = event.detail?.chatId;
				const timestamp = event.detail?.timestamp;
				console.log('Received chatCreated event with chatId:', newChatId, 'timestamp:', timestamp);
				
				if (newChatId && pendingSupportId) {
					console.log('Immediately updating support with new chat ID from event');
					updateSupportWithChatId(pendingSupportId, newChatId);
				}
			}) as EventListener);
			
			// Subscribe to the chatId store as a backup
			chatIdSubscription = storeChatId.subscribe((newChatId) => {
				console.log('Chat ID store changed:', newChatId);
				if (newChatId && newChatId !== 'local' && pendingSupportId) {
					console.log('Detected chat ID change from store:', newChatId);
					updateSupportWithChatId(pendingSupportId, newChatId);
				}
			});
			
			// Set up monitoring for URL changes as another backup
			urlCheckInterval = setInterval(() => {
				// Check if there's still a pending support to process
				try {
					const pendingSupportData = localStorage.getItem('pendingSupportData');
					if (!pendingSupportData) {
						console.log('No pending support data, clearing URL check interval');
						clearInterval(urlCheckInterval);
						return;
					}
					
					// Check for expiration
					const supportData = JSON.parse(pendingSupportData);
					const currentTime = Date.now();
					const supportTimestamp = supportData.timestamp || 0;
					const MAX_SUPPORT_AGE_MS = 30 * 60 * 1000; // 30 minutes
					
					if (currentTime - supportTimestamp >= MAX_SUPPORT_AGE_MS) {
						console.log('Support request expired during URL check, clearing');
						localStorage.removeItem('pendingSupportData');
						clearInterval(urlCheckInterval);
						return;
					}
					
					// Check for URL changes indicating chat creation
					const currentURL = window.location.pathname;
					if (currentURL.startsWith('/student/c/')) {
						const newChatId = currentURL.split('/student/c/')[1].split('/')[0];
						if (newChatId && supportData.id) {
							console.log('Detected chat URL change to:', newChatId);
							updateSupportWithChatId(supportData.id, newChatId);
						}
					}
				} catch (error) {
					console.error('Error in URL check interval:', error);
					// On any error, clear the data and interval
					localStorage.removeItem('pendingSupportData');
					clearInterval(urlCheckInterval);
				}
			}, 1000);
		}
	});

	// Clean up listeners on component destruction
	onDestroy(() => {
		console.log('SupportCreation component destroyed');
		if (browser) {
			// Remove global event listener
			window.openTutorEvents.removeEventListener('chatCreated', ((event: CustomEvent) => {
				// This is just for cleanup, the actual handler is defined in onMount
			}) as EventListener);
			
			if (chatIdSubscription) {
				chatIdSubscription();
				console.log('Chat ID subscription removed');
			}
			
			if (urlCheckInterval) {
				clearInterval(urlCheckInterval);
				console.log('URL check interval cleared');
			}
		}
	});

	// Subscribe to page changes as an additional detection method
	$: if ($page && $page.url && browser) {
		currentPath = $page.url.pathname || '';
		
		// Check for chat creation
		if (currentPath.startsWith('/student/c/')) {
			chatIdFromURL = currentPath.replace('/student/c/', '').split('/')[0];
			
			// Only proceed if we have a valid ID and there's a pending support
			if (chatIdFromURL && localStorage.getItem('pendingSupportData')) {
				try {
					const supportData = JSON.parse(localStorage.getItem('pendingSupportData') || '{}');
					const supportId = supportData.id;
					
					// Validate support hasn't expired
					const currentTime = Date.now();
					const supportTimestamp = supportData.timestamp || 0;
					const MAX_SUPPORT_AGE_MS = 30 * 60 * 1000; // 30 minutes
					
					if (supportId && currentTime - supportTimestamp < MAX_SUPPORT_AGE_MS) {
						console.log('Detected chat page navigation:', chatIdFromURL);
						updateSupportWithChatId(supportId, chatIdFromURL);
					} else if (currentTime - supportTimestamp >= MAX_SUPPORT_AGE_MS) {
						// Support too old, clear it
						console.log('Support expired during page navigation, clearing');
						localStorage.removeItem('pendingSupportData');
					}
				} catch (error) {
					console.error('Error handling page navigation:', error);
					localStorage.removeItem('pendingSupportData');
				}
			}
		}
	}

	// Function to update a support with a chat ID
	async function updateSupportWithChatId(supportId: string, chatId: string) {
		// Only update once and validate inputs
		if (!supportId || !chatId || !browser || chatId === 'local' || chatId === 'undefined') {
			console.log('Invalid inputs for updateSupportWithChatId:', { supportId, chatId });
			return;
		}
		
		// Make sure we haven't already processed this
		let pendingSupportData;
		try {
			pendingSupportData = localStorage.getItem('pendingSupportData');
			if (!pendingSupportData) {
				console.log('No pending support data found in localStorage, update already completed');
				return;
			}
			
			const supportData = JSON.parse(pendingSupportData);
			
			// Only process if the pending ID matches our input ID
			if (supportData.id !== supportId) {
				console.log('Support ID mismatch:', { 
					pendingId: supportData.id, 
					providedId: supportId 
				});
				return;
			}
			
			// Check if support request is too old
			const currentTime = Date.now();
			const supportTimestamp = supportData.timestamp || 0;
			const MAX_SUPPORT_AGE_MS = 30 * 60 * 1000; // 30 minutes
			
			if (currentTime - supportTimestamp >= MAX_SUPPORT_AGE_MS) {
				console.log('Support request too old, ignoring update');
				localStorage.removeItem('pendingSupportData');
				return;
			}
		} catch (error) {
			console.error('Error parsing pendingSupportData:', error);
			localStorage.removeItem('pendingSupportData');
			return;
		}
		
		try {
			const token = localStorage.getItem('token');
			if (!token) {
				console.error('No token found in localStorage');
				return;
			}
			
			console.log(`Updating support ${supportId} with chat ID ${chatId}`);
			const result = await updateSupportChatId(token, supportId, chatId);
			console.log('Support update result:', result);
			
			// Clear the pending support data to prevent duplicate updates
			localStorage.removeItem('pendingSupportData');
			pendingSupportId = '';
			console.log('Support updated successfully with chat ID:', chatId);
		} catch (error) {
			console.error("Failed to update support with chat ID:", error);
			toast.error($i18n.t('Failed to link support to chat. Please try again.'));
			
			// Even on error, clear the pending support after a certain number of attempts
			try {
				const supportData = JSON.parse(pendingSupportData || '{}');
				const attemptCount = (supportData.attempts || 0) + 1;
				
				if (attemptCount >= 3) {
					// After 3 failed attempts, give up
					console.log('Exceeded max attempts to update support, clearing data');
					localStorage.removeItem('pendingSupportData');
				} else {
					// Update attempt count
					supportData.attempts = attemptCount;
					localStorage.setItem('pendingSupportData', JSON.stringify(supportData));
					console.log(`Update failed, attempt ${attemptCount}/3`);
				}
			} catch (parseError) {
				// If we can't even parse/update the attempt count, just clear it
				localStorage.removeItem('pendingSupportData');
			}
		}
	}

	// Step Navigation
	const steps = [
		'Subject',
		'Course',
		'Objectives',
		'Level',
		'Details',
		'Avatar',
		'Review'
	];

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
	const learningTypes = [
		{ id: 'exam', name: 'I\'m preparing for an exam', icon: '📝' },
		{ id: 'course', name: 'I\'m reviewing a course', icon: '📚' },
		{ id: 'skill', name: 'I want to build a new skill', icon: '🚀' }
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
				keywords: keywords.length > 0 ? keywords : undefined,
				start_date: startDate || undefined,
				end_date: endDate || undefined,
				avatar_id: undefined
			};

			console.log('Creating support request with data:', JSON.stringify(supportDetails));
			const supportResponse = await createSupport(token, supportDetails);
			console.log('Create support API response:', supportResponse);
			
			if (supportResponse && supportResponse.id) {
				// First, clean up any existing pendingSupportData
				localStorage.removeItem('pendingSupportData');
				
				// Store the support ID in localStorage for later update with chat ID,
				// including a timestamp and attempt counter
				const supportData = {
					id: supportResponse.id,
					timestamp: Date.now(),
					attempts: 0
				};
				localStorage.setItem('pendingSupportData', JSON.stringify(supportData));
				pendingSupportId = supportResponse.id;
				
				toast.success($i18n.t('Support created successfully!'));
				
				if (uploadedFiles.length > 0) {
					try {
						for (const file of uploadedFiles) {
							await uploadSupportFile(token, supportResponse.id, file);
						}
						toast.success($i18n.t(`Uploaded ${uploadedFiles.length} file(s)`));
					} catch (fileError: any) {
						console.error('Error uploading files:', fileError);
						toast.error($i18n.t(`Support saved, but file upload failed: ${fileError?.message || 'Unknown error'}`));
					}
				}
				
				// Dispatch global event to notify components that a support is waiting for chat linkage
				if (browser) {
					window.openTutorEvents.dispatchEvent(new CustomEvent('supportCreated', { 
						detail: { 
							supportId: supportResponse.id,
							timestamp: Date.now()
						} 
					}));
				}
				
				// Before redirecting, clear any old chat ID to ensure we don't accidentally connect
				// to an existing chat
				storeChatId.set('');
				
				// After creating the support, redirect to chat selection page
				goto('/student/chat');
			} else {
				toast.error($i18n.t('Failed to save support request: Unexpected response from server.'));
			}
		} catch (error: any) {
			console.error('Error in saveSupportToDatabase:', error);
			toast.error(`${$i18n.t('An error occurred')}: ${error?.message || $i18n.t('Failed to process your request. Please try again.')}`);
		} finally {
			isSubmitting = false;
		}
	}

	// Navigation functions
	function nextStep() {
		if (currentStep < steps.length - 1) {
			// Add transition direction class for content
			const contentEl = document.querySelector('.step-content-enter');
			if (contentEl) {
				contentEl.classList.remove('step-content-enter');
				contentEl.classList.add('step-content-exit');
				
				// Use a timeout to allow animation to complete before changing step
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
	$: isSubjectSelected = selectedSubject || customSubject.trim().length > 0;
	$: isCourseSelected = uploadedFiles.length > 0 || true; // Make this always return true since we're not requiring course selection anymore
	$: isObjectiveValid = learningObjective.trim().length > 0;
	$: isLearningTypeSelected = selectedLearningType !== null;
	$: isLevelSelected = selectedLevel.trim().length > 0;
	$: canProceed =
		currentStep === 0
			? isTitleValid && isSubjectSelected
			: currentStep === 1
				? true
				: currentStep === 2
					? isLearningTypeSelected && selectedLearningType !== null
					: currentStep === 3
						? isLevelSelected
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
		philosophy: 'psychology',
		other: 'school'
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
									<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" class="checkmark-appear"></path>
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
										<div class="absolute top-0 left-0 h-full bg-blue-600 line-progress" 
											 style="width: 100%; transition-delay: {index * 0.1}s;"></div>
									{/if}
								</div>
							{/if}
						</li>
					{/each}
				</ol>
			</div>

			<!-- Enhanced content container with better styling -->
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 sm:p-8 transition-all duration-300">
				<!-- Step content with improved styling -->
				<div class="min-h-[400px] transition-all duration-300">
				{#if currentStep === 0}
						<!-- Basic Information step - Enhanced UI -->
						<div class="space-y-8 step-content-enter">
						<div>
								<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
									{$i18n.t('Tell us about your learning needs')}
								</h3>
								
								<div class="mb-6">
									<label for="supportTitle" class="block text-gray-700 dark:text-gray-200 font-medium mb-2 text-sm">
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

							<div class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700">
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
												<span class="text-sm text-gray-800 dark:text-gray-200 font-medium">{$i18n.t(subject.name)}</span>
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
											<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
												<path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
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
											<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
												<path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
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
							{$i18n.t('Course Materials')}
						</h3>

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
								{$i18n.t('Upload your course materials to get personalized learning assistance')}
							</p>
						</div>
					</div>
				{:else if currentStep === 2}
						<!-- Objectives step - Enhanced UI -->
						<div class="space-y-8 step-content-enter">
						<div>
							<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
								{$i18n.t('Define your learning objectives')}
							</h3>
							
							<div class="mb-8 bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700">
								<div class="flex items-center justify-between mb-3">
								<label
									for="learningObjective"
										class="block text-gray-700 dark:text-gray-200 font-medium text-sm"
								>
										{$i18n.t("What do you want to explore today?")}
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
												<path d="M11 17a1 1 0 001.447.894l4-2A1 1 0 0017 15V9.236a1 1 0 00-1.447-.894l-4 2a1 1 0 00-.553.894V17zM15.211 6.276a1 1 0 000-1.788l-4.764-2.382a1 1 0 00-.894 0L4.789 4.488a1 1 0 000 1.788l4.764 2.382a1 1 0 00.894 0l4.764-2.382zM4.447 8.342A1 1 0 003 9.236V15a1 1 0 00.553.894l4 2A1 1 0 009 17v-5.764a1 1 0 00-.553-.894l-4-2z" />
									</svg>
								</button>
										<div class="absolute z-10 right-0 w-64 p-3 bg-white dark:bg-gray-800 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 text-sm border border-gray-200 dark:border-gray-700 mt-2">
											{$i18n.t('AI can help you craft personalized learning objectives based on your interests and goals')}
							</div>
									</div>
								</div>
								
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

							<div class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700">
								<div class="mb-4">
									<label class="block text-gray-700 dark:text-gray-200 font-medium text-sm">
									{$i18n.t('How can I support you today?')}
										<span class="text-red-500 ml-1">*</span>
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
											<span class="text-sm font-medium text-gray-800 dark:text-gray-200">{$i18n.t(type.name)}</span>
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
							{$i18n.t('Choose your learning level')}
						</h3>

						<p class="text-gray-600 dark:text-gray-400 mb-6">
							{$i18n.t('Select the appropriate learning level for this material to ensure the content matches your needs')}
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
										<div class={`w-12 h-12 rounded-full flex items-center justify-center mr-4 ${
											level.color === 'green' 
												? 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-300' 
												: level.color === 'red' 
													? 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-300' 
													: level.color === 'orange' 
														? 'bg-orange-100 text-orange-600 dark:bg-orange-900 dark:text-orange-300' 
														: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900 dark:text-yellow-300'
										}`}>
											<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
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
								{$i18n.t('Fine-tune your learning experience')}
							</h3>
							
							<p class="text-gray-600 dark:text-gray-400 mb-8">
								{$i18n.t('These additional details help us personalize your support experience')}
							</p>
							
							<div class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700 mb-8">
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
											<div class="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
												<svg class="w-5 h-5 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
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
											<div class="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
												<svg class="w-5 h-5 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
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
							<div class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700 mb-8">
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
									<div class="flex flex-wrap gap-2 mt-4 p-3 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
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
											<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
												<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
											</svg>
										</button>
									</div>
								{/each}
							</div>
								{:else}
									<div class="mt-4 p-3 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 text-sm text-gray-500 dark:text-gray-400 italic">
										{$i18n.t('No keywords added yet')}
									</div>
								{/if}
						</div>

						<!-- Availability -->
							<div class="bg-gray-50 dark:bg-gray-750 p-6 rounded-lg border border-gray-100 dark:border-gray-700">
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
				{:else if currentStep === 5}
					<!-- Avatar step placeholder -->
					<div class="space-y-6 step-content-enter">
					<div class="text-gray-800 dark:text-gray-200">
						<h3 class="text-xl font-semibold mb-4">{$i18n.t('Choose Your Avatar')}</h3>
						<p>{$i18n.t('This step would allow selecting a tutor avatar.')}</p>
						</div>
					</div>
				{:else if currentStep === 6}
					<!-- Review step - Clean, professional design -->
					<div class="space-y-8 step-content-enter">
						<div>
							<h3 class="text-xl font-semibold text-gray-800 dark:text-white mb-6">
								{$i18n.t('Review your support')}
							</h3>
							
							<p class="text-gray-600 dark:text-gray-400 mb-8">
								{$i18n.t('Verify all details before creating your support')}
							</p>

							<div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden border border-gray-200 dark:border-gray-700">
								<!-- Title and subject header -->
								<div class="bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-5 flex items-center justify-between">
									<div class="flex-1">
										<h4 class="text-lg font-bold text-white">{supportTitle}</h4>
										{#if selectedSubject}
											<div class="flex items-center mt-2">
												<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-white/20 text-white">
													{selectedSubject ? subjects.find(s => s.id === selectedSubject)?.name || customSubject : customSubject}
												</span>
					</div>
				{/if}
									</div>
			</div>

								<!-- Content sections -->
								<div class="p-0">
									<!-- Summary Info -->
									<div class="px-6 py-5 border-b border-gray-200 dark:border-gray-700 grid grid-cols-1 md:grid-cols-2 gap-6">
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
													<div class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-200">
														{learningTypes.find(lt => lt.id === selectedLearningType)?.name || selectedLearningType}
													</div>
												{:else}
													<p class="text-gray-400 dark:text-gray-500 italic text-sm">Not specified</p>
												{/if}
											</div>

											<div>
												<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">
													{$i18n.t('Learning Level')}
												</h5>
												{#if selectedLevel}
													<div class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200">
														{learningLevels.find(ll => ll.id === selectedLevel)?.name || selectedLevel}
													</div>
												{:else}
													<p class="text-gray-400 dark:text-gray-500 italic text-sm">Not specified</p>
												{/if}
											</div>

											<div>
												<h5 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">
													{$i18n.t('Content Details')}
												</h5>
												<div class="flex items-center text-gray-700 dark:text-gray-300 space-x-4">
													<div class="flex items-center">
														<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500 dark:text-gray-400 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"/>
														</svg>
														<span class="text-sm">{contentLanguage}</span>
													</div>
													<div class="flex items-center">
														<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500 dark:text-gray-400 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
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
															<span class="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200">
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
															<li class="flex items-center text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700/50 px-3 py-2 rounded-md">
																<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500 dark:text-gray-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																	<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
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
																<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500 dark:text-gray-400 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																	<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
																</svg>
																<span class="text-sm">{$i18n.t('From')}: {formatDate(startDate)}</span>
															</div>
														{/if}
														{#if endDate}
															<div class="flex items-center text-gray-700 dark:text-gray-300">
																<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500 dark:text-gray-400 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																	<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
																</svg>
																<span class="text-sm">{$i18n.t('To')}: {formatDate(endDate)}</span>
															</div>
														{/if}
													</div>
												</div>
											{/if}
										</div>
									{/if}

									<!-- Confirmation Message -->
									<div class="px-6 py-5 bg-gray-50 dark:bg-gray-750">
										<div class="flex items-center text-gray-700 dark:text-gray-300">
											<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
											</svg>
											<p class="text-sm">{$i18n.t('Click "Start Learning" below to create your support and begin your personalized learning experience.')}</p>
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
					class="px-6 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200 font-medium flex items-center"
					disabled={isSubmitting}
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
					</svg>
					{currentStep === 0 ? $i18n.t('Cancel') : $i18n.t('Back')}
				</button>

				<button
					on:click={nextStep}
					class="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 font-medium flex items-center shadow-sm"
					disabled={!canProceed || isSubmitting}
				>
					{#if isSubmitting}
						<svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						{$i18n.t('Processing...')}
					{:else}
						{currentStep === steps.length - 1 ? $i18n.t('Start Learning') : $i18n.t('Continue')}
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
						</svg>
					{/if}
				</button>
			</div>
		</div>
	{:else}
			<!-- Success screen -->
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center animate-fadeIn">
				<div class="mb-6 flex justify-center">
					<div class="w-20 h-20 rounded-full bg-green-100 dark:bg-green-800 flex items-center justify-center">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-green-600 dark:text-green-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
						</svg>
					</div>
				</div>
				
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-3">{$i18n.t('Support Created!')}</h2>
				<p class="text-gray-600 dark:text-gray-300 mb-8 max-w-md mx-auto">{$i18n.t('Your support has been successfully created. Get ready for a personalized learning experience!')}</p>
				
				<button 
					on:click={() => goto('/student/dashboard')}
					class="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium"
				>
					{$i18n.t('Return to Dashboard')}
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
		from { opacity: 0; transform: translateY(20px); }
		to { opacity: 1; transform: translateY(0); }
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
		transition: width 0.5s ease-out, background-color 0.5s ease-out;
	}
	
	/* Step content slide animations */
	.step-content-enter {
		animation: slideIn 0.5s ease-out forwards;
	}
	
	@keyframes slideIn {
		from { opacity: 0; transform: translateX(30px); }
		to { opacity: 1; transform: translateX(0); }
	}
	
	.step-content-exit {
		animation: slideOut 0.3s ease-in forwards;
	}
	
	@keyframes slideOut {
		from { opacity: 1; transform: translateX(0); }
		to { opacity: 0; transform: translateX(-30px); }
	}
	
	/* Checkmark animation */
	.checkmark-appear {
		stroke-dasharray: 100;
		stroke-dashoffset: 100;
		animation: drawCheck 0.6s ease-in-out forwards;
	}
	
	@keyframes drawCheck {
		from { stroke-dashoffset: 100; }
		to { stroke-dashoffset: 0; }
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

