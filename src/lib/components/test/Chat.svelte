<!-- src/lib/components/edu_chat/Chat.svelte -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import { onMount, tick, getContext } from 'svelte';

	// Import icons (you may need to create these in your components folder)
	import XMark from '../icons/XMark.svelte';
	import Photo from '../icons/Photo.svelte';
	import Spinner from '../common/Spinner.svelte';

	// Chat state
	let messages: Array<{ role: 'user' | 'assistant'; content: string; timestamp?: Date }> = [];
	let currentMessage = '';
	let isLoading = false;
	let messagesContainerElement: HTMLDivElement;
	let autoScroll = true;
	let files = [];

	// Add welcome message
	$: if (messages.length === 0) {
		messages = [
			{
				role: 'assistant',
				content: "Welcome to your AI tutor chat! I'm here to help you with your studies. What would you like to learn about today?",
				timestamp: new Date()
			}
		];
	}

	onMount(() => {
		// Focus the input field when component is mounted
		const chatInput = document.getElementById('chat-input');
		chatInput?.focus();
		
		// Scroll to bottom on initial load
		setTimeout(() => scrollToBottom(), 0);
	});

	// Scroll to bottom function
	const scrollToBottom = () => {
		if (messagesContainerElement) {
			messagesContainerElement.scrollTop = messagesContainerElement.scrollHeight;
		}
	};

	// Keep scrolled to bottom when new messages arrive
	$: if (autoScroll && messages.length > 0) {
		tick().then(() => scrollToBottom());
	}

	// Handle sending messages
	async function handleSendMessage() {
		if (!currentMessage.trim() || isLoading) return;

		const userMessage = currentMessage.trim();
		messages = [...messages, { role: 'user', content: userMessage, timestamp: new Date() }];
		currentMessage = '';
		isLoading = true;
		
		// Auto scroll to bottom when sending message
		tick().then(() => scrollToBottom());

		try {
			// TODO: Implement actual chat API call
			// For now, simulate a response
			setTimeout(() => {
				messages = [
					...messages,
					{
						role: 'assistant',
						content: "I'm here to help you with your studies. What specific topic would you like to learn more about?",
						timestamp: new Date()
					}
				];
				isLoading = false;
				// Auto scroll to bottom when receiving message
				tick().then(() => scrollToBottom());
			}, 1000);
		} catch (error) {
			console.error('Error sending message:', error);
			isLoading = false;
		}
	}

	// Handle enter key press
	function handleKeyDown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			handleSendMessage();
		}
	}

	// Handle message container scroll
	function handleScroll() {
		if (!messagesContainerElement) return;
		const { scrollTop, scrollHeight, clientHeight } = messagesContainerElement;
		// Set autoScroll to true if we're near the bottom, false otherwise
		autoScroll = scrollHeight - scrollTop - clientHeight < 50;
	}

	// Format time
	function formatTime(date: Date | undefined): string {
		if (!date) return '';
		return new Intl.DateTimeFormat('default', {
			hour: 'numeric',
			minute: 'numeric'
		}).format(date);
	}
</script>

<div class="h-full w-full flex flex-col overflow-hidden">
	<!-- Header / Navbar -->
	<div class="w-full bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 z-10">
		<div class="flex items-center justify-between px-4 h-14">
			<div class="flex items-center space-x-4">
				<div>
					<h1 class="text-xl font-semibold text-gray-900 dark:text-white">
						Open Tutor AI
					</h1>
				</div>
			</div>

			<div class="flex items-center gap-2">
				<!-- Back Button -->
				<button
					on:click={() => goto('/student')}
					class="rounded-md p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-400"
					aria-label="Back to dashboard"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-5 w-5"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M10 19l-7-7m0 0l7-7m-7 7h18"
						/>
					</svg>
				</button>
			</div>
		</div>
	</div>

	<!-- Messages Container -->
	<div 
		bind:this={messagesContainerElement}
		on:scroll={handleScroll}
		class="flex-1 overflow-y-auto overflow-x-hidden px-4 pt-6 pb-20 bg-gray-50 dark:bg-gray-900"
		id="messages-container"
	>
		<div class="max-w-3xl mx-auto space-y-6">
			{#each messages as message, i}
				<div class={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
					{#if message.role === 'assistant'}
						<div class="flex-shrink-0 w-8 h-8 mr-2 rounded-full bg-blue-500 flex items-center justify-center">
							<span class="text-white text-sm font-medium">AI</span>
						</div>
					{/if}
					
					<div 
						class={`rounded-lg px-4 py-2 max-w-[85%] shadow-sm
							${message.role === 'user' 
								? 'bg-blue-500 text-white' 
								: 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'}`}
					>
						<div class="prose dark:prose-invert prose-sm max-w-none break-words whitespace-pre-wrap">{message.content}</div>
						<div class={`text-xs mt-1 text-right ${message.role === 'user' ? 'text-blue-200' : 'text-gray-400'}`}>
							{formatTime(message.timestamp)}
						</div>
					</div>
					
					{#if message.role === 'user'}
						<div class="flex-shrink-0 w-8 h-8 ml-2 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
							<span class="text-gray-800 dark:text-gray-200 text-sm font-medium">You</span>
						</div>
					{/if}
				</div>
			{/each}
			
			{#if isLoading}
				<div class="flex justify-start mb-4">
					<div class="flex-shrink-0 w-8 h-8 mr-2 rounded-full bg-blue-500 flex items-center justify-center">
						<span class="text-white text-sm font-medium">AI</span>
					</div>
					<div class="rounded-lg px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
						<div class="flex space-x-2 items-center h-5">
							<div class="w-2 h-2 bg-blue-500 opacity-75 rounded-full animate-bounce"></div>
							<div class="w-2 h-2 bg-blue-500 opacity-75 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
							<div class="w-2 h-2 bg-blue-500 opacity-75 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
						</div>
					</div>
				</div>
			{/if}
			
			{#if !autoScroll && messages.length > 2}
				<button
					on:click={scrollToBottom}
					class="fixed bottom-20 right-5 z-10 p-2 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600 transition-colors"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M14.707 12.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd" />
					</svg>
				</button>
			{/if}
		</div>
	</div>

	<!-- Input Area - Fixed at Bottom -->
	<div class="absolute bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-4 py-3">
		<div class="max-w-3xl mx-auto">
			<div class="relative rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 shadow-sm">
				<textarea
					id="chat-input"
					bind:value={currentMessage}
					on:keydown={handleKeyDown}
					placeholder="Type your message..."
					class="w-full resize-none py-3 px-4 pr-16 bg-transparent text-gray-900 dark:text-white focus:outline-none"
					rows="1"
					style="min-height: 44px; max-height: 120px;"
				></textarea>
				
				<div class="absolute right-2 bottom-1.5 flex">
					<button
						on:click={handleSendMessage}
						disabled={!currentMessage.trim() || isLoading}
						class="p-2 rounded-md text-blue-500 hover:bg-blue-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:pointer-events-none transition-colors"
						aria-label="Send message"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
							<path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
						</svg>
					</button>
				</div>
			</div>
		</div>
	</div>
</div>