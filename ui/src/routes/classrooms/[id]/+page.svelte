<!-- src/routes/classrooms/[id]/+page.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import { toast } from 'svelte-sonner';
	import { ClassroomsAPI } from '$lib/apis/classrooms';
	import { SessionsAPI } from '$lib/apis/sessions';
	import { ForbiddenError } from '$lib/apis/errors';
	import type {
		ClassroomDetail,
		AttendanceStats,
		SessionSummary,
		SessionOut,
		PresenceOut,
		StudentHistory
	} from '$lib/types/classroom';
	import AttendanceKPICards from '$lib/components/attendance/AttendanceKPICards.svelte';
	import SessionList from '$lib/components/attendance/SessionList.svelte';
	import SessionDetail from '$lib/components/attendance/SessionDetail.svelte';
	import StudentHistoryPanel from '$lib/components/attendance/StudentHistoryPanel.svelte';
	import StudentsTab from '$lib/components/StudentsTab.svelte';
	import DeleteClassroomModal from '$lib/components/DeleteClassroomModal.svelte';
	import AnnouncementsFeed from '$lib/components/AnnouncementsFeed.svelte';
	import StartSessionModal from '$lib/components/StartSessionModal.svelte';
	import Pencil from '$lib/components/icons/Pencil.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import DocumentDuplicate from '$lib/components/icons/DocumentDuplicate.svelte';

	const i18n = getContext('i18n');

	const TABS = [
		'Overview',
		'Students',
		'Resources',
		'Présences',
		'Devoirs',
		'Rapports',
		'Paramètres'
	];

	$: classroomId = $page.params.id;

	let activeTab = 'Présences';
	let loading = true;
	let forbidden = false;
	let notFound = false;

	let classroom: ClassroomDetail | null = null;
	let stats: AttendanceStats | null = null;
	let sessions: SessionSummary[] = [];

	let selectedSessionId: string | null = null;
	let sessionPresences: PresenceOut[] = [];

	let selectedStudentId: string | null = null;
	let studentHistory: StudentHistory | null = null;

	$: selectedStudentName =
		sessionPresences.find((p) => p.student_id === selectedStudentId)?.student_name ?? '';

	let showDeleteModal = false;
	let showStartSessionModal = false;

	const token = () => localStorage.getItem('token') ?? '';

	const loadClassroom = async () => {
		loading = true;
		forbidden = false;
		notFound = false;
		try {
			const [detail, attendanceStats, sessionList] = await Promise.all([
				ClassroomsAPI.getDetail(token(), classroomId),
				SessionsAPI.getStats(token(), classroomId),
				SessionsAPI.getSessions(token(), classroomId)
			]);
			classroom = detail;
			stats = attendanceStats;
			sessions = sessionList;
		} catch (err) {
			if (err instanceof ForbiddenError) {
				forbidden = true;
			} else {
				notFound = true;
			}
		} finally {
			loading = false;
		}
	};

	onMount(() => {
		if (!browser) return;
		loadClassroom();
	});

	const selectSession = async (event: CustomEvent<string>) => {
		selectedSessionId = event.detail;
		selectedStudentId = null;
		studentHistory = null;
		sessionPresences = await SessionsAPI.getPresences(token(), selectedSessionId);
	};

	const selectStudent = async (event: CustomEvent<string>) => {
		selectedStudentId = event.detail;
		studentHistory = await SessionsAPI.getStudentHistory(token(), classroomId, selectedStudentId);
	};

	const onSessionStarted = async (event: CustomEvent<SessionOut>) => {
		sessions = await SessionsAPI.getSessions(token(), classroomId);
		selectedSessionId = event.detail.id;
		selectedStudentId = null;
		studentHistory = null;
		sessionPresences = await SessionsAPI.getPresences(token(), selectedSessionId);
	};

	const endSession = async (event: CustomEvent<string>) => {
		await SessionsAPI.endSession(token(), event.detail);
		sessions = await SessionsAPI.getSessions(token(), classroomId);
		if (selectedSessionId === event.detail) {
			sessionPresences = await SessionsAPI.getPresences(token(), selectedSessionId);
		}
	};

	const deleteSession = async (event: CustomEvent<string>) => {
		try {
			await SessionsAPI.deleteSession(token(), event.detail);
			sessions = await SessionsAPI.getSessions(token(), classroomId);
			if (selectedSessionId === event.detail) {
				selectedSessionId = null;
				sessionPresences = [];
				selectedStudentId = null;
				studentHistory = null;
			}
			toast.success($i18n.t('Session deleted'));
		} catch (err: any) {
			toast.error(err?.detail || $i18n.t('Failed to delete session'));
		}
	};

	const handleDeleted = () => {
		goto('/classrooms');
	};
