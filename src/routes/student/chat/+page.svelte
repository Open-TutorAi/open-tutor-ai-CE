<!-- student/chat/+page.svelte -->
<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import Chat from '$lib/components/edu_chat/Chat.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// Check if user is a student
	onMount(() => {
		console.log('Chat page mounted');
		console.log('User role from store:', $user?.role);
		
		if (!$user || $user.role !== 'student') {
			console.log('User is not a student, redirecting to home');
			goto('/');
			return;
		}
	});
</script>

<Chat />
