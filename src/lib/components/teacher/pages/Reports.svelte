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

	let selectedCourse = '';
	let selectedStatus = 'all';
	let selectedDate = '';

	// Visibility Modal States
	let showHideModal = false;
	let selectedStudentId = '';
	let selectedStudentName = '';

	let statuses = [
		{ id: 'completed', name: 'Completed' },
		{ id: 'in_progress', name: 'In progress' }
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
				channels = data.map((c: any) => ({
					id: c.id,
					name: c.title
				}));

				if (channels.length > 0) {
					selectedCourse = channels[0].id;
					await fetchReports();
				}
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
			if (selectedDate) {
				url += `&date=${selectedDate}`;
			}
			const res = await fetch(url, {
				headers: { Authorization: `Bearer ${token}` }
			});
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

	$: filteredStudents = students.filter((student) =>
		student.name.toLowerCase().includes(searchQuery.toLowerCase())
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

	function handleHideLesson(student: any) {
		selectedStudentId = student.id;
		selectedStudentName = student.name;
		showHideModal = true;
		openMenuId = null;
	}

	let isDarkMode = false;

	onMount(async () => {
		isDarkMode = localStorage.getItem('theme') === 'dark';
		applyTheme();
		await fetchCourses();
		await fetchReports();
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

<!-- نفس الـ <script> ديالك شغال عادي ومريغل بدون أي تغيير ف الـ الـ logic -->

<div
	class="p-8 space-y-6 bg-[#F8FAFC] dark:bg-[#030712] min-h-screen text-slate-800 dark:text-slate-100 font-sans transition-colors duration-500"
>
	<!-- ── 1. HEADER SECTION (MATCHING QUIZ DESIGN) ── -->
	<div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4">
		<div>
			<h1 class="text-3xl font-black tracking-tight text-slate-900 dark:text-white">
				{$i18n.t('Student Tracking')}
			</h1>
			<p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
				{$i18n.t('Analyze student performance and intervene at the right time.')}
			</p>
		</div>

		<!-- 📊 COMPACT STATS CARDS (RIGHT-ALIGNED LIKE IMAGE_DABBBC) -->
		<div class="flex gap-3 w-full md:w-auto overflow-x-auto pb-2 md:pb-0">
			<!-- Card 1: Completion Rate -->
			<div
				class="bg-[#EFF6FF] dark:bg-blue-950/30 border border-[#BFDBFE] dark:border-blue-900/50 rounded-2xl px-5 py-3 min-w-[120px] text-center shadow-sm"
			>
				<span
					class="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider block"
				>
					{completionRate}
				</span>
				<span
					class="text-[11px] font-black text-blue-800 dark:text-blue-300 uppercase tracking-tight block mt-0.5"
				>
					{$i18n.t('TOTAL RATE')}
				</span>
			</div>

			<!-- Card 2: Enrolled Students -->
			<div
				class="bg-[#F0FDF4] dark:bg-emerald-950/30 border border-[#BBF7D0] dark:border-emerald-900/50 rounded-2xl px-5 py-3 min-w-[120px] text-center shadow-sm"
			>
				<div class="flex items-center justify-center gap-1">
					<span
						class="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider"
					>
						{enrolledStudentsCount}
					</span>
					<span class="text-[9px] text-green-500 font-bold">↗</span>
				</div>
				<span
					class="text-[11px] font-black text-emerald-800 dark:text-emerald-300 uppercase tracking-tight block mt-0.5"
				>
					{$i18n.t('ENROLLED')}
				</span>
			</div>
		</div>
	</div>

	<!-- ── 2. COMPACT FILTER BAR ── -->
	<div
		class="flex flex-wrap gap-3 items-center p-3 bg-white dark:bg-[#111827] rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm"
	>
		<div
			class="flex items-center gap-1.5 bg-slate-50 dark:bg-[#1e293b] border border-slate-200/60 dark:border-slate-700/60 rounded-xl px-3 py-1.5"
		>
			<select
				bind:value={selectedCourse}
				class="bg-transparent border-none text-xs font-semibold text-slate-600 dark:text-slate-300 outline-none cursor-pointer"
			>
				{#each channels as ch}
					<option value={ch.id}>{ch.name}</option>
				{/each}
			</select>
		</div>

		<div
			class="flex items-center gap-1.5 bg-slate-50 dark:bg-[#1e293b] border border-slate-200/60 dark:border-slate-700/60 rounded-xl px-3 py-1.5"
		>
			<input
				type="date"
				bind:value={selectedDate}
				class="bg-transparent border-none text-xs font-semibold text-slate-600 dark:text-slate-300 outline-none cursor-pointer"
			/>
		</div>

		<div
			class="flex items-center gap-1.5 bg-slate-50 dark:bg-[#1e293b] border border-slate-200/60 dark:border-slate-700/60 rounded-xl px-3 py-1.5"
		>
			<select
				bind:value={selectedStatus}
				class="bg-transparent border-none text-xs font-semibold text-slate-600 dark:text-slate-300 outline-none cursor-pointer"
			>
				<option value="all">{$i18n.t('All statuses')}</option>
				{#each statuses as st}
					<option value={st.id}>{$i18n.t(st.name)}</option>
				{/each}
			</select>
		</div>

		<button
			on:click={() => {
				selectedCourse = 'all';
				selectedStatus = 'all';
				selectedDate = '';
			}}
			class="text-slate-400 dark:text-slate-500 hover:text-red-500 dark:hover:text-red-400 text-xs font-bold flex items-center gap-1 ml-auto px-2 py-1 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-lg transition-colors"
		>
			<span>🔄</span>
			{$i18n.t('Réinitialiser')}
		</button>
	</div>

	<!-- ── 3. LIST CONTAINER (BOX LOOK LIKE GENERAL INFORMATION) ── -->
	<div
		class="bg-white dark:bg-[#111827] border border-slate-100 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden"
	>
		<!-- Header د الـ قائمة مع الـ البحث -->
		<div
			class="p-5 border-b border-slate-100 dark:border-slate-800 flex flex-wrap justify-between items-center gap-4"
		>
			<div>
				<h2 class="text-sm font-bold text-slate-900 dark:text-slate-50">
					{$i18n.t('Informations des étudiants')}
				</h2>
				<p class="text-[11px] text-slate-400 mt-0.5">
					{$i18n.t('Définissez et suivez la progression globale')}
				</p>
			</div>
			<div class="relative">
				<span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs">🔍</span>
				<input
					type="text"
					bind:value={searchQuery}
					placeholder={$i18n.t('Search for a student...')}
					class="pl-9 pr-4 py-1.5 bg-slate-50 dark:bg-[#1e293b] border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-600 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 w-56 transition-all"
				/>
			</div>
		</div>

		<!-- الأسطر د الـ تلامذ نقيين وملمومين -->
		<div class="divide-y divide-slate-100 dark:divide-slate-800/60 max-h-[480px] overflow-y-auto">
			{#if isLoading}
				<div class="text-center text-slate-400 text-xs py-10">
					✨ {$i18n.t('Loading list...')}
				</div>
			{:else if filteredStudents.length === 0}
				<div class="text-center text-slate-400 text-xs py-10">
					🍃 {$i18n.t('No students found')}
				</div>
			{:else}
				{#each filteredStudents as s, index}
					<div
						class="flex flex-wrap md:flex-nowrap items-center justify-between gap-4 p-4 hover:bg-slate-50/50 dark:hover:bg-slate-800/20 transition-all duration-200 group"
					>
						<!-- الاسم والأفاتار -->
						<div class="flex items-center gap-3 w-full md:w-1/4 min-w-[180px]">
							<div
								class="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center text-xs font-black shadow-sm uppercase"
							>
								{s.name.charAt(0)}
							</div>
							<span
								class="text-xs font-bold text-slate-700 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors"
								>{s.name}</span
							>
						</div>

						<!-- تاريخ الـتسجيل -->
						<div class="text-xs text-slate-400 dark:text-slate-500 font-medium">
							{s.date || '---'}
						</div>

						<!-- الـبروغريس بار رقيق ومفيني -->
						<div class="w-full md:w-1/4 min-w-[140px]">
							<div class="flex items-center gap-2">
								<div class="flex-1 h-1 bg-slate-100 dark:bg-[#1e293b] rounded-full overflow-hidden">
									<div
										class="h-full bg-blue-500 rounded-full transition-all duration-500"
										style="width: {s.progress}%"
									></div>
								</div>
								<span
									class="text-[10px] font-black text-slate-500 dark:text-slate-400 min-w-[24px] text-right"
									>{s.progress}%</span
								>
							</div>
						</div>

						<!-- الـنقطة -->
						<div class="text-center">
							<span
								class="text-xs font-black text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-[#1e293b] px-2 py-0.5 rounded-md border border-slate-100 dark:border-slate-800"
								>{s.note}</span
							>
						</div>

						<!-- الـحالة بـ بادج دائري ناعم -->
						<div class="text-center md:text-left">
							<span
								class="px-2.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider inline-block
                                {s.status.toLowerCase() === 'active' ||
								s.status.toLowerCase() === 'completed'
									? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
									: s.status.toLowerCase() === 'struggling' ||
										  s.status.toLowerCase() === 'in progress'
										? 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
										: 'bg-rose-500/10 text-rose-600 dark:text-rose-400'}"
							>
								{s.status}
							</span>
						</div>

						<!-- الـتحكم (الأكشنز) -->
						<div class="w-full md:w-auto flex justify-end gap-1 text-slate-400 items-center">
							<!-- الـ 3 نقاط -->
							<div class="relative">
								<button
									on:click|stopPropagation={() => toggleMenu(index)}
									class="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors font-black text-sm text-slate-500"
									>⋮</button
								>
								{#if openMenuId === index}
									<div
										class="absolute right-0 mt-1 w-44 bg-white dark:bg-[#1e293b] border border-slate-100 dark:border-slate-800 shadow-xl rounded-xl z-50 overflow-hidden py-1 ring-1 ring-black/5"
									>
										<button
											on:click|stopPropagation={() => handleHideLesson(s)}
											class="w-full text-left px-4 py-2 text-xs font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2 transition-colors"
										>
											<span>👁️‍🗨️</span>
											{$i18n.t('Hide lesson')}
										</button>
									</div>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			{/if}
		</div>

		<!-- الـ Pagination بـ نفس الـ روح -->
		<div
			class="p-3 bg-slate-50 dark:bg-[#111827] border-t border-slate-100 dark:border-slate-800 flex justify-between items-center text-[11px] font-bold text-slate-400 dark:text-slate-500"
		>
			<span>{$i18n.t('Showing {{count}} students', { count: filteredStudents.length })}</span>
			<div class="flex gap-1">
				<button
					class="px-2.5 py-1 bg-white dark:bg-[#1e293b] border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
					>{$i18n.t('Previous')}</button
				>
				<button class="px-2.5 py-1 bg-blue-600 text-white rounded-lg font-black shadow-sm">1</button
				>
				<button
					class="px-2.5 py-1 bg-white dark:bg-[#1e293b] border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
					>{$i18n.t('Next')}</button
				>
			</div>
		</div>
	</div>
</div>

<HideLessonsModal
	bind:show={showHideModal}
	studentId={selectedStudentId}
	studentName={selectedStudentName}
/>

<style>
	/* Custom mini-scrollbar alignment */
	::-webkit-scrollbar {
		width: 4px;
	}
	::-webkit-scrollbar-thumb {
		background: #cbd5e1;
		border-radius: 10px;
	}
	:global(.dark) ::-webkit-scrollbar-thumb {
		background: #334155;
	}
</style>
