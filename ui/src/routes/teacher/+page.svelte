<script lang="ts">
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let loading = true;

	onMount(async () => {
		if (!$user) {
			await goto('/auth');
			return;
		}
		if ($user.role !== 'teacher') {
			await goto(`/${$user.role}`);
			return;
		}
		await goto('/teacher/dashboard');
	});
</script>

{#if loading}
	<div class="flex justify-center items-center min-h-[40vh]">
		<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
	</div>
{/if}
