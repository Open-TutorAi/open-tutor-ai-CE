<script lang="ts">
    import { onMount } from 'svelte';
    import i18n from '$lib/i18n';
    import { goto } from '$app/navigation';

    let myCourses: any[] = [];
    let isLoading = true;

    onMount(() => {
        loadCourses();
    });

    async function loadCourses() {
        isLoading = true;
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('http://localhost:8080/api/v1/courses/', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                myCourses = data.courses || [];
            }
        } catch (error) {
            console.error('Erreur lors du chargement des cours:', error);
        } finally {
            isLoading = false;
        }
    }

    function openCourse(courseId: number) {
        const course = myCourses.find(c => c.id === courseId);
        if (course) {
            localStorage.setItem('currentPath', JSON.stringify(course));
            goto('/student/paths/view');
        }
    }

    async function deleteCourse(courseId: number) {
        if (confirm('Voulez-vous vraiment supprimer ce cours ?')) {
            try {
                const token = localStorage.getItem('token');
                const response = await fetch(`http://localhost:8080/api/v1/courses/${courseId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    myCourses = myCourses.filter(c => c.id !== courseId);
                }
            } catch (error) {
                console.error('Erreur lors de la suppression:', error);
            }
        }
    }

    function formatDate(dateString: string) {
        if (!dateString) return '';
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

    <!-- Loading state -->
    {#if isLoading}
        <div class="text-center py-12">
            <p class="text-gray-500 dark:text-gray-400">Chargement de tes cours...</p>
        </div>
    {:else if myCourses.length === 0}
        <!-- Empty state -->
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
        <!-- Courses grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each myCourses as course}
                <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 hover:shadow-lg transition-all">
                    <div class="flex items-start justify-between mb-4">
                        <div class="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white font-bold text-lg">
                            {course.chapters ? course.chapters.length : 0}
                        </div>
                        <button
    on:click={() => deleteCourse(course.id)}
    class="p-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50 rounded-lg transition-all"
    title="{$i18n.t('Delete')}"
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
                        <span>📅 {formatDate(course.created_at)}</span>
                        <span>📖 {course.chapters ? course.chapters.length : 0} chapitres</span>
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