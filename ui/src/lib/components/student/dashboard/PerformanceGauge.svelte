<!-- Jauge de performance style compteur de vitesse -->
<script lang="ts">
	export let value: number = 0; // 0–100 (completion rate %)
	export let count: number = 0; // tutorials completed
	export let countLabel: string = 'Tutoriels terminés';
	export let totalPoints: number = 0;

	// SVG gauge: semicircle from left (180°) to right (0°) through top
	const cx = 120;
	const cy = 110;
	const r = 80;
	const strokeWidth = 10;

	function polarXY(angleDeg: number) {
		const rad = angleDeg * (Math.PI / 180);
		return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
	}

	const trackStart = polarXY(180);
	const trackEnd = polarXY(0);
	const trackPath = `M ${trackStart.x} ${trackStart.y} A ${r} ${r} 0 0 1 ${trackEnd.x} ${trackEnd.y}`;

	$: valueAngleDeg = 180 - value * 1.8;
	$: valueEnd = polarXY(valueAngleDeg);
	$: valueSweep = value * 1.8;
	$: valueLargeArc = valueSweep > 180 ? 1 : 0;
	$: valuePath =
		value <= 0
			? ''
			: value >= 100
				? `M ${trackStart.x} ${trackStart.y} A ${r} ${r} 0 0 1 ${trackEnd.x} ${trackEnd.y}`
				: `M ${trackStart.x} ${trackStart.y} A ${r} ${r} 0 ${valueLargeArc} 1 ${valueEnd.x} ${valueEnd.y}`;

	$: needleRad = valueAngleDeg * (Math.PI / 180);
	$: needleTip = {
		x: cx + (r - 12) * Math.cos(needleRad),
		y: cy + (r - 12) * Math.sin(needleRad)
	};

	const redEnd = polarXY(180 - 33 * 1.8);
	const yellowEnd = polarXY(180 - 66 * 1.8);
	const redPath = `M ${trackStart.x} ${trackStart.y} A ${r} ${r} 0 0 1 ${redEnd.x} ${redEnd.y}`;
	const yellowPath = `M ${redEnd.x} ${redEnd.y} A ${r} ${r} 0 0 1 ${yellowEnd.x} ${yellowEnd.y}`;
	const greenPath = `M ${yellowEnd.x} ${yellowEnd.y} A ${r} ${r} 0 0 1 ${trackEnd.x} ${trackEnd.y}`;
</script>

<div class="flex flex-col items-center gap-1 w-full">
	<svg viewBox="0 0 240 145" class="w-full max-w-[260px]">
		<!-- Colored background segments -->
		<path d={redPath} fill="none" stroke="#fca5a5" stroke-width={strokeWidth} stroke-linecap="butt" />
		<path d={yellowPath} fill="none" stroke="#fde68a" stroke-width={strokeWidth} stroke-linecap="butt" />
		<path d={greenPath} fill="none" stroke="#6ee7b7" stroke-width={strokeWidth} stroke-linecap="butt" />

		<!-- Value arc overlay -->
		{#if value > 0}
			<path d={valuePath} fill="none" stroke="#2563eb" stroke-width={strokeWidth} stroke-linecap="round" />
		{/if}

		<!-- Needle -->
		<line
			x1={cx} y1={cy}
			x2={needleTip.x} y2={needleTip.y}
			stroke="#1e293b" stroke-width="2.5" stroke-linecap="round"
			class="dark:stroke-gray-200"
		/>
		<circle cx={cx} cy={cy} r="5" fill="#1e293b" class="dark:fill-gray-200" />

		<!-- Labels: 0 left, 100 right -->
		<text x="36" y={cy + 16} text-anchor="middle" font-size="9" fill="#9ca3af">0</text>
		<text x="204" y={cy + 16} text-anchor="middle" font-size="9" fill="#9ca3af">100</text>

		<!-- Percentage centered above center hub -->
		<text x={cx} y={cy - 18} text-anchor="middle" font-size="18" font-weight="bold" fill="#1d4ed8" class="dark:fill-blue-400">{value}%</text>
	</svg>

	<!-- Tutoriels terminés -->
	<div class="text-center -mt-1">
		<p class="text-2xl font-bold text-gray-800 dark:text-white">{count}</p>
		<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{countLabel}</p>
	</div>

	<!-- Points badge -->
	<div class="mt-2 flex items-center gap-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/40 rounded-full px-4 py-1.5">
		<span class="text-amber-500 text-sm">⭐</span>
		<span class="text-lg font-bold text-amber-600 dark:text-amber-400">{totalPoints}</span>
		<span class="text-xs text-amber-600/70 dark:text-amber-400/70 font-medium">points</span>
	</div>
	<p class="text-[10px] text-gray-400 dark:text-gray-500 text-center">
		+5 pts par soutien créé · +100 pts par soutien terminé
	</p>
</div>
