<!-- chat/+page.svelte -->
<script lang="ts">
	import Chat from '$lib/components/student/tutor/Chat.svelte';
	import RightBar from '$lib/components/student/elements/RightBar.svelte';
	import { page } from '$app/stores';
	import { isFullscreenAvatar } from '$lib/stores';

	let chatData = {};
	let isRightBarVisible = false;
	let sidebarOpen = true;

	function handleChatEvent(event) {
		chatData = { ...chatData, ...event.detail };
	}

	function toggleRightBar() {
		isRightBarVisible = !isRightBarVisible;
	}
</script>

<div
	class="chat-layout flex h-full overflow-hidden relative bg-white dark:bg-gray-900 {$isFullscreenAvatar ? '' : 'p-2'}"
>
	

	<!-- Main Chat component -->
	<div
		class="chat-container flex-1 h-full overflow-hidden bg-[#F5F7F9] dark:bg-gray-900 {$isFullscreenAvatar ? '' : 'rounded-2xl shadow-sm mr-2'}"
	>
		<Chat chatIdProp={$page.params.id} on:chatEvent={handleChatEvent} />

		<!-- Toggle button mobile pour RightBar -->
		{#if !$isFullscreenAvatar}
			<button
				class="toggle-rightbar hidden max-[1210px]:block fixed right-4 bottom-4 bg-blue-500 hover:bg-blue-600 text-white rounded-full p-2 shadow-lg z-99999"
				on:click={toggleRightBar}
				aria-label={isRightBarVisible ? 'Hide sidebar' : 'Show sidebar'}
			>
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-4 h-4">
					{#if isRightBarVisible}
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
					{:else}
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
					{/if}
				</svg>
			</button>
		{/if}
	</div>

	<!-- RightBar à droite - cachée en fullscreen -->
	{#if !$isFullscreenAvatar}
		<div
			class="rightbar-container h-full w-80 bg-[#F5F7F9] dark:bg-gray-900 rounded-2xl shadow-sm overflow-y-auto transition-transform duration-300 ease-in-out"
			class:mobile-visible={isRightBarVisible}
		>
			<RightBar {chatData} />
		</div>
	{/if}
</div>

<style>
	.chat-layout {
		height: 100%;
		width: 100%;
	}

	.history-sidebar-wrap {
		height: 100%;
		border-radius: 16px;
		overflow: hidden;
		flex-shrink: 0;
		box-shadow: 0 2px 8px rgba(0,0,0,0.15);
	}

	.chat-container,
	.rightbar-container {
		height: 100%;
	}

	@media (max-width: 1210px) {
		.history-sidebar-wrap {
			display: none;
		}

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