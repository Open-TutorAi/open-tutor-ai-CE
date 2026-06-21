<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getAssignments, createAssignment, type Assignment } from '$lib/apis/assignments';
	import { getClassrooms, createClassroom, type Classroom } from '$lib/apis/classrooms';
	import { uploadFile } from '$lib/apis/files';
	import { TUTOR_API_BASE_URL } from '$lib/constants';

	const i18n = getContext('i18n');

	let assignments: Assignment[] = [];
	let classrooms: Classroom[] = [];
	let loading = true;
	let activeTab: 'all' | 'active' | 'pastdue' | 'completed' = 'all';

	// Create modal
	let showModal = false;
	let form = { title: '', instructions: '', classroom_id: '', due_date: '', max_score: 20 };
	let formErrors = { title: '', classroom_id: '', due_date: '' };
	let submitting = false;
	let attachmentFile: File | null = null;
	let attachmentName = '';

	// Inline classroom creation
	let showClassroomForm = false;
	let classForm = { name: '', subject: '' };
	let creatingClass = false;

	async function handleCreateClassroom() {
		if (!classForm.name.trim()) { toast.error('Class name is required'); return; }
		creatingClass = true;
		try {
			const c = await createClassroom(localStorage.token, {
				name: classForm.name.trim(),
				subject: classForm.subject.trim() || undefined,
			});
			classrooms = [...classrooms, c];
			form.classroom_id = c.id;
			classForm = { name: '', subject: '' };
			showClassroomForm = false;
			toast.success('Classroom created');
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to create classroom');
		} finally { creatingClass = false; }
	}

	onMount(async () => {
		try {
			[assignments, classrooms] = await Promise.all([
				getAssignments(localStorage.token).catch(() => []),
				getClassrooms(localStorage.token).catch(() => [])
			]);
		} finally { loading = false; }
	});

	function openModal() {
		form = { title: '', instructions: '', classroom_id: '', due_date: '', max_score: 20 };
		formErrors = { title: '', classroom_id: '', due_date: '' };
		attachmentFile = null;
		attachmentName = '';
		showClassroomForm = false;
		showModal = true;
	}

	function handleFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		attachmentFile = input.files?.[0] ?? null;
		attachmentName = attachmentFile?.name ?? '';
	}

	function removeAttachment() {
		attachmentFile = null;
		attachmentName = '';
	}

	function validate(): boolean {
		formErrors = { title: '', classroom_id: '', due_date: '' };
		let ok = true;
		if (!form.title.trim()) { formErrors.title = 'Title is required'; ok = false; }
		if (!form.classroom_id) { formErrors.classroom_id = 'Please select a class'; ok = false; }
		if (!form.due_date) { formErrors.due_date = 'Due date is required'; ok = false; }
		return ok;
	}

	async function handleCreate() {
		if (!validate()) return;
		submitting = true;
		try {
			let attachment_url: string | undefined;
			if (attachmentFile) {
				const uploaded = await uploadFile(localStorage.token, attachmentFile);
				attachment_url = `${TUTOR_API_BASE_URL}/files/${uploaded.id}/content`;
			}
			const a = await createAssignment(localStorage.token, {
				title: form.title.trim(),
				instructions: form.instructions.trim() || undefined,
				classroom_id: form.classroom_id,
				due_date: new Date(form.due_date).toISOString(),
				max_score: form.max_score,
				attachment_url,
			});
			assignments = [a, ...assignments];
			showModal = false;
			toast.success('Assignment created');
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to create assignment');
		} finally { submitting = false; }
	}

	function classroomName(id: string) {
		return classrooms.find(c => c.id === id)?.name ?? '—';
	}

	function isPastDue(a: Assignment) { return new Date(a.due_date) < new Date(); }

	$: filtered = assignments.filter(a => {
		if (activeTab === 'active') return !isPastDue(a);
		if (activeTab === 'pastdue') return isPastDue(a);
		return true;
	});

	$: totalCount  = assignments.length;
	$: activeCount = assignments.filter(a => !isPastDue(a)).length;
	$: pastDueCount = assignments.filter(a => isPastDue(a)).length;

	function fmtDate(d: string) {
		return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
	}

	function statusLabel(a: Assignment) {
		return isPastDue(a) ? 'Past Due' : 'Active';
	}
</script>

