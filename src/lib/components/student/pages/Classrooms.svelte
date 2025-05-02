<!-- Classrooms.svelte -->
<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');
</script>

<div class="mb-6">
	<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-4">{$i18n.t('Classrooms Page')}</h2>
</div>
