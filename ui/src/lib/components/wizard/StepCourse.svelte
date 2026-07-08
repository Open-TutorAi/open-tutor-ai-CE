<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	export let course = '';
</script>

<div data-testid="wizard-step-course" class="space-y-4">
	<div>
		<label
			for="classroom-course"
			class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
		>
			{$i18n.t('Course Name')}
		</label>
		<input
			id="classroom-course"
			type="text"
			bind:value={course}
			placeholder={$i18n.t('e.g. Algebra Fundamentals')}
			class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
		/>
	</div>
</div>
