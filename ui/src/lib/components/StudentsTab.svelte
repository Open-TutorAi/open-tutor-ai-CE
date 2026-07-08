<!-- src/lib/components/StudentsTab.svelte -->

<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import { ClassroomsAPI } from '$lib/apis/classrooms';
	import type { StudentOut } from '$lib/types/classroom';
	import CreateStudentModal from './CreateStudentModal.svelte';
	import StudentAvatar from './StudentAvatar.svelte';
	import ClassroomSeatingChart from './ClassroomSeatingChart.svelte';
	import StudentInfoModal from './StudentInfoModal.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import DocumentDuplicate from '$lib/components/icons/DocumentDuplicate.svelte';

	const i18n = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';

	let students: StudentOut[] = [];
	let loading = true;
	let error: string | null = null;
	let emailInput = '';
	let submitting = false;
	let showCreateModal = false;
	let view: 'list' | 'seating' = 'list';
	let showStudentModal = false;
	let selectedStudent: StudentOut | null = null;

	const openStudentInfo = (student: StudentOut) => {
		selectedStudent = student;
		showStudentModal = true;
	};

	// CSV import state
	let csvFile: File | null = null;
	let importing = false;
	let importResult: any = null;

	// Invite creation state
	let inviteCreating = false;
	let inviteCode: string | null = null;
	let inviteExpires: string = '';
	let inviteMaxUses: number | null = null;

	const loadStudents = async () => {
		loading = true;
		error = null;
		try {
			students = await ClassroomsAPI.listStudents(token(), $page.params.id);
		} catch (err: any) {
			error = err?.detail || $i18n.t('Failed to load students');
		} finally {
			loading = false;
		}
	};

	onMount(() => {
		if (!browser) return;
		loadStudents();
	});

	const addStudent = async () => {
		if (!emailInput.trim()) return;
		submitting = true;
		error = null;
		try {
			const result = await ClassroomsAPI.addStudent(token(), $page.params.id, emailInput.trim());
			students = [
				...students,
				{
					id: result.student_id,
					name: result.student_name,
					email: result.student_email,
					enrolled_at: new Date().toISOString()
				}
			];
			emailInput = '';
		} catch (err: any) {
			error = err?.detail || $i18n.t('Failed to add student');
		} finally {
			submitting = false;
		}
	};

	const onFileChange = (e: Event) => {
		const input = e.target as HTMLInputElement;
		if (input.files && input.files.length) csvFile = input.files[0];
	};

	const uploadCsv = async () => {
		if (!csvFile) return;
		importing = true;
		try {
			const res = await ClassroomsAPI.importStudents(token(), $page.params.id, csvFile);
			importResult = res;
			// reload students list after import
			loadStudents();
		} catch (err: any) {
			error = err?.detail || $i18n.t('Failed to import CSV');
		} finally {
			importing = false;
		}
	};

	const createInvite = async () => {
		inviteCreating = true;
		inviteCode = null;
		try {
			const body: any = {};
			if (inviteExpires) body.expires_at = inviteExpires;
			if (inviteMaxUses) body.max_uses = inviteMaxUses;
			const res = await ClassroomsAPI.createInvite(token(), $page.params.id, body);
			inviteCode = res.code;
		} catch (err: any) {
			error = err?.detail || $i18n.t('Failed to create invite');
		} finally {
			inviteCreating = false;
		}
	};

	const removeStudent = async (studentId: string) => {
		if (!confirm($i18n.t('Remove this student from the classroom?'))) return;
		try {
			await ClassroomsAPI.removeStudent(token(), $page.params.id, studentId);
			students = students.filter((s) => s.id !== studentId);
		} catch (err: any) {
			error = err?.detail || $i18n.t('Failed to remove student');
		}
	};

	const handleStudentAdded = () => {
		loadStudents();
	};
</script>

