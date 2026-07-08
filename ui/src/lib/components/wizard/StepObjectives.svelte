<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	export let objectives = '';
</script>

<div data-testid="wizard-step-objectives" class="space-y-4">
	<div>
		<label
			for="classroom-objectives"
			class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
		>
			{$i18n.t('Learning Objectives')}
		</label>
		<textarea
			id="classroom-objectives"
			bind:value={objectives}
			rows="5"
			placeholder={$i18n.t('What will students learn in this classroom?')}
			class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
		></textarea>
	</div>
</div>
