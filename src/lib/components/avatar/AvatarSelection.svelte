<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { settings } from '$lib/stores';
  import { fade } from 'svelte/transition';
  import { toast } from 'svelte-sonner';
  
  const dispatch = createEventDispatcher();

  // Avatar data - each avatar has unique traits that influence their personality
  // These avatars represent different teaching styles for our tutoring platform
  const avatars = [
    {
      id: 'The Scholar',
      name: 'The Scholar',
      image: 'static/images/The Scholar.png',
      accentColor: '#2196F3',
      gradientEnd: '#3D5E94',
      description: 'Analytical, detail-oriented, methodical, patient. Emphasizes deep understanding with comprehensive explanations.'
    },
    {
      id: 'The Mentor',
      name: 'The Mentor',
      image: 'static/images/The Mentor.png',
      accentColor: '#F59E0B',
      gradientEnd: '#3D5E94',
      description: 'Encouraging, warm, supportive, insightful. Focuses on building confidence through guided discovery.'
    },
    {
      id: 'The Coach',
      name: 'The Coach',
      image: 'static/images/The Coach.png',
      accentColor: '#10B981',
      gradientEnd: '#3D5E94',
      description: 'Energetic, motivational, direct, goal-oriented. Emphasizes practical application and quick results.'
    },
    {
      id: 'The Innovator',
      name: 'The Innovator',
      image: 'static/images/The Innovator.png',
      accentColor: '#EF4444',
      gradientEnd: '#3D5E94',
      description: 'Creative, adaptable, curious, thought-provoking. Explores alternative perspectives and connections.'
    }
  ];

  // Default to first avatar on load
  let selectedAvatar = avatars[0].id;
  
  // Carousel display controls - shows 3 avatars at once in the horizontal view
  let visibleIndex = 0;
  const visibleCount = 3;

  // Updates the selected avatar when user makes a selection
  // Does not immediately start chat, just highlights the selection
  const selectAvatar = (avatarId: string) => {
    selectedAvatar = avatarId;
  };

  // Initializes chat with the selected avatar personality
  // This function handles:
  // 1. Updating global settings to enable avatar mode
  // 2. Storing the selected avatar in user preferences
  // 3. Notifying the user of selection
  // 4. Triggering the parent component to start the chat session
  const startChatWithAvatar = (avatarId: string) => {
    selectedAvatar = avatarId;
    
    // Update app settings with avatar preferences
    settings.update(s => {
      const updatedSettings = {...s};
      (updatedSettings as any).avatarEnabled = true;
      (updatedSettings as any).selectedAvatarId = avatarId;
      return updatedSettings;
    });

    // Persist settings between sessions
    localStorage.setItem('settings', JSON.stringify($settings));
    
    // User feedback for selection
    toast.success(`Starting chat with ${avatars.find(a => a.id === avatarId)?.name}`);
    
    // Tell parent component to initialize chat
    dispatch('select', { avatarId });
  };

  // Return to chat type selection screen
  const goBack = () => {
    dispatch('back');
  };
  
  // Carousel navigation controls
  // These handle the horizontal scrolling when there are more avatars
  // than can fit in the visible area
  const prevSlide = () => {
    if (visibleIndex > 0) {
      visibleIndex--;
    }
  };
  
  const nextSlide = () => {
    if (visibleIndex < avatars.length - visibleCount) {
      visibleIndex++;
    }
  };
</script>

<div class="h-full w-full flex items-center justify-center bg-white dark:bg-gray-900">
  <div class="w-full max-w-6xl px-4 py-8" in:fade={{ duration: 300 }}>
    <!-- Header with back button -->
    <div class="flex items-center mb-8">
      <button 
        class="mr-4 flex items-center justify-center w-10 h-10 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors"
        on:click={goBack}
        aria-label="Go back"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Choose your avatar</h1>
    </div>
    
    <!-- Avatar carousel -->
    <div class="relative mb-8">
      <!-- Avatars wrapper -->
      <div class="w-full overflow-hidden">
        <div 
          class="flex transition-transform duration-300 ease-in-out" 
          style="transform: translateX(-{visibleIndex * (100 / visibleCount)}%)"
        >
          {#each avatars as avatar, i}
            <div 
              class="w-1/3 flex-shrink-0 px-3 transition-all duration-200"
              class:opacity-70={selectedAvatar !== avatar.id}
              class:scale-95={selectedAvatar !== avatar.id}
            >
              <!-- Avatar card -->
              <div 
                class="relative h-80 w-full rounded-lg overflow-hidden shadow-xl cursor-pointer transition-all duration-200 group"
                style="background-image: url('static/images/background.jpeg'); background-size: cover; background-position: center; {selectedAvatar === avatar.id ? `border: 3px solid ${avatar.accentColor};` : ''}"
                on:click={() => selectAvatar(avatar.id)}
              >
                <!-- Selection indicator -->
                {#if selectedAvatar === avatar.id}
                  <div class="absolute top-0 left-0 w-full h-full z-10 pointer-events-none" style="box-shadow: inset 0 0 0 3px {avatar.accentColor}, 0 0 15px {avatar.accentColor}"></div>
                {/if}
                
                <!-- Always visible gradient shadow effect -->
                <div class="absolute inset-0 z-10 bg-gradient-to-t from-black/70 to-transparent"></div>
                
                <!-- Image centered with subtle shadow -->
                <img 
                  src={avatar.image} 
                  alt={avatar.name}
                  class="relative z-20 w-full h-full object-contain" 
                  style="filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.4));"
                  draggable="false"
                />
                
                <!-- Hover overlay with info and select button -->
                <div 
                  class="absolute inset-0 z-30 bg-gradient-to-t from-black/70 to-transparent opacity-0 transition-opacity duration-300 flex flex-col justify-end p-4"
                  class:opacity-100={selectedAvatar === avatar.id || false}
                  class:group-hover:opacity-100={true}
                >
                  <p class="text-white font-medium">{avatar.name}</p>
                  <p class="text-white/80 text-xs mb-2">{avatar.description}</p>
                  <button
                    class="w-full px-3 py-1 rounded text-sm font-medium text-white"
                    style="background-color: {avatar.accentColor};"
                    on:click|stopPropagation={() => startChatWithAvatar(avatar.id)}
                  >
                    Start Chat
                  </button>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
    
    <!-- Navigation arrows (now below cards) -->
    <div class="flex justify-center items-center gap-4 mb-8">
      <button 
        class="flex items-center justify-center w-10 h-10 bg-white dark:bg-gray-800 rounded-full shadow-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        on:click={prevSlide}
        disabled={visibleIndex === 0}
        class:opacity-50={visibleIndex === 0}
        class:cursor-not-allowed={visibleIndex === 0}
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <div class="flex gap-1">
        {#each Array(Math.ceil(avatars.length / visibleCount)) as _, i}
          <div 
            class="w-2 h-2 rounded-full transition-colors"
            class:bg-blue-500={Math.floor(visibleIndex / visibleCount) === i}
            class:bg-gray-300={Math.floor(visibleIndex / visibleCount) !== i}
          ></div>
        {/each}
      </div>
      
      <button 
        class="flex items-center justify-center w-10 h-10 bg-white dark:bg-gray-800 rounded-full shadow-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        on:click={nextSlide}
        disabled={visibleIndex >= avatars.length - visibleCount}
        class:opacity-50={visibleIndex >= avatars.length - visibleCount}
        class:cursor-not-allowed={visibleIndex >= avatars.length - visibleCount}
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  </div>
</div> 