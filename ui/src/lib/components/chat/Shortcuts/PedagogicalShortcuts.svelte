<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	const dispatch = createEventDispatcher();
	const i18n: any = getContext('i18n');

	let currentView = 'main';

	$: understandActions = [
		{
			label: $i18n.t('Analogy'),
			icon: '🔁',
			prompt: $i18n.t(
				'Explain this concept using a creative analogy from everyday life to make the abstract ideas more concrete and relatable.'
			)
		},
		{
			label: $i18n.t('Example'),
			icon: '💡',
			prompt: $i18n.t(
				'Give me a concrete, real-world application of this concept. Show me how it works in a practical scenario I might actually encounter.'
			)
		},
		{
			label: $i18n.t('Visual'),
			icon: '📊',
			prompt: $i18n.t(
				'Organize the key components of this topic into a clear Markdown table or a structured list to help me visualize the relationships between ideas.'
			)
		}
	];

	$: quizActions = [
		{
			label: $i18n.t('Open Ended'),
			icon: '💬',
			prompt: $i18n.t(
				'Ask me one challenging open-ended question that requires a detailed explanation to test my memory and comprehension of what we just discussed.'
			)
		},
		{
			label: $i18n.t('Multiple Choice'),
			icon: '🧩',
			prompt: $i18n.t(
				'Provide 3 Multiple Choice Questions with distinct options to test if I can identify the correct logic among common misconceptions.'
			)
		},
		{
			label: $i18n.t('Concept Link'),
			icon: '🔗',
			prompt: $i18n.t(
				'Pick two distinct concepts we just discussed and ask me to explain the relationship or connection between them to test my ability to synthesize the information.'
			)
		}
	];

	$: difficultyLevels = [
		{
			label: $i18n.t('Beginner'),
			icon: '🟢',
			color: 'rgba(34, 197, 94, 0.15)',
			border: 'rgba(34, 197, 94, 0.3)',
			text: '#4ade80',
			prompt: $i18n.t(
				'Explain the current topic using very simple language and basic analogies, as if I am 5 years old.'
			)
		},
		{
			label: $i18n.t('Intermediate'),
			icon: '🟡',
			color: 'rgba(234, 179, 8, 0.15)',
			border: 'rgba(234, 179, 8, 0.3)',
			text: '#facc15',
			prompt: $i18n.t(
				'Explain this concept with more depth, using standard technical terms where appropriate but ensuring the core logic remains clear and accessible.'
			)
		},
		{
			label: $i18n.t('Advanced'),
			icon: '🔴',
			color: 'rgba(239, 68, 68, 0.15)',
			border: 'rgba(239, 68, 68, 0.3)',
			text: '#f87171',
			prompt: $i18n.t(
				'Provide a deep-dive, technical explanation of the current topic, including nuances and complex details.'
			)
		}
	];

	function sendAction(prompt: string) {
		dispatch('submit', prompt);
		currentView = 'main';
	}
</script>

<div class="shortcut-row">
	{#if currentView === 'main'}
		<button
			type="button"
			on:click={() => (currentView = 'difficulty')}
			class="nav-button menu-theme"
		>
			<span>🎚️</span>
			{$i18n.t('Difficulty')} <span class="chevron">›</span>
		</button>

		<button
			type="button"
			on:click={() => (currentView = 'understand')}
			class="nav-button menu-theme"
		>
			<span>🔍</span>
			{$i18n.t('Understand')} <span class="chevron">›</span>
		</button>

		<button
			type="button"
			on:click={() =>
				sendAction(
					$i18n.t(
						'Synthesize our conversation into 3-5 high-impact bullet points that capture the "must-know" essentials of this topic.'
					)
				)}
			class="nav-button"
		>
			<span>📝</span>
			{$i18n.t('Summarize')}
		</button>

		<button
			type="button"
			on:click={() =>
				sendAction(
					$i18n.t(
						'Based on what we just covered, what is the most logical next concept I should learn? Briefly introduce it and show me how it connects to this.'
					)
				)}
			class="nav-button"
		>
			<span>⏭️</span>
			{$i18n.t('Next Step')}
		</button>

		<button type="button" on:click={() => (currentView = 'quiz')} class="nav-button menu-theme">
			<span>🧠</span>
			{$i18n.t('Quiz')} <span class="chevron">›</span>
		</button>
	{:else if currentView === 'difficulty'}
		<button type="button" on:click={() => (currentView = 'main')} class="nav-button back-button">
			<span>⬅️</span>
			{$i18n.t('Back')}
		</button>
		{#each difficultyLevels as level}
			<button
				type="button"
				on:click={() => sendAction(level.prompt)}
				class="nav-button pulse-animation"
				style="background: {level.color}; border-color: {level.border}; color: {level.text}"
			>
				<span>{level.icon}</span>
				{level.label}
			</button>
		{/each}
	{:else if currentView === 'understand'}
		<button type="button" on:click={() => (currentView = 'main')} class="nav-button back-button">
			<span>⬅️</span>
			{$i18n.t('Back')}
		</button>
		{#each understandActions as action}
			<button
				type="button"
				on:click={() => sendAction(action.prompt)}
				class="nav-button pulse-animation"
			>
				<span>{action.icon}</span>
				{action.label}
			</button>
		{/each}
	{:else if currentView === 'quiz'}
		<button type="button" on:click={() => (currentView = 'main')} class="nav-button back-button">
			<span>⬅️</span>
			{$i18n.t('Back')}
		</button>
		{#each quizActions as action}
			<button
				type="button"
				on:click={() => sendAction(action.prompt)}
				class="nav-button pulse-animation"
			>
				<span>{action.icon}</span>
				{action.label}
			</button>
		{/each}
	{/if}
</div>

<style>
	.shortcut-row {
		display: flex;
		flex-wrap: nowrap;
		overflow-x: auto;
		gap: 12px;
		width: 100%;
		margin-bottom: 8px;
		margin-top: 5px;
		padding-bottom: 4px;
		align-items: center;
	}

	.no-scrollbar::-webkit-scrollbar {
		display: none;
	}
	.no-scrollbar {
		-ms-overflow-style: none;
		scrollbar-width: none;
	}

	.nav-button {
		flex: 0 0 auto;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		padding: 8px 14px;
		background: rgba(255, 255, 255, 0.08);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		font-size: 14px;
		color: #ececec;
		transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
		white-space: nowrap;
	}

	.nav-button:hover {
		filter: brightness(1.2);
		background: rgba(255, 255, 255, 0.15);
		transform: translateY(-1px);
	}

	.chevron {
		opacity: 0.5;
		font-size: 16px;
		margin-left: 2px;
	}

	.menu-theme {
		background: rgba(59, 130, 246, 0.15);
		border-color: rgba(59, 130, 246, 0.3);
		color: #60a5fa;
	}

	.back-button {
		background: transparent;
		border: 1px dashed rgba(255, 255, 255, 0.2);
		color: #9ca3af;
	}

	.pulse-animation {
		animation: pulse-border 1.5s ease-out 1;
	}

	@keyframes pulse-border {
		0% {
			box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.2);
		}
		70% {
			box-shadow: 0 0 0 8px rgba(255, 255, 255, 0);
		}
		100% {
			box-shadow: 0 0 0 0 rgba(255, 255, 255, 0);
		}
	}
</style>
