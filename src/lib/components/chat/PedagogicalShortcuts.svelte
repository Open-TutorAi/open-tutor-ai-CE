<script lang="ts">
	import { getContext } from 'svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	
	const i18n = getContext('i18n');
	
	export let onAction: (action: string, prompt: string) => void;
	export let disabled: boolean = false;
	
	$: shortcuts = [
		{
			id: 're-explain',
			label: $i18n.t('Re-explain'),
			shortLabel: $i18n.t('Re-explain'),
			prompt: $i18n.t('Please re-explain the last concept we discussed using simpler terms, analogies, and step-by-step breakdowns. Make it easier to understand.'),
			svg: '<path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />'
		},
		{
			id: 'continue',
			label: $i18n.t('Next Step'),
			shortLabel: $i18n.t('Next'),
			prompt: $i18n.t('I understand the current concept. Please advance to the next stage of the personalized learning support based on the lesson plan.'),
			svg: '<path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />'
		},
		{
			id: 'example',
			label: $i18n.t('Example'),
			shortLabel: $i18n.t('Example'),
			prompt: $i18n.t('Can you provide a real-world or illustrative example related to what we just discussed? I learn better with concrete examples.'),
			svg: '<path stroke-linecap="round" stroke-linejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />'
		},
		{
			id: 'quiz',
			label: $i18n.t('Quiz Me'),
			shortLabel: $i18n.t('Quiz'),
			prompt: $i18n.t('Please provide a short quiz or exercise to reinforce the concepts we\'ve covered. Include 3 questions from the current lesson and 2 from previous topics.'),
			svg: '<path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />'
		},
		{
			id: 'summarize',
			label: $i18n.t('Summary'),
			shortLabel: $i18n.t('Summary'),
			prompt: $i18n.t('Can you generate a summary of the key points we\'ve discussed so far? Help me consolidate my understanding.'),
			svg: '<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" />'
		},
		{
			id: 'adjust-difficulty',
			label: $i18n.t('Difficulty'),
			shortLabel: $i18n.t('Level'),
			prompt: $i18n.t('I would like to adjust the difficulty level of our learning session. Please ask me if I want simpler explanations (beginner), current level (intermediate), or more advanced content (expert), then adjust accordingly.'),
			svg: '<path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />'
		}
	];
	
	function handleAction(shortcut: any) {
		if (!disabled) {
			onAction(shortcut.id, shortcut.prompt);
		}
	}
</script>

<div class="shortcuts-wrapper w-full mb-3">
	<div class="flex items-center justify-center gap-2.5">
		{#each shortcuts as shortcut}
			<Tooltip content={shortcut.label} placement="top">
				<button
					class="shortcut-btn group flex items-center gap-2 px-3.5 py-2 
					       bg-black/20 backdrop-blur-md
					       border border-white/10
					       rounded-lg text-white/90 text-sm font-normal
					       transition-all duration-200 ease-in-out
					       {disabled ? 'opacity-30 cursor-not-allowed' : 'hover:bg-black/30 hover:border-white/20 hover:text-white'}"
					on:click={() => handleAction(shortcut)}
					disabled={disabled}
					aria-label={shortcut.label}
				>
					<svg 
						xmlns="http://www.w3.org/2000/svg" 
						fill="none" 
						viewBox="0 0 24 24" 
						stroke-width="1.5" 
						stroke="currentColor" 
						class="w-4 h-4 opacity-80 group-hover:opacity-100 transition-opacity"
					>
						{@html shortcut.svg}
					</svg>
					<span class="hidden md:inline whitespace-nowrap">{shortcut.shortLabel}</span>
				</button>
			</Tooltip>
		{/each}
	</div>
</div>

<style>
	.shortcuts-wrapper {
		animation: fadeIn 0.5s ease-out;
	}
	
	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
	
	.shortcut-btn {
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
	}
	
	.shortcut-btn:hover:not(:disabled) {
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
	}
	
	.shortcut-btn:active:not(:disabled) {
		transform: translateY(1px);
	}
</style>


