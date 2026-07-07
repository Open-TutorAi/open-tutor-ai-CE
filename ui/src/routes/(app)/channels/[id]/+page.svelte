<script lang="ts">
	import { page } from '$app/stores';

	import Channel from '$lib/features/channel/components/Channel.svelte';
</script>

<Channel id={$page.params.id} />
