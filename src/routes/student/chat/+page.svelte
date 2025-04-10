<!-- student/chat/+page.svelte -->
<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Chat from '$lib/components/chat/Chat.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');
</script>

<div >
		<Chat />
</div> 