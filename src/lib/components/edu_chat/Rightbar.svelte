<script>
    import { onMount } from 'svelte';
    import { getContext } from 'svelte';

    // Props for the component
    export let courseCompletion = 45;
    export let modules = [
      { id: 1, name: "Introduction", status: "completed" },
      { id: 2, name: "HDFS", status: "completed" },
      { id: 3, name: "MapReduce", status: "in-progress" },
      { id: 4, name: "YARN", status: "not-started" },
      { id: 5, name: "Hive & Pig", status: "not-started" }
    ];
  
    // Animation for progress bar
    let animatedProgress = 0;
    const i18n = getContext('i18n');
    
    onMount(() => {
      setTimeout(() => {
        animatedProgress = courseCompletion;
      }, 200);
    });
  
    // Calculate number of completed modules for accessibility
    $: completedModules = modules.filter(module => module.status === "completed").length;
</script>
  
    <!-- Progress Summary Card -->
    <div class="max-w-60 bg-white rounded-lg shadow-sm mb-4 p-4" 
      role="region" 
      aria-label="Course progress summary">
      <div class="mb-1">
        <h2 class="text-gray-800 font-medium text-base mb-2">{$i18n.t("Program Completion")}</h2>
        
        <div class="flex items-center mb-2">
          <span class="text-lg font-bold text-gray-900" aria-live="polite">
            {courseCompletion}%
          </span>
        </div>
        
      
        <div 
          class="h-2 w-full bg-blue-100 rounded-full overflow-hidden" 
          role="progressbar" 
          aria-valuenow={courseCompletion} 
          aria-valuemin="0" 
          aria-valuemax="100">
          <div 
            class="h-full bg-green-500 rounded-full transition-all duration-1000 ease-out"
            style="width: {animatedProgress}%">
          </div>
        </div>
      </div>
    </div>
    
    <!-- Modules Progress Card -->
    <div class="max-w-60 bg-white rounded-lg shadow-sm p-6 flex-grow" 
      role="region" 
      aria-label="Module progress tracker">
      <ul class="flex flex-col space-y-8 list-none m-0 p-0">
        {#each modules as module, index}
          <li class="flex items-center">
            <!-- Status indicator -->
            <div class="relative flex justify-center w-16">
              {#if module.status === "completed"}
                <div 
                  class="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center z-10"
                  aria-hidden="true">
                  <!-- Check icon -->
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </div>
              {:else if module.status === "in-progress"}
                <div 
                  class="w-6 h-6 rounded-full border-2 border-blue-600 flex items-center justify-center bg-white z-10"
                  aria-hidden="true">
                  <div class="w-2 h-2 rounded-full bg-blue-600"></div>
                </div>
              {:else}
                <div 
                  class="w-6 h-6 rounded-full border border-gray-300 bg-white z-10"
                  aria-hidden="true">
                </div>
              {/if}
              
              <!-- Vertical connector line -->
              {#if index < modules.length - 1}
                <div 
                  class="absolute top-6 w-px h-8 bg-blue-600"
                  aria-hidden="true">
                </div>
              {/if}
            </div>
            
            <!-- Module name -->
            <span class={`text-sm ${
              module.status === "completed" ? "text-gray-800" : 
              module.status === "in-progress" ? "text-gray-800" : 
              "text-gray-500"
            }`}>
              {module.name}
              <span class="sr-only">
                {#if module.status === "completed"}
                  , completed
                {:else if module.status === "in-progress"}
                  , in progress
                {:else}
                  , not started
                {/if}
              </span>
            </span>
          </li>
        {/each}
      </ul>
    </div>