<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getAssignment, getSubmissions, gradeSubmission, getStatusTracker, updateAssignment, deleteAssignment, type Assignment, type Submission, type StatusRow } from '$lib/apis/assignments';
	import { getClassrooms, getClassroomStudents, type Classroom } from '$lib/apis/classrooms';

	const i18n = getContext('i18n');
	$: assignmentId = $page.params.id;

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

	type Tab = 'submissions' | 'overview' | 'status';

	let assignment: Assignment | null = null;
	let submissions: Submission[] = [];
	let statusRows: StatusRow[] = [];
	let classrooms: Classroom[] = [];
	let studentNames = new Map<string, string>();
	let activeTab: Tab = 'submissions';
	let loading = true;

	// Edit modal
	let showEditModal = false;
	let editTitle = '';
	let editInstructions = '';
	let editDueDate = '';
	let editMaxScore = '';
	let saving = false;

	function openEdit() {
		if (!assignment) return;
		editTitle = assignment.title;
		editInstructions = assignment.instructions ?? '';
		editDueDate = assignment.due_date.slice(0, 16);
		editMaxScore = String(assignment.max_score);
		showEditModal = true;
	}

	async function handleEdit() {
		if (!assignment) return;
		saving = true;
		try {
			const updated = await updateAssignment(localStorage.token, assignment.id, {
				title: editTitle.trim() || undefined,
				instructions: editInstructions || undefined,
				due_date: editDueDate ? new Date(editDueDate).toISOString() : undefined,
				max_score: editMaxScore ? parseInt(editMaxScore) : undefined,
			});
			assignment = updated;
			showEditModal = false;
			toast.success('Assignment updated');
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to update');
		} finally { saving = false; }
	}

	// Delete
	let deleting = false;
	async function handleDelete() {
		if (!assignment) return;
		if (!confirm(`Delete "${assignment.title}"? This will also delete all submissions.`)) return;
		deleting = true;
		try {
			await deleteAssignment(localStorage.token, assignment.id);
			toast.success('Assignment deleted');
			goto('/teacher/assignments');
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to delete');
		} finally { deleting = false; }
	}

	// Grade modal
	let showGradeModal = false;
	let gradingSub: Submission | null = null;
	let gradeScore = '';
	let gradeFeedback = '';
	let gradeScoreError = '';
	let grading = false;

	onMount(async () => {
		try {
			[assignment, submissions, classrooms] = await Promise.all([
				getAssignment(localStorage.token, assignmentId),
				getSubmissions(localStorage.token, assignmentId).catch(() => []),
				getClassrooms(localStorage.token).catch(() => []),
			]);
			statusRows = await getStatusTracker(localStorage.token, assignmentId).catch(() => []);
			if (assignment?.classroom_id) {
				const enrolled = await getClassroomStudents(localStorage.token, assignment.classroom_id).catch(() => []);
				studentNames = new Map(enrolled.map((s: { student_id: string; name: string }) => [s.student_id, s.name]));
			}
		} catch {
			toast.error('Assignment not found');
			goto('/teacher/assignments');
		} finally { loading = false; }
	});

	function classroomName(id: string) {
		return classrooms.find(c => c.id === id)?.name ?? id;
	}

	function fmtDate(d: string | null) {
		if (!d) return '—';
		return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
	}

	function fmtDateTime(d: string | null) {
		if (!d) return '—';
		const dt = new Date(d);
		return dt.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) + ' · ' + dt.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
	}

	function isPastDue(a: Assignment) { return new Date(a.due_date) < new Date(); }

	function initials(id: string) {
		const name = studentNames.get(id);
		if (name) return name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2);
		return id.slice(0, 2).toUpperCase();
	}
	function studentLabel(id: string) {
		return studentNames.get(id) ?? id.slice(0, 8) + '…';
	}

	function openGrade(sub: Submission) {
		gradingSub = sub;
		gradeScore = sub.score != null ? String(sub.score) : '';
		gradeFeedback = sub.feedback ?? '';
		gradeScoreError = '';
		showGradeModal = true;
	}

	async function handleGrade() {
		if (!gradingSub || !assignment) return;
		gradeScoreError = '';
		const score = parseInt(gradeScore);
		if (isNaN(score) || score < 0 || score > assignment.max_score) {
			gradeScoreError = `Score must be between 0 and ${assignment.max_score}`;
			return;
		}
		grading = true;
		try {
			const updated = await gradeSubmission(localStorage.token, assignment.id, gradingSub.id, { score, feedback: gradeFeedback || undefined });
			submissions = submissions.map(s => s.id === updated.id ? updated : s);
			statusRows = statusRows.map(r => r.submission?.id === updated.id ? { ...r, submission: updated, status: 'returned' } : r);
			showGradeModal = false;
			toast.success('Grade returned to student');
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to grade');
		} finally { grading = false; }
	}

	$: submittedCount = submissions.length;
	$: notYetCount = statusRows.filter(r => r.status === 'not_submitted' || r.status === 'missed').length;
	$: lateCount = submissions.filter(s => s.status === 'late').length;

	const STATUS_COLORS: Record<string, string> = {
		submitted: 'bg-indigo-100 text-indigo-700',
		late:      'bg-amber-100 text-amber-700',
		returned:  'bg-green-100 text-green-700',
		missed:    'bg-red-100 text-red-600',
		not_submitted: 'bg-gray-100 text-gray-500',
	};
	const STATUS_LABELS: Record<string, string> = {
		submitted: 'On Time', late: 'Late', returned: 'Returned',
		missed: 'Missed', not_submitted: 'Not Yet',
	};
