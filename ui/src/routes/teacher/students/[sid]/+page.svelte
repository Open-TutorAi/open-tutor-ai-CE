<script lang="ts">
	import { getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { sampleStudents } from '$lib/components/teacher/sampleData';

	const i18n: any = getContext('i18n');
	$: student = sampleStudents.find((s) => s.id === $page.params.sid);
</script>

<div class="flex flex-col gap-6">
	<button
		class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 self-start"
		on:click={() => goto('/teacher/students')}
	>
		‹ {$i18n.t('Students')}
	</button>

	<div class="flex items-start justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold text-gray-800 dark:text-white">
				{student?.name ?? $i18n.t('Student')}
			</h1>
			{#if student}
				<p class="text-gray-500 dark:text-gray-400 mt-1">{student.classes.join(', ')}</p>
			{/if}
		</div>
		<button
			class="px-3 py-2 rounded-full border border-blue-400 text-blue-500 text-sm hover:bg-blue-50 dark:hover:bg-blue-900/20"
		>
			✉ {$i18n.t('Contact parent')}
		</button>
	</div>

	<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
		<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
			<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Activity')}</div>
			<div class="text-gray-800 dark:text-white font-semibold capitalize mt-1">
				{$i18n.t(student?.status ?? 'not started')}
			</div>
		</div>
		<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
			<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Supports')}</div>
			<div class="text-2xl font-bold text-gray-800 dark:text-white mt-1">
				{student?.supports ?? 0}
			</div>
		</div>
		<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
			<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('Guardians')}</div>
			<div class="text-gray-800 dark:text-white font-semibold capitalize mt-1">
				{$i18n.t(student?.guardians ?? 'none')}
			</div>
		</div>
	</div>

	<div
		class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
	>
		{$i18n.t('Detailed progress')} — {$i18n.t('coming soon')}.
	</div>
</div>
