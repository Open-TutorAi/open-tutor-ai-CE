<script lang="ts">
	import { getContext } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	
	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();
	
	function exitDemo() {
		dispatch('toggle');
	}
</script>

<div class="demo-banner bg-gradient-to-r from-amber-500 to-orange-500 text-white px-4 py-2 flex items-center justify-between shadow-md">
	<div class="flex items-center gap-2">
		<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
			<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
		</svg>
		<span class="text-sm font-medium">
			{$i18n.t('Demo Mode Active - Exploring with sample data')}
		</span>
	</div>
	
	<button
		on:click={exitDemo}
		class="text-sm font-medium hover:text-gray-100 transition-colors px-3 py-1 rounded-md hover:bg-white/10"
	>
		{$i18n.t('Exit Demo')}
	</button>
</div>

<style>
	.demo-banner {
		position: sticky;
		top: 0;
		z-index: 40;
		animation: slideDown 0.3s ease-out;
	}
	
	@keyframes slideDown {
		from {
			transform: translateY(-100%);
			opacity: 0;
		}
		to {
			transform: translateY(0);
			opacity: 1;
		}
	}
</style>

