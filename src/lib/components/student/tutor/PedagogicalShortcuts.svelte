<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	type ShortcutAction = {
		label: string;
		description: string;
		prompt: string;
	};

	const dispatch = createEventDispatcher<{ select: string }>();

	const shortcutActions: ShortcutAction[] = [
		{
			label: 'Re-explain',
			description: 'Ask for a simpler explanation of the latest concept.',
			prompt:
				'Please re-explain the last concept in simpler terms. Use one analogy, one step-by-step breakdown, and one quick check question at the end.'
		},
		{
			label: 'Example',
			description: 'Request a practical example tied to the topic.',
			prompt:
				'Show me a practical example of the concept we are discussing. Connect it to a real-world use case and explain why each step matters.'
		},
		{
			label: 'Practice',
			description: 'Generate a short formative activity.',
			prompt:
				'Give me a short practice activity for this topic. Ask one question at a time, wait for my answer, then give feedback before moving on.'
		},
		{
			label: 'Summarize',
			description: 'Create a concise learning recap.',
			prompt:
				'Summarize what I have learned so far in this conversation. Include the key ideas, common mistakes to avoid, and two next-step study recommendations.'
		},
		{
			label: 'Adjust level',
			description: 'Ask the tutor to adapt the difficulty.',
			prompt:
				'Adjust the difficulty of the explanation. First ask whether I want beginner, intermediate, or advanced level, then continue using that level.'
		}
	];
</script>

<div class="mx-auto mb-2 flex w-full max-w-4xl flex-wrap gap-2 px-3 sm:px-4">
	{#each shortcutActions as action}
		<button
			type="button"
			class="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 dark:hover:border-indigo-500 dark:hover:bg-indigo-950"
			title={action.description}
			aria-label={`Use pedagogical shortcut: ${action.label}`}
			on:click={() => dispatch('select', action.prompt)}
		>
			{action.label}
		</button>
	{/each}
</div>
