<script lang="ts">
	import { getContext } from 'svelte';
	import type { AttendanceStats } from '$lib/types/classroom';

	const i18n = getContext('i18n');

	export let stats: AttendanceStats;

	$: cards = [
		{
			testid: 'kpi-avg-rate',
			label: 'Taux moyen',
			value: `${stats.avg_rate.toFixed(1)}%`,
			icon: '📊'
		},
		{ testid: 'kpi-sessions', label: 'Séances', value: String(stats.sessions_count), icon: '📅' },
		{
			testid: 'kpi-absences',
			label: 'Absences',
			value: String(stats.total_absences),
			icon: '🚫'
		},
		{ testid: 'kpi-lates', label: 'Retards', value: String(stats.total_lates), icon: '⏰' }
	];
</script>

<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
	{#each cards as card}
		<div data-testid="kpi-card" class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
			<div class="text-2xl mb-1">{card.icon}</div>
			<div data-testid={card.testid} class="text-xl font-bold text-gray-900 dark:text-white">
				{card.value}
			</div>
			<div class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t(card.label)}</div>
		</div>
	{/each}
</div>
