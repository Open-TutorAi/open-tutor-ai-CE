<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { getTutorSystemPrompt, setTutorSystemPrompt } from '$lib/apis/configs';

	const i18n = getContext<Writable<i18nType>>('i18n');

	let prompt = '';
	let loading = false;
	let saving = false;

	onMount(async () => {
		loading = true;
		const content = await getTutorSystemPrompt(localStorage.token);
		if (content !== null) {
			prompt = content;
		}
		loading = false;
	});

	const savePrompt = async () => {
		saving = true;
		const ok = await setTutorSystemPrompt(localStorage.token, prompt);
		saving = false;
		if (ok) {
			toast.success($i18n.t('Tutor system prompt saved.'));
		} else {
			toast.error($i18n.t('Failed to save tutor system prompt.'));
		}
	};
</script>

<div class="flex flex-col gap-4 text-sm">
	<div>
		<div class="mb-1 font-medium">{$i18n.t('System Prompt')}</div>
		<p class="text-xs text-gray-500 dark:text-gray-400 mb-2">
			{$i18n.t('Define the default behavior and persona of the AI tutor.')}
		</p>

		{#if loading}
			<div class="text-xs text-gray-400">{$i18n.t('Loading...')}</div>
		{:else}
			<textarea
				class="w-full min-h-[320px] rounded-lg px-3 py-2 text-sm bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 outline-none resize-y font-mono"
				bind:value={prompt}
				placeholder={$i18n.t('Enter the tutor system prompt...')}
				disabled={saving}
			/>
		{/if}
	</div>

	<div class="flex justify-end">
		<button
			class="px-4 py-2 rounded-lg bg-black dark:bg-white text-white dark:text-black text-sm font-medium disabled:opacity-50 transition"
			on:click={savePrompt}
			disabled={loading || saving}
		>
			{saving ? $i18n.t('Saving...') : $i18n.t('Save')}
		</button>
	</div>
</div>
