<script lang="ts">
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	const i18n = getContext<Writable<i18nType>>('i18n');

	let channels = [
		{ id: 'JAVA-101', name: 'General - Java Course' },
		{ id: 'WEB-202', name: 'Final Project - Web' },
		{ id: 'ALGO-303', name: 'Advanced Algorithms' },
		{ id: 'SQL-404', name: 'SQL Database' },
		{ id: 'AI-505', name: 'Artificial Intelligence' }
	];

	let selectedCourse = 'all';
	let selectedStatus = 'all';
	let selectedDate = '';

	let statuses = [
		{ id: 'completed', name: 'Completed' },
		{ id: 'in_progress', name: 'In progress' },
		{ id: 'failed', name: 'Failed' }
	];

	let students = [
		{
			id: '1',
			name: 'Lahcen ECHCHARIY',
			date: '12 Sept 2023',
			progress: 85,
			note: '16/20',
			status: 'Active'
		},
		{
			id: '2',
			name: 'Abdelhadi Ait Boubker',
			date: '15 Sept 2023',
			progress: 42,
			note: '16/20',
			status: 'Active'
		},
		{
			id: '3',
			name: 'Abdelaziz Boukdous',
			date: '10 Sept 2023',
			progress: 92,
			note: '19/20',
			status: 'Active'
		},
		{
			id: '4',
			name: 'Mourad Amribd',
			date: '18 Sept 2023',
			progress: 15,
			note: '05/20',
			status: 'Struggling'
		},
		{
			id: '5',
			name: 'Hafid Qastali',
			date: '12 Sept 2023',
			progress: 68,
			note: '14/20',
			status: 'Inactive'
		}
	];

	let searchQuery = '';
	let openMenuId: number | null = null;

	$: filteredStudents = students.filter((student) =>
		student.name.toLowerCase().includes(searchQuery.toLowerCase())
	);

	$: {
		applyFilter(selectedCourse, selectedStatus, selectedDate);
	}

	function applyFilter(course: string, status: string, date: string) {
		console.log(`Filtre appliqué: Course=${course}, Status=${status}, Date=${date}`);
	}

	function openMessage(studentName: string) {
		goto(`/teacher/discussions?student=${encodeURIComponent(studentName)}`);
	}

	function viewStudentProfile(studentId: string) {
		goto(`/teacher/students/${studentId}`);
	}

	function sendReport(studentName: string) {
		toast.success(`Report sent to ${studentName} successfully!`);
	}

	function toggleMenu(index: number) {
		openMenuId = openMenuId === index ? null : index;
	}

	function handleDelete(name: string) {
		console.log('Hadaf student:', name);
		openMenuId = null;
	}

	function handleHideLesson(name: string) {
		console.log('Ikhfa2 dars 3en:', name);
		openMenuId = null;
	}

	let isDarkMode = false;

	onMount(() => {
		isDarkMode = localStorage.getItem('theme') === 'dark';
		applyTheme();
	});

	function toggleDarkMode() {
		isDarkMode = !isDarkMode;
		applyTheme();
	}

	function applyTheme() {
		if (isDarkMode) {
			document.documentElement.classList.add('dark');
			localStorage.setItem('theme', 'dark');
		} else {
			document.documentElement.classList.remove('dark');
			localStorage.setItem('theme', 'light');
		}
	}

	const navigateTo = (path: string) => goto(`/teacher/reports/${path}`);
	const handleNewAnalysis = () => goto('/teacher/reports/new-analysis');
	const handleGlobalReport = () => goto('/teacher/reports/global');
</script>

<div
	class="p-8 space-y-8 bg-[#F8FAFC] dark:bg-[#030712] min-h-screen transition-colors duration-500"
