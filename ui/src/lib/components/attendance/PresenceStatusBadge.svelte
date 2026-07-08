<script lang="ts">
	import { getContext } from 'svelte';
	import type { PresenceStatus } from '$lib/types/classroom';

	const i18n = getContext('i18n');

	export let status: PresenceStatus;

	const STYLES: Record<PresenceStatus, string> = {
		PRESENT: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
		ABSENT: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
		LATE: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'
	};

	const LABELS: Record<PresenceStatus, string> = {
		PRESENT: 'Présent',
		ABSENT: 'Absent',
		LATE: 'Retard'
	};
</script>

<span
	data-testid="presence-status-badge"
	class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium {STYLES[status]}"
>
	{$i18n.t(LABELS[status])}
</span>
