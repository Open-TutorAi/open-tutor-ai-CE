<!-- chat/+page.svelte -->
<script lang="ts">
	import Chat from '$lib/components/tutor/Chat.svelte';
	import RightBar from '$lib/components/tutor/Rightbar.svelte';
	import { page } from '$app/stores';
	
	let chatData = {};
	let isRightBarVisible = false;
	
	function handleChatEvent(event) {
		// Process chat events and update rightbar if needed
		chatData = {...chatData, ...event.detail};
	}

	function toggleRightBar() {
		isRightBarVisible = !isRightBarVisible;
	}
</script>

<div class="chat-layout flex h-full overflow-hidden relative">
	<!-- Main Chat component takes most of the space -->
	<div class="chat-container flex-1 h-full overflow-hidden">
		<Chat chatIdProp={$page.params.id} on:chatEvent={handleChatEvent} />
		
		<!-- Toggle button for mobile -->
		<button
			class="toggle-rightbar hidden max-[1210px]:block fixed right-4 bottom-4 bg-blue-500 hover:bg-blue-600 text-white rounded-full p-2 shadow-lg z-99999"
			on:click={toggleRightBar}
			aria-label={isRightBarVisible ? 'Hide sidebar' : 'Show sidebar'}
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				class="w-4 h-4"
			>
				{#if isRightBarVisible}
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					/>
				{:else}
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M15 19l-7-7 7-7"
					/>
				{/if}
			</svg>
		</button>
	</div>
	
	<!-- RightBar with fixed width -->
	<div class="rightbar-container h-auto w-80 border-l border-gray-200 dark:border-gray-700 overflow-y-auto transition-transform duration-300 ease-in-out px-0"
		class:mobile-visible={isRightBarVisible}
	>
		<RightBar {chatData} />
	</div>
</div>

<style>
	.chat-layout {
		/* Ensure this layout container takes full height within parent */
		height: 100%;
		width: 100%;
	}
	
	.chat-container {
		/* Ensure proper scroll containment */
		height: 100%;
	}
	
	.rightbar-container {
		/* Let rightbar size to content */
		height: auto;
		width: 250px;
	}
	
	/* Mobile styles */
	@media (max-width: 1210px) {
		.rightbar-container {
			position: fixed;
			right: -320px; /* Start off-screen */
			top: 0;
			bottom: 0;
			z-index: 9999;
			transition: transform 0.3s ease-in-out;
			background: rgba(255, 255, 255, 0.2);
			backdrop-filter: blur(5px);
		}

		.rightbar-container.mobile-visible {
			transform: translateX(-320px);
		}
	}

	/* Desktop styles */
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