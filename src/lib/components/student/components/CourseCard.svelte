<!-- CourseCard.svelte -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	export let title: string;
	export let progress: number;
	export let subject: string;
	export let href: string;

	// Subject configuration based on SupportCreation.svelte
	const subjectConfig: Record<string, { icon: string; color: string }> = {
		mathematics: { icon: '📊', color: 'bg-blue-50 dark:bg-blue-900/10' },
		science: { icon: '🔬', color: 'bg-teal-50 dark:bg-teal-900/10' },
		history: { icon: '🏛️', color: 'bg-amber-50 dark:bg-amber-900/10' },
		'computer-science': { icon: '💻', color: 'bg-indigo-50 dark:bg-indigo-900/10' },
		english: { icon: '📚', color: 'bg-purple-50 dark:bg-purple-900/10' },
		geography: { icon: '🌍', color: 'bg-green-50 dark:bg-green-900/10' },
		chemistry: { icon: '🔬', color: 'bg-rose-50 dark:bg-rose-900/10' },
		biology: { icon: '🌿', color: 'bg-emerald-50 dark:bg-emerald-900/10' },
		physics: { icon: '⚛️', color: 'bg-cyan-50 dark:bg-cyan-900/10' }
	};

	// Get subject config or fallback to mathematics if subject not found
	$: subjectStyle = subjectConfig[subject] || subjectConfig.mathematics;

	function handleClick() {
		goto(href);
	}
</script>

<button
	class={`block w-full p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-200 relative overflow-hidden group ${subjectStyle.color}`}
	on:click={handleClick}
>
	<div class="flex items-start justify-between mb-4">
		<div class="p-3 rounded-full bg-white dark:bg-gray-800 shadow-sm">
			<span class="text-2xl leading-none">{subjectStyle.icon}</span>
		</div>
	</div>

	<h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4 group-hover:text-gray-900 dark:group-hover:text-white transition-colors text-left">
		{title}
	</h3>

	<div class="relative pt-1">
		<div class="flex mb-2 items-center justify-between">
			<div>
				<span class="text-xs font-semibold inline-block text-gray-600 dark:text-gray-400">
					{progress}% {$i18n.t('Complete')}
				</span>
			</div>
		</div>
		<div class="overflow-hidden h-2 text-xs flex rounded bg-gray-200 dark:bg-gray-700">
			<div
				style="width: {progress}%"
				class="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-indigo-500 dark:bg-indigo-600 transition-all"
			></div>
		</div>
	</div>
</button> 