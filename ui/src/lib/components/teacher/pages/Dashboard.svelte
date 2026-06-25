<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import ClassCard from '$lib/components/teacher/elements/ClassCard.svelte';
	import { getClassrooms, type Classroom } from '$lib/apis/classrooms';

	const i18n: any = getContext('i18n');

	let classes: Classroom[] = [];
	let loading = true;

	$: studentTotal = classes.reduce((n, c) => n + (c.student_count ?? 0), 0);
	$: stats = [
		{ key: 'Classes', value: classes.length, accent: 'blue' },
		{ key: 'Students', value: studentTotal, accent: 'emerald' },
		{ key: 'Pending invites', value: 0, accent: 'amber' },
		{ key: 'To grade', value: 0, accent: 'violet' }
	];

	const accentMap: Record<string, string> = {
		blue: 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300',
		emerald: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-300',
		amber: 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-300',
		violet: 'bg-violet-50 text-violet-600 dark:bg-violet-900/30 dark:text-violet-300'
	};

	onMount(async () => {
		try {
			classes = await getClassrooms(localStorage.getItem('token') ?? '');
		} catch (err) {
			classes = [];
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex flex-col gap-6">
	<!-- Top action (greeting lives in the top bar, like the student dashboard) -->
	<div class="flex justify-end">
		<button
			class="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full transition shadow-sm"
			on:click={() => goto('/teacher/classes/create')}
		>
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"
				><path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 4v16m8-8H4"
				/></svg
			>
			{$i18n.t('Create a class')}
		</button>
	</div>

	<!-- Stats -->
	<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
		{#each stats as s}
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5 flex items-center gap-4">
				<div class={`h-12 w-12 rounded-xl grid place-items-center ${accentMap[s.accent]}`}>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 17v-6m4 6V7m4 10v-3M5 21h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2z"
						/></svg
					>
				</div>
				<div>
					<div class="text-2xl font-bold text-gray-800 dark:text-white">{s.value}</div>
					<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t(s.key)}</div>
				</div>
			</div>
		{/each}
	</div>

	<!-- My Classes -->
	<div class="flex flex-col gap-3">
		<div class="flex items-center justify-between">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-white">{$i18n.t('My Classes')}</h2>
			<a href="/teacher/classes" class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
				>{$i18n.t('View all')}</a
			>
		</div>

		{#if loading}
			<div class="flex justify-center py-10">
				<div class="animate-spin rounded-full h-9 w-9 border-t-2 border-b-2 border-blue-500"></div>
			</div>
		{:else if classes.length === 0}
			<div
				class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-12 text-center"
			>
				<div
					class="mx-auto h-14 w-14 rounded-2xl grid place-items-center bg-blue-50 text-blue-500 dark:bg-blue-900/30 dark:text-blue-300 mb-4"
				>
					<svg class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="1.8"
							d="M12 14l9-5-9-5-9 5 9 5z"
						/><path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="1.8"
							d="M12 14l6.16-3.42A12 12 0 0112 21a12 12 0 01-6.16-10.42L12 14z"
						/></svg
					>
				</div>
				<h3 class="text-lg font-semibold text-gray-800 dark:text-white">
					{$i18n.t('No classes yet')}
				</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-5 max-w-sm mx-auto">
					{$i18n.t(
						'Create your first class to start organising your students and tracking their progress.'
					)}
				</p>
				<button
					class="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full transition shadow-sm"
					on:click={() => goto('/teacher/classes/create')}
				>
					+ {$i18n.t('Create a class')}
				</button>
			</div>
		{:else}
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each classes.slice(0, 6) as klass (klass.id)}
					<ClassCard {klass} />
				{/each}
			</div>
		{/if}
	</div>
</div>
