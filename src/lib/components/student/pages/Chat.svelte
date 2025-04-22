<!-- settings/+page.svelte -->
<script lang="ts">
	import Chat from '$lib/components/student/tutor/Chat.svelte';
	import RightBar from '$lib/components/student/elements/RightBar.svelte';
	import { page } from '$app/stores';
	
	let chatData = {};
	
	
	function handleChatEvent(event) {
		// Process chat events and update rightbar if needed
		chatData = {...chatData, ...event.detail};
	}
</script>

<div class="settings-layout flex h-full overflow-hidden">
	<!-- Main Chat component takes most of the space -->
	<div class="chat-container flex-1 h-full overflow-hidden">
		<Chat chatIdProp={$page.params.id} on:chatEvent={handleChatEvent} />
	</div>
	
	<!-- RightBar with fixed width -->
	<div class="rightbar-container h-full w-80 border-l border-gray-200 dark:border-gray-700 overflow-y-auto">
		<RightBar {chatData} />
	</div>
</div>

<style>
	.settings-layout {
		/* Ensure this layout container takes full height within parent */
		height: 100%;
		width: 100%;
	}
	
	.chat-container, .rightbar-container {
		/* Ensure proper scroll containment */
		height: 100%;
	}
	
	/* If responsive behavior is needed */
	@media (max-width: 768px) {
		.rightbar-container {
			display: none; /* Hide on mobile */
		}
	}
</style>