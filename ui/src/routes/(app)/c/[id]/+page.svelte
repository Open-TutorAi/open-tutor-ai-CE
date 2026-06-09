<script lang="ts">
	import { page } from '$app/stores';

	import { Chat } from '$lib/features/chat';
	import Help from '$lib/components/layout/Help.svelte';
</script>

<Help />
<Chat chatIdProp={$page.params.id} />
