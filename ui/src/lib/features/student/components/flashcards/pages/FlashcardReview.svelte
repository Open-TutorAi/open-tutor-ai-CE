<script>
  import { onMount } from 'svelte';
  import Flashcard from '../elements/Flashcard.svelte';
  import { getDueCards, getDueCardsByTag, reviewCard, getStats } from '$lib/apis/flashcards';
  
  export let tag = null;
  
  let token = '';
  let cards = [];
  let currentIndex = 0;
  let stats = { total: 0, mastered: 0, to_review: 0, learning: 0 };
  let loading = true;
  let error = null;
  let processing = false;
  let isFlipped = false;
  
  $: currentCard = cards[currentIndex];
  $: progress = cards.length > 0 ? ((currentIndex) / cards.length) * 100 : 0;
  
  async function loadDueCards() {
    if (!token) {
      error = 'Non authentifié';
      loading = false;
      return;
    }
    try {
      if (tag) {
        cards = await getDueCardsByTag(token, tag);
      } else {
        cards = await getDueCards(token);
      }
      currentIndex = 0;
      isFlipped = false;
    } catch (e) {
      console.error('Erreur chargement cartes:', e);
      error = 'Impossible de charger les cartes';
    } finally {
      loading = false;
    }
  }
  
  async function loadStats() {
    if (!token) return;
    try {
      stats = await getStats(token);
    } catch (e) {
      console.error('Erreur chargement stats:', e);
    }
  }
  
  function flipCard() {
    if (!processing && currentCard) {
      isFlipped = !isFlipped;
    }
  }
  
  async function answer(correct) {
    if (processing || !currentCard) return;
    
    processing = true;
    
    try {
      await reviewCard(token, currentCard.id, correct);
      
      currentIndex++;
      isFlipped = false;
      
      if (currentIndex >= cards.length) {
        await Promise.all([loadDueCards(), loadStats()]);
      }
      
    } catch (e) {
      console.error('Erreur révision:', e);
    } finally {
      processing = false;
    }
  }
  
  async function init() {
    loading = true;
    error = null;
    await Promise.all([loadDueCards(), loadStats()]);
    loading = false;
  }
  
  onMount(() => {
    token = localStorage.getItem('token') || '';
    init();
  });
</script>

<svelte:head>
  <title>Révision Flashcards {tag ? `- ${tag}` : ''} - Open TutorAI</title>
</svelte:head>

