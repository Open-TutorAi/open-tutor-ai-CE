<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { generateFlashcards, generateFromPDF } from '$lib/apis/flashcards';
	
	let content = '';
	let numCards = 5;
	let tag = '';
	let loading = false;
	let error = null;
	let success = false;
	let token = '';
	let pdfFile = null;
	let uploadMode = 'text';
	let selectedModel = 'phi3:mini';
	
	const suggestedTags = ['Philosophie', 'Python', 'Mathématiques', 'Histoire', 'Physique'];
	
	onMount(() => {
		token = localStorage.getItem('token') || '';
	});
	
	function handleFileSelect(event) {
		const file = event.target.files[0];
		if (file) {
			if (!file.name.toLowerCase().endsWith('.pdf')) {
				error = 'Seuls les fichiers PDF sont acceptés';
				return;
			}
			if (file.size > 10 * 1024 * 1024) {
				error = 'Fichier trop volumineux (max 10 MB)';
				return;
			}
			pdfFile = file;
			error = null;
		}
	}
	
	async function handleGenerate() {
		error = null;
		success = false;
		
		if (uploadMode === 'text' && !content.trim()) {
			error = 'Veuillez entrer du contenu';
			return;
		}
		
		if (uploadMode === 'pdf' && !pdfFile) {
			error = 'Veuillez sélectionner un PDF';
			return;
		}
		
		loading = true;
		
		try {
			if (uploadMode === 'text') {
				await generateFlashcards(token, content, numCards, null, tag || null);
			} else {
				await generateFromPDF(token, pdfFile, numCards, tag || null, selectedModel);
			}
			
			success = true;
			setTimeout(() => goto('/student/flashcards/review?mode=quiz'), 2000);
		} catch (e) {
			error = e.message || 'Erreur lors de la génération';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Générer Flashcards - Open TutorAI</title>
</svelte:head>

<div class="max-w-3xl mx-auto px-6 py-8">
	<!-- Header -->
	<div class="text-center mb-8">
		<h1 class="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-2">
			📝 Créer des Flashcards
		</h1>
		<p class="text-gray-600 dark:text-gray-400">
			Générez des cartes de révision à partir de votre contenu
		</p>
	</div>
	
	<!-- Form Card -->
	<div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-8">
		<!-- Mode Tabs -->
		<div class="flex gap-2 mb-6 bg-gray-100 dark:bg-gray-900 p-2 rounded-xl">
			<button
				class="flex-1 py-3 px-4 rounded-lg font-semibold transition-all {uploadMode === 'text' ? 'bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-sm' : 'text-gray-600 dark:text-gray-400'}"
				on:click={() => uploadMode = 'text'}
			>
				✍️ Texte
			</button>
			<button
				class="flex-1 py-3 px-4 rounded-lg font-semibold transition-all {uploadMode === 'pdf' ? 'bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-sm' : 'text-gray-600 dark:text-gray-400'}"
				on:click={() => uploadMode = 'pdf'}
			>
				📄 PDF
			</button>
		</div>
		
		<!-- Tag Input -->
		<div class="mb-6">
			<label class="block mb-2 font-semibold text-gray-800 dark:text-gray-100">
				Matière
			</label>
			<input
				type="text"
				bind:value={tag}
				placeholder="Ex: Philosophie, Python..."
				list="tags"
				class="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-700 rounded-lg focus:border-indigo-500 dark:focus:border-indigo-500 bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100"
			/>
			<datalist id="tags">
				{#each suggestedTags as t}
					<option value={t} />
				{/each}
			</datalist>
		</div>
		
		<!-- Content Input -->
		{#if uploadMode === 'text'}
			<div class="mb-6">
				<label class="block mb-2 font-semibold text-gray-800 dark:text-gray-100">
					Contenu
				</label>
				<textarea
					bind:value={content}
					placeholder="Collez votre cours ici..."
					rows="8"
					class="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-700 rounded-lg focus:border-indigo-500 dark:focus:border-indigo-500 bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 resize-y min-h-[200px]"
				></textarea>
			</div>
		{:else}
			<div class="mb-6">
				<label class="block mb-2 font-semibold text-gray-800 dark:text-gray-100">
					Fichier PDF
				</label>
				<label class="block p-8 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl cursor-pointer hover:border-indigo-500 dark:hover:border-indigo-500 transition-all text-center">
					<input
						type="file"
						accept=".pdf"
						on:change={handleFileSelect}
						class="hidden"
					/>
					{#if pdfFile}
						<div class="flex items-center justify-center gap-3">
							<span class="text-3xl">📄</span>
							<div>
								<div class="font-semibold text-gray-800 dark:text-gray-100">{pdfFile.name}</div>
								<div class="text-sm text-gray-500">{(pdfFile.size / 1024).toFixed(0)} KB</div>
							</div>
						</div>
					{:else}
						<div class="text-3xl mb-2">📎</div>
						<div class="font-semibold text-gray-800 dark:text-gray-100">Cliquez pour sélectionner un PDF</div>
					{/if}
				</label>
			</div>
		{/if}
		
		<!-- Number of Cards -->
		<div class="mb-6">
			<label class="block mb-2 font-semibold text-gray-800 dark:text-gray-100">
				Nombre de cartes : {numCards}
			</label>
			<input
				type="range"
				bind:value={numCards}
				min="3"
				max="15"
				step="1"
				class="w-full"
			/>
		</div>
		
		<!-- Messages -->
		{#if error}
			<div class="mb-4 p-4 bg-red-50 dark:bg-red-900/10 border-l-4 border-red-500 text-red-700 dark:text-red-400 rounded">
				⚠️ {error}
			</div>
		{/if}
		
		{#if success}
			<div class="mb-4 p-4 bg-green-50 dark:bg-green-900/10 border-l-4 border-green-500 text-green-700 dark:text-green-400 rounded">
				✅ Flashcards générées ! Redirection...
			</div>
		{/if}
		
		<!-- Submit Button -->
		<button
			class="w-full py-4 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl font-semibold text-lg transition-all shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
			on:click={handleGenerate}
			disabled={loading}
		>
			{loading ? '⏳ Génération...' : '🚀 Générer les flashcards'}
		</button>
	</div>
</div>