</script>

{#if loading}
	<div class="flex justify-center py-20">
		<div class="h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
	</div>
{:else if assignment}
<div class="space-y-4">

	<!-- Back -->
	<button on:click={() => goto('/teacher/assignments')}
		class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 transition font-medium">
		<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
		Back to Assignments
	</button>

	<!-- Header card -->
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
		<div class="flex items-start justify-between mb-4">
			<div>
				<h1 class="text-xl font-bold text-gray-800 dark:text-white">{assignment.title}</h1>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
					📚 {classroomName(assignment.classroom_id)} &nbsp;·&nbsp; 📅 Due {fmtDate(assignment.due_date)}
				</p>
			</div>
			<div class="flex items-center gap-2 shrink-0">
				{#if isPastDue(assignment)}
					<span class="px-3 py-1 bg-red-100 text-red-600 text-xs font-semibold rounded-full">Past Due</span>
				{:else}
					<span class="px-3 py-1 bg-indigo-100 text-indigo-700 text-xs font-semibold rounded-full">Active</span>
				{/if}
				<button on:click={openEdit}
					class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-600 border border-indigo-200 rounded-xl hover:bg-indigo-50 transition">
					<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
					Edit
				</button>
				<button on:click={handleDelete} disabled={deleting}
					class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-red-600 border border-red-200 rounded-xl hover:bg-red-50 transition disabled:opacity-50">
					<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
					Delete
				</button>
			</div>
		</div>

		<!-- Stats -->
		<div class="grid grid-cols-3 gap-3">
			<div class="bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-3 text-center">
				<p class="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{submittedCount}</p>
				<p class="text-xs text-gray-500 dark:text-gray-400">Submitted</p>
			</div>
			<div class="bg-amber-50 dark:bg-amber-900/20 rounded-xl p-3 text-center">
				<p class="text-2xl font-bold text-amber-500">{notYetCount}</p>
				<p class="text-xs text-gray-500 dark:text-gray-400">Not yet</p>
			</div>
			<div class="bg-red-50 dark:bg-red-900/20 rounded-xl p-3 text-center">
				<p class="text-2xl font-bold text-red-500">{lateCount}</p>
				<p class="text-xs text-gray-500 dark:text-gray-400">Late</p>
			</div>
		</div>
	</div>

	<!-- Tabs + content -->
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm overflow-hidden">
		<div class="border-b border-gray-100 dark:border-gray-700 flex">
			{#each [['submissions','Submissions'],['overview','Overview'],['status','Status Tracker']] as [id, label]}
				<button on:click={() => activeTab = id}
					class="px-5 py-4 text-sm font-medium border-b-2 transition
					{activeTab === id ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-200'}">
					{label}
				</button>
			{/each}
		</div>

		<!-- Submissions tab -->
		{#if activeTab === 'submissions'}
			{#if submissions.length === 0}
				<div class="py-16 text-center text-gray-400">
					<div class="text-4xl mb-3">📭</div>
					<p class="font-medium">No submissions yet</p>
				</div>
			{:else}
				<table class="w-full text-sm">
					<thead class="bg-gray-50 dark:bg-gray-700/40">
						<tr>
							<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Student</th>
							<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider hidden sm:table-cell">Submitted At</th>
							<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
							<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Grade</th>
							<th class="px-5 py-3"></th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100 dark:divide-gray-700">
						{#each submissions as sub}
							<tr class="hover:bg-gray-50 dark:hover:bg-gray-700/20 transition-colors">
								<td class="px-5 py-3">
									<div class="flex items-center gap-2">
										<div class="h-7 w-7 rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-300 text-xs font-bold flex items-center justify-center shrink-0">
											{initials(sub.student_id)}
										</div>
										<span class="font-medium text-gray-800 dark:text-white text-xs">{studentLabel(sub.student_id)}</span>
									</div>
								</td>
								<td class="px-5 py-3 text-gray-500 dark:text-gray-400 hidden sm:table-cell">
									<div class="flex items-center gap-1.5">
										{fmtDateTime(sub.submitted_at)}
										{#if sub.attachment_url}
											<svg title="Has attachment" class="h-3.5 w-3.5 text-indigo-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
											</svg>
										{/if}
									</div>
								</td>
								<td class="px-5 py-3">
									<span class="px-2 py-0.5 text-xs font-semibold rounded-full {STATUS_COLORS[sub.status] ?? 'bg-gray-100 text-gray-500'}">
										{STATUS_LABELS[sub.status] ?? sub.status}
									</span>
								</td>
								<td class="px-5 py-3">
									{#if sub.score != null}
										<span class="font-semibold text-gray-800 dark:text-white">{sub.score}/{assignment.max_score}</span>
									{:else}
										<span class="text-gray-400 italic text-xs">Not graded</span>
									{/if}
								</td>
								<td class="px-5 py-3 text-right">
									<button on:click={() => openGrade(sub)}
										class="text-xs font-semibold border border-indigo-200 dark:border-indigo-700 text-indigo-600 dark:text-indigo-400 px-3 py-1 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition">
										{sub.status === 'returned' ? 'Review' : 'Grade'}
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			{/if}

		<!-- Overview tab -->
		{:else if activeTab === 'overview'}
			<div class="p-6 space-y-4">
				<div>
					<p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Instructions</p>
					<p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{assignment.instructions ?? 'No instructions provided.'}</p>
				</div>
				<div class="grid grid-cols-2 gap-4 pt-2">
					<div>
						<p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Due Date</p>
						<p class="text-sm font-medium text-gray-700 dark:text-gray-300">{fmtDate(assignment.due_date)}</p>
					</div>
					<div>
						<p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Max Score</p>
						<p class="text-sm font-medium text-gray-700 dark:text-gray-300">{assignment.max_score} points</p>
					</div>
				</div>
				{#if assignment.attachment_url}
				<div class="pt-2">
					<p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Attachment</p>
					<button on:click={() => downloadAttachment(assignment.attachment_url ?? '')}
						class="inline-flex items-center gap-2 px-4 py-2 border border-indigo-200 dark:border-indigo-700 rounded-xl text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition font-medium">
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
						</svg>
						Download Attachment
					</button>
				</div>
				{/if}
			</div>

		<!-- Status Tracker tab -->
		{:else}
			{#if statusRows.length === 0}
				<div class="py-16 text-center text-gray-400">
					<p class="font-medium">No students enrolled yet</p>
				</div>
			{:else}
				<table class="w-full text-sm">
					<thead class="bg-gray-50 dark:bg-gray-700/40">
						<tr>
							<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Student</th>
							<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
							<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider hidden sm:table-cell">Submitted At</th>
							<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Grade</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100 dark:divide-gray-700">
						{#each statusRows as row}
							<tr class="hover:bg-gray-50 dark:hover:bg-gray-700/20 transition-colors">
								<td class="px-5 py-3">
									<div class="flex items-center gap-2">
										<div class="h-7 w-7 rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-300 text-xs font-bold flex items-center justify-center shrink-0">
											{initials(row.student_id)}
										</div>
										<span class="font-medium text-gray-800 dark:text-white text-xs">{studentLabel(row.student_id)}</span>
									</div>
								</td>
								<td class="px-5 py-3">
									<span class="px-2 py-0.5 text-xs font-semibold rounded-full {STATUS_COLORS[row.status] ?? 'bg-gray-100 text-gray-500'}">
										{STATUS_LABELS[row.status] ?? row.status}
									</span>
								</td>
								<td class="px-5 py-3 text-gray-500 dark:text-gray-400 hidden sm:table-cell">
									{fmtDateTime(row.submission?.submitted_at ?? null)}
								</td>
								<td class="px-5 py-3">
									{#if row.submission?.score != null}
										<span class="font-semibold text-gray-800 dark:text-white">{row.submission.score}/{assignment.max_score}</span>
									{:else}
										<span class="text-gray-400">—</span>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			{/if}
		{/if}
	</div>
</div>
{/if}

<!-- Edit modal -->
{#if showEditModal && assignment}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
	on:click|self={() => (showEditModal = false)} role="dialog" aria-modal="true">
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-lg p-6">
		<div class="flex items-center justify-between mb-5">
			<h3 class="font-bold text-gray-800 dark:text-white">Edit Assignment</h3>
			<button on:click={() => (showEditModal = false)} class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
				<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
			</button>
		</div>

		<div class="space-y-4">
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Title <span class="text-red-500">*</span></label>
				<input bind:value={editTitle} type="text" class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300"/>
			</div>
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Instructions</label>
				<textarea bind:value={editInstructions} rows="4" class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"></textarea>
			</div>
			<div class="grid grid-cols-2 gap-4">
				<div>
					<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Due Date</label>
					<input bind:value={editDueDate} type="datetime-local" class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300"/>
				</div>
				<div>
					<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Max Score</label>
					<input bind:value={editMaxScore} type="number" min="1" class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300"/>
				</div>
			</div>
		</div>

		<div class="flex gap-3 mt-5">
			<button type="button" on:click={() => (showEditModal = false)}
				class="flex-1 py-2.5 text-sm font-medium text-gray-600 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
				Cancel
			</button>
			<button on:click={handleEdit} disabled={saving || !editTitle.trim()}
				class="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-semibold rounded-xl transition flex items-center justify-center gap-2">
				{#if saving}
					<span class="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
					Saving…
				{:else}
					Save Changes
				{/if}
			</button>
		</div>
	</div>
</div>
{/if}

<!-- Grade modal -->
{#if showGradeModal && gradingSub && assignment}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
	on:click|self={() => (showGradeModal = false)} role="dialog" aria-modal="true">
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-lg p-6">
		<div class="flex items-center justify-between mb-4">
			<h3 class="font-bold text-gray-800 dark:text-white">Grade Submission</h3>
			<button on:click={() => (showGradeModal = false)} class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
				<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
			</button>
		</div>

		<!-- Student info -->
		<div class="flex items-center gap-3 bg-gray-50 dark:bg-gray-900/40 rounded-xl p-3 mb-4">
			<div class="h-10 w-10 rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-300 font-bold flex items-center justify-center shrink-0">
				{initials(gradingSub.student_id)}
			</div>
			<div>
				<p class="font-semibold text-gray-800 dark:text-white text-sm">{studentLabel(gradingSub.student_id)}</p>
				<p class="text-xs text-gray-500">
					Submitted {fmtDateTime(gradingSub.submitted_at)} ·
					<span class="{gradingSub.status === 'late' ? 'text-amber-600' : 'text-green-600'} font-semibold">
						{gradingSub.status === 'late' ? 'Late' : 'On Time'}
					</span>
				</p>
			</div>
		</div>

		<!-- Student's work -->
		{#if gradingSub.content || gradingSub.attachment_url}
			<div class="mb-4">
				<p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Student's Work</p>
				{#if gradingSub.content}
					<div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-xl p-4 text-sm text-gray-700 dark:text-gray-300 max-h-40 overflow-y-auto whitespace-pre-wrap mb-2">
						{gradingSub.content}
					</div>
				{/if}
				{#if gradingSub.attachment_url}
					<button on:click={() => downloadAttachment(gradingSub?.attachment_url ?? '')}
						class="inline-flex items-center gap-2 px-4 py-2 border border-indigo-200 dark:border-indigo-700 rounded-xl text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition font-medium">
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
						</svg>
						Download student's attachment
					</button>
				{/if}
			</div>
		{/if}

		<!-- Score + feedback -->
		<div class="grid grid-cols-2 gap-4 mb-4">
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Score <span class="text-red-500">*</span></label>
				<div class="flex items-center gap-2">
					<input type="number" bind:value={gradeScore} min="0" max={assignment.max_score}
						class="w-full border {gradeScoreError ? 'border-red-400' : 'border-gray-200 dark:border-gray-700'} rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300" />
					<span class="text-gray-500 text-sm whitespace-nowrap">/ {assignment.max_score}</span>
				</div>
				{#if gradeScoreError}<p class="mt-1 text-xs text-red-500">{gradeScoreError}</p>{/if}
			</div>
			<div class="flex items-end">
				<div class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-400 bg-gray-50 dark:bg-gray-900">
					Returned after grading
				</div>
			</div>
		</div>

		<div class="mb-5">
			<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Feedback (optional)</label>
			<textarea bind:value={gradeFeedback} rows="3" placeholder="Write feedback for the student..."
				class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"></textarea>
		</div>

		<div class="flex gap-3">
			<button type="button" on:click={() => (showGradeModal = false)}
				class="flex-1 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
				Cancel
			</button>
			<button on:click={handleGrade} disabled={grading}
				class="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-semibold rounded-xl transition flex items-center justify-center gap-2">
				{#if grading}
					<span class="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
					Returning…
				{:else}
					Return Grade
				{/if}
			</button>
		</div>
	</div>
</div>
{/if}
