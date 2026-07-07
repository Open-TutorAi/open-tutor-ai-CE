<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { generateFlashcards, generateFromPDF } from '$lib/apis/flashcards';
  
  let content = '';
  let numCards = 5;
  let tag = '';
  let loading = false;
  let error = null;
  let success = false;
  let token = '';
  let pdfFile = null;
  let uploadMode = 'text';
  let selectedModel = 'phi3:mini';
  
  const suggestedTags = ['Philosophie', 'Python', 'Mathématiques', 'Histoire', 'Physique'];
  
  onMount(() => {
    token = localStorage.getItem('token') || '';
  });
  
  function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        error = 'Seuls les fichiers PDF sont acceptés';
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        error = 'Fichier trop volumineux (max 10 MB)';
        return;
      }
      pdfFile = file;
      error = null;
    }
  }
  
  async function handleGenerate() {
    error = null;
    success = false;
    
    if (uploadMode === 'text' && !content.trim()) {
      error = 'Veuillez entrer du contenu';
      return;
    }
    
    if (uploadMode === 'pdf' && !pdfFile) {
      error = 'Veuillez sélectionner un PDF';
      return;
    }
    
    loading = true;
    
    try {
      if (uploadMode === 'text') {
        await generateFlashcards(token, content, numCards, null, tag || null);
      } else {
        await generateFromPDF(token, pdfFile, numCards, tag || null, selectedModel);
      }
      
      success = true;
      setTimeout(() => goto('/student/flashcards/review?mode=quiz'), 2000);
      
    } catch (e) {
      error = e.message || 'Erreur lors de la génération';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Générer Flashcards - Open TutorAI</title>
</svelte:head>

<div class="generate-page">
  <div class="header">
    <h1>📝 Créer des Flashcards</h1>
    <p>Générez des cartes de révision à partir de votre contenu</p>
  </div>
  
  <div class="form-card">
    <!-- Mode selector -->
    <div class="mode-tabs">
      <button 
        class="tab" 
        class:active={uploadMode === 'text'}
        on:click={() => uploadMode = 'text'}
      >
        ✍️ Texte
      </button>
      <button 
        class="tab" 
        class:active={uploadMode === 'pdf'}
        on:click={() => uploadMode = 'pdf'}
      >
        📄 PDF
      </button>
    </div>
    
    <!-- Tag input -->
    <div class="field">
      <label>Matière</label>
      <input 
        type="text" 
        bind:value={tag}
        placeholder="Ex: Philosophie, Python..."
        list="tags"
      />
      <datalist id="tags">
        {#each suggestedTags as t}<option value={t} />{/each}
      </datalist>
    </div>
    
    <!-- Content input -->
    {#if uploadMode === 'text'}
      <div class="field">
        <label>Contenu</label>
        <textarea 
          bind:value={content}
          placeholder="Collez votre cours ici..."
          rows="8"
        ></textarea>
      </div>
    {:else}
      <div class="field">
        <label>Fichier PDF</label>
        <label class="file-drop">
          <input 
            type="file" 
            accept=".pdf"
            on:change={handleFileSelect}
            class="hidden"
          />
          {#if pdfFile}
            <div class="file-info">
              <span class="icon">📄</span>
              <span>{pdfFile.name}</span>
              <span class="size">{(pdfFile.size / 1024).toFixed(0)} KB</span>
            </div>
          {:else}
            <div class="file-placeholder">
              <span class="icon">📎</span>
              <span>Cliquez pour sélectionner un PDF</span>
            </div>
          {/if}
        </label>
      </div>
    {/if}
    
    <!-- Number of cards -->
    <div class="field">
      <label>Nombre de cartes : {numCards}</label>
      <input 
        type="range" 
        bind:value={numCards}
        min="3"
        max="15"
        step="1"
      />
    </div>
    
    <!-- Messages -->
    {#if error}
      <div class="message error">⚠️ {error}</div>
    {/if}
    
    {#if success}
      <div class="message success">✅ Flashcards générées ! Redirection...</div>
    {/if}
    
    <!-- Submit button -->
    <button 
      class="submit-btn"
      on:click={handleGenerate}
      disabled={loading}
    >
      {loading ? '⏳ Génération...' : '🚀 Générer les flashcards'}
    </button>
  </div>
</div>

<style>
  .generate-page {
    max-width: 700px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .header {
    text-align: center;
    margin-bottom: 2rem;
  }
  
  .header h1 {
    font-size: 2rem;
    color: #2d3748;
    margin-bottom: 0.5rem;
  }
  
  .header p {
    color: #718096;
  }
  
  .form-card {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  }
  
  .mode-tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    background: #f7fafc;
    padding: 0.5rem;
    border-radius: 12px;
  }
  
  .tab {
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
  
  .tab.active {
    background: white;
    color: #667eea;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
  
  .field {
    margin-bottom: 1.5rem;
  }
  
  .field label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: #2d3748;
  }
  
  .field input[type="text"],
  .field textarea {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 1rem;
    font-family: inherit;
    transition: border-color 0.2s;
  }
  
  .field input:focus,
  .field textarea:focus {
    outline: none;
    border-color: #667eea;
  }
  
  .field textarea {
    resize: vertical;
    min-height: 150px;
  }
  
  .field input[type="range"] {
    width: 100%;
    height: 6px;
    border-radius: 3px;
    background: #e2e8f0;
    outline: none;
    -webkit-appearance: none;
  }
  
  .field input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #667eea;
    cursor: pointer;
  }
  
  .file-drop {
    display: block;
    padding: 2rem;
    border: 2px dashed #cbd5e0;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
  }
  
  .file-drop:hover {
    border-color: #667eea;
    background: #f7fafc;
  }
  
  .file-info, .file-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
  }
  
  .file-info .icon, .file-placeholder .icon {
    font-size: 2rem;
  }
  
  .file-info .size {
    color: #a0aec0;
    font-size: 0.9rem;
  }
  
  .hidden {
    display: none;
  }
  
  .message {
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    font-weight: 600;
  }
  
  .message.error {
    background: #fff5f5;
    color: #c53030;
    border-left: 4px solid #c53030;
  }
  
  .message.success {
    background: #f0fff4;
    color: #22543d;
    border-left: 4px solid #48bb78;
  }
  
  .submit-btn {
    width: 100%;
    padding: 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s;
  }
  
  .submit-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }
  
  .submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
