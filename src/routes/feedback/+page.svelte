<script>
  import { enhance } from '$app/forms';
  import Toast from '$lib/Toast.svelte';

  export let data;
  export let form;
  
  let note = 0;
  let hoverNote = 0;
  let showToast = false;
  let toastMessage = '';
  let toastType = 'success';
  
  function afficherNotification(message, type = 'success') {
    toastMessage = message;
    toastType = type;
    showToast = true;
    setTimeout(() => { showToast = false; }, 3000);
  }
  
  // Déclencher la notification quand le formulaire est soumis
  $: if (form?.success && !showToast) {
    afficherNotification('✅ Thank you! Your feedback has been saved.', 'success');
  }
  $: if (form?.error && !showToast) {
    afficherNotification(form.error, 'error');
  }
</script>

<div class="max-w-2xl mx-auto p-6 space-y-8">
  
  <!-- Titre Principal -->
  <h1 class="text-3xl font-bold text-center">📝 User Feedback</h1>

  <!-- Formulaire d'envoi -->
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <form method="POST" use:enhance class="space-y-4">
      
      <div>
        <label for="name" class="block text-sm font-medium text-gray-700 mb-1">Name</label>
        <input
          type="text"
          id="name"
          name="name"
          placeholder="Your name"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          required
        />
      </div>

      <!-- ⭐ ÉTOILES DE NOTATION -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">⭐ Your rating (1 to 5)</label>
        <div class="flex gap-2">
          {#each [1, 2, 3, 4, 5] as star}
            <button
              type="button"
              class="text-3xl transition transform hover:scale-110 focus:outline-none {star <= (hoverNote || note) ? 'text-yellow-400' : 'text-gray-300'}"
              on:mouseenter={() => hoverNote = star}
              on:mouseleave={() => hoverNote = 0}
              on:click={() => note = star}
            >
              {star <= (hoverNote || note) ? '★' : '☆'}
            </button>
          {/each}
        </div>
        {#if note > 0}
          <p class="text-sm text-gray-500 mt-1">Selected rating: {note} star{note > 1 ? 's' : ''}</p>
        {/if}
      </div>

      <div>
        <label for="feedback" class="block text-sm font-medium text-gray-700 mb-1">Your Feedback</label>
        <textarea
          id="feedback"
          name="feedback"
          rows="4"
          placeholder="Write your feedback here..."
          class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          required
        ></textarea>
      </div>

      <!-- Champ caché pour envoyer la note -->
      <input type="hidden" name="note" value={note} />

      <button
        type="submit"
        class="w-full sm:w-auto bg-black text-white px-6 py-2 rounded-lg hover:bg-gray-800 transition font-medium"
      >
        Send Feedback
      </button>
    </form>

    <!-- 🔔 NOTIFICATION TOAST -->
    {#if showToast}
      <Toast message={toastMessage} type={toastType} />
    {/if}
  </div>

  <!-- Liste des Feedbacks -->
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <h2 class="text-xl font-bold mb-4 flex items-center gap-2">
      💬 Feedbacks received
      <span class="text-sm font-normal text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
        {data.feedbacks?.length || 0}
      </span>
    </h2>

    {#if data.feedbacks?.length === 0}
      <div class="text-center py-8 text-gray-400">
        <p>No feedback yet. Be the first!</p>
      </div>
    {:else}
      <div class="space-y-4 max-h-[500px] overflow-y-auto pr-2 scrollbar-thin">
        {#each data.feedbacks as f}
          <div class="border-b border-gray-100 pb-3 last:border-0">
            <div class="flex justify-between items-start mb-1">
              <span class="font-semibold text-gray-800">{f.name || 'Anonyme'}</span>
              <div class="flex items-center gap-2">
                <!-- ⭐ AFFICHAGE DES ÉTOILES DANS LA LISTE -->
                {#if f.note}
                  <span class="text-xs text-yellow-500">
                    {'★'.repeat(f.note)}{'☆'.repeat(5 - f.note)}
                  </span>
                {/if}
                <span class="text-xs text-gray-400 whitespace-nowrap">
                  {new Date(f.created_at).toLocaleDateString('fr-FR', {
                    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
                  })}
                </span>
              </div>
            </div>
            <p class="text-gray-600 whitespace-pre-wrap text-sm leading-relaxed">{f.message}</p>
          </div>
        {/each}
      </div>
    {/if}
  </div>

</div>

<style>
  .scrollbar-thin::-webkit-scrollbar {
    width: 8px;
  }
  
  .scrollbar-thin::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
  }
  
  .scrollbar-thin::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
  }
  
  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background: #555;
  }
</style>