<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';

    let myCourses: any[] = [];

    onMount(() => {
        const stored = localStorage.getItem('myCourses');
        if (stored) {
            myCourses = JSON.parse(stored);
            console.log('Cours chargés:', myCourses);
        } else {
            console.log('Aucun cours trouvé dans localStorage');
        }
    });

    function openCourse(courseId: number) {
        const course = myCourses.find(c => c.id === courseId);
        if (course) {
            localStorage.setItem('currentPath', JSON.stringify(course));
            goto('/student/paths/view');
        }
    }

    function deleteCourse(courseId: number) {
        if (confirm('Voulez-vous vraiment supprimer ce cours ?')) {
            myCourses = myCourses.filter(c => c.id !== courseId);
            localStorage.setItem('myCourses', JSON.stringify(myCourses));
        }
    }

    function formatDate(dateString: string) {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', { 
            day: 'numeric', 
            month: 'long', 
            year: 'numeric' 
        });
    }
</script>

<div class="max-w-6xl mx-auto p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
        <div>
            <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                📚 Mes cours
            </h1>
            <p class="text-gray-600 dark:text-gray-400">
                Tous les cours que tu as créés avec l'IA
            </p>
        </div>
        <button
            on:click={() => goto('/student/paths/create')}
            class="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-indigo-700 transition-all"
        >
            ➕ Créer un nouveau cours
        </button>
    </div>

    <!-- Liste des cours -->
    {#if myCourses.length === 0}
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
            <div class="text-6xl mb-4">📭</div>
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Aucun cours pour le moment
            </h2>
            <p class="text-gray-600 dark:text-gray-400 mb-6">
                Commence par créer ton premier cours avec l'IA !
            </p>
            <button
                on:click={() => goto('/student/paths/create')}
                class="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-indigo-700 transition-all"
            >
                ✨ Créer mon premier cours
            </button>
        </div>
    {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each myCourses as course}
                <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 hover:shadow-lg transition-all">
                    <div class="flex items-start justify-between mb-4">
                        <div class="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white font-bold text-lg">
                            {course.chapters.length}
                        </div>
                        <button
                            on:click={() => deleteCourse(course.id)}
                            class="text-gray-400 hover:text-red-500 transition-colors"
                            title="Supprimer"
                        >
                            🗑️
                        </button>
                    </div>
                    
                    <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2 line-clamp-2">
                        {course.title}
                    </h3>
                    
                    <p class="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-3">
                        {course.description}
                    </p>
                    
                    <div class="flex items-center justify-between text-sm text-gray-500 dark:text-gray-500 mb-4">
                        <span>📅 {formatDate(course.createdAt)}</span>
                        <span>📖 {course.chapters.length} chapitres</span>
                    </div>
                    
                    <button
                        on:click={() => openCourse(course.id)}
                        class="w-full py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-indigo-700 transition-all"
                    >
                        📖 Ouvrir le cours
                    </button>
                </div>
            {/each}
        </div>
    {/if}
</div>
