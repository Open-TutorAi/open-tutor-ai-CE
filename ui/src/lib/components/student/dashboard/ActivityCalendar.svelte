<!-- Calendrier mensuel / hebdomadaire avec filtre et indicateurs d'activité -->
<script lang="ts">
	export let activeDays: number[] = [];
	export let year: number = new Date().getFullYear();
	export let month: number = new Date().getMonth() + 1; // 1–12
	export let weekStart: string | undefined = undefined; // ISO date for weekly mode
	export let onMonthChange: (year: number, month: number) => void = () => {};
	export let onWeekChange: (startDate: string) => void = () => {};
	export let period: 'monthly' | 'weekly' = 'monthly';
	export let onPeriodChange: (p: 'monthly' | 'weekly') => void = () => {};

	const MONTHS_FR = [
		'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
		'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
	];
	const DAYS_FR = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];
	const DAYS_LONG_FR = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];

	const today = new Date();
	$: todayDay =
		today.getFullYear() === year && today.getMonth() + 1 === month ? today.getDate() : -1;

	// ── Monthly mode ────────────────────────────────────────────────────────────
	$: firstWeekday = (() => {
		const d = new Date(year, month - 1, 1).getDay();
		return d === 0 ? 6 : d - 1;
	})();

	$: daysInMonth = new Date(year, month, 0).getDate();

	$: cells = [
		...Array.from({ length: firstWeekday }, () => null),
		...Array.from({ length: daysInMonth }, (_, i) => i + 1)
	];

	function prevMonth() {
		if (month === 1) { year -= 1; month = 12; }
		else { month -= 1; }
		onMonthChange(year, month);
	}

	function nextMonth() {
		if (month === 12) { year += 1; month = 1; }
		else { month += 1; }
		onMonthChange(year, month);
	}

	// ── Weekly mode ─────────────────────────────────────────────────────────────
	// weekStart is an ISO date string (YYYY-MM-DD)
	$: weekStartDate = weekStart ? new Date(weekStart + 'T00:00:00') : null;

	// 7 days starting from weekStartDate
	$: weekDays = weekStartDate
		? Array.from({ length: 7 }, (_, i) => {
				const d = new Date(weekStartDate!);
				d.setDate(d.getDate() + i);
				return d;
			})
		: [];

	// For weekly mode, activeDays are offsets 0–6 from weekStart
	function isWeekDayActive(offset: number): boolean {
		return activeDays.includes(offset);
	}

	function isWeekDayToday(d: Date): boolean {
		return (
			d.getFullYear() === today.getFullYear() &&
			d.getMonth() === today.getMonth() &&
			d.getDate() === today.getDate()
		);
	}

	function prevWeek() {
		if (!weekStartDate) return;
		const d = new Date(weekStartDate);
		d.setDate(d.getDate() - 7);
		onWeekChange(toISODate(d));
	}

	function nextWeek() {
		if (!weekStartDate) return;
		const d = new Date(weekStartDate);
		d.setDate(d.getDate() + 7);
		onWeekChange(toISODate(d));
	}

	function toISODate(d: Date): string {
		const y = d.getFullYear();
		const m = String(d.getMonth() + 1).padStart(2, '0');
		const day = String(d.getDate()).padStart(2, '0');
		return `${y}-${m}-${day}`;
	}

	function weekLabel(): string {
		if (!weekDays.length) return '';
		const start = weekDays[0];
		const end = weekDays[6];
		const fmtDay = (d: Date) =>
			`${String(d.getDate()).padStart(2, '0')} ${MONTHS_FR[d.getMonth()].slice(0, 3)}`;
		return `${fmtDay(start)} – ${fmtDay(end)} ${end.getFullYear()}`;
	}

	// Click a day in monthly mode → switch to weekly mode starting that day
	function clickDay(day: number) {
		if (period === 'monthly') {
			// Switch to weekly mode starting from this day
			const d = new Date(year, month - 1, day);
			onPeriodChange('weekly');
			onWeekChange(toISODate(d));
		}
	}

	$: activeCount = period === 'weekly' ? activeDays.length : activeDays.length;
</script>

