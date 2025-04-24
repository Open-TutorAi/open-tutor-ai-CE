<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext, tick, createEventDispatcher } from 'svelte';
	import { fade, scale } from 'svelte/transition';

	const dispatch = createEventDispatcher();

	// Get i18n from context with proper typing to fix the linter errors
	interface I18nContext {
		t?: (key: string) => string;
	}
	const i18n: I18nContext = getContext('i18n') || {};

	// Safe translation function to handle cases where i18n.t might not be available
	function t(key: string): string {
		if (i18n && typeof i18n.t === 'function') {
			return i18n.t(key);
		}
		// Fallback to the key itself if translation is not available
		return key;
	}

	import { settings, user } from '$lib/stores';
	import { goto } from '$app/navigation';
	import AvatarSelection from '../tutor/AvatarSelection.svelte';

	// Props that must be kept for component compatibility
	export let createMessagePair: Function;
	export let stopResponse: Function;
	export let autoScroll = false;
	export let atSelectedModel: any | undefined;
	export let selectedModels: [''];
	export let history: any;
	export let prompt = '';
	export let files: any[] = [];
	export let selectedToolIds: any[] = [];
	export let imageGenerationEnabled = false;
	export let codeInterpreterEnabled = false;
	export let webSearchEnabled = false;
	export let transparentBackground = false;

	// State for chat type selection - use type assertion to avoid TS errors
	let selectedChatType =
		($settings as any)?.avatarEnabled !== undefined
			? ($settings as any).avatarEnabled
				? 'avatar'
				: 'text'
			: 'text';

	// Add state to track if we're showing avatar selection
	let showingAvatarSelection = false;

	// Function to set chat type preference and start chat
	const startChat = async (type: 'text' | 'avatar') => {
		selectedChatType = type;

		if (type === 'text') {
			// For text chat, update settings and start immediately
			settings.update((s) => {
				const updatedSettings = { ...s };
				(updatedSettings as any).avatarEnabled = false;
				return updatedSettings;
			});

			// Save settings to localStorage for persistence
			localStorage.setItem('settings', JSON.stringify($settings));

			// Notify user of the selection
			toast.success('Text-only chat enabled');

			// Force UI update before submitting
			await tick();

			// Send a default prompt to initialize the chat
			const initialPrompt = 'Hello';
			dispatch('submit', initialPrompt);
		} else {
			// For avatar chat, show the avatar selection screen
			showingAvatarSelection = true;
		}
	};

	// Handle avatar selection completion
	const handleAvatarSelected = async (event: { detail: { avatarId: string } }) => {
		// Avatar selection already updated settings, now initialize chat
		await tick();

		// Send a default prompt to initialize the chat with the selected avatar
		const initialPrompt = 'Hello';
		dispatch('submit', initialPrompt);

		// Fallback navigation if chat doesn't initialize
		setTimeout(() => {
			if (history && !history.currentId) {
				goto('/');
			}
		}, 300);
	};

	// Handle going back from avatar selection to chat type selection
	const handleAvatarSelectionBack = () => {
		showingAvatarSelection = false;
	};

	// Handle keyboard navigation
	const handleKeydown = (event: KeyboardEvent, type: 'text' | 'avatar') => {
		if (event.key === 'Enter' || event.key === ' ') {
			startChat(type);
		}
	};
</script>

