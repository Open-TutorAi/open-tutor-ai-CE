<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import type { ClassroomOut } from '$lib/types/classroom';
	import EllipsisHorizontal from '$lib/components/icons/EllipsisHorizontal.svelte';
	import UsersSolid from '$lib/components/icons/UsersSolid.svelte';
	import Document from '$lib/components/icons/Document.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import DeleteClassroomModal from '$lib/components/DeleteClassroomModal.svelte';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	
	export let classroom: ClassroomOut;

	let menuOpen = false;
	let showDeleteModal = false;

	$: isOwner = Boolean($user && $user.id === classroom.owner_id);

	// Subject -> accent color. Approximated from the EduLearn mockup palette
	// (no mockup asset was available at implementation time); adjust freely.
	const SUBJECT_COLORS: Record<string, string> = {
		math: 'bg-blue-500',
		mathematics: 'bg-blue-500',
		science: 'bg-green-500',
		history: 'bg-amber-500',
		language: 'bg-purple-500',
		art: 'bg-pink-500'
	};
	const DEFAULT_COLOR = 'bg-slate-500';

	const iconColor = (subject?: string) =>
		(subject && SUBJECT_COLORS[subject.toLowerCase()]) || DEFAULT_COLOR;

	const badgeLabel = (c: ClassroomOut) => [c.level, c.subject].filter(Boolean).join(' · ');

	const formatDate = (dateString: string): string => {
		if (!dateString) return '';
		try {
			return new Intl.DateTimeFormat(navigator.language || 'en-US', {
				year: 'numeric',
				month: 'short',
				day: 'numeric'
			}).format(new Date(dateString));
		} catch {
			return dateString;
		}
	};

	const handleDeleted = (event: CustomEvent<string>) => {
		dispatch('deleted', event.detail);
	};
</script>

<div
	data-testid="classroom-card"
	data-classroom-id={classroom.id}
	class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden hover:shadow-md transition-shadow p-5"
>
	<div class="flex items-start justify-between mb-3">
		<div class="flex items-center gap-3 min-w-0">
			<div class="w-10 h-10 rounded-lg flex-shrink-0 {iconColor(classroom.subject)}"></div>
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate">
				{classroom.name}
			</h3>
		</div>

		<div class="relative flex-shrink-0">
			<button
				type="button"
				aria-label={$i18n.t('Classroom options')}
				class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
				on:click={() => (menuOpen = !menuOpen)}
			>
				<EllipsisHorizontal className="w-5 h-5" />
			</button>

			{#if menuOpen}
				<!-- svelte-ignore a11y-click-events-have-key-events -->
				<!-- svelte-ignore a11y-no-static-element-interactions -->
				<div class="fixed inset-0 z-0" on:click={() => (menuOpen = false)}></div>
				<div
					class="absolute right-0 mt-1 w-40 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-100 dark:border-gray-700 z-10"
				>
					<button
						type="button"
						class="flex items-center gap-2 w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
						on:click={() => {
							menuOpen = false;
							goto(`/classrooms/${classroom.id}`);
						}}
					>
						<Document className="w-4 h-4" />
						{$i18n.t('View Details')}
					</button>

					{#if isOwner}
						<button
							type="button"
							class="flex items-center gap-2 w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-50 dark:hover:bg-gray-700"
							on:click={() => {
								menuOpen = false;
								showDeleteModal = true;
							}}
						>
							<GarbageBin className="w-4 h-4" />
							{$i18n.t('Delete')}
						</button>
					{/if}
				</div>
			{/if}
		</div>
	</div>

	{#if badgeLabel(classroom)}
		<div
			data-testid="classroom-badge"
			class="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 mb-3"
		>
			{badgeLabel(classroom)}
		</div>
	{/if}

	<div class="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
		<div class="flex items-center gap-1">
			<UsersSolid className="w-4 h-4" />
			<span data-testid="student-count">
				{classroom.student_count}
				{$i18n.t('students')}
			</span>
		</div>

		<div class="flex items-center gap-1">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-4 w-4"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
				/>
			</svg>
			<span data-testid="classroom-date">{formatDate(classroom.created_at)}</span>
		</div>
	</div>
</div>

<DeleteClassroomModal
	bind:show={showDeleteModal}
	classroomId={classroom.id}
	classroomName={classroom.name}
	on:deleted={handleDeleted}
/>
