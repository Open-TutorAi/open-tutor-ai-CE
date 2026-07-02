<!-- Assignments.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getAssignments, type AssignmentResponse } from '$lib/apis/assignments';

	const i18n = getContext('i18n');

	let assignments: AssignmentResponse[] = [];
	let loading = true;
	let error: string | null = null;

	async function loadAssignments() {
		const token = localStorage.getItem('token');
		if (!token) {
			error = $i18n.t('Authentication required');
			loading = false;
			return;
		}

		loading = true;
		try {
			assignments = await getAssignments(token);
			error = null;
		} catch (err) {
			error = typeof err === 'string' ? err : $i18n.t('Failed to load assignments');
			assignments = [];
		} finally {
			loading = false;
		}
	}

	onMount(loadAssignments);
</script>

<div class="mb-6">
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
		<div>
			<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1">
				{$i18n.t('Assignments')}
			</h2>
			<p class="text-gray-600 dark:text-gray-400">
				{$i18n.t('Create assignments and review student submissions')}
			</p>
		</div>
		<button
			on:click={() => goto('/teacher/assignments/create')}
			class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors shadow-sm mt-4 sm:mt-0"
		>
			{$i18n.t('New Assignment')}
		</button>
	</div>

	{#if loading}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
			<div class="animate-pulse space-y-4">
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
			</div>
		</div>
	{:else if error}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center">
			<p class="text-gray-600 dark:text-gray-400">{error}</p>
			<button
				on:click={loadAssignments}
				class="mt-4 inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
			>
				{$i18n.t('Try Again')}
			</button>
		</div>
	{:else if assignments.length === 0}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center">
			<p class="text-gray-600 dark:text-gray-400 mb-4">
				{$i18n.t("You haven't created any assignments yet")}
			</p>
			<button
				on:click={() => goto('/teacher/assignments/create')}
				class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
			>
				{$i18n.t('Create Your First Assignment')}
			</button>
		</div>
	{:else}
		<div class="space-y-4">
			{#each assignments as assignment (assignment.id)}
				<button
					on:click={() => goto(`/teacher/assignments/${assignment.id}/submissions`)}
					class="w-full text-left bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow"
				>
					<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
						{assignment.title}
					</h3>
					{#if assignment.description}
						<p class="text-sm text-gray-600 dark:text-gray-400 mb-2">{assignment.description}</p>
					{/if}
					{#if assignment.due_date}
						<span class="text-sm text-gray-500 dark:text-gray-400">
							{$i18n.t('Due')}: {new Date(assignment.due_date).toLocaleDateString()}
						</span>
					{/if}
				</button>
			{/each}
		</div>
	{/if}
</div>
