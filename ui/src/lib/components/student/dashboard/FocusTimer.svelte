<!-- Minuteur Pomodoro — état persistant via focusTimer store -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { isDemo } from '$lib/stores';
	import {
		focusTimer,
		focusTimeDisplay,
		startFocusTimer,
		pauseFocusTimer,
		resetFocusTimer,
		updateFocusSettingsStore,
		initFocusSettings
	} from '$lib/stores/focusTimer';
	import { getFocusSettings, updateFocusSettings } from '$lib/apis/focus';

	const R = 54;
	const C = 2 * Math.PI * R;

	$: totalSec = $focusTimer.totalSeconds || 1;
	$: dashOffset = $focusTimer.remaining <= 0 ? C : C * (1 - $focusTimer.remaining / totalSec);
	$: isAtStart = $focusTimer.remaining >= $focusTimer.totalSeconds;

	function setWork(delta: number) {
		if ($focusTimer.running) return;
		const newVal = Math.max(1, Math.min(90, $focusTimer.workMinutes + delta));
		updateFocusSettingsStore(newVal, $focusTimer.breakMinutes);
		saveSettings(newVal, $focusTimer.breakMinutes);
	}

	function setBreak(delta: number) {
		if ($focusTimer.running) return;
		const newVal = Math.max(1, Math.min(30, $focusTimer.breakMinutes + delta));
		updateFocusSettingsStore($focusTimer.workMinutes, newVal);
		saveSettings($focusTimer.workMinutes, newVal);
	}

	async function saveSettings(wm: number, bm: number) {
		const token = localStorage.getItem('token');
		if (!token || $isDemo) return;
		try {
			await updateFocusSettings(token, {
				work_minutes: wm,
				break_minutes: bm,
				long_break_minutes: 15,
				long_break_interval: 4
			});
		} catch {}
	}

	onMount(async () => {
		// Load settings only if timer hasn't been started yet
		if ($focusTimer.phase === 'idle' && !$focusTimer.running) {
			const token = localStorage.getItem('token');
			if (token && !$isDemo) {
				try {
					const settings = await getFocusSettings(token);
					initFocusSettings(settings.work_minutes, settings.break_minutes);
				} catch {}
			}
		}
	});
</script>

<div class="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm flex flex-col items-center gap-4 h-full">
	<!-- Header -->
	<div class="flex items-center justify-between w-full">
		<h3 class="font-semibold text-gray-800 dark:text-white text-sm">Mode Focus</h3>
		<span
			class="text-xs px-2.5 py-1 rounded-full font-medium
			{$focusTimer.phase === 'break'
				? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
				: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'}"
		>
			{$focusTimer.phase === 'break' ? 'Pause' : 'Travail'}
		</span>
	</div>

	<!-- Ring timer -->
	<div class="relative w-40 h-40 flex items-center justify-center">
		<svg class="absolute inset-0 -rotate-90" viewBox="0 0 120 120">
			<!-- Track -->
			<circle cx="60" cy="60" r={R} fill="none" stroke="#e5e7eb" stroke-width="8"
				class="dark:stroke-gray-700" />
			<!-- Progress -->
			<circle
				cx="60"
				cy="60"
				r={R}
				fill="none"
				stroke={$focusTimer.phase === 'break' ? '#16a34a' : '#2563eb'}
				stroke-width="8"
				stroke-linecap="round"
				stroke-dasharray={C}
				stroke-dashoffset={dashOffset}
				style="transition: stroke-dashoffset 1s linear;"
			/>
		</svg>
		<div class="text-center z-10">
			<p class="text-3xl font-bold text-gray-800 dark:text-white font-mono tracking-tight">
				{$focusTimeDisplay}
			</p>
			<p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
				{$focusTimer.phase === 'break' ? 'Repos' : 'Concentration'}
			</p>
		</div>
	</div>

	<!-- Controls -->
	<div class="flex items-center gap-3">
		{#if !$focusTimer.running}
			<button
				on:click={startFocusTimer}
				class="px-7 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full text-sm font-semibold transition shadow-sm shadow-blue-200 dark:shadow-blue-900/30"
			>
				{isAtStart ? 'Démarrer' : 'Reprendre'}
			</button>
		{:else}
			<button
				on:click={pauseFocusTimer}
				class="px-7 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full text-sm font-semibold transition"
			>
				Pause
			</button>
		{/if}
		<button
			on:click={resetFocusTimer}
			class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition"
			title="Réinitialiser"
		>
			<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none"
				stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
				<path d="M3 3v5h5" />
			</svg>
		</button>
	</div>

	<!-- Settings: work / break duration -->
	<div class="w-full border-t border-gray-100 dark:border-gray-700 pt-3 space-y-2">
		<!-- Work duration -->
		<div class="flex items-center justify-between">
			<span class="text-xs text-gray-500 dark:text-gray-400">Travail</span>
			<div class="flex items-center gap-1">
				<button
					on:click={() => setWork(-1)}
					disabled={$focusTimer.running}
					class="w-6 h-6 flex items-center justify-center rounded text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-gray-700 disabled:opacity-40 transition"
				>−</button>
				<span class="text-sm font-semibold text-gray-700 dark:text-gray-200 w-14 text-center">
					{$focusTimer.workMinutes} min
				</span>
				<button
					on:click={() => setWork(1)}
					disabled={$focusTimer.running}
					class="w-6 h-6 flex items-center justify-center rounded text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-gray-700 disabled:opacity-40 transition"
				>+</button>
			</div>
		</div>
		<!-- Break duration -->
		<div class="flex items-center justify-between">
			<span class="text-xs text-gray-500 dark:text-gray-400">Pause</span>
			<div class="flex items-center gap-1">
				<button
					on:click={() => setBreak(-1)}
					disabled={$focusTimer.running}
					class="w-6 h-6 flex items-center justify-center rounded text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-gray-700 disabled:opacity-40 transition"
				>−</button>
				<span class="text-sm font-semibold text-gray-700 dark:text-gray-200 w-14 text-center">
					{$focusTimer.breakMinutes} min
				</span>
				<button
					on:click={() => setBreak(1)}
					disabled={$focusTimer.running}
					class="w-6 h-6 flex items-center justify-center rounded text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-gray-700 disabled:opacity-40 transition"
				>+</button>
			</div>
		</div>
	</div>
</div>
