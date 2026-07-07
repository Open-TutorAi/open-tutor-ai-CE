<script>
  import { page } from '$app/stores';
  import QuizReview from '$lib/features/student/components/flashcards/pages/QuizReview.svelte';
  import FlashcardReview from '$lib/features/student/components/flashcards/pages/FlashcardReview.svelte';
  
  $: tag = $page.url.searchParams.get('tag') || '';
  $: mode = $page.url.searchParams.get('mode') || 'quiz';
</script>

<svelte:head>
  <title>Révision Flashcards - Open TutorAI</title>
</svelte:head>

<div class="review-page">
  <div class="mode-switch">
    <button 
      class:active={mode === 'quiz'}
      on:click={() => {
        const url = new URL(window.location);
        url.searchParams.set('mode', 'quiz');
        window.history.pushState({}, '', url);
        mode = 'quiz';
      }}
    >
      ⌨️ Quiz
    </button>
    <button 
      class:active={mode === 'flip'}
      on:click={() => {
        const url = new URL(window.location);
        url.searchParams.set('mode', 'flip');
        window.history.pushState({}, '', url);
        mode = 'flip';
      }}
    >
      🔄 Flip
    </button>
  </div>
  
  {#if mode === 'quiz'}
    <QuizReview tag={tag} />
  {:else}
    <FlashcardReview tag={tag} />
  {/if}
</div>

<style>
  .review-page {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .mode-switch {
    display: flex;
    gap: 0.5rem;
    background: #f7fafc;
    padding: 0.5rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    max-width: 300px;
    margin-left: auto;
    margin-right: auto;
  }
  
  .mode-switch button {
    flex: 1;
    padding: 0.75rem;
    border: none;
    background: transparent;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    color: #4a5568;
  }
  
  .mode-switch button.active {
    background: white;
    color: #667eea;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
</style>
