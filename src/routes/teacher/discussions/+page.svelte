<!-- Discussions Page -->
<script lang="ts">
	import { getContext } from 'svelte';
	import i18nStore from '$lib/i18n';

	const i18n = /** @type {import('svelte/store').Readable<any>} */ (getContext('i18n') ?? i18nStore);
</script>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Discussions</h1>
			<p class="text-gray-600 dark:text-gray-400 mt-1">Échangez avec vos étudiants</p>
		</div>
	</div>

	<!-- Placeholder content -->
	<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
		<p class="text-gray-600 dark:text-gray-400">Contenu de la page Discussions à implémenter</p>
	</div>
</div>