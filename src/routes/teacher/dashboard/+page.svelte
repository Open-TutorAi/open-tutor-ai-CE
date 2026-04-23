<script lang="ts">
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');
</script>

<div class="p-6">
	<h1 class="text-3xl font-bold mb-6">Dashboard</h1>
	<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
		<p class="text-gray-600 dark:text-gray-400">{$i18n.t('Dashboard content coming soon')}</p>
	</div>
</div>
