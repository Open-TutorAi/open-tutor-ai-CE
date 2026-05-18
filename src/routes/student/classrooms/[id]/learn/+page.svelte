<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import Chat from '$lib/components/student/tutor/Chat.svelte';

	let courseId: string;

	onMount(() => {
		// Get course ID from URL parameter
		courseId = $page.params.id;
		
		if (!courseId) {
			// Redirect back if no course ID provided
			goto('/student/classrooms');
			return;
		}

		// Store course data in localStorage for Chat component to use
		const courseData = {
			id: courseId,
			type: 'course'
		};
		localStorage.setItem('pendingCourseData', JSON.stringify(courseData));
		
		console.log('Course learning session started:', courseData);
	});
</script>

<Chat />
