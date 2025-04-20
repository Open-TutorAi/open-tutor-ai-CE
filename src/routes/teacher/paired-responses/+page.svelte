<script lang="ts">
	import PairedResponses from '$lib/components/chat/PairedResponses.svelte';
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	const i18n = getContext<Writable<i18nType>>('i18n');
</script>

<div class="h-full overflow-auto">
	<div class="flex flex-col gap-8 w-full max-w-5xl mx-auto px-4 py-8">
		<PairedResponses />
	</div>
</div>

<style>
	/* Ensure the page takes full height */
	:global(html, body) {
		height: 100%;
	}
	
	:global(#app) {
		height: 100%;
	}
	
	/* Enable smooth scrolling */
	.h-full {
		height: 100%;
	}
	
	.overflow-auto {
		-webkit-overflow-scrolling: touch;
	}
</style>
