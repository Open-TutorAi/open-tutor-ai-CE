<script>
  import { onMount } from 'svelte';
  
  let questions = [];
  let loading = true;
  let selectedQuestion = null;
  let reponse = '';
  
  onMount(async () => {
    try {
      const res = await fetch('http://localhost:5500/api/admin/faq-questions');
      if (res.ok) {
        questions = await res.json();
      }
    } catch (err) {
      console.error(err);
    }
    loading = false;
  });
  
  async function updateStatut(id, statut) {
    const res = await fetch(`http://localhost:5500/api/admin/faq-questions/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ statut })
    });
    if (res.ok) {
      const idx = questions.findIndex(q => q.id === id);
      questions[idx].statut = statut;
    }
  }
  
  async function submitReponse(id) {
    const res = await fetch(`http://localhost:5500/api/admin/faq-questions/${id}/repondre`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reponse })
    });
    if (res.ok) {
      const idx = questions.findIndex(q => q.id === id);
      questions[idx].reponse = reponse;
      questions[idx].statut = 'repondu';
      selectedQuestion = null;
      reponse = '';
    }
  }
  
  async function deleteQuestion(id) {
    if (confirm('Supprimer cette question ?')) {
      const res = await fetch(`http://localhost:5500/api/admin/faq-questions/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        questions = questions.filter(q => q.id !== id);
      }
    }
  }
  
  let filtreStatut = 'tous';
  let recherche = '';
  
  $: questionsFiltrees = questions.filter(q => {
    if (filtreStatut !== 'tous' && q.statut !== filtreStatut) return false;
    if (recherche && !q.question.toLowerCase().includes(recherche.toLowerCase())) return false;
    return true;
  });
  
  $: stats = {
    total: questions.length,
    enAttente: questions.filter(q => q.statut === 'en_attente').length,
    repondu: questions.filter(q => q.statut === 'repondu').length
  };
</script>

<div class="max-w-7xl mx-auto px-4 py-8">
  <!-- TITRE -->
  <h1 class="text-3xl font-bold text-gray-800 mb-6">📋 Panneau Admin - FAQ</h1>
  
  <!-- STATS (style Tailwind comme ta collègue) -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
    <div class="bg-white rounded-xl shadow p-6 border-2 border-gray-100">
      <div class="text-3xl font-bold text-blue-600">{stats.total}</div>
      <div class="text-gray-600">Total questions</div>
    </div>
    <div class="bg-white rounded-xl shadow p-6 border-2 border-orange-100">
      <div class="text-3xl font-bold text-orange-500">{stats.enAttente}</div>
      <div class="text-gray-600">En attente</div>
    </div>
    <div class="bg-white rounded-xl shadow p-6 border-2 border-green-100">
      <div class="text-3xl font-bold text-green-600">{stats.repondu}</div>
      <div class="text-gray-600">Répondu</div>
    </div>
  </div>
  
  <!-- FILTRES (style Tailwind) -->
  <div class="flex flex-col md:flex-row gap-4 mb-8">
    <input 
      type="text" 
      bind:value={recherche} 
      placeholder="🔍 Rechercher une question..."
      class="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition"
    />
    <select bind:value={filtreStatut} class="px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none">
      <option value="tous">Tous les statuts</option>
      <option value="en_attente">⏳ En attente</option>
      <option value="repondu">✅ Répondu</option>
    </select>
  </div>
  
  <!-- LISTE DES QUESTIONS -->
  {#if loading}
    <div class="text-center py-12 text-gray-500">Chargement...</div>
  {:else if questionsFiltrees.length === 0}
    <div class="text-center py-12 text-gray-500">Aucune question trouvée</div>
  {:else}
    <div class="space-y-4">
      {#each questionsFiltrees as q}
        <div class="bg-white rounded-xl shadow-md border-2 border-gray-100 overflow-hidden hover:border-blue-200 transition">
          <!-- En-tête -->
          <div class="px-6 py-4 bg-gray-50 border-b border-gray-100 flex flex-col md:flex-row justify-between gap-2">
            <span class="font-medium text-gray-700">📧 {q.email}</span>
            <span class="text-sm px-3 py-1 rounded-full {q.statut === 'en_attente' ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700'}">
              {q.statut === 'en_attente' ? '⏳ En attente' : '✅ Répondu'}
            </span>
          </div>
          
          <!-- Question -->
          <div class="px-6 py-4">
            <strong class="text-gray-700">❓ Question :</strong>
            <p class="mt-2 text-gray-600 bg-blue-50 p-3 rounded-lg">{q.question}</p>
          </div>
          
          <!-- Réponse (si existe) -->
          {#if q.reponse}
            <div class="px-6 pb-4">
              <strong class="text-gray-700">💬 Réponse :</strong>
              <p class="mt-2 text-gray-600 bg-green-50 p-3 rounded-lg">{q.reponse}</p>
            </div>
          {/if}
          
          <!-- Actions -->
          <div class="px-6 py-3 bg-gray-50 border-t border-gray-100 flex flex-wrap gap-3">
            <select on:change={(e) => updateStatut(q.id, e.target.value)} class="px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="en_attente" selected={q.statut === 'en_attente'}>📝 En attente</option>
              <option value="repondu" selected={q.statut === 'repondu'}>✅ Répondu</option>
            </select>
            <button 
              on:click={() => selectedQuestion = q}
              class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition text-sm font-medium"
            >
              ✏️ Répondre
            </button>
            <button 
              on:click={() => deleteQuestion(q.id)}
              class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition text-sm font-medium"
            >
              🗑️ Supprimer
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
  
  <!-- MODAL POUR RÉPONDRE (style Tailwind) -->
  {#if selectedQuestion}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-xl max-w-lg w-full">
        <div class="px-6 py-4 border-b border-gray-200">
          <h2 class="text-xl font-bold text-gray-800">Répondre à :</h2>
          <p class="text-gray-600">{selectedQuestion.email}</p>
        </div>
        
        <div class="px-6 py-4">
          <p class="text-gray-700 mb-2"><strong>Question :</strong></p>
          <p class="bg-blue-50 p-3 rounded-lg text-gray-700 mb-4">{selectedQuestion.question}</p>
          
          <label class="block text-gray-700 mb-2">Votre réponse :</label>
          <textarea 
            bind:value={reponse} 
            placeholder="Écrivez votre réponse ici..." 
            rows="5"
            class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
          ></textarea>
        </div>
        
        <div class="px-6 py-4 bg-gray-50 rounded-b-xl flex justify-end gap-3">
          <button 
            on:click={() => selectedQuestion = null}
            class="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition"
          >
            Annuler
          </button>
          <button 
            on:click={() => submitReponse(selectedQuestion.id)}
            class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
          >
            📤 Envoyer la réponse
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>