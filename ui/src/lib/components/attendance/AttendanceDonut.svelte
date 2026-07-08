<script lang="ts">
	export let present = 0;
	export let absent = 0;
	export let late = 0;

	const RADIUS = 40;
	const STROKE = 16;
	const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

	$: total = present + absent + late;
	$: arcs = (
		[
			{ value: present, color: '#22c55e' },
			{ value: absent, color: '#ef4444' },
			{ value: late, color: '#f59e0b' }
		] as { value: number; color: string }[]
	).reduce<{ value: number; color: string; length: number; offset: number }[]>((acc, seg) => {
		const prevOffset = acc.length > 0 ? acc[acc.length - 1].offset + acc[acc.length - 1].length : 0;
		const fraction = total > 0 ? seg.value / total : 0;
		acc.push({ ...seg, length: fraction * CIRCUMFERENCE, offset: prevOffset });
		return acc;
	}, []);
</script>

<svg
	data-testid="donut"
	role="img"
	aria-label="Attendance breakdown"
	width="100"
	height="100"
	viewBox="0 0 100 100"
>
	<circle cx="50" cy="50" r={RADIUS} fill="none" stroke="#e5e7eb" stroke-width={STROKE} />
	{#each arcs as arc}
		{#if arc.length > 0}
			<circle
				cx="50"
				cy="50"
				r={RADIUS}
				fill="none"
				stroke={arc.color}
				stroke-width={STROKE}
				stroke-dasharray={`${arc.length} ${CIRCUMFERENCE - arc.length}`}
				stroke-dashoffset={-arc.offset}
				transform="rotate(-90 50 50)"
			/>
		{/if}
	{/each}
</svg>
