<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { getStudentsDirectory, type DirectoryStudent } from '$lib/apis/classrooms';

	const i18n: any = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';

	let student: DirectoryStudent | null = null;
	let loading = true;

	onMount(async () => {
		try {
			const directory = await getStudentsDirectory(token());
			student = directory.find((s) => s.student_id === $page.params.sid) ?? null;
		} catch (err) {
			student = null;
		} finally {
			loading = false;
		}
	});

	const fmtDate = (iso: string | null): string => (iso ? new Date(iso).toLocaleString() : '—');
</script>

<div class="flex flex-col gap-6">
	<button
		class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 self-start"
		on:click={() => goto('/teacher/students')}
	>
		‹ {$i18n.t('Students')}
	</button>

	{#if loading}
		<div class="text-gray-500 dark:text-gray-400">{$i18n.t('Loading...')}</div>
	{:else if !student}
		<div
			class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
		>
			{$i18n.t('Student not found.')}
		</div>
	{:else}
		<div class="flex items-start justify-between gap-4">
			<div>
				<h1 class="text-2xl font-bold text-gray-800 dark:text-white">
					{student.name ?? student.email ?? $i18n.t('Student')}
				</h1>
				{#if student.email}
					<p class="text-gray-500 dark:text-gray-400 mt-1">{student.email}</p>
				{/if}
			</div>
		</div>

		<div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
				<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Activity')}</div>
				<div class="text-gray-800 dark:text-white font-semibold capitalize mt-1">
					{$i18n.t(student.status.replace('_', ' '))}
				</div>
			</div>
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
				<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Supports')}</div>
				<div class="text-2xl font-bold text-gray-800 dark:text-white mt-1">
					{student.supports_total}
				</div>
			</div>
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
				<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Guardians')}</div>
				<div class="text-2xl font-bold text-gray-800 dark:text-white mt-1">
					{student.guardians}
				</div>
			</div>
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
				<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Last active')}</div>
				<div class="text-gray-800 dark:text-white font-semibold mt-1">
					{fmtDate(student.last_active)}
				</div>
			</div>
		</div>

		<!-- Detailed progress and guardian contact are class-scoped — link into each class. -->
		<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
			<h3 class="text-sm font-semibold text-gray-800 dark:text-white mb-3">
				{$i18n.t('Classes')}
			</h3>
			<ul class="flex flex-col gap-2">
				{#each student.classes as c (c.id)}
					<li>
						<button
							class="text-blue-600 dark:text-blue-400 text-sm hover:underline"
							on:click={() => goto(`/teacher/classes/${c.id}/students/${student?.student_id}`)}
						>
							{c.name} — {$i18n.t('view detailed progress')} ›
						</button>
					</li>
				{/each}
			</ul>
		</div>
	{/if}
</div>