<div data-testid="students-tab" class="space-y-4">
	{#if error}
		<div
			class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-sm text-red-700 dark:text-red-300"
		>
			{error}
		</div>
	{/if}

	<div class="flex flex-col sm:flex-row gap-2">
		<input
			type="email"
			bind:value={emailInput}
			placeholder={$i18n.t('Student email')}
			class="flex-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
			disabled={submitting}
			on:keydown={(e) => e.key === 'Enter' && addStudent()}
		/>
		<button
			type="button"
			on:click={addStudent}
			disabled={!emailInput.trim() || submitting}
			class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
		>
			{submitting ? $i18n.t('Adding...') : $i18n.t('Add Student')}
		</button>
		<button
			type="button"
			on:click={() => (showCreateModal = true)}
			class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 whitespace-nowrap"
		>
			{$i18n.t('+ Create Student')}
		</button>
	</div>

	<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
		<div
			class="bg-gray-50 dark:bg-gray-900/40 border border-gray-100 dark:border-gray-700 rounded-lg p-4 hover:shadow-sm transition-shadow"
		>
			<label
				for="csv-import-input"
				class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
			>
				{$i18n.t('Import students (CSV)')}
			</label>
			<div class="flex gap-2">
				<input
					id="csv-import-input"
					type="file"
					accept="text/csv"
					on:change={onFileChange}
					class="flex-1 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
				/>
				<button
					type="button"
					on:click={uploadCsv}
					disabled={!csvFile || importing}
					class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
				>
					{importing ? $i18n.t('Importing...') : $i18n.t('Upload')}
				</button>
			</div>
			<p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
				{$i18n.t('Columns: email, name, password (optional)')}
			</p>

			{#if importResult}
				<div
					transition:fade={{ duration: 150 }}
					data-testid="import-result"
					class="mt-3 p-2 bg-white dark:bg-gray-800 rounded text-xs text-gray-600 dark:text-gray-400"
				>
					{$i18n.t('Created')}: {importResult.created} · {$i18n.t('Enrolled')}: {importResult.enrolled}
					· {$i18n.t('Skipped')}: {importResult.skipped}
				</div>
			{/if}
		</div>

		<div
			class="bg-gray-50 dark:bg-gray-900/40 border border-gray-100 dark:border-gray-700 rounded-lg p-4 hover:shadow-sm transition-shadow"
		>
			<label
				for="invite-expires-input"
				class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
			>
				{$i18n.t('Create a join code')}
			</label>
			<div class="flex flex-wrap gap-2">
				<input
					id="invite-expires-input"
					type="datetime-local"
					bind:value={inviteExpires}
					class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1.5 text-sm"
				/>
				<input
					type="number"
					min="1"
					bind:value={inviteMaxUses}
					placeholder={$i18n.t('Max uses')}
					aria-label={$i18n.t('Max uses')}
					class="w-24 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1.5 text-sm"
				/>
				<button
					type="button"
					on:click={createInvite}
					disabled={inviteCreating}
					class="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
				>
					{inviteCreating ? $i18n.t('Creating...') : $i18n.t('Create Code')}
				</button>
			</div>

			{#if inviteCode}
				<div
					transition:fade={{ duration: 150 }}
					data-testid="invite-code"
					class="mt-3 flex items-center justify-between gap-2 text-sm bg-white dark:bg-gray-800 px-3 py-2 rounded-lg"
				>
					<span class="font-mono font-semibold text-gray-900 dark:text-white">{inviteCode}</span>
					<button
						type="button"
						data-testid="copy-invite-code-button"
						title={$i18n.t('Copy')}
						aria-label={$i18n.t('Copy')}
						on:click={() => inviteCode && navigator.clipboard?.writeText(inviteCode)}
						class="p-1.5 rounded-full text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
					>
						<DocumentDuplicate className="w-4 h-4" />
					</button>
				</div>
				<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
					{$i18n.t('Share this code — students can use it to join from their dashboard.')}
				</p>
			{/if}
		</div>
	</div>

	{#if loading}
		<div class="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-3">
			<div
				class="w-4 h-4 rounded-full border-2 border-gray-300 dark:border-gray-600 border-t-blue-600 animate-spin"
			></div>
			{$i18n.t('Loading students...')}
		</div>
		<div class="space-y-2" aria-hidden="true">
			{#each Array(3) as _}
				<div class="h-12 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse"></div>
			{/each}
		</div>
	{:else if students.length === 0}
		<div class="text-center py-8 text-gray-500 dark:text-gray-400">
			{$i18n.t('No students enrolled yet')}
		</div>
	{:else}
		<div class="flex justify-end mb-3">
			<div class="inline-flex rounded-lg border border-gray-200 dark:border-gray-700 p-0.5">
				<button
					type="button"
					data-testid="view-toggle-list"
					on:click={() => (view = 'list')}
					class="px-3 py-1 text-xs font-medium rounded-md transition-colors {view === 'list'
						? 'bg-blue-600 text-white'
						: 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}"
				>
					{$i18n.t('List')}
				</button>
				<button
					type="button"
					data-testid="view-toggle-seating"
					on:click={() => (view = 'seating')}
					class="px-3 py-1 text-xs font-medium rounded-md transition-colors {view === 'seating'
						? 'bg-blue-600 text-white'
						: 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}"
				>
					{$i18n.t('Classroom view')}
				</button>
			</div>
		</div>

		{#if view === 'seating'}
			<ClassroomSeatingChart {students} on:selectStudent={(e) => openStudentInfo(e.detail)} />
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="text-left border-b border-gray-200 dark:border-gray-700">
							<th class="py-2 text-gray-600 dark:text-gray-400">{$i18n.t('Name')}</th>
							<th class="py-2 text-gray-600 dark:text-gray-400">{$i18n.t('Email')}</th>
							<th class="py-2 text-gray-600 dark:text-gray-400">{$i18n.t('Enrolled')}</th>
							<th class="py-2 text-right text-gray-600 dark:text-gray-400">{$i18n.t('Actions')}</th>
						</tr>
					</thead>
					<tbody>
						{#each students as student (student.id)}
							<tr
								in:fade={{ duration: 150 }}
								class="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/60 transition-colors"
								data-testid="student-row"
							>
								<td class="py-2 text-gray-900 dark:text-white">
									<div class="flex items-center gap-2">
										<button
											type="button"
											data-testid="student-avatar-button"
											on:click={() => openStudentInfo(student)}
											aria-label={$i18n.t('View student info')}
											class="rounded-full focus:outline-none focus:ring-2 focus:ring-blue-400"
										>
											<StudentAvatar
												name={student.name}
												imageUrl={student.profile_image_url}
												size="sm"
											/>
										</button>
										{student.name}
									</div>
								</td>
								<td class="py-2 text-gray-600 dark:text-gray-400">{student.email}</td>
								<td class="py-2 text-gray-500 dark:text-gray-400">
									{new Date(student.enrolled_at).toLocaleDateString()}
								</td>
								<td class="py-2 text-right">
									<button
										type="button"
										data-testid="remove-student-button"
										title={$i18n.t('Remove')}
										aria-label={$i18n.t('Remove student')}
										on:click={() => removeStudent(student.id)}
										class="p-1.5 rounded-full text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
									>
										<GarbageBin className="w-4 h-4" />
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

<CreateStudentModal
	bind:show={showCreateModal}
	classroomId={$page.params.id}
	on:studentAdded={handleStudentAdded}
/>

<StudentInfoModal
	bind:show={showStudentModal}
	student={selectedStudent}
	classroomId={$page.params.id}
/>
