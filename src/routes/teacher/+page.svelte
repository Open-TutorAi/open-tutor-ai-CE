<!-- Teacher Home Page -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	onMount(() => {
		goto('/teacher/dashboard');
	});
</script>

<div class="flex items-center justify-center h-full">
	<div class="text-center">
		<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
		<p class="text-gray-600 dark:text-gray-400">Redirection vers le dashboard...</p>
	</div>
</div>

