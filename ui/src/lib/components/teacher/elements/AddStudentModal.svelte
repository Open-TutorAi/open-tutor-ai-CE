<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { enrolStudent, createInvitation, type RosterEntry } from '$lib/apis/classrooms';

	const dispatch = createEventDispatcher();
	const i18n: any = getContext('i18n');
	export let classId: string;

	let email = '';
	let busy = false;
	let message = '';
	let notFound = false;
	let joinUrl = '';
	const token = () => localStorage.getItem('token') ?? '';

	function close() {
		dispatch('close');
	}

	async function enrol() {
		message = '';
		notFound = false;
		joinUrl = '';
		if (!email.trim()) {
			message = $i18n.t('Email is required');
			return;
		}
		busy = true;
		try {
			const entry: RosterEntry = await enrolStudent(token(), classId, email.trim());
			dispatch('enrolled', entry);
		} catch (err: any) {
			const detail = typeof err === 'string' ? err : '';
			if (detail === '' || detail.toLowerCase().includes('user')) {
				notFound = true;
				message = $i18n.t('No account for this email.');
			} else {
				message = detail || $i18n.t('Could not enrol the student');
			}
		} finally {
			busy = false;
		}
	}

	async function invite() {
		busy = true;
		try {
			const res = await createInvitation(token(), classId, email.trim(), 'student');
			joinUrl = res.join_url;
			message = res.email_sent ? $i18n.t('Invitation sent.') : $i18n.t('Share this invite link:');
			dispatch('invited');
		} catch (err: any) {
			message = typeof err === 'string' ? err : $i18n.t('Could not send the invitation');
		} finally {
			busy = false;
		}
	}
</script>

<div
	class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
	on:click|self={close}
	role="presentation"
>
	<div class="w-full max-w-md rounded-2xl bg-white dark:bg-gray-800 shadow-xl p-6">
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-white">{$i18n.t('Add student')}</h2>
			<button class="text-gray-400 hover:text-gray-600" on:click={close} aria-label="Close"
				>✕</button
			>
		</div>
		<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1" for="enrol-email"
			>{$i18n.t('Email')}</label
		>
		<div class="flex gap-2">
			<input
				id="enrol-email"
				class="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-transparent px-3 py-2 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300"
				bind:value={email}
				placeholder="student@school.org"
			/>
			<button
				class="px-4 py-2 rounded-full bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
				on:click={enrol}
				disabled={busy}
			>
				{$i18n.t('Enrol')}
			</button>
		</div>
		{#if message}<p class="text-sm mt-3 text-gray-600 dark:text-gray-300">{message}</p>{/if}
		{#if joinUrl}
			<div class="mt-2 flex items-center gap-2">
				<input
					class="flex-1 text-xs rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1 text-gray-700 dark:text-gray-200"
					readonly
					value={joinUrl}
				/>
				<button
					class="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-gray-700"
					on:click={() => navigator.clipboard?.writeText(joinUrl)}>{$i18n.t('Copy')}</button
				>
			</div>
		{:else if notFound}
			<button
				class="mt-3 w-full px-4 py-2 rounded-full border border-blue-400 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 disabled:opacity-50"
				on:click={invite}
				disabled={busy}
			>
				✉ {$i18n.t('Send invitation instead')}
			</button>
		{/if}
	</div>
</div>
