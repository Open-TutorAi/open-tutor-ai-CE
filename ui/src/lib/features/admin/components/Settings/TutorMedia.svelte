<script lang="ts">
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	import Audio from '$lib/features/admin/components/Settings/Audio.svelte';
	import Images from '$lib/features/admin/components/Settings/Images.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	let activeTab: 'audio' | 'images' = 'audio';
</script>

<div class="flex flex-col gap-4 text-sm">
	<div class="flex gap-3 border-b border-gray-100 dark:border-gray-800 pb-0">
		<button
			class="pb-2 text-sm font-medium border-b-2 transition {activeTab === 'audio'
				? 'border-black dark:border-white'
				: 'border-transparent text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
			on:click={() => (activeTab = 'audio')}
		>
			{$i18n.t('Voice & Audio')}
		</button>
		<button
			class="pb-2 text-sm font-medium border-b-2 transition {activeTab === 'images'
				? 'border-black dark:border-white'
				: 'border-transparent text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
			on:click={() => (activeTab = 'images')}
		>
			{$i18n.t('Illustrations')}
		</button>
	</div>

	{#if activeTab === 'audio'}
		<div class="text-xs text-gray-500 dark:text-gray-400 -mt-2">
			{$i18n.t('Configure speech-to-text and text-to-speech for the tutor voice experience.')}
		</div>
		<Audio
			saveHandler={() => {
				toast.success($i18n.t('Audio settings saved.'));
			}}
		/>
	{:else}
		<div class="text-xs text-gray-500 dark:text-gray-400 -mt-2">
			{$i18n.t('Configure image generation for educational illustrations.')}
		</div>
		<Images
			on:save={() => {
				toast.success($i18n.t('Image settings saved.'));
			}}
		/>
	{/if}
</div>