>
	<div class="flex justify-between items-start">
		<div>
			<h1 class="text-3xl font-bold text-slate-800 dark:text-slate-50 transition-colors">
				{$i18n.t('Student Tracking')}
			</h1>
			<p class="text-slate-500 dark:text-slate-400 mt-1 transition-colors">
				{$i18n.t('Analyze student performance and intervene at the right time.')}
			</p>
		</div>

	</div>

	<div
		class="flex flex-wrap gap-4 items-center p-4 bg-white dark:bg-[#111827] rounded-[24px] border border-slate-100 dark:border-slate-800 shadow-sm transition-all"
	>
		<select
			bind:value={selectedCourse}
			class="bg-slate-50 dark:bg-[#1e293b] border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2 text-sm text-slate-600 dark:text-slate-300 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all cursor-pointer"
		>
			<option value="all">{$i18n.t('All courses')}</option>
			{#each channels as ch}
				<option value={ch.id}>{$i18n.t(ch.name)}</option>
			{/each}
		</select>

		<input
			type="date"
			bind:value={selectedDate}
			class="bg-slate-50 dark:bg-[#1e293b] border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2 text-sm text-slate-600 dark:text-slate-300 outline-none transition-all"
		/>

		<select
			bind:value={selectedStatus}
			class="bg-slate-50 dark:bg-[#1e293b] border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2 text-sm text-slate-600 dark:text-slate-300 outline-none transition-all cursor-pointer"
		>
			<option value="all">{$i18n.t('All statuses')}</option>
			{#each statuses as st}
				<option value={st.id}>{$i18n.t(st.name)}</option>
			{/each}
		</select>

		<button
			on:click={() => {
				selectedCourse = 'all';
				selectedStatus = 'all';
				selectedDate = '';
			}}
			class="text-slate-400 dark:text-slate-500 hover:text-red-500 dark:hover:text-red-400 text-xs font-bold flex items-center gap-1.5 transition-colors px-2"
		>
			<span>🔄</span>
			{$i18n.t('Reset')}
		</button>
	</div>

	<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
		{#each [{ label: 'Completion Rate', value: '78.4%', icon: '↗' }, { label: 'ENROLLED STUDENTS', value: '120', trend: '↗ +12%', icon: '' }] as stat}
			<div
				class="bg-white dark:bg-[#111827] p-6 rounded-[28px] border border-slate-100 dark:border-slate-800 shadow-sm flex items-center justify-between transition-all"
			>
				<div>
					<p
						class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em]"
					>
						{$i18n.t(stat.label)}
					</p>
					<h2 class="text-3xl font-black text-slate-800 dark:text-white mt-2">{stat.value}</h2>
					{#if stat.trend}
						<span class="text-green-500 text-xs font-bold mt-1 inline-block">{stat.trend}</span>
					{/if}
				</div>
				
			</div>
		{/each}
	</div>

	<div
		class="bg-white dark:bg-[#111827] rounded-[32px] border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden transition-all"
	>
		<div
			class="p-6 border-b border-slate-50 dark:border-slate-800 flex flex-wrap justify-between items-center gap-4"
		>
			<h2 class="text-lg font-bold text-slate-800 dark:text-slate-50 flex items-center gap-2">
				<span class="w-1.5 h-6 bg-blue-500 rounded-full"></span>
				{$i18n.t('Student List')}
			</h2>
			<div class="relative">
				<span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
				<input
					type="text"
					bind:value={searchQuery}
					placeholder={$i18n.t('Search for a student...')}
					class="pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-[#1e293b] border border-slate-200 dark:border-slate-700 rounded-2xl text-sm text-slate-600 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 w-64 transition-all"
				/>
			</div>
		</div>

		<div class="overflow-x-auto">
			<table class="w-full text-left border-collapse">
				<thead>
					<tr
						class="bg-slate-50/50 dark:bg-[#030712]/30 text-slate-400 dark:text-slate-500 text-[10px] font-black uppercase tracking-[0.15em]"
					>
						<th class="px-6 py-5">{$i18n.t('Student Name')}</th>
						<th class="px-6 py-5">{$i18n.t('Enrollment Date')}</th>
						<th class="px-6 py-5">{$i18n.t('Progress (%)')}</th>
						<th class="px-6 py-5">{$i18n.t('Last Grade')}</th>
						<th class="px-6 py-5">{$i18n.t('Status')}</th>
						<th class="px-6 py-5 text-right">{$i18n.t('Actions')}</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-50 dark:divide-slate-800/50">
					{#each filteredStudents as s}
						<tr class="hover:bg-slate-50/80 dark:hover:bg-[#1e293b]/30 transition-colors group">
							<td class="px-6 py-4 flex items-center gap-3">
								<div
									class="w-9 h-9 rounded-xl bg-blue-600 dark:bg-indigo-600 text-white flex items-center justify-center text-xs font-black shadow-lg shadow-blue-500/20"
								>
									{s.name.charAt(0)}
								</div>
								<span class="text-sm font-bold text-slate-700 dark:text-slate-200 transition-colors"
									>{s.name}</span
								>
							</td>
							<td class="px-6 py-4 text-sm text-slate-500 dark:text-slate-400">{s.date}</td>
							<td class="px-6 py-4">
								<div class="flex items-center gap-3">
									<div
										class="flex-1 h-1.5 bg-slate-100 dark:bg-[#1e293b] rounded-full overflow-hidden"
									>
										<div
											class="h-full bg-blue-500 dark:bg-indigo-500 rounded-full"
											style="width: {s.progress}%"
										></div>
									</div>
									<span class="text-[11px] font-black text-slate-600 dark:text-slate-400"
										>{s.progress}%</span
									>
								</div>
							</td>
							<td class="px-6 py-4 text-sm font-black text-slate-700 dark:text-slate-300"
								>{s.note}</td
							>
							<td class="px-6 py-4">
								<span
									class="px-3 py-1 rounded-full text-[10px] font-black uppercase
                                {s.status === 'Active'
										? 'bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-400'
										: s.status === 'Struggling'
											? 'bg-orange-50 dark:bg-orange-500/10 text-orange-600 dark:text-orange-400'
											: 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400'}"
								>
									{s.status}
								</span>
							</td>
							<td class="px-6 py-4 text-right">
								<div
									class="flex justify-end gap-2 text-slate-400 items-center opacity-40 group-hover:opacity-100 transition-opacity"
								>
									<button
										on:click={() => openMessage(s.name)}
										class="p-2 hover:bg-blue-50 dark:hover:bg-blue-500/10 hover:text-blue-600 rounded-lg transition-all"
										title="Message"
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="h-5 w-5"
											fill="none"
											viewBox="0 0 24 24"
											stroke="currentColor"
											><path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
											/></svg
										>
									</button>
									<button
										on:click={() => viewStudentProfile(s.id || '123')}
										class="p-2 hover:bg-indigo-50 dark:hover:bg-indigo-500/10 hover:text-indigo-600 rounded-lg transition-all"
										title="Profile"
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="h-5 w-5"
											fill="none"
											viewBox="0 0 24 24"
											stroke="currentColor"
											><path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
											/></svg
										>
									</button>
									<div class="relative">
										<button
											on:click|stopPropagation={() => toggleMenu(students.indexOf(s))}
											class="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-all font-black text-lg"
											>⋮</button
										>
										{#if openMenuId === students.indexOf(s)}
											<div
												class="absolute right-0 mt-2 w-56 bg-white dark:bg-[#1e293b] border border-slate-100 dark:border-slate-800 shadow-xl rounded-2xl z-50 overflow-hidden py-2 ring-1 ring-black/5"
											>
												<button
													class="w-full text-left px-4 py-2.5 text-xs font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-3 transition-colors"
												>
													<span>👁️‍🗨️</span>
													{$i18n.t('Hide lesson')}
												</button>
												<button
													class="w-full text-left px-4 py-2.5 text-xs font-bold text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-3 transition-colors"
												>
													<span>🗑️</span>
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
		</div>

		<div
			class="p-5 bg-slate-50/50 dark:bg-[#030712]/20 flex justify-between items-center text-[11px] font-bold text-slate-400 dark:text-slate-500 border-t border-slate-100 dark:border-slate-800/50 transition-all"
		>
			<span>{$i18n.t('Showing 5 of 120 students')}</span>
			<div class="flex gap-2">
				<button
					class="px-4 py-2 bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-all shadow-sm"
					>{$i18n.t('Previous')}</button
				>
				<button
					class="px-4 py-2 bg-blue-600 dark:bg-indigo-600 text-white rounded-xl shadow-lg shadow-blue-500/20"
					>1</button
				>
				<button
					class="px-4 py-2 bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-all"
					>{$i18n.t('Next')}</button
				>
			</div>
		</div>
	</div>
</div>
