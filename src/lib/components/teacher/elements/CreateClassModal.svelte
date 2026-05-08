<script lang="ts">
  export let show: boolean = false;
  export let onClose: () => void = () => {};

  let courseName = '';
  let section = '';
  let level = '';
  let subject = '';

  function handleCreate() {
    console.log({ courseName, section, level, subject });
    alert(`Cours "${courseName}" créé (simulation)`);
    courseName = '';
    section = '';
    level = '';
    subject = '';
    onClose();
  }
</script>

{#if show}
  <!-- Overlay avec fond sombre garanti -->
  <div
    style="position: fixed; inset: 0; background: rgba(0, 0, 0, 0.6); z-index: 9999; display: flex; align-items: center; justify-content: center;"
    on:click={onClose}
  >
    <!-- Contenu de la modale -->
    <div
      class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-lg mx-4"
      style="z-index: 10000;"
      on:click|stopPropagation
    >
      <h2 class="text-xl font-bold mb-4">Créer un cours</h2>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium mb-1">Nom du cours *</label>
          <input
            type="text"
            bind:value={courseName}
            placeholder="Obligatoire"
            class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Section</label>
          <input
            type="text"
            bind:value={section}
            class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Niveau(x)</label>
          <input
            type="text"
            bind:value={level}
            class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Matière</label>
          <input
            type="text"
            bind:value={subject}
            class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
      </div>

      <div class="flex justify-end gap-3 mt-6">
        <button
          class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
          on:click={onClose}
        >
          Annuler
        </button>
        <button
          class="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg"
          on:click={handleCreate}
        >
          Créer
        </button>
      </div>
    </div>
  </div>
{/if}