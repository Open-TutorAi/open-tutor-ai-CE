<!-- chat/+layout.svelte -->
<script lang="ts">
	import { onMount } from 'svelte';
		
	onMount(() => {
		// Ensure container elements have proper overflow handling
		document.body.style.overflow = 'hidden';
	});
</script>

<!-- Chat Layout Container -->
<div class="chat-layout-container h-full w-full flex flex-col overflow-hidden">
	<!-- Slot for chat page content -->
	<slot />
</div>

<style>
	.chat-layout-container {
		/* Ensure this container fills available space and handles overflow properly */
		height: 100%;
		max-height: 100%;
		width: 100%;
		position: relative;
	}
	
	/* Add global styles to ensure proper layout behavior */
	:global(.chat-container) {
		overflow: hidden !important;
		display: flex !important;
		flex-direction: column !important;
	}
	
	/* Ensure scroll areas are properly contained */
	:global(#messages-container) {
		overflow-y: auto !important;
		flex: 1 !important;
		scrollbar-width: thin;
	}
	
	/* Ensure the navbar is always visible on top */
	:global(.chat-navbar) {
		position: sticky !important;
		top: 0 !important;
		z-index: 40 !important;
	}
	
	/* Style scrollbars to be less obtrusive */
	:global(::-webkit-scrollbar) {
		width: 5px;
		height: 5px;
	}
	
	:global(::-webkit-scrollbar-thumb) {
		background-color: rgba(156, 163, 175, 0.5);
		border-radius: 3px;
	}
</style>