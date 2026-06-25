<!-- Assignments.svelte — the student's real assignments feed (E7-S5) -->
<script lang="ts">
	import { onMount, tick, getContext } from 'svelte';
	import {
		getMyAssignments,
		submitAssignment,
		downloadAssignmentAttachment,
		downloadMySubmissionAttachment,
		type StudentAssignment
	} from '$lib/apis/assignments';
	import { uploadFile } from '$lib/apis/files';
	import { getExam, startExam, type ExamInfo, type ExamConfig } from '$lib/apis/exams';
	import ExamShell from '$lib/components/student/ExamShell.svelte';

	const i18n: any = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';

	let assignments: StudentAssignment[] = [];
	let loading = true;
	let active: StudentAssignment | null = null;
	let draft = '';
	let file: File | null = null;
	let submitting = false;
	let message = '';

	// E10 exam mode
	let examInfo: ExamInfo | null = null;
	let examActive = false;
	let examConfig: ExamConfig | null = null;
	let examViolations = 0;
	let examStartedAt: string | null = null;
	let startingExam = false;

	async function startExamFlow() {
		if (!active) return;
		startingExam = true;
		try {
			const { config, session } = await startExam(token(), active.id);
			examConfig = config;
			examViolations = session.violation_count;
			examStartedAt = session.started_at;
			examActive = true;
		} catch (e) {
			message = typeof e === 'string' ? e : $i18n.t('Could not start the exam');
		} finally {
			startingExam = false;
		}
	}
	async function onExamDone() {
		examActive = false;
		examConfig = null;
		active = null;
		await load();
	}

	function onPickFile(e: Event) {
		const input = e.target as HTMLInputElement;
		file = input.files && input.files.length ? input.files[0] : null;
	}
	function saveBlob(blob: Blob, filename: string) {
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = filename;
		a.click();
		URL.revokeObjectURL(url);
	}
	async function getTeacherFile() {
		if (!active?.attachment_id) return;
		try {
			saveBlob(
				await downloadAssignmentAttachment(token(), active.id),
				active.attachment_name ?? 'attachment'
			);
		} catch (err) {
			/* ignore */
		}
	}
	async function getMyFile() {
		if (!active?.submission?.attachment_id) return;
		try {
			saveBlob(
				await downloadMySubmissionAttachment(token(), active.id),
				active.submission.attachment_name ?? 'submission'
			);
		} catch (err) {
			/* ignore */
		}
	}

	const statusStyle: Record<string, string> = {
		graded: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
		submitted: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
		late: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
		missing: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
		pending: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
	};
	const statusLabel: Record<string, string> = {
		graded: 'Graded',
		submitted: 'Submitted',
		late: 'Submitted late',
		missing: 'Missing',
		pending: 'To do'
	};

	function fmtDate(ts?: string | null): string {
		return ts ? new Date(ts).toLocaleDateString() : '—';
	}

	// Show the proctored-exam gate when this assignment is an exam the student hasn't taken.
	$: isExamGate =
		!!examInfo?.is_exam && (active?.status === 'pending' || active?.status === 'missing');

	async function load() {
		loading = true;
		try {
			assignments = await getMyAssignments(token());
		} catch (err) {
			assignments = [];
		} finally {
			loading = false;
		}
	}

	async function open(a: StudentAssignment) {
		active = a;
		draft = a.submission?.content ?? '';
		file = null;
		message = '';
		examInfo = null;
		try {
			examInfo = await getExam(token(), a.id);
		} catch (_) {
			/* not an exam or no access */
		}
	}

	async function submit() {
		if (!active || (!draft.trim() && !file)) return;
		submitting = true;
		message = '';
		try {
			let attachmentId: string | undefined;
			if (file) {
				const uploaded = await uploadFile(token(), file);
				attachmentId = uploaded.id;
			}
			const sub = await submitAssignment(token(), active.id, draft.trim(), attachmentId);
			// Reflect the new submission locally, then refresh from the server.
			active = { ...active, submission: sub, status: sub.is_late ? 'late' : 'submitted' };
			await load();
			await tick();
			active = assignments.find((x) => x.id === active!.id) ?? null;
			file = null;
			message = $i18n.t('Submitted!');
		} catch (err: any) {
			message = typeof err === 'string' ? err : $i18n.t('Could not submit your work');
		} finally {
			submitting = false;
		}
	}

	onMount(load);
