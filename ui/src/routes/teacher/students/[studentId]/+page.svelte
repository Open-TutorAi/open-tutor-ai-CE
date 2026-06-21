<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import {
		getStudentGuardians,
		inviteGuardian,
		resendInvitation,
		type Guardian,
		type GuardianRelationship
	} from '$lib/apis/guardians';

	const i18n = getContext('i18n');

	type Tab = 'overview' | 'progress' | 'assignments' | 'messages' | 'guardians';

	interface StudentDetail {
		id: string;
		name: string;
		email: string;
		status: 'active' | 'inactive';
		enrolledAt: string;
		studentCode: string;
		classroom: string;
		classroomId: string;
		course: string;
	}

	$: studentId = $page.params.studentId;

	let activeTab: Tab = 'guardians';
	let student: StudentDetail | null = null;
	let guardians: Guardian[] = [];
	let loadingStudent = true;
	let loadingGuardians = false;

	// Invite form
	let inviteEmail = '';
	let inviteRelationship: GuardianRelationship | '' = '';
	let inviteEmailError = '';
	let inviteRelationshipError = '';
	let submitting = false;

	// Contact modal
	let showContactModal = false;
	let contactGuardian: Guardian | null = null;

	// Invite modal
	let showInviteModal = false;

	function openInviteModal() {
		inviteEmail = '';
		inviteRelationship = '';
		inviteEmailError = '';
		inviteRelationshipError = '';
		showInviteModal = true;
	}

	// ── Mock data ─────────────────────────────────────────────────────────────
	const MOCK_STUDENTS: Record<string, StudentDetail> = {
		'stu-1': { id: 'stu-1', name: 'Alex Johnson',  email: 'alex.johnson@email.com',  status: 'active',   enrolledAt: '2024-05-12', studentCode: 'STU-2024-001', classroom: 'Learn Python Basics for Beginners', classroomId: 'cls-1', course: 'Computer Science • High School' },
		'stu-2': { id: 'stu-2', name: 'Sarah Miller',  email: 'sarah.miller@email.com',  status: 'active',   enrolledAt: '2024-05-12', studentCode: 'STU-2024-002', classroom: 'Learn Python Basics for Beginners', classroomId: 'cls-1', course: 'Computer Science • High School' },
		'stu-3': { id: 'stu-3', name: 'Emma Williams', email: 'emma.williams@email.com', status: 'inactive', enrolledAt: '2024-05-14', studentCode: 'STU-2024-003', classroom: 'Learn Python Basics for Beginners', classroomId: 'cls-1', course: 'Computer Science • High School' },
		'stu-4': { id: 'stu-4', name: 'Lucas Brown',   email: 'lucas.brown@email.com',   status: 'active',   enrolledAt: '2024-09-01', studentCode: 'STU-2024-004', classroom: 'Advanced Mathematics',              classroomId: 'cls-2', course: 'Mathematics • High School' },
		'stu-5': { id: 'stu-5', name: 'Mia Davis',     email: 'mia.davis@email.com',     status: 'inactive', enrolledAt: '2024-09-01', studentCode: 'STU-2024-005', classroom: 'Advanced Mathematics',              classroomId: 'cls-2', course: 'Mathematics • High School' },
		'stu-6': { id: 'stu-6', name: 'Noah Wilson',   email: 'noah.wilson@email.com',   status: 'active',   enrolledAt: '2024-09-15', studentCode: 'STU-2024-006', classroom: 'Introduction to Biology',           classroomId: 'cls-3', course: 'Biology • Middle School' },
	};

	const MOCK_GUARDIANS: Record<string, Guardian[]> = {
		'stu-1': [
			{ id: 'g-1', student_id: 'stu-1', name: 'Sarah Johnson',  email: 'sarah.phil@gmail.com',   relationship: 'Mother',   status: 'active',  linked_at: '2024-05-12' },
			{ id: 'g-2', student_id: 'stu-1', name: 'Mark Johnson',   email: 'mark.johnson@gmail.com',  relationship: 'Father',   status: 'active',  linked_at: '2024-05-12' },
			{ id: 'g-3', student_id: 'stu-1', name: 'Emily Williams', email: 'emma.williams@gmail.com', relationship: 'Guardian', status: 'pending', linked_at: null },
		],
		'stu-2': [
			{ id: 'g-4', student_id: 'stu-2', name: 'Anna Miller', email: 'anna.miller@gmail.com', relationship: 'Mother', status: 'active', linked_at: '2024-05-20' },
		],
	};

	onMount(async () => {
		student = MOCK_STUDENTS[studentId] ?? null;
		if (!student) { toast.error($i18n.t('Student not found')); goto('/teacher/classrooms'); return; }
		loadingStudent = false;
		await loadGuardians();
	});

	async function loadGuardians() {
		loadingGuardians = true;
		try {
			guardians = await getStudentGuardians(localStorage.token, studentId).catch(
				() => MOCK_GUARDIANS[studentId] ?? []
			);
		} finally {
			loadingGuardians = false;
		}
	}

	async function switchTab(tab: Tab) {
		activeTab = tab;
		if (tab === 'guardians' && guardians.length === 0) await loadGuardians();
	}

	function validateInvite(): boolean {
		inviteEmailError = '';
		inviteRelationshipError = '';
		let ok = true;
		if (!inviteEmail.trim()) { inviteEmailError = $i18n.t('Email is required'); ok = false; }
		else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inviteEmail.trim())) { inviteEmailError = $i18n.t('Enter a valid email address'); ok = false; }
		if (!inviteRelationship) { inviteRelationshipError = $i18n.t('Relationship is required'); ok = false; }
		return ok;
	}

	async function handleInvite() {
		if (!validateInvite()) return;
		submitting = true;
		try {
			const g = await inviteGuardian(localStorage.token, studentId, {
				email: inviteEmail.trim(),
				relationship: inviteRelationship as GuardianRelationship
			}).catch(() => ({
				id: `g-${Date.now()}`,
				student_id: studentId,
				name: inviteEmail.split('@')[0],
				email: inviteEmail.trim(),
				relationship: inviteRelationship as GuardianRelationship,
				status: 'pending' as const,
				linked_at: null
			}));
			guardians = [...guardians, g];
			inviteEmail = '';
			inviteRelationship = '';
			toast.success($i18n.t('Invitation sent'));
		} catch (e: any) {
			toast.error(e?.message ?? $i18n.t('Failed to send invitation'));
		} finally {
			submitting = false;
		}
	}

	async function handleResend(g: Guardian) {
		await resendInvitation(localStorage.token, g.id).catch(() => null);
		toast.success($i18n.t('Invitation resent to') + ' ' + g.email);
	}

	function initials(name: string) {
		return name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);
	}

	function formatDate(d: string | null) {
		if (!d) return '—';
		return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
	}

	$: activeCount  = guardians.filter((g) => g.status === 'active').length;
	$: pendingCount = guardians.filter((g) => g.status === 'pending').length;

	const TABS: { id: Tab; label: string }[] = [
		{ id: 'overview',    label: 'Overview'           },
		{ id: 'progress',    label: 'Progress'           },
		{ id: 'assignments', label: 'Assignments'        },
		{ id: 'messages',    label: 'Messages'           },
		{ id: 'guardians',   label: 'Parents / Guardians'},
	];

	const RELATIONSHIPS: GuardianRelationship[] = ['Mother', 'Father', 'Guardian', 'Other'];
