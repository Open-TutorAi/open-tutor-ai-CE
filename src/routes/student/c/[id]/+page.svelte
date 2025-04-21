<script lang="ts">
	import { page } from '$app/stores';

	import Chat from '$lib/components/edu_chat/Chat.svelte';
</script>

<Chat chatIdProp={$page.params.id} />
