
<!-- src/lib/components/AnnouncementsFeed.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { toast } from 'svelte-sonner';
	import { AnnouncementsAPI } from '$lib/apis/announcements';
	import type { AnnouncementOut } from '$lib/types/classroom';
	import StudentAvatar from '$lib/components/StudentAvatar.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';

	const i18n = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';

	export let classroomId: string;
	export let canPost = false;

	let announcements: AnnouncementOut[] = [];
	let loading = true;
	let error = '';
	let content = '';
	let posting = false;

	const load = async () => {
		loading = true;
		error = '';
		try {
			announcements = await AnnouncementsAPI.list(token(), classroomId);
		} catch (err: any) {
			error = err?.detail || $i18n.t('Failed to load announcements');
		} finally {
			loading = false;
		}
	};

	onMount(load);

	const post = async () => {
		if (!content.trim() || posting) return;
		posting = true;
		try {
			const created = await AnnouncementsAPI.create(token(), classroomId, content.trim());
			announcements = [created, ...announcements];
			content = '';
		} catch (err: any) {
			toast.error(err?.detail || $i18n.t('Failed to post announcement'));
		} finally {
			posting = false;
		}
	};

	const remove = async (id: string) => {
		try {
			await AnnouncementsAPI.delete(token(), id);
			announcements = announcements.filter((a) => a.id !== id);
		} catch (err: any) {
			toast.error(err?.detail || $i18n.t('Failed to delete announcement'));
		}
	};

	const relativeTime = (iso: string) => {
		const diffMs = Date.now() - new Date(iso).getTime();
		const minutes = Math.floor(diffMs / 60000);
		if (minutes < 1) return $i18n.t('just now');
		if (minutes < 60) return `${minutes} ${$i18n.t('min ago')}`;
		const hours = Math.floor(minutes / 60);
		if (hours < 24) return `${hours} ${$i18n.t('h ago')}`;
		const days = Math.floor(hours / 24);
		return `${days} ${$i18n.t('d ago')}`;
	};
</script>

<div data-testid="announcements-feed" class="space-y-4">
	{#if canPost}
		<div class="flex gap-2">
			<textarea
				bind:value={content}
				placeholder={$i18n.t('Share an announcement with your class...')}
				rows="2"
				disabled={posting}
				class="flex-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
			></textarea>
			<button
				type="button"
				data-testid="post-announcement-button"
				on:click={post}
				disabled={!content.trim() || posting}
				class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium self-start whitespace-nowrap"
			>
				{posting ? $i18n.t('Posting...') : $i18n.t('Post')}
			</button>
		</div>
	{/if}

	{#if loading}
		<div class="space-y-2" aria-hidden="true">
			{#each Array(2) as _}
				<div class="h-14 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse"></div>
			{/each}
		</div>
	{:else if error}
		<p class="text-sm text-red-600 dark:text-red-400">{error}</p>
	{:else if announcements.length === 0}
		<p class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
			{$i18n.t('No announcements yet.')}
		</p>
	{:else}
		<div class="space-y-3">
			{#each announcements as announcement (announcement.id)}
				<div
					in:fade={{ duration: 150 }}
					data-testid="announcement-item"
					class="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-900/40"
				>
					<StudentAvatar name={announcement.author_name || '?'} size="sm" />
					<div class="flex-1 min-w-0">
						<div class="flex items-center gap-2 text-sm">
							<span class="font-medium text-gray-900 dark:text-white"
								>{announcement.author_name}</span
							>
							<span class="text-xs text-gray-400 dark:text-gray-500"
								>{relativeTime(announcement.created_at)}</span
							>
						</div>
						<p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
							{announcement.content}
						</p>
					</div>
					{#if canPost}
						<button
							type="button"
							data-testid="delete-announcement-button"
							title={$i18n.t('Delete')}
							aria-label={$i18n.t('Delete announcement')}
							on:click={() => remove(announcement.id)}
							class="p-1.5 rounded-full text-gray-400 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 flex-shrink-0 transition-colors"
						>
							<GarbageBin className="w-4 h-4" />
						</button>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
