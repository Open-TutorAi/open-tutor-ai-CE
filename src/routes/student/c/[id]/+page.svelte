<script lang="ts">
	import { page } from '$app/stores';

	import Chat from '$lib/components/tutor/Chat.svelte';
</script>

<Chat chatIdProp={$page.params.id} />
