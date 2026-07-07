<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';

    let path: any = null;
    let currentChapter = 0;
    let progress = 0;
    let showQuiz = false;
    let quizAnswers: number[] = [];
    let quizSubmitted = false;

    onMount(() => {
        const stored = localStorage.getItem('currentPath');
        if (stored) {
            path = JSON.parse(stored);
            updateProgress();
        } else {
            goto('/student/paths/create');
        }
    });

    function updateProgress() {
        if (path && path.chapters) {
            progress = ((currentChapter + 1) / path.chapters.length) * 100;
        }
    }

    function nextChapter() {
        if (path && currentChapter < path.chapters.length - 1) {
            currentChapter++;
            updateProgress();
        }
    }

    function prevChapter() {
        if (currentChapter > 0) {
            currentChapter--;
            updateProgress();
        }
    }
    function selectAnswer(questionIndex: number, answerIndex: number) {
        if (quizSubmitted) return;
        quizAnswers[questionIndex] = answerIndex;
    }

    function submitQuiz() {
        quizSubmitted = true;
        
        // Calculer le score
        let score = 0;
        const quiz = path.chapters[currentChapter].quiz;
        quiz.forEach((q: any, i: number) => {
            if (quizAnswers[i] === q.correct) {
                score++;
            }
        });
        
        // Sauvegarder le résultat
        const quizResults = JSON.parse(localStorage.getItem('quizResults') || '{}');
        const chapterId = path.chapters[currentChapter].id;
        quizResults[`${path.id}_chapter_${chapterId}`] = {
            score: score,
            total: quiz.length,
            percentage: (score / quiz.length) * 100,
            date: new Date().toISOString()
        };
        localStorage.setItem('quizResults', JSON.stringify(quizResults));
    }

    function getScore() {
        if (!quizSubmitted) return 0;
        let score = 0;
        const quiz = path.chapters[currentChapter].quiz;
        quiz.forEach((q: any, i: number) => {
            if (quizAnswers[i] === q.correct) score++;
        });
        return score;
    }

    function getPercentage() {
        if (!quizSubmitted) return 0;
        const quiz = path.chapters[currentChapter].quiz;
        return ((getScore() / quiz.length) * 100).toFixed(0);
    }

    function resetQuiz() {
        quizAnswers = [];
        quizSubmitted = false;
    }
</script>

