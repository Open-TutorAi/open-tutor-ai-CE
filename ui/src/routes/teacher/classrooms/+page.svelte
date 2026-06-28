<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getClassrooms, createClassroom, updateClassroom, deleteClassroom, type Classroom } from '$lib/apis/classrooms';

	const i18n = getContext('i18n');

	let classrooms: Classroom[] = [];
	let loading = true;
	let searchQuery = '';

	// Create modal
	let showModal = false;
	let form = { name: '', description: '', subject: '' };
	let submitting = false;

	// Edit modal
	let showEditModal = false;
	let editingClassroom: Classroom | null = null;
	let editForm = { name: '', description: '', subject: '' };
	let editSubmitting = false;

	// Delete modal
	let showDeleteModal = false;
	let deletingClassroom: Classroom | null = null;
	let deleteSubmitting = false;

	onMount(async () => {
		try {
			classrooms = await getClassrooms(localStorage.token).catch(() => []);
		} finally {
			loading = false;
		}
	});

	$: filtered = classrooms.filter(
		(c) =>
			!searchQuery ||
			c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
			(c.subject ?? '').toLowerCase().includes(searchQuery.toLowerCase())
	);

	async function handleCreate() {
		if (!form.name.trim()) { toast.error('Class name is required'); return; }
		submitting = true;
		try {
			const c = await createClassroom(localStorage.token, {
				name: form.name.trim(),
				description: form.description.trim() || undefined,
				subject: form.subject.trim() || undefined,
			});
			classrooms = [c, ...classrooms];
			showModal = false;
			form = { name: '', description: '', subject: '' };
			toast.success('Classroom created');
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to create classroom');
		} finally { submitting = false; }
	}

	function openEdit(e: Event, classroom: Classroom) {
		e.stopPropagation();
		editingClassroom = classroom;
		editForm = { name: classroom.name, description: classroom.description ?? '', subject: classroom.subject ?? '' };
		showEditModal = true;
	}

	async function handleEdit() {
		if (!editForm.name.trim()) { toast.error('Class name is required'); return; }
		editSubmitting = true;
		try {
			const updated = await updateClassroom(localStorage.token, editingClassroom!.id, {
				name: editForm.name.trim(),
				description: editForm.description.trim() || undefined,
				subject: editForm.subject.trim() || undefined,
			});
			classrooms = classrooms.map(c => c.id === updated.id ? updated : c);
			showEditModal = false;
			editingClassroom = null;
			toast.success('Classroom updated');
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to update classroom');
		} finally { editSubmitting = false; }
	}

	function openDelete(e: Event, classroom: Classroom) {
		e.stopPropagation();
		deletingClassroom = classroom;
		showDeleteModal = true;
	}

	async function handleDelete() {
		deleteSubmitting = true;
		try {
			await deleteClassroom(localStorage.token, deletingClassroom!.id);
			classrooms = classrooms.filter(c => c.id !== deletingClassroom!.id);
			showDeleteModal = false;
			deletingClassroom = null;
			toast.success('Classroom deleted');
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to delete classroom');
		} finally { deleteSubmitting = false; }
	}

	function initials(name: string) { return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2); }

	const GRAD = ['from-indigo-500 to-violet-600','from-emerald-500 to-teal-600','from-rose-500 to-pink-600','from-amber-500 to-orange-600'];
	function grad(i: number) { return GRAD[i % GRAD.length]; }
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold text-gray-800 dark:text-white">My Classrooms</h1>
			<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage your classes and students</p>
		</div>
		<div class="flex items-center gap-3">
			<!-- Search -->
			<div class="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2 shadow-sm">
				<svg class="h-4 w-4 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
				</svg>
				<input type="text" placeholder="Search classrooms…" bind:value={searchQuery}
					class="bg-transparent text-sm outline-none text-gray-700 dark:text-gray-200 placeholder-gray-400 w-40"/>
			</div>
			<!-- Create button -->
			<button on:click={() => (showModal = true)}
				class="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl shadow transition">
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
				</svg>
				New Classroom
			</button>
		</div>
	</div>

	{#if loading}
		<div class="flex justify-center py-16">
			<div class="h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
		</div>

	{:else if filtered.length === 0}
		<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-16 text-center">
			<div class="text-4xl mb-4">🏫</div>
			<p class="text-gray-600 dark:text-gray-300 font-medium">
				{searchQuery ? 'No classrooms found' : 'No classrooms yet'}
			</p>
			{#if searchQuery}
				<button class="mt-3 text-sm text-indigo-600 hover:underline" on:click={() => (searchQuery = '')}>Clear search</button>
			{:else}
				<button on:click={() => (showModal = true)} class="mt-3 text-sm text-indigo-600 hover:underline">Create your first classroom</button>
			{/if}
		</div>

	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
			{#each filtered as classroom, i}
				<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 hover:shadow-md hover:border-indigo-200 dark:hover:border-indigo-700 transition-all duration-200 group">
					<!-- Card header -->
					<div class="flex items-start justify-between mb-3">
						<button on:click={() => goto(`/teacher/classrooms/${classroom.id}`)} class="flex items-center gap-3 flex-1 min-w-0 text-left">
							<div class="h-10 w-10 rounded-xl bg-gradient-to-br {grad(i)} flex items-center justify-center text-white font-bold text-sm shrink-0">
								{initials(classroom.name)}
							</div>
							{#if classroom.subject}
								<span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 truncate">
									{classroom.subject}
								</span>
							{/if}
						</button>
						<!-- Action buttons -->
						<div class="flex items-center gap-1 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
							<button on:click={(e) => openEdit(e, classroom)}
								title="Edit classroom"
								class="p-1.5 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 transition">
								<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
								</svg>
							</button>
							<button on:click={(e) => openDelete(e, classroom)}
								title="Delete classroom"
								class="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 transition">
								<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
								</svg>
							</button>
						</div>
					</div>

					<!-- Card body — clickable area -->
					<button on:click={() => goto(`/teacher/classrooms/${classroom.id}`)} class="w-full text-left">
						<h3 class="font-semibold text-gray-800 dark:text-white text-sm leading-snug group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2 mb-1">
							{classroom.name}
						</h3>
						{#if classroom.description}
							<p class="text-xs text-gray-500 dark:text-gray-400 mb-3 line-clamp-1">{classroom.description}</p>
						{/if}

						<div class="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-700 mt-3">
							<span class="text-xs text-gray-400">
								{new Date(classroom.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
							</span>
							<svg class="h-4 w-4 text-gray-300 group-hover:text-indigo-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
							</svg>
						</div>
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Create modal -->
{#if showModal}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
	on:click|self={() => (showModal = false)} role="dialog" aria-modal="true">
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6">
		<div class="flex items-center justify-between mb-5">
			<h3 class="font-bold text-gray-800 dark:text-white">New Classroom</h3>
			<button on:click={() => (showModal = false)} class="text-gray-400 hover:text-gray-600">
				<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
			</button>
		</div>

		<form on:submit|preventDefault={handleCreate} class="space-y-4">
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Class Name <span class="text-red-500">*</span></label>
				<input bind:value={form.name} placeholder="e.g. Math 6A"
					class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"/>
			</div>
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Subject</label>
				<input bind:value={form.subject} placeholder="e.g. Mathematics"
					class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"/>
			</div>
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Description</label>
				<textarea bind:value={form.description} placeholder="Optional description…" rows="2"
					class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"></textarea>
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
						Create
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>
{/if}

<!-- Edit modal -->
{#if showEditModal && editingClassroom}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
	on:click|self={() => (showEditModal = false)} role="dialog" aria-modal="true">
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6">
		<div class="flex items-center justify-between mb-5">
			<h3 class="font-bold text-gray-800 dark:text-white">Edit Classroom</h3>
			<button on:click={() => (showEditModal = false)} class="text-gray-400 hover:text-gray-600">
				<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
			</button>
		</div>

		<form on:submit|preventDefault={handleEdit} class="space-y-4">
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Class Name <span class="text-red-500">*</span></label>
				<input bind:value={editForm.name} placeholder="e.g. Math 6A"
					class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"/>
			</div>
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Subject</label>
				<input bind:value={editForm.subject} placeholder="e.g. Mathematics"
					class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"/>
			</div>
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Description</label>
				<textarea bind:value={editForm.description} placeholder="Optional description…" rows="2"
					class="w-full border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"></textarea>
			</div>
			<div class="flex gap-3 pt-1">
				<button type="button" on:click={() => (showEditModal = false)}
					class="flex-1 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
					Cancel
				</button>
				<button type="submit" disabled={editSubmitting}
					class="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-semibold rounded-xl transition flex items-center justify-center gap-2">
					{#if editSubmitting}
						<span class="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
						Saving…
					{:else}
						Save Changes
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>
{/if}

<!-- Delete confirmation modal -->
{#if showDeleteModal && deletingClassroom}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
	on:click|self={() => (showDeleteModal = false)} role="dialog" aria-modal="true">
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-sm p-6">
		<div class="flex items-center gap-3 mb-4">
			<div class="h-10 w-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center shrink-0">
				<svg class="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
				</svg>
			</div>
			<div>
				<h3 class="font-bold text-gray-800 dark:text-white">Delete Classroom</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400">This action cannot be undone</p>
			</div>
		</div>

		<p class="text-sm text-gray-600 dark:text-gray-300 mb-5">
			Are you sure you want to delete <span class="font-semibold">"{deletingClassroom.name}"</span>?
			All assignments and submissions will be permanently deleted.
		</p>

		<div class="flex gap-3">
			<button on:click={() => (showDeleteModal = false)}
				class="flex-1 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
				Cancel
			</button>
			<button on:click={handleDelete} disabled={deleteSubmitting}
				class="flex-1 py-2.5 bg-red-600 hover:bg-red-700 disabled:opacity-60 text-white text-sm font-semibold rounded-xl transition flex items-center justify-center gap-2">
				{#if deleteSubmitting}
					<span class="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
					Deleting…
				{:else}
					Delete
				{/if}
			</button>
		</div>
	</div>
</div>
{/if}
