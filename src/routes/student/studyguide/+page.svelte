<!-- studyguide/+page.svelte -->
<script lang="ts">
	import StudyGuide from '$lib/components/student/pages/StudyGuide.svelte';
	import { onMount, getContext } from 'svelte';
	import { writable } from 'svelte/store';
	
	// Get the parent layout's activePage store
	const activePage = getContext('activePage');
	
	onMount(() => {
		// Set the active page to 'support' when this component mounts
		if (activePage && typeof activePage.set === 'function') {
			activePage.set('support');
		}
		
		// Clean up when component is destroyed
		return () => {
			// Optionally reset the active page when navigating away
		};
	});
</script>

<StudyGuide /> 