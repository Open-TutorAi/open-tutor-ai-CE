<script lang="ts">
	export let className = 'size-5';
	export let strokeWidth = '2';
	import { user } from '$lib/stores';
</script>

{#if $user?.role === 'admin'}
	<svg
		xmlns="http://www.w3.org/2000/svg"
		fill="none"
		viewBox="0 0 24 24"
		stroke-width={strokeWidth}
		stroke="currentColor"
		class={className}
	>
		<path
			stroke-linecap="round"
			stroke-linejoin="round"
			d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12"
		/>
	</svg>
{/if}
