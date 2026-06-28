<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getAssignment, getMySubmission, submitAssignment, cancelSubmission, type Assignment, type Submission } from '$lib/apis/assignments';
	import { uploadFile } from '$lib/apis/files';
	import { TUTOR_API_BASE_URL } from '$lib/constants';

	const i18n = getContext('i18n');
	$: assignmentId = $page.params.id;

	let assignment: Assignment | null = null;
	let submission: Submission | null = null;
	let loading = true;

	let content = '';
	let attachmentFile: File | null = null;
	let attachmentName = '';
	let attachmentUrl = '';
	let submitting = false;

	onMount(async () => {
		try {
			[assignment, submission] = await Promise.all([
				getAssignment(localStorage.token, assignmentId),
				getMySubmission(localStorage.token, assignmentId).catch(() => null),
			]);
			if (submission?.content) content = submission.content;
			if (submission?.attachment_url && !submission.attachment_url.startsWith(TUTOR_API_BASE_URL)) {
				attachmentUrl = submission.attachment_url;
			}
		} catch {
			toast.error('Assignment not found');
			goto('/student/assignments');
		} finally { loading = false; }
	});

	function isPastDue(a: Assignment) { return new Date(a.due_date) < new Date(); }

	function daysUntil(d: string): string {
		const diff = Math.ceil((new Date(d).getTime() - Date.now()) / 86400000);
		if (diff < 0) return 'Overdue';
		if (diff === 0) return 'Due today';
		if (diff === 1) return 'Due tomorrow';
		return `Due in ${diff} days`;
	}

	function fmtDate(d: string) {
		return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
	}

	function fmtDateTime(d: string | null) {
		if (!d) return '—';
		const dt = new Date(d);
		return dt.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) + ' · ' + dt.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
	}

	function handleFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		attachmentFile = input.files?.[0] ?? null;
		attachmentName = attachmentFile?.name ?? '';
	}

	function removeFile() {
		attachmentFile = null;
		attachmentName = '';
	}

	async function downloadAttachment(url: string) {
		try {
			const res = await fetch(url, { headers: { Authorization: `Bearer ${localStorage.token}` } });
			if (!res.ok) { toast.error('Download failed'); return; }
			const blob = await res.blob();
			const disposition = res.headers.get('content-disposition') ?? '';
			const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
			const filename = match ? match[1].replace(/['"]/g, '') : 'attachment';
			const a = document.createElement('a');
			a.href = URL.createObjectURL(blob);
			a.download = filename;
			a.click();
			URL.revokeObjectURL(a.href);
		} catch {
			toast.error('Download failed');
		}
	}

	let cancelling = false;
	async function handleCancel() {
		if (!assignment) return;
		if (!confirm('Cancel your submission? You can resubmit before the deadline.')) return;
		cancelling = true;
		try {
			await cancelSubmission(localStorage.token, assignment.id);
			submission = null;
			content = '';
			attachmentFile = null;
			attachmentName = '';
			attachmentUrl = '';
			toast.success('Submission cancelled');
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to cancel submission');
		} finally { cancelling = false; }
	}

	async function handleSubmit() {
		if (!assignment) return;
		if (!content.trim() && !attachmentFile && !attachmentUrl.trim()) {
			toast.error('Please write an answer, attach a file, or paste a link before submitting');
			return;
		}
		submitting = true;
		try {
			let attachment_url: string | undefined;
			if (attachmentFile) {
				const uploaded = await uploadFile(localStorage.token, attachmentFile);
				attachment_url = `${TUTOR_API_BASE_URL}/files/${uploaded.id}/content`;
			} else if (attachmentUrl.trim()) {
				attachment_url = attachmentUrl.trim();
			}
			submission = await submitAssignment(localStorage.token, assignment.id, {
				content: content.trim() || undefined,
				attachment_url,
			});
			attachmentFile = null;
			attachmentName = '';
			toast.success(isPastDue(assignment) ? 'Submitted (late)' : 'Assignment submitted!');
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to submit');
		} finally { submitting = false; }
	}
</script>

{#if loading}
	<div class="flex justify-center py-20">
		<div class="h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
	</div>
{:else if assignment}
<div class="space-y-4 max-w-3xl mx-auto">

	<!-- Back -->
	<button on:click={() => goto('/student/assignments')}
		class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 transition font-medium">
		<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
		Back to Assignments
	</button>

	<!-- Assignment header -->
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
		<div class="flex items-start justify-between mb-4">
			<div>
				<p class="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-1">Assignment</p>
				<h1 class="text-xl font-bold text-gray-800 dark:text-white">{assignment.title}</h1>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">📅 Due {fmtDate(assignment.due_date)}</p>
			</div>
			{#if submission?.status === 'returned'}
				<span class="px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full">Graded</span>
			{:else if submission}
				<span class="px-3 py-1 bg-indigo-100 text-indigo-700 text-xs font-semibold rounded-full">Submitted</span>
			{:else if isPastDue(assignment)}
				<span class="px-3 py-1 bg-red-100 text-red-600 text-xs font-semibold rounded-full">Overdue</span>
			{:else}
				<span class="px-3 py-1 bg-amber-100 text-amber-700 text-xs font-semibold rounded-full">{daysUntil(assignment.due_date)}</span>
			{/if}
		</div>

		{#if assignment.instructions}
			<div class="pt-4 border-t border-gray-100 dark:border-gray-700">
				<p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Instructions</p>
				<p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">{assignment.instructions}</p>
			</div>
		{/if}
		{#if assignment.attachment_url}
			<div class="pt-4 border-t border-gray-100 dark:border-gray-700">
				<p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Teacher Attachment</p>
				{#if assignment.attachment_url.startsWith(TUTOR_API_BASE_URL)}
					<button on:click={() => downloadAttachment(assignment.attachment_url ?? '')}
						class="inline-flex items-center gap-2 px-4 py-2 border border-indigo-200 dark:border-indigo-700 rounded-xl text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition font-medium">
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
						</svg>
						Download Attachment
					</button>
				{:else}
					<a href={assignment.attachment_url} target="_blank" rel="noopener noreferrer"
						class="inline-flex items-center gap-2 px-4 py-2 border border-indigo-200 dark:border-indigo-700 rounded-xl text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition font-medium">
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
						</svg>
						Open Link
					</a>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Grade result (if returned) -->
	{#if submission?.status === 'returned'}
		<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
			<h2 class="font-bold text-gray-800 dark:text-white mb-4">Result</h2>
			<div class="flex items-center gap-4 bg-green-50 dark:bg-green-900/20 rounded-xl p-4 mb-4">
				<div class="h-14 w-14 rounded-full bg-green-100 dark:bg-green-900/40 flex items-center justify-center shrink-0">
					<span class="text-lg font-bold text-green-700 dark:text-green-400">{submission.score}</span>
				</div>
				<div>
					<p class="text-sm text-gray-500 dark:text-gray-400">Your Score</p>
					<p class="text-2xl font-bold text-green-700 dark:text-green-400">{submission.score} <span class="text-base font-normal text-gray-500">/ {assignment.max_score}</span></p>
				</div>
			</div>
			{#if submission.feedback}
				<div>
					<p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Teacher Feedback</p>
					<div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-xl p-4 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
						{submission.feedback}
					</div>
				</div>
			{/if}
			<p class="text-xs text-gray-400 mt-3">Graded on {fmtDateTime(submission.graded_at)}</p>
		</div>
	{/if}

	<!-- Your work -->
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
		<div class="flex items-center justify-between mb-4">
			<h2 class="font-bold text-gray-800 dark:text-white">Your Work</h2>
			{#if submission}
				<p class="text-xs text-gray-400">Submitted {fmtDateTime(submission.submitted_at)}</p>
			{/if}
		</div>

		{#if submission?.status === 'returned'}
			<!-- Read-only view -->
			{#if submission.content}
				<div class="mb-4">
					<p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Your Answer</p>
					<div class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-3 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-900/50 whitespace-pre-wrap min-h-[80px]">
						{submission.content}
					</div>
				</div>
			{/if}
			{#if submission.attachment_url}
				<div class="mt-3">
					<p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Your Attachment</p>
					{#if submission.attachment_url.startsWith(TUTOR_API_BASE_URL)}
						<button on:click={() => downloadAttachment(submission?.attachment_url ?? '')}
							class="inline-flex items-center gap-2 px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition font-medium">
							<svg class="h-4 w-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
							</svg>
							Download my submission
						</button>
					{:else}
						<a href={submission.attachment_url} target="_blank" rel="noopener noreferrer"
							class="inline-flex items-center gap-2 px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition font-medium">
							<svg class="h-4 w-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
							</svg>
							Open my link
						</a>
					{/if}
				</div>
			{/if}
		{:else}
			<!-- Editable -->
			<div class="mb-4">
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
					Answer / Response <span class="text-xs font-normal text-gray-400">(optional if you attach a file)</span>
				</label>
				<textarea bind:value={content} rows="5" placeholder="Write your answer here..."
					class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-3 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"></textarea>
			</div>

			<!-- File attachment + URL link -->
			<div class="mb-5">
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
					Attachment <span class="text-xs font-normal text-gray-400">(file or link — optional)</span>
				</label>

				{#if submission?.attachment_url && !submission.attachment_url.startsWith(TUTOR_API_BASE_URL) && !attachmentFile}
					<div class="flex items-center gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-900/30 mb-2">
						<svg class="h-5 w-5 text-indigo-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
						</svg>
						<a href={submission.attachment_url} target="_blank" rel="noopener noreferrer" class="text-sm text-indigo-600 dark:text-indigo-400 flex-1 truncate hover:underline">{submission.attachment_url}</a>
					</div>
				{:else if submission?.attachment_url && submission.attachment_url.startsWith(TUTOR_API_BASE_URL) && !attachmentFile}
					<div class="flex items-center gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-900/30 mb-2">
						<svg class="h-5 w-5 text-indigo-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
						</svg>
						<span class="text-sm text-gray-600 dark:text-gray-300 flex-1">Previous uploaded file</span>
						<button type="button" on:click={() => downloadAttachment(submission?.attachment_url ?? '')} class="text-xs text-indigo-600 hover:underline">Download</button>
					</div>
				{/if}

				{#if attachmentFile}
					<div class="flex items-center gap-2 px-3 py-2.5 border border-indigo-200 dark:border-indigo-700 rounded-xl bg-indigo-50 dark:bg-indigo-900/20">
						<svg class="h-4 w-4 text-indigo-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
						</svg>
						<span class="text-sm text-indigo-700 dark:text-indigo-300 truncate flex-1">{attachmentName}</span>
						<button type="button" on:click={removeFile} class="text-gray-400 hover:text-red-500 transition shrink-0">
							<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
						</button>
					</div>
				{:else}
					<label class="flex items-center gap-2 px-3 py-2.5 border border-dashed border-gray-300 dark:border-gray-600 rounded-xl cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/10 transition">
						<svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
						</svg>
						<span class="text-sm text-gray-500 dark:text-gray-400">Click to upload a file…</span>
						<input type="file" class="hidden" on:change={handleFileSelect}
							accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.png,.jpg,.jpeg,.gif,.zip"/>
					</label>
				{/if}
				<div class="mt-2 flex items-center gap-2">
					<div class="flex-1 border-t border-gray-200 dark:border-gray-700"></div>
					<span class="text-xs text-gray-400 shrink-0">or paste a link</span>
					<div class="flex-1 border-t border-gray-200 dark:border-gray-700"></div>
				</div>
				<input bind:value={attachmentUrl} type="url" placeholder="https://drive.google.com/…"
					disabled={!!attachmentFile}
					class="mt-2 w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300 transition disabled:opacity-50 disabled:cursor-not-allowed" />
			</div>

			<div class="flex gap-3">
				{#if submission}
					<button on:click={handleCancel} disabled={cancelling}
						class="px-4 py-3 border border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-50 font-semibold rounded-xl transition text-sm flex items-center gap-2">
						{#if cancelling}
							<span class="h-4 w-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin"></span>
						{:else}
							Cancel Submission
						{/if}
					</button>
				{/if}
				<button on:click={handleSubmit} disabled={submitting}
					class="flex-1 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-semibold rounded-xl transition flex items-center justify-center gap-2">
					{#if submitting}
						<span class="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
						Submitting…
					{:else}
						{submission ? 'Update Submission' : 'Submit Assignment'}
					{/if}
				</button>
			</div>
			{#if isPastDue(assignment) && !submission}
				<p class="text-xs text-red-500 text-center mt-2">⚠️ This assignment is past due — your submission will be marked late</p>
			{/if}
		{/if}
	</div>
</div>
{/if}
