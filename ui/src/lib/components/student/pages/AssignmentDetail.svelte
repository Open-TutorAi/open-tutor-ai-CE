<!-- AssignmentDetail.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import {
		getAssignmentById,
		getMySubmission,
		submitAssignmentWork,
		type AssignmentResponse,
		type MySubmissionResponse
	} from '$lib/apis/assignments';

	const i18n = getContext('i18n');

	$: assignmentId = $page.params.id;

	let assignment: AssignmentResponse | null = null;
	let submission: MySubmissionResponse | null = null;
	let loading = true;
	let error: string | null = null;
	let selectedFile: File | null = null;
	let submitting = false;

	async function load() {
		const token = localStorage.getItem('token');
		if (!token) {
			error = $i18n.t('Authentication required');
			loading = false;
			return;
		}

		loading = true;
		try {
			assignment = await getAssignmentById(token, assignmentId);
			submission = await getMySubmission(token, assignmentId);
			error = null;
		} catch (err) {
			error = typeof err === 'string' ? err : $i18n.t('Failed to load assignment');
		} finally {
			loading = false;
		}
	}

	function handleFileChange(event: Event) {
		selectedFile = (event.target as HTMLInputElement).files?.[0] ?? null;
	}

	async function handleSubmit() {
		const token = localStorage.getItem('token');
		if (!token || !selectedFile) {
			toast.error($i18n.t('Choose a file first'));
			return;
		}

		submitting = true;
		try {
			const result = await submitAssignmentWork(token, assignmentId, selectedFile);
			submission = {
				id: result.id,
				assignment_id: result.assignment_id,
				filename: result.filename,
				file_size: result.file_size,
				status: result.status,
				created_at: result.created_at,
				updated_at: result.updated_at
			};
			toast.success($i18n.t('Submitted'));
		} catch (err) {
			toast.error(typeof err === 'string' ? err : $i18n.t('Failed to submit'));
		} finally {
			submitting = false;
		}
	}

	onMount(load);
</script>

<div class="mb-6 max-w-2xl">
	<button
		on:click={() => goto('/student/assignments')}
		class="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-2"
	>
		{$i18n.t('← Back to My Assignments')}
	</button>

	{#if loading}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mt-4">
			<div class="animate-pulse space-y-4">
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
			</div>
		</div>
	{:else if error || !assignment}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center mt-4">
			<p class="text-gray-600 dark:text-gray-400">{error}</p>
		</div>
	{:else}
		<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1 mt-2">
			{assignment.title}
		</h2>
		<p class="text-gray-600 dark:text-gray-400 mb-6">
			{#if assignment.due_date}
				{$i18n.t('Due')}: {new Date(assignment.due_date).toLocaleDateString()}
			{/if}
			{#if submission?.status === 'finalized'}
				· {$i18n.t('Graded')}
			{/if}
		</p>

		{#if assignment.description}
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-4">
				<p class="text-gray-700 dark:text-gray-300">{assignment.description}</p>
			</div>
		{/if}

		{#if !submission}
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
				<h3 class="font-bold text-gray-900 dark:text-gray-100 mb-3">
					{$i18n.t('Submit your work')}
				</h3>
				<input
					type="file"
					accept="application/pdf"
					on:change={handleFileChange}
					class="block w-full text-sm text-gray-700 dark:text-gray-300 mb-4"
				/>
				<button
					on:click={handleSubmit}
					disabled={submitting || !selectedFile}
					class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
				>
					{submitting ? $i18n.t('Submitting…') : $i18n.t('Submit')}
				</button>
			</div>
		{:else}
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-4">
				<h3 class="font-bold text-gray-900 dark:text-gray-100 mb-2">
					{$i18n.t('Your Submission')}
				</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400">📄 {submission.filename}</p>
			</div>

			{#if submission.status === 'finalized'}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
					<h3 class="font-bold text-gray-900 dark:text-gray-100 mb-2">
						{$i18n.t('Your Grade')}
					</h3>
					<p class="text-3xl font-bold text-green-600 dark:text-green-400 mb-3">
						{submission.teacher_score} / 100
					</p>
					{#if submission.teacher_feedback}
						<p class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-1">
							{$i18n.t('Feedback from your teacher')}
						</p>
						<p class="text-gray-700 dark:text-gray-300">{submission.teacher_feedback}</p>
					{/if}
				</div>
			{:else}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 text-center">
					<p class="text-gray-600 dark:text-gray-400">
						{$i18n.t('Waiting for your teacher to grade this.')}
					</p>
				</div>
			{/if}
		{/if}
	{/if}
</div>
