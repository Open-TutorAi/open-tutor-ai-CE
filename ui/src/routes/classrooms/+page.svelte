<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { writable, derived } from 'svelte/store';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { ClassroomsAPI } from '$lib/apis/classrooms';
	import type { ClassroomOut } from '$lib/types/classroom';
	import ClassroomCard from '$lib/components/ClassroomCard.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';

	
	const i18n = getContext('i18n');

	const classrooms = writable<ClassroomOut[]>([]);
	const searchTerm = writable('');
	const filteredClassrooms = derived([classrooms, searchTerm], ([$classrooms, $searchTerm]) =>
		$classrooms.filter((c) => c.name.toLowerCase().includes($searchTerm.toLowerCase()))
	);

	let loading = true;
	let error: string | null = null;

	const loadClassrooms = async () => {
		const token = localStorage.getItem('token') ?? '';
		loading = true;
		try {
			classrooms.set(await ClassroomsAPI.list(token));
			error = null;
		} catch (err: any) {
			error = err?.message || $i18n.t('Failed to load classrooms');
		} finally {
			loading = false;
		}
	};

	onMount(() => {
		if (!browser) return;
		loadClassrooms();
	});

	const handleDeleted = (event: CustomEvent<string>) => {
		classrooms.update((list) => list.filter((c) => c.id !== event.detail));
	};
</script>

<div class="max-w-6xl mx-auto">
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
		<div>
			<h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
				{$i18n.t('My Classrooms')}
			</h1>
			<p class="text-gray-600 dark:text-gray-400 mb-4 sm:mb-0">
				{$i18n.t('Manage your classrooms')}
			</p>
		</div>

		<button
			type="button"
			on:click={() => goto('/classrooms/new')}
			class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
		>
			<Plus className="w-5 h-5 mr-2" />
			{$i18n.t('Create Classroom')}
		</button>
	</div>

	<div class="mb-6">
		<input
			type="text"
			bind:value={$searchTerm}
			placeholder={$i18n.t('Search classrooms by name...')}
			data-testid="classroom-search"
			class="w-full max-w-md rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
		/>
	</div>

	{#if loading}
		<div
			data-testid="classrooms-skeleton"
			class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
		>
			{#each Array(3) as _}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
					<div class="animate-pulse space-y-4">
						<div class="h-10 w-10 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
						<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
						<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
					</div>
				</div>
			{/each}
		</div>
	{:else if error}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 text-center text-red-600">
			{error}
		</div>
	{:else if $classrooms.length === 0}
		<div
			data-testid="classrooms-empty"
			class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center"
		>
			<h3 class="text-xl font-medium text-gray-900 dark:text-white mb-2">
				{$i18n.t('No Classrooms Found')}
			</h3>
			<p class="text-gray-600 dark:text-gray-400 mb-6">
				{$i18n.t("You haven't created any classrooms yet")}
			</p>
			<button
				type="button"
				on:click={() => goto('/classrooms/new')}
				class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
			>
				<Plus className="w-5 h-5 mr-2" />
				{$i18n.t('+ Create Classroom')}
			</button>
		</div>
	{:else if $filteredClassrooms.length === 0}
		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center text-gray-600 dark:text-gray-400"
		>
			{$i18n.t('No classrooms match your search')}
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each $filteredClassrooms as classroom (classroom.id)}
				<ClassroomCard {classroom} on:deleted={handleDeleted} />
			{/each}
		</div>
	{/if}
</div>
