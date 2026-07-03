<!-- Onglet Performance: Statistiques matières + Jauge + Calendrier -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { isDemo } from '$lib/stores';
	import {
		getDashboardStatistics,
		getDashboardPerformance,
		getDashboardCalendar,
		type SubjectStat,
		type PerformanceData,
		type CalendarData
	} from '$lib/apis/dashboard';
	import PerformanceGauge from './PerformanceGauge.svelte';
	import ActivityCalendar from './ActivityCalendar.svelte';

	type Period = 'monthly' | 'weekly';
	let period: Period = 'monthly';
	let calYear = new Date().getFullYear();
	let calMonth = new Date().getMonth() + 1;
	let weekStartDate: string | undefined = undefined;

	let subjects: SubjectStat[] = [];
	let performance: PerformanceData = {
		completion_rate: 0,
		tutorials_completed: 0,
		total_tutorials: 0,
		total_points: 0
	};
	let calendar: CalendarData = { year: calYear, month: calMonth, active_days: [] };
	let loading = true;
	let statsLoading = false; // pour les refreshes partiels

	const SUBJECT_COLORS = [
		{ bar: 'bg-blue-500', text: 'text-blue-600', light: 'bg-blue-50 dark:bg-blue-900/20', dot: 'bg-blue-500' },
		{ bar: 'bg-green-500', text: 'text-green-600', light: 'bg-green-50 dark:bg-green-900/20', dot: 'bg-green-500' },
		{ bar: 'bg-orange-400', text: 'text-orange-500', light: 'bg-orange-50 dark:bg-orange-900/20', dot: 'bg-orange-400' },
		{ bar: 'bg-red-400', text: 'text-red-500', light: 'bg-red-50 dark:bg-red-900/20', dot: 'bg-red-400' },
		{ bar: 'bg-purple-500', text: 'text-purple-600', light: 'bg-purple-50 dark:bg-purple-900/20', dot: 'bg-purple-500' }
	];

	// ── Demo data ─────────────────────────────────────────────────────────────
	const DEMO_SUBJECTS_ALL: SubjectStat[] = [
		{ subject: 'Mathématiques', percentage: 80, total_count: 5 },
		{ subject: 'Physique', percentage: 50, total_count: 4 },
		{ subject: 'Algorithmique', percentage: 85, total_count: 6 },
		{ subject: 'Chimie', percentage: 40, total_count: 3 }
	];
	const DEMO_SUBJECTS_MONTHLY: SubjectStat[] = [
		{ subject: 'Mathématiques', percentage: 75, total_count: 2 },
		{ subject: 'Physique', percentage: 50, total_count: 2 },
		{ subject: 'Algorithmique', percentage: 100, total_count: 1 },
		{ subject: 'Chimie', percentage: 0, total_count: 1 }
	];
	const DEMO_SUBJECTS_WEEKLY: SubjectStat[] = [
		{ subject: 'Mathématiques', percentage: 100, total_count: 1 },
		{ subject: 'Algorithmique', percentage: 50, total_count: 2 }
	];
	const DEMO_PERF_ALL: PerformanceData = {
		completion_rate: 85,
		tutorials_completed: 20,
		total_tutorials: 24,
		total_points: 24 * 5 + 20 * 100
	};
	const DEMO_PERF_MONTHLY: PerformanceData = {
		completion_rate: 75,
		tutorials_completed: 6,
		total_tutorials: 8,
		total_points: 8 * 5 + 6 * 100
	};
	const DEMO_PERF_WEEKLY: PerformanceData = {
		completion_rate: 66,
		tutorials_completed: 2,
		total_tutorials: 3,
		total_points: 3 * 5 + 2 * 100
	};
	const DEMO_ACTIVE_DAYS = [1, 3, 5, 8, 9, 10, 13, 15, 17, 20, 22, 24, 27, 28];

	// ── Period label for display ────────────────────────────────────────────────
	const MONTHS_FR = [
		'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
		'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
	];
	$: periodLabel = period === 'monthly'
		? MONTHS_FR[calMonth - 1] + ' ' + calYear
		: weekStartDate
			? 'Semaine du ' + new Date(weekStartDate + 'T00:00:00').toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
			: '';

	// ── ISO date helpers ───────────────────────────────────────────────────────
	function todayISO(): string {
		const now = new Date();
		return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
	}

	// ── Data loading ───────────────────────────────────────────────────────────
	async function loadAll() {
		if ($isDemo) {
			subjects = DEMO_SUBJECTS_ALL;
			performance = DEMO_PERF_ALL;
			calendar = { year: calYear, month: calMonth, active_days: DEMO_ACTIVE_DAYS };
			loading = false;
			return;
		}
		const token = localStorage.getItem('token');
		if (!token) { loading = false; return; }
		try {
			[subjects, performance, calendar] = await Promise.all([
				getDashboardStatistics(token),
				getDashboardPerformance(token),
				getDashboardCalendar(token, calYear, calMonth)
			]);
		} catch (e) {
			console.error('Performance data fetch failed', e);
		} finally {
			loading = false;
		}
	}

	// Re-fetch stats + performance for a given date range (monthly or weekly)
	async function refreshStatsAndPerf(opts: { year?: number; month?: number; startDate?: string }) {
		if ($isDemo) {
			if (opts.startDate) {
				subjects = DEMO_SUBJECTS_WEEKLY;
				performance = DEMO_PERF_WEEKLY;
			} else {
				subjects = DEMO_SUBJECTS_MONTHLY;
				performance = DEMO_PERF_MONTHLY;
			}
			return;
		}
		const token = localStorage.getItem('token');
		if (!token) return;
		statsLoading = true;
		try {
			[subjects, performance] = await Promise.all([
				getDashboardStatistics(token, opts),
				getDashboardPerformance(token, opts)
			]);
		} catch (e) {
			console.error('Stats refresh failed', e);
		} finally {
			statsLoading = false;
		}
	}

	// ── Calendar handlers ──────────────────────────────────────────────────────
	async function onMonthChange(y: number, m: number) {
		calYear = y;
		calMonth = m;
		if ($isDemo) {
			calendar = { year: y, month: m, active_days: DEMO_ACTIVE_DAYS };
		} else {
			const token = localStorage.getItem('token');
			if (token) {
				try { calendar = await getDashboardCalendar(token, y, m); } catch {}
			}
		}
		// If in monthly mode, also refresh stats for this new month
		if (period === 'monthly') {
			await refreshStatsAndPerf({ year: y, month: m });
		}
	}

	async function onWeekChange(startDate: string) {
		weekStartDate = startDate;
		const d = new Date(startDate + 'T00:00:00');
		if ($isDemo) {
			calendar = { year: calYear, month: calMonth, active_days: [0, 2, 4], week_start: startDate };
		} else {
			const token = localStorage.getItem('token');
			if (token) {
				try {
					calendar = await getDashboardCalendar(token, d.getFullYear(), d.getMonth() + 1, startDate);
				} catch {}
			}
		}
		// Refresh stats for this week
		await refreshStatsAndPerf({ startDate });
	}

	async function onPeriodChange(p: Period) {
		period = p;
		if (p === 'monthly') {
			// Reset to all-time or current month
			if ($isDemo) {
				subjects = DEMO_SUBJECTS_MONTHLY;
				performance = DEMO_PERF_MONTHLY;
			} else {
				await refreshStatsAndPerf({ year: calYear, month: calMonth });
			}
		} else {
			// Weekly: if no week selected yet, use today
			if (!weekStartDate) {
				weekStartDate = todayISO();
				await onWeekChange(weekStartDate);
			} else {
				await refreshStatsAndPerf({ startDate: weekStartDate });
			}
		}
	}

	onMount(loadAll);
