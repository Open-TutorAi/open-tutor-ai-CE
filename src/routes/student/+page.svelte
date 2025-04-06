<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount, getContext } from 'svelte';
	import i18n from '$lib/i18n';

	onMount(() => {
		goto('/student/dashboard');
	});
</script>

<div class="flex items-center justify-center h-full">
	<p class="text-gray-500">{$i18n.t('Redirecting to dashboard...')}</p>
</div>
