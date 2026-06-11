<script lang="ts">
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { browser } from '$app/environment';
	import HideLessonsModal from '$lib/components/teacher/pages/HideLessonsModal.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	let channels: any[] = [];
	let students: any[] = [];
	let completionRate = '0.0%';
	let enrolledStudentsCount = '0';
	let isLoading = true;

	let selectedCourse = 'all';
	let selectedStatus = 'all';
	let selectedDate = '';

	let showHideModal = false;
	let selectedStudentId = '';
	let selectedStudentName = '';

	let statuses = [
		{ id: 'completed', name: 'Completed' },
		{ id: 'in_progress', name: 'In progress' },
		{ id: 'failed', name: 'Failed' }
	];

	let searchQuery = '';
	let openMenuId: number | null = null;

	async function fetchCourses() {
		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch('/api/v1/teacher/courses/', {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				const data = await res.json();
				channels = data.map((c: any) => ({ id: c.id, name: c.title }));
			}
		} catch (e) {
			console.error('Error fetching courses:', e);
		}
	}

	async function fetchReports() {
		isLoading = true;
		try {
			const token = localStorage.getItem('token') ?? '';
			let url = `/api/v1/teacher/analytics/reports?course_id=${selectedCourse}&status=${selectedStatus}`;
			if (selectedDate) url += `&date=${selectedDate}`;
			const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
			if (res.ok) {
				const data = await res.json();
				students = data.students || [];
				completionRate = data.completion_rate || '0.0%';
				enrolledStudentsCount = data.enrolled_students || '0';
			}
		} catch (e) {
			console.error('Error fetching reports:', e);
		} finally {
			isLoading = false;
		}
	}

	$: filteredStudents = students.filter((s) =>
		s.name.toLowerCase().includes(searchQuery.toLowerCase())
	);

	$: if (browser && (selectedCourse || selectedStatus || selectedDate)) {
		fetchReports();
	}

	function openMessage(studentName: string, studentId: string) {
		goto(`/teacher/messages?chatId=${studentId}&student=${encodeURIComponent(studentName)}`);
	}

	function viewStudentProfile(studentId: string) {
		goto(`/teacher/reports/student/${studentId}`);
	}

	function toggleMenu(index: number) {
		openMenuId = openMenuId === index ? null : index;
	}

	function handleHideLesson(student: any) {
		selectedStudentId = student.id;
		selectedStudentName = student.name;
		showHideModal = true;
		openMenuId = null;
	}

	function resetFilters() {
		selectedCourse = 'all';
		selectedStatus = 'all';
		selectedDate = '';
	}

	let isDarkMode = false;

	onMount(async () => {
		isDarkMode = localStorage.getItem('theme') === 'dark';
		applyTheme();
		await fetchCourses();
		await fetchReports();
	});

	function applyTheme() {
		if (isDarkMode) {
			document.documentElement.classList.add('dark');
			localStorage.setItem('theme', 'dark');
		} else {
			document.documentElement.classList.remove('dark');
			localStorage.setItem('theme', 'light');
		}
	}

	function statusClasses(status: string): string {
		if (status === 'Active') return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400';
		if (status === 'Struggling') return 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400';
		return 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400';
	}
</script>

<svelte:window on:click={() => { openMenuId = null; }} />

