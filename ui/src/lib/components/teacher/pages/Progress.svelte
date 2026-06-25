<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { getClassrooms, getClassProgress, type Classroom } from '$lib/apis/classrooms';

	const i18n: any = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';

	type Row = {
		student_id: string;
		name: string | null;
		status: string;
		supports_total: number;
		last_active: string | null;
		classId: string;
		className: string;
	};

	let classes: Classroom[] = [];
	let rows: Row[] = [];
	let classFilter = 'all';
	let loading = true;

	$: filtered = classFilter === 'all' ? rows : rows.filter((r) => r.classId === classFilter);

	const statusStyle: Record<string, string> = {
		active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
		idle: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
		not_started: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
	};
	const statusLabel: Record<string, string> = {
		active: 'active',
		idle: 'idle',
		not_started: 'not started'
	};

	function fmt(ts: string | null): string {
		return ts ? new Date(ts).toLocaleDateString() : '—';
	}

	onMount(async () => {
		try {
			classes = await getClassrooms(token());
			const all = await Promise.all(
				classes.map(async (c) => {
					const prog = await getClassProgress(token(), c.id);
					return prog.map((p) => ({ ...p, classId: c.id, className: c.name }));
				})
			);
			rows = all.flat();
		} catch (err) {
			rows = [];
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex flex-col gap-6">
	<div>
		<h1 class="text-2xl font-bold text-gray-800 dark:text-white">{$i18n.t('Progress')}</h1>
		<p class="text-gray-500 dark:text-gray-400 mt-1">{$i18n.t('How your students are doing.')}</p>
	</div>

	{#if loading}
		<div class="flex justify-center py-12">
			<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
		</div>
	{:else if rows.length === 0}
		<div
			class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-12 text-center text-gray-500 dark:text-gray-400"
		>
			{$i18n.t('No progress to show yet')} — {$i18n.t('enrol students into a class first.')}
		</div>
	{:else}
		<select
			class="rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 py-2 text-sm text-gray-800 dark:text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300 max-w-xs"
			bind:value={classFilter}
		>
			<option value="all">{$i18n.t('All classes')}</option>
			{#each classes as c}<option value={c.id}>{c.name}</option>{/each}
		</select>

		<div class="overflow-x-auto rounded-2xl bg-white dark:bg-gray-800 shadow-sm">
			<table class="w-full text-left text-sm">
				<thead
					class="text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700"
				>
					<tr>
						<th class="px-5 py-3 font-medium">{$i18n.t('Name')}</th>
						<th class="px-5 py-3 font-medium">{$i18n.t('Class')}</th>
						<th class="px-5 py-3 font-medium">{$i18n.t('Status')}</th>
						<th class="px-5 py-3 font-medium">{$i18n.t('Supports')}</th>
						<th class="px-5 py-3 font-medium">{$i18n.t('Last active')}</th>
						<th class="px-5 py-3"></th>
					</tr>
				</thead>
				<tbody>
					{#each filtered as r (r.classId + r.student_id)}
						<tr class="border-b border-gray-50 dark:border-gray-700/50">
							<td class="px-5 py-3 text-gray-800 dark:text-white">{r.name ?? '—'}</td>
							<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{r.className}</td>
							<td class="px-5 py-3"
								><span class={`text-xs px-2 py-0.5 rounded-full ${statusStyle[r.status]}`}
									>{$i18n.t(statusLabel[r.status])}</span
								></td
							>
							<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{r.supports_total}</td>
							<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{fmt(r.last_active)}</td>
							<td class="px-5 py-3 text-right"
								><button
									class="text-blue-600 dark:text-blue-400 text-xs hover:underline"
									on:click={() => goto(`/teacher/classes/${r.classId}/students/${r.student_id}`)}
									>{$i18n.t('View')}</button
								></td
							>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
