<script lang="ts">
	import { onMount, getContext, createEventDispatcher } from 'svelte';
	import { user } from '$lib/stores';
	import { getAllChildrenTeachers } from '$lib/apis/messages';
	import type { ChildTeacher } from '$lib/apis/messages';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher<{
		message: { teacherId: string; studentId: string; teacherName: string; studentName: string };
	}>();

	let entries: ChildTeacher[] = [];
	let loading = true;
	let error: string | null = null;

	onMount(async () => {
		if (!$user) return;
		try {
			entries = await getAllChildrenTeachers(localStorage.token);
		} catch (err: any) {
			error = err || 'Impossible de charger les enseignants';
		} finally {
			loading = false;
		}
	});
</script>

<div class="bg-white dark:bg-gray-850 rounded-xl border border-gray-100 dark:border-gray-800 overflow-hidden">
	<div class="px-5 py-4 border-b border-gray-100 dark:border-gray-800">
		<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-200">Enseignants de mes enfants</h2>
		<p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">Cliquez sur un enseignant pour lui envoyer un message</p>
	</div>

	{#if loading}
		<div class="flex justify-center py-12">
			<div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
		</div>
	{:else if error}
		<p class="text-center text-red-500 text-sm py-8 px-6">{error}</p>
	{:else if entries.length === 0}
		<div class="flex flex-col items-center justify-center py-16 px-6 text-center">
			<svg class="w-10 h-10 text-indigo-400 dark:text-indigo-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
				<path stroke-linecap="round" stroke-linejoin="round" d="M12 14l9-5-9-5-9 5 9 5z" />
				<path stroke-linecap="round" stroke-linejoin="round" d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
			</svg>
			<p class="text-sm font-medium text-gray-800 dark:text-white mb-2">Aucun enseignant lié</p>
			<p class="text-sm text-gray-600 dark:text-gray-400">Demandez à un administrateur de lier vos enfants à leurs enseignants.</p>
		</div>
	{:else}
		<ul class="divide-y divide-gray-50 dark:divide-gray-800">
			{#each entries as entry (entry.teacher.id + entry.student.id)}
				<li class="flex items-center justify-between px-5 py-4 hover:bg-gray-50 dark:hover:bg-gray-900 transition group">
					<div class="flex items-center gap-3 min-w-0">
						<div class="w-11 h-11 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-semibold text-base flex-shrink-0">
							{entry.teacher.name[0]?.toUpperCase() ?? '?'}
						</div>
						<div class="min-w-0">
							<p class="text-sm font-semibold text-gray-800 dark:text-white truncate">{entry.teacher.name}</p>
							<p class="text-xs text-gray-500 dark:text-gray-400 truncate">
								Enfant : <span class="font-medium text-gray-600 dark:text-gray-300">{entry.student.name}</span>
							</p>
						</div>
					</div>
					<button
						class="ml-4 flex-shrink-0 inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-gradient-to-r from-blue-500 to-blue-600 hover:opacity-90 text-white rounded-lg transition"
						on:click={() =>
							dispatch('message', {
								teacherId: entry.teacher.id,
								studentId: entry.student.id,
								teacherName: entry.teacher.name,
								studentName: entry.student.name
							})}
					>
						<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
						</svg>
						Message
					</button>
				</li>
			{/each}
		</ul>
	{/if}
</div>
