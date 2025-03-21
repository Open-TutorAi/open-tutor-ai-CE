<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext, tick, createEventDispatcher } from 'svelte';
	import { fade, scale } from 'svelte/transition';
	
	const dispatch = createEventDispatcher();
	const i18n: any = getContext('i18n');

	import { settings, user } from '$lib/stores';
	import { goto } from '$app/navigation';
	import AvatarSelection from './AvatarSelection.svelte';

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
	let selectedChatType = ($settings as any)?.avatarEnabled !== undefined ? 
		(($settings as any).avatarEnabled ? 'avatar' : 'text') : 'text';
	
	// Add state to track if we're showing avatar selection
	let showingAvatarSelection = false;

	// Function to set chat type preference and start chat
	const startChat = async (type: 'text' | 'avatar') => {
		selectedChatType = type;
		
		if (type === 'text') {
			// For text chat, update settings and start immediately
			settings.update(s => {
				const updatedSettings = {...s};
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
			const initialPrompt = "Hello";
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
		const initialPrompt = "Hello";
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
	<AvatarSelection 
		on:select={handleAvatarSelected} 
		on:back={handleAvatarSelectionBack} 
	/>
{:else}
	<!-- Chat type selection screen -->
	<div class="relative h-full w-full flex items-center justify-center bg-white dark:bg-gray-900">
		<div class="max-w-4xl w-full px-4 py-10" in:scale={{ duration: 400, start: 0.95, opacity: 0 }}>
			<div class="text-center mb-8">
				<h1 class="text-4xl font-bold mb-4 text-gray-800 dark:text-white tracking-tight">Choose Your Experience</h1>
				<p class="text-gray-600 dark:text-gray-300 max-w-lg mx-auto">Select the type of chat experience you prefer. You can change this anytime from the settings.</p>
			</div>
			
			<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
				<!-- Text Chat Option -->
				<div 
					class="relative bg-gray-50 dark:bg-gradient-to-br dark:from-gray-800 dark:to-gray-900 rounded-xl overflow-hidden border-2 transition-all duration-300 
							{selectedChatType === 'text' ? 'border-blue-500 shadow-lg shadow-blue-500/20' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}"
					on:click={() => startChat('text')}
					on:keydown={(e) => handleKeydown(e, 'text')}
					tabindex="0"
					role="button"
					aria-label="Start text chat"
				>
					<div class="absolute inset-0 bg-cover bg-center opacity-10" style="background-image: url('https://cdn-icons-png.flaticon.com/512/2665/2665038.png')"></div>
					
					<div class="relative p-8 flex flex-col items-center text-center h-full">
						<div class="mb-6 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 p-5 w-20 h-20 flex items-center justify-center">
							<svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
							</svg>
						</div>
						<h2 class="text-2xl font-bold text-gray-800 dark:text-white mb-2">Text Chat</h2>
						<p class="text-gray-600 dark:text-gray-300 mb-6">Standard text-based conversation with advanced AI capabilities</p>
						<ul class="text-left text-gray-600 dark:text-gray-300 space-y-2 mt-auto">
							<li class="flex items-center">
								<svg class="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
								</svg>
								Fast responses
							</li>
							<li class="flex items-center">
								<svg class="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
								</svg>
								Resource-efficient
							</li>
							<li class="flex items-center">
								<svg class="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
								</svg>
								Code blocks support
							</li>
						</ul>
						<div class="mt-6 w-full">
							<button 
								class="w-full py-3 px-6 rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium transition-all hover:shadow-lg hover:shadow-blue-500/30 focus:outline-none focus:ring-2 focus:ring-blue-500"
							>
								Start Text Chat
							</button>
						</div>
					</div>
				</div>
				
				<!-- Avatar Chat Option -->
				<div 
					class="relative bg-gray-50 dark:bg-gradient-to-br dark:from-gray-800 dark:to-gray-900 rounded-xl overflow-hidden border-2 transition-all duration-300 
							{selectedChatType === 'avatar' ? 'border-purple-500 shadow-lg shadow-purple-500/20' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}"
					on:click={() => startChat('avatar')}
					on:keydown={(e) => handleKeydown(e, 'avatar')}
					tabindex="0"
					role="button"
					aria-label="Start avatar chat"
				>
					<div class="absolute inset-0 bg-cover bg-center opacity-10" style="background-image: url('https://cdn-icons-png.flaticon.com/512/4712/4712037.png')"></div>
					
					<div class="relative p-8 flex flex-col items-center text-center h-full">
						<div class="mb-6 rounded-full bg-gradient-to-br from-purple-400 to-purple-600 p-5 w-20 h-20 flex items-center justify-center">
							<svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path d="M12 2a5 5 0 0 0-5 5v2a5 5 0 0 0 10 0V7a5 5 0 0 0-5-5zm-9 16v-1a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v1"></path>
								<circle cx="12" cy="10" r="3"></circle>
							</svg>
						</div>
						<h2 class="text-2xl font-bold text-gray-800 dark:text-white mb-2">Avatar Chat</h2>
						<p class="text-gray-600 dark:text-gray-300 mb-6">Interactive 3D avatar with speech and dynamic animations</p>
						<ul class="text-left text-gray-600 dark:text-gray-300 space-y-2 mt-auto">
							<li class="flex items-center">
								<svg class="w-5 h-5 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
								</svg>
								Realistic animations
							</li>
							<li class="flex items-center">
								<svg class="w-5 h-5 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
								</svg>
								Natural voice synthesis
							</li>
							<li class="flex items-center">
								<svg class="w-5 h-5 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
								</svg>
								Immersive experience
							</li>
						</ul>
						<div class="mt-6 w-full">
							<button 
								class="w-full py-3 px-6 rounded-lg bg-gradient-to-r from-purple-500 to-purple-600 text-white font-medium transition-all hover:shadow-lg hover:shadow-purple-500/30 focus:outline-none focus:ring-2 focus:ring-purple-500"
							>
								Start Avatar Chat
							</button>
						</div>
					</div>
				</div>
			</div>

			<!-- Footer text -->
			<div class="mt-8 text-center">
				<p class="text-gray-500 dark:text-gray-400 text-sm">
					Your chat selection will determine how the AI presents information to you. 
					You can switch between these modes at any time using the settings panel.
				</p>
			</div>
		</div>
	</div>
{/if}