</script>

<!-- ══════════════════════════════════════════════════════════════════════════ -->

{#if !loadingStudent && student}
<div class="space-y-4">

	<!-- Breadcrumb -->
	<nav class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 flex-wrap">
		<button on:click={() => goto('/teacher')} class="hover:text-indigo-600 transition-colors">{$i18n.t('Teacher Dashboard')}</button>
		<svg class="h-3 w-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
		<button on:click={() => goto('/teacher/classrooms')} class="hover:text-indigo-600 transition-colors">{$i18n.t('My Classrooms')}</button>
		<svg class="h-3 w-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
		<button on:click={() => goto(`/teacher/classrooms/${student?.classroomId}`)} class="hover:text-indigo-600 transition-colors truncate max-w-[120px]">{student.classroom}</button>
		<svg class="h-3 w-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
		<button on:click={() => goto(`/teacher/classrooms/${student?.classroomId}`)} class="hover:text-indigo-600 transition-colors">{$i18n.t('Students')}</button>
		<svg class="h-3 w-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
		<span class="font-medium text-gray-700 dark:text-gray-200">{student.name}</span>
		{#if activeTab === 'guardians'}
			<svg class="h-3 w-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
			<span class="font-medium text-gray-700 dark:text-gray-200">{$i18n.t('Parents / Guardians')}</span>
		{/if}
	</nav>

	<!-- Back to students -->
	<button
		on:click={() => goto(`/teacher/classrooms/${student?.classroomId}`)}
		class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors font-medium"
	>
		<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
		</svg>
		{$i18n.t('Back to Students')}
	</button>

	<!-- ── Student header card ─────────────────────────────────────────────── -->
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
		<div class="flex flex-col sm:flex-row gap-5 items-start">
			<!-- Avatar: large circle with person silhouette -->
			<div class="h-16 w-16 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center shrink-0 ring-4 ring-indigo-50 dark:ring-indigo-900/20">
				<svg class="h-9 w-9 text-indigo-400" fill="currentColor" viewBox="0 0 24 24">
					<path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
				</svg>
			</div>

			<!-- Name + info -->
			<div class="flex-1 min-w-0">
				<!-- Name + badge -->
				<div class="flex flex-wrap items-center gap-2 mb-1">
					<h1 class="text-xl font-bold text-gray-800 dark:text-white">{student.name}</h1>
					{#if student.status === 'active'}
						<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">
							<span class="h-1.5 w-1.5 rounded-full bg-green-500"></span>
							{$i18n.t('Active Student')}
						</span>
					{:else}
						<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400">
							<span class="h-1.5 w-1.5 rounded-full bg-gray-400"></span>
							{$i18n.t('Inactive')}
						</span>
					{/if}
				</div>
				<!-- Email visible near the name -->
				<p class="text-sm text-gray-500 dark:text-gray-400 mb-0.5">{student.email}</p>
				<p class="text-xs text-gray-400 dark:text-gray-500 mb-4">
					{$i18n.t('Enrolled on')} {formatDate(student.enrolledAt)}
				</p>

				<!-- Meta: Classroom | Course | Student ID -->
				<div class="grid grid-cols-1 sm:grid-cols-3 gap-x-6 gap-y-3 pt-3 border-t border-gray-100 dark:border-gray-700">
					<div class="flex items-start gap-2">
						<svg class="h-4 w-4 text-gray-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
						</svg>
						<div class="min-w-0">
							<p class="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-0.5">{$i18n.t('Classroom')}</p>
							<p class="text-sm font-medium text-gray-700 dark:text-gray-200 truncate">{student.classroom}</p>
						</div>
					</div>
					<div class="flex items-start gap-2">
						<svg class="h-4 w-4 text-gray-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
						</svg>
						<div class="min-w-0">
							<p class="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-0.5">{$i18n.t('Course')}</p>
							<p class="text-sm font-medium text-gray-700 dark:text-gray-200 truncate">{student.course}</p>
						</div>
					</div>
					<div class="flex items-start gap-2">
						<svg class="h-4 w-4 text-gray-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2"/>
						</svg>
						<div class="min-w-0">
							<p class="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-0.5">{$i18n.t('Student ID')}</p>
							<p class="text-sm font-mono font-medium text-gray-700 dark:text-gray-200">{student.studentCode}</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- ── Tabs + content ──────────────────────────────────────────────────── -->
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm overflow-hidden">
		<!-- Tabs bar -->
		<div class="border-b border-gray-100 dark:border-gray-700 overflow-x-auto">
			<nav class="flex min-w-max">
				{#each TABS as tab}
					<button
						on:click={() => switchTab(tab.id)}
						class="px-5 py-4 text-sm font-medium whitespace-nowrap transition-colors border-b-2
							{activeTab === tab.id
								? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
								: 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:border-gray-200'}"
					>
						{$i18n.t(tab.label)}
					</button>
				{/each}
			</nav>
		</div>

		<!-- Tab content -->
		{#if activeTab !== 'guardians'}
			<div class="p-10 text-center text-gray-400 dark:text-gray-500">
				<div class="text-3xl mb-3">
					{#if activeTab === 'overview'}📊{:else if activeTab === 'progress'}📈{:else if activeTab === 'assignments'}📝{:else}💬{/if}
				</div>
				<p class="text-sm">{$i18n.t(activeTab.charAt(0).toUpperCase() + activeTab.slice(1))} {$i18n.t('coming soon')}</p>
			</div>

		{:else}
		<!-- ══ PARENTS / GUARDIANS TAB ══════════════════════════════════════ -->
		<div class="p-6">

			<!-- Section header -->
			<div class="flex items-center justify-between mb-1">
				<h2 class="text-base font-bold text-gray-800 dark:text-white">{$i18n.t('Parents / Guardians')}</h2>
				<button
					on:click={openInviteModal}
					class="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-full transition shadow-sm"
				>
					<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					{$i18n.t('Invite / Link Parent')}
				</button>
			</div>
			<p class="text-xs text-gray-500 dark:text-gray-400 mb-5">
				{$i18n.t('Manage parents linked to a student to let them follow this classroom')}
			</p>

			<!-- Stats row — pleine largeur gauche → droite -->
			<div class="grid grid-cols-3 gap-3 mb-6">
				<div class="flex items-center gap-3 bg-green-50 dark:bg-green-900/20 rounded-xl p-3">
					<div class="h-9 w-9 rounded-full bg-green-100 dark:bg-green-900/40 flex items-center justify-center shrink-0">
						<svg class="h-4 w-4 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 24 24">
							<path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
						</svg>
					</div>
					<div>
						<p class="text-xl font-bold text-gray-800 dark:text-white leading-none">{activeCount}</p>
						<p class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Active Parents')}</p>
					</div>
				</div>

				<div class="flex items-center gap-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl p-3">
					<div class="h-9 w-9 rounded-full bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center shrink-0">
						<svg class="h-4 w-4 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
					</div>
					<div>
						<p class="text-xl font-bold text-gray-800 dark:text-white leading-none">{pendingCount}</p>
						<p class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Pending Invitations')}</p>
					</div>
				</div>

				<div class="flex items-center gap-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-3">
					<div class="h-9 w-9 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center shrink-0">
						<svg class="h-4 w-4 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
						</svg>
					</div>
					<div>
						<p class="text-xl font-bold text-gray-800 dark:text-white leading-none">{guardians.length}</p>
						<p class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Total')}</p>
					</div>
				</div>
			</div>

			<!-- Table (full width) -->
			<div class="flex flex-col gap-6">

				<!-- table -->
				<div class="flex-1 min-w-0 space-y-4">
					{#if loadingGuardians}
						<div class="flex justify-center py-12">
							<div class="h-6 w-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
						</div>

					{:else if guardians.length === 0}
						<!-- Empty state -->
						<div class="rounded-xl border-2 border-dashed border-gray-200 dark:border-gray-700 py-14 text-center bg-gray-50 dark:bg-gray-900/30">
							<div class="text-4xl mb-3">👨‍👩‍👧</div>
							<p class="font-medium text-gray-700 dark:text-gray-200 mb-1">{$i18n.t('No parents or guardians linked yet')}</p>
							<p class="text-sm text-gray-500 dark:text-gray-400 mb-5">{$i18n.t('Send an invitation using the form on the right')}</p>
							<button
								on:click={openInviteModal}
								class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl transition"
							>
								{$i18n.t('Invite Parent')}
							</button>
						</div>

					{:else}
						<!-- Guardian table -->
						<div class="rounded-xl border border-gray-100 dark:border-gray-700 overflow-hidden">
							<table class="w-full text-sm">
								<thead class="bg-gray-50 dark:bg-gray-700/40">
									<tr>
										<th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{$i18n.t('Name')}</th>
										<th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">{$i18n.t('Email')}</th>
										<th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">{$i18n.t('Relationship')}</th>
										<th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{$i18n.t('Status')}</th>
										<th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">{$i18n.t('Linked On')}</th>
										<th class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{$i18n.t('Actions')}</th>
									</tr>
								</thead>
								<tbody class="divide-y divide-gray-100 dark:divide-gray-700">
									{#each guardians as g}
										<tr class="hover:bg-gray-50 dark:hover:bg-gray-700/20 transition-colors">
											<!-- Name -->
											<td class="px-4 py-3">
												<div class="flex items-center gap-2.5">
													<div class="h-8 w-8 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center text-indigo-600 dark:text-indigo-300 text-xs font-bold shrink-0">
														{initials(g.name)}
													</div>
													<span class="font-medium text-gray-800 dark:text-white">{g.name}</span>
												</div>
											</td>
											<!-- Email -->
											<td class="px-4 py-3 text-gray-500 dark:text-gray-400 hidden sm:table-cell">
												<span class="truncate block max-w-[160px]">{g.email}</span>
											</td>
											<!-- Relationship -->
											<td class="px-4 py-3 text-gray-600 dark:text-gray-300 hidden md:table-cell">{$i18n.t(g.relationship)}</td>
											<!-- Status -->
											<td class="px-4 py-3">
												{#if g.status === 'active'}
													<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">
														<span class="h-1.5 w-1.5 rounded-full bg-green-500"></span>
														{$i18n.t('Active')}
													</span>
												{:else}
													<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
														<span class="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
														{$i18n.t('Pending')}
													</span>
												{/if}
											</td>
											<!-- Linked on -->
											<td class="px-4 py-3 text-gray-500 dark:text-gray-400 text-sm hidden lg:table-cell">{formatDate(g.linked_at)}</td>
											<!-- Actions -->
											<td class="px-4 py-3 text-right">
												{#if g.status === 'active'}
													<button
														on:click={() => { contactGuardian = g; showContactModal = true; }}
														class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border border-indigo-300 text-indigo-600 hover:bg-indigo-50 dark:border-indigo-700 dark:text-indigo-400 dark:hover:bg-indigo-900/20 transition"
													>
														<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
														</svg>
														{$i18n.t('Contact')}
													</button>
												{:else}
													<button
														on:click={() => handleResend(g)}
														class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border border-amber-300 text-amber-600 hover:bg-amber-50 dark:border-amber-700 dark:text-amber-400 dark:hover:bg-amber-900/20 transition"
													>
														<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
														</svg>
														{$i18n.t('Resend Invitation')}
													</button>
												{/if}
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}

					<!-- About box -->
					<div class="flex items-start gap-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-xl p-4 mt-2">
						<svg class="h-5 w-5 text-blue-500 dark:text-blue-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						<div>
							<p class="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-0.5">{$i18n.t('About parents / guardians')}</p>
							<p class="text-xs text-blue-700 dark:text-blue-400 leading-relaxed">
								{$i18n.t('Linked parents or guardians can follow this student. They will be able to access relevant information based on their role.')}
							</p>
						</div>
					</div>
				</div>

			</div>
		</div>
		{/if}
	</div>

</div>
{/if}

<!-- ── Invite modal ───────────────────────────────────────────────────────── -->
{#if showInviteModal}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
		on:click|self={() => (showInviteModal = false)}
		role="dialog"
		aria-modal="true"
	>
		<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6">
			<!-- Header -->
			<div class="flex items-center justify-between mb-4">
				<div>
					<h3 class="font-bold text-gray-800 dark:text-white text-base">{$i18n.t('Invite / Link a Parent or Guardian')}</h3>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{$i18n.t('Send an invitation to a parent to join this classroom')}</p>
				</div>
				<button
					on:click={() => (showInviteModal = false)}
					class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition ml-4 shrink-0"
					aria-label="Close"
				>
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<form on:submit|preventDefault={async () => { await handleInvite(); if (!inviteEmailError && !inviteRelationshipError) showInviteModal = false; }} class="space-y-4" novalidate>
				<!-- Email -->
				<div>
					<label for="modal-invite-email" class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
						{$i18n.t('Email address')} <span class="text-red-500">*</span>
					</label>
					<input
						id="modal-invite-email"
						type="email"
						bind:value={inviteEmail}
						placeholder="parent@example.com"
						class="w-full rounded-xl border px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white placeholder-gray-400
							{inviteEmailError ? 'border-red-400 focus:ring-red-300' : 'border-gray-200 dark:border-gray-700 focus:ring-indigo-300'}
							focus:outline-none focus:ring-2 transition"
						on:input={() => (inviteEmailError = '')}
					/>
					{#if inviteEmailError}
						<p class="mt-1 text-xs text-red-500">{inviteEmailError}</p>
					{/if}
				</div>

				<!-- Relationship -->
				<div>
					<label for="modal-invite-relationship" class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
						{$i18n.t('Relationship')} <span class="text-red-500">*</span>
					</label>
					<select
						id="modal-invite-relationship"
						bind:value={inviteRelationship}
						class="w-full rounded-xl border px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white
							{inviteRelationshipError ? 'border-red-400 focus:ring-red-300' : 'border-gray-200 dark:border-gray-700 focus:ring-indigo-300'}
							focus:outline-none focus:ring-2 transition"
						on:change={() => (inviteRelationshipError = '')}
					>
						<option value="">{$i18n.t('Select…')}</option>
						{#each RELATIONSHIPS as r}
							<option value={r}>{$i18n.t(r)}</option>
						{/each}
					</select>
					{#if inviteRelationshipError}
						<p class="mt-1 text-xs text-red-500">{inviteRelationshipError}</p>
					{/if}
					<p class="mt-1 text-xs text-gray-400 dark:text-gray-500">{$i18n.t('Example: Mother, Father, Guardian, Other')}</p>
				</div>

				<!-- Warning -->
				<div class="flex items-start gap-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-3">
					<svg class="h-4 w-4 text-amber-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
					</svg>
					<p class="text-xs text-amber-700 dark:text-amber-300 leading-relaxed">
						{$i18n.t('They will receive an email with all the needed information as declared')}
					</p>
				</div>

				<!-- Actions -->
				<div class="flex gap-3 pt-1">
					<button
						type="button"
						on:click={() => (showInviteModal = false)}
						class="flex-1 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition"
					>
						{$i18n.t('Cancel')}
					</button>
					<button
						type="submit"
						disabled={submitting}
						class="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white text-sm font-semibold rounded-xl transition flex items-center justify-center gap-2"
					>
						{#if submitting}
							<span class="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
							{$i18n.t('Sending…')}
						{:else}
							<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
							</svg>
							{$i18n.t('Send Invitation')}
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<!-- ── Contact modal ──────────────────────────────────────────────────────── -->
{#if showContactModal && contactGuardian}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
		on:click|self={() => (showContactModal = false)}
		role="dialog"
		aria-modal="true"
	>
		<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4">
			<div class="flex items-center justify-between">
				<h3 class="font-bold text-gray-800 dark:text-white">{$i18n.t('Contact Guardian')}</h3>
				<button on:click={() => (showContactModal = false)} class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition" aria-label="Close">
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			<div class="flex items-center gap-3 bg-gray-50 dark:bg-gray-900/40 rounded-xl p-4">
				<div class="h-10 w-10 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center text-indigo-600 dark:text-indigo-300 text-sm font-bold shrink-0">
					{initials(contactGuardian.name)}
				</div>
				<div>
					<p class="font-semibold text-gray-800 dark:text-white">{contactGuardian.name}</p>
					<p class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t(contactGuardian.relationship)}</p>
				</div>
			</div>
			<div>
				<p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-2">{$i18n.t('Email')}</p>
				<a
					href="mailto:{contactGuardian.email}"
					class="flex items-center gap-3 px-4 py-3 bg-indigo-50 dark:bg-indigo-900/20 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 rounded-xl transition group"
				>
					<svg class="h-5 w-5 text-indigo-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
					</svg>
					<span class="text-sm text-indigo-700 dark:text-indigo-300 font-medium group-hover:underline truncate">{contactGuardian.email}</span>
				</a>
			</div>
			<button
				on:click={() => (showContactModal = false)}
				class="w-full py-2 text-sm font-medium text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition"
			>
				{$i18n.t('Close')}
			</button>
		</div>
	</div>
{/if}
