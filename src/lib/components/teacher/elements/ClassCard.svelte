<script lang="ts">
  export let name: string;
  export let subject: string;
  export let students: number;
  export let href: string;

  // Couleurs de fond pour les icônes (peut être paramétrable)
  $: bgColor = 'bg-indigo-500';
</script>

<a
  {href}
  class="block bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden border border-gray-100 dark:border-gray-700"
>
  <!-- Partie supérieure colorée (petite barre) -->
  <div class="h-2 {bgColor}"></div>

  <div class="p-5">
    <div class="flex items-start gap-4">
      <!-- Cercle avec la première lettre -->
      <span
        class="flex-shrink-0 w-12 h-12 {bgColor} text-white rounded-full flex items-center justify-center font-bold text-xl"
      >
        {name.charAt(0)}
      </span>

      <div class="min-w-0">
        <h3 class="text-lg font-semibold truncate">{name}</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">{subject}</p>
        <p class="text-xs mt-1 text-gray-400 dark:text-gray-500">{students} élèves</p>
      </div>
    </div>
  </div>
</a>