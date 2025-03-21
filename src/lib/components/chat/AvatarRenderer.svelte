<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { settings } from '$lib/stores';
  import type { Writable } from 'svelte/store';

  // Define types for renderer and container
  interface AvatarRenderer {
    initialize: () => Promise<void>;
    dispose: () => void;
  }

  interface Settings {
    darkMode?: boolean;
  }

  // Props
  export const modelPath = 'backend/glb/Masculine_TPose.glb';
  export let visible = true;

  // Container reference
  let avatarContainer: HTMLDivElement;
  let renderer: AvatarRenderer | null = null;

  onMount(async () => {
    // Dynamically import the renderer only on client-side
    if (typeof window !== 'undefined') {
      try {
        // Debug output to help diagnose issues
        console.log('Attempting to load avatar renderer');
        const module = await import('$lib/js/avatar-renderer');
        console.log('Module loaded:', module);
        
        if (module && module.AvatarRenderer) {
          console.log('AvatarRenderer found in module');
          // Initialize avatar once component is mounted
          if (avatarContainer) {
            console.log('Creating avatar renderer with container:', avatarContainer);
            renderer = new module.AvatarRenderer(avatarContainer);
            console.log('Initializing avatar renderer');
            await renderer.initialize();
            console.log('Avatar renderer initialized successfully');
          } else {
            console.error('Avatar container not found');
          }
        } else {
          console.error('AvatarRenderer not found in module');
        }
      } catch (error) {
        console.error('Failed to load avatar renderer:', error);
      }
    }
  });

  onDestroy(() => {
    // Clean up ThreeJS resources on component destruction
    if (renderer) {
      renderer.dispose();
    }
  });

  // Type assertion for settings store
  $: settingsValue = $settings as Settings;
</script>

<div class="avatar-sidebar {visible ? 'visible' : 'hidden'}" class:dark={settingsValue?.darkMode}>
  <div class="avatar-container" bind:this={avatarContainer}></div>
</div>

<style>
  .avatar-sidebar {
    height: 100%;
    width: 100%;
    display: flex;
    flex-direction: column;
    background-color: rgba(45, 50, 80, 0.2);
    border-right: 1px solid rgba(229, 231, 235, 0.1);
  }

  .avatar-sidebar.dark {
    background-color: rgba(30, 33, 50, 0.3);
  }

  .avatar-container {
    flex: 1;
    position: relative;
    overflow: hidden;
  }

  /* Hide avatar on small screens by default */
  @media (max-width: 768px) {
    .avatar-sidebar {
      display: none;
    }
  }
</style>