<div class="min-h-screen bg-slate-50 dark:bg-[#0a0f1a] transition-colors duration-300">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

		<!-- Header -->
		<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
			<div>
				<h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-50 tracking-tight">
					{$i18n.t('Student Tracking')}
				</h1>
				<p class="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
					{$i18n.t('Analyze student performance and intervene at the right time.')}
				</p>
			</div>
		</div>

		<!-- Stats -->
		<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
			<div class="bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800 p-5">
				<p class="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">
					{$i18n.t('Completion Rate')}
				</p>
				<p class="text-3xl font-bold text-slate-900 dark:text-white">{completionRate}</p>
			</div>
			<div class="bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800 p-5">
				<p class="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">
					{$i18n.t('Enrolled Students')}
				</p>
				<div class="flex items-end gap-2">
					<p class="text-3xl font-bold text-slate-900 dark:text-white">{enrolledStudentsCount}</p>
					<span class="text-xs font-semibold text-emerald-600 dark:text-emerald-400 mb-1">↗ +12%</span>
				</div>
			</div>
		</div>

		<!-- Filters -->
		<div class="bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800 p-4">
			<div class="flex flex-wrap gap-3 items-center">
				<select
					bind:value={selectedCourse}
					class="h-9 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 text-sm text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition cursor-pointer"
				>
					<option value="all">{$i18n.t('All courses')}</option>
					{#each channels as ch}
						<option value={ch.id}>{$i18n.t(ch.name)}</option>
					{/each}
				</select>

				<input
					type="date"
					bind:value={selectedDate}
					class="h-9 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 text-sm text-slate-700 dark:text-slate-300 outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
				/>

				<select
					bind:value={selectedStatus}
					class="h-9 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 text-sm text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition cursor-pointer"
				>
					<option value="all">{$i18n.t('All statuses')}</option>
					{#each statuses as st}
						<option value={st.id}>{$i18n.t(st.name)}</option>
					{/each}
				</select>

				<button
					on:click={resetFilters}
					class="h-9 flex items-center gap-1.5 px-3 text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
					</svg>
					{$i18n.t('Reset')}
				</button>
			</div>
		</div>

		<!-- Student Table -->
		<div class="bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
			<!-- Table Header -->
			<div class="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
				<h2 class="text-base font-semibold text-slate-900 dark:text-slate-50">
					{$i18n.t('Student List')}
				</h2>
				<div class="relative w-full sm:w-64">
					<svg class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z" />
					</svg>
					<input
						type="text"
						bind:value={searchQuery}
						placeholder={$i18n.t('Search for a student...')}
						class="w-full h-9 pl-9 pr-4 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-300 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
					/>
				</div>
			</div>

			<!-- Table -->
			<div class="overflow-x-auto">
				{#if isLoading}
					<div class="py-16 text-center text-sm text-slate-400 dark:text-slate-500">
						{$i18n.t('Loading...')}
					</div>
				{:else if filteredStudents.length === 0}
					<div class="py-16 text-center text-sm text-slate-400 dark:text-slate-500">
						{$i18n.t('No students found.')}
					</div>
				{:else}
					<table class="w-full text-left">
						<thead>
							<tr class="border-b border-slate-100 dark:border-slate-800">
								<th class="px-6 py-3 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">{$i18n.t('Student')}</th>
								<th class="px-6 py-3 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider hidden md:table-cell">{$i18n.t('Enrolled')}</th>
								<th class="px-6 py-3 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">{$i18n.t('Progress')}</th>
								<th class="px-6 py-3 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider hidden sm:table-cell">{$i18n.t('Grade')}</th>
								<th class="px-6 py-3 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">{$i18n.t('Status')}</th>
								<th class="px-6 py-3 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider text-right">{$i18n.t('Actions')}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-50 dark:divide-slate-800">
							{#each filteredStudents as s, i}
								<tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors group">
									<td class="px-6 py-3.5">
										<div class="flex items-center gap-3">
											<div class="w-8 h-8 rounded-lg bg-blue-600 dark:bg-indigo-600 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
												{s.name.charAt(0).toUpperCase()}
											</div>
											<span class="text-sm font-medium text-slate-800 dark:text-slate-200">{s.name}</span>
										</div>
									</td>
									<td class="px-6 py-3.5 text-sm text-slate-500 dark:text-slate-400 hidden md:table-cell">{s.date}</td>
									<td class="px-6 py-3.5">
										<div class="flex items-center gap-2.5 min-w-[100px]">
											<div class="flex-1 h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
												<div class="h-full bg-blue-500 dark:bg-indigo-500 rounded-full transition-all" style="width: {s.progress}%"></div>
											</div>
											<span class="text-xs font-semibold text-slate-600 dark:text-slate-400 w-8 text-right">{s.progress}%</span>
										</div>
									</td>
									<td class="px-6 py-3.5 text-sm font-semibold text-slate-700 dark:text-slate-300 hidden sm:table-cell">{s.note}</td>
									<td class="px-6 py-3.5">
										<span class="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-semibold {statusClasses(s.status)}">
											{$i18n.t(s.status)}
										</span>
									</td>
									<td class="px-6 py-3.5 text-right">
										<div class="flex justify-end items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
											<button
												on:click={() => openMessage(s.name, s.id)}
												title={$i18n.t('Send message')}
												class="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:text-blue-400 dark:hover:bg-blue-500/10 transition"
											>
												<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
												</svg>
											</button>
											<button
												on:click={() => viewStudentProfile(s.id || '123')}
												title={$i18n.t('View profile')}
												class="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:text-indigo-400 dark:hover:bg-indigo-500/10 transition"
											>
												<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
												</svg>
											</button>
											<div class="relative">
												<button
													on:click|stopPropagation={() => toggleMenu(students.indexOf(s))}
													title={$i18n.t('More options')}
													class="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 dark:hover:text-slate-200 dark:hover:bg-slate-700 transition"
												>
													<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
														<circle cx="12" cy="5" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="12" cy="19" r="1.5" />
													</svg>
												</button>
												{#if openMenuId === students.indexOf(s)}
													<div
														class="absolute right-0 mt-1 w-48 bg-white dark:bg-[#1e293b] border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg z-50 py-1"
														on:click|stopPropagation
													>
														<button
															on:click={() => handleHideLesson(s)}
															class="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2.5 transition"
														>
															<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-5 0-9-4-9-7a9.77 9.77 0 012.1-3.9M9.88 9.88A3 3 0 0115 12m0 0a3 3 0 01-3 3m6.364-6.364A9 9 0 0121 12c0 3-4 7-9 7a9.8 9.8 0 01-2.825-.412M3 3l18 18" />
															</svg>
															{$i18n.t('Hide lesson')}
														</button>
														<div class="my-1 border-t border-slate-100 dark:border-slate-700"></div>
														<button
															class="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 flex items-center gap-2.5 transition"
														>
															<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
															</svg>
															{$i18n.t('Delete Student')}
														</button>
													</div>
												{/if}
											</div>
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				{/if}
			</div>

			<!-- Footer -->
			<div class="px-6 py-3.5 border-t border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
				<span class="text-xs text-slate-400 dark:text-slate-500">
					{$i18n.t('Showing {{count}} students', { count: filteredStudents.length })}
				</span>
				<div class="flex gap-1.5">
					<button class="h-8 px-3 text-xs font-medium text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition">
						{$i18n.t('Previous')}
					</button>
					<button class="h-8 px-3 text-xs font-medium text-white bg-blue-600 dark:bg-indigo-600 rounded-lg">
						1
					</button>
					<button class="h-8 px-3 text-xs font-medium text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition">
						{$i18n.t('Next')}
					</button>
				</div>
			</div>
		</div>

	</div>
</div>

<HideLessonsModal
	bind:show={showHideModal}
	studentId={selectedStudentId}
	studentName={selectedStudentName}
/>