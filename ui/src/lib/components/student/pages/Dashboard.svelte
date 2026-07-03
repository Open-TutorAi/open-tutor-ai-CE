<!-- Dashboard Étudiant — Performance & Productivité -->
<script lang="ts">
	import { getContext, onMount, onDestroy } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
 main
	import { chatId as storeChatId, isDemo, demoData, user } from '$lib/stores';
	import { dashboardTab } from '$lib/stores/focusTimer';
	import { getSupportRequests, type SupportResponse, updateSupportChatId } from '$lib/apis/supports';

	import { chatId as storeChatId, isDemo, demoData } from '$lib/stores';
	import CourseCard from '../elements/CourseCard.svelte';
	import {
		getSupportRequests,
		type SupportResponse,
		updateSupportChatId
	} from '$lib/apis/supports';
 main
	import { page } from '$app/stores';
	import { fade, scale } from 'svelte/transition';
	import { toast } from 'svelte-sonner';

	import PerformanceTab from '../dashboard/PerformanceTab.svelte';
	import ProductivityTab from '../dashboard/ProductivityTab.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// ── Greeting ───────────────────────────────────────────────────────────────
	$: firstName = $user?.name?.split(' ')[0] ?? '';

	function formatDateFR(): string {
		const now = new Date();
		const days = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'];
		const months = [
			'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
			'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
		];
		return `${days[now.getDay()]} ${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}`;
	}

	// ── Support request management (existing logic preserved) ─────────────────
	let userSupports: SupportResponse[] = [];
	let isLoading = true;

	$: displaySupports = $isDemo
		? $demoData.supports.map((s) => ({
				id: s.id,
				title: s.title,
				description: s.description,
				status: s.progress < 30 ? 'not-started' : s.progress < 100 ? 'in-progress' : 'completed',
				category: s.category,
				difficulty: s.difficulty,
				progress: s.progress
			}))
		: userSupports;

 main

	// Track pending support and chat linkage
 main
	let pendingSupportId = '';
	let chatIdSubscription: Function;
	let urlCheckInterval: ReturnType<typeof setInterval>;
	let currentPath = '';
	let chatIdFromURL = '';

	onMount(async () => {
		if (browser) {
 main
			storeChatId.set('');
			sessionStorage.removeItem('selectedModels');

			if (localStorage.getItem('pendingSupportData')) {
				localStorage.removeItem('pendingSupportData');
			}
			const keysToRemove: string[] = [];

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
 main
			for (let i = 0; i < localStorage.length; i++) {
				const key = localStorage.key(i);
				if (key && key.startsWith('chat-input-')) keysToRemove.push(key);
			}
 main
			keysToRemove.forEach((k) => localStorage.removeItem(k));



			// Remove the collected keys
			keysToRemove.forEach((key) => {
				localStorage.removeItem(key);
			});

			// Fetch user's support requests
 main
			if ($isDemo) {
				isLoading = false;
			} else {
				const token = localStorage.getItem('token');
				if (token) {
					try {
						const supports = await getSupportRequests(token);
						if (supports && Array.isArray(supports)) userSupports = supports;
					} catch {
						userSupports = [];
					} finally {
						isLoading = false;
					}
				} else {
					isLoading = false;
				}
			}

 main
			if (!window.openTutorEvents) window.openTutorEvents = new EventTarget();
			window.openTutorEvents.addEventListener('chatCreated', ((event: CustomEvent) => {
				const newChatId = event.detail?.chatId;
				if (newChatId && pendingSupportId) updateSupportWithChatId(pendingSupportId, newChatId);
			}) as EventListener);


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
 main
			chatIdSubscription = storeChatId.subscribe((newChatId) => {
				if (newChatId && newChatId !== 'local' && pendingSupportId)
					updateSupportWithChatId(pendingSupportId, newChatId);
			});

 main

			// Set up monitoring for URL changes as another backup
 main
			urlCheckInterval = setInterval(() => {
				try {
					const pendingSupportData = localStorage.getItem('pendingSupportData');
 main
					if (!pendingSupportData) { clearInterval(urlCheckInterval); return; }
					const supportData = JSON.parse(pendingSupportData);
					if (Date.now() - (supportData.timestamp || 0) >= 30 * 60 * 1000) {

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
 main
						localStorage.removeItem('pendingSupportData');
						clearInterval(urlCheckInterval);
						return;
					}
 main


					// Check for URL changes indicating chat creation
 main
					const currentURL = window.location.pathname;
					if (currentURL.startsWith('/student/c/')) {
						const newChatId = currentURL.split('/student/c/')[1].split('/')[0];
						if (newChatId && supportData.id) updateSupportWithChatId(supportData.id, newChatId);
					}
				} catch {
					localStorage.removeItem('pendingSupportData');
					clearInterval(urlCheckInterval);
				}
			}, 1000);
		}
	});

	onDestroy(() => {
		if (browser) {
 main
			if (chatIdSubscription) chatIdSubscription();
			if (urlCheckInterval) clearInterval(urlCheckInterval);

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
 main
		}
	});

	$: if ($page && $page.url && browser) {
		currentPath = $page.url.pathname || '';
 main
		if (currentPath.startsWith('/student/c/')) {
			chatIdFromURL = currentPath.replace('/student/c/', '').split('/')[0];


		// Check for chat creation
		if (currentPath.startsWith('/student/c/')) {
			chatIdFromURL = currentPath.replace('/student/c/', '').split('/')[0];

			// Only proceed if we have a valid ID and there's a pending support
 main
			if (chatIdFromURL && localStorage.getItem('pendingSupportData')) {
				try {
					const supportData = JSON.parse(localStorage.getItem('pendingSupportData') || '{}');
					const supportId = supportData.id;
 main
					const age = Date.now() - (supportData.timestamp || 0);
					if (supportId && age < 30 * 60 * 1000) updateSupportWithChatId(supportId, chatIdFromURL);
					else if (age >= 30 * 60 * 1000) localStorage.removeItem('pendingSupportData');
				} catch {


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
 main
					localStorage.removeItem('pendingSupportData');
				}
			}
		}
	}

	async function updateSupportWithChatId(supportId: string, chatId: string) {
 main
		if (!supportId || !chatId || !browser || chatId === 'local' || chatId === 'undefined') return;
		let pendingSupportData: string | null;
		try {
			pendingSupportData = localStorage.getItem('pendingSupportData');
			if (!pendingSupportData) return;
			const supportData = JSON.parse(pendingSupportData);
			if (supportData.id !== supportId) return;
			if (Date.now() - (supportData.timestamp || 0) >= 30 * 60 * 1000) {

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
 main
				localStorage.removeItem('pendingSupportData');
				return;
			}
		} catch {
			localStorage.removeItem('pendingSupportData');
			return;
		}
 main
		try {
			const token = localStorage.getItem('token');
			if (!token) return;
			await updateSupportChatId(token, supportId, chatId);
			localStorage.removeItem('pendingSupportData');
			pendingSupportId = '';
		} catch {
			try {
				const supportData = JSON.parse(pendingSupportData || '{}');
				const attemptCount = (supportData.attempts || 0) + 1;
				if (attemptCount >= 3) localStorage.removeItem('pendingSupportData');
				else {
=======

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
			console.error('Failed to update support with chat ID:', error);

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
 main
					supportData.attempts = attemptCount;
					localStorage.setItem('pendingSupportData', JSON.stringify(supportData));
				}
			} catch {
				localStorage.removeItem('pendingSupportData');
			}
		}
	}

	// ── Support popup ──────────────────────────────────────────────────────────
	let showSupportPopup = false;
	let dontShowAgain = false;

	if (browser) {
		dontShowAgain = localStorage.getItem('hideSupportPopup') === 'true';
	}

	$: if (browser) {
		if (dontShowAgain) localStorage.setItem('hideSupportPopup', 'true');
		else localStorage.removeItem('hideSupportPopup');
	}

	function toggleSupportPopup() {
		if (dontShowAgain || (browser && localStorage.getItem('hideSupportPopup') === 'true')) {
			goto('/student/support/create');
			return;
		}
		showSupportPopup = !showSupportPopup;
	}

	function handleCreateSupport() {
		goto('/student/support/create');
		showSupportPopup = false;
	}
 main
</script>

<!-- ── Page header ── -->
<div class="mb-6 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
	<div>
		<h1 class="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
			Bonjour, {firstName} 👋
		</h1>
		<p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{formatDateFR()}</p>


	// Handle card click - open support details page
	function handleCardClick(support: SupportResponse, index: number) {
		goto(`/student/support/${support.id}`);
	}
</script>

<div class="flex flex-col gap-6">
	<div class="flex justify-end">
		<div class="flex gap-4">
			<button
				class="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white dark:bg-white dark:text-black dark:hover:bg-gray-200 rounded-full transition"
				on:click={toggleSupportPopup}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					viewBox="0 0 20 22"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
						clip-rule="evenodd"
					/>
				</svg>
				{$i18n.t('Support')}
			</button>
		</div>
 main
	</div>
	<button
		class="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full transition shadow-sm shadow-blue-200 dark:shadow-blue-900/30 self-start"
		on:click={toggleSupportPopup}
	>
		<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
			<path fill-rule="evenodd"
				d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
				clip-rule="evenodd" />
		</svg>
		{$i18n.t('Support')}
	</button>
</div>

 main
<!-- ── Performance section header ── -->
<div class="mb-4">
	<h2 class="text-base font-semibold text-gray-700 dark:text-gray-200">Votre performance</h2>
	<p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
		{new Date().toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })}
	</p>
