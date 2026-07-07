<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getStats, getTags } from '$lib/apis/flashcards';
	
	let stats = { total: 0, mastered: 0, to_review: 0, learning: 0, by_tag: {} };
	let tags = [];
	let loading = true;
	let token = '';
	
	onMount(async () => {
		token = localStorage.getItem('token') || '';
		await loadData();
		loading = false;
	});
	
	async function loadData() {
		try {
			stats = await getStats(token);
			const result = await getTags(token);
			tags = result.tags || [];
		} catch (e) {
			console.error('Erreur:', e);
		}
	}
	
	async function deleteAllCards() {
		if (!confirm('Êtes-vous sûr de vouloir supprimer TOUTES vos flashcards ?')) {
			return;
		}
		
		try {
			const response = await fetch(`http://localhost:8080/api/v1/flashcards/delete-all`, {
				method: 'DELETE',
				headers: { 'authorization': `Bearer ${token}` }
			});
			
			if (!response.ok) throw new Error('Erreur suppression');
			
			const result = await response.json();
			alert(`✅ ${result.deleted_count} cartes supprimées`);
			await loadData();
		} catch (e) {
			alert('❌ Erreur: ' + e.message);
		}
	}
</script>

<svelte:head>
	<title>Flashcards - Open TutorAI</title>
</svelte:head>

<div class="max-w-6xl mx-auto px-6 py-8">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-2">
			📚 Mes Flashcards
		</h1>
		<p class="text-gray-600 dark:text-gray-400">
			Mémorisez efficacement avec la répétition espacée
		</p>
	</div>
	
	{#if loading}
		<div class="text-center py-12 text-gray-500">Chargement...</div>
	{:else}
		<!-- Stats Grid -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
			<div class="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
				<div class="text-3xl mb-2">📊</div>
				<div class="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-1">
					{stats.total}
				</div>
				<div class="text-sm text-gray-600 dark:text-gray-400">Total</div>
			</div>
			
			<div class="bg-indigo-50 dark:bg-indigo-900/10 p-6 rounded-xl shadow-sm border-2 border-indigo-200 dark:border-indigo-800">
				<div class="text-3xl mb-2">📚</div>
				<div class="text-3xl font-bold text-indigo-700 dark:text-indigo-300 mb-1">
					{stats.to_review}
				</div>
				<div class="text-sm text-indigo-600 dark:text-indigo-400">À réviser</div>
			</div>
			
			<div class="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
				<div class="text-3xl mb-2">✅</div>
				<div class="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-1">
					{stats.mastered}
				</div>
				<div class="text-sm text-gray-600 dark:text-gray-400">Maîtrisées</div>
			</div>
		</div>
		
		<!-- Action Buttons -->
		<div class="flex flex-wrap gap-4 justify-center mb-8">
			<button
				class="px-6 py-3 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl font-semibold transition-all shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
				on:click={() => goto('/student/flashcards/review?mode=quiz')}
				disabled={stats.to_review === 0}
			>
				🎯 Commencer la révision
			</button>
			
			<button
				class="px-6 py-3 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-indigo-600 dark:text-indigo-400 border-2 border-indigo-500 rounded-xl font-semibold transition-all"
				on:click={() => goto('/student/flashcards/generate')}
			>
				✨ Créer des flashcards
			</button>
		</div>
		
		<!-- Tags Section -->
		{#if tags.length > 0}
			<div class="mb-8">
				<h2 class="text-xl font-bold text-gray-800 dark:text-gray-100 mb-4 text-center">
					📁 Mes matières
				</h2>
				<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
					{#each tags as tag}
						<button
							class="bg-white dark:bg-gray-800 p-4 rounded-xl border-2 border-gray-200 dark:border-gray-700 hover:border-indigo-500 dark:hover:border-indigo-500 transition-all text-center group"
							on:click={() => goto(`/student/flashcards/review?tag=${encodeURIComponent(tag)}&mode=quiz`)}
						>
							<div class="font-semibold text-gray-800 dark:text-gray-100 mb-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
								{tag}
							</div>
							<div class="text-sm text-gray-600 dark:text-gray-400">
								{stats.by_tag[tag]?.to_review || 0} à réviser
							</div>
						</button>
					{/each}
				</div>
			</div>
		{/if}
		
		<!-- Danger Zone -->
		{#if stats.total > 0}
			<div class="mt-8 p-6 bg-red-50 dark:bg-red-900/10 border-2 border-red-200 dark:border-red-800 rounded-xl text-center">
				<button
					class="px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-xl font-semibold transition-all"
					on:click={deleteAllCards}
				>
					🗑️ Supprimer toutes les cartes
				</button>
			</div>
		{/if}
	{/if}
</div>
