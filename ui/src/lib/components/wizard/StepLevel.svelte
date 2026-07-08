<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	export let level = '';

	// Moroccan secondary curriculum ladder. Adjust/extend as needed.
	const LEVELS = [
		'1ère Année Collège',
		'2ème Année Collège',
		'3ème Année Collège',
		'Tronc Commun',
		'1ère Année Bac',
		'2ème Année Bac'
	];
</script>

<div data-testid="wizard-step-level" class="space-y-4">
	<div>
		<label
			for="classroom-level"
			class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
		>
			{$i18n.t('Level')}
		</label>
		<select
			id="classroom-level"
			bind:value={level}
			class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
		>
			<option value="">{$i18n.t('Select a level')}</option>
			{#each LEVELS as lvl}
				<option value={lvl}>{lvl}</option>
			{/each}
		</select>
	</div>
</div>
