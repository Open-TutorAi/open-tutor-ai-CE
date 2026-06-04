<script lang="ts">
  export let show: boolean = false;
  export let onClose: () => void = () => {};

  let courseName = '';
  let section = '';
  let level = '';
  let subject = '';

  function handleCreate() {
    console.log({ courseName, section, level, subject });
    alert(`Course "${courseName}" created (simulation)`);
    courseName = '';
    section = '';
    level = '';
    subject = '';
    onClose();
  }
</script>

{#if show}
  <!-- Overlay clair (blanc transparent + blur) -->
  <div
    style="position: fixed; inset: 0; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(2px); z-index: 9999; display: flex; align-items: center; justify-content: center;"
    on:click={onClose}
  >
    <!-- Modale -->
    <div
      class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-lg mx-4 border border-indigo-100 dark:border-indigo-900"
      style="z-index: 10000;"
      on:click|stopPropagation
    >
      <!-- Titre en noir (gris foncé) -->
      <h2 class="text-2xl font-bold mb-4 text-gray-900 dark:text-white">Create a course</h2>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Course name *</label>
          <input
            type="text"
            bind:value={courseName}
            placeholder="Required"
            class="w-full border border-indigo-200 dark:border-indigo-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Section</label>
          <input
            type="text"
            bind:value={section}
            class="w-full border border-indigo-200 dark:border-indigo-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Level(s)</label>
          <input
            type="text"
            bind:value={level}
            class="w-full border border-indigo-200 dark:border-indigo-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Subject</label>
          <input
            type="text"
            bind:value={subject}
            class="w-full border border-indigo-200 dark:border-indigo-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
      </div>

      <div class="flex justify-end gap-3 mt-6">
        <button
          class="px-4 py-2 border border-indigo-300 dark:border-indigo-600 rounded-lg text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 transition-colors"
          on:click={onClose}
        >
          Cancel
        </button>
        <button
          class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-sm transition-colors focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          on:click={handleCreate}
        >
          Create
        </button>
      </div>
    </div>
  </div>
{/if}