<script lang="ts">
    import { goto } from '$app/navigation';

    let subject = '';
    let level = 'Débutant';
    let objective = 'Comprendre les bases';
    let isGenerating = false;
    let errorMessage = '';
        let myCourses: any[] = [];
    
    import { onMount } from 'svelte';
    
    onMount(() => {
        loadCourses();
    });
    
    function loadCourses() {
        const stored = localStorage.getItem('myCourses');
        if (stored) {
            myCourses = JSON.parse(stored);
        }
    }
    
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

    const levels = ['Débutant', 'Intermédiaire', 'Avancé'];
    const objectives = ['Comprendre les bases', 'Préparer un examen', 'Construire un projet', 'Passer un entretien'];

    async function generatePath() {
        if (!subject.trim()) {
            errorMessage = 'Veuillez entrer un sujet';
            return;
        }
        
        errorMessage = '';
        isGenerating = true;
        
        try {
            // Récupérer le token
            const token = localStorage.getItem('token');
            
            console.log('Envoi de la requête...');
            console.log('Token:', token ? 'présent' : 'absent');
            
            const response = await fetch('http://localhost:8080/api/paths/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify({
                    subject: subject,
                    level: level,
                    objective: objective
                })
            });

            console.log('Réponse reçue, status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Erreur:', errorText);
                throw new Error(`Erreur ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            console.log('Données reçues:', data);
            
                        if (data.success && data.path) {
                // Sauvegarder le parcours actuel
                localStorage.setItem('currentPath', JSON.stringify(data.path));
                
                // Ajouter à la liste de tous les cours
                let myCourses = JSON.parse(localStorage.getItem('myCourses') || '[]');
                myCourses.push({
                    id: Date.now(),
                    title: data.path.title,
                    description: data.path.description,
                    chapters: data.path.chapters,
                    createdAt: new Date().toISOString()
                });
                localStorage.setItem('myCourses', JSON.stringify(myCourses));
                
                console.log('✅ Cours sauvegardé dans myCourses !');
                console.log('Nombre de cours:', myCourses.length);
                goto('/student/paths/view');
           
            } else {
                throw new Error('Réponse invalide du serveur');
            }
        } catch (error) {
            console.error('Erreur complète:', error);
            errorMessage = `Erreur: ${error.message}`;
        } finally {
            isGenerating = false;
        }
    }
</script>

<div class="max-w-3xl mx-auto p-6">
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-8">
        <!-- En-tête -->
        <div class="text-center mb-8">
            <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                Crée ton parcours personnalisé
            </h1>
            <p class="text-gray-500 dark:text-gray-400">
                L'IA va générer un cours structuré selon ton niveau et tes objectifs
            </p>
        </div>

        <!-- Message d'erreur -->
        {#if errorMessage}
            <div class="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
                <p class="text-red-600 dark:text-red-400 text-sm">{errorMessage}</p>
            </div>
        {/if}

        <div class="space-y-8">
            <!-- Champ Sujet -->
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Quel sujet veux-tu apprendre ?
                </label>
                <input 
                    type="text" 
                    bind:value={subject}
                    placeholder="Ex : Python pour débutants, Machine Learning, SQL..." 
                    class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                />
            </div>

            <!-- Sélection du niveau -->
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Ton niveau
                </label>
                <div class="flex flex-wrap gap-3">
                    {#each levels as lvl}
                        <button 
                            type="button"
                            on:click={() => level = lvl}
                            class={`px-5 py-2.5 rounded-full text-sm font-medium transition-all ${
                                level === lvl 
                                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300 border border-blue-200 dark:border-blue-700' 
                                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
                            }`}
                        >
                            {lvl}
                        </button>
                    {/each}
                </div>
            </div>

            <!-- Sélection de l'objectif -->
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Objectif principal
                </label>
                <div class="flex flex-wrap gap-3">
                    {#each objectives as obj}
                        <button 
                            type="button"
                            on:click={() => objective = obj}
                            class={`px-5 py-2.5 rounded-full text-sm font-medium transition-all ${
                                objective === obj 
                                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300 border border-blue-200 dark:border-blue-700' 
                                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
                            }`}
                        >
                            {obj}
                        </button>
                    {/each}
                </div>
            </div>

            <!-- Bouton Générer -->
            <div class="pt-4">
                <button 
                    on:click={generatePath}
                    disabled={isGenerating}
                    class="w-full py-4 bg-white dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-300 dark:border-gray-600 rounded-xl font-semibold text-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {#if isGenerating}
                        <svg class="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Génération en cours... (peut prendre 1-3 minutes)</span>
                    {:else}
                        <span>✦ Générer mon parcours avec l'IA</span>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                    {/if}
                </button>
            </div>
        </div>
    </div>
    <!-- Liste des cours créés -->
    {#if myCourses.length > 0}
        <div class="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                📚 Mes cours créés ({myCourses.length})
            </h2>
            
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
        </div>
    {/if}
</div>