<div class="review-container">
  {#if loading}
    <div class="loading">
      <div class="spinner"></div>
      <p>Chargement de vos cartes...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <h2>⚠️ Erreur</h2>
      <p>{error}</p>
      <button on:click={init}>Réessayer</button>
    </div>
  {:else if currentCard}
    <header class="stats-bar">
      <div class="stat">
        <span class="value">{stats.mastered}</span>
        <span class="label">✅ Maîtrisées</span>
      </div>
      <div class="stat">
        <span class="value">{currentIndex + 1}/{cards.length}</span>
        <span class="label">🎯 Progression</span>
      </div>
      <div class="stat">
        <span class="value">{stats.to_review}</span>
        <span class="label">📚 À réviser</span>
      </div>
    </header>
    
    <div class="progress-bar">
      <div class="progress-fill" style="width: {progress}%"></div>
    </div>
    
    {#if tag}
      <div class="tag-badge">📁 {tag}</div>
    {/if}
    
    <div class="flashcard-wrapper" on:click={flipCard}>
      <div class="flashcard" class:flipped={isFlipped}>
        <div class="face front">
          <div class="level-badge">Niveau {currentCard.box}/5</div>
          <div class="label">QUESTION</div>
          <div class="content">{currentCard.question}</div>
          <div class="hint">Cliquez pour voir la réponse</div>
        </div>
        
        <div class="face back">
          <div class="label">RÉPONSE</div>
          <div class="content">{currentCard.answer}</div>
        </div>
      </div>
    </div>
    
    <div class="actions">
      <button 
        class="btn wrong" 
        on:click={() => answer(false)}
        disabled={processing || !isFlipped}
      >
        ❌ À revoir
      </button>
      <button 
        class="btn correct" 
        on:click={() => answer(true)}
        disabled={processing || !isFlipped}
      >
        ✅ Je sais
      </button>
    </div>
    
    {#if !isFlipped}
      <p class="instruction">💡 Cliquez sur la carte pour révéler la réponse</p>
    {/if}
    
  {:else}
    <div class="empty-state">
      <h2>🎉 Bravo !</h2>
      <p>Aucune carte à réviser {tag ? `pour ${tag}` : ''}.</p>
      <p>Générez des flashcards depuis un cours pour commencer !</p>
      <a href="/student/flashcards/generate" class="btn-primary">Générer des flashcards</a>
    </div>
  {/if}
</div>

<style>
  .review-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .loading, .error-state, .empty-state {
    text-align: center;
    padding: 3rem;
  }
  
  .spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .error-state {
    background: #fff5f5;
    border-radius: 12px;
    border: 1px solid #fc8181;
  }
  
  .error-state h2 { color: #c53030; margin-bottom: 1rem; }
  
  .error-state button {
    margin-top: 1rem;
    padding: 0.75rem 1.5rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
  }
  
  .stats-bar {
    display: flex;
    justify-content: space-around;
    padding: 1.5rem;
    background: #f7fafc;
    border-radius: 12px;
    margin-bottom: 1.5rem;
  }
  
  .stat { text-align: center; }
  .stat .value { 
    font-size: 2rem; 
    font-weight: bold; 
    display: block; 
    color: #2d3748; 
  }
  .stat .label { 
    font-size: 0.85rem; 
    color: #718096; 
  }
  
  .progress-bar {
    width: 100%;
    height: 8px;
    background: #e2e8f0;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 2rem;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    transition: width 0.3s ease;
  }
  
  .tag-badge {
    display: inline-block;
    padding: 0.4rem 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.9rem;
  }
  
  .flashcard-wrapper {
    perspective: 1000px;
    width: 100%;
    max-width: 600px;
    height: 350px;
    margin: 2rem auto;
    cursor: pointer;
  }
  
  .flashcard {
    position: relative;
    width: 100%;
    height: 100%;
    transition: transform 0.6s cubic-bezier(0.4, 0.0, 0.2, 1);
    transform-style: preserve-3d;
  }
  
  .flashcard.flipped {
    transform: rotateY(180deg);
  }
  
  .face {
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    border-radius: 20px;
    padding: 2.5rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-shadow: 0 15px 40px rgba(0,0,0,0.15);
  }
  
  .front {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }
  
  .back {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    transform: rotateY(180deg);
  }
  
  .level-badge {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: rgba(255,255,255,0.2);
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
  }
  
  .label {
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 3px;
    opacity: 0.9;
    margin-bottom: 1.5rem;
    font-weight: 600;
  }
  
  .content {
    font-size: 1.5rem;
    text-align: center;
    line-height: 1.6;
    max-width: 90%;
    font-weight: 500;
  }
  
  .hint {
    position: absolute;
    bottom: 1.5rem;
    font-size: 0.85rem;
    opacity: 0.7;
  }
  
  .actions {
    display: flex;
    gap: 1.5rem;
    justify-content: center;
    margin-top: 2.5rem;
  }
  
  .btn {
    padding: 1.2rem 2.5rem;
    border: none;
    border-radius: 16px;
    font-size: 1.1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 600;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  }
  
  .btn:hover:not(:disabled) { 
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
  }
  
  .btn:active:not(:disabled) {
    transform: translateY(-1px);
  }
  
  .btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
  
  .btn.wrong { 
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
    color: white; 
  }
  
  .btn.correct { 
    background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
    color: white; 
  }
  
  .instruction {
    text-align: center;
    margin-top: 1.5rem;
    color: #718096;
    font-size: 0.95rem;
  }
  
  .empty-state {
    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
    border-radius: 16px;
    padding: 4rem 2rem;
  }
  
  .empty-state h2 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: #2d3748;
  }
  
  .empty-state p {
    color: #718096;
    margin-bottom: 1.5rem;
    font-size: 1.1rem;
  }
  
  .btn-primary {
    display: inline-block;
    padding: 1rem 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-decoration: none;
    border-radius: 12px;
    font-weight: 600;
    transition: transform 0.2s;
  }
  
  .btn-primary:hover {
    transform: translateY(-2px);
  }
</style>
