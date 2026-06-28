<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getMyAnnouncements,
		createAnnouncement,
		updateAnnouncement,
		publishAnnouncement,
		unpublishAnnouncement,
		deleteAnnouncement
	} from '$lib/apis/announcements';
	import type { Announcement } from '$lib/apis/announcements';

	let announcements: Announcement[] = [];
	let loading = true;
	let error: string | null = null;

	// Form state
	let showForm = false;
	let editingId: string | null = null;
	let formTitle = '';
	let formContent = '';
	let formPriority: 'normal' | 'important' | 'urgent' = 'normal';
	let formLoading = false;
	let formError: string | null = null;

	const load = async () => {
		loading = true;
		error = null;
		try {
			announcements = await getMyAnnouncements(localStorage.token);
		} catch (e: any) {
			error = String(e);
		} finally {
			loading = false;
		}
	};

	const openCreate = () => {
		editingId = null;
		formTitle = '';
		formContent = '';
		formPriority = 'normal';
		formError = null;
		showForm = true;
	};

	const openEdit = (ann: Announcement) => {
		editingId = ann.id;
		formTitle = ann.title;
		formContent = ann.content;
		formPriority = ann.priority;
		formError = null;
		showForm = true;
	};

	const cancelForm = () => {
		showForm = false;
		editingId = null;
		formError = null;
	};

	const submitForm = async () => {
		if (!formTitle.trim() || !formContent.trim()) {
			formError = 'Le titre et le contenu sont obligatoires.';
			return;
		}
		formLoading = true;
		formError = null;
		try {
			if (editingId) {
				const updated = await updateAnnouncement(localStorage.token, editingId, {
					title: formTitle,
					content: formContent,
					priority: formPriority
				});
				announcements = announcements.map((a) => (a.id === editingId ? updated : a));
			} else {
				const created = await createAnnouncement(
					localStorage.token,
					formTitle,
					formContent,
					formPriority
				);
				announcements = [created, ...announcements];
			}
			cancelForm();
		} catch (e: any) {
			formError = String(e);
		} finally {
			formLoading = false;
		}
	};

	const togglePublish = async (ann: Announcement) => {
		try {
			const updated = ann.is_published
				? await unpublishAnnouncement(localStorage.token, ann.id)
				: await publishAnnouncement(localStorage.token, ann.id);
			announcements = announcements.map((a) => (a.id === ann.id ? updated : a));
		} catch (e: any) {
			error = String(e);
		}
	};

	const handleDelete = async (ann: Announcement) => {
		if (!confirm(`Supprimer l'annonce "${ann.title}" ?`)) return;
		try {
			await deleteAnnouncement(localStorage.token, ann.id);
			announcements = announcements.filter((a) => a.id !== ann.id);
		} catch (e: any) {
			error = String(e);
		}
	};

	const priorityBadge = (p: string) => {
		if (p === 'urgent') return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
		if (p === 'important') return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400';
		return 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400';
	};

	const priorityLabel = (p: string) => {
		if (p === 'urgent') return 'Urgent';
		if (p === 'important') return 'Important';
		return 'Normal';
	};

	onMount(load);
</script>

