<!-- SubmissionReview.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import {
		getAssignmentById,
		getSubmissionById,
		requestAiGrade,
		finalizeGrade,
		type AssignmentResponse,
		type SubmissionResponse
	} from '$lib/apis/assignments';

	const i18n = getContext('i18n');

	$: assignmentId = $page.params.assignmentId;
	$: submissionId = $page.params.submissionId;

	let assignment: AssignmentResponse | null = null;
	let submission: SubmissionResponse | null = null;
	let loading = true;
	let error: string | null = null;
	let requestingAiGrade = false;
	let confirming = false;

	let scoreInput = '';
	let feedbackInput = '';

	function fillDraftFromSubmission(s: SubmissionResponse) {
		scoreInput = String(s.teacher_score ?? s.ai_score ?? '');
		feedbackInput = s.teacher_feedback ?? s.ai_feedback ?? '';
	}

	async function load() {
		const token = localStorage.getItem('token');
		if (!token) {
			error = $i18n.t('Authentication required');
			loading = false;
			return;
		}

		loading = true;
		try {
			[assignment, submission] = await Promise.all([
				getAssignmentById(token, assignmentId),
				getSubmissionById(token, assignmentId, submissionId)
			]);
			fillDraftFromSubmission(submission);
			error = null;
		} catch (err) {
			error = typeof err === 'string' ? err : $i18n.t('Failed to load submission');
		} finally {
			loading = false;
		}
	}

	async function handleAiSuggest() {
		const token = localStorage.getItem('token');
		if (!token || !submission) return;

		requestingAiGrade = true;
		try {
			submission = await requestAiGrade(token, assignmentId, submissionId);
			if (submission.status === 'ai_grade_failed') {
				toast.error($i18n.t("AI grading isn't available right now — grade it manually"));
			} else {
				fillDraftFromSubmission(submission);
				toast.success($i18n.t('AI draft ready — review before confirming'));
			}
		} catch (err) {
			toast.error(typeof err === 'string' ? err : $i18n.t('AI grading failed'));
		} finally {
			requestingAiGrade = false;
		}
	}

	async function handleConfirm() {
		const token = localStorage.getItem('token');
		if (!token) return;

		const score = Number(scoreInput);
		if (!scoreInput.trim() || Number.isNaN(score)) {
			toast.error($i18n.t('Enter a valid score'));
			return;
		}
		if (!feedbackInput.trim()) {
			toast.error($i18n.t('Feedback is required'));
			return;
		}

		confirming = true;
		try {
			submission = await finalizeGrade(token, assignmentId, submissionId, {
				score,
				feedback: feedbackInput.trim()
			});
			toast.success($i18n.t('Grade confirmed'));
		} catch (err) {
			toast.error(typeof err === 'string' ? err : $i18n.t('Failed to confirm grade'));
		} finally {
			confirming = false;
		}
	}

	onMount(load);
</script>

<div class="mb-6">
	<button
		on:click={() => goto(`/teacher/assignments/${assignmentId}/submissions`)}
		class="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-2"
	>
		{$i18n.t('← Back to Submissions')}
	</button>

	{#if loading}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mt-4">
			<div class="animate-pulse space-y-4">
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
			</div>
		</div>
	{:else if error || !submission}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center mt-4">
			<p class="text-gray-600 dark:text-gray-400">{error}</p>
		</div>
	{:else}
		<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1 mt-2">
			{submission.filename} — {assignment?.title}
		</h2>
		{#if assignment?.rubric}
			<div
				class="inline-block bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 text-sm px-3 py-2 rounded-lg mb-6"
			>
				{$i18n.t('Rubric')}: {assignment.rubric}
			</div>
		{/if}

		<div class="grid md:grid-cols-2 gap-6">
			<!-- Submission preview -->
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
				<h3 class="font-bold text-gray-900 dark:text-gray-100 mb-3">{$i18n.t('Submission')}</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400 mb-4">📄 {submission.filename}</p>

				<p class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">
					{$i18n.t('Extracted text preview')}
				</p>
				{#if submission.extracted_text}
					<div
						class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap max-h-64 overflow-y-auto"
					>
						{submission.extracted_text}
					</div>
				{:else}
					<div
						class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 text-sm text-gray-500 dark:text-gray-400"
					>
						{$i18n.t("Couldn't read this file automatically — grade it manually.")}
					</div>
				{/if}
			</div>

			<!-- AI suggestion + final grade -->
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
				{#if submission.ai_score !== undefined && submission.ai_score !== null}
					<div class="flex items-center gap-2 mb-2">
						<span
							class="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
							>{$i18n.t('AI DRAFT')}</span
						>
						<span class="font-semibold text-gray-900 dark:text-gray-100"
							>{$i18n.t('Suggested grade')}</span
						>
					</div>
					<p class="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
						{submission.ai_score} / 100
					</p>
					{#if submission.ai_feedback}
						<p class="text-sm text-gray-700 dark:text-gray-300 mb-2">{submission.ai_feedback}</p>
					{/if}
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						{$i18n.t('Draft only — review before confirming.')}
					</p>
				{:else}
					<button
						on:click={handleAiSuggest}
						disabled={requestingAiGrade || !submission.extracted_text}
						class="w-full mb-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
					>
						{requestingAiGrade ? $i18n.t('Asking AI…') : $i18n.t('AI Suggest')}
					</button>
					{#if !submission.extracted_text}
						<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
							{$i18n.t('No readable text — grade manually below.')}
						</p>
					{/if}
				{/if}

				<hr class="border-gray-200 dark:border-gray-700 mb-4" />

				<h4 class="font-bold text-gray-900 dark:text-gray-100 mb-3">
					{$i18n.t('Your Final Grade')}
				</h4>
				<label for="score" class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1"
					>{$i18n.t('Score')}</label
				>
				<input
					id="score"
					type="number"
					min="0"
					max="100"
					bind:value={scoreInput}
					class="w-full mb-4 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
				/>
				<label
					for="feedback"
					class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1"
					>{$i18n.t('Feedback')}</label
				>
				<textarea
					id="feedback"
					bind:value={feedbackInput}
					rows="4"
					class="w-full mb-4 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
				></textarea>

				<button
					on:click={handleConfirm}
					disabled={confirming}
					class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
				>
					{submission.status === 'finalized' ? $i18n.t('Update Grade') : $i18n.t('Confirm Grade')}
				</button>
			</div>
		</div>
	{/if}
</div>
