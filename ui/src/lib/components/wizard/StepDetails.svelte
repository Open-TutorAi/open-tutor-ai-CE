<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	export let duration = '';
	export let language = '';

	const LANGUAGES = ['English', 'French', 'Arabic'];
</script>

<div data-testid="wizard-step-details" class="space-y-4">
	<div>
		<label
			for="classroom-duration"
			class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
		>
			{$i18n.t('Estimated Duration')}
		</label>
		<input
			id="classroom-duration"
			type="text"
			bind:value={duration}
			placeholder={$i18n.t('e.g. 12 weeks')}
			class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
		/>
	</div>

	<div>
		<label
			for="classroom-language"
			class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
		>
			{$i18n.t('Language')}
		</label>
		<select
			id="classroom-language"
			bind:value={language}
			class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
		>
			<option value="">{$i18n.t('Select a language')}</option>
			{#each LANGUAGES as lang}
				<option value={lang}>{$i18n.t(lang)}</option>
			{/each}
		</select>
	</div>
</div>
