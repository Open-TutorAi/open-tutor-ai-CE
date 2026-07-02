<!-- Assignments.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isDemo, demoData } from '$lib/stores';
	import {
		getAssignments,
		getMySubmission,
		type AssignmentResponse,
		type MySubmissionResponse
	} from '$lib/apis/assignments';

	const i18n = getContext('i18n');

	$: demoAssignments = $isDemo ? $demoData.assignments : [];

	function getStatusColor(status: string) {
		switch (status) {
			case 'completed':
				return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-200';
			case 'in-progress':
				return 'text-blue-600 bg-blue-100 dark:bg-blue-900 dark:text-blue-200';
			case 'pending':
				return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-200';
			case 'overdue':
				return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-200';
			default:
				return 'text-gray-600 bg-gray-100';
		}
	}

	function getStatusLabel(status: string) {
		return $i18n.t(status.charAt(0).toUpperCase() + status.slice(1).replace('-', ' '));
	}

	// Real (non-demo) assignments, each paired with the student's own submission (if any)
	type Row = { assignment: AssignmentResponse; submission: MySubmissionResponse | null };
	let rows: Row[] = [];
	let loading = true;
	let error: string | null = null;

	function rowStatus(row: Row): 'not_submitted' | 'submitted' | 'graded' {
		if (!row.submission) return 'not_submitted';
		if (row.submission.status === 'finalized') return 'graded';
		return 'submitted';
	}

	async function load() {
		if ($isDemo) {
			loading = false;
			return;
		}

		const token = localStorage.getItem('token');
		if (!token) {
			error = $i18n.t('Authentication required');
			loading = false;
			return;
		}

		loading = true;
		try {
			const assignments = await getAssignments(token);
			rows = await Promise.all(
				assignments.map(async (assignment) => ({
					assignment,
					submission: await getMySubmission(token, assignment.id)
				}))
			);
			error = null;
		} catch (err) {
			error = typeof err === 'string' ? err : $i18n.t('Failed to load assignments');
		} finally {
			loading = false;
		}
	}

	onMount(load);
</script>

<div class="mb-6">
	<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1">
		{$i18n.t('My Assignments')}
	</h2>
	<p class="text-gray-600 dark:text-gray-400 mb-6">
		{$i18n.t("Track what's due and see your grades once your teacher finalizes them.")}
	</p>

	{#if $isDemo}
		{#if demoAssignments.length > 0}
			<div class="grid gap-4">
				{#each demoAssignments as assignment (assignment.id)}
					<div
						class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow"
					>
						<div class="flex justify-between items-start mb-3">
							<div class="flex-1">
								<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
									{assignment.title}
								</h3>
								<p class="text-sm text-gray-600 dark:text-gray-400 mb-2">
									{assignment.description}
								</p>
								<div class="flex items-center gap-3 text-sm">
									<span class="text-gray-500 dark:text-gray-400">
										<strong>{$i18n.t('Course')}:</strong>
										{assignment.course}
									</span>
									<span class="text-gray-500 dark:text-gray-400">
										<strong>{$i18n.t('Due')}:</strong>
										{assignment.due}
									</span>
									<span class="text-gray-500 dark:text-gray-400">
										<strong>{$i18n.t('Points')}:</strong>
										{assignment.points}
									</span>
								</div>
							</div>
							<span
								class="px-3 py-1 rounded-full text-xs font-medium {getStatusColor(
									assignment.status
								)}"
							>
								{getStatusLabel(assignment.status)}
							</span>
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center">
				<p class="text-gray-600 dark:text-gray-400">{$i18n.t('No assignments available')}</p>
			</div>
		{/if}
	{:else if loading}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
			<div class="animate-pulse space-y-4">
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
			</div>
		</div>
	{:else if error}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center">
			<p class="text-gray-600 dark:text-gray-400">{error}</p>
		</div>
	{:else if rows.length === 0}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center">
			<p class="text-gray-600 dark:text-gray-400">{$i18n.t('No assignments yet')}</p>
		</div>
	{:else}
		<div class="grid gap-4">
			{#each rows as row (row.assignment.id)}
				{@const status = rowStatus(row)}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
					<div class="flex justify-between items-start gap-4">
						<div class="flex-1">
							<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
								{row.assignment.title}
							</h3>
							<p class="text-sm text-gray-500 dark:text-gray-400">
								{#if row.assignment.due_date}
									{$i18n.t('Due')}: {new Date(row.assignment.due_date).toLocaleDateString()}
								{/if}
								{#if status === 'graded'}
									· {$i18n.t('Score')}: {row.submission?.teacher_score} / 100
								{/if}
							</p>
						</div>
						<span
							class="px-3 py-1 rounded-full text-xs font-medium {status === 'graded'
								? 'text-green-700 bg-green-100 dark:bg-green-900 dark:text-green-200'
								: status === 'submitted'
									? 'text-amber-700 bg-amber-100 dark:bg-amber-900 dark:text-amber-200'
									: 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-300'}"
						>
							{status === 'graded'
								? $i18n.t('Graded')
								: status === 'submitted'
									? $i18n.t('Submitted')
									: $i18n.t('Not submitted')}
						</span>
					</div>
					<button
						on:click={() => goto(`/student/assignments/${row.assignment.id}`)}
						class="mt-3 text-sm font-medium {status === 'not_submitted'
							? 'text-white bg-blue-600 hover:bg-blue-700 px-3 py-1.5 rounded-lg inline-block'
							: 'text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300'}"
					>
						{status === 'graded'
							? $i18n.t('View Feedback')
							: status === 'submitted'
								? $i18n.t('View Submission')
								: $i18n.t('Start')}
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>
