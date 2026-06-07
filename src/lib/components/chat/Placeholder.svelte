<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext, tick, createEventDispatcher } from 'svelte';
	import { fade, scale } from 'svelte/transition';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	const dispatch = createEventDispatcher();
	const i18n = getContext<Writable<i18nType>>('i18n');

	import { settings } from '$lib/stores';
	import { goto } from '$app/navigation';
	import AvatarSelection from './AvatarSelection.svelte';

	// @ts-ignore
	export let createMessagePair: Function;
	// @ts-ignore
	export let stopResponse: Function;
	// @ts-ignore
	export let autoScroll = false;
	// @ts-ignore
	export let atSelectedModel: any | undefined;
	export let selectedModels: string[] = [];
	// @ts-ignore
	export let history: any;
	// @ts-ignore
	export let prompt = '';
	// @ts-ignore
	export let files: any[] = [];
	// @ts-ignore
	export let selectedToolIds: any[] = [];
	// @ts-ignore
	export let imageGenerationEnabled = false;
	// @ts-ignore
	export let codeInterpreterEnabled = false;
	// @ts-ignore
	export let webSearchEnabled = false;
	// @ts-ignore
	export let transparentBackground = false;

	let selectedChatType =
		($settings as any)?.avatarEnabled !== undefined
			? ($settings as any).avatarEnabled
				? 'avatar'
				: 'text'
			: 'text';

	let showingAvatarSelection = false;
	let showWelcomePopup = !localStorage.getItem('welcomeCardDismissed');
	let dontShowAgain = false;

	const closeWelcomePopup = () => {
		if (dontShowAgain) {
			localStorage.setItem('welcomeCardDismissed', 'true');
		}
		showWelcomePopup = false;
		// Remove portal when closed
		const portal = document.getElementById('welcome-portal');
		if (portal) portal.remove();
	};

	onMount(() => {
		if (showWelcomePopup) {
			// Create a portal div directly on body
			const portal = document.createElement('div');
			portal.id = 'welcome-portal';
			portal.style.cssText = `
				position: fixed;
				top: 0;
				left: 0;
				width: 100vw;
				height: 100vh;
				z-index: 999999;
				background: rgba(0, 0, 0, 0.65);
				backdrop-filter: blur(4px);
				display: flex;
				align-items: center;
				justify-content: center;
			`;

			// Create the card
			const card = document.createElement('div');
			card.style.cssText = `
				background: #1f2937;
				border-radius: 1rem;
				padding: 1.5rem;
				width: 90%;
				max-width: 22rem;
				position: relative;
				box-shadow: 0 25px 50px rgba(0,0,0,0.5);
				font-family: inherit;
			`;

			card.innerHTML = `
				<button id="welcome-close-btn" style="
					position:absolute;top:0.75rem;right:1rem;
					color:#9ca3af;font-size:1.4rem;background:none;
					border:none;cursor:pointer;line-height:1;
				">&times;</button>

				<div style="display:flex;justify-content:center;margin-bottom:1.25rem;">
					<img src="/favicon.png" alt="OT Logo" style="width:4rem;height:4rem;border-radius:0.75rem;" />
				</div>

				<h2 style="text-align:center;font-size:1.1rem;font-weight:700;color:white;margin-bottom:0.25rem;">
					Welcome to OpenTutorAI!
				</h2>
				<h3 style="text-align:center;font-size:0.875rem;font-weight:600;color:white;margin-bottom:1.25rem;">
					Tips to get the most out of your AI tutor
				</h3>

				<div style="display:flex;flex-direction:column;gap:0.75rem;margin-bottom:1.5rem;">
					${[
						'Ask specific questions like "Explain recursion with an example"',
						'Ask for a summary: "Summarize this in 3 points"',
						'Say "I did not understand" to get a simpler explanation',
						'Request exercises: "Give me a practice problem"'
					].map((tip, i) => `
						<div style="display:flex;align-items:center;gap:0.75rem;">
							<div style="
								flex-shrink:0;background:#4F46E5;color:white;
								border-radius:50%;width:1.5rem;height:1.5rem;
								display:flex;align-items:center;justify-content:center;
								font-weight:700;font-size:0.75rem;
							">${i + 1}</div>
							<span style="font-size:0.875rem;color:#e5e7eb;">${tip}</span>
						</div>
					`).join('')}
				</div>

				<button id="welcome-start-btn" style="
					width:100%;background:#4F46E5;color:white;
					padding:0.625rem 2rem;border-radius:9999px;
					font-weight:600;font-size:0.875rem;border:none;
					cursor:pointer;margin-bottom:1rem;
					transition:background 0.2s;
				">Start Learning</button>

				<div style="display:flex;align-items:center;justify-content:center;gap:0.5rem;">
					<input type="checkbox" id="welcome-dont-show"
						style="width:0.75rem;height:0.75rem;accent-color:#6366f1;" />
					<label for="welcome-dont-show"
						style="font-size:0.75rem;color:#9ca3af;cursor:pointer;">
						Don't show me again
					</label>
				</div>
			`;

			portal.appendChild(card);
			document.body.appendChild(portal);

			// Add event listeners
			document.getElementById('welcome-close-btn')?.addEventListener('click', () => {
				const checked = (document.getElementById('welcome-dont-show') as HTMLInputElement)?.checked;
				if (checked) localStorage.setItem('welcomeCardDismissed', 'true');
				portal.remove();
				showWelcomePopup = false;
			});

			document.getElementById('welcome-start-btn')?.addEventListener('click', () => {
				const checked = (document.getElementById('welcome-dont-show') as HTMLInputElement)?.checked;
				if (checked) localStorage.setItem('welcomeCardDismissed', 'true');
				portal.remove();
				showWelcomePopup = false;
			});

			// Hover effect on start button
			const startBtn = document.getElementById('welcome-start-btn');
			if (startBtn) {
				startBtn.addEventListener('mouseover', () => startBtn.style.background = '#4338CA');
				startBtn.addEventListener('mouseout', () => startBtn.style.background = '#4F46E5');
			}
		}

		return () => {
			const portal = document.getElementById('welcome-portal');
			if (portal) portal.remove();
		};
	});

	const startChat = async (type: 'text' | 'avatar') => {
		selectedChatType = type;

		if (selectedModels.length === 0 || selectedModels.every(model => !model || model === '')) {
			toast.error($i18n.t('Please select a model before starting a chat'));
			return;
		}

		if (typeof window !== 'undefined' && window.sessionStorage) {
			window.sessionStorage.setItem('selectedModels', JSON.stringify(selectedModels));
		}

		if (type === 'text') {
			settings.update((s) => {
				const updatedSettings = { ...s };
				(updatedSettings as any).avatarEnabled = false;
				return updatedSettings;
			});
			localStorage.setItem('settings', JSON.stringify($settings));
			await tick();
			dispatch('submit', 'Hello');
		} else {
			settings.update((s) => {
				const updatedSettings = { ...s };
				(updatedSettings as any).avatarEnabled = true;
				return updatedSettings;
			});
			localStorage.setItem('settings', JSON.stringify($settings));
			showingAvatarSelection = true;
		}
	};

	const handleAvatarSelected = async (event: { detail: { avatarId: string } }) => {
		await tick();

		if (selectedModels.length === 0 || selectedModels.every(model => !model || model === '')) {
			toast.error($i18n.t('A model must be selected before starting the chat'));
			showingAvatarSelection = false;
			if (typeof window !== 'undefined' && window.localStorage) {
				window.localStorage.removeItem('pendingSupportData');
			}
			return;
		}

		try {
			dispatch('submit', 'Hello');
		} catch (error) {
			console.error('Error starting chat with avatar:', error);
			toast.error($i18n.t('Failed to start avatar chat. Please try again.'));
			if (typeof window !== 'undefined' && window.localStorage) {
				window.localStorage.removeItem('pendingSupportData');
			}
		}

		setTimeout(() => {
			if (history && !history.currentId) {
				if (typeof window !== 'undefined' && window.localStorage) {
					window.localStorage.removeItem('pendingSupportData');
				}
				goto('/');
			}
		}, 300);
	};

	const handleAvatarSelectionBack = () => {
		showingAvatarSelection = false;
	};

	const handleKeydown = (event: KeyboardEvent, type: 'text' | 'avatar') => {
		if (event.key === 'Enter' || event.key === ' ') {
			startChat(type);
		}
	};
