<script lang="ts">
	import { getContext } from 'svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	
	const i18n = getContext('i18n');
	
	export let onAction: (action: string, prompt: string) => void;
	export let disabled: boolean = false;
	
	const shortcuts = [
		{
			id: 're-explain',
			icon: '📖',
			label: 'Re-explain this concept',
			prompt: 'Please re-explain the last concept we discussed using simpler terms, analogies, and step-by-step breakdowns. Make it easier to understand.',
			color: 'bg-blue-500 hover:bg-blue-600'
		},
		{
			id: 'continue',
			icon: '➡️',
			label: 'Continue to the next learning step',
			prompt: 'I understand the current concept. Please advance to the next stage of the personalized learning support based on the lesson plan.',
			color: 'bg-green-500 hover:bg-green-600'
		},
		{
			id: 'example',
			icon: '💡',
			label: 'Show me a practical example',
			prompt: 'Can you provide a real-world or illustrative example related to what we just discussed? I learn better with concrete examples.',
			color: 'bg-yellow-500 hover:bg-yellow-600'
		},
		{
			id: 'quiz',
			icon: '🧪',
			label: 'Give me a quiz or activity',
			prompt: 'Please provide a short quiz or exercise to reinforce the concepts we\'ve covered. Include 3 questions from the current lesson and 2 from previous topics.',
			color: 'bg-purple-500 hover:bg-purple-600'
		},
		{
			id: 'summarize',
			icon: '📝',
			label: 'Summarize what I have learned',
			prompt: 'Can you generate a summary of the key points we\'ve discussed so far? Help me consolidate my understanding.',
			color: 'bg-orange-500 hover:bg-orange-600'
		},
		{
			id: 'adjust-difficulty',
			icon: '📊',
			label: 'Adjust difficulty level',
			prompt: 'I would like to adjust the difficulty level of our learning session. Please ask me if I want simpler explanations (beginner), current level (intermediate), or more advanced content (expert), then adjust accordingly.',
			color: 'bg-pink-500 hover:bg-pink-600'
		}
	];
	
	function handleAction(shortcut: any) {
		if (!disabled) {
			onAction(shortcut.id, shortcut.prompt);
		}
	}
</script>

<div class="pedagogical-shortcuts w-full py-2 px-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
	<div class="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hidden">
		<span class="text-xs font-medium text-gray-600 dark:text-gray-400 whitespace-nowrap mr-2">
			{$i18n.t('Quick Actions')}:
		</span>
		
		{#each shortcuts as shortcut}
			<Tooltip content={shortcut.label} placement="top">
				<button
					class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-white text-xs font-medium 
					       transition-all duration-200 whitespace-nowrap shadow-sm hover:shadow-md
					       {shortcut.color} {disabled ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'}"
					on:click={() => handleAction(shortcut)}
					disabled={disabled}
					aria-label={shortcut.label}
				>
					<span class="text-sm">{shortcut.icon}</span>
					<span class="hidden sm:inline">{shortcut.label}</span>
				</button>
			</Tooltip>
		{/each}
	</div>
</div>

<style>
	.pedagogical-shortcuts {
		scrollbar-width: none;
	}
	
	.pedagogical-shortcuts::-webkit-scrollbar {
		display: none;
	}
	
	.scrollbar-hidden {
		scrollbar-width: none;
		-ms-overflow-style: none;
	}
	
	.scrollbar-hidden::-webkit-scrollbar {
		display: none;
	}
</style>

