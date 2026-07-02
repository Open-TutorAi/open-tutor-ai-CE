<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18nType } from '$lib/types';
	import { goto } from '$app/navigation';
	import { user, models } from '$lib/stores';
	import { fade } from 'svelte/transition';
	import { generateCurriculum, generateScenario } from '$lib/apis/teacher-content';
	import Markdown from '$lib/components/chat/Messages/Markdown.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	let fileInput: HTMLInputElement;
	let selectedFile: File | null = null;
	let error = '';

	// State - Generation
	let selectedModel = '';
	let generating = false;
	let curriculumData: any = null;
	let showUpload = true;

	// State - Scenarios
	let scenarios: Record<number, string> = {};
	let generatingScenario: Record<number, boolean> = {};
	let selectedScenarioWeek: number | null = null;
	let isEditingScenario = false;

	onMount(() => {
		if ($models && $models.length > 0) {
			selectedModel = $models[0].id;
		}
	});

	function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			selectedFile = target.files[0];
			error = '';
		}
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
			selectedFile = event.dataTransfer.files[0];
			error = '';
		}
	}

	async function handleGenerate() {
		if (!selectedFile) {
			error = $i18n.t('Veuillez fournir un document de programme.');
			return;
		}

		generating = true;
		error = '';
		curriculumData = null;

		try {
			const token = localStorage.getItem('token');
			if (token) {
				const response = await generateCurriculum(token, selectedFile, selectedModel);
				if (response && response.curriculum) {
					curriculumData = response.curriculum;
					showUpload = false; // Hide upload panel on success
				} else {
					error = $i18n.t('Erreur: La génération a échoué (réponse invalide).');
				}
			}
		} catch (err: any) {
			console.error('Generation error:', err);
			error = err || $i18n.t('Échec de la génération. Vérifiez le format du document.');
		} finally {
			generating = false;
		}
	}

	async function handleGenerateScenario(week: any) {
		const token = localStorage.getItem('token');
		if (!token) return;

		generatingScenario[week.week_number] = true;
		generatingScenario = { ...generatingScenario };

		try {
			const payload = {
				theme: week.theme,
				objectives: week.objectives || [],
				estimated_hours: week.estimated_hours || 2,
				model_id: selectedModel
			};
			const response = await generateScenario(token, payload);
			if (response && response.scenario) {
				// Nettoyage des balises <br> ou <br>- générées dans les tableaux Markdown
				let cleanedScenario = response.scenario.replace(/<br\s*\/?>-?/gi, ' • ');
				scenarios[week.week_number] = cleanedScenario;
				scenarios = { ...scenarios };
			}
		} catch (err) {
			console.error('Scenario generation error:', err);
		} finally {
			generatingScenario[week.week_number] = false;
			generatingScenario = { ...generatingScenario };
		}
	}

	// Svelte action to auto-resize textareas on mount and update
	function autoResize(node: HTMLTextAreaElement, value: string) {
		const resize = () => {
			node.style.height = 'auto';
			node.style.height = node.scrollHeight + 'px';
		};

		// Initial resize
		setTimeout(resize, 0);

		return {
			update(newValue: string) {
				setTimeout(resize, 0);
			}
		};
	}
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<div class="flex flex-col gap-6 p-6 max-w-6xl mx-auto w-full">
		<div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">
				{$i18n.t('Planification Annuelle IA')}
			</h1>
			<p class="text-gray-500 dark:text-gray-400 mt-1">
				{$i18n.t(
					'Transformez le programme officiel (PDF, TXT) en un calendrier pédagogique détaillé.'
				)}
			</p>
		</div>

		{#if error}
			<div
				class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 p-4 rounded-lg border border-red-200 dark:border-red-800 text-sm"
			>
				{error}
			</div>
		{/if}

		<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
			{#if showUpload}
				<!-- Configuration Panel -->
				<div class="lg:col-span-4 flex flex-col gap-6" in:fade>
					<!-- Upload Card -->
					<div
						class="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700"
					>
						<h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
							1. {$i18n.t('Programme Officiel')}
						</h2>
						<div class="space-y-4">
							<!-- svelte-ignore a11y-click-events-have-key-events -->
							<!-- svelte-ignore a11y-no-static-element-interactions -->
							<div
								class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-6 text-center hover:bg-gray-50 dark:hover:bg-gray-700/50 transition cursor-pointer"
								on:click={() => fileInput.click()}
								on:dragover|preventDefault
								on:drop={handleDrop}
							>
								<input
									type="file"
									accept=".pdf,.txt,.docx"
									class="hidden"
									bind:this={fileInput}
									on:change={handleFileSelect}
								/>

								<div class="mb-3">
									<svg
										class="mx-auto h-10 w-10 text-gray-400"
										stroke="currentColor"
										fill="none"
										viewBox="0 0 48 48"
										aria-hidden="true"
									>
										<path
											d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
											stroke-width="2"
											stroke-linecap="round"
											stroke-linejoin="round"
										/>
									</svg>
								</div>

								{#if selectedFile}
									<p class="text-sm font-medium text-gray-900 dark:text-white">
										{selectedFile.name}
									</p>
									<p class="text-xs text-gray-500 mt-1">
										{(selectedFile.size / 1024 / 1024).toFixed(2)} MB
									</p>
								{:else}
									<p class="text-sm font-medium text-gray-900 dark:text-white">
										{$i18n.t('Cliquez ou glissez-déposez le document')}
									</p>
									<p class="text-xs text-gray-500 mt-1">PDF, TXT, DOCX</p>
								{/if}
							</div>
						</div>

						<div class="mt-6">
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

						<div class="mt-6">
							<button
								class="w-full inline-flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg transition shadow-md disabled:opacity-50"
								on:click={handleGenerate}
								disabled={generating || !selectedFile}
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
									{$i18n.t('Générer le Plan')}
								{/if}
							</button>
						</div>
					</div>
				</div>
			{/if}

			<!-- Result Panel -->
			<div class="{showUpload ? 'lg:col-span-8' : 'lg:col-span-12'} transition-all duration-300">
				<div
					class="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 h-full min-h-[500px]"
				>
					<div class="flex justify-between items-center mb-6">
						<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
							{showUpload ? '2. ' : ''}{$i18n.t('Calendrier Pédagogique (Timeline)')}
						</h2>
						{#if !showUpload}
							<button
								class="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 flex items-center gap-1 bg-blue-50 dark:bg-blue-900/30 px-3 py-1.5 rounded-lg transition"
								on:click={() => (showUpload = true)}
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
								{$i18n.t('Nouvelle planification')}
							</button>
						{/if}
					</div>

					{#if generating}
						<div
							class="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400"
							in:fade
						>
							<div class="relative w-16 h-16 mb-6">
								<div
									class="absolute inset-0 border-4 border-gray-200 dark:border-gray-700 rounded-full"
								></div>
								<div
									class="absolute inset-0 border-4 border-blue-500 rounded-full border-t-transparent animate-spin"
								></div>
							</div>
							<p class="text-lg">{$i18n.t("L'IA conçoit la progression annuelle...")}</p>
							<p class="text-sm opacity-70 mt-2">{$i18n.t('Lecture du programme en cours')}</p>
						</div>
					{:else if curriculumData && curriculumData.weeks}
						<div
							class="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:ml-[8.5rem] md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-200 dark:before:via-gray-700 before:to-transparent"
							in:fade
						>
							<div class="mb-8">
								<textarea
									bind:value={curriculumData.title}
									use:autoResize={curriculumData.title}
									rows="1"
									class="text-2xl font-bold text-gray-900 dark:text-white bg-transparent border-b-2 border-transparent hover:border-gray-300 focus:border-blue-500 focus:bg-white dark:focus:bg-gray-800 focus:outline-none w-full transition py-1 px-2 -ml-2 rounded-t placeholder-gray-400 resize-none overflow-hidden"
									placeholder="Progression Annuelle"
									on:input={(e) => {
										e.target.style.height = 'auto';
										e.target.style.height = e.target.scrollHeight + 'px';
									}}
								></textarea>
							</div>

							{#each curriculumData.weeks as week}
								<div
									class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group"
								>
									<!-- Timeline dot -->
									<div
										class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white dark:border-gray-800 bg-blue-500 text-white font-bold shadow-sm shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10"
									>
										{week.week_number}
									</div>

									<!-- Content Card -->
									<div
										class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition"
									>
										<div class="flex justify-between items-start mb-4 gap-2">
											<textarea
												bind:value={week.theme}
												use:autoResize={week.theme}
												rows="1"
												class="font-bold text-lg text-gray-900 dark:text-white bg-transparent border-b-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600 focus:border-blue-500 focus:bg-white dark:focus:bg-gray-800 focus:outline-none w-full transition py-1 px-2 -ml-2 rounded-t resize-none overflow-hidden"
												placeholder="Thème de la semaine"
												on:input={(e) => {
													e.target.style.height = 'auto';
													e.target.style.height = e.target.scrollHeight + 'px';
												}}
											></textarea>
											<div
												class="flex items-center bg-blue-100 dark:bg-blue-900/60 rounded-lg px-2.5 py-1.5 shrink-0 border border-transparent hover:border-blue-300 dark:hover:border-blue-700 transition shadow-sm mt-1"
											>
												<input
													type="number"
													bind:value={week.estimated_hours}
													class="w-10 bg-transparent text-sm font-bold text-blue-800 dark:text-blue-200 focus:outline-none text-right appearance-none"
												/>
												<span class="text-sm font-bold text-blue-800 dark:text-blue-200 ml-1"
													>h</span
												>
											</div>
										</div>

										<div class="mt-3">
											<p class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
												Objectifs :
											</p>
											<div class="space-y-2">
												{#if week.objectives}
													{#each week.objectives as obj, i}
														<div class="flex items-start gap-3 group/obj relative">
															<div class="w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0 mt-3"></div>
															<textarea
																bind:value={week.objectives[i]}
																use:autoResize={week.objectives[i]}
																rows="1"
																class="text-sm md:text-base font-medium text-gray-700 dark:text-gray-200 bg-transparent border-b border-transparent hover:border-gray-200 dark:hover:border-gray-700 focus:border-blue-500 focus:bg-gray-50 dark:focus:bg-gray-900/50 focus:outline-none w-full transition py-1.5 px-2 rounded-t resize-none overflow-hidden"
																placeholder="Nouvel objectif"
																on:input={(e) => {
																	e.target.style.height = 'auto';
																	e.target.style.height = e.target.scrollHeight + 'px';
																}}
															></textarea>
															<button
																class="absolute -right-2 top-1.5 opacity-0 group-hover/obj:opacity-100 text-gray-400 hover:text-red-500 transition shrink-0 bg-white dark:bg-gray-800 rounded-full p-1"
																on:click={() => {
																	week.objectives.splice(i, 1);
																	week.objectives = [...week.objectives];
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
																		d="M6 18L18 6M6 6l12 12"
																	/></svg
																>
															</button>
														</div>
													{/each}
												{/if}
											</div>
											<button
												class="text-xs font-medium text-blue-500 hover:text-blue-600 flex items-center gap-1 mt-3"
												on:click={() => {
													if (!week.objectives) week.objectives = [];
													week.objectives = [...week.objectives, ''];
												}}
											>
												<svg
													xmlns="http://www.w3.org/2000/svg"
													class="h-3 w-3"
													viewBox="0 0 20 20"
													fill="currentColor"
													><path
														fill-rule="evenodd"
														d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z"
														clip-rule="evenodd"
													/></svg
												>
												Ajouter un objectif
											</button>
										</div>

										<div class="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
											{#if generatingScenario[week.week_number]}
												<div class="flex items-center gap-2 text-indigo-500 text-sm">
													<span
														class="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full"
													></span>
													{$i18n.t('Création de la fiche...')}
												</div>
											{:else if scenarios[week.week_number]}
												<button
													class="text-sm font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 flex items-center gap-1"
													on:click={() => {
														selectedScenarioWeek = week.week_number;
														isEditingScenario = false;
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
															d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
														/></svg
													>
													{$i18n.t('Voir la fiche pédagogique')}
												</button>
											{:else}
												<button
													class="text-sm font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 flex items-center gap-1"
													on:click={() => handleGenerateScenario(week)}
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
															d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
														/></svg
													>
													{$i18n.t('Créer la fiche pédagogique')}
												</button>
											{/if}
										</div>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<div
							class="flex flex-col items-center justify-center h-64 text-gray-400 dark:text-gray-500 border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-xl"
						>
							<svg
								class="w-12 h-12 mb-4 opacity-50"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="1.5"
									d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
								/>
							</svg>
							<p>{$i18n.t('Le calendrier apparaîtra ici après génération')}</p>
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>
</div>

<!-- Modal Overlay for Pedagogical Scenario -->
{#if selectedScenarioWeek !== null && scenarios[selectedScenarioWeek]}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-sm"
		in:fade={{ duration: 200 }}
		out:fade={{ duration: 150 }}
		on:click|self={() => {
			selectedScenarioWeek = null;
			isEditingScenario = false;
		}}
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden border border-gray-200 dark:border-gray-700"
		>
			<!-- Header -->
			<div
				class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center bg-gray-50/80 dark:bg-gray-900/80"
			>
				<div class="flex items-center gap-3">
					<div
						class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400 font-bold text-sm"
					>
						{selectedScenarioWeek}
					</div>
					<h3 class="text-xl font-bold text-gray-900 dark:text-white">
						{$i18n.t('Fiche Pédagogique')}
					</h3>
				</div>
				<button
					class="text-gray-400 hover:text-gray-900 dark:hover:text-white transition p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700"
					on:click={() => {
						selectedScenarioWeek = null;
						isEditingScenario = false;
					}}
				>
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/></svg
					>
				</button>
			</div>
			<!-- Body -->
			<div class="p-6 overflow-y-auto w-full relative group">
				{#if isEditingScenario}
					<textarea
						bind:value={scenarios[selectedScenarioWeek]}
						class="w-full h-full min-h-[500px] p-4 font-mono text-sm text-gray-800 dark:text-gray-200 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y"
					></textarea>
				{:else}
					<div
						class="prose prose-base dark:prose-invert max-w-none prose-headings:text-indigo-600 dark:prose-headings:text-indigo-400 prose-a:text-blue-600 prose-table:border-gray-200 dark:prose-table:border-gray-700"
					>
						<Markdown
							id="modal-scenario-{selectedScenarioWeek}"
							content={scenarios[selectedScenarioWeek]}
						/>
					</div>
				{/if}
			</div>
			<!-- Footer -->
			<div
				class="px-6 py-4 border-t border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/50 flex justify-between items-center"
			>
				<button
					class="px-4 py-2 text-sm font-medium rounded-lg border transition flex items-center gap-2 {isEditingScenario
						? 'bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-indigo-800'
						: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'}"
					on:click={() => (isEditingScenario = !isEditingScenario)}
				>
					{#if isEditingScenario}
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
						{$i18n.t('Éditer la fiche')}
					{/if}
				</button>
				<button
					class="px-4 py-2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 font-medium rounded-lg shadow-sm hover:opacity-90 transition"
					on:click={() => {
						selectedScenarioWeek = null;
						isEditingScenario = false;
					}}
				>
					Fermer
				</button>
			</div>
		</div>
	</div>
{/if}
