<script lang="ts">
	import { isFullscreenAvatar } from '$lib/stores';
	
	export let onClick: () => void;
	
	$: isFullscreen = $isFullscreenAvatar;
</script>

<button
	class="absolute top-12 right-4 z-50 p-3 rounded-full bg-white/10 dark:bg-black/30 
	       backdrop-blur-sm hover:bg-white/20 dark:hover:bg-black/40 
	       transition-all duration-300 shadow-lg group hover:scale-110"
	on:click={onClick}
	aria-label={isFullscreen ? 'Exit Full Screen' : 'Enter Full Screen'}
	title={isFullscreen ? 'Exit Full Screen (ESC)' : 'Enter Full Screen'}
>
	{#if isFullscreen}
		<!-- Exit fullscreen icon (compress arrows) -->
		<svg 
			class="w-6 h-6 text-white transition-transform duration-300 group-hover:rotate-90" 
			fill="none" 
			stroke="currentColor" 
			viewBox="0 0 24 24" 
			xmlns="http://www.w3.org/2000/svg"
		>
			<path 
				stroke-linecap="round" 
				stroke-linejoin="round" 
				stroke-width="2" 
				d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M15 9V4.5M15 9h4.5M15 9l5.25-5.25M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 15v4.5m0-4.5h4.5m-4.5 0l5.25 5.25"
			/>
		</svg>
	{:else}
		<!-- Enter fullscreen icon (expand arrows) -->
		<svg 
			class="w-6 h-6 text-white transition-transform duration-300 group-hover:scale-110" 
			fill="none" 
			stroke="currentColor" 
			viewBox="0 0 24 24" 
			xmlns="http://www.w3.org/2000/svg"
		>
			<path 
				stroke-linecap="round" 
				stroke-linejoin="round" 
				stroke-width="2" 
				d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15"
			/>
		</svg>
	{/if}
</button>

<style>
	button {
		-webkit-tap-highlight-color: transparent;
	}
</style>

