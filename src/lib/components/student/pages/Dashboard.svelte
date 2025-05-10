<!-- Dashboard.svelte -->
<script lang="ts">
	import { getContext, onMount, onDestroy } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { chatId as storeChatId } from '$lib/stores';
	import CourseCard from '../elements/CourseCard.svelte';
	import { getSupportRequests, type SupportResponse, updateSupportChatId } from '$lib/apis/supports';
	import { page } from '$app/stores';
	import { toast } from 'svelte-sonner';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// State for user's support requests
	let userSupports: SupportResponse[] = [];
	let isLoading = true;
	
	// Track pending support and chat linkage
	let pendingSupportId = '';
	let chatIdSubscription: Function;
	let urlCheckInterval: ReturnType<typeof setInterval>;
	let currentPath = '';
	let chatIdFromURL = '';

	// Sample progress data (keeping this for UI)
	const progressData = [75, 45, 60, 30, 85, 40, 55, 65];

	// Clear chat ID and support data when the dashboard is loaded
	onMount(async () => {
		if (browser) {
			console.log('Dashboard mounted: clearing chat and support data');
			
			// Clear chatId from the store
			storeChatId.set('');
			
			// Clear any sessionStorage data
			if (sessionStorage.selectedModels) {
				sessionStorage.removeItem('selectedModels');
			}
			
			// Clear any localStorage data for pending support
			if (localStorage.getItem('pendingSupportData')) {
				localStorage.removeItem('pendingSupportData');
			}
			
			// Clear any stored chat input data
			const keysToRemove = [];
			for (let i = 0; i < localStorage.length; i++) {
				const key = localStorage.key(i);
				if (key && key.startsWith('chat-input-')) {
					keysToRemove.push(key);
				}
			}
			
			// Remove the collected keys
			keysToRemove.forEach(key => {
				localStorage.removeItem(key);
			});
			
			// Fetch user's support requests
			const token = localStorage.getItem('token');
			if (token) {
				try {
					const supports = await getSupportRequests(token);
					if (supports && Array.isArray(supports)) {
						userSupports = supports;
						console.log('Fetched user supports:', userSupports);
					}
				} catch (error) {
					console.error('Error fetching supports:', error);
					userSupports = [];
				} finally {
					isLoading = false;
				}
			} else {
				console.log('No auth token found');
				isLoading = false;
			}

			// Create a global event handler for chat creation that can be triggered from any component
			if (!window.openTutorEvents) {
				window.openTutorEvents = new EventTarget();
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
						console.log('Support expired during URL check, clearing');
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

	// Clean up listeners and intervals on component destruction
	onDestroy(() => {
		console.log('Dashboard component destroyed');
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
			
			// Check if support is too old
			const currentTime = Date.now();
			const supportTimestamp = supportData.timestamp || 0;
			const MAX_SUPPORT_AGE_MS = 30 * 60 * 1000; // 30 minutes
			
			if (currentTime - supportTimestamp >= MAX_SUPPORT_AGE_MS) {
				console.log('Support too old, ignoring update');
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

	// State for pagination
	let currentPage = 0;
	const cardsPerPage = 4;

	// Calculate total pages
	$: totalPages = Math.ceil(userSupports.length / cardsPerPage);

	// Get current page courses/supports
	$: currentSupports = userSupports.slice(
		currentPage * cardsPerPage,
		(currentPage + 1) * cardsPerPage
	);

	// Animation direction tracking
	let animationDirection = 'right'; // 'left' or 'right'

	// Navigation functions
	function nextPage() {
		if (currentPage < totalPages - 1) {
			animationDirection = 'right';
			currentPage += 1;
		}
	}

	function previousPage() {
		if (currentPage > 0) {
			animationDirection = 'left';
			currentPage -= 1;
		}
	}

	function goToPage(pageIndex: number) {
		if (pageIndex !== currentPage) {
			animationDirection = pageIndex > currentPage ? 'right' : 'left';
			currentPage = pageIndex;
		}
	}

	// State to control the join course popup
	let showJoinCoursePopup = false;

	// State to control the support popup
	let showSupportPopup = false;

	// Toggle the popups
	function toggleJoinCoursePopup() {
		showJoinCoursePopup = !showJoinCoursePopup;
		if (showJoinCoursePopup) showSupportPopup = false;
	}

	function toggleSupportPopup() {
		showSupportPopup = !showSupportPopup;
		if (showSupportPopup) showJoinCoursePopup = false;
	}

	// Course code input
	let courseCode = '';

	// Don't show again state
	let dontShowAgain = false;

	// Handle joining a course
	function handleJoinCourse() {
		if (courseCode === '0000') {
			// Redirect to student chat component if code is 0000
			goto('/student/chat');
			showJoinCoursePopup = false;
		} else if (courseCode.trim() !== '') {
			// For other valid codes, you would implement the actual join logic here
			// For now, just close the popup
			showJoinCoursePopup = false;
		}
	}

	// Handle creating support
	function handleCreateSupport() {
		// Navigate to student support page
		goto('/student/support');
		showSupportPopup = false;
	}
	
	// Handle card click - open chat if exists or save support ID and navigate to chat page
	function handleCardClick(support: SupportResponse, index: number) {
		if (support.chat_id) {
			// If the support already has a chat linked, open it
			goto(`/student/c/${support.chat_id}`);
		} else {
			// No chat linked yet, save the support ID and navigate to chat page
			const supportData = {
				id: support.id,
				timestamp: Date.now(),
				attempts: 0
			};
			
			localStorage.setItem('pendingSupportData', JSON.stringify(supportData));
			pendingSupportId = support.id;
			console.log('Saved support ID to localStorage:', support.id);
			
			goto('/student/chat');
		}
	}
</script>

<div class="flex flex-col gap-6">
	<div class="flex justify-end">
		<div class="flex gap-4">
			<button
				class="flex items-center gap-2 bg-indigo-500 dark:bg-indigo-600 text-white py-3 px-6 rounded-full hover:bg-indigo-600 dark:hover:bg-indigo-700 transition-colors"
				on:click={toggleSupportPopup}
			>
				<span class="text-xl font-bold">+</span>
				<span>{$i18n.t('Support')}</span>
			</button>
		</div>
	</div>

	<div class="flex flex-col gap-6">
		{#if isLoading}
			<div class="flex justify-center items-center py-12">
				<div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
				<span class="ml-3 text-gray-600 dark:text-gray-300">{$i18n.t('Loading your supports...')}</span>
		</div>
		{:else if userSupports.length === 0}
			<div class="flex flex-col items-center justify-center py-6 text-center">
				<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-indigo-400 dark:text-indigo-300 mb-3">
					<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
					</svg>
				<h3 class="text-lg font-medium text-gray-800 dark:text-white mb-2">
					{$i18n.t('No supports found')}
				</h3>
				<p class="text-sm text-gray-600 dark:text-gray-400">
					{$i18n.t('Create a support to get personalized learning assistance')}
				</p>
			</div>
		{:else}
			<div class="relative">
				<!-- Left arrow -->
				{#if currentPage > 0}
				<button
						class="absolute left-0 top-1/2 transform -translate-y-1/2 -translate-x-4 sm:-translate-x-6 p-2 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-all"
					on:click={previousPage}
						aria-label="{$i18n.t('Previous supports')}"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
					</svg>
				</button>
				{/if}
				
				<!-- Right arrow -->
				{#if currentPage < totalPages - 1}
				<button
						class="absolute right-0 top-1/2 transform -translate-y-1/2 translate-x-4 sm:translate-x-6 p-2 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-all"
					on:click={nextPage}
						aria-label="{$i18n.t('Next supports')}"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
					</svg>
				</button>
				{/if}

				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 card-container">
					{#each currentSupports as support, index (support.id)}
						<div 
							class="cursor-pointer card-item"
							class:card-slide-enter-from-right={animationDirection === 'right'}
							class:card-slide-enter-from-left={animationDirection === 'left'}
							on:click={() => handleCardClick(support, index)}
							on:keypress={(e) => e.key === 'Enter' && handleCardClick(support, index)}
							tabindex="0"
							role="button"
							style="animation-delay: {index * 0.05}s"
						>
							<CourseCard
								title={support.title}
								progress={progressData[index % progressData.length]}
								subject={index % 2 === 0 ? 'computer-science' : 'mathematics'}
								href="#"
							/>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>

<!-- Join Course Popup Modal -->
{#if showJoinCoursePopup}
	<div
		class="fixed inset-0 backdrop-blur-sm bg-white/30 dark:bg-black/30 flex items-center justify-center z-50"
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 w-full max-w-md mx-auto relative"
		>
			<!-- Close Button -->
			<button
				class="absolute top-3 right-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none"
				on:click={toggleJoinCoursePopup}
			>
				<span class="text-2xl font-light">×</span>
			</button>

			<!-- OT Logo -->
			<div class="flex justify-center mb-8">
				<img src="/favicon.png" alt="OT Logo" class="w-26 h-26" />
			</div>

			<!-- Title and Instructions -->
			<h2 class="text-center text-xl font-bold mb-2 text-gray-900 dark:text-white">
				{$i18n.t('Enter the course code provided by your teacher')}
			</h2>
			<p class="text-center text-gray-500 dark:text-gray-400 mb-6">
				{$i18n.t('The code is a 6-8 character alphanumeric string')}
			</p>

			<!-- Course Code Input -->
			<div class="mb-6">
				<input
					type="text"
					bind:value={courseCode}
					placeholder={$i18n.t('Enter Course Code')}
					class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md text-center focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
					on:keydown={(e) => e.key === 'Enter' && handleJoinCourse()}
				/>
			</div>

			<!-- Help Text -->
			<p class="text-center text-gray-500 dark:text-gray-400 mb-6">
				{$i18n.t('Need a code? Ask your teacher or institution')}
			</p>

			<!-- Join Button -->
			<div class="flex justify-center mb-4">
				<button
					class="bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-700 dark:hover:bg-indigo-800 text-white py-3 px-8 rounded-full font-medium"
					on:click={handleJoinCourse}
				>
					{$i18n.t('Join Course')}
				</button>
			</div>

			<!-- Create Course Link -->
			<div class="text-center">
				<span class="text-gray-500 dark:text-gray-400">{$i18n.t('or')}</span>
				<a href="#" class="text-blue-600 dark:text-blue-400 hover:underline"
					>{$i18n.t('create your own course')}</a
				>
			</div>
		</div>
	</div>
{/if}

<!-- Support Popup Modal -->
{#if showSupportPopup}
	<div
		class="fixed inset-0 backdrop-blur-sm bg-white/30 dark:bg-black/30 flex items-center justify-center z-50"
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 w-full max-w-md mx-auto relative"
		>
			<!-- Close Button -->
			<button
				class="absolute top-3 right-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none"
				on:click={toggleSupportPopup}
			>
				<span class="text-2xl font-light">×</span>
			</button>

			<!-- OT Logo -->
			<div class="flex justify-center mb-8">
				<img src="/favicon.png" alt="OT Logo" class="w-26 h-26" />
			</div>

			<!-- Title -->
			<h2 class="text-center text-xl font-bold text-gray-900 dark:text-white">
				{$i18n.t('Create Personalized Tutorials for any Subject or Topic')}
			</h2>

			<!-- Divider -->
			<div class="my-8">
				<hr class="border-gray-200 dark:border-gray-600" />
			</div>

			<!-- Learning Path Section -->
			<h3 class="text-center text-lg font-medium mb-6 text-gray-900 dark:text-white">
				{$i18n.t('Create Tour Learning Path')}
			</h3>

			<!-- Steps -->
			<div class="space-y-4 mb-10 px-4">
				<div class="flex items-center gap-4">
					<div
						class="flex-shrink-0 bg-[#004AAD] text-white rounded-full w-7 h-7 flex items-center justify-center"
					>
						<span class="font-bold">1</span>
					</div>
					<span class="text-gray-800 dark:text-gray-200"
						>{$i18n.t('Choose your topic and difficulty level')}</span
					>
				</div>
				<div class="flex items-center gap-4">
					<div
						class="flex-shrink-0 bg-[#004AAD] text-white rounded-full w-7 h-7 flex items-center justify-center"
					>
						<span class="font-bold">2</span>
					</div>
					<span class="text-gray-800 dark:text-gray-200"
						>{$i18n.t('Set your learning objectives')}</span
					>
				</div>
				<div class="flex items-center gap-4">
					<div
						class="flex-shrink-0 bg-[#004AAD] text-white rounded-full w-7 h-7 flex items-center justify-center"
					>
						<span class="font-bold">3</span>
					</div>
					<span class="text-gray-800 dark:text-gray-200"
						>{$i18n.t('Enjoy AI-powered personalized learning')}</span
					>
				</div>
			</div>

			<!-- Create Support Button -->
			<div class="flex justify-center mb-8">
				<button
					class="bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-700 dark:hover:bg-indigo-800 text-white py-3 px-12 rounded-full font-medium"
					on:click={handleCreateSupport}
				>
					{$i18n.t('Create My support')}
				</button>
			</div>

			<!-- Don't Show Again Checkbox -->
			<div class="flex items-center justify-center gap-2 mt-4">
				<input
					type="checkbox"
					id="dontShow"
					bind:checked={dontShowAgain}
					class="h-4 w-4 text-indigo-600 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded focus:ring-indigo-500"
				/>
				<label for="dontShow" class="text-sm text-gray-500 dark:text-gray-400"
					>{$i18n.t('Don\'t show me again')}</label
				>
			</div>
		</div>
	</div>
{/if}

<style>
	/* Card transition animations */
	.card-container {
		position: relative;
		overflow: hidden;
	}

	.card-item {
		transform-origin: center center;
		backface-visibility: hidden;
		transition: transform 0.2s ease;
	}
	
	.card-item:hover {
		transform: translateY(-3px);
	}

	.card-slide-enter-from-right {
		animation: slideInFromRight 0.5s cubic-bezier(0.25, 0.1, 0.25, 1) forwards;
	}

	.card-slide-enter-from-left {
		animation: slideInFromLeft 0.5s cubic-bezier(0.25, 0.1, 0.25, 1) forwards;
	}

	.card-slide-exit-to-right {
		animation: slideOutToRight 0.5s cubic-bezier(0.25, 0.1, 0.25, 1) forwards;
	}

	.card-slide-exit-to-left {
		animation: slideOutToLeft 0.5s cubic-bezier(0.25, 0.1, 0.25, 1) forwards;
	}

	@keyframes slideInFromRight {
		from {
			transform: translateX(30px);
			opacity: 0;
		}
		to {
			transform: translateX(0);
			opacity: 1;
		}
	}

	@keyframes slideInFromLeft {
		from {
			transform: translateX(-30px);
			opacity: 0;
		}
		to {
			transform: translateX(0);
			opacity: 1;
		}
	}

	@keyframes slideOutToRight {
		from {
			transform: translateX(0);
			opacity: 1;
		}
		to {
			transform: translateX(30px);
			opacity: 0;
		}
	}

	@keyframes slideOutToLeft {
		from {
			transform: translateX(0);
			opacity: 1;
		}
		to {
			transform: translateX(-30px);
			opacity: 0;
		}
	}
</style>
