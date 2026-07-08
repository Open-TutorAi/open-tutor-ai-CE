<!-- Classrooms.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { browser } from '$app/environment';
	import { toast } from 'svelte-sonner';
	import { ClassroomsAPI } from '$lib/apis/classrooms';
	import { SessionsAPI } from '$lib/apis/sessions';
	import type { EnrolledClassroomOut } from '$lib/types/classroom';
	import AnnouncementsFeed from '$lib/components/AnnouncementsFeed.svelte';

	const i18n = getContext('i18n');

	let classrooms: EnrolledClassroomOut[] = [];
	let loading = true;
	let error = '';
	let joiningId: string | null = null;
	let joinedSessionIds = new Set<string>();
	let expandedAnnouncementsId: string | null = null;

	let inviteCode = '';
	let redeeming = false;

	const token = () => localStorage.getItem('token') ?? '';

	const SUBJECT_COLORS: Record<string, string> = {
		math: 'bg-blue-500',
		mathematics: 'bg-blue-500',
		science: 'bg-green-500',
		history: 'bg-amber-500',
		language: 'bg-purple-500',
		art: 'bg-pink-500'
	};
	const iconColor = (subject?: string) =>
		(subject && SUBJECT_COLORS[subject.toLowerCase()]) || 'bg-slate-500';

	const load = async () => {
		loading = true;
		error = '';
		try {
			classrooms = await ClassroomsAPI.listEnrolled(token());
		} catch (err: any) {
			error = err?.detail || $i18n.t('Failed to load classrooms');
		} finally {
			loading = false;
		}
	};

	onMount(() => {
		if (!browser) return;
		load();
	});

	const redeemCode = async () => {
		if (!inviteCode.trim() || redeeming) return;
		redeeming = true;
		try {
			const result = await ClassroomsAPI.redeemInvite(token(), inviteCode.trim());
			inviteCode = '';
			toast.success(
				result.enrolled
					? $i18n.t('You joined the classroom!')
					: $i18n.t("You're already enrolled in this classroom.")
			);
			load();
		} catch (err: any) {
			toast.error(err?.detail || $i18n.t('Invalid or expired course code'));
		} finally {
			redeeming = false;
		}
	};

	const joinSession = async (classroom: EnrolledClassroomOut) => {
		if (!classroom.active_session_id || joiningId) return;
		const sessionId = classroom.active_session_id;
		joiningId = classroom.id;
		try {
			await SessionsAPI.joinSession(token(), sessionId);
			joinedSessionIds = new Set(joinedSessionIds).add(sessionId);
			toast.success($i18n.t('You are marked present for this session.'));
		} catch (err: any) {
			toast.error(err?.detail || $i18n.t('Could not join the session. It may have ended.'));
		} finally {
			joiningId = null;
			load();
		}
	};
</script>

<div class="mb-6">
	<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1">
		{$i18n.t('My Classrooms')}
	</h2>
	<p class="text-sm text-gray-500 dark:text-gray-400">
		{$i18n.t('Classrooms you are enrolled in')}
	</p>
</div>

<div
	class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4 mb-6"
>
	<label
		for="invite-code-input"
		class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
	>
		{$i18n.t('Join a classroom with a code')}
	</label>
	<div class="flex gap-2">
		<input
			id="invite-code-input"
			type="text"
			bind:value={inviteCode}
			placeholder={$i18n.t('Enter course code')}
			disabled={redeeming}
			on:keydown={(e) => e.key === 'Enter' && redeemCode()}
			class="flex-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
		/>
		<button
			type="button"
			data-testid="redeem-code-button"
			on:click={redeemCode}
			disabled={!inviteCode.trim() || redeeming}
			class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium whitespace-nowrap"
		>
			{redeeming ? $i18n.t('Joining...') : $i18n.t('Join')}
		</button>
	</div>
</div>

