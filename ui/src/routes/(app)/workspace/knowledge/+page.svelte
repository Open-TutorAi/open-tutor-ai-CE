<script>
	import { onMount } from 'svelte';
	import { knowledge } from '$lib/stores';

	import { getKnowledgeBases } from '$lib/apis/knowledge';
	import Knowledge from '$lib/features/workspace/components/Knowledge.svelte';

	onMount(async () => {
		await Promise.all([
			(async () => {
				knowledge.set(await getKnowledgeBases(localStorage.token));
			})()
		]);
	});
</script>

{#if $knowledge !== null}
	<Knowledge />
{/if}
