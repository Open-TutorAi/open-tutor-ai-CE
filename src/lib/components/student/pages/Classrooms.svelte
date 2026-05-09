<script lang="ts">
	import { getContext } from 'svelte';
	import { isDemo, demoData, user } from '$lib/stores';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	const i18n = getContext<Writable<i18nType>>('i18n');
	
	// Always show demo data for now to view the design
	$: courses = $demoData.courses || [];
	$: username = $user?.name ? $user.name.split(' ')[0] : 'Karim'; // Using Karim as requested

	// Styling map for courses to match the design (gradients, icons, colors)
	const courseStyles: Record<string, any> = {
		'demo-course-1': {
			gradient: 'bg-gradient-to-tr from-[#E8A0E8] to-[#FFD1FF]', // Pinkish
			icon: 'cpu',
			textColor: 'text-[#E8A0E8]',
			avatarBg: 'bg-[#E8A0E8]',
			buttonBg: 'bg-[#0ea5e9]'
		},
		'demo-course-2': {
			gradient: 'bg-gradient-to-tr from-[#00F2FE] to-[#4FACFE]', // Cyan
			icon: 'book',
			textColor: 'text-[#4FACFE]',
			avatarBg: 'bg-[#4FACFE]',
			buttonBg: 'bg-[#0ea5e9]'
		},
		'demo-course-3': {
			gradient: 'bg-gradient-to-tr from-[#42E695] to-[#3BB2B8]', // Green
			icon: 'calculator',
			textColor: 'text-[#42E695]',
			avatarBg: 'bg-[#42E695]',
			buttonBg: 'bg-[#0ea5e9]'
		},
		'demo-course-4': {
			gradient: 'bg-gradient-to-tr from-[#F6D365] to-[#FDA085]', // Orange/Yellow
			icon: 'chart',
			textColor: 'text-[#FDA085]',
			avatarBg: 'bg-[#FDA085]',
			buttonBg: 'bg-[#0ea5e9]'
		}
	};

	function getStyle(id: string) {
		return courseStyles[id] || courseStyles['demo-course-2'];
	}
</script>

<div class="h-full flex flex-col p-4 md:p-8 flex-1 max-w-[1400px] w-full mx-auto font-sans">
	
	<!-- Welcome Section -->
	<div class="mb-8 text-center md:text-left">
		<h1 class="text-[2rem] font-bold text-slate-800 dark:text-white mb-1 tracking-tight">
			{$i18n.t('Hello')} {username}
		</h1>
		<p class="text-slate-500 dark:text-gray-400 text-[15px] font-medium">
			{$i18n.t("Let's learn something new today!")}
		</p>
	</div>

	<!-- Main Dark Wrapper -->
	<div class="bg-white dark:bg-[#27272a] rounded-[2rem] p-8 md:p-10 shadow-sm flex-1 flex flex-col border border-gray-100 dark:border-gray-800">
		
		<!-- Filters & Title -->
		<div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
			<h2 class="text-[22px] font-bold text-slate-800 dark:text-white tracking-tight">{$i18n.t('My Courses')}</h2>
			
			<div class="flex flex-wrap items-center gap-4 w-full md:w-auto">
				<!-- Search -->
				<div class="relative w-full md:w-[320px]">
					<div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
						<svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
					</div>
					<input type="text" placeholder="Rechercher un cours ou professe" class="block w-full pl-11 pr-4 py-2.5 bg-gray-50 dark:bg-[#3f3f46] border border-gray-200 dark:border-transparent rounded-full leading-5 text-slate-800 dark:text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0ea5e9] sm:text-sm transition duration-150 shadow-sm" />
				</div>

				<!-- Subject Dropdown -->
				<div class="relative flex-1 md:flex-none">
					<select class="w-full md:w-[160px] appearance-none bg-gray-50 dark:bg-[#3f3f46] border border-gray-200 dark:border-transparent text-slate-700 dark:text-gray-200 py-2.5 pl-5 pr-10 rounded-full focus:outline-none focus:ring-2 focus:ring-[#0ea5e9] text-sm font-medium shadow-sm transition-shadow cursor-pointer">
						<option>{$i18n.t('All Subjects')}</option>
						<option>{$i18n.t('Mathematics')}</option>
						<option>{$i18n.t('Science')}</option>
					</select>
					<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-400">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
					</div>
				</div>
			</div>
		</div>

		<!-- Grid -->
		{#if courses.length > 0}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 gap-y-8">
				{#each courses as course (course.id)}
					{@const style = getStyle(course.id)}
					<div class="bg-gray-50 dark:bg-[#3f3f46] rounded-[1.5rem] shadow-sm flex flex-col relative transition-transform hover:-translate-y-1 duration-300 group border border-gray-100 dark:border-gray-800">
						
						<!-- Top Half: Gradient with Icon -->
						<div class="h-[140px] w-full rounded-t-[1.5rem] {style.gradient} flex items-center justify-center relative overflow-hidden">
							{#if style.icon === 'cpu'}
								<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" class="w-24 h-24 text-white opacity-40"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>
							{:else if style.icon === 'book'}
								<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" class="w-24 h-24 text-white opacity-40"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
							{:else if style.icon === 'calculator'}
								<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" class="w-24 h-24 text-white opacity-40"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
							{:else}
								<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" class="w-24 h-24 text-white opacity-40"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
							{/if}
						</div>
						
						<!-- Teacher Pill -->
						<div class="absolute top-[124px] left-6 bg-white dark:bg-[#3f3f46] border-4 border-gray-50 dark:border-[#3f3f46] pl-0.5 pr-3 py-0.5 rounded-full flex items-center gap-2 shadow-sm z-10">
							<div class="w-6 h-6 rounded-full {style.avatarBg} text-white flex items-center justify-center text-[10px] font-bold">
								{course.teacher.charAt(0)}
							</div>
							<span class="text-[11px] font-bold text-slate-800 dark:text-white leading-none pb-px">{course.teacher}</span>
						</div>
						
						<!-- Bottom Half -->
						<div class="px-6 pb-6 pt-10 flex flex-col flex-1">
							<!-- Title -->
							<h3 class="text-slate-800 dark:text-white font-bold text-[16px] mb-8 leading-snug line-clamp-2">
								{course.name}
							</h3>

							<!-- Footer -->
							<div class="flex justify-between items-center mt-auto">
								<span class="text-[13px] font-bold {style.textColor}">
									{$i18n.t(course.level || 'Beginner')}
								</span>
								
								<button class="{style.buttonBg} text-white hover:opacity-90 shadow-sm shadow-[#0ea5e9]/20 px-6 py-2.5 rounded-xl text-sm font-bold transition-opacity">
									{$i18n.t('Start')}
								</button>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<div class="bg-gray-50 dark:bg-[#3f3f46]/50 rounded-2xl border border-dashed border-gray-200 dark:border-gray-700 p-12 text-center mt-6 flex-1 flex flex-col justify-center items-center">
				<div class="w-16 h-16 bg-white dark:bg-[#27272a] rounded-full flex items-center justify-center mb-4 shadow-sm">
					<svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
				</div>
				<h3 class="text-lg font-medium text-slate-700 dark:text-white mb-2">{$i18n.t('No courses available')}</h3>
				<p class="text-gray-500 dark:text-gray-400 max-w-sm mb-6">
					{$i18n.t('Enable demo mode to see sample courses.')}
				</p>
			</div>
		{/if}
	</div>
</div>