{#if showingAvatarSelection}
	<!-- Show avatar selection screen -->
	<AvatarSelection on:select={handleAvatarSelected} on:back={handleAvatarSelectionBack} />
{:else}
	<!-- Chat type selection screen with improved centering -->
	<div class="page-container">
		<div class="content-wrapper">
			<div
				class="max-w-5xl w-full px-4 py-6 md:py-10"
				in:scale={{ duration: 400, start: 0.95, opacity: 0 }}
			>
				<div class="text-center mb-6 md:mb-8">
					<h1
						class="text-2xl sm:text-3xl md:text-4xl font-bold mb-3 md:mb-4 text-gray-800 dark:text-white tracking-tight"
					>
						{$i18n.t('Choose Your Experience')}
					</h1>
					<p class="text-sm md:text-base text-gray-600 dark:text-gray-300 max-w-lg mx-auto">
						{$i18n.t(
							'Select the type of chat experience you prefer. You can change this anytime from the settings.'
						)}
					</p>
				</div>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
					<!-- Text Chat Option -->
					<div
						class="relative bg-gray-50 dark:bg-gradient-to-br dark:from-gray-800 dark:to-gray-900 rounded-xl overflow-hidden border-2 transition-all duration-300
								{selectedChatType === 'text'
							? 'border-blue-500 shadow-lg shadow-blue-500/20'
							: 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}"
						on:click={() => startChat('text')}
						on:keydown={(e) => handleKeydown(e, 'text')}
						tabindex="0"
						role="button"
						aria-label={$i18n.t('Start text chat')}
					>
						<div
							class="absolute inset-0 bg-cover bg-center opacity-10"
							style="background-image: url('https://cdn-icons-png.flaticon.com/512/2665/2665038.png')"
						></div>

						<div class="relative p-5 md:p-6 flex flex-col items-center text-center h-full">
							<div
								class="mb-4 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 p-3 md:p-5 w-16 h-16 md:w-20 md:h-20 flex items-center justify-center"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-8 w-8 md:h-10 md:w-10 text-white"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
								>
									<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
								</svg>
							</div>
							<h2 class="text-xl md:text-2xl font-bold text-gray-800 dark:text-white mb-2">
								{$i18n.t('Text Chat')}
							</h2>
							<p class="text-sm text-gray-600 dark:text-gray-300 mb-4 md:mb-6">
								{$i18n.t('Standard text-based conversation with advanced AI capabilities')}
							</p>
							<ul class="text-left text-gray-600 dark:text-gray-300 space-y-2 mt-auto text-sm">
								<li class="flex items-center">
									<svg
										class="w-4 h-4 md:w-5 md:h-5 mr-2 text-blue-500"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 13l4 4L19 7"
										></path>
									</svg>
									{$i18n.t('Fast responses')}
								</li>
								<li class="flex items-center">
									<svg
										class="w-4 h-4 md:w-5 md:h-5 mr-2 text-blue-500"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 13l4 4L19 7"
										></path>
									</svg>
									{$i18n.t('Resource-efficient')}
								</li>
								<li class="flex items-center">
									<svg
										class="w-4 h-4 md:w-5 md:h-5 mr-2 text-blue-500"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 13l4 4L19 7"
										></path>
									</svg>
									{$i18n.t('Code blocks support')}
								</li>
							</ul>
							<div class="mt-5 md:mt-6 w-full">
								<button
									class="w-full py-3 px-6 rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium transition-all hover:shadow-lg hover:shadow-blue-500/30 focus:outline-none focus:ring-2 focus:ring-blue-500"
								>
									{$i18n.t('Start Text Chat')}
								</button>
							</div>
						</div>
					</div>

					<!-- Avatar Chat Option -->
					<div
						class="relative bg-gray-50 dark:bg-gradient-to-br dark:from-gray-800 dark:to-gray-900 rounded-xl overflow-hidden border-2 transition-all duration-300
								{selectedChatType === 'avatar'
							? 'border-purple-500 shadow-lg shadow-purple-500/20'
							: 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}"
						on:click={() => startChat('avatar')}
						on:keydown={(e) => handleKeydown(e, 'avatar')}
						tabindex="0"
						role="button"
						aria-label={$i18n.t('Start avatar chat')}
					>
						<div
							class="absolute inset-0 bg-cover bg-center opacity-10"
							style="background-image: url('https://cdn-icons-png.flaticon.com/512/4712/4712037.png')"
						></div>

						<div class="relative p-5 md:p-6 flex flex-col items-center text-center h-full">
							<div
								class="mb-4 rounded-full bg-gradient-to-br from-purple-400 to-purple-600 p-3 md:p-5 w-16 h-16 md:w-20 md:h-20 flex items-center justify-center"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-8 w-8 md:h-10 md:w-10 text-white"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
								>
									<path
										d="M12 2a5 5 0 0 0-5 5v2a5 5 0 0 0 10 0V7a5 5 0 0 0-5-5zm-9 16v-1a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v1"
									></path>
									<circle cx="12" cy="10" r="3"></circle>
								</svg>
							</div>
							<h2 class="text-xl md:text-2xl font-bold text-gray-800 dark:text-white mb-2">
								{$i18n.t('Avatar Chat')}
							</h2>
							<p class="text-sm text-gray-600 dark:text-gray-300 mb-4 md:mb-6">
								{$i18n.t('Interactive 3D avatar with speech and dynamic animations')}
							</p>
							<ul class="text-left text-gray-600 dark:text-gray-300 space-y-2 mt-auto text-sm">
								<li class="flex items-center">
									<svg
										class="w-4 h-4 md:w-5 md:h-5 mr-2 text-purple-500"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 13l4 4L19 7"
										></path>
									</svg>
									{$i18n.t('Realistic animations')}
								</li>
								<li class="flex items-center">
									<svg
										class="w-4 h-4 md:w-5 md:h-5 mr-2 text-purple-500"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 13l4 4L19 7"
										></path>
									</svg>
									{$i18n.t('Natural voice synthesis')}
								</li>
								<li class="flex items-center">
									<svg
										class="w-4 h-4 md:w-5 md:h-5 mr-2 text-purple-500"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 13l4 4L19 7"
										></path>
									</svg>
									{$i18n.t('Immersive experience')}
								</li>
							</ul>
							<div class="mt-5 md:mt-6 w-full">
								<button
									class="w-full py-3 px-6 rounded-lg bg-gradient-to-r from-purple-500 to-purple-600 text-white font-medium transition-all hover:shadow-lg hover:shadow-purple-500/30 focus:outline-none focus:ring-2 focus:ring-purple-500"
								>
									{$i18n.t('Start Avatar Chat')}
								</button>
							</div>
						</div>
					</div>
				</div>

				<!-- Footer text -->
				<div class="mt-6 md:mt-8 text-center">
					<p class="text-xs md:text-sm text-gray-500 dark:text-gray-400">
						{$i18n.t(
							'Your chat selection will determine how the AI presents information to you. You can switch between these modes at any time using the settings panel.'
						)}
					</p>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	/* Fixed layout for better visibility on all screen sizes */
	.page-container {
		height: 100vh;
		width: 100%;
		max-height: 100vh;
		overflow-y: auto;
		padding-top: 1rem; /* Add padding to ensure header is visible */
	}

	.content-wrapper {
		min-height: 100%;
		width: 100%;
		display: flex;
		align-items: flex-start; /* Start from top on small screens */
		justify-content: center;
		padding: 0.5rem 0;
	}

	/* Adjust for larger screens */
	@media (min-height: 700px) {
		.content-wrapper {
			align-items: center; /* Center on larger screens */
			padding: 2rem 0;
		}
	}

	/* Extra small screens */
	@media (max-height: 500px) {
		.page-container {
			padding-top: 0.5rem;
		}
	}
</style>