<div class="bg-white dark:bg-gray-800 rounded-2xl p-4 shadow-sm h-full flex flex-col">
	<!-- Period filter -->
	<div class="flex items-center justify-between mb-3">
		<div class="flex items-center gap-1 bg-gray-100 dark:bg-gray-700 rounded-full p-0.5">
			<button
				class="px-3 py-1 rounded-full text-xs font-medium transition
					{period === 'monthly'
						? 'bg-white dark:bg-gray-600 text-gray-800 dark:text-white shadow-sm'
						: 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
				on:click={() => onPeriodChange('monthly')}
			>Mensuel</button>
			<button
				class="px-3 py-1 rounded-full text-xs font-medium transition
					{period === 'weekly'
						? 'bg-white dark:bg-gray-600 text-gray-800 dark:text-white shadow-sm'
						: 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
				on:click={() => onPeriodChange('weekly')}
			>Hebdo</button>
		</div>
		<span class="text-xs text-blue-600 dark:text-blue-400 font-medium">{activeCount} jour{activeCount !== 1 ? 's' : ''} actif{activeCount !== 1 ? 's' : ''}</span>
	</div>

	{#if period === 'monthly'}
		<!-- ── Monthly view ── -->
		<div class="flex items-center justify-between mb-2">
			<button
				on:click={prevMonth}
				class="w-6 h-6 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 text-sm font-bold transition"
			>‹</button>
			<h3 class="text-sm font-semibold text-gray-800 dark:text-white">
				{MONTHS_FR[month - 1]} {year}
			</h3>
			<button
				on:click={nextMonth}
				class="w-6 h-6 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 text-sm font-bold transition"
			>›</button>
		</div>

		<!-- Day labels -->
		<div class="grid grid-cols-7 mb-1">
			{#each DAYS_FR as d}
				<div class="text-center text-[10px] font-medium text-gray-400 dark:text-gray-500 py-0.5">{d}</div>
			{/each}
		</div>

		<!-- Calendar grid — clicking a day switches to weekly mode -->
		<div class="grid grid-cols-7 gap-y-0.5 flex-1">
			{#each cells as day}
				{#if day === null}
					<div></div>
				{:else}
					<div class="flex flex-col items-center py-0.5">
						<button
							on:click={() => clickDay(day)}
							class="w-7 h-7 flex items-center justify-center text-xs rounded-full transition
								{day === todayDay
									? 'bg-blue-600 text-white font-bold'
									: activeDays.includes(day)
										? 'text-blue-700 dark:text-blue-300 font-semibold hover:bg-blue-50 dark:hover:bg-blue-900/20'
										: 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}"
							title="Voir la semaine du {day}/{month}"
						>{day}</button>
						{#if activeDays.includes(day) && day !== todayDay}
							<span class="w-1 h-1 rounded-full bg-blue-500 mt-0.5"></span>
						{/if}
					</div>
				{/if}
			{/each}
		</div>

		<p class="mt-2 text-[10px] text-gray-400 dark:text-gray-500">
			Cliquer un jour pour voir la semaine correspondante
		</p>

	{:else}
		<!-- ── Weekly view ── -->
		<div class="flex items-center justify-between mb-3">
			<button
				on:click={prevWeek}
				class="w-6 h-6 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 text-sm font-bold transition"
			>‹</button>
			<h3 class="text-xs font-semibold text-gray-700 dark:text-gray-200 text-center">
				{weekLabel()}
			</h3>
			<button
				on:click={nextWeek}
				class="w-6 h-6 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 text-sm font-bold transition"
			>›</button>
		</div>

		{#if weekDays.length}
			<!-- 7-day strip -->
			<div class="grid grid-cols-7 gap-1 flex-1">
				{#each weekDays as d, i}
					<div class="flex flex-col items-center gap-1">
						<!-- Day letter -->
						<span class="text-[10px] font-medium text-gray-400 dark:text-gray-500">
							{DAYS_LONG_FR[i]}
						</span>
						<!-- Day circle -->
						<div
							class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold
								{isWeekDayToday(d)
									? 'bg-blue-600 text-white'
									: isWeekDayActive(i)
										? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
										: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}"
						>{d.getDate()}</div>
						<!-- Month label for first/last days or month boundary -->
						<span class="text-[9px] text-gray-400 dark:text-gray-500 leading-none">
							{MONTHS_FR[d.getMonth()].slice(0, 3)}
						</span>
						<!-- Activity dot -->
						{#if isWeekDayActive(i) && !isWeekDayToday(d)}
							<span class="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
						{:else if !isWeekDayActive(i)}
							<span class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-gray-600"></span>
						{/if}
					</div>
				{/each}
			</div>

			<!-- Weekly summary -->
			<div class="mt-3 p-2.5 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
				<div class="flex items-center justify-between text-xs">
					<span class="text-gray-600 dark:text-gray-300">Sessions enregistrées</span>
					<span class="font-bold text-blue-700 dark:text-blue-300">{activeCount} / 7 jours</span>
				</div>
				<div class="mt-1.5 h-1.5 rounded-full bg-blue-100 dark:bg-blue-900/40 overflow-hidden">
					<div
						class="h-full rounded-full bg-blue-500 transition-all duration-700"
						style="width: {(activeCount / 7) * 100}%"
					></div>
				</div>
			</div>
		{:else}
			<div class="flex-1 flex items-center justify-center">
				<p class="text-sm text-gray-400 dark:text-gray-500">
					Cliquez sur un jour en vue mensuelle pour sélectionner une semaine
				</p>
			</div>
		{/if}
	{/if}
</div>
