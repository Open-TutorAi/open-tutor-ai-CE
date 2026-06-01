<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount, getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { browser } from '$app/environment';

	const i18n = getContext<Writable<i18nType>>('i18n');

	const studentId = $page.params.id;

	let profile: any = null;
	let isLoading = true;
	let isDarkMode = false;

	onMount(async () => {
		if (browser) {
			isDarkMode = localStorage.getItem('theme') === 'dark';
			applyTheme();
		}
		await fetchStudentProfile();
	});

	function applyTheme() {
		if (isDarkMode) {
			document.documentElement.classList.add('dark');
		} else {
			document.documentElement.classList.remove('dark');
		}
	}

	async function fetchStudentProfile() {
		isLoading = true;
		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`/api/v1/teacher/students/${studentId}/profile`, {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				profile = await res.json();
			} else {
				console.error('Failed to fetch student profile');
			}
		} catch (e) {
			console.error('Error fetching student profile:', e);
		} finally {
			isLoading = false;
		}
	}

	// Calculate average progress across courses
	$: avgProgress = profile?.enrolled_courses?.length
		? (profile.enrolled_courses.reduce((acc: number, c: any) => acc + c.progress, 0) / profile.enrolled_courses.length).toFixed(1)
		: '0.0';
</script>

<div class="p-8 space-y-8 bg-[#F8FAFC] dark:bg-[#030712] min-h-screen transition-colors duration-500 text-slate-700 dark:text-slate-200">
	<!-- Top Bar / Back Navigation -->
	<div class="flex items-center justify-between">
		<button
			on:click={() => goto('/teacher/reports')}
			class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-[#111827] border border-slate-100 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 font-bold text-xs shadow-sm transition-all"
		>
			<span>⬅️</span>
			{$i18n.t('Back to Tracking')}
		</button>
		
		<button
			on:click={() => goto(`/teacher/messages?chatId=${studentId}&student=${encodeURIComponent(profile?.name || '')}`)}
			class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-lg shadow-blue-500/20 transition-all"
			disabled={!profile}
		>
			<span>✉️</span>
			{$i18n.t('Send Message')}
		</button>
	</div>

	{#if isLoading}
		<div class="flex flex-col items-center justify-center py-32 space-y-4">
			<div class="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
			<span class="text-sm font-bold text-slate-400 dark:text-slate-500">{$i18n.t('Loading dynamic profile report...')}</span>
		</div>
	{:else if !profile}
		<div class="flex flex-col items-center justify-center py-20 text-center space-y-3 bg-white dark:bg-[#111827] rounded-[32px] border border-slate-100 dark:border-slate-800 p-8 shadow-sm">
			<span class="text-4xl">⚠️</span>
			<h2 class="text-lg font-black text-slate-800 dark:text-slate-100">{$i18n.t('Failed to load profile')}</h2>
			<p class="text-sm text-slate-400 dark:text-slate-500 max-w-sm">
				{$i18n.t('The student profile could not be found or you do not have permission to view it.')}
			</p>
		</div>
	{:else}
		<!-- Profile Summary Card -->
		<div class="bg-white dark:bg-[#111827] p-8 rounded-[32px] border border-slate-100 dark:border-slate-800 shadow-sm flex flex-wrap gap-6 items-center justify-between transition-all">
			<div class="flex items-center gap-5">
				<div class="w-16 h-16 rounded-[22px] bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center text-2xl font-black shadow-lg shadow-blue-500/30">
					{profile.name.charAt(0)}
				</div>
				<div>
					<h1 class="text-2xl font-black text-slate-800 dark:text-white transition-colors">{profile.name}</h1>
					<p class="text-sm text-slate-400 dark:text-slate-500 mt-0.5">{profile.email}</p>
				</div>
			</div>

			<div class="flex gap-4">
				<div class="bg-slate-50 dark:bg-[#1e293b]/30 border border-slate-100/50 dark:border-slate-800 rounded-2xl p-4 min-w-[120px] text-center">
					<span class="text-[10px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-wider">{$i18n.t('Study Footprints')}</span>
					<h3 class="text-2xl font-black text-slate-800 dark:text-white mt-1">{profile.study_footprints_count}</h3>
				</div>
				<div class="bg-slate-50 dark:bg-[#1e293b]/30 border border-slate-100/50 dark:border-slate-800 rounded-2xl p-4 min-w-[120px] text-center">
					<span class="text-[10px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-wider">{$i18n.t('Courses')}</span>
					<h3 class="text-2xl font-black text-slate-800 dark:text-white mt-1">{profile.enrolled_courses.length}</h3>
				</div>
				<div class="bg-slate-50 dark:bg-[#1e293b]/30 border border-slate-100/50 dark:border-slate-800 rounded-2xl p-4 min-w-[120px] text-center">
					<span class="text-[10px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-wider">{$i18n.t('Avg. Progress')}</span>
					<h3 class="text-2xl font-black text-blue-500 mt-1">{avgProgress}%</h3>
				</div>
			</div>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
			<!-- Enrolled Courses -->
			<div class="bg-white dark:bg-[#111827] rounded-[32px] border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden p-6 space-y-6 transition-all">
				<h2 class="text-lg font-black text-slate-800 dark:text-slate-50 flex items-center gap-2">
					<span class="w-1.5 h-6 bg-blue-500 rounded-full"></span>
					{$i18n.t('Course Progress Details')}
				</h2>

				{#if profile.enrolled_courses.length === 0}
					<div class="text-center py-10 text-slate-400 dark:text-slate-500 text-sm">
						{$i18n.t('No enrolled courses active.')}
					</div>
				{:else}
					<div class="space-y-4">
						{#each profile.enrolled_courses as course}
							<div class="p-4 bg-slate-50 dark:bg-[#1e293b]/20 border border-slate-100/50 dark:border-slate-800 rounded-2xl space-y-3">
								<div class="flex justify-between items-center">
									<h4 class="font-extrabold text-sm text-slate-800 dark:text-slate-200 line-clamp-1">{course.title}</h4>
									<span class="text-xs font-black text-blue-500">{course.progress}%</span>
								</div>
								
								<div class="h-2 bg-slate-200/60 dark:bg-[#111827] rounded-full overflow-hidden">
									<div class="h-full bg-blue-500 rounded-full" style="width: {course.progress}%"></div>
								</div>

								<div class="flex justify-between text-[11px] font-bold text-slate-400">
									<span>{$i18n.t('Completed sections')}</span>
									<span>{course.completed_sections} / {course.total_sections}</span>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Quiz Grades -->
			<div class="bg-white dark:bg-[#111827] rounded-[32px] border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden p-6 space-y-6 transition-all">
				<h2 class="text-lg font-black text-slate-800 dark:text-slate-50 flex items-center gap-2">
					<span class="w-1.5 h-6 bg-indigo-500 rounded-full"></span>
					{$i18n.t('Quiz Submissions')}
				</h2>

				{#if profile.quiz_grades.length === 0}
					<div class="text-center py-12 text-slate-400 dark:text-slate-500 text-sm flex flex-col items-center justify-center space-y-2">
						<span class="text-2xl">📝</span>
						<span>{$i18n.t('No quiz submissions registered yet.')}</span>
					</div>
				{:else}
					<div class="overflow-x-auto">
						<table class="w-full text-left border-collapse">
							<thead>
								<tr class="text-slate-400 dark:text-slate-500 text-[10px] font-black uppercase tracking-wider border-b border-slate-100 dark:border-slate-800/80">
									<th class="pb-3">{$i18n.t('Quiz Title')}</th>
									<th class="pb-3 text-center">{$i18n.t('Grade')}</th>
									<th class="pb-3 text-right">{$i18n.t('Date Graded')}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-slate-50 dark:divide-slate-850">
								{#each profile.quiz_grades as grade}
									{@const pct = (grade.score / grade.total_questions) * 100}
									<tr class="hover:bg-slate-50/50 dark:hover:bg-[#1e293b]/10 transition-colors">
										<td class="py-3 text-sm font-bold text-slate-700 dark:text-slate-200 line-clamp-1">{grade.quiz_title}</td>
										<td class="py-3 text-center">
											<span class="px-2.5 py-0.5 rounded-full text-xs font-black
												{pct >= 80
													? 'bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-400'
													: pct >= 50
														? 'bg-orange-50 dark:bg-orange-500/10 text-orange-600 dark:text-orange-400'
														: 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400'}">
												{grade.score} / {grade.total_questions}
											</span>
										</td>
										<td class="py-3 text-right text-xs text-slate-400 dark:text-slate-500 font-medium">{grade.graded_at}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
