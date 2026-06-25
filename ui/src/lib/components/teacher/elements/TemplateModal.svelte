<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { saveTemplate, type AssignmentTemplate } from '$lib/apis/resources';

	const dispatch = createEventDispatcher();
	const i18n: any = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';

	let title = '';
	let instructions = '';
	let busy = false;
	let message = '';

	$: valid = !!title.trim();

	function close() {
		dispatch('close');
	}

	async function save() {
		message = '';
		if (!valid) {
			message = $i18n.t('Title is required');
			return;
		}
		busy = true;
		try {
			const created: AssignmentTemplate = await saveTemplate(
				token(),
				title.trim(),
				instructions.trim()
			);
			dispatch('saved', created);
		} catch (err: any) {
			message = typeof err === 'string' ? err : $i18n.t('Could not save the template');
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
	<div class="w-full max-w-lg rounded-2xl bg-white dark:bg-gray-800 shadow-xl p-6">
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-white">{$i18n.t('New template')}</h2>
			<button class="text-gray-400 hover:text-gray-600" on:click={close} aria-label="Close"
				>✕</button
			>
		</div>

		<div class="flex flex-col gap-4">
			<div>
				<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
					>{$i18n.t('Title')} *</label
				>
				<input
					class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300"
					bind:value={title}
					placeholder={$i18n.t('e.g. Weekly quiz')}
				/>
			</div>
			<div>
				<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
					>{$i18n.t('Instructions')}</label
				>
				<textarea
					rows="4"
					class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300"
					bind:value={instructions}
					placeholder={$i18n.t('Reusable instructions for assignments built from this template')}
				></textarea>
			</div>
		</div>

		{#if message}<p class="text-sm mt-3 text-red-500">{message}</p>{/if}

		<div class="flex justify-end gap-2 mt-5">
			<button
				class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
				on:click={close}>{$i18n.t('Cancel')}</button
			>
			<button
				class="px-4 py-2 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm hover:opacity-90 disabled:opacity-50"
				on:click={save}
				disabled={busy || !valid}>{$i18n.t('Save')}</button
			>
		</div>
	</div>
</div>
