<!-- chat/+page.svelte -->
<script lang="ts">
	import Chat from '$lib/components/student/tutor/Chat.svelte';
	import RightBar from '$lib/components/student/elements/RightBar.svelte';
	import { page } from '$app/stores';
	import { onMount, onDestroy } from 'svelte';

	let isRightBarVisible = false;
	let courseCompletion = 0;
	let intervalId: ReturnType<typeof setInterval>;

	// Get chat ID from URL
	$: chatId = $page.params.id ?? '';

	// Calculate progress based on number of messages in the chat
	const calculateProgress = () => {
		if (!chatId) return;
		try {
			// Read chat from localStorage (Open WebUI stores chats there)
			const chats = JSON.parse(localStorage.getItem('chats') ?? '{}');
			const chat = chats[chatId];
			if (chat?.messages) {
				const msgCount = Object.keys(chat.messages).length;
				courseCompletion = Math.min(msgCount * 5, 100);
			} else {
				// Fallback: count from chat history stored by Open WebUI
				const allKeys = Object.keys(localStorage);
				const chatKey = allKeys.find(k => k.includes(chatId));
				if (chatKey) {
					const data = JSON.parse(localStorage.getItem(chatKey) ?? '{}');
					const msgCount = data?.messages ? Object.keys(data.messages).length : 0;
					courseCompletion = Math.min(msgCount * 5, 100);
				}
			}
		} catch (e) {
			console.error('Progress calculation error:', e);
		}
	};

	onMount(() => {
		calculateProgress();
		// Poll every 3 seconds to update progress as messages arrive
		intervalId = setInterval(calculateProgress, 3000);
	});

	onDestroy(() => {
		clearInterval(intervalId);
	});

	function toggleRightBar() {
		isRightBarVisible = !isRightBarVisible;
	}
</script>

<div class="chat-layout flex h-full overflow-hidden relative bg-white dark:bg-gray-900 p-2">
	<div class="chat-container flex-1 h-full overflow-hidden bg-[#F5F7F9] dark:bg-gray-900 rounded-2xl shadow-sm mr-2">
		<Chat chatIdProp={$page.params.id} />

		<button
			class="toggle-rightbar hidden max-[1210px]:block fixed right-4 bottom-4 bg-blue-500 hover:bg-blue-600 text-white rounded-full p-2 shadow-lg z-99999"
			on:click={toggleRightBar}
			aria-label={isRightBarVisible ? 'Hide sidebar' : 'Show sidebar'}
		>
			<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-4 h-4">
				{#if isRightBarVisible}
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				{:else}
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
				{/if}
			</svg>
		</button>
	</div>

	<div
		class="rightbar-container h-full w-80 bg-[#F5F7F9] dark:bg-gray-900 rounded-2xl shadow-sm overflow-y-auto transition-transform duration-300 ease-in-out"
		class:mobile-visible={isRightBarVisible}
	>
		<RightBar {courseCompletion} />
	</div>
</div>

<style>
	.chat-layout {
		height: 100%;
		width: 100%;
	}

	.chat-container, .rightbar-container {
		height: 100%;
	}

	@media (max-width: 1210px) {
		.rightbar-container {
			position: fixed;
			right: -320px;
			top: 0;
			bottom: 0;
			z-index: 9999;
			background: var(--background-color, #ffffff);
			backdrop-filter: blur(8px);
			transition: transform 0.3s ease-in-out;
			border-left: 1px solid rgba(229, 231, 235, 0.1);
		}

		.rightbar-container.mobile-visible {
			transform: translateX(-320px);
		}

		:global(.dark) .rightbar-container {
			--background-color: rgba(31, 41, 55, 0.95);
		}
	}

	@media (min-width: 1211px) {
		.rightbar-container {
			position: relative;
			right: 0;
		}
	}

	.toggle-rightbar {
		transition: transform 0.3s ease-in-out;
	}

	.toggle-rightbar:hover {
		transform: scale(1.1);
	}
</style>