<div class="bg-white dark:bg-gray-850 rounded-xl border border-gray-100 dark:border-gray-800 h-full flex flex-col">
	<!-- Header -->
	<div class="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-800">
		<div class="flex items-center gap-2">
			<span class="grid place-items-center w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 text-white">
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
				</svg>
			</span>
			<h2 class="font-semibold text-gray-900 dark:text-white">Annonces</h2>
			<span class="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-900 rounded-lg px-2 py-0.5">{announcements.length}</span>
		</div>
		<button
			on:click={openCreate}
			class="flex items-center gap-1.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:opacity-90 text-white text-sm font-medium rounded-lg px-4 py-2 transition"
		>
			<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
				<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
			</svg>
			Nouvelle annonce
		</button>
	</div>

	<!-- Create / Edit form -->
	{#if showForm}
		<div class="px-5 py-4 border-b border-blue-100 dark:border-blue-900/40 bg-blue-50 dark:bg-blue-900/10">
			<h3 class="font-medium text-gray-900 dark:text-white mb-3 text-sm">
				{editingId ? 'Modifier l\'annonce' : 'Nouvelle annonce'}
			</h3>
			{#if formError}
				<p class="text-xs text-red-600 dark:text-red-400 mb-2">{formError}</p>
			{/if}
			<input
				bind:value={formTitle}
				placeholder="Titre *"
				class="w-full mb-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300"
			/>
			<textarea
				bind:value={formContent}
				placeholder="Contenu *"
				rows="4"
				class="w-full mb-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
			></textarea>
			<div class="flex items-center gap-3 mb-3">
				<label class="text-xs font-medium text-gray-600 dark:text-gray-400">Priorité :</label>
				{#each ['normal', 'important', 'urgent'] as p}
					<label class="flex items-center gap-1 cursor-pointer">
						<input type="radio" bind:group={formPriority} value={p} class="accent-blue-600" />
						<span class="text-xs capitalize text-gray-700 dark:text-gray-300">{priorityLabel(p)}</span>
					</label>
				{/each}
			</div>
			<div class="flex items-center gap-2">
				<button
					on:click={submitForm}
					disabled={formLoading}
					class="bg-gradient-to-r from-blue-500 to-blue-600 hover:opacity-90 disabled:opacity-50 text-white text-sm font-medium rounded-lg px-5 py-2 transition"
				>
					{formLoading ? 'Enregistrement…' : editingId ? 'Mettre à jour' : 'Créer'}
				</button>
				<button
					on:click={cancelForm}
					class="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition px-3 py-2"
				>
					Annuler
				</button>
			</div>
		</div>
	{/if}

	<!-- List -->
	<div class="flex-1 overflow-y-auto">
		{#if loading}
			<div class="flex items-center justify-center h-32">
				<div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
			</div>
		{:else if error}
			<div class="p-5 text-sm text-red-600 dark:text-red-400">{error}</div>
		{:else if announcements.length === 0}
			<div class="flex flex-col items-center justify-center py-16 text-center px-4">
				<svg class="w-10 h-10 text-indigo-400 dark:text-indigo-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
				</svg>
				<p class="text-sm font-medium text-gray-800 dark:text-white mb-1">Aucune annonce</p>
				<p class="text-sm text-gray-500 dark:text-gray-400">Créez votre première annonce pour vos parents.</p>
			</div>
		{:else}
			<ul class="divide-y divide-gray-100 dark:divide-gray-800">
				{#each announcements as ann (ann.id)}
					<li class="px-5 py-4 hover:bg-gray-50 dark:hover:bg-gray-900 transition group">
						<div class="flex items-start gap-3">
							<div class="flex-1 min-w-0">
								<div class="flex items-center gap-2 flex-wrap mb-1">
									<p class="font-semibold text-gray-900 dark:text-white text-sm truncate">{ann.title}</p>
									<span class="text-[11px] font-medium px-2 py-0.5 rounded-lg {priorityBadge(ann.priority)}">{priorityLabel(ann.priority)}</span>
									{#if ann.is_published}
										<span class="text-[11px] font-medium px-2 py-0.5 rounded-lg bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Publiée</span>
									{:else}
										<span class="text-[11px] font-medium px-2 py-0.5 rounded-lg bg-gray-100 text-gray-500 dark:bg-gray-900 dark:text-gray-400">Brouillon</span>
									{/if}
								</div>
								<p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">{ann.content}</p>
								<p class="text-[11px] text-gray-400 dark:text-gray-500 mt-1">
									{new Date(ann.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })}
								</p>
							</div>
							<div class="flex items-center gap-1.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition">
								{#if !ann.is_published}
									<button
										on:click={() => openEdit(ann)}
										class="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition"
										title="Modifier"
									>
										<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
										</svg>
									</button>
								{/if}
								<button
									on:click={() => togglePublish(ann)}
									class="p-1.5 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition"
									title={ann.is_published ? 'Dépublier' : 'Publier'}
								>
									{#if ann.is_published}
										<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
										</svg>
									{:else}
										<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
											<path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
										</svg>
									{/if}
								</button>
								<button
									on:click={() => handleDelete(ann)}
									class="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition"
									title="Supprimer"
								>
									<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
								</button>
							</div>
						</div>
					</li>
				{/each}
			</ul>
		{/if}
	</div>
</div>
