<script>
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
    import { onMount, getContext } from 'svelte';


	let loading = true;
	let error = null;
    const i18n = getContext('i18n');


	onMount(async () => {
		try {
			loading = true;

			if (!$user) {
				console.log('No user found, redirecting to auth page');
				goto('/auth');
				return;
			}

			console.log('Current user role:', $user.role);

			// Allow access to teachers
			if ($user.role !== 'teacher') {
				console.log('User is not a teacher, redirecting to home');
				await goto(`/${$user.role}`);
				return;
			}else{
       			await goto(`/teacher/dashboard`);
     		}

			// User has the correct role, continue loading the page
			loading = false;
		} catch (err) {
			console.error('Error in teacher page:', err);
			error = err.message || 'An error occurred';
			loading = false;
		}
	});
</script>