</script>

<div class="flex flex-col gap-6">
	<div>
		<h1 class="text-2xl font-bold text-gray-800 dark:text-white">{$i18n.t('Assignments')}</h1>
		<p class="text-gray-500 dark:text-gray-400 mt-1">
			{$i18n.t('Work assigned across your classes.')}
		</p>
	</div>

	{#if loading}
		<div class="flex justify-center py-12">
			<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
		</div>
	{:else if assignments.length === 0}
		<div
			class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
		>
			{$i18n.t('No assignments yet — they’ll appear here when a teacher assigns work.')}
		</div>
	{:else}
		<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
			{#each assignments as a (a.id)}
				<button
					class="text-left rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5 hover:shadow-md transition"
					on:click={() => open(a)}
				>
					<div class="flex items-start justify-between gap-2">
						<h3 class="font-semibold text-gray-800 dark:text-white">{a.title}</h3>
						<span class={`text-xs px-2 py-0.5 rounded-full shrink-0 ${statusStyle[a.status]}`}
							>{$i18n.t(statusLabel[a.status] ?? a.status)}</span
						>
					</div>
					<div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
						{a.class_name ?? ''} · {$i18n.t('Due')}
						{fmtDate(a.due_date)}
					</div>
					{#if a.status === 'graded' && a.submission?.grade != null}
						<div class="text-sm font-semibold text-blue-600 dark:text-blue-400 mt-2">
							{$i18n.t('Grade')}: {a.submission.grade}
						</div>
					{/if}
				</button>
			{/each}
		</div>
	{/if}
</div>

{#if active && !examActive}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
		on:click|self={() => (active = null)}
		role="presentation"
	>
		<div
			class="w-full max-w-lg rounded-2xl bg-white dark:bg-gray-800 shadow-xl p-6 max-h-[90vh] overflow-y-auto"
		>
			<div class="flex items-start justify-between mb-1 gap-3">
				<div>
					<h2 class="text-lg font-semibold text-gray-800 dark:text-white">{active.title}</h2>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						{active.class_name ?? ''} · {$i18n.t('Due')}
						{fmtDate(active.due_date)}
					</p>
				</div>
				<button
					class="text-gray-400 hover:text-gray-600"
					on:click={() => (active = null)}
					aria-label="Close">✕</button
				>
			</div>

			{#if active.instructions}
				<div
					class="mt-3 rounded-lg bg-gray-50 dark:bg-gray-700/40 p-3 text-sm text-gray-700 dark:text-gray-200 whitespace-pre-wrap"
				>
					{active.instructions}
				</div>
			{/if}
			{#if active.attachment_id}
				<button
					class="mt-3 inline-flex items-center gap-1.5 text-sm text-blue-600 dark:text-blue-400 hover:underline"
					on:click={getTeacherFile}
				>
					📎 {active.attachment_name ?? $i18n.t('Attachment')}
				</button>
			{/if}

			{#if active.status === 'graded' && active.submission}
				<div class="mt-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 p-3">
					<div class="text-sm font-semibold text-blue-700 dark:text-blue-300">
						{$i18n.t('Grade')}: {active.submission.grade}
					</div>
					{#if active.submission.feedback}<div
							class="text-sm text-gray-700 dark:text-gray-200 mt-1"
						>
							{active.submission.feedback}
						</div>{/if}
				</div>
			{/if}

			{#if isExamGate}
				<!-- E10: proctored-exam gate -->
				<div
					class="mt-4 rounded-xl border border-amber-300 dark:border-amber-700/50 bg-amber-50 dark:bg-amber-900/20 p-4"
				>
					<div
						class="flex items-center gap-2 text-amber-800 dark:text-amber-300 font-semibold text-sm"
					>
						🔒 {$i18n.t('Proctored exam')}
					</div>
					<ul class="text-sm text-gray-700 dark:text-gray-200 mt-2 space-y-1 list-disc pl-5">
						<li>{$i18n.t('The exam opens in full screen.')}</li>
						<li>
							{$i18n.t(
								'Leaving the page or exiting full screen is recorded and your teacher is notified.'
							)}
						</li>
						{#if examInfo?.config?.max_violations}
							<li>
								{$i18n
									.t('After {{n}} warnings the exam is submitted automatically.')
									.replace('{{n}}', String(examInfo.config.max_violations))}
							</li>
						{/if}
						{#if examInfo?.config?.time_limit_minutes}
							<li>
								{$i18n
									.t('Time limit: {{n}} minutes.')
									.replace('{{n}}', String(examInfo.config.time_limit_minutes))}
							</li>
						{/if}
					</ul>
				</div>
				{#if message}<p class="text-sm mt-2 text-red-500">{message}</p>{/if}
				<div class="flex justify-end gap-2 mt-5">
					<button
						class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
						on:click={() => (active = null)}>{$i18n.t('Cancel')}</button
					>
					<button
						class="px-5 py-2 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-semibold hover:opacity-90 disabled:opacity-50"
						on:click={startExamFlow}
						disabled={startingExam}
						>{startingExam ? $i18n.t('Starting…') : $i18n.t('Start exam')}</button
					>
				</div>
			{:else if examInfo?.is_exam}
				<!-- E10: a proctored exam already taken — read-only, no resubmit -->
				<div
					class="mt-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/40 p-4 text-sm text-gray-700 dark:text-gray-200"
				>
					✅ {$i18n.t('You have completed this exam. Exam answers cannot be resubmitted.')}
					{#if active.submission?.content}
						<div class="mt-3 whitespace-pre-wrap text-gray-600 dark:text-gray-300">
							{active.submission.content}
						</div>
					{/if}
				</div>
				<div class="flex justify-end mt-5">
					<button
						class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
						on:click={() => (active = null)}>{$i18n.t('Close')}</button
					>
				</div>
			{:else}
				<div class="mt-4">
					<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
						>{$i18n.t('Your work')}</label
					>
					<textarea
						rows="6"
						class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300"
						bind:value={draft}
						placeholder={$i18n.t('Type your answer…')}
					></textarea>
					{#if active.submission}
						<p class="text-xs text-gray-400 mt-1">
							{$i18n.t('Submitting again replaces your previous work and clears any grade.')}
						</p>
					{/if}
				</div>

				<div class="mt-3">
					<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
						>{$i18n.t('Attachment (optional)')}</label
					>
					<input
						type="file"
						class="w-full text-sm text-gray-600 dark:text-gray-300 file:mr-3 file:rounded-full file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-blue-700 hover:file:bg-blue-100"
						on:change={onPickFile}
					/>
					{#if active.submission?.attachment_id}
						<button
							class="mt-2 inline-flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 hover:underline"
							on:click={getMyFile}
						>
							📎 {$i18n.t('Your submitted file')}: {active.submission.attachment_name ??
								$i18n.t('attachment')}
						</button>
					{/if}
				</div>

				{#if message}<p
						class="text-sm mt-2 {message === $i18n.t('Submitted!')
							? 'text-green-600'
							: 'text-red-500'}"
					>
						{message}
					</p>{/if}

				<div class="flex justify-end gap-2 mt-5">
					<button
						class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
						on:click={() => (active = null)}>{$i18n.t('Close')}</button
					>
					<button
						class="px-4 py-2 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm hover:opacity-90 disabled:opacity-50"
						on:click={submit}
						disabled={submitting || (!draft.trim() && !file)}
						>{active.submission ? $i18n.t('Resubmit') : $i18n.t('Submit')}</button
					>
				</div>
			{/if}
		</div>
	</div>
{/if}

{#if examActive && active && examConfig}
	<ExamShell
		assignment={{
			id: active.id,
			title: active.title,
			instructions: active.instructions,
			attachment_id: active.attachment_id,
			attachment_name: active.attachment_name
		}}
		config={examConfig}
		violations={examViolations}
		startedAt={examStartedAt}
		on:done={() => load()}
		on:close={onExamDone}
	/>
{/if}
