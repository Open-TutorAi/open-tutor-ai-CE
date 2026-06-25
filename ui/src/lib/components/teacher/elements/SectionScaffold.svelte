<script lang="ts">
	import { getContext } from 'svelte';
	import { goto } from '$app/navigation';

	const i18n: any = getContext('i18n');

	export let title: string;
	export let subtitle: string = '';
	export let emptyTitle: string = '';
	export let emptyText: string = '';
	export let ctaLabel: string = '';
	export let ctaHref: string = '';
	export let accent: 'blue' | 'emerald' | 'violet' | 'amber' = 'blue';

	const accentMap: Record<string, string> = {
		blue: 'bg-blue-50 text-blue-500 dark:bg-blue-900/30 dark:text-blue-300',
		emerald: 'bg-emerald-50 text-emerald-500 dark:bg-emerald-900/30 dark:text-emerald-300',
		violet: 'bg-violet-50 text-violet-500 dark:bg-violet-900/30 dark:text-violet-300',
		amber: 'bg-amber-50 text-amber-500 dark:bg-amber-900/30 dark:text-amber-300'
	};
</script>

<div class="flex flex-col gap-6">
	<!-- Header -->
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold text-gray-800 dark:text-white">{$i18n.t(title)}</h1>
			{#if subtitle}
				<p class="text-gray-500 dark:text-gray-400 mt-1">{$i18n.t(subtitle)}</p>
			{/if}
		</div>
		{#if ctaLabel && ctaHref}
			<button
				class="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full transition shadow-sm"
				on:click={() => goto(ctaHref)}
			>
				+ {$i18n.t(ctaLabel)}
			</button>
		{/if}
	</div>

	<!-- Empty state -->
	<div
		class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-12 text-center"
	>
		<div class={`mx-auto h-14 w-14 rounded-2xl grid place-items-center mb-4 ${accentMap[accent]}`}>
			<slot name="icon" />
		</div>
		<h3 class="text-lg font-semibold text-gray-800 dark:text-white">
			{$i18n.t(emptyTitle || 'Nothing here yet')}
		</h3>
		{#if emptyText}
			<p class="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-5 max-w-sm mx-auto">
				{$i18n.t(emptyText)}
			</p>
		{/if}
		{#if ctaLabel && ctaHref}
			<button
				class="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full transition shadow-sm"
				on:click={() => goto(ctaHref)}
			>
				+ {$i18n.t(ctaLabel)}
			</button>
		{/if}
	</div>
</div>
