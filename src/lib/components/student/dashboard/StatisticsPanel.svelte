<script lang="ts">
    import { getContext } from 'svelte';
    import type { Writable } from 'svelte/store';
    import type { i18n as i18nType } from 'i18next';

    const i18n = getContext<Writable<i18nType>>('i18n');

    export let totalSupports: number = 0;
    export let activeSupports: number = 0;
    export let completedSupports: number = 0;
    export let animCompletionRate: number = 0;
    export let topSubjects: Array<{ name: string; count: number }> = [];

    export let ringOffset: number        = 0;
    export let ringCirc: number          = 0;
    export let ringR: number             = 52;

    // Helper to get progress bar width for a subject count
    $: getPercent = (count: number) => {
        if (totalSupports === 0) return 0;
        return (count / totalSupports) * 100;
    };
</script>

<!-- ▌1. STATISTICS PANEL ▐ -->
<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 p-5 flex flex-col gap-4">
	<h3 class="text-base font-bold text-gray-800 dark:text-white">{$i18n.t('Statistics')}</h3>
	<div class="flex flex-col sm:flex-row items-center gap-5">
		<!-- Stat bars -->
		<div class="flex flex-col gap-3 flex-1 w-full">
			{#if topSubjects && topSubjects.length > 0}
				{#each topSubjects as subject, idx}
					{@const pct = getPercent(subject.count)}
					<div class="flex items-center gap-3">
						<div class="w-9 h-9 rounded-full flex items-center justify-center shrink-0 
							{idx === 0 ? 'bg-indigo-100 dark:bg-indigo-900/30' : 
							 idx === 1 ? 'bg-emerald-100 dark:bg-emerald-900/30' : 
							 'bg-amber-100 dark:bg-amber-900/30'}">
							<svg class="w-5 h-5 {idx === 0 ? 'text-indigo-500' : idx === 1 ? 'text-emerald-500' : 'text-amber-500'}" fill="currentColor" viewBox="0 0 24 24">
								{#if idx === 0}
									<path d="M12 3L1 9l11 6 9-4.91V17h2V9L12 3z"/>
								{:else if idx === 1}
									<path d="M12 11.55C9.64 9.35 6.48 8 3 8v11c3.48 0 6.64 1.35 9 3.55 2.36-2.2 5.52-3.55 9-3.55V8c-3.48 0-6.64 1.35-9 3.55z"/>
								{:else}
									<path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
								{/if}
							</svg>
						</div>
						<div class="flex-1">
							<div class="flex justify-between mb-1">
								<span class="text-xs font-medium text-gray-600 dark:text-gray-300">{subject.name || $i18n.t('Autre')}</span>
								<span class="text-xs font-bold {idx === 0 ? 'text-indigo-500' : idx === 1 ? 'text-emerald-500' : 'text-amber-500'}">
									{subject.count} {subject.count > 1 ? $i18n.t('supports') : $i18n.t('support')}
								</span>
							</div>
							<div class="h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
								<div class="h-full rounded-full {idx === 0 ? 'bg-indigo-500' : idx === 1 ? 'bg-emerald-500' : 'bg-amber-500'}" style="width:{pct}%"></div>
							</div>
						</div>
					</div>
				{/each}
			{:else}
				<!-- Fallback if no subjects -->
				<div class="flex flex-col gap-2">
					<div class="flex items-center gap-3">
						<div class="w-9 h-9 rounded-full flex items-center justify-center bg-indigo-100 dark:bg-indigo-900/30 shrink-0">
							<svg class="w-5 h-5 text-indigo-500" fill="currentColor" viewBox="0 0 24 24">
								<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
							</svg>
						</div>
						<div class="flex-1">
							<div class="flex justify-between mb-1">
								<span class="text-xs font-medium text-gray-600 dark:text-gray-300">{$i18n.t('Active Supports')}</span>
								<span class="text-xs font-bold text-indigo-500">{activeSupports}</span>
							</div>
							<div class="h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
								<div class="h-full rounded-full bg-indigo-500" style="width:{totalSupports > 0 ? (activeSupports / totalSupports) * 100 : 0}%"></div>
							</div>
						</div>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-9 h-9 rounded-full flex items-center justify-center bg-emerald-100 dark:bg-emerald-900/30 shrink-0">
							<svg class="w-5 h-5 text-emerald-500" fill="currentColor" viewBox="0 0 24 24">
								<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
							</svg>
						</div>
						<div class="flex-1">
							<div class="flex justify-between mb-1">
								<span class="text-xs font-medium text-gray-600 dark:text-gray-300">{$i18n.t('Completed Supports')}</span>
								<span class="text-xs font-bold text-emerald-500">{completedSupports}</span>
							</div>
							<div class="h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
								<div class="h-full rounded-full bg-emerald-500" style="width:{totalSupports > 0 ? (completedSupports / totalSupports) * 100 : 0}%"></div>
							</div>
						</div>
					</div>
				</div>
			{/if}
		</div>

		<!-- Circular grades ring -->
		<div class="flex flex-col items-center shrink-0">
			<div class="relative w-28 h-28">
				<svg class="w-full h-full -rotate-90" viewBox="0 0 128 128">
					<circle cx="64" cy="64" r={ringR} fill="none" stroke="#e5e7eb" class="dark:stroke-gray-700" stroke-width="10"/>
					<circle cx="64" cy="64" r={ringR} fill="none" stroke="#6366f1" stroke-width="10"
						stroke-linecap="round" stroke-dasharray={ringCirc} stroke-dashoffset={ringOffset}/>
				</svg>
				<div class="absolute inset-0 flex flex-col items-center justify-center">
					<span class="text-xl font-extrabold text-gray-800 dark:text-white">{Math.round(animCompletionRate)}%</span>
					<span class="text-[9px] text-gray-400 dark:text-gray-500 text-center leading-tight px-1">{$i18n.t('Completion Rate')}</span>
				</div>
			</div>
		</div>
	</div>
</div>