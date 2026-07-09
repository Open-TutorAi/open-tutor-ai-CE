<script lang="ts">
	import { onMount, createEventDispatcher, getContext } from 'svelte';
	import { getGuardians, inviteGuardian, type GuardianLink } from '$lib/apis/classrooms';

	const dispatch = createEventDispatcher();
	const i18n: any = getContext('i18n');
	export let classId: string;
	export let studentId: string;
	export let studentName = '';
	const token = () => localStorage.getItem('token') ?? '';

	let guardians: GuardianLink[] = [];
	let loading = true;
	let email = '';
	let busy = false;
	let message = '';

	function close() {
		dispatch('close');
	}

	async function load() {
		loading = true;
		try {
			guardians = await getGuardians(token(), classId, studentId);
		} catch (err: any) {
			message = typeof err === 'string' ? err : $i18n.t('Could not load guardians');
		} finally {
			loading = false;
		}
	}

	async function invite() {
		message = '';
		if (!email.trim()) {
			message = $i18n.t('Email is required');
			return;
		}
		busy = true;
		try {
			await inviteGuardian(token(), classId, studentId, email.trim());
			email = '';
			await load();
		} catch (err: any) {
			message = typeof err === 'string' ? err : $i18n.t('Could not invite the parent');
		} finally {
			busy = false;
		}
	}

	onMount(load);
</script>

<div
	class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
	on:click|self={close}
	role="presentation"
>
	<div class="w-full max-w-md rounded-2xl bg-white dark:bg-gray-800 shadow-xl p-6">
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-white">
				{$i18n.t('Guardians')}{studentName ? ` — ${studentName}` : ''}
			</h2>
			<button class="text-gray-400 hover:text-gray-600" on:click={close} aria-label="Close"
				>✕</button
			>
		</div>

		<div class="text-sm text-gray-600 dark:text-gray-300 mb-2">{$i18n.t('Linked parents')}</div>
		{#if loading}
			<div class="py-6 flex justify-center">
				<div class="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500"></div>
			</div>
		{:else if guardians.length === 0}
			<div class="text-gray-500 dark:text-gray-400 text-sm py-3">
				{$i18n.t('No guardian linked — invite a parent below.')}
			</div>
		{:else}
			<ul class="divide-y divide-gray-100 dark:divide-gray-700 mb-2">
				{#each guardians as g (g.id)}
					<li class="py-2 flex items-center justify-between">
						<div>
							<div class="text-gray-800 dark:text-white text-sm">{g.invited_email ?? '—'}</div>
							<span
								class={`text-xs px-2 py-0.5 rounded-full ${g.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'}`}
							>
								{g.status === 'active' ? $i18n.t('active') : $i18n.t('pending')}
							</span>
						</div>
						{#if g.status === 'active' && g.invited_email}
							<a
								class="text-blue-500 hover:text-blue-600 text-xs"
								href={`mailto:${g.invited_email}`}>✉ {$i18n.t('Email parent')}</a
							>
						{:else}
							<span class="text-xs text-gray-400">{$i18n.t('invite sent')}</span>
						{/if}
					</li>
				{/each}
			</ul>
		{/if}

		<div class="border-t border-gray-100 dark:border-gray-700 pt-3 mt-2">
			<div class="text-sm text-gray-600 dark:text-gray-300 mb-1">{$i18n.t('Invite a parent')}</div>
			<div class="flex gap-2">
				<input
					class="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-transparent px-3 py-2 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300"
					bind:value={email}
					placeholder="parent@mail.com"
				/>
				<button
					class="px-4 py-2 rounded-full bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
					on:click={invite}
					disabled={busy}>{$i18n.t('Invite')}</button
				>
			</div>
			{#if message}<p class="text-sm mt-2 text-gray-600 dark:text-gray-300">{message}</p>{/if}
		</div>
	</div>
</div>