</script>

{#if forbidden}
	<div class="flex items-center justify-center py-24">
		<p class="text-lg font-medium text-red-600">{$i18n.t('Accès non autorisé')}</p>
	</div>
{:else if loading}
	<div class="flex items-center justify-center py-24">
		<div class="animate-pulse text-gray-500 dark:text-gray-400">{$i18n.t('Loading...')}</div>
	</div>
{:else if notFound || !classroom}
	<div class="flex items-center justify-center py-24">
		<p class="text-lg font-medium text-gray-600 dark:text-gray-400">
			{$i18n.t('Classroom not found')}
		</p>
	</div>
{:else}
	<div class="max-w-6xl mx-auto">
		<button
			type="button"
			on:click={() => goto('/classrooms')}
			class="inline-flex items-center text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 mb-4"
		>
			&larr; {$i18n.t('My Classrooms')}
		</button>

		<div class="flex items-center justify-between mb-6">
			<div class="flex items-center gap-3">
				<h1 class="text-2xl font-bold text-gray-900 dark:text-white">{classroom.name}</h1>
				{#if classroom.level}
					<span
						class="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
					>
						{classroom.level}
					</span>
				{/if}
			</div>
			<div class="flex items-center gap-2">
				<button
					type="button"
					on:click={() => goto(`/classrooms/${classroomId}/edit`)}
					class="inline-flex items-center gap-1.5 px-4 py-2 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
				>
					<Pencil className="w-4 h-4" />
					{$i18n.t('Edit')}
				</button>
				<button
					type="button"
					on:click={() => (showDeleteModal = true)}
					class="inline-flex items-center gap-1.5 px-4 py-2 text-red-600 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
				>
					<GarbageBin className="w-4 h-4" />
					{$i18n.t('Delete')}
				</button>
			</div>
		</div>

		{#if classroom.join_code}
			<div
				data-testid="join-code-banner"
				class="flex items-center justify-between gap-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-lg px-4 py-2.5 mb-6"
			>
				<div class="flex items-center gap-2 text-sm">
					<span class="text-blue-700 dark:text-blue-300">{$i18n.t('Class code')}:</span>
					<span class="font-mono font-semibold text-blue-900 dark:text-blue-100 tracking-wide"
						>{classroom.join_code}</span
					>
				</div>
				<button
					type="button"
					data-testid="copy-join-code-button"
					title={$i18n.t('Copy')}
					aria-label={$i18n.t('Copy')}
					on:click={() => {
						if (classroom?.join_code) {
							navigator.clipboard?.writeText(classroom.join_code);
							toast.success($i18n.t('Code copied!'));
						}
					}}
					class="p-1.5 rounded-full text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
				>
					<DocumentDuplicate className="w-4 h-4" />
				</button>
			</div>
		{/if}

		<div
			class="flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-6 overflow-x-auto"
			role="tablist"
		>
			{#each TABS as tab}
				<button
					type="button"
					role="tab"
					aria-selected={activeTab === tab}
					on:click={() => (activeTab = tab)}
					class="px-4 py-2 text-sm font-medium border-b-2 whitespace-nowrap {activeTab === tab
						? 'border-blue-600 text-blue-600'
						: 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
				>
					{$i18n.t(tab)}
				</button>
			{/each}
		</div>

		{#if activeTab === 'Overview'}
			<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
				<div class="lg:col-span-2 space-y-6">
					<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
						<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
							{$i18n.t('Announcements')}
						</h2>
						<AnnouncementsFeed {classroomId} canPost={true} />
					</div>

					<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 space-y-4">
						<div>
							<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
								{$i18n.t('Description')}
							</h2>
							<p class="text-sm text-gray-600 dark:text-gray-400">
								{classroom.description || $i18n.t('No description yet.')}
							</p>
						</div>

						{#if classroom.course}
							<div>
								<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
									{$i18n.t('Course')}
								</h2>
								<p class="text-sm text-gray-600 dark:text-gray-400">{classroom.course}</p>
							</div>
						{/if}

						<div>
							<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
								{$i18n.t('Learning Objectives')}
							</h2>
							{#if classroom.objectives_list.length > 0}
								<ul
									class="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 space-y-1"
								>
									{#each classroom.objectives_list as objective}
										<li>{objective}</li>
									{/each}
								</ul>
							{:else}
								<p class="text-sm text-gray-500 dark:text-gray-400">
									{$i18n.t('No objectives set yet.')}
								</p>
							{/if}
						</div>
					</div>
				</div>

				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 space-y-3">
					<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300">
						{$i18n.t('Quick Actions')}
					</h2>
					<button
						type="button"
						on:click={() => (activeTab = 'Présences')}
						class="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
					>
						{$i18n.t('View Attendance')} &rarr;
					</button>
					<button
						type="button"
						on:click={() => (activeTab = 'Students')}
						class="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
					>
						{$i18n.t('Manage Students')} ({classroom.student_count}) &rarr;
					</button>
					<button
						type="button"
						on:click={() => goto(`/classrooms/${classroomId}/edit`)}
						class="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
					>
						{$i18n.t('Edit Classroom Details')} &rarr;
					</button>
				</div>
			</div>
		{:else if activeTab === 'Présences'}
			<div class="space-y-6">
				{#if stats}
					<AttendanceKPICards {stats} />
				{/if}

				<div class="flex justify-end">
					<button
						type="button"
						on:click={() => (showStartSessionModal = true)}
						class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
					>
						{$i18n.t('Démarrer une séance')}
					</button>
				</div>

				<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
					<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
						<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
							{$i18n.t('Sessions')}
						</h2>
						<SessionList
							{sessions}
							selectedId={selectedSessionId}
							on:select={selectSession}
							on:end={endSession}
							on:delete={deleteSession}
						/>
					</div>

					<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 space-y-6">
						{#if selectedSessionId}
							<div>
								<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
									{$i18n.t('Student Attendance')}
								</h2>
								<SessionDetail presences={sessionPresences} on:selectStudent={selectStudent} />
							</div>
						{/if}

						{#if studentHistory}
							<div>
								<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
									{$i18n.t('Student History')}
								</h2>
								<StudentHistoryPanel history={studentHistory} studentName={selectedStudentName} />
							</div>
						{/if}
					</div>
				</div>
			</div>
		{:else if activeTab === 'Students'}
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
				<StudentsTab />
			</div>
		{:else}
			<div
				class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center text-gray-500 dark:text-gray-400"
			>
				{$i18n.t('Coming soon')}
			</div>
		{/if}
	</div>

	<DeleteClassroomModal
		bind:show={showDeleteModal}
		classroomId={classroom.id}
		classroomName={classroom.name}
		on:deleted={handleDeleted}
	/>

	<StartSessionModal
		bind:show={showStartSessionModal}
		{classroomId}
		defaultSubject={classroom.subject ?? ''}
		on:started={onSessionStarted}
	/>
{/if}