{#if loading}
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" aria-busy="true">
		{#each Array(3) as _}
			<div
				class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-5 space-y-3 animate-pulse"
			>
				<div class="flex items-center gap-3">
					<div class="w-10 h-10 rounded-lg bg-gray-200 dark:bg-gray-700"></div>
					<div class="h-4 w-2/3 rounded bg-gray-200 dark:bg-gray-700"></div>
				</div>
				<div class="h-3 w-1/3 rounded bg-gray-200 dark:bg-gray-700"></div>
				<div class="h-9 rounded-lg bg-gray-100 dark:bg-gray-700"></div>
			</div>
		{/each}
	</div>
{:else if error}
	<div
		class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-sm text-red-700 dark:text-red-300"
	>
		{error}
	</div>
{:else if classrooms.length === 0}
	<div
		class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center text-gray-500 dark:text-gray-400"
	>
		{$i18n.t("You're not enrolled in any classroom yet. Ask your teacher for a course code.")}
	</div>
{:else}
	<div
		data-testid="enrolled-classrooms-list"
		class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
	>
		{#each classrooms as classroom (classroom.id)}
			<div
				in:fade={{ duration: 150 }}
				data-testid="enrolled-classroom-card"
				data-classroom-id={classroom.id}
				class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border p-5 space-y-3 transition-shadow hover:shadow-md {classroom.active_session_id
					? 'border-green-200 dark:border-green-900/40'
					: 'border-gray-100 dark:border-gray-700'}"
			>
				<div class="flex items-start justify-between gap-2">
					<div class="flex items-center gap-3 min-w-0">
						<div class="w-10 h-10 rounded-lg flex-shrink-0 {iconColor(classroom.subject)}"></div>
						<h3 class="font-semibold text-gray-900 dark:text-white truncate">{classroom.name}</h3>
					</div>
					{#if classroom.active_session_id}
						<span
							data-testid="live-badge"
							class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 whitespace-nowrap"
						>
							<span class="relative flex w-1.5 h-1.5">
								<span
									class="absolute inline-flex w-full h-full rounded-full bg-green-500 opacity-75 animate-ping"
								></span>
								<span class="relative inline-flex w-1.5 h-1.5 rounded-full bg-green-500"></span>
							</span>
							{$i18n.t('Live')}
						</span>
					{/if}
				</div>

				{#if classroom.subject}
					<p class="text-sm text-gray-500 dark:text-gray-400">{classroom.subject}</p>
				{/if}

				{#if classroom.active_session_id && joinedSessionIds.has(classroom.active_session_id)}
					<button
						type="button"
						disabled
						in:fade={{ duration: 200 }}
						data-testid="joined-indicator"
						class="w-full px-4 py-2 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-lg text-sm font-medium cursor-default"
					>
						{$i18n.t('You are present ✓')}
					</button>
				{:else if classroom.active_session_id}
					<button
						type="button"
						data-testid="join-session-button"
						on:click={() => joinSession(classroom)}
						disabled={joiningId === classroom.id}
						class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 active:scale-[0.98] transition-transform disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
					>
						{joiningId === classroom.id ? $i18n.t('Joining...') : $i18n.t('Join Session')}
					</button>
				{:else}
					<p class="text-xs text-gray-400 dark:text-gray-500">
						{$i18n.t('No live session right now')}
					</p>
				{/if}

				<button
					type="button"
					data-testid="toggle-announcements-button"
					on:click={() =>
						(expandedAnnouncementsId =
							expandedAnnouncementsId === classroom.id ? null : classroom.id)}
					class="text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
				>
					{expandedAnnouncementsId === classroom.id
						? $i18n.t('Hide announcements')
						: $i18n.t('View announcements')}
				</button>

				{#if expandedAnnouncementsId === classroom.id}
					<div
						transition:fade={{ duration: 150 }}
						class="pt-2 border-t border-gray-100 dark:border-gray-700"
					>
						<AnnouncementsFeed classroomId={classroom.id} canPost={false} />
					</div>
				{/if}
			</div>
		{/each}
	</div>
{/if}
