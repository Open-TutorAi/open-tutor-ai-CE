<script>
  import { onMount, tick } from 'svelte';
  import { getDueCards, getDueCardsByTag, reviewCard, getStats } from '$lib/apis/flashcards';
  
  export let tag = null;
  
  let token = '';
  let cards = [];
  let currentIndex = 0;
  let stats = { total: 0, mastered: 0, to_review: 0, learning: 0 };
  let loading = true;
  let error = null;
  let processing = false;
  
  // État du quiz
  let userAnswer = '';
  let showResult = false;
  let isCorrect = false;
  let showAnswer = false;
  let inputRef = null;
  
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
      await resetQuizState();
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
  
  async function resetQuizState() {
    userAnswer = '';
    showResult = false;
    isCorrect = false;
    showAnswer = false;
    processing = false;
    
    await tick();
    
    setTimeout(() => {
      if (inputRef) {
        inputRef.focus();
      }
    }, 200);
  }
  
  // ========== VALIDATION INTELLIGENTE ==========
  
  function normalize(text) {
    if (!text) return '';
    return text
      .toLowerCase()
      .trim()
      .replace(/[.,!?;:'"()\-\/\\]/g, '')
      .replace(/\s+/g, ' ')
      .replace(/^(le|la|les|un|une|des|de|du|à|en|pour|sur|avec|sans|the|a|an|of|for|in|on|with)\s+/g, '');
  }
  
  function isAnswerCorrect(userAns, expectedAns) {
    const u = normalize(userAns);
    const e = normalize(expectedAns);
    
    if (!u || !e) return false;
    if (u === e) return true;
    
    // Correspondance partielle
    if (u.includes(e) || e.includes(u)) return true;
    
    // Mots-clés (70% doivent correspondre)
    const uWords = u.split(' ').filter(w => w.length > 0);
    const eWords = e.split(' ').filter(w => w.length > 0);
    
    if (uWords.length === 0 || eWords.length === 0) return false;
    
    const matches = uWords.filter(w => eWords.includes(w)).length;
    const required = Math.min(uWords.length, eWords.length);
    
    if (required > 0 && matches / required >= 0.7) return true;
    
    // Similarité Levenshtein
    if (similarity(u, e) > 0.85) return true;
    
    return false;
  }
  
  function similarity(s1, s2) {
    if (s1 === s2) return 1;
    if (!s1 || !s2) return 0;
    
    const longer = s1.length > s2.length ? s1 : s2;
    const shorter = s1.length > s2.length ? s2 : s1;
    
    if (longer.length === 0) return 1;
    
    const editDistance = levenshtein(longer, shorter);
    return (longer.length - editDistance) / longer.length;
  }
  
  function levenshtein(a, b) {
    const matrix = [];
    for (let i = 0; i <= b.length; i++) matrix[i] = [i];
    for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
    
    for (let i = 1; i <= b.length; i++) {
      for (let j = 1; j <= a.length; j++) {
        if (b.charAt(i - 1) === a.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          );
        }
      }
    }
    return matrix[b.length][a.length];
  }
  
  // ========== FIN VALIDATION ==========
  
  async function checkAnswer() {
    if (!userAnswer.trim() || !currentCard || processing) return;
    
    processing = true;
    
    isCorrect = isAnswerCorrect(userAnswer, currentCard.answer);
    
    console.log(`Validation: "${userAnswer}" vs "${currentCard.answer}" → ${isCorrect ? '✅' : '❌'}`);
    
    showResult = true;
    
    try {
      await reviewCard(token, currentCard.id, isCorrect);
      
      setTimeout(async () => {
        await nextCard();
      }, 1500);
      
    } catch (e) {
      console.error('Erreur:', e);
      processing = false;
    }
  }
  
  async function nextCard() {
    currentIndex++;
    
    if (currentIndex >= cards.length) {
      await Promise.all([loadDueCards(), loadStats()]);
    } else {
      await resetQuizState();
    }
  }
  
  function skipCard() {
    showAnswer = true;
  }
  
  function handleKeydown(event) {
    if (event.key === 'Enter' && userAnswer.trim() && !showResult && !processing) {
      checkAnswer();
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
  <title>Quiz Flashcards {tag ? `- ${tag}` : ''} - Open TutorAI</title>
</svelte:head>

<div class="quiz-container">
  {#if loading}
    <div class="loading">
      <div class="spinner"></div>
      <p>Chargement du quiz...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <h2>⚠️ Erreur</h2>
      <p>{error}</p>
      <button on:click={init}>Réessayer</button>
    </div>
  {:else if currentCard}
    <header class="quiz-header">
      <div class="stats-bar">
        <div class="stat">
          <span class="value">{stats.mastered}</span>
          <span class="label">✅ Maîtrisées</span>
        </div>
        <div class="stat">
          <span class="value">{currentIndex + 1}/{cards.length}</span>
          <span class="label">🎯 Question</span>
        </div>
        <div class="stat">
          <span class="value">{stats.to_review}</span>
          <span class="label">📚 À réviser</span>
        </div>
      </div>
      
      <div class="progress-bar">
        <div class="progress-fill" style="width: {progress}%"></div>
      </div>
      
      {#if tag}
        <div class="tag-badge">📁 {tag}</div>
      {/if}
    </header>
    
    <div class="quiz-card" class:correct={showResult && isCorrect} class:incorrect={showResult && !isCorrect}>
      <div class="question-section">
        <div class="level-badge">Niveau {currentCard.box}/5</div>
        <div class="question-label">QUESTION</div>
        <div class="question-text">{currentCard.question}</div>
      </div>
      
      <div class="answer-section">
        {#if !showAnswer}
          <input
            bind:this={inputRef}
            bind:value={userAnswer}
            on:keydown={handleKeydown}
            type="text"
            placeholder="Tapez votre réponse ici..."
            class="answer-input"
            class:correct-input={showResult && isCorrect}
            class:incorrect-input={showResult && !isCorrect}
            disabled={showResult || processing}
            autocomplete="off"
          />
        {:else}
          <div class="revealed-answer">
            <div class="answer-label">Réponse attendue :</div>
            <div class="answer-text">{currentCard.answer}</div>
          </div>
        {/if}
        
        {#if showResult}
          <div class="feedback" class:correct-feedback={isCorrect} class:incorrect-feedback={!isCorrect}>
            {#if isCorrect}
              <span class="feedback-icon">✅</span>
              <span class="feedback-text">Correct ! Bravo !</span>
            {:else}
              <span class="feedback-icon">❌</span>
              <div class="feedback-text">
                <div>Incorrect</div>
                <div class="expected-answer">Réponse : <strong>{currentCard.answer}</strong></div>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    </div>
    
    <div class="actions">
      {#if !showResult && !showAnswer}
        <button 
          class="btn btn-submit" 
          on:click={checkAnswer}
          disabled={!userAnswer.trim() || processing}
        >
          ✓ Valider
        </button>
        <button 
          class="btn btn-skip" 
          on:click={skipCard}
          disabled={processing}
        >
          👁 Voir la réponse
        </button>
      {:else if showAnswer && !showResult}
        <button 
          class="btn btn-next" 
          on:click={() => { reviewCard(token, currentCard.id, false); nextCard(); }}
        >
          → Carte suivante
        </button>
      {/if}
    </div>
    
    <p class="hint">💡 Appuyez sur Entrée pour valider votre réponse</p>
    
  {:else}
    <div class="empty-state">
      <h2>🎉 Bravo !</h2>
      <p>Aucune carte à réviser {tag ? `pour ${tag}` : ''}.</p>
      <p>Vous avez terminé toutes vos révisions !</p>
      <div class="empty-actions">
        <a href="/student/flashcards" class="btn-primary">Retour au dashboard</a>
        <a href="/student/flashcards/generate" class="btn-secondary">Générer plus de cartes</a>
      </div>
    </div>
  {/if}
</div>

<style>
  .quiz-container {
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
  
  .quiz-header {
    margin-bottom: 2rem;
  }
  
  .stats-bar {
    display: flex;
    justify-content: space-around;
    padding: 1.5rem;
    background: #f7fafc;
    border-radius: 12px;
    margin-bottom: 1rem;
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
    margin-bottom: 1rem;
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
  
  .quiz-card {
    background: white;
    border-radius: 20px;
    padding: 2.5rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
    transition: all 0.3s ease;
    border: 3px solid transparent;
  }
  
  .quiz-card.correct {
    border-color: #48bb78;
    background: #f0fff4;
  }
  
  .quiz-card.incorrect {
    border-color: #f56565;
    background: #fff5f5;
  }
  
  .question-section {
    margin-bottom: 2rem;
    position: relative;
  }
  
  .level-badge {
    position: absolute;
    top: -1rem;
    right: 0;
    background: rgba(102, 126, 234, 0.1);
    color: #667eea;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
  }
  
  .question-label {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #718096;
    margin-bottom: 0.5rem;
    font-weight: 600;
  }
  
  .question-text {
    font-size: 1.5rem;
    color: #2d3748;
    line-height: 1.5;
    font-weight: 500;
  }
  
  .answer-section {
    margin-top: 2rem;
  }
  
  .answer-input {
    width: 100%;
    padding: 1.2rem 1.5rem;
    font-size: 1.2rem;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    transition: all 0.3s ease;
    background: #f7fafc;
  }
  
  .answer-input:focus {
    outline: none;
    border-color: #667eea;
    background: white;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
  
  .answer-input.correct-input {
    border-color: #48bb78;
    background: #f0fff4;
  }
  
  .answer-input.incorrect-input {
    border-color: #f56565;
    background: #fff5f5;
  }
  
  .revealed-answer {
    padding: 1.5rem;
    background: #edf2f7;
    border-radius: 12px;
    border-left: 4px solid #667eea;
  }
  
  .answer-label {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #718096;
    margin-bottom: 0.5rem;
    font-weight: 600;
  }
  
  .answer-text {
    font-size: 1.3rem;
    color: #2d3748;
    font-weight: 600;
  }
  
  .feedback {
    margin-top: 1.5rem;
    padding: 1.2rem;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 1rem;
    animation: slideIn 0.3s ease;
  }
  
  @keyframes slideIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  .correct-feedback {
    background: #c6f6d5;
    color: #22543d;
  }
  
  .incorrect-feedback {
    background: #fed7d7;
    color: #742a2a;
  }
  
  .feedback-icon {
    font-size: 2rem;
  }
  
  .feedback-text {
    font-size: 1.1rem;
    font-weight: 600;
  }
  
  .expected-answer {
    font-size: 0.95rem;
    margin-top: 0.3rem;
    font-weight: normal;
  }
  
  .actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-top: 1.5rem;
  }
  
  .btn {
    padding: 1rem 2rem;
    border: none;
    border-radius: 12px;
    font-size: 1.05rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }
  
  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .btn-submit {
    background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
    color: white;
    flex: 1;
  }
  
  .btn-skip {
    background: #edf2f7;
    color: #4a5568;
  }
  
  .btn-next {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    width: 100%;
  }
  
  .hint {
    text-align: center;
    margin-top: 1.5rem;
    color: #718096;
    font-size: 0.9rem;
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
  
  .empty-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .btn-primary, .btn-secondary {
    display: inline-block;
    padding: 1rem 2rem;
    text-decoration: none;
    border-radius: 12px;
    font-weight: 600;
    transition: transform 0.2s;
  }
  
  .btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }
  
  .btn-secondary {
    background: white;
    color: #667eea;
    border: 2px solid #667eea;
  }
  
  .btn-primary:hover, .btn-secondary:hover {
    transform: translateY(-2px);
  }
</style>
