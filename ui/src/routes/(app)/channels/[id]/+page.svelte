<script lang="ts">
	import { page } from '$app/stores';

	import { Channel } from '$lib/features/channel';
</script>

<Channel id={$page.params.id} />
