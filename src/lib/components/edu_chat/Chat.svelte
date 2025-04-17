<!-- src/lib/components/edu_chat/Chat.svelte -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';

	// Chat state
	let messages: Array<{ role: 'user' | 'assistant'; content: string }> = [];
	let currentMessage = '';
	let isLoading = false;

	// Add welcome message
	$: if (messages.length === 0) {
		messages = [
			{
				role: 'assistant',
				content: "Welcome to your AI tutor chat! I'm here to help you with your studies. What would you like to learn about today?"
			}
		];
	}

	// Handle sending messages
	async function handleSendMessage() {
		if (!currentMessage.trim() || isLoading) return;

		const userMessage = currentMessage.trim();
		messages = [...messages, { role: 'user', content: userMessage }];
		currentMessage = '';
		isLoading = true;

		try {
			// TODO: Implement actual chat API call
			// For now, simulate a response
			setTimeout(() => {
				messages = [
					...messages,
					{
						role: 'assistant',
						content: "I'm here to help you with your studies. What specific topic would you like to learn more about?"
					}
				];
				isLoading = false;
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
</script>

<div class="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<header class="bg-white dark:bg-gray-800 shadow-sm">
		<div class="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-xl font-semibold text-gray-900 dark:text-white">
						AI Tutor Chat
					</h1>
				</div>
				<button
					class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
					on:click={() => goto('/student')}
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
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>
		</div>
	</header>

	<!-- Chat Messages -->
	<div class="flex-1 overflow-y-auto p-4 space-y-4">
		{#each messages as message}
			<div
				class={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
			>
				<div
					class={`max-w-[80%] rounded-lg p-4 ${
						message.role === 'user'
							? 'bg-blue-500 text-white'
							: 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white'
					}`}
				>
					<p class="whitespace-pre-wrap">{message.content}</p>
				</div>
			</div>
		{/each}
		{#if isLoading}
			<div class="flex justify-start">
				<div class="bg-white dark:bg-gray-800 rounded-lg p-4">
					<div class="flex space-x-2">
						<div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
						<div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
						<div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<!-- Message Input -->
	<div class="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4">
		<div class="max-w-7xl mx-auto">
			<div class="flex space-x-4">
				<textarea
					bind:value={currentMessage}
					on:keydown={handleKeyDown}
					placeholder="Type your message..."
					class="flex-1 min-h-[50px] max-h-[200px] p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
					rows="1"
				></textarea>
				<button
					on:click={handleSendMessage}
					disabled={!currentMessage.trim() || isLoading}
					class="self-end px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-5 w-5"
						viewBox="0 0 20 20"
						fill="currentColor"
					>
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z"
							clip-rule="evenodd"
						/>
					</svg>
				</button>
			</div>
		</div>
	</div>
</div> 