</script>

{#if showingAvatarSelection}
	<AvatarSelection on:select={handleAvatarSelected} on:back={handleAvatarSelectionBack} />
{:else}
	<div class="page-container">
		<div class="content-wrapper">
			<div
				class="max-w-5xl w-full px-4 py-6 md:py-10"
				in:scale={{ duration: 400, start: 0.95, opacity: 0 }}
			>
				<div class="text-center mb-6 md:mb-8">
					<h1 class="text-2xl sm:text-3xl md:text-4xl font-bold mb-3 md:mb-4 text-gray-800 dark:text-white tracking-tight">
						{$i18n.t('Choose Your Experience')}
					</h1>
					<p class="text-sm md:text-base text-gray-600 dark:text-gray-300 max-w-lg mx-auto">
						{$i18n.t('Select the type of chat experience you prefer. You can change this anytime from the settings.')}
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
						<div class="relative p-5 md:p-6 flex flex-col items-center text-center h-full">
							<div class="mb-4 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 p-3 md:p-5 w-16 h-16 md:w-20 md:h-20 flex items-center justify-center">
								<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 md:h-10 md:w-10 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
									<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
								</svg>
							</div>
							<h2 class="text-xl md:text-2xl font-bold text-gray-800 dark:text-white mb-2">{$i18n.t('Text Chat')}</h2>
							<p class="text-sm text-gray-600 dark:text-gray-300 mb-4 md:mb-6">{$i18n.t('Standard text-based conversation with advanced AI capabilities')}</p>
							<ul class="text-left text-gray-600 dark:text-gray-300 space-y-2 mt-auto text-sm">
								<li class="flex items-center">
									<svg class="w-4 h-4 md:w-5 md:h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
									</svg>
									{$i18n.t('Fast responses')}
								</li>
								<li class="flex items-center">
									<svg class="w-4 h-4 md:w-5 md:h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
									</svg>
									{$i18n.t('Resource-efficient')}
								</li>
								<li class="flex items-center">
									<svg class="w-4 h-4 md:w-5 md:h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
									</svg>
									{$i18n.t('Code blocks support')}
								</li>
							</ul>
							<div class="mt-5 md:mt-6 w-full">
								<button class="w-full py-3 px-6 rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium transition-all hover:shadow-lg hover:shadow-blue-500/30 focus:outline-none focus:ring-2 focus:ring-blue-500">
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
						<div class="relative p-5 md:p-6 flex flex-col items-center text-center h-full">
							<div class="mb-4 rounded-full bg-gradient-to-br from-purple-400 to-purple-600 p-3 md:p-5 w-16 h-16 md:w-20 md:h-20 flex items-center justify-center">
								<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 md:h-10 md:w-10 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
									<path d="M12 2a5 5 0 0 0-5 5v2a5 5 0 0 0 10 0V7a5 5 0 0 0-5-5zm-9 16v-1a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v1"></path>
									<circle cx="12" cy="10" r="3"></circle>
								</svg>
							</div>
							<h2 class="text-xl md:text-2xl font-bold text-gray-800 dark:text-white mb-2">{$i18n.t('Avatar Chat')}</h2>
							<p class="text-sm text-gray-600 dark:text-gray-300 mb-4 md:mb-6">{$i18n.t('Interactive 3D avatar with speech and dynamic animations')}</p>
							<ul class="text-left text-gray-600 dark:text-gray-300 space-y-2 mt-auto text-sm">
								<li class="flex items-center">
									<svg class="w-4 h-4 md:w-5 md:h-5 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
									</svg>
									{$i18n.t('Realistic animations')}
								</li>
								<li class="flex items-center">
									<svg class="w-4 h-4 md:w-5 md:h-5 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
									</svg>
									{$i18n.t('Natural voice synthesis')}
								</li>
								<li class="flex items-center">
									<svg class="w-4 h-4 md:w-5 md:h-5 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
									</svg>
									{$i18n.t('Immersive experience')}
								</li>
							</ul>
							<div class="mt-5 md:mt-6 w-full">
								<button class="w-full py-3 px-6 rounded-lg bg-gradient-to-r from-purple-500 to-purple-600 text-white font-medium transition-all hover:shadow-lg hover:shadow-purple-500/30 focus:outline-none focus:ring-2 focus:ring-purple-500">
									{$i18n.t('Start Avatar Chat')}
								</button>
							</div>
						</div>
					</div>
				</div>

				<div class="mt-6 md:mt-8 text-center">
					<p class="text-xs md:text-sm text-gray-500 dark:text-gray-400">
						{$i18n.t('Your chat selection will determine how the AI presents information to you. You can switch between these modes at any time using the settings panel.')}
					</p>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.page-container {
		height: 100%;
		width: 100%;
		display: flex;
		justify-content: center;
		overflow-y: auto;
		overflow-x: hidden;
	}

	.content-wrapper {
		width: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: flex-start;
		padding: 0.5rem 0;
	}

	@media (min-height: 700px) {
		.content-wrapper {
			padding: 2rem 0;
		}
	}

	@media (max-height: 500px) {
		.page-container {
			padding-top: 0.5rem;
		}
	}
</style>