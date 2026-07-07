<script>
	import { page } from '$app/stores';
	import QuizReview from '$lib/features/student/components/flashcards/pages/QuizReview.svelte';
	import FlashcardReview from '$lib/features/student/components/flashcards/pages/FlashcardReview.svelte';
	
	$: tag = $page.url.searchParams.get('tag') || '';
	$: mode = $page.url.searchParams.get('mode') || 'quiz';
	
	function switchMode(newMode) {
		const url = new URL(window.location);
		url.searchParams.set('mode', newMode);
		window.history.pushState({}, '', url);
		mode = newMode;
	}
</script>

<svelte:head>
	<title>Révision Flashcards - Open TutorAI</title>
</svelte:head>

<div class="max-w-4xl mx-auto px-6 py-8">
	<!-- Mode Switch -->
	<div class="flex gap-2 mb-8 bg-gray-100 dark:bg-gray-900 p-2 rounded-xl max-w-md mx-auto">
		<button
			class="flex-1 py-3 px-4 rounded-lg font-semibold transition-all {mode === 'quiz' ? 'bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-sm' : 'text-gray-600 dark:text-gray-400'}"
			on:click={() => switchMode('quiz')}
		>
			⌨️ Quiz
		</button>
		<button
			class="flex-1 py-3 px-4 rounded-lg font-semibold transition-all {mode === 'flip' ? 'bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-sm' : 'text-gray-600 dark:text-gray-400'}"
			on:click={() => switchMode('flip')}
		>
			🔄 Flip
		</button>
	</div>
	
	<!-- Content -->
	{#if mode === 'quiz'}
		<QuizReview {tag} />
	{:else}
		<FlashcardReview {tag} />
	{/if}
</div>