</script>

{#if loading}
	<div class="flex justify-center items-center py-16">
		<div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
	</div>
{:else}
	<div class="grid grid-cols-1 xl:grid-cols-3 gap-4">

		<!-- ── Carte Statistiques ── -->
		<div class="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm relative">
			<div class="flex items-center justify-between mb-1">
				<h2 class="text-base font-semibold text-gray-800 dark:text-white">Statistiques</h2>
				{#if periodLabel}
					<span class="text-xs text-blue-600 dark:text-blue-400 font-medium bg-blue-50 dark:bg-blue-900/20 px-2 py-0.5 rounded-full">{periodLabel}</span>
				{/if}
			</div>

			{#if statsLoading}
				<div class="absolute inset-0 flex items-center justify-center bg-white/70 dark:bg-gray-800/70 rounded-2xl z-10">
					<div class="animate-spin w-6 h-6 border-3 border-blue-500 border-t-transparent rounded-full"></div>
				</div>
			{/if}

			<div class="space-y-4 mt-3">
				{#if subjects.length === 0}
					<p class="text-sm text-gray-400 dark:text-gray-500 text-center py-4">
						Aucun soutien {period === 'weekly' ? 'cette semaine' : 'ce mois'}
					</p>
				{:else}
					{#each subjects as s, i}
						{@const color = SUBJECT_COLORS[i % SUBJECT_COLORS.length]}
						<div class="space-y-1.5">
							<div class="flex items-center justify-between">
								<div class="flex items-center gap-2">
									<span class="w-2.5 h-2.5 rounded-sm {color.bar} flex-shrink-0"></span>
									<span class="text-sm text-gray-700 dark:text-gray-200">{s.subject}</span>
								</div>
								<span class="text-sm font-semibold {color.text}">{s.percentage}%</span>
							</div>
							<div class="h-2 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
								<div
									class="h-full rounded-full {color.bar} transition-all duration-700"
									style="width: {s.percentage}%"
								></div>
							</div>
						</div>
					{/each}
				{/if}
			</div>

			<!-- Séparation avant taux de complétion -->
			<div class="mt-5 pt-4 border-t border-gray-100 dark:border-gray-700">
				<!-- Cercle taux de complétion -->
				<div class="flex items-center gap-4 mb-4">
					<div class="relative w-20 h-20 flex-shrink-0">
						<svg class="-rotate-90 absolute inset-0" viewBox="0 0 80 80">
							<circle cx="40" cy="40" r="34" fill="none" stroke="#e5e7eb" stroke-width="8"
								class="dark:stroke-gray-700" />
							<circle
								cx="40" cy="40" r="34"
								fill="none" stroke="#3b82f6" stroke-width="8" stroke-linecap="round"
								stroke-dasharray={2 * Math.PI * 34}
								stroke-dashoffset={2 * Math.PI * 34 * (1 - performance.completion_rate / 100)}
								style="transition: stroke-dashoffset 1s ease;"
							/>
						</svg>
						<div class="absolute inset-0 flex flex-col items-center justify-center">
							<span class="text-base font-bold text-gray-800 dark:text-white">{performance.completion_rate}%</span>
							<span class="text-[8px] text-gray-400 dark:text-gray-500 leading-tight text-center">Taux</span>
						</div>
					</div>
					<div>
						<p class="text-xs text-gray-500 dark:text-gray-400">Taux de complétion</p>
						<p class="text-sm font-semibold text-gray-800 dark:text-white mt-0.5">
							{performance.tutorials_completed} / {performance.total_tutorials} terminés
						</p>
					</div>
				</div>

				<!-- Tableau soutiens par matière -->
				{#if subjects.length > 0}
					<p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Soutiens créés par matière</p>
					<div class="space-y-1.5">
						{#each subjects as s, i}
							{@const color = SUBJECT_COLORS[i % SUBJECT_COLORS.length]}
							<div class="flex items-center justify-between py-1 px-2 rounded-lg {color.light}">
								<div class="flex items-center gap-2">
									<span class="w-2 h-2 rounded-full {color.dot}"></span>
									<span class="text-xs text-gray-700 dark:text-gray-200 font-medium">{s.subject}</span>
								</div>
								<span class="text-xs font-bold {color.text}">
									{s.total_count ?? 0} soutien{(s.total_count ?? 0) !== 1 ? 's' : ''}
								</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- ── Carte Performance (jauge) ── -->
		<div class="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm flex flex-col relative">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-base font-semibold text-gray-800 dark:text-white">Performance</h2>
				{#if periodLabel}
					<span class="text-xs text-blue-600 dark:text-blue-400 font-medium bg-blue-50 dark:bg-blue-900/20 px-2 py-0.5 rounded-full">{periodLabel}</span>
				{/if}
			</div>

			{#if statsLoading}
				<div class="absolute inset-0 flex items-center justify-center bg-white/70 dark:bg-gray-800/70 rounded-2xl z-10">
					<div class="animate-spin w-6 h-6 border-3 border-blue-500 border-t-transparent rounded-full"></div>
				</div>
			{/if}

			<div class="flex items-center gap-2 mb-3">
				<span class="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
				<span class="text-xs text-gray-500 dark:text-gray-400">Taux de complétion</span>
			</div>

			<div class="flex-1 flex items-center justify-center">
				<PerformanceGauge
					value={performance.completion_rate}
					count={performance.tutorials_completed}
					countLabel="Tutoriels terminés"
					totalPoints={performance.total_points ?? 0}
				/>
			</div>
		</div>

		<!-- ── Calendrier + filtre Mensuel/Hebdo ── -->
		<ActivityCalendar
			activeDays={calendar.active_days}
			year={calYear}
			month={calMonth}
			weekStart={weekStartDate}
			{period}
			{onMonthChange}
			{onWeekChange}
			{onPeriodChange}
		/>

	</div>
{/if}
