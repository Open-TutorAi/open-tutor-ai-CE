
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { user } from '$lib/stores';
	import { ClassroomsAPI } from '$lib/apis/classrooms';
	import type { ClassroomOut } from '$lib/types/classroom';
	import ClassroomCard from '$lib/components/ClassroomCard.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';

	const i18n = getContext('i18n');

	let loading = true;
	let error: string | null = null;
	let classrooms: ClassroomOut[] = [];

	$: totalStudents = classrooms.reduce((sum, c) => sum + c.student_count, 0);
	$: recentClassrooms = classrooms.slice(0, 3);

	const loadClassrooms = async () => {
		const token = localStorage.getItem('token') ?? '';
		loading = true;
		try {
			classrooms = await ClassroomsAPI.list(token);
			error = null;
		} catch (err: any) {
			error = err?.detail || $i18n.t('Failed to load classrooms');
		} finally {
			loading = false;
		}
	};

	onMount(() => {
		if (!browser) return;
		loadClassrooms();
	});

	const handleDeleted = (event: CustomEvent<string>) => {
		classrooms = classrooms.filter((c) => c.id !== event.detail);
	};
</script>

<div class="max-w-6xl mx-auto">
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
		<div>
			<h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-1">
				{$i18n.t('Welcome back')}{$user ? `, ${$user.name.split(' ')[0]}` : ''}
			</h1>
			<p class="text-gray-600 dark:text-gray-400">
				{$i18n.t('Here is an overview of your classrooms')}
			</p>
		</div>

		<button
			type="button"
			on:click={() => goto('/classrooms/new')}
			class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors mt-4 sm:mt-0"
		>
			<Plus className="w-5 h-5 mr-2" />
			{$i18n.t('Create Classroom')}
		</button>
	</div>

	{#if loading}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
			{#each Array(4) as _}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 animate-pulse">
					<div class="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
				</div>
			{/each}
		</div>
	{:else}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
				<div class="text-2xl font-bold text-gray-900 dark:text-white">{classrooms.length}</div>
				<div class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Classrooms')}</div>
			</div>
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
				<div class="text-2xl font-bold text-gray-900 dark:text-white">{totalStudents}</div>
				<div class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Students')}</div>
			</div>
		</div>
	{/if}

	<div class="flex items-center justify-between mb-4">
		<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
			{$i18n.t('My Classrooms')}
		</h2>
		{#if classrooms.length > 0}
			<button
				type="button"
				on:click={() => goto('/classrooms')}
				class="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline"
			>
				{$i18n.t('View all')}
			</button>
		{/if}
	</div>

	{#if error}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 text-center text-red-600">
			{error}
		</div>
	{:else if loading}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each Array(3) as _}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-5 animate-pulse">
					<div class="h-10 w-10 bg-gray-200 dark:bg-gray-700 rounded-lg mb-3"></div>
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
				</div>
			{/each}
		</div>
	{:else if classrooms.length === 0}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center">
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
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each recentClassrooms as classroom (classroom.id)}
				<ClassroomCard {classroom} on:deleted={handleDeleted} />
			{/each}
		</div>
	{/if}
</div>
