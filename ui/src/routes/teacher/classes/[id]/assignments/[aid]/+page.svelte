<script lang="ts">
	import { onMount, onDestroy, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { socket } from '$lib/stores';
	import {
		getAssignment,
		deleteAssignment,
		downloadAssignmentAttachment,
		downloadSubmissionAttachment,
		type AssignmentOverview,
		type SubmissionRow,
		type Submission
	} from '$lib/apis/assignments';
	import { getExam, getProctoring, type ProctorRow } from '$lib/apis/exams';
	import GradeModal from '$lib/components/teacher/elements/GradeModal.svelte';
	import EditAssignmentModal from '$lib/components/teacher/elements/EditAssignmentModal.svelte';
	import {
		submissionStatusStyle as statusStyle,
		submissionStatusLabel as statusLabel
	} from '$lib/utils/status';
	import { fmtDate, downloadBlob as saveBlob } from '$lib/utils/format';

	const i18n: any = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';
	const classId = $page.params.id;
	const assignmentId = $page.params.aid;

	let data: AssignmentOverview | null = null;
	let loading = true;
	let grading: SubmissionRow | null = null;

	// E10 proctoring
	let isExam = false;
	let proctorRows: ProctorRow[] = [];
	const examStatusStyle: Record<string, string> = {
		in_progress: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
		submitted: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
		terminated: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
		not_started: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
	};

	async function loadProctoring() {
		try {
			proctorRows = await getProctoring(token(), classId, assignmentId);
		} catch (err) {
			/* ignore */
		}
	}
	function onExamViolation(d: any) {
		if (!d || d.assignment_id !== assignmentId) return;
		proctorRows = proctorRows.map((r) =>
			r.student_id === d.student_id
				? { ...r, status: d.status, violation_count: d.violation_count }
				: r
		);
	}

	async function getAssignmentFile() {
		if (!data?.attachment_id) return;
		try {
			saveBlob(
				await downloadAssignmentAttachment(token(), assignmentId),
				data.attachment_name ?? 'attachment'
			);
		} catch (err) {
			/* ignore */
		}
	}
	async function getSubmissionFile(r: SubmissionRow) {
		try {
			saveBlob(
				await downloadSubmissionAttachment(token(), classId, assignmentId, r.student_id),
				r.submission?.attachment_name ?? 'submission'
			);
		} catch (err) {
			/* ignore */
		}
	}

	async function load() {
		loading = true;
		try {
			data = await getAssignment(token(), classId, assignmentId);
		} catch (err) {
			data = null;
		} finally {
			loading = false;
		}
	}

	let showDelete = false;
	let deleting = false;
	let showEdit = false;

	async function onEdited() {
		showEdit = false;
		await load();
	}
	async function onDelete() {
		deleting = true;
		try {
			await deleteAssignment(token(), classId, assignmentId);
			goto(`/teacher/classes/${classId}`);
		} catch (err) {
			deleting = false;
			showDelete = false;
		}
	}

	function onGraded(e: CustomEvent<Submission>) {
		if (data) {
			const updated = e.detail;
			data.submissions = data.submissions.map((r) =>
				r.student_id === updated.student_id ? { ...r, status: 'graded', submission: updated } : r
			);
			data.graded_count = data.submissions.filter((r) => r.status === 'graded').length;
		}
		grading = null;
	}

	onMount(async () => {
		await load();
		try {
			const info = await getExam(token(), assignmentId);
			isExam = info.is_exam;
			if (isExam) {
				await loadProctoring();
				$socket?.on('exam:violation', onExamViolation);
			}
		} catch (err) {
			/* not an exam */
		}
	});
	onDestroy(() => {
		$socket?.off('exam:violation', onExamViolation);
	});
</script>

<div class="flex flex-col gap-6">
	<button
		class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 self-start"
		on:click={() => goto(`/teacher/classes/${classId}`)}
	>
		‹ {$i18n.t('Class')}
	</button>

	{#if loading}
		<div class="flex justify-center py-12">
			<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
		</div>
	{:else if !data}
		<div class="rounded-2xl bg-red-50 dark:bg-red-900/20 p-4 text-red-600">
			{$i18n.t('Could not load this assignment')}
		</div>
	{:else}
		<div>
			<div class="flex items-start justify-between gap-3">
				<h1 class="text-2xl font-bold text-gray-800 dark:text-white">{data.title}</h1>
				<div class="flex items-center gap-1 shrink-0">
					{#if !isExam}
						<!-- Exams are immutable, so editing is offered only for plain assignments. -->
						<button
							class="text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-full p-2"
							title={$i18n.t('Edit assignment')}
							aria-label={$i18n.t('Edit assignment')}
							on:click={() => (showEdit = true)}
						>
							✎
						</button>
					{/if}
					<button
						class="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full p-2"
						title={$i18n.t('Delete assignment')}
						aria-label={$i18n.t('Delete assignment')}
						on:click={() => (showDelete = true)}
					>
						🗑
					</button>
				</div>
			</div>
			<p class="text-gray-500 dark:text-gray-400 mt-1">
				{$i18n.t('Due')}
				{fmtDate(data.due_date)} · {data.submitted_count}/{data.student_count}
				{$i18n.t('submitted')} · {data.graded_count}
				{$i18n.t('graded')}
			</p>
			{#if data.instructions}
				<div
					class="mt-3 rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5 text-sm text-gray-700 dark:text-gray-200 whitespace-pre-wrap"
				>
					{data.instructions}
				</div>
			{/if}
			{#if data.attachment_id}
				<button
					class="mt-3 inline-flex items-center gap-1.5 text-sm text-blue-600 dark:text-blue-400 hover:underline"
					on:click={getAssignmentFile}
				>
					📎 {data.attachment_name ?? $i18n.t('Attachment')}
				</button>
			{/if}
		</div>

		{#if isExam}
			<!-- E10: live proctoring -->
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
				<div class="flex items-center gap-2 mb-1">
					<span class="h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse"></span>
					<h2 class="text-lg font-semibold text-gray-800 dark:text-white">
						{$i18n.t('Proctoring')}
					</h2>
				</div>
				<p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
					{$i18n.t('Live exam sessions — leaving the page is recorded as a warning.')}
				</p>
				<div class="overflow-x-auto">
					<table class="w-full text-left text-sm">
						<thead
							class="text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700"
						>
							<tr>
								<th class="px-3 py-2 font-medium">{$i18n.t('Name')}</th>
								<th class="px-3 py-2 font-medium">{$i18n.t('Status')}</th>
								<th class="px-3 py-2 font-medium">{$i18n.t('Warnings')}</th>
							</tr>
						</thead>
						<tbody>
							{#each proctorRows as r (r.student_id)}
								<tr class="border-b border-gray-50 dark:border-gray-700/50">
									<td class="px-3 py-2 text-gray-800 dark:text-white">{r.name ?? r.email ?? '—'}</td
									>
									<td class="px-3 py-2">
										<span class={`text-xs px-2 py-0.5 rounded-full ${examStatusStyle[r.status]}`}>
											{$i18n.t(r.status.replace('_', ' '))}
										</span>
									</td>
									<td class="px-3 py-2">
										<span
											class={r.violation_count > 0
												? 'text-amber-600 dark:text-amber-400 font-semibold'
												: 'text-gray-400'}
										>
											{r.violation_count}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}

		<h2 class="text-lg font-semibold text-gray-800 dark:text-white">{$i18n.t('Submissions')}</h2>
		{#if data.submissions.length === 0}
			<div
				class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
			>
				{$i18n.t('No students yet — add or invite one.')}
			</div>
		{:else}
			<div class="overflow-x-auto rounded-2xl bg-white dark:bg-gray-800 shadow-sm">
				<table class="w-full text-left text-sm">
					<thead
						class="text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700"
					>
						<tr>
							<th class="px-5 py-3 font-medium">{$i18n.t('Name')}</th>
							<th class="px-5 py-3 font-medium">{$i18n.t('Status')}</th>
							<th class="px-5 py-3 font-medium">{$i18n.t('Grade')}</th>
							<th class="px-5 py-3"></th>
						</tr>
					</thead>
					<tbody>
						{#each data.submissions as r (r.student_id)}
							<tr class="border-b border-gray-50 dark:border-gray-700/50">
								<td class="px-5 py-3 text-gray-800 dark:text-white">{r.name ?? r.email ?? '—'}</td>
								<td class="px-5 py-3"
									><span class={`text-xs px-2 py-0.5 rounded-full ${statusStyle[r.status]}`}
										>{$i18n.t(statusLabel[r.status] ?? r.status)}</span
									></td
								>
								<td class="px-5 py-3 text-gray-600 dark:text-gray-300"
									>{r.submission?.grade != null ? r.submission.grade : '—'}</td
								>
								<td class="px-5 py-3 text-right">
									{#if r.submission || r.status === 'auto_submitted'}
										{#if r.submission?.attachment_id}
											<button
												class="text-gray-500 dark:text-gray-400 text-xs hover:underline mr-3"
												on:click={() => getSubmissionFile(r)}>📎 {$i18n.t('File')}</button
											>
										{/if}
										{#if !r.submission}
											<!-- Exam ended before any answer was recovered — gradable anyway. -->
											<span class="text-xs text-gray-400 mr-3"
												>{$i18n.t('No answer recovered')}</span
											>
										{/if}
										<button
											class="text-blue-600 dark:text-blue-400 text-xs hover:underline"
											on:click={() => (grading = r)}
											>{r.status === 'graded' ? $i18n.t('Edit grade') : $i18n.t('Grade')}</button
										>
									{:else}
										<span class="text-xs text-gray-400">{$i18n.t('Not submitted')}</span>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	{/if}
</div>

{#if grading}
	<GradeModal
		{classId}
		{assignmentId}
		row={grading}
		on:close={() => (grading = null)}
		on:graded={onGraded}
	/>
{/if}

{#if showEdit && data}
	<EditAssignmentModal
		{classId}
		assignment={data}
		on:updated={onEdited}
		on:close={() => (showEdit = false)}
	/>
{/if}

{#if showDelete}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
		on:click|self={() => (showDelete = false)}
		role="presentation"
	>
		<div class="w-full max-w-sm rounded-2xl bg-white dark:bg-gray-800 shadow-xl p-6 text-center">
			<div class="text-3xl mb-2">🗑</div>
			<h2 class="text-lg font-semibold text-gray-800 dark:text-white mb-1">
				{$i18n.t('Delete this assignment?')}
			</h2>
			<p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
				{$i18n.t(
					'This permanently removes the assignment, its submissions and any exam data. This cannot be undone.'
				)}
			</p>
			<div class="flex justify-center gap-2">
				<button
					class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
					on:click={() => (showDelete = false)}>{$i18n.t('Cancel')}</button
				>
				<button
					class="px-5 py-2 rounded-full bg-red-600 hover:bg-red-700 text-white text-sm font-semibold disabled:opacity-50"
					on:click={onDelete}
					disabled={deleting}>{deleting ? $i18n.t('Deleting…') : $i18n.t('Delete')}</button
				>
			</div>
		</div>
	</div>
{/if}
