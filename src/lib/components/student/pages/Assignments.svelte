<script lang="ts">
	import { getContext } from 'svelte';
	import { isDemo, demoData, user } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	const i18n = getContext<Writable<i18nType>>('i18n');
	
	$: assignments = $isDemo ? $demoData.assignments : [];
	
	$: upcomingDeadlines = assignments.filter(a => ['pending', 'in-progress', 'overdue'].includes(a.status)).length;
	
	$: username = $user?.name ? $user.name.split(' ')[0] : 'Student';

	function getTopBorderColor(status: string) {
		switch (status) {
			case 'completed': return 'bg-green-500';
			case 'in-progress': return 'bg-blue-500';
			case 'overdue': return 'bg-red-500';
			case 'pending':
			default: return 'bg-gray-400';
		}
	}
	
	function getButtonProps(status: string) {
		switch (status) {
			case 'completed': 
				return { text: 'View Feedback', class: 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 shadow-sm' };
			case 'in-progress': 
				return { text: 'Continue', class: 'bg-blue-500 text-white hover:bg-blue-600 shadow-sm shadow-blue-500/30' };
			case 'overdue': 
				return { text: 'Submit Late', class: 'bg-blue-500 text-white hover:bg-blue-600 shadow-sm shadow-blue-500/30' };
			case 'pending':
			default: 
				return { text: 'Start', class: 'bg-blue-500 text-white hover:bg-blue-600 shadow-sm shadow-blue-500/30' };
		}
	}
	
	function handleSubmit(assignment: any) {
		if ($isDemo) {
			toast.info($i18n.t('Submissions are disabled in demo mode'));
		} else {
			toast.info($i18n.t('Submission functionality coming soon'));
		}
	}
</script>

<div class="h-full flex flex-col p-4 md:p-0">
	<div class="bg-white dark:bg-gray-900 md:rounded-[2rem] p-8 md:p-10 shadow-sm flex-1 max-w-[1400px] w-full mx-auto flex flex-col border border-gray-100 dark:border-gray-800">
		
		<!-- Welcome Section -->
		<div class="mb-10 text-center md:text-left">
			<h1 class="text-[2rem] font-medium text-slate-700 dark:text-white mb-2 tracking-tight">
				{$i18n.t('Welcome back')}, {username}!
			</h1>
			<p class="text-slate-500 dark:text-gray-400 text-[15px]">
				{$i18n.t('You have {{count}} upcoming deadlines this week. Stay focused and keep learning !', { count: upcomingDeadlines })}
			</p>
		</div>

		<!-- Filters & Title -->
		<div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
			<h2 class="text-xl font-medium text-slate-700 dark:text-white tracking-tight">{$i18n.t('My Assignments')}</h2>
			
			<div class="flex flex-wrap items-center gap-3 w-full md:w-auto">
				<div class="relative flex-1 md:flex-none">
					<select class="w-full appearance-none bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 py-2 pl-4 pr-10 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm shadow-sm transition-shadow hover:shadow">
						<option>{$i18n.t('All Subjects')}</option>
						<option>{$i18n.t('Mathematics')}</option>
						<option>{$i18n.t('Science')}</option>
					</select>
					<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-400">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
					</div>
				</div>

				<div class="relative flex-1 md:flex-none">
					<select class="w-full appearance-none bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 py-2 pl-4 pr-10 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm shadow-sm transition-shadow hover:shadow">
						<option>{$i18n.t('All Status')}</option>
						<option>{$i18n.t('Pending')}</option>
						<option>{$i18n.t('Completed')}</option>
					</select>
					<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-400">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
					</div>
				</div>

				<button class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 py-2 px-6 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm shadow-sm hover:shadow">
					{$i18n.t('Filter')}
				</button>
			</div>
		</div>

		<!-- Grid -->
		{#if assignments.length > 0}
			<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mb-10">
				{#each assignments as assignment (assignment.id)}
					<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.06)] overflow-hidden flex flex-col h-[260px] relative border border-gray-100 dark:border-gray-700 transition-transform hover:-translate-y-1 duration-300">
						<!-- Top colored bar -->
						<div class="h-3 w-full {getTopBorderColor(assignment.status)}"></div>
						
						<div class="p-6 flex flex-col flex-1">
							<!-- Subject & Points -->
							<div class="flex justify-between items-center mb-4">
								<span class="bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 text-xs font-medium px-3 py-1 rounded-md">
									{assignment.course}
								</span>
								<span class="text-gray-400 dark:text-gray-500 text-xs font-medium">
									{assignment.points} {$i18n.t('points')}
								</span>
							</div>

							<!-- Title & Description -->
							<h3 class="text-slate-700 dark:text-gray-100 font-semibold text-[15px] mb-2 line-clamp-1">
								{assignment.title}
							</h3>
							<p class="text-gray-500 dark:text-gray-400 text-[13px] leading-relaxed line-clamp-3 mb-4 flex-1">
								{assignment.description}
							</p>

							<!-- Footer separator -->
							<div class="w-full h-px bg-gray-100 dark:bg-gray-700 mt-auto mb-4"></div>

							<!-- Footer -->
							<div class="flex justify-between items-center mt-auto">
								<span class="text-gray-400 dark:text-gray-500 text-xs">
									{#if assignment.status === 'completed'}
										{$i18n.t('Completed')}: {assignment.due}
									{:else if assignment.status === 'overdue'}
										{$i18n.t('Due')}: {assignment.due} ({$i18n.t('Late')})
									{:else}
										{$i18n.t('Due')}: {assignment.due}
									{/if}
								</span>
								
								<button 
									on:click={() => handleSubmit(assignment)}
									class="px-4 py-2 rounded-lg text-xs font-medium transition-all {getButtonProps(assignment.status).class}"
								>
									{$i18n.t(getButtonProps(assignment.status).text)}
								</button>
							</div>
						</div>
					</div>
				{/each}
			</div>

			<!-- Pagination -->
			<div class="flex justify-between items-center mt-auto pt-4 pb-2 px-2">
				<button class="text-gray-300 dark:text-gray-600 text-sm font-medium hover:text-gray-500 transition-colors" disabled>
					{$i18n.t('Back')}
				</button>
				<button class="text-gray-300 dark:text-gray-600 text-sm font-medium hover:text-gray-500 transition-colors" disabled>
					{$i18n.t('Next')}
				</button>
			</div>
		{:else}
			<div class="bg-gray-50 dark:bg-gray-800/50 rounded-2xl border border-dashed border-gray-200 dark:border-gray-700 p-12 text-center mt-6 flex-1 flex flex-col justify-center items-center">
				<div class="w-16 h-16 bg-white dark:bg-gray-700 rounded-full flex items-center justify-center mb-4 shadow-sm">
					<svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path></svg>
				</div>
				<h3 class="text-lg font-medium text-slate-700 dark:text-white mb-2">{$i18n.t('No assignments right now')}</h3>
				<p class="text-gray-500 dark:text-gray-400 max-w-sm mb-6">
					{$i18n.t('You are all caught up! Enable demo mode to see sample assignments or check back later.')}
				</p>
			</div>
		{/if}
	</div>
</div>
