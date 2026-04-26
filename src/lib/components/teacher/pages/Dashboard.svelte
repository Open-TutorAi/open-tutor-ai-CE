<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { user } from '$lib/stores';
	const i18n = getContext('i18n');

	// Mock data for UI testing
	let courses = [
		{ id: 1, title: 'PROJET D\'ETUDE', modified: '2 heures', code: 'PER-402', students: 34 },
		{ id: 2, title: 'Technologies DevOps', modified: 'hier', code: 'D-Ops-101', students: 42 },
		{ id: 3, title: 'Full stack avancé', modified: '3 jours', code: 'Ful-220', students: 28 },
		{ id: 4, title: 'bases de données NoSQL', modified: '1 semaine', code: 'BaSE-305', students: 16 }
	];

	function copyToClipboard(text: string) {
		navigator.clipboard.writeText(text);
		// You can add a toast here
	}
</script>

<div class="p-8 bg-gray-50 dark:bg-gray-900 min-h-screen">
	<div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
		<div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">
				{$i18n.t('Bonjour')}, Prof. {$user?.name?.toUpperCase() || 'SAADY'}
			</h1>
			<p class="text-gray-500 mt-1">{$i18n.t('Voici ce qui se passe dans vos classes aujourd\'hui.')}</p>
		</div>
		<button class="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-all shadow-sm">
			<span class="text-xl">+</span> {$i18n.t('Créer un nouveau cours')}
		</button>
	</div>

	<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
		<div class="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col items-center text-center">
			<span class="text-xs font-bold text-gray-400 uppercase tracking-wider">{$i18n.t('TOTAL DES COURS')}</span>
			<div class="flex items-center gap-2 mt-2">
				<span class="text-4xl font-black text-gray-900 dark:text-white">4</span>
				<span class="text-xs text-green-500 font-bold">↗ +1 ce mois</span>
			</div>
		</div>

		<div class="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col items-center text-center">
			<span class="text-xs font-bold text-gray-400 uppercase tracking-wider">{$i18n.t('ÉTUDIANTS INSCRITS')}</span>
			<div class="flex items-center gap-2 mt-2">
				<span class="text-4xl font-black text-gray-900 dark:text-white">120</span>
				<span class="text-xs text-green-500 font-bold">↗ +12% vs sem. dernière</span>
			</div>
		</div>
	</div>

	<div class="flex justify-between items-center mb-6">
		<h2 class="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
			<span class="text-indigo-500">🕒</span> {$i18n.t('Cours Récents')}
		</h2>
		<button class="text-indigo-600 font-semibold text-sm hover:underline">{$i18n.t('Voir tout')}</button>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		{#each courses as course}
			<div class="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
				<div class="flex justify-between items-start mb-4">
					<div>
						<h3 class="font-bold text-gray-900 dark:text-white text-lg">{course.title}</h3>
						<p class="text-xs text-gray-400 mt-1 flex items-center gap-1">
							📅 Modifié il y a {course.modified}
						</p>
					</div>
					<button class="text-gray-400 hover:text-gray-600">⋮</button>
				</div>

				<div class="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 flex justify-between items-center mb-6">
					<div>
						<p class="text-[10px] font-bold text-gray-400 uppercase">CODE PARTICIPATION</p>
						<p class="font-mono font-bold text-gray-800 dark:text-gray-200">{course.code}</p>
					</div>
					<button on:click={() => copyToClipboard(course.code)} class="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
						</svg>
					</button>
				</div>

				<div class="flex justify-between items-center">
					<div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 font-medium">
						👥 {course.students} Étudiants
					</div>
					<button class="bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 px-6 py-2 rounded-lg text-sm font-bold transition">
						Gérer
					</button>
				</div>
			</div>
		{/each}
	</div>
</div>