<!-- Histogramme SVG des heures d'étude par jour -->
<script lang="ts">
	import type { DailyHours } from '$lib/apis/dashboard';

	export let data: DailyHours[] = [];

	const CHART_H = 110;
	const BAR_W = 24;
	const SLOT_W = 38;
	const PADDING = 8;

	$: maxH = Math.max(...data.map((d) => d.hours), 0.5);
	$: svgW = data.length * SLOT_W + PADDING * 2;
	$: svgH = CHART_H + 30;

	function barHeight(h: number): number {
		return (h / maxH) * CHART_H;
	}

	function barX(i: number): number {
		return PADDING + i * SLOT_W + (SLOT_W - BAR_W) / 2;
	}

	function labelX(i: number): number {
		return PADDING + i * SLOT_W + SLOT_W / 2;
	}
</script>

<div class="w-full overflow-x-auto">
	{#if data.length === 0}
		<div class="flex items-center justify-center h-24 text-sm text-gray-400 dark:text-gray-500">
			Aucune donnée disponible
		</div>
	{:else}
		<svg viewBox="0 0 {svgW} {svgH}" class="w-full" style="height: 160px;">
			{#each data as item, i}
				<!-- Bar -->
				<rect
					x={barX(i)}
					y={CHART_H - barHeight(item.hours)}
					width={BAR_W}
					height={Math.max(barHeight(item.hours), 2)}
					rx="5"
					fill={item.hours > 0 ? '#3b82f6' : '#e5e7eb'}
					class="transition-all duration-300"
				/>
				<!-- Hour label on top -->
				{#if item.hours > 0}
					<text
						x={labelX(i)}
						y={CHART_H - barHeight(item.hours) - 4}
						text-anchor="middle"
						font-size="9"
						fill="#6b7280"
						class="dark:fill-gray-400"
					>{item.hours}h</text>
				{/if}
				<!-- Day label below -->
				<text
					x={labelX(i)}
					y={CHART_H + 16}
					text-anchor="middle"
					font-size="9"
					fill="#9ca3af"
					class="dark:fill-gray-500"
				>{item.day}</text>
			{/each}
		</svg>
	{/if}
</div>
