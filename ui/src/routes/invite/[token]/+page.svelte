<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { user } from '$lib/stores';
	import { onMount, getContext } from 'svelte';
	import { acceptInvitation } from '$lib/apis/classrooms';

	const i18n: any = getContext('i18n');
	let inviteToken = '';
	let state: 'idle' | 'accepting' | 'done' | 'error' = 'idle';
	let message = '';

	onMount(() => {
		inviteToken = $page.params.token;
	});

	async function accept() {
		if (!$user) {
			localStorage.setItem('post_login_redirect', `/invite/${inviteToken}`);
			goto('/auth');
			return;
		}
		state = 'accepting';
		try {
			const res = await acceptInvitation(localStorage.getItem('token') ?? '', inviteToken);
			state = 'done';
			message = $i18n.t('You have joined the class.');
			if (res?.classroom_id) {
				setTimeout(() => goto(`/${$user.role}`), 1200);
			}
		} catch (err: any) {
			state = 'error';
			message = typeof err === 'string' ? err : $i18n.t('This invitation is no longer valid.');
		}
	}
</script>

<div
	class="flex flex-col items-center justify-center min-h-screen bg-[#F4F7FE] dark:bg-gray-900 p-6"
>
	<div class="w-full max-w-md rounded-2xl bg-white dark:bg-gray-800 shadow-lg p-8 text-center">
		<h1 class="text-xl font-bold text-gray-800 dark:text-white mb-2">{$i18n.t('Open TutorAI')}</h1>
		{#if state === 'done'}
			<p class="text-green-600">{message}</p>
		{:else if state === 'error'}
			<p class="text-red-500">{message}</p>
		{:else}
			<p class="text-gray-600 dark:text-gray-300 mb-6">
				{$i18n.t('You have been invited to join a class.')}
			</p>
			<button
				class="w-full px-4 py-2.5 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold transition disabled:opacity-50"
				on:click={accept}
				disabled={state === 'accepting'}
			>
				{$user ? $i18n.t('Join the class') : $i18n.t('Log in & join')}
			</button>
		{/if}
	</div>
</div>
