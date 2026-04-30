<!-- courses/+page.svelte -->
<script lang="ts">
	import Courses from '$lib/components/teacher/pages/Courses.svelte';
</script>

<Courses/>
<script lang="ts">
    /**
     * Importation des stores SvelteKit et des composants de page
     */
    import { page } from '$app/stores'; 
    import CourseCreation from '$lib/components/teacher/pages/CourseCreation.svelte';
    import CoursePlanEditor from '$lib/components/teacher/pages/CoursePlanEditor.svelte';

    /** * Gestion réactive de la vue actuelle :
     * On récupère le paramètre 'view' depuis l'URL (ex: ?view=plan).
     * Si le paramètre est absent, la vue par défaut est 'create'.
     */
    $: view = $page.url.searchParams.get('view') || 'create';

    /** affichage:
     * Récupération des données du cours via l'état de navigation :
     * 'courseData' contient les informations nécessaires pour l'édition du plan.
     * Si l'état est vide, la valeur par défaut est 'null'.
     */
    $: courseData = $page.state?.courseData ?? null;
</script>

{#if view === 'create'}
    <CourseCreation />

{:else if view === 'plan' && courseData}
    <CoursePlanEditor {courseData} />

{/if}
