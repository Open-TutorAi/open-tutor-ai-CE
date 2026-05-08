<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  let code = `# Écris ton code Python ici\nprint("Bonjour le monde !")`;
  let output = '';
  let isRunning = false;

  const runCode = async () => {
    isRunning = true;
    output = '⏳ Exécution en cours...';
    await new Promise(r => setTimeout(r, 1000));
    output = '✅ Résultat simulé :\nBonjour le monde !';
    isRunning = false;
  };

  const sendToTutor = () => {
    dispatch('sendToTutor', { code, output });
  };
</script>

<div class="python-editor p-4 rounded-xl bg-gray-900 text-white">
  <h3 class="text-lg font-bold mb-3">🐍 Éditeur Python</h3>
  
  <textarea
    bind:value={code}
    class="w-full h-48 p-3 font-mono text-sm bg-gray-800 text-green-300 rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500 resize-y"
    placeholder="Écris ton code Python ici..."
  />
  
  <div class="flex gap-3 mt-3">
    <button
      on:click={runCode}
      disabled={isRunning}
      class="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg font-medium transition"
    >
      {isRunning ? '⏳ Exécution...' : '▶ Exécuter'}
    </button>
    
    <button
      on:click={sendToTutor}
      class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition"
    >
      🤖 Envoyer au tuteur IA
    </button>
  </div>
  
  {#if output}
    <div class="mt-4">
      <h4 class="text-sm font-semibold text-gray-400 mb-1">Résultat :</h4>
      <pre class="p-3 bg-black rounded-lg text-green-400 text-sm whitespace-pre-wrap">{output}</pre>
    </div>
  {/if}
</div>