<script lang="ts">
    import { page } from '$app/stores';
    import ClassroomDetail from '$lib/components/student/pages/ClassroomDetail.svelte';
</script>

<ClassroomDetail courseId={$page.params.id} />