</div>

<!-- ── Tab navigation ── -->
<div class="flex gap-1 mb-5 border border-gray-200 dark:border-gray-700 rounded-full p-0.5 w-fit bg-white dark:bg-gray-800 shadow-sm">
	<button
		class="px-5 py-1.5 rounded-full text-sm font-medium transition
			{$dashboardTab === 'performance'
				? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-white shadow-sm border border-gray-200 dark:border-gray-600'
				: 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
		on:click={() => dashboardTab.set('performance')}
	>
		Performance
	</button>
	<button
		class="px-5 py-1.5 rounded-full text-sm font-medium transition
			{$dashboardTab === 'productivity'
				? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-white shadow-sm border border-gray-200 dark:border-gray-600'
				: 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
		on:click={() => dashboardTab.set('productivity')}
	>
		Productivité
	</button>
</div>

	<div class="flex flex-col gap-6">
		{#if isLoading}
			<div class="flex justify-center items-center py-12">
				<div
					class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"
				></div>
				<span class="ml-3 text-gray-600 dark:text-gray-300"
					>{$i18n.t('Loading your supports...')}</span
				>
			</div>
		{:else if displaySupports.length === 0}
			<div class="flex flex-col items-center justify-center py-6 text-center">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="40"
					height="40"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="text-indigo-400 dark:text-indigo-300 mb-3"
				>
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
						aria-label={$i18n.t('Previous supports')}
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
				{/if}

				<!-- Right arrow -->
				{#if currentPage < totalPages - 1}
					<button
						class="absolute right-0 top-1/2 transform -translate-y-1/2 translate-x-4 sm:translate-x-6 p-2 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-all"
						on:click={nextPage}
						aria-label={$i18n.t('Next supports')}
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
				{/if}

				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 card-container">
					{#each currentSupports as support, index (support.id)}
						<div
							class="cursor-pointer card-item h-full"
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
								subject={support.subject || 'mathematics'}
								progress={0}
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
		role="dialog"
		aria-modal="true"
		in:fade
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-11/12 sm:w-full max-w-md mx-auto relative overflow-y-auto max-h-[90vh] ring-1 ring-gray-200 dark:ring-gray-700"
			transition:scale={{ duration: 200 }}
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
 main

<!-- ── Tab content ── -->
{#if $dashboardTab === 'performance'}
	<PerformanceTab />
{:else}
	<ProductivityTab />
{/if}

<!-- ── Support popup ── -->
{#if showSupportPopup}
	<div
		class="fixed inset-0 backdrop-blur-sm bg-white/30 dark:bg-black/30 flex items-center justify-center z-50"
		role="dialog"
		aria-modal="true"
		in:fade
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-4 w-11/12 sm:w-full max-w-sm mx-auto relative overflow-y-auto max-h-[90vh] ring-1 ring-gray-200 dark:ring-gray-700"
			transition:scale={{ duration: 200 }}
		>
			<button
				class="absolute top-2 right-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none"
				on:click={() => (showSupportPopup = false)}
			>
				<span class="text-xl font-light">×</span>
			</button>

			<div class="flex justify-center mb-4">
				<img src="/favicon.png" alt="OT Logo" class="w-20 h-20" />
			</div>

			<h2 class="text-center text-lg font-bold text-gray-900 dark:text-white mb-4">
				{$i18n.t('Create Personalized Tutorials for any Subject or Topic')}
			</h2>
			<h3 class="text-center text-md font-medium mb-4 text-gray-900 dark:text-white">
				{$i18n.t('Create Your Learning Path')}
			</h3>

			<div class="space-y-3 mb-6 px-2">
				{#each [
					$i18n.t('Choose your topic and level'),
					$i18n.t('Set your learning objectives'),
					$i18n.t('Enjoy AI-powered personalized learning')
				] as step, idx}
					<div class="flex items-center gap-3">
						<div class="flex-shrink-0 bg-[#004AAD] text-white rounded-full w-6 h-6 flex items-center justify-center">
							<span class="font-bold text-sm">{idx + 1}</span>
						</div>
						<span class="text-sm text-gray-800 dark:text-gray-200">{step}</span>
					</div>
				{/each}
			</div>

			<div class="flex justify-center mb-4">
				<button
					class="bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-8 rounded-full font-medium text-sm transition"
					on:click={handleCreateSupport}
				>
					{$i18n.t('Create My support')}
				</button>
			</div>

			<div class="flex items-center justify-center gap-2">
				<input
					type="checkbox"
					id="dontShowDash"
					bind:checked={dontShowAgain}
					class="h-3 w-3 text-indigo-600 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded"
				/>
 main
				<label for="dontShowDash" class="text-xs text-gray-500 dark:text-gray-400">
					{$i18n.t("Don't show me again")}
				</label>

				<label for="dontShow" class="text-xs text-gray-500 dark:text-gray-400"
					>{$i18n.t("Don't show me again")}</label
				>
 main
			</div>
		</div>
	</div>
{/if}
 main


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
		display: flex; /* Make the card item a flex container */
	}

	.card-item > :global(*) {
		flex: 1; /* Make child components expand to fill the space */
		height: 100%; /* Ensure full height */
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
 main
