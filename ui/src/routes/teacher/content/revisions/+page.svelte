<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { goto } from '$app/navigation';
	import { user, models } from '$lib/stores';
	import { fade } from 'svelte/transition';
	import { generateRevisionSheet } from '$lib/apis/teacher-content';
	import Markdown from '$lib/components/chat/Messages/Markdown.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	let loading = true;
	let generating = false;
	let error = '';

	// State
	let frequentErrors = '';
	let selectedModel = '';
	let generatedContent = '';
	let isEditing = false;

	onMount(async () => {
		if (!$user) {
			goto('/auth');
			return;
		}

		if ($user.role !== 'teacher') {
			goto(`/${$user.role}`);
			return;
		}

		loading = false;
	});

	// Reactively set selectedModel once models are loaded
	$: if ($models && $models.length > 0 && !selectedModel) {
		selectedModel = $models[0].id;
	}

	async function handleGenerate() {
		if (!frequentErrors) {
			error = $i18n.t('Veuillez remplir les erreurs fréquentes.');
			return;
		}

		generating = true;
		error = '';
		generatedContent = '';
		isEditing = false;

		try {
			const token = localStorage.getItem('token');
			if (token) {
				const response = await generateRevisionSheet(token, {
					classroom_id: 1, // Mock
					frequent_errors: frequentErrors,
					model_id: selectedModel
				});

				if (response && response.content) {
					generatedContent = response.content;
				}
			}
		} catch (err) {
			console.error('Caught error:', err);
			let errMsg = '';
			if (typeof err === 'string') {
				errMsg = err;
			} else if (Array.isArray(err)) {
				errMsg = err.map((e) => (typeof e === 'object' ? JSON.stringify(e) : e)).join(', ');
			} else if (err && typeof err === 'object') {
				errMsg = err.message || err.detail || JSON.stringify(err);
			}

			if (
				(errMsg && errMsg.includes('429')) ||
				errMsg.includes('Too Many Requests') ||
				errMsg.includes('exhausted')
			) {
				error = $i18n.t(
					"Trop de requêtes vers l'IA (Quota dépassé). Veuillez patienter un instant avant de réessayer."
				);
			} else {
				error =
					errMsg ||
					$i18n.t('Failed to generate revision sheet. Please check your AI configuration.');
			}
		} finally {
			generating = false;
		}
	}
</script>

