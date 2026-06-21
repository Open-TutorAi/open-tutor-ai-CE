<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';

	const i18n = getContext('i18n');

	// ── Types ─────────────────────────────────────────────────────────────────
	interface Student {
		id: string;
		name: string;
		email: string;
		status: 'active' | 'inactive';
		enrolledAt: string;
		studentCode: string;
	}

	interface Classroom {
		id: string;
		name: string;
		course: string;
		level: string;
		students: Student[];
	}

	// ── State ─────────────────────────────────────────────────────────────────
	$: classroomId = $page.params.classroomId;
	let classroom: Classroom | null = null;
	let loading = true;
	let searchQuery = '';

	// ── Mock data ─────────────────────────────────────────────────────────────
	const MOCK: Record<string, Classroom> = {
		'cls-1': {
			id: 'cls-1',
			name: 'Learn Python Basics for Beginners',
			course: 'Computer Science • High School',
			level: 'Beginner',
			students: [
				{ id: 'stu-1', name: 'Alex Johnson',  email: 'alex.johnson@email.com',  status: 'active',   enrolledAt: '2024-05-12', studentCode: 'STU-2024-001' },
				{ id: 'stu-2', name: 'Sarah Miller',  email: 'sarah.miller@email.com',  status: 'active',   enrolledAt: '2024-05-12', studentCode: 'STU-2024-002' },
				{ id: 'stu-3', name: 'Emma Williams', email: 'emma.williams@email.com', status: 'inactive', enrolledAt: '2024-05-14', studentCode: 'STU-2024-003' },
			]
		},
		'cls-2': {
			id: 'cls-2',
			name: 'Advanced Mathematics',
			course: 'Mathematics • High School',
			level: 'Advanced',
			students: [
				{ id: 'stu-4', name: 'Lucas Brown', email: 'lucas.brown@email.com', status: 'active',   enrolledAt: '2024-09-01', studentCode: 'STU-2024-004' },
				{ id: 'stu-5', name: 'Mia Davis',   email: 'mia.davis@email.com',   status: 'inactive', enrolledAt: '2024-09-01', studentCode: 'STU-2024-005' },
			]
		},
		'cls-3': {
			id: 'cls-3',
			name: 'Introduction to Biology',
			course: 'Biology • Middle School',
			level: 'Beginner',
			students: [
				{ id: 'stu-6', name: 'Noah Wilson', email: 'noah.wilson@email.com', status: 'active', enrolledAt: '2024-09-15', studentCode: 'STU-2024-006' },
			]
		}
	};

	onMount(async () => {
		try {
			await new Promise((r) => setTimeout(r, 250));
			classroom = MOCK[classroomId] ?? null;
			if (!classroom) toast.error($i18n.t('Classroom not found'));
		} catch (e) {
			toast.error($i18n.t('Failed to load classroom'));
		} finally {
			loading = false;
		}
	});

	$: filteredStudents = (classroom?.students ?? []).filter(
		(s) =>
			!searchQuery ||
			s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
			s.email.toLowerCase().includes(searchQuery.toLowerCase())
	);

	function initials(name: string) {
		return name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);
	}

	function formatDate(d: string) {
		return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
	}
</script>

<div class="space-y-6">
	<!-- Breadcrumb -->
	<nav class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
		<button on:click={() => goto('/teacher/classrooms')} class="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
			{$i18n.t('My Classrooms')}
		</button>
		<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
		</svg>
		<span class="text-gray-800 dark:text-white font-medium truncate max-w-xs">{classroom?.name ?? '…'}</span>
	</nav>

	<!-- Header -->
	{#if classroom}
		<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
			<div class="flex flex-col sm:flex-row sm:items-center gap-4">
				<div class="h-12 w-12 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-xl shrink-0">
					{classroom.name[0]}
				</div>
				<div class="flex-1 min-w-0">
					<h1 class="text-xl font-bold text-gray-800 dark:text-white">{classroom.name}</h1>
					<p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{classroom.course}</p>
				</div>
				<div class="flex items-center gap-2 shrink-0">
					<span class="text-sm text-gray-500 dark:text-gray-400">
						{classroom.students.length} {$i18n.t('students enrolled')}
					</span>
				</div>
			</div>
		</div>
	{/if}

	<!-- Students -->
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm overflow-hidden">
		<!-- Table header -->
		<div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
			<h2 class="font-semibold text-gray-800 dark:text-white">{$i18n.t('Students')}</h2>
			<div class="flex items-center gap-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-1.5">
				<svg class="h-4 w-4 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<input
					type="text"
					placeholder={$i18n.t('Search students…')}
					bind:value={searchQuery}
					class="bg-transparent text-sm outline-none text-gray-700 dark:text-gray-200 placeholder-gray-400 w-36"
				/>
			</div>
		</div>

		{#if loading}
			<div class="flex justify-center py-16">
				<div class="h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
			</div>

		{:else if filteredStudents.length === 0}
			<div class="py-16 text-center">
				<div class="text-4xl mb-4">👨‍🎓</div>
				<p class="text-gray-500 dark:text-gray-400 font-medium">{$i18n.t('No students found')}</p>
			</div>

		{:else}
			<table class="w-full text-sm">
				<thead class="bg-gray-50 dark:bg-gray-700/40">
					<tr>
						<th class="text-left px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{$i18n.t('Student')}</th>
						<th class="text-left px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">{$i18n.t('Student ID')}</th>
						<th class="text-left px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">{$i18n.t('Enrolled On')}</th>
						<th class="text-left px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{$i18n.t('Status')}</th>
						<th class="px-6 py-3"></th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100 dark:divide-gray-700">
					{#each filteredStudents as student}
						<tr class="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors cursor-pointer"
							on:click={() => goto(`/teacher/students/${student.id}`)}>
							<!-- Student name + avatar -->
							<td class="px-6 py-4">
								<div class="flex items-center gap-3">
									<div class="h-9 w-9 rounded-full bg-gradient-to-br from-indigo-400 to-violet-500 flex items-center justify-center text-white text-xs font-bold shrink-0">
										{initials(student.name)}
									</div>
									<div>
										<p class="font-medium text-gray-800 dark:text-white">{student.name}</p>
										<p class="text-xs text-gray-500 dark:text-gray-400">{student.email}</p>
									</div>
								</div>
							</td>
							<!-- Student code -->
							<td class="px-6 py-4 text-gray-600 dark:text-gray-300 hidden sm:table-cell font-mono text-xs">{student.studentCode}</td>
							<!-- Enrolled -->
							<td class="px-6 py-4 text-gray-600 dark:text-gray-300 hidden md:table-cell">{formatDate(student.enrolledAt)}</td>
							<!-- Status -->
							<td class="px-6 py-4">
								{#if student.status === 'active'}
									<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">
										<span class="h-1.5 w-1.5 rounded-full bg-green-500"></span>
										{$i18n.t('Active')}
									</span>
								{:else}
									<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300">
										<span class="h-1.5 w-1.5 rounded-full bg-gray-400"></span>
										{$i18n.t('Inactive')}
									</span>
								{/if}
							</td>
							<!-- Arrow -->
							<td class="px-6 py-4 text-right">
								<svg class="h-4 w-4 text-gray-300 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
								</svg>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{/if}
	</div>
</div>
