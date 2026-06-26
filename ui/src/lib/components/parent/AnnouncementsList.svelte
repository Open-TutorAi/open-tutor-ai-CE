<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { getPublishedAnnouncements, markAnnouncementRead, getUnreadCount } from '$lib/apis/announcements';
	import type { Announcement } from '$lib/apis/announcements';

	let announcements: Announcement[] = [];
	let loading = true;
	let error: string | null = null;
	let expanded: string | null = null;
	let pollInterval: ReturnType<typeof setInterval> | null = null;

	$: unreadCount = announcements.filter((a) => !a.is_read).length;

	const load = async () => {
		try {
			announcements = await getPublishedAnnouncements(localStorage.token);
		} catch (e: any) {
			error = String(e);
		} finally {
			loading = false;
		}
	};

	const toggle = async (ann: Announcement) => {
		if (expanded === ann.id) {
			expanded = null;
			return;
		}
		expanded = ann.id;
		if (!ann.is_read) {
			try {
				const updated = await markAnnouncementRead(localStorage.token, ann.id);
				announcements = announcements.map((a) => (a.id === ann.id ? updated : a));
			} catch (_) {}
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

	const urgentBorder = (p: string) => {
		if (p === 'urgent') return 'border-l-4 border-red-500';
		if (p === 'important') return 'border-l-4 border-amber-400';
		return '';
	};

	onMount(async () => {
		await load();
		pollInterval = setInterval(load, 30000);
	});

	onDestroy(() => {
		if (pollInterval) clearInterval(pollInterval);
	});
</script>

<div class="bg-white dark:bg-gray-850 rounded-xl border border-gray-100 dark:border-gray-800 h-full flex flex-col">
	<!-- Header -->
	<div class="flex items-center gap-2 px-5 py-4 border-b border-gray-100 dark:border-gray-800">
		<span class="grid place-items-center w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 text-white">
			<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
			</svg>
		</span>
		<h2 class="font-semibold text-gray-900 dark:text-white">Annonces</h2>
		{#if unreadCount > 0}
			<span class="text-[11px] font-semibold bg-red-500 text-white rounded-full px-2 py-0.5">{unreadCount} non lu{unreadCount > 1 ? 'es' : 'e'}</span>
		{/if}
	</div>

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
				<p class="text-sm text-gray-500 dark:text-gray-400">Vos enseignants n'ont pas encore publié d'annonces.</p>
			</div>
		{:else}
			<ul class="divide-y divide-gray-100 dark:divide-gray-800">
				{#each announcements as ann (ann.id)}
					<li
						class="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-900 transition {urgentBorder(ann.priority)}"
						on:click={() => toggle(ann)}
						on:keydown={(e) => e.key === 'Enter' && toggle(ann)}
						role="button"
						tabindex="0"
					>
						<div class="px-5 py-4">
							<div class="flex items-start gap-3">
								<!-- Unread dot -->
								<span class="mt-1.5 w-2 h-2 rounded-full flex-shrink-0 {ann.is_read ? 'bg-transparent' : 'bg-blue-500'}"></span>
								<div class="flex-1 min-w-0">
									<div class="flex items-center gap-2 flex-wrap mb-1">
										<p class="font-semibold text-sm {ann.is_read ? 'text-gray-700 dark:text-gray-300' : 'text-gray-900 dark:text-white'} truncate">
											{ann.title}
										</p>
										{#if ann.priority !== 'normal'}
											<span class="text-[11px] font-medium px-2 py-0.5 rounded-lg {priorityBadge(ann.priority)}">{priorityLabel(ann.priority)}</span>
										{/if}
									</div>
									{#if expanded !== ann.id}
										<p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">{ann.content}</p>
									{:else}
										<p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{ann.content}</p>
									{/if}
									<p class="text-[11px] text-gray-400 dark:text-gray-500 mt-1">
										{new Date(ann.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })}
									</p>
								</div>
								<svg
									class="w-4 h-4 text-gray-400 flex-shrink-0 transition-transform {expanded === ann.id ? 'rotate-180' : ''}"
									fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
								>
									<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
								</svg>
							</div>
						</div>
					</li>
				{/each}
			</ul>
		{/if}
	</div>
</div>