{#if loading}
	<div class="flex justify-center items-center min-h-screen">
		<div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
	</div>
{:else}
	<div class="flex flex-col gap-6 p-6 max-w-6xl mx-auto w-full">
		<div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">
				{$i18n.t('Génération de Fiches de Révision')}
			</h1>
			<p class="text-gray-500 dark:text-gray-400 mt-1">
				{$i18n.t(
					"Créez des fiches ciblées basées sur les erreurs fréquentes de vos élèves grâce à l'IA."
				)}
			</p>
		</div>

		{#if error}
			<div class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-4 rounded-lg">
				{error}
			</div>
		{/if}

		<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
			<!-- Configuration Panel -->
			{#if !generatedContent}
				<div class="lg:col-span-4 flex flex-col gap-6" in:fade>
					<div
						class="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700"
					>
						<h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
							1. {$i18n.t('Contexte & Difficultés')}
						</h2>
						<div class="space-y-4">
							<div>
								<label
									for="errors"
									class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
								>
									{$i18n.t('Erreurs fréquentes observées')}
								</label>
								<textarea
									id="errors"
									bind:value={frequentErrors}
									rows="5"
									placeholder={$i18n.t(
										'Ex: Confusion entre périmètre et aire, difficulté à simplifier des fractions...'
									)}
									class="block w-full py-2 px-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
								></textarea>
								<p class="text-xs text-gray-500 mt-1">
									{$i18n.t(
										"Saisissez les erreurs récurrentes. L'IA générera des rappels et des exemples corrigés spécifiques."
									)}
								</p>
							</div>

							<div>
								<label
									for="model"
									class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
								>
									{$i18n.t('Modèle IA')}
								</label>
								<select
									id="model"
									bind:value={selectedModel}
									class="block w-full py-2 px-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
								>
									{#each $models as model}
										<option value={model.id}>{model.name}</option>
									{/each}
								</select>
							</div>

							<button
								class="w-full mt-4 inline-flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg transition shadow-md disabled:opacity-50"
								on:click={handleGenerate}
								disabled={generating || !frequentErrors}
							>
								{#if generating}
									<span
										class="animate-spin inline-block w-5 h-5 border-2 border-white border-t-transparent rounded-full"
									></span>
									{$i18n.t('Génération en cours...')}
								{:else}
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-5 w-5"
										viewBox="0 0 20 20"
										fill="currentColor"
									>
										<path
											fill-rule="evenodd"
											d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z"
											clip-rule="evenodd"
										/>
									</svg>
									{$i18n.t('Générer la Fiche')}
								{/if}
							</button>
						</div>
					</div>
				</div>
			{/if}

			<!-- Rendu de la fiche -->
			<div
				class="{generatedContent
					? 'lg:col-span-12'
					: 'lg:col-span-8'} transition-all duration-300 bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 min-h-[500px]"
			>
				<div class="flex justify-between items-center mb-6">
					<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
						{generatedContent ? '' : '2. '}{$i18n.t('Aperçu de la fiche')}
					</h2>
					{#if generatedContent}
						<div class="flex items-center gap-3">
							<button
								class="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 flex items-center gap-1 bg-blue-50 dark:bg-blue-900/30 px-3 py-1.5 rounded-lg transition"
								on:click={() => {
									generatedContent = '';
									frequentErrors = '';
								}}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-4 w-4"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
									><path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M12 4v16m8-8H4"
									/></svg
								>
								{$i18n.t('Nouvelle fiche')}
							</button>
							<button
								class="text-sm font-medium flex items-center gap-1 px-3 py-1.5 rounded-lg border transition {isEditing
									? 'bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-indigo-800'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'}"
								on:click={() => (isEditing = !isEditing)}
							>
								{#if isEditing}
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-4 w-4"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
										><path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
										/><path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
										/></svg
									>
									{$i18n.t("Voir l'aperçu")}
								{:else}
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-4 w-4"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
										><path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
										/></svg
									>
									{$i18n.t('Éditer')}
								{/if}
							</button>
							<button
								class="text-sm font-medium text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 flex items-center gap-1 bg-gray-100 dark:bg-gray-700 px-3 py-1.5 rounded-lg transition"
								on:click={() => {
									navigator.clipboard.writeText(generatedContent);
								}}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-4 w-4"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
									/>
								</svg>
								{$i18n.t('Copier')}
							</button>
						</div>
					{/if}
				</div>

				{#if generatedContent}
					{#if isEditing}
						<textarea
							bind:value={generatedContent}
							class="w-full h-full min-h-[500px] p-4 font-mono text-sm text-gray-800 dark:text-gray-200 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y"
						></textarea>
					{:else}
						<div
							class="prose prose-sm sm:prose lg:prose-lg dark:prose-invert max-w-none bg-gray-50 dark:bg-gray-900/50 p-6 rounded-lg border border-gray-100 dark:border-gray-700"
						>
							<Markdown id="revision-result" content={generatedContent} />
						</div>
					{/if}
				{:else if generating}
					<div class="flex flex-col items-center justify-center h-64 text-gray-400">
						<div class="animate-pulse flex flex-col items-center">
							<svg
								class="w-12 h-12 mb-4 text-blue-500 opacity-50"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="1.5"
									d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
								/>
							</svg>
							<p>{$i18n.t("L'IA rédige la fiche de révision...")}</p>
						</div>
					</div>
				{:else}
					<div class="flex flex-col items-center justify-center h-64 text-gray-400">
						<svg
							class="w-16 h-16 mb-4 opacity-50"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="1.5"
								d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
							/>
						</svg>
						<p>{$i18n.t('La fiche générée apparaîtra ici.')}</p>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
