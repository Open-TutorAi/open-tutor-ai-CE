<script lang="ts">
	import { getContext } from 'svelte';
	import type { StudentHistory } from '$lib/types/classroom';
	import AttendanceDonut from '$lib/components/attendance/AttendanceDonut.svelte';
	import StudentAvatar from '$lib/components/StudentAvatar.svelte';

	const i18n = getContext('i18n');

	export let history: StudentHistory;
	export let studentName: string = '';

	const CIRCLE_COLORS: Record<string, string> = {
		PRESENT: 'bg-green-500',
		ABSENT: 'bg-red-500',
		LATE: 'bg-orange-500'
	};

	$: total = history.presences + history.absences + history.lates;
	$: absenceRate = total > 0 ? (history.absences / total) * 100 : 0;
</script>

<div data-testid="student-history-panel" class="space-y-4">
	{#if studentName}
		<div class="flex items-center gap-2">
			<StudentAvatar name={studentName} size="md" />
			<span class="font-medium text-gray-900 dark:text-white">{studentName}</span>
		</div>
	{/if}

	<div class="flex items-center gap-6">
		<AttendanceDonut present={history.presences} absent={history.absences} late={history.lates} />
		<div class="flex gap-6">
			<div>
				<div
					class="text-2xl font-bold text-green-600 dark:text-green-400"
					data-testid="presence-rate"
				>
					{history.rate.toFixed(1)}%
				</div>
				<div class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Taux de présence')}</div>
			</div>
			<div>
				<div class="text-2xl font-bold text-red-600 dark:text-red-400" data-testid="absence-rate">
					{absenceRate.toFixed(1)}%
				</div>
				<div class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t("Taux d'absence")}</div>
			</div>
		</div>
	</div>

	<div class="flex gap-4 text-sm text-gray-700 dark:text-gray-300">
		<span>{$i18n.t('Présences')}: {history.presences}</span>
		<span>{$i18n.t('Absences')}: {history.absences}</span>
		<span>{$i18n.t('Retards')}: {history.lates}</span>
	</div>

	<div>
		<div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
			{$i18n.t('10 dernières séances')}
		</div>
		<div class="flex gap-1">
			{#each history.last_10 as status}
				<div
					data-testid="history-circle"
					title={status}
					class="w-4 h-4 rounded-full {CIRCLE_COLORS[status] ?? 'bg-gray-300'}"
				></div>
			{/each}
		</div>
	</div>
</div>
