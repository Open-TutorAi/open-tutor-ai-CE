<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import ClassCard from '$lib/components/teacher/elements/ClassCard.svelte';
	import { getClassrooms, type Classroom } from '$lib/apis/classrooms';

	const i18n: any = getContext('i18n');
	let classes: Classroom[] = [];
	let loading = true;
	let loadError = '';
	let query = '';

	$: filtered = classes.filter((c) =>
		`${c.name} ${c.subject ?? ''}`.toLowerCase().includes(query.toLowerCase())
	);

	onMount(async () => {
		try {
			classes = await getClassrooms(localStorage.getItem('token') ?? '');
		} catch (err: any) {
			loadError = typeof err === 'string' ? err : $i18n.t('Could not load your classes');
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex flex-col gap-6">
	<!-- Header -->
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold text-gray-800 dark:text-white">{$i18n.t('Classes')}</h1>
			<p class="text-gray-500 dark:text-gray-400 mt-1">
				{$i18n.t('Create and manage your classes.')}
			</p>
		</div>
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

	{#if loading}
		<div class="flex justify-center py-12">
			<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
		</div>
	{:else if loadError}
		<div class="rounded-2xl bg-red-50 dark:bg-red-900/20 p-4 text-red-600">{loadError}</div>
	{:else if classes.length === 0}
		<div
			class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-12 text-center"
		>
			<div
				class="mx-auto h-14 w-14 rounded-2xl grid place-items-center mb-4 bg-blue-50 text-blue-500 dark:bg-blue-900/30 dark:text-blue-300"
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
				{$i18n.t('Create your first class to start organising your students and their work.')}
			</p>
			<button
				class="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full transition shadow-sm"
				on:click={() => goto('/teacher/classes/create')}
			>
				+ {$i18n.t('Create a class')}
			</button>
		</div>
	{:else}
		<div class="relative max-w-xs">
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
				placeholder={$i18n.t('Search classes…')}
				bind:value={query}
			/>
		</div>
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each filtered as klass (klass.id)}
				<ClassCard {klass} />
			{/each}
		</div>
	{/if}
</div>
