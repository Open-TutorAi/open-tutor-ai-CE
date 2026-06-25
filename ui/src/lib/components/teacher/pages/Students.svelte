<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { getStudentsDirectory, type DirectoryStudent } from '$lib/apis/classrooms';

	const i18n: any = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';

	let students: DirectoryStudent[] = [];
	let loading = true;
	let classFilter = 'all';
	let query = '';

	$: classes = Array.from(
		new Map(students.flatMap((s) => s.classes).map((c) => [c.id, c])).values()
	);
	$: filtered = students.filter(
		(s) =>
			(classFilter === 'all' || s.classes.some((c) => c.id === classFilter)) &&
			(s.name ?? s.email ?? '').toLowerCase().includes(query.toLowerCase())
	);

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

	function fmtDate(ts: string | null): string {
		return ts ? new Date(ts).toLocaleDateString() : '—';
	}
	function openStudent(s: DirectoryStudent) {
		// Open the student in the context of their first class.
		if (s.classes.length) goto(`/teacher/classes/${s.classes[0].id}/students/${s.student_id}`);
	}

	onMount(async () => {
		try {
			students = await getStudentsDirectory(token());
		} catch (err) {
			/* leave empty */
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex flex-col gap-6">
	<div>
		<h1 class="text-2xl font-bold text-gray-800 dark:text-white">{$i18n.t('Students')}</h1>
		<p class="text-gray-500 dark:text-gray-400 mt-1">
			{$i18n.t('All your students across classes.')}
		</p>
	</div>

	<div class="flex flex-col sm:flex-row gap-3 sm:items-center">
		<select
			class="rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 py-2 text-sm text-gray-800 dark:text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
			bind:value={classFilter}
		>
			<option value="all" class="bg-white dark:bg-gray-800 text-gray-800 dark:text-white"
				>{$i18n.t('All classes')}</option
			>
			{#each classes as c (c.id)}
				<option value={c.id} class="bg-white dark:bg-gray-800 text-gray-800 dark:text-white"
					>{c.name}</option
				>
			{/each}
		</select>
		<div class="relative max-w-xs flex-1">
			<svg
				class="h-5 w-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				><path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"
				/></svg
			>
			<input
				class="w-full rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 pl-10 pr-4 py-2 text-sm text-gray-800 dark:text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
				placeholder={$i18n.t('Search students…')}
				bind:value={query}
			/>
		</div>
	</div>

	{#if loading}
		<div class="flex justify-center py-12">
			<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
		</div>
	{:else if students.length === 0}
		<div
			class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
		>
			{$i18n.t('No students yet — add or invite one from a class.')}
		</div>
	{:else}
		<div class="overflow-x-auto rounded-2xl bg-white dark:bg-gray-800 shadow-sm">
			<table class="w-full text-left text-sm">
				<thead
					class="text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700"
				>
					<tr>
						<th class="px-5 py-3 font-medium">{$i18n.t('Name')}</th>
						<th class="px-5 py-3 font-medium">{$i18n.t('Class(es)')}</th>
						<th class="px-5 py-3 font-medium">{$i18n.t('Activity')}</th>
						<th class="px-5 py-3 font-medium">{$i18n.t('Supports')}</th>
						<th class="px-5 py-3 font-medium">{$i18n.t('Guardians')}</th>
					</tr>
				</thead>
				<tbody>
					{#each filtered as s (s.student_id)}
						<tr
							class="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 cursor-pointer"
							on:click={() => openStudent(s)}
						>
							<td class="px-5 py-3 font-medium text-gray-800 dark:text-white"
								>{s.name ?? s.email ?? '—'}</td
							>
							<td class="px-5 py-3 text-gray-600 dark:text-gray-300">
								<div class="flex flex-wrap gap-1">
									{#each s.classes as c (c.id)}
										<span
											class="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300"
											>{c.name}</span
										>
									{/each}
								</div>
							</td>
							<td class="px-5 py-3">
								<span class={`text-xs px-2 py-0.5 rounded-full ${statusStyle[s.status]}`}
									>{$i18n.t(statusLabel[s.status])}</span
								>
								<span class="text-xs text-gray-400 ml-2">{fmtDate(s.last_active)}</span>
							</td>
							<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{s.supports_total}</td>
							<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{s.guardians}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
