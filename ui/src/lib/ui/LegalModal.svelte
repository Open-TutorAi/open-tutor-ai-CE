<script lang="ts">
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { fade } from 'svelte/transition';

	import { flyAndScale } from '$lib/utils/transitions';

	export let title = '';
	export let showClose = true;
	export let width = 'max-w-4xl';
	export let open = false;

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	function handleClose() {
		dispatch('close');
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && open) {
			handleClose();
		}
	}

	function handleClickOutside(e: MouseEvent) {
		if (e.target === e.currentTarget && open) {
			handleClose();
		}
	}

	onMount(() => {
		document.addEventListener('keydown', handleKeydown);
		return () => {
			document.removeEventListener('keydown', handleKeydown);
		};
	});
</script>

{#if open}
	<div 
		class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto"
		on:click={handleClickOutside}
	>
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg {width} w-full max-h-[90vh] overflow-y-auto">
			<div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
				<h3 class="text-xl font-semibold text-gray-900 dark:text-white">{title}</h3>
				{#if showClose}
				<button 
					class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
					on:click={handleClose}
					aria-label="Close"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
				{/if}
			</div>
			<div class="p-4 overflow-y-auto" style="max-height: 70vh;">
				<slot></slot>
			</div>
			<div class="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
				<button 
					class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
					on:click={handleClose}
				>
					{$i18n.t('OK')}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-content {
		animation: scaleUp 0.1s ease-out forwards;
	}

	@keyframes scaleUp {
		from {
			transform: scale(0.985);
			opacity: 0;
		}
		to {
			transform: scale(1);
			opacity: 1;
		}
	}
</style>
