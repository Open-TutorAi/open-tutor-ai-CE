<!-- LearningPath.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { fly, scale } from 'svelte/transition';
	import { elasticOut } from 'svelte/easing';

	const i18n = getContext<Writable<i18nType>>('i18n');
	
	// Define the type for a learning step
	type LearningStep = {
		id: string;
		title: string;
		completed: boolean;
		current?: boolean;
	};
	
	// Props
	export let steps: LearningStep[] = [];
	
	// Event handler function
	export let onStepClick: (stepId: string) => void = (stepId) => console.log(`Step clicked: ${stepId}`);
	
	// Track whether component is mounted (for animations)
	let mounted = false;
	
	// Hover state for each step
	let hoveredStep: string | null = null;
	
	onMount(() => {
		mounted = true;
	});
</script>

<div class="bg-white dark:bg-gray-800 p-3 sm:p-6 rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-300 relative z-5">
	<div class="relative">
		<!-- Animated vertical line with gradient -->
		<div class="absolute left-auto right-[13px] sm:right-[15px] top-4 bottom-0 w-0.5 bg-gradient-to-b from-blue-600 via-blue-400 to-gray-200 dark:to-gray-700 opacity-60"></div>
		
		<!-- Steps -->
		{#each steps as step, index}
			<div 
				class="flex items-center justify-between mb-4 sm:mb-10 relative z-10 group"
				on:mouseenter={() => hoveredStep = step.id}
				on:mouseleave={() => hoveredStep = null}
				on:focus={() => hoveredStep = step.id}
				on:blur={() => hoveredStep = null}
			>
				<span 
					class={`text-sm sm:text-base font-medium transition-colors duration-200 max-w-[calc(100%-36px)] truncate ${
						step.current 
							? 'text-blue-600 dark:text-blue-400' 
							: hoveredStep === step.id 
								? 'text-gray-800 dark:text-gray-200' 
								: 'text-gray-600 dark:text-gray-300'
					}`}
				>
					{step.title}
					
					<!-- Show small preview on hover -->
					{#if hoveredStep === step.id && !step.completed}
						<div 
							class="absolute left-0 top-6 bg-white dark:bg-gray-700 p-2 rounded-md shadow-md text-xs max-w-[120px] text-gray-600 dark:text-gray-300 z-20"
							transition:fly={{ y: -5, duration: 150 }}
						>
							{$i18n.t('Click to view')}
						</div>
					{/if}
				</span>
				
				<!-- Circle indicators with animations -->
				{#if mounted}
					<div 
						class={`flex-shrink-0 w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center transform transition-all duration-300 ${
							hoveredStep === step.id ? 'scale-110' : ''
						} ${
							step.completed 
								? 'bg-blue-600 shadow-md shadow-blue-200 dark:shadow-blue-900/20' 
								: step.current 
									? 'border-2 border-blue-600 bg-white dark:bg-gray-800 pulse-border' 
									: 'border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
						}`}
						transition:scale={{ 
							delay: index * 100, 
							duration: 350,
							easing: elasticOut,
							start: 0.5
						}}
					>
						{#if step.completed}
							<svg xmlns="http://www.w3.org/2000/svg" class="h-2.5 w-2.5 sm:h-4 sm:w-4 text-white" viewBox="0 0 20 20" fill="currentColor">
								<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
							</svg>
						{:else if step.current}
							<div class="w-1.5 h-1.5 sm:w-2.5 sm:h-2.5 rounded-full bg-blue-600 pulse"></div>
						{/if}
					</div>
				{/if}
				
				<!-- Clickable overlay for the entire row -->
				<button 
					class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
					on:click={() => onStepClick(step.id)}
					aria-label={$i18n.t(`Go to ${step.title}`)}
				></button>
			</div>
		{/each}
	</div>
</div>

<style>
	.pulse {
		animation: pulse 2s infinite;
	}
	
	.pulse-border {
		animation: pulseBorder 2s infinite;
	}
	
	@keyframes pulse {
		0% {
			transform: scale(0.95);
			opacity: 0.8;
		}
		50% {
			transform: scale(1.05);
			opacity: 1;
		}
		100% {
			transform: scale(0.95);
			opacity: 0.8;
		}
	}
	
	@keyframes pulseBorder {
		0% {
			box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.3);
		}
		70% {
			box-shadow: 0 0 0 6px rgba(37, 99, 235, 0);
		}
		100% {
			box-shadow: 0 0 0 0 rgba(37, 99, 235, 0);
		}
	}
	
	/* Additional compact styles for mobile */
	@media (max-width: 480px) {
		:global(.learning-path-container) {
			margin-top: 0 !important;
			padding: 0 !important;
		}
	}
</style> 