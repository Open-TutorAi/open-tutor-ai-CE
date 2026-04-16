<!-- Teacher Dashboard Page -->
<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	// TODO: Implement dashboard content
	// Include Assistant IA / Insight IA element
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
			<p class="text-gray-600 dark:text-gray-400 mt-1">Bienvenue dans votre espace enseignant</p>
		</div>
	</div>

	<!-- Placeholder content -->
	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
		<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Mes Cours</h3>
			<p class="text-gray-600 dark:text-gray-400">Gérez vos cours et contenus pédagogiques</p>
		</div>

		<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Devoirs & Quiz</h3>
			<p class="text-gray-600 dark:text-gray-400">Créez et suivez les évaluations</p>
		</div>

		<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Suivi & Rapports</h3>
			<p class="text-gray-600 dark:text-gray-400">Analysez les performances des étudiants</p>
		</div>
	</div>
</div>