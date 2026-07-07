<!-- chat/+page.svelte -->
<script lang="ts">
	import Chat from '$lib/components/student/tutor/Chat.svelte';
	import RightBar from '$lib/components/student/elements/RightBar.svelte';
	import ChatHistorySidebar from '$lib/components/student/elements/ChatHistorySidebar.svelte';
	import { page } from '$app/stores';
	import { isFullscreenAvatar, settings } from '$lib/stores';
	import { get } from 'svelte/store';

	let chatData = {};
	let isRightBarVisible = false;
	let sidebarKey = 0;

	$: currentChatId = $page.params.id ?? null;

	// Synchronously disable avatar BEFORE first render when loading a historical chat.
	// Using get() here (not onMount) so it runs before the component paints.
	if (typeof window !== 'undefined') {
		const _p = get(page);
		if (_p.params?.id) {
			settings.update(s => ({ ...s, avatarEnabled: false }));
			isFullscreenAvatar.set(false);
		}
	}

	function handleChatEvent(event) {
		// Process chat events and update rightbar if needed
		chatData = { ...chatData, ...event.detail };
	}

	function toggleRightBar() {
		isRightBarVisible = !isRightBarVisible;
	}

	function handleNewChat() {
		sidebarKey++;
	}
</script>

<div class="chat-layout flex h-full overflow-hidden relative bg-white dark:bg-gray-900 {$isFullscreenAvatar ? '' : 'p-2'}">

	<!-- ── Left sidebar: conversation history ── -->
	{#if !$isFullscreenAvatar}
		{#key sidebarKey}
			<ChatHistorySidebar
				{currentChatId}
				on:newChat={handleNewChat}
				on:selectChat={() => { sidebarKey++; }}
			/>
		{/key}
	{/if}

	<!-- ── Main Chat area ── -->
	<div class="chat-container flex-1 h-full overflow-hidden bg-[#F5F7F9] dark:bg-gray-900 {$isFullscreenAvatar ? '' : 'rounded-r-2xl shadow-sm mr-2'}">
		<Chat chatIdProp={$page.params.id} chatMode="quiz" on:chatEvent={handleChatEvent} />

		<!-- Toggle button for mobile - hide in fullscreen -->
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

	<!-- ── Right bar ── -->
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

	.chat-container,
	.rightbar-container {
		/* Ensure proper scroll containment */
		height: 100%;
	}

	/* Mobile styles */
	@media (max-width: 1210px) {
		.rightbar-container {
			position: fixed;
			right: -320px;
			top: 0; bottom: 0;
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
		/* Hide history sidebar on small screens */
		:global(.chat-history-sidebar) {
			display: none;
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
