<!-- SubmissionsList.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		getAssignmentById,
		getSubmissions,
		type AssignmentResponse,
		type SubmissionResponse
	} from '$lib/apis/assignments';

	const i18n = getContext('i18n');

	$: assignmentId = $page.params.assignmentId;

	let assignment: AssignmentResponse | null = null;
	let submissions: SubmissionResponse[] = [];
	let loading = true;
	let error: string | null = null;

	const statusStyle: Record<string, string> = {
		finalized: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200',
		ai_graded: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200',
		submitted: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-200',
		needs_manual_review: 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-200',
		ai_grade_failed: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200'
	};

	async function load() {
		const token = localStorage.getItem('token');
		if (!token) {
			error = $i18n.t('Authentication required');
			loading = false;
			return;
		}

		loading = true;
		try {
			[assignment, submissions] = await Promise.all([
				getAssignmentById(token, assignmentId),
				getSubmissions(token, assignmentId)
			]);
			error = null;
		} catch (err) {
			error = typeof err === 'string' ? err : $i18n.t('Failed to load submissions');
		} finally {
			loading = false;
		}
	}

	onMount(load);
</script>

<div class="mb-6">
	<button
		on:click={() => goto('/teacher/assignments')}
		class="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-2"
	>
		{$i18n.t('← Back to Assignments')}
	</button>

	{#if loading}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mt-4">
			<div class="animate-pulse space-y-4">
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
			</div>
		</div>
	{:else if error}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center mt-4">
			<p class="text-gray-600 dark:text-gray-400">{error}</p>
		</div>
	{:else}
		<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1 mt-2">
			{assignment?.title}
		</h2>
		{#if assignment?.due_date}
			<p class="text-gray-600 dark:text-gray-400 mb-6">
				{$i18n.t('Due')}: {new Date(assignment.due_date).toLocaleDateString()}
			</p>
		{/if}

		{#if submissions.length === 0}
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center">
				<p class="text-gray-600 dark:text-gray-400">{$i18n.t('No submissions yet')}</p>
			</div>
		{:else}
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
				<table class="w-full text-left">
					<thead>
						<tr
							class="border-b border-gray-200 dark:border-gray-700 text-xs uppercase text-gray-500 dark:text-gray-400"
						>
							<th class="px-6 py-3">{$i18n.t('Student')}</th>
							<th class="px-6 py-3">{$i18n.t('Status')}</th>
							<th class="px-6 py-3">{$i18n.t('Score')}</th>
							<th class="px-6 py-3"></th>
						</tr>
					</thead>
					<tbody>
						{#each submissions as submission (submission.id)}
							<tr class="border-b border-gray-100 dark:border-gray-700 last:border-0">
								<td class="px-6 py-4 text-gray-900 dark:text-gray-100">{submission.filename}</td>
								<td class="px-6 py-4">
									<span
										class="text-xs font-semibold px-2 py-1 rounded-full {statusStyle[
											submission.status
										] ?? statusStyle.submitted}"
									>
										{submission.status.replace('_', ' ')}
									</span>
								</td>
								<td class="px-6 py-4 text-gray-700 dark:text-gray-300">
									{submission.teacher_score ?? submission.ai_score ?? '—'}
								</td>
								<td class="px-6 py-4 text-right">
									<button
										on:click={() =>
											goto(`/teacher/assignments/${assignmentId}/submissions/${submission.id}`)}
										class="px-3 py-1.5 text-sm rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600"
									>
										{submission.status === 'finalized' ? $i18n.t('View') : $i18n.t('Review')}
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	{/if}
</div>
