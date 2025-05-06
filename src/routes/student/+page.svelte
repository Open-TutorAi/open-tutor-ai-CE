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
        console.log("No user found, redirecting to auth page");
        await goto('/auth');
        return;
      }

      console.log("Current user role:", $user.role);
      
      // Allow access to students
      if ($user.role !== 'user') {
        console.log("User is not a student, redirecting to home");
        await goto(`/${$user.role}`);
        return;
      }else{
        await goto(`/student/dashboard`);
      }
      
      // User has the correct role, continue loading the page
      loading = false;
    } catch (err) {
      console.error("Error in student page:", err);
      error = err.message || "An error occurred";
      loading = false;
    }
  });
</script>
