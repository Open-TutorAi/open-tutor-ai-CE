<script lang="ts">
	import { page } from '$app/stores';
	import StudentProgress from '$lib/components/teacher/pages/StudentProgress.svelte';
</script>

<StudentProgress classId={$page.params.id} studentId={$page.params.sid} />
