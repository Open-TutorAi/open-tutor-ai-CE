<!-- Assignments.svelte -->
<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');
</script>

<div class="mb-6">
	<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-4">
		{$i18n.t('Assignments')}
	</h2>
	<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center mt-6">
		<p class="text-gray-600 dark:text-gray-400">{$i18n.t('Assignment management coming soon')}</p>
	</div>
</div>
