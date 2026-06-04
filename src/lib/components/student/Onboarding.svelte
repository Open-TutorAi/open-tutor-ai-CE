<script lang="ts">
	import { onMount } from 'svelte';

	export let onComplete: () => void = () => {};

	let step = 1;
	let tooltipStyle = 'display: none;';
	let show = true;
	let interval: number | null = null;
	let arrowClass = '';

	function getTargetSelector(): string {
		if (step === 1) return 'aside';
		if (step === 2) return '.card-container';
		return '#create-support-btn';
	}

	function findAndPosition() {
		const selector = getTargetSelector();
		const element = document.querySelector(selector);
		if (element) {
			const rect = element.getBoundingClientRect();
			if (step === 1) {
				tooltipStyle = `top: ${rect.top + rect.height / 2 - 70}px; left: ${rect.right + 15}px; display: block;`;
				arrowClass = 'arrow-left';
			} else if (step === 2) {
				// Get sidebar (aside) right edge
				const sidebar = document.querySelector('aside');
				let leftPos = rect.left + rect.width / 2 - 160; // default centered
				if (sidebar) {
					const sidebarRect = sidebar.getBoundingClientRect();
					// Ensure at least 20px gap from sidebar's right edge
					const minLeft = sidebarRect.right + 20;
					if (leftPos < minLeft) {
						leftPos = minLeft;
					}
				}
				tooltipStyle = `top: ${rect.top - 110}px; left: ${leftPos}px; display: block;`;
				arrowClass = 'arrow-down';
			} else {
				tooltipStyle = `top: ${rect.bottom + 15}px; left: ${rect.left + rect.width / 2 - 160}px; display: block;`;
				arrowClass = 'arrow-up';
			}
			if (interval) clearInterval(interval);
		} else {
			if (step === 2) {
				// Fallback center screen
				tooltipStyle = 'top: 50%; left: 50%; transform: translate(-50%, -50%); display: block;';
				arrowClass = '';
			} else {
				tooltipStyle = 'display: none;';
			}
		}
	}

	function startSearching() {
		if (interval) clearInterval(interval);
		findAndPosition();
		interval = setInterval(findAndPosition, 300);
	}

	onMount(() => {
		startSearching();
	});

	function next() {
		if (step < 3) {
			step++;
			startSearching();
		} else {
			localStorage.setItem('onboardingDone', 'true');
			show = false;
			if (interval) clearInterval(interval);
			onComplete();
		}
	}
</script>

{#if show}
	<div class="fixed inset-0 z-50 pointer-events-none">
		<div class="absolute inset-0 bg-black/60 pointer-events-auto" on:click={next}></div>
		<div
			class="absolute bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-5 max-w-sm pointer-events-auto tooltip-bubble {arrowClass}"
			style={tooltipStyle}
		>
			{#if step === 1}
				<div class="font-bold text-indigo-600 text-lg">Your Personal Menu</div>
				<p class="text-gray-700 dark:text-gray-300 mt-2">Here you'll find all sections: Dashboard, Classes, Support, etc.</p>
			{:else if step === 2}
				<div class="font-bold text-indigo-600 text-lg">Your Courses</div>
				<p class="text-gray-700 dark:text-gray-300 mt-2">Your courses will appear here once you add them.</p>
			{:else}
				<div class="font-bold text-indigo-600 text-lg">Homework & Support</div>
				<p class="text-gray-700 dark:text-gray-300 mt-2">Ready to learn? Use the Support button to ask questions or view your assignments.</p>
			{/if}
			<button on:click={next} class="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition">
				{step === 3 ? "Let's go!" : "Next →"}
			</button>
		</div>
	</div>
{/if}

<style>
	.tooltip-bubble {
		position: absolute;
	}

	/* Arrow pointing LEFT (tooltip on the right of sidebar) */
	.tooltip-bubble.arrow-left::before {
		content: '';
		position: absolute;
		left: -8px;
		top: 50%;
		transform: translateY(-50%);
		border-width: 8px 8px 8px 0;
		border-style: solid;
		border-color: transparent white transparent transparent;
	}

	/* Arrow pointing UP (tooltip below the button) */
	.tooltip-bubble.arrow-up::before {
		content: '';
		position: absolute;
		top: -8px;
		left: 50%;
		transform: translateX(-50%);
		border-width: 0 8px 8px 8px;
		border-style: solid;
		border-color: transparent transparent white transparent;
	}

	/* Arrow pointing DOWN (tooltip above the grid) */
	.tooltip-bubble.arrow-down::before {
		content: '';
		position: absolute;
		bottom: -8px;
		left: 50%;
		transform: translateX(-50%);
		border-width: 8px 8px 0 8px;
		border-style: solid;
		border-color: white transparent transparent transparent;
	}

	/* Dark mode support */
	:global(.dark) .tooltip-bubble.arrow-left::before {
		border-right-color: #1f2937;
	}
	:global(.dark) .tooltip-bubble.arrow-up::before {
		border-bottom-color: #1f2937;
	}
	:global(.dark) .tooltip-bubble.arrow-down::before {
		border-top-color: #1f2937;
	}
</style>