{#if path}
    <div class="max-w-4xl mx-auto p-6">
        <!-- Header -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-8 mb-6">
            <div class="flex items-start justify-between mb-4">
                <div>
                    <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        {path.title}
                    </h1>
                    <p class="text-gray-600 dark:text-gray-400">
                        {path.description}
                    </p>
                </div>
                <button
                    on:click={() => goto('/student/paths')}
                    class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                    ← Retour
                </button>
            </div>

            <!-- Progress bar -->
            <div class="mt-6">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Progression
                    </span>
                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {currentChapter + 1} / {path.chapters.length}
                    </span>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                    <div
                        class="bg-gradient-to-r from-blue-500 to-indigo-600 h-2.5 rounded-full transition-all duration-300"
                        style="width: {progress}%"
                    ></div>
                </div>
            </div>
        </div>

        <!-- Chapter content -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-8">
            <div class="mb-6">
                <div class="flex items-center gap-3 mb-4">
                    <div class="flex items-center justify-center w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-300 font-bold">
                        {path.chapters[currentChapter].id}
                    </div>
                    <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
                        {path.chapters[currentChapter].title}
                    </h2>
                </div>
                <p class="text-gray-700 dark:text-gray-300 leading-relaxed text-lg whitespace-pre-wrap ">
                      {path.chapters[currentChapter].content}
                </p>
            </div>
                               <!-- Quiz Section - Affichée à la fin du chapitre -->
                {#if path.chapters[currentChapter].quiz && path.chapters[currentChapter].quiz.length > 0}
                    <div class="mt-8 pt-8 border-t-2 border-gray-200 dark:border-gray-700">
                        <div class="flex items-center gap-3 mb-6">
                            <div class="flex items-center justify-center w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/50 text-purple-600 dark:text-purple-300 font-bold">
                                📝
                            </div>
                            <h3 class="text-2xl font-bold text-gray-900 dark:text-white">
                                Quiz de validation
                            </h3>
                        </div>

                        <p class="text-gray-600 dark:text-gray-400 mb-6">
                            Teste tes connaissances sur ce chapitre en répondant à ces questions.
                        </p>

                        {#if !quizSubmitted}
                            <!-- Questions -->
                            <div class="space-y-6">
                                {#each path.chapters[currentChapter].quiz as question, qIndex}
                                    <div class="p-5 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-700">
                                        <h4 class="font-semibold text-gray-900 dark:text-white mb-4">
                                            Question {qIndex + 1}: {question.question}
                                        </h4>
                                        <div class="space-y-3">
                                            {#each question.options as option, oIndex}
                                                <button
                                                    on:click={() => selectAnswer(qIndex, oIndex)}
                                                    class="w-full text-left p-4 rounded-lg border-2 transition-all {quizAnswers[qIndex] === oIndex 
                                                        ? 'border-purple-500 dark:border-purple-400 bg-purple-50 dark:bg-purple-900/20' 
                                                        : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-purple-300 dark:hover:border-purple-600'}"
                                                >
                                                    <span class="font-medium text-gray-700 dark:text-gray-300">
                                                        {String.fromCharCode(65 + oIndex)}. {option}
                                                    </span>
                                                </button>
                                            {/each}
                                        </div>
                                    </div>
                                {/each}
                            </div>

                            <!-- Submit Button -->
                            <div class="mt-6 flex justify-end">
                                <button
                                    on:click={submitQuiz}
                                    disabled={quizAnswers.length < path.chapters[currentChapter].quiz.length}
                                    class="px-8 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl font-medium hover:from-purple-700 hover:to-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
                                >
                                    ✓ Valider mes réponses
                                </button>
                            </div>
                        {:else}
                            <!-- Results -->
                            <div class="p-8 bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-2xl border-2 border-purple-200 dark:border-purple-800">
                                <div class="text-center mb-6">
                                    <div class="text-6xl mb-4">
                                        {#if getPercentage() >= 80}🎉
                                        {:else if getPercentage() >= 60}👍
                                        {:else}📚{/if}
                                    </div>
                                    
                                    <h4 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                                        {#if getPercentage() >= 80}Excellent travail !
                                        {:else if getPercentage() >= 60}Bien joué !
                                        {:else}Continue tes efforts !{/if}
                                    </h4>
                                    
                                    <div class="text-5xl font-bold text-purple-600 dark:text-purple-400 mb-2 mt-4">
                                        {getScore()} / {path.chapters[currentChapter].quiz.length}
                                    </div>
                                    
                                    <div class="text-xl text-gray-600 dark:text-gray-400">
                                        {getPercentage()}% de bonnes réponses
                                    </div>
                                </div>

                                <!-- Progress bar -->
                                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 mb-6">
                                    <div
                                        class="bg-gradient-to-r from-purple-500 to-indigo-600 h-4 rounded-full transition-all duration-500"
                                        style="width: {getPercentage()}%"
                                    ></div>
                                </div>

                                <!-- Show correct/incorrect answers -->
                                <div class="space-y-3 mb-6">
                                    {#each path.chapters[currentChapter].quiz as question, qIndex}
                                        <div class="p-3 rounded-lg {quizAnswers[qIndex] === question.correct 
                                            ? 'bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700' 
                                            : 'bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700'}">
                                            <p class="font-medium text-sm">
                                                Question {qIndex + 1}: {quizAnswers[qIndex] === question.correct ? '✓ Correcte' : '✗ Incorrecte'}
                                            </p>
                                            {#if quizAnswers[qIndex] !== question.correct}
                                                <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                                    Bonne réponse : {question.options[question.correct]}
                                                </p>
                                            {/if}
                                        </div>
                                    {/each}
                                </div>

                                <!-- Actions -->
                                <div class="flex justify-center gap-4">
                                    <button
                                        on:click={resetQuiz}
                                        class="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-xl font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-all"
                                    >
                        🔄 Refaire le quiz
                                    </button>
                                    {#if getPercentage() >= 60 && currentChapter < path.chapters.length - 1}
                                        <button
                                            on:click={() => {
                                                nextChapter();
                                                resetQuiz();
                                            }}
                                            class="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-indigo-700 transition-all"
                                        >
                                            Chapitre suivant →
                                        </button>
                                    {/if}
                                </div>
                            </div>
                        {/if}
                    </div>
                {/if} 

            <!-- Navigation buttons -->
            <div class="flex justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                <button
                    on:click={prevChapter}
                    disabled={currentChapter === 0}
                    class="px-6 py-3 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-xl font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    ← Chapitre précédent
                </button>
                               {#if currentChapter === path.chapters.length - 1}
                    <button
                        on:click={() => {
                            // Option 1: Rediriger vers la page des parcours
                            goto('/student/paths');
                            
                            // Option 2: Afficher une alerte de félicitations
                            alert('🎉 Félicitations ! Vous avez terminé ce cours !');
                        }}
                        class="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl font-medium hover:from-green-700 hover:to-emerald-700 transition-all"
                    >
                        ✓ Terminer le cours
                    </button>
                {:else}
                    <button
                        on:click={nextChapter}
                        class="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-indigo-700 transition-all"
                    >
                        Chapitre suivant →
                    </button>
                {/if}
            </div>
        </div>
    </div>
{:else}
    <div class="max-w-4xl mx-auto p-6 text-center">
        <div class="animate-pulse">
            <div class="h-8 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mx-auto"></div>
        </div>
    </div>
{/if}

