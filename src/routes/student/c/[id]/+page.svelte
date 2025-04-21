<script lang="ts">
	import { page } from '$app/stores';

	import Chat from '$lib/components/student/components/Chat.svelte';
	// import Help from '$lib/components/layout/Help.svelte';
</script>

<Chat chatIdProp={$page.params.id} />
