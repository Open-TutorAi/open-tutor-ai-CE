<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => {
		// Redirect from /user to /student/dashboard
		console.log("Redirecting from /user to /student/dashboard");
		goto('/student/dashboard');
	});
</script>

<div class="flex justify-center items-center min-h-screen">
	<div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
</div> 