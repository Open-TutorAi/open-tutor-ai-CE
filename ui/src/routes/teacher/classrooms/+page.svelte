<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { user } from '$lib/stores';

	const i18n = getContext('i18n');

	// ── Types ─────────────────────────────────────────────────────────────────
	interface Student {
		id: string;
		name: string;
		email: string;
		status: 'active' | 'inactive';
		avatar?: string;
	}

	interface Classroom {
		id: string;
		name: string;
		course: string;
		level: string;
		students: Student[];
		createdAt: string;
	}

	// ── State ─────────────────────────────────────────────────────────────────
	let classrooms: Classroom[] = [];
	let loading = true;
	let searchQuery = '';

	// ── Mock data (replace with API call when backend ready) ─────────────────
	const MOCK_CLASSROOMS: Classroom[] = [
		{
			id: 'cls-1',
			name: 'Learn Python Basics for Beginners',
			course: 'Computer Science • High School',
			level: 'Beginner',
			createdAt: '2024-09-01',
			students: [
				{ id: 'stu-1', name: 'Alex Johnson', email: 'alex.johnson@email.com', status: 'active' },
				{ id: 'stu-2', name: 'Sarah Miller', email: 'sarah.miller@email.com', status: 'active' },
				{ id: 'stu-3', name: 'Emma Williams', email: 'emma.williams@email.com', status: 'active' },
			]
		},
		{
			id: 'cls-2',
			name: 'Advanced Mathematics',
			course: 'Mathematics • High School',
			level: 'Advanced',
			createdAt: '2024-09-01',
			students: [
				{ id: 'stu-4', name: 'Lucas Brown', email: 'lucas.brown@email.com', status: 'active' },
				{ id: 'stu-5', name: 'Mia Davis', email: 'mia.davis@email.com', status: 'inactive' },
			]
		},
		{
			id: 'cls-3',
			name: 'Introduction to Biology',
			course: 'Biology • Middle School',
			level: 'Beginner',
			createdAt: '2024-09-15',
			students: [
				{ id: 'stu-6', name: 'Noah Wilson', email: 'noah.wilson@email.com', status: 'active' },
			]
		}
	];

	onMount(async () => {
		try {
			// TODO: replace with real API call
			// classrooms = await getTeacherClassrooms(localStorage.token);
			await new Promise((r) => setTimeout(r, 300)); // simulate network
			classrooms = MOCK_CLASSROOMS;
		} catch (e) {
			toast.error($i18n.t('Failed to load classrooms'));
		} finally {
			loading = false;
		}
	});

	$: filtered = classrooms.filter(
		(c) =>
			!searchQuery ||
			c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
			c.course.toLowerCase().includes(searchQuery.toLowerCase())
	);

	function levelColor(level: string) {
		if (level === 'Beginner')
			return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300';
		if (level === 'Advanced')
			return 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300';
		return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300';
	}
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold text-gray-800 dark:text-white">{$i18n.t('My Classrooms')}</h1>
			<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
				{$i18n.t('Select a classroom to manage students and guardians')}
			</p>
		</div>
		<!-- Search -->
		<div class="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2 shadow-sm">
			<svg class="h-4 w-4 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
			</svg>
			<input
				type="text"
				placeholder={$i18n.t('Search classrooms…')}
				bind:value={searchQuery}
				class="bg-transparent text-sm outline-none text-gray-700 dark:text-gray-200 placeholder-gray-400 w-48"
			/>
		</div>
	</div>

	<!-- Loading -->
	{#if loading}
		<div class="flex justify-center py-16">
			<div class="h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
		</div>

	<!-- Empty -->
	{:else if filtered.length === 0}
		<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-16 text-center">
			<div class="text-4xl mb-4">🏫</div>
			<p class="text-gray-500 dark:text-gray-400 font-medium">{$i18n.t('No classrooms found')}</p>
			{#if searchQuery}
				<button class="mt-3 text-sm text-indigo-600 hover:underline" on:click={() => (searchQuery = '')}>
					{$i18n.t('Clear search')}
				</button>
			{/if}
		</div>

	<!-- Grid -->
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
			{#each filtered as classroom}
				<button
					on:click={() => goto(`/teacher/classrooms/${classroom.id}`)}
					class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 text-left hover:shadow-md hover:border-indigo-200 dark:hover:border-indigo-700 transition-all duration-200 group"
				>
					<!-- Top row -->
					<div class="flex items-start justify-between mb-3">
						<div class="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-lg shrink-0">
							{classroom.name[0]}
						</div>
						<span class="text-xs font-semibold px-2 py-0.5 rounded-full {levelColor(classroom.level)}">
							{$i18n.t(classroom.level)}
						</span>
					</div>

					<!-- Name + course -->
					<h3 class="font-semibold text-gray-800 dark:text-white text-sm leading-snug group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2 mb-1">
						{classroom.name}
					</h3>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">{classroom.course}</p>

					<!-- Students count -->
					<div class="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-700">
						<div class="flex items-center gap-1.5">
							<svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
							</svg>
							<span class="text-xs text-gray-500 dark:text-gray-400">
								{classroom.students.length} {$i18n.t('students')}
							</span>
						</div>
						<svg class="h-4 w-4 text-gray-300 group-hover:text-indigo-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
						</svg>
					</div>
				</button>
			{/each}
		</div>
	{/if}
</div>
