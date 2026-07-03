<!-- Onglet Productivité: Série + Sessions + Heures + Graphique + Mode Focus -->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { get } from 'svelte/store';
	import { isDemo } from '$lib/stores';
	import { getDashboardProductivity, type ProductivityData } from '$lib/apis/dashboard';
	import { focusTimer } from '$lib/stores/focusTimer';
	import StudyHoursChart from './StudyHoursChart.svelte';
	import FocusTimer from './FocusTimer.svelte';

	let data: ProductivityData = {
		streak: 0,
		total_sessions: 0,
		weekly_hours: 0,
		daily_hours: []
	};
	let loading = true;

	// Demo fallback
	const DEMO_DATA: ProductivityData = {
		streak: 5,
		total_sessions: 4,
		weekly_hours: 14,
		daily_hours: [
			{ day: 'Lun', hours: 2 },
			{ day: 'Mar', hours: 3 },
			{ day: 'Mer', hours: 1 },
			{ day: 'Jeu', hours: 4 },
			{ day: 'Ven', hours: 2.5 },
			{ day: 'Sam', hours: 1.5 },
			{ day: 'Dim', hours: 0 }
		]
	};

	const WEEK_DAYS = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];

	async function refreshProductivityData() {
		if ($isDemo) {
			data = { ...data, total_sessions: $focusTimer.sessionsCompleted };
			return;
		}
		const token = localStorage.getItem('token');
		if (!token) return;
		try {
			data = await getDashboardProductivity(token);
		} catch {}
	}

	let unsubscribeFocus: (() => void) | null = null;

	onMount(async () => {
		if ($isDemo) {
			data = DEMO_DATA;
			loading = false;
		} else {
			const token = localStorage.getItem('token');
			if (token) {
				try {
					data = await getDashboardProductivity(token);
				} catch (e) {
					console.error('Productivity fetch failed', e);
				}
			}
			loading = false;
		}

		// Watch for new completed sessions while component is mounted
		let prevSessions = get(focusTimer).sessionsCompleted;
		unsubscribeFocus = focusTimer.subscribe(($ft) => {
			if ($ft.sessionsCompleted > prevSessions) {
				prevSessions = $ft.sessionsCompleted;
				refreshProductivityData();
			}
		});
	});

	onDestroy(() => {
		if (unsubscribeFocus) unsubscribeFocus();
	});

	// Build streak dots (Mon–Sun): true = studied that day
	$: streakDots = (() => {
		const today = new Date();
		return WEEK_DAYS.map((_, i) => {
			const diff = (today.getDay() === 0 ? 6 : today.getDay() - 1) - i;
			return diff >= 0 && diff < data.streak;
		});
	})();
</script>

{#if loading}
	<div class="flex justify-center items-center py-16">
		<div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
	</div>
{:else}
	<div class="space-y-4">

		<!-- ── Ligne 1: 3 stat cards ── -->
		<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
			<!-- Série -->
			<div class="bg-white dark:bg-gray-800 rounded-2xl p-4 shadow-sm">
				<div class="flex items-center justify-between mb-2">
					<p class="text-xs font-medium text-gray-500 dark:text-gray-400">Série</p>
					<span class="text-lg">🔥</span>
				</div>
				<p class="text-2xl font-bold text-gray-800 dark:text-white">{data.streak} <span class="text-sm font-normal text-gray-500">jours</span></p>
				<!-- Week dots -->
				<div class="flex gap-1.5 mt-3">
					{#each WEEK_DAYS as label, i}
						<div class="flex flex-col items-center gap-0.5">
							<div
								class="w-6 h-6 rounded-full flex items-center justify-center text-[9px]
									{streakDots[i]
										? 'bg-orange-400 text-white'
										: 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500'}"
							>{label}</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Sessions réussies -->
			<div class="bg-white dark:bg-gray-800 rounded-2xl p-4 shadow-sm">
				<div class="flex items-center justify-between mb-2">
					<p class="text-xs font-medium text-gray-500 dark:text-gray-400">Sessions réussies</p>
					<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-green-500" viewBox="0 0 24 24" fill="none"
						stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<polyline points="20 6 9 17 4 12" />
					</svg>
				</div>
				<p class="text-2xl font-bold text-gray-800 dark:text-white">{data.total_sessions}</p>
				<p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Pomodoros complétés aujourd'hui</p>
			</div>

			<!-- Cette semaine -->
			<div class="bg-white dark:bg-gray-800 rounded-2xl p-4 shadow-sm">
				<div class="flex items-center justify-between mb-2">
					<p class="text-xs font-medium text-gray-500 dark:text-gray-400">Cette semaine</p>
					<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-blue-500" viewBox="0 0 24 24" fill="none"
						stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
					</svg>
				</div>
				<p class="text-2xl font-bold text-gray-800 dark:text-white">
					{data.weekly_hours} <span class="text-sm font-normal text-gray-500">h</span>
				</p>
				<p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Temps d'étude total</p>
			</div>
		</div>

		<!-- ── Ligne 2: Graphique + Mode Focus ── -->
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
			<!-- Graphique heures d'étude -->
			<div class="lg:col-span-2 bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm">
				<div class="flex items-center justify-between mb-4">
					<h2 class="text-base font-semibold text-gray-800 dark:text-white">Heures d'étude</h2>
					<span class="text-xs text-gray-400 dark:text-gray-500">Cette semaine</span>
				</div>
				<StudyHoursChart data={data.daily_hours} />
			</div>

			<!-- Pomodoro / Mode Focus (state lives in global store) -->
			<FocusTimer />
		</div>

	</div>
{/if}
