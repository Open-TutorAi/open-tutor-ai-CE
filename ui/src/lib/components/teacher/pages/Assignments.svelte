<!-- Assignments.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { getAssignments, deleteAssignment, type AssignmentResponse } from '$lib/apis/assignments';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';

	const i18n = getContext('i18n');

	let assignments: AssignmentResponse[] = [];
	let loading = true;
	let error: string | null = null;

	let showDeleteConfirm = false;
	let assignmentToDelete: AssignmentResponse | null = null;

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

	function confirmDelete(assignment: AssignmentResponse) {
		assignmentToDelete = assignment;
		showDeleteConfirm = true;
	}

	async function deleteHandler() {
		const assignment = assignmentToDelete;
		if (!assignment) return;

		const token = localStorage.getItem('token');
		if (!token) return;

		try {
			await deleteAssignment(token, assignment.id);
			assignments = assignments.filter((a) => a.id !== assignment.id);
			toast.success($i18n.t('Assignment deleted successfully.'));
		} catch (err) {
			toast.error(typeof err === 'string' ? err : $i18n.t('Failed to delete assignment'));
		} finally {
			assignmentToDelete = null;
		}
	}

	onMount(loadAssignments);
</script>

<ConfirmDialog
	bind:show={showDeleteConfirm}
	title={$i18n.t('Delete Assignment')}
	message={$i18n.t(
		'This will permanently delete "{{title}}" and all of its submissions. This action cannot be undone.',
		{ title: assignmentToDelete?.title ?? '' }
	)}
	confirmLabel={$i18n.t('Delete')}
	on:confirm={deleteHandler}
	on:cancel={() => (assignmentToDelete = null)}
/>

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
				<div
					class="flex items-start justify-between gap-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow"
				>
					<button
						on:click={() => goto(`/teacher/assignments/${assignment.id}/submissions`)}
						class="flex-1 text-left"
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
					<button
						on:click={() => confirmDelete(assignment)}
						aria-label={$i18n.t('Delete Assignment')}
						class="shrink-0 p-2 rounded-lg text-gray-500 hover:text-red-600 hover:bg-red-50 dark:text-gray-400 dark:hover:text-red-400 dark:hover:bg-red-950/30 transition-colors"
					>
						<GarbageBin className="size-4" />
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>
