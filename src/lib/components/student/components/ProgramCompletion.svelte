<!-- ProgramCompletion.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { tweened } from 'svelte/motion';
	import { cubicOut } from 'svelte/easing';

	const i18n = getContext<Writable<i18nType>>('i18n');
	
	// Props
	export let progress: number = 0;
	export let showOptions: boolean = true;
	
	// Animate the progress value
	const progressTween = tweened(0, {
		duration: 1000,
		easing: cubicOut
	});
	
	// Determine the color class based on progress
	$: progressColorClass = 
		progress < 30 ? 'from-orange-500 to-orange-400' :
		progress < 70 ? 'from-teal-600 to-emerald-500' :
		'from-green-600 to-emerald-400';
		
	onMount(() => {
		// Start the progress animation after component is mounted
		progressTween.set(progress);
	});
</script>

<div class="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-300">
	<div class="flex justify-between items-center mb-2">
		<h2 class="text-base text-gray-500 dark:text-gray-400 font-medium">{$i18n.t('Program Completion')}</h2>
		{#if showOptions}
			<button
				class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors duration-200"
				aria-label={$i18n.t('View completion options')}
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
					<path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
				</svg>
			</button>
		{/if}
	</div>
	
	<div class="text-4xl font-bold text-gray-800 dark:text-white mb-2">{Math.round($progressTween)}%</div>
	
	<div 
		class="w-full bg-teal-50 dark:bg-teal-900/10 rounded-full h-2 overflow-hidden"
		role="progressbar" 
		aria-valuenow={progress} 
		aria-valuemin="0" 
		aria-valuemax="100"
	>
		<div 
			class={`h-2 rounded-full bg-gradient-to-r ${progressColorClass}`} 
			style={`width: ${$progressTween}%; transition: width 0.3s ease-out;`}
		></div>
	</div>
</div>

<style>
	@keyframes pulse {
		0% {
			opacity: 0.8;
		}
		50% {
			opacity: 1;
		}
		100% {
			opacity: 0.8;
		}
	}
</style> 