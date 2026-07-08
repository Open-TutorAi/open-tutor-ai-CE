
<script lang="ts">
	export let name: string;
	export let size: 'sm' | 'md' | 'lg' = 'md';
	export let imageUrl: string | null | undefined = null;

	$: hasPhoto = !!imageUrl && imageUrl !== '/user.png';
	let photoFailed = false;

	const COLORS = [
		'bg-blue-500',
		'bg-emerald-500',
		'bg-amber-500',
		'bg-purple-500',
		'bg-pink-500',
		'bg-teal-500',
		'bg-indigo-500',
		'bg-rose-500'
	];

	const SIZES: Record<string, string> = {
		sm: 'w-7 h-7 text-xs',
		md: 'w-9 h-9 text-sm',
		lg: 'w-12 h-12 text-base'
	};

	const colorFor = (value: string) => {
		let hash = 0;
		for (let i = 0; i < value.length; i++) hash = (hash << 5) - hash + value.charCodeAt(i);
		return COLORS[Math.abs(hash) % COLORS.length];
	};

	const initialsOf = (value: string) =>
		value
			.trim()
			.split(/\s+/)
			.slice(0, 2)
			.map((part) => part[0]?.toUpperCase() ?? '')
			.join('');

	$: bgColor = colorFor(name || '?');
	$: initials = initialsOf(name || '?');
</script>

{#if hasPhoto && !photoFailed}
	<img
		src={imageUrl}
		alt={name}
		data-testid="student-avatar"
		on:error={() => (photoFailed = true)}
		class="rounded-full object-cover flex-shrink-0 select-none {SIZES[size]}"
	/>
{:else}
	<div
		data-testid="student-avatar"
		class="rounded-full flex items-center justify-center font-semibold text-white flex-shrink-0 select-none {bgColor} {SIZES[
			size
		]}"
	>
		{initials}
	</div>
{/if}