<div class="space-y-6">

	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-gray-800 dark:text-white">Assignments</h1>
			<p class="text-sm text-gray-500 dark:text-gray-400">Manage and track your class assignments</p>
		</div>
		<button on:click={openModal}
			class="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl shadow transition">
			<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			New Assignment
		</button>
	</div>

	<!-- Stats -->
	<div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
		{#each [
			{ label: 'Total Assignments', value: totalCount, color: 'text-gray-800 dark:text-white' },
			{ label: 'Active', value: activeCount, color: 'text-indigo-600' },
			{ label: 'Pending Review', value: 0, color: 'text-amber-500' },
			{ label: 'Past Due', value: pastDueCount, color: 'text-red-500' },
		] as stat}
			<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4">
				<p class="text-2xl font-bold {stat.color}">{stat.value}</p>
				<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{stat.label}</p>
			</div>
		{/each}
	</div>

	<!-- Table -->
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm overflow-hidden">
		<!-- Tabs -->
		<div class="border-b border-gray-100 dark:border-gray-700 flex overflow-x-auto">
			{#each [['all','All'],['active','Active'],['pastdue','Past Due']] as [id, label]}
				<button on:click={() => activeTab = id}
					class="px-5 py-4 text-sm font-medium whitespace-nowrap border-b-2 transition
					{activeTab === id ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-200'}">
					{label}
				</button>
			{/each}
		</div>

		{#if loading}
			<div class="flex justify-center py-16">
				<div class="h-6 w-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
			</div>
		{:else if filtered.length === 0}
			<div class="py-16 text-center text-gray-400">
				<div class="text-4xl mb-3">📝</div>
				<p class="font-medium text-gray-600 dark:text-gray-300">No assignments yet</p>
				<p class="text-sm mt-1">Click "New Assignment" to create your first one</p>
			</div>
		{:else}
			<table class="w-full text-sm">
				<thead class="bg-gray-50 dark:bg-gray-700/40">
					<tr>
						<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Assignment</th>
						<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">Class</th>
						<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Due Date</th>
						<th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Status</th>
						<th class="px-5 py-3"></th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100 dark:divide-gray-700">
					{#each filtered as a}
						<tr class="hover:bg-gray-50 dark:hover:bg-gray-700/20 transition-colors cursor-pointer" on:click={() => goto(`/teacher/assignments/${a.id}`)}>
							<td class="px-5 py-4 font-medium text-gray-800 dark:text-white">{a.title}</td>
							<td class="px-5 py-4 text-gray-500 dark:text-gray-400 hidden sm:table-cell">{classroomName(a.classroom_id)}</td>
							<td class="px-5 py-4 {isPastDue(a) ? 'text-red-500 font-medium' : 'text-gray-500 dark:text-gray-400'}">{fmtDate(a.due_date)}</td>
							<td class="px-5 py-4 hidden md:table-cell">
								{#if isPastDue(a)}
									<span class="px-2 py-1 bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 text-xs font-semibold rounded-full">Past Due</span>
								{:else}
									<span class="px-2 py-1 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs font-semibold rounded-full">Active</span>
								{/if}
							</td>
							<td class="px-5 py-4 text-right">
								<button class="text-indigo-600 dark:text-indigo-400 text-xs font-semibold hover:underline">View →</button>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{/if}
	</div>
</div>

<!-- Create modal -->
{#if showModal}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
	on:click|self={() => (showModal = false)} role="dialog" aria-modal="true">
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-xl p-6">
		<div class="flex items-center justify-between mb-5">
			<div>
				<h3 class="font-bold text-gray-800 dark:text-white text-base">New Assignment</h3>
				<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Fill in the details below</p>
			</div>
			<button on:click={() => (showModal = false)} class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
				<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
			</button>
		</div>

		<form on:submit|preventDefault={handleCreate} class="space-y-4" novalidate>
			<!-- Title -->
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Title <span class="text-red-500">*</span></label>
				<input bind:value={form.title} placeholder="e.g. Chapter 3 Quiz"
					class="w-full border rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white
					{formErrors.title ? 'border-red-400' : 'border-gray-200 dark:border-gray-700'} focus:outline-none focus:ring-2 focus:ring-indigo-300 transition" />
				{#if formErrors.title}<p class="mt-1 text-xs text-red-500">{formErrors.title}</p>{/if}
			</div>

			<!-- Instructions -->
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Instructions</label>
				<textarea bind:value={form.instructions} placeholder="Describe what students need to do..." rows="3"
					class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"></textarea>
			</div>

			<!-- Class + Due date -->
			<div class="grid grid-cols-2 gap-4">
				<div>
					<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Class <span class="text-red-500">*</span></label>
					{#if classrooms.length === 0 && !showClassroomForm}
						<div class="flex items-center gap-2 p-3 border border-dashed border-gray-300 dark:border-gray-600 rounded-xl text-sm text-gray-500">
							<span>No classes yet.</span>
							<button type="button" on:click={() => (showClassroomForm = true)}
								class="text-indigo-600 hover:underline font-semibold">Create one</button>
						</div>
					{:else}
						<select bind:value={form.classroom_id}
							class="w-full border rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white
							{formErrors.classroom_id ? 'border-red-400' : 'border-gray-200 dark:border-gray-700'} focus:outline-none focus:ring-2 focus:ring-indigo-300 transition">
							<option value="">Select a class...</option>
							{#each classrooms as c}<option value={c.id}>{c.name}</option>{/each}
						</select>
						<button type="button" on:click={() => (showClassroomForm = !showClassroomForm)}
							class="mt-1 text-xs text-indigo-600 hover:underline">
							{showClassroomForm ? 'Cancel' : '+ Create new class'}
						</button>
					{/if}
					{#if formErrors.classroom_id}<p class="mt-1 text-xs text-red-500">{formErrors.classroom_id}</p>{/if}
				</div>
				<div>
					<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Due Date <span class="text-red-500">*</span></label>
					<input type="datetime-local" bind:value={form.due_date}
						class="w-full border rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white
						{formErrors.due_date ? 'border-red-400' : 'border-gray-200 dark:border-gray-700'} focus:outline-none focus:ring-2 focus:ring-indigo-300 transition" />
					{#if formErrors.due_date}<p class="mt-1 text-xs text-red-500">{formErrors.due_date}</p>{/if}
				</div>
			</div>

			<!-- Inline classroom creation form -->
			{#if showClassroomForm}
			<div class="border border-indigo-200 dark:border-indigo-700 rounded-xl p-4 bg-indigo-50 dark:bg-indigo-900/20 space-y-3">
				<p class="text-xs font-semibold text-indigo-700 dark:text-indigo-300 uppercase tracking-wide">New Classroom</p>
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1">Name <span class="text-red-500">*</span></label>
						<input bind:value={classForm.name} placeholder="e.g. Math 6A"
							class="w-full border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"/>
					</div>
					<div>
						<label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1">Subject</label>
						<input bind:value={classForm.subject} placeholder="e.g. Mathematics"
							class="w-full border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"/>
					</div>
				</div>
				<div class="flex gap-2">
					<button type="button" on:click={() => (showClassroomForm = false)}
						class="px-3 py-1.5 text-xs text-gray-500 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition">
						Cancel
					</button>
					<button type="button" on:click={handleCreateClassroom} disabled={creatingClass}
						class="px-3 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-semibold rounded-lg transition flex items-center gap-1.5">
						{#if creatingClass}
							<span class="h-3 w-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
						{/if}
						Create Classroom
					</button>
				</div>
			</div>
			{/if}

			<!-- Max score -->
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Max Score</label>
				<input type="number" bind:value={form.max_score} min="1" max="100"
					class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300 transition" />
			</div>

			<!-- Attachment -->
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Attachment <span class="text-xs font-normal text-gray-400">(optional)</span></label>
				{#if attachmentName}
					<div class="flex items-center gap-2 px-3 py-2.5 border border-indigo-200 dark:border-indigo-700 rounded-xl bg-indigo-50 dark:bg-indigo-900/20">
						<svg class="h-4 w-4 text-indigo-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
						</svg>
						<span class="text-sm text-indigo-700 dark:text-indigo-300 truncate flex-1">{attachmentName}</span>
						<button type="button" on:click={removeAttachment} class="text-gray-400 hover:text-red-500 transition shrink-0">
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
							accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.png,.jpg,.jpeg"/>
					</label>
				{/if}
			</div>

			<div class="flex gap-3 pt-1">
				<button type="button" on:click={() => (showModal = false)}
					class="flex-1 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
					Cancel
				</button>
				<button type="submit" disabled={submitting}
					class="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-semibold rounded-xl transition flex items-center justify-center gap-2">
					{#if submitting}
						<span class="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
						Creating…
					{:else}
						Create Assignment
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>
{/if}
