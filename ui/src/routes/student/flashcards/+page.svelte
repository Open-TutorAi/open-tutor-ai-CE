<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getStats, getTags } from '$lib/apis/flashcards';
  
  let stats = { total: 0, mastered: 0, to_review: 0, learning: 0, by_tag: {} };
  let tags = [];
  let loading = true;
  let token = '';
  
  onMount(async () => {
    token = localStorage.getItem('token') || '';
    await loadData();
    loading = false;
  });
  
  async function loadData() {
    try {
      stats = await getStats(token);
      const result = await getTags(token);
      tags = result.tags || [];
    } catch (e) {
      console.error('Erreur:', e);
    }
  }
  
    async function deleteAllCards() {
    console.log('🔴 Clic sur "Supprimer toutes les cartes"');
    
    try {
      const token = localStorage.getItem('token');
      
      if (!token) {
        throw new Error('Token non trouvé. Veuillez vous reconnecter.');
      }
      
      const url = `http://localhost:8080/api/v1/flashcards/delete-all`;
      console.log(' Envoi requête DELETE vers:', url);
      
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('📥 Réponse reçue - Status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
        throw new Error(errorData.detail || `Erreur HTTP ${response.status}`);
      }
      
      const result = await response.json();
      console.log('✅ Succès! Cartes supprimées:', result.deleted_count);
      
      alert(`✅ ${result.deleted_count} cartes supprimées !`);
      
      // Recharger les données
      await loadData();
      
    } catch (e) {
      console.error('💥 Erreur complète:', e);
      alert('❌ Erreur lors de la suppression : ' + e.message);
    }
  }
</script>

<svelte:head>
  <title>Flashcards - Open TutorAI</title>
</svelte:head>

<div class="dashboard">
  <div class="header">
    <h1>📚 Mes Flashcards</h1>
    <p>Mémorisez efficacement avec la répétition espacée</p>
  </div>
  
  {#if loading}
    <div class="loading">Chargement...</div>
  {:else}
    <!-- Stats cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-value">{stats.total}</div>
        <div class="stat-label">Total</div>
      </div>
      
      <div class="stat-card highlight">
        <div class="stat-icon">📚</div>
        <div class="stat-value">{stats.to_review}</div>
        <div class="stat-label">À réviser</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-value">{stats.mastered}</div>
        <div class="stat-label">Maîtrisées</div>
      </div>
    </div>
    
    <!-- Action buttons -->
    <div class="actions">
      <button 
        class="btn-primary"
        on:click={() => goto('/student/flashcards/review?mode=quiz')}
        disabled={stats.to_review === 0}
      >
        🎯 Commencer la révision
      </button>
      
      <button 
        class="btn-secondary"
        on:click={() => goto('/student/flashcards/generate')}
      >
        ✨ Créer des flashcards
      </button>
    </div>
    
    <!-- Tags -->
    {#if tags.length > 0}
      <div class="tags-section">
        <h2> Mes matières</h2>
        <div class="tags-grid">
          {#each tags as tag}
            <button 
              class="tag-card"
              on:click={() => goto(`/student/flashcards/review?tag=${encodeURIComponent(tag)}&mode=quiz`)}
            >
              <div class="tag-name">{tag}</div>
              <div class="tag-count">
                {stats.by_tag[tag]?.to_review || 0} à réviser
              </div>
            </button>
          {/each}
        </div>
      </div>
    {/if}
    
    <!-- Danger zone -->
    {#if stats.total > 0}
      <div class="danger-zone">
        <button class="btn-danger" on:click={deleteAllCards}>
          🗑️ Supprimer toutes les cartes
        </button>
      </div>
    {/if}
  {/if}
</div>

<style>
  .dashboard {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .header {
    text-align: center;
    margin-bottom: 3rem;
  }
  
  .header h1 {
    font-size: 2.5rem;
    color: #2d3748;
    margin-bottom: 0.5rem;
  }
  
  .header p {
    color: #718096;
    font-size: 1.1rem;
  }
  
  .loading {
    text-align: center;
    padding: 3rem;
    color: #718096;
  }
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
  }
  
  .stat-card {
    background: white;
    padding: 2rem;
    border-radius: 16px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transition: transform 0.2s;
  }
  
  .stat-card:hover {
    transform: translateY(-4px);
  }
  
  .stat-card.highlight {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }
  
  .stat-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
  }
  
  .stat-value {
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
  }
  
  .stat-label {
    color: #718096;
    font-size: 0.9rem;
  }
  
  .stat-card.highlight .stat-label {
    color: rgba(255,255,255,0.9);
  }
  
  .actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-bottom: 3rem;
    flex-wrap: wrap;
  }
  
  .btn-primary, .btn-secondary {
    padding: 1rem 2rem;
    border: none;
    border-radius: 12px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }
  
  .btn-primary:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }
  
  .btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .btn-secondary {
    background: white;
    color: #667eea;
    border: 2px solid #667eea;
  }
  
  .btn-secondary:hover {
    background: #667eea;
    color: white;
  }
  
  .tags-section {
    margin-bottom: 3rem;
  }
  
  .tags-section h2 {
    font-size: 1.5rem;
    color: #2d3748;
    margin-bottom: 1.5rem;
    text-align: center;
  }
  
  .tags-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 1rem;
  }
  
  .tag-card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    border: 2px solid #e2e8f0;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
  }
  
  .tag-card:hover {
    border-color: #667eea;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
  }
  
  .tag-name {
    font-size: 1.1rem;
    font-weight: 600;
    color: #2d3748;
    margin-bottom: 0.5rem;
  }
  
  .tag-count {
    color: #718096;
    font-size: 0.9rem;
  }
  
  .danger-zone {
    margin-top: 3rem;
    padding: 1.5rem;
    background: #fff5f5;
    border: 2px solid #fc8181;
    border-radius: 12px;
    text-align: center;
  }
  
  .btn-danger {
    padding: 0.75rem 1.5rem;
    background: #f56565;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-danger:hover {
    background: #c53030;
  }
</style>
