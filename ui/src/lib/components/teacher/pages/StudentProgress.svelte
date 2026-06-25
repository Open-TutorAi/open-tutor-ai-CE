<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { getStudentProgress, type StudentProgress } from '$lib/apis/classrooms';
	import GuardiansModal from '$lib/components/teacher/elements/GuardiansModal.svelte';

	const i18n: any = getContext('i18n');
	export let classId: string;
	export let studentId: string;

	let data: StudentProgress | null = null;
	let loading = true;
	let loadError = '';
	let showGuardians = false;

	function fmt(ts: string | null | undefined): string {
		return ts ? new Date(ts).toLocaleString() : '—';
	}

	onMount(async () => {
		try {
			data = await getStudentProgress(localStorage.getItem('token') ?? '', classId, studentId);
		} catch (err: any) {
			loadError = typeof err === 'string' ? err : $i18n.t('Could not load this student');
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex flex-col gap-6">
	<button
		class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 self-start"
		on:click={() => goto(`/teacher/classes/${classId}`)}
	>
		‹ {$i18n.t('Class')}
	</button>

	{#if loading}
		<div class="flex justify-center py-12">
			<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
		</div>
	{:else if loadError || !data}
		<div class="rounded-2xl bg-red-50 dark:bg-red-900/20 p-4 text-red-600">
			{loadError || $i18n.t('Could not load this student')}
		</div>
	{:else}
		<div class="flex items-start justify-between gap-4">
			<div>
				<h1 class="text-2xl font-bold text-gray-800 dark:text-white">{data.name ?? '—'}</h1>
				<p class="text-gray-500 dark:text-gray-400 mt-1">{data.email ?? '—'}</p>
			</div>
			<button
				class="px-3 py-2 rounded-full border border-blue-400 text-blue-500 text-sm hover:bg-blue-50 dark:hover:bg-blue-900/20"
				on:click={() => (showGuardians = true)}
			>
				✉ {$i18n.t('Contact parent')}
			</button>
		</div>

		<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
				<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Activity')}</div>
				<div class="text-gray-800 dark:text-white font-semibold capitalize mt-1">
					{$i18n.t(data.activity.status.replace('_', ' '))}
				</div>
				<div class="text-xs text-gray-400 mt-1">
					{$i18n.t('Last active')}: {fmt(data.activity.last_active)}
				</div>
			</div>
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
				<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Supports')}</div>
				<div class="text-2xl font-bold text-gray-800 dark:text-white mt-1">
					{data.supports.total}
				</div>
			</div>
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
				<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Engagement')}</div>
				<div class="text-gray-800 dark:text-white mt-1">
					👍 {data.engagement.feedback_positive} · 👎 {data.engagement.feedback_negative}
				</div>
			</div>
		</div>

		<h2 class="text-lg font-semibold text-gray-800 dark:text-white">
			{$i18n.t('Supports')}
			<span class="text-sm font-normal text-gray-400">({$i18n.t('read-only')})</span>
		</h2>
		{#if data.supports.items.length === 0}
			<div
				class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-8 text-center text-gray-500 dark:text-gray-400"
			>
				{$i18n.t('No activity yet.')}
			</div>
		{:else}
			<div class="overflow-x-auto rounded-2xl bg-white dark:bg-gray-800 shadow-sm">
				<table class="w-full text-left text-sm">
					<thead
						class="text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700"
					>
						<tr
							><th class="px-5 py-3 font-medium">{$i18n.t('Title')}</th><th
								class="px-5 py-3 font-medium">{$i18n.t('Subject')}</th
							><th class="px-5 py-3 font-medium">{$i18n.t('Level')}</th><th
								class="px-5 py-3 font-medium">{$i18n.t('Status')}</th
							><th class="px-5 py-3 font-medium">{$i18n.t('Updated')}</th></tr
						>
					</thead>
					<tbody>
						{#each data.supports.items as s (s.id)}
							<tr class="border-b border-gray-50 dark:border-gray-700/50">
								<td class="px-5 py-3 text-gray-800 dark:text-white">{s.title ?? '—'}</td>
								<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{s.subject ?? '—'}</td>
								<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{s.level ?? '—'}</td>
								<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{s.status}</td>
								<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{fmt(s.updated_at)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	{/if}
</div>

{#if showGuardians && data}
	<GuardiansModal
		{classId}
		{studentId}
		studentName={data.name ?? ''}
		on:close={() => (showGuardians = false)}
	/>
{/if}
