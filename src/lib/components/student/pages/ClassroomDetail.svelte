<!-- 
  ClassroomDetail.svelte — UPDATED
  Replace: src/lib/components/student/pages/ClassroomDetail.svelte
  
  Changes:
  - Shows real taux de progression (progress bar)
  - "Commencer l'apprentissage" resumes existing chat if one exists
  - Section statuses reflect real DB state (✓ completed, → in-progress)
-->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { fade, slide } from 'svelte/transition';
	import { getCourseById } from '$lib/apis/courses';

	export let courseId: string;

	const i18n = getContext('i18n');

	interface Section {
		id: string;
		title: string;
		status: 'not-started' | 'in-progress' | 'completed';
	}

	interface Chapter {
		id: string;
		title: string;
		sections: Section[];
	}

	interface CourseFile {
		id: string;
		name: string;
		size_kb: number;
		type: string;
	}

	interface CourseDetail {
		id: string;
		title: string;
		language: string;
		category: string | null;
		level: string;
		teacher_name: string;
		teacher_profile_image_url?: string;
		objectives: string;
		welcome_message?: string;
		files: CourseFile[];
		chapters: Chapter[];
		enrolled_at: string;
		status: string;
		progress_percentage: number;
		chat_id: string | null;
	}

	let cours: CourseDetail | null = null;
	let estEnChargement = true;
	let erreurChargement = '';
	let chapitresDeveloppes = new Set<string>();

	function normalizeAvatarPath(url?: string | null) {
		if (!url || url.trim() === '') return null;
		const clean = url.split('?')[0].trim();
		if (
			clean.startsWith('http://') ||
			clean.startsWith('https://') ||
			clean.startsWith('/static/') ||
			clean.startsWith('/uploads/') ||
			clean.startsWith('/api/')
		) {
			return clean;
		}
		if (clean.startsWith('/')) return clean;
		return `/uploads/avatars/${clean}`;
	}

	async function chargerDetailsCours() {
		estEnChargement = true;
		erreurChargement = '';
		try {
			const token = localStorage.getItem('token') ?? '';
			cours = await getCourseById(token, courseId);

			if (cours?.chapters?.length) {
				chapitresDeveloppes.add(cours.chapters[0].id);
				chapitresDeveloppes = new Set(chapitresDeveloppes);
			}
		} catch (e: any) {
			erreurChargement = e?.message ?? e ?? 'Erreur lors du chargement';
		} finally {
			estEnChargement = false;
		}
	}

	onMount(() => {
		chargerDetailsCours();

		// Listen for course progress updates and refresh data
		const handleProgressUpdate = (event: CustomEvent) => {
			const { courseId: updatedCourseId } = event.detail;
			if (updatedCourseId === courseId) {
				console.log('[ClassroomDetail] Course progress updated, refreshing data...');
				chargerDetailsCours();
			}
		};

		// Listen for teacher avatar updates and refresh course data
		const handleAvatarUpdate = () => {
			if (cours) {
				chargerDetailsCours();
			}
		};

		if (typeof window !== 'undefined') {
			window.addEventListener('courseProgressUpdated', handleProgressUpdate as EventListener);
			window.addEventListener('avatar-updated', handleAvatarUpdate as EventListener);

			return () => {
				window.removeEventListener('courseProgressUpdated', handleProgressUpdate as EventListener);
				window.removeEventListener('avatar-updated', handleAvatarUpdate as EventListener);
			};
		}
	});

	// ── Progress helpers ───────────────────────────────────────────────────
	$: progressPct = cours?.progress_percentage ?? 0;
	$: progressColor = progressPct >= 100 ? '#10b981' : progressPct >= 50 ? '#3b82f6' : '#f59e0b';
	$: progressLabel =
		progressPct >= 100
			? $i18n.t('Terminé')
			: progressPct > 0
				? `${progressPct}% ${$i18n.t('complété')}`
				: $i18n.t('Pas encore commencé');

	// ── Section status helpers ─────────────────────────────────────────────
	function statusIcon(status: string): string {
		switch (status) {
			case 'completed':
				return '✓';
			case 'in-progress':
				return '→';
			default:
				return '○';
		}
	}
	function statusColor(status: string): string {
		switch (status) {
			case 'completed':
				return '#10b981';
			case 'in-progress':
				return '#f59e0b';
			default:
				return '#94a3b8';
		}
	}

	// ── Misc helpers ───────────────────────────────────────────────────────
	function formaterTaille(kb: number): string {
		if (!kb) return '';
		return kb >= 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`;
	}

	function basculerChapitre(id: string) {
		chapitresDeveloppes.has(id) ? chapitresDeveloppes.delete(id) : chapitresDeveloppes.add(id);
		chapitresDeveloppes = new Set(chapitresDeveloppes);
	}

	// ── Start / Resume learning ────────────────────────────────────────────
	async function demarrerApprentissage() {
		if (!cours) return;

		// Refresh course data to get the latest chat_id from the backend
		// This ensures we don't use stale data if a chat was previously saved
		try {
			const token = localStorage.getItem('token') ?? '';
			const coursLatest = await getCourseById(token, courseId);

			if (coursLatest.chat_id) {
				// Existing chat session - resume it
				localStorage.setItem(
					'resumeCourseChat',
					JSON.stringify({ courseId: coursLatest.id, chatId: coursLatest.chat_id })
				);
				localStorage.removeItem('pendingCourseData');
			} else {
				// New chat session - create one
				localStorage.removeItem('resumeCourseChat');
				localStorage.setItem(
					'pendingCourseData',
					JSON.stringify({ id: coursLatest.id, type: 'course' })
				);
			}
		} catch (e) {
			console.error('Failed to refresh course data:', e);
			// Fallback to current course data if refresh fails
			if (cours.chat_id) {
				localStorage.setItem(
					'resumeCourseChat',
					JSON.stringify({ courseId: cours.id, chatId: cours.chat_id })
				);
				localStorage.removeItem('pendingCourseData');
			} else {
				localStorage.removeItem('resumeCourseChat');
				localStorage.setItem('pendingCourseData', JSON.stringify({ id: cours.id, type: 'course' }));
			}
		}

		goto(`/student/classrooms/${courseId}/learn`);
	}

	$: listeObjectifs = cours?.objectives ? cours.objectives.split('\n').filter((l) => l.trim()) : [];

	$: nombreTotalSections =
		cours?.chapters?.reduce((acc, ch) => acc + (ch.sections?.length ?? 0), 0) ?? 0;

	$: sectionsCompletees =
		cours?.chapters?.reduce(
			(acc, ch) => acc + ch.sections.filter((s) => s.status === 'completed').length,
			0
		) ?? 0;
</script>

<svelte:head>
	<link
		href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

{#if estEnChargement}
	<div class="page-conteneur flex-centre">
		<div class="chargeur"></div>
	</div>
{:else if erreurChargement}
	<div class="page-conteneur flex-centre">
		<div class="boite-erreur">
			<p>{erreurChargement}</p>
			<button class="btn-primaire" on:click={chargerDetailsCours}>
				{$i18n.t('Réessayer')}
			</button>
		</div>
	</div>
{:else if cours}
	<div class="page-conteneur" in:fade={{ duration: 300 }}>
		<button class="btn-retour" on:click={() => goto('/student/classrooms')}>
			← {$i18n.t('Retour aux cours')}
		</button>

		<div class="grille-bento">
			<!-- 1. HERO CARD -->
			<div class="carte carte-hero col-12">
				<div class="en-tete-hero">
					<div class="info-prof">
						<div class="avatar">
							{#if cours.teacher_profile_image_url && normalizeAvatarPath(cours.teacher_profile_image_url)}
								<img
									src={normalizeAvatarPath(cours.teacher_profile_image_url)}
									alt={cours.teacher_name}
									class="avatar-img"
								/>
							{:else}
								{cours.teacher_name?.slice(0, 2).toUpperCase() ?? 'PR'}
							{/if}
						</div>
						<span class="nom-prof">Pr. {cours.teacher_name}</span>
					</div>
					<div class="badges">
						{#if cours.category}
							<span class="etiquette-categorie">{cours.category}</span>
						{/if}
						<span class="etiquette-langue">{cours.language}</span>
					</div>
				</div>

				<h1 class="titre-cours">{cours.title}</h1>

				<p class="texte-bienvenue">
					{cours.welcome_message ||
						$i18n.t(
							'Bienvenue dans ce cours ! Préparez-vous à apprendre et à explorer de nouveaux concepts.'
						)}
				</p>

				<!-- ── PROGRESS BAR ── -->
				<div class="progress-section">
					<div class="progress-header">
						<span class="progress-label-text">{$i18n.t('Progression')}</span>
						<span class="progress-pct-badge" style="color:{progressColor}">
							{progressLabel}
						</span>
					</div>
					<div class="progress-track">
						<div
							class="progress-fill"
							style="width:{progressPct}%; background:{progressColor};"
						></div>
					</div>
					<div class="progress-detail">
						{sectionsCompletees} / {nombreTotalSections}
						{$i18n.t('sections complétées')}
					</div>
				</div>

				<!-- STATS ROW -->
				<div class="statistiques">
					<div class="stat-item">
						<span class="stat-nombre">{cours.chapters?.length ?? 0}</span>
						<span class="stat-libelle">{$i18n.t('Chapitres')}</span>
					</div>
					<div class="stat-separateur"></div>
					<div class="stat-item">
						<span class="stat-nombre">{nombreTotalSections}</span>
						<span class="stat-libelle">{$i18n.t('Sections')}</span>
					</div>
					<div class="stat-separateur"></div>
					<div class="stat-item">
						<span class="stat-nombre">{cours.files?.length ?? 0}</span>
						<span class="stat-libelle">{$i18n.t('Ressources')}</span>
					</div>
				</div>
			</div>

			<!-- 3. RESOURCES CARD -->
			<div class="carte col-6">
				<h2 class="titre-carte">{$i18n.t('Ressources du cours')}</h2>
				<hr class="separateur" />

				{#if cours.files && cours.files.length > 0}
					<div class="liste-ressources">
						{#each cours.files as fichier}
							<div class="item-ressource">
								<div class="icone-ressource">
									<svg
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="2"
										width="20"
										height="20"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
										/>
									</svg>
								</div>
								<div class="info-ressource">
									<p class="nom-ressource">{fichier.name}</p>
									<p class="meta-ressource">PDF • {formaterTaille(fichier.size_kb)}</p>
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<p class="texte-centre texte-muet">{$i18n.t('Aucune ressource disponible')}</p>
				{/if}
			</div>

			<!-- 4. OBJECTIVES CARD -->
			<div class="carte col-6">
				<h2 class="titre-carte">{$i18n.t("Objectifs d'apprentissage")}</h2>
				<hr class="separateur" />

				{#if listeObjectifs.length > 0}
					<p class="texte-carte mb-4">{$i18n.t('À la fin de ce cours, vous serez capable de :')}</p>
					<ol class="liste-objectifs">
						{#each listeObjectifs as objectif}
							<li>{objectif}</li>
						{/each}
					</ol>
				{:else}
					<p class="texte-centre texte-muet">{$i18n.t('Aucun objectif défini')}</p>
				{/if}
			</div>

			<!-- 5. CHAPTERS CARD (full width) -->
			<div class="carte col-12">
				<h2 class="titre-carte">{$i18n.t('Plan de cours')}</h2>
				<hr class="separateur" />

				{#if cours.chapters && cours.chapters.length > 0}
					<div class="liste-chapitres">
						{#each cours.chapters as chapitre, indice (chapitre.id)}
							{@const chCompleted = chapitre.sections.filter(
								(s) => s.status === 'completed'
							).length}
							{@const chTotal = chapitre.sections.length}
							{@const chPct = chTotal > 0 ? Math.round((chCompleted / chTotal) * 100) : 0}

							<div class="bloc-chapitre">
								<button
									class="en-tete-chapitre"
									class:developpe={chapitresDeveloppes.has(chapitre.id)}
									on:click={() => basculerChapitre(chapitre.id)}
								>
									<div class="numero-chapitre">{indice + 1}</div>
									<div class="ch-title-group">
										<span class="titre-chapitre">{chapitre.title}</span>
										<!-- mini progress per chapter -->
										{#if chTotal > 0}
											<div class="ch-mini-progress">
												<div class="ch-mini-track">
													<div
														class="ch-mini-fill"
														style="width:{chPct}%; background:{chPct === 100
															? '#10b981'
															: '#3b82f6'};"
													></div>
												</div>
												<span class="ch-mini-label">{chCompleted}/{chTotal}</span>
											</div>
										{/if}
									</div>
									<span class="nombre-sections">
										{chTotal}
										{$i18n.t('sections')}
									</span>
									<svg
										class="fleche"
										class:tournee={chapitresDeveloppes.has(chapitre.id)}
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										width="18"
										height="18"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M9 18l6-6-6-6"
										/>
									</svg>
								</button>

								{#if chapitresDeveloppes.has(chapitre.id)}
									<div class="contenu-chapitre" transition:slide={{ duration: 250 }}>
										{#if chapitre.sections && chapitre.sections.length > 0}
											<div class="liste-sections">
												{#each chapitre.sections as section (section.id)}
													<div class="item-section">
														<span
															class="status-icon"
															style="color:{statusColor(section.status)};"
															title={section.status}
														>
															{statusIcon(section.status)}
														</span>
														<span class="titre-section">{section.title}</span>
														{#if section.status !== 'not-started'}
															<span
																class="statut-section"
																style="color:{statusColor(section.status)};"
															>
																{section.status === 'completed'
																	? $i18n.t('Terminé')
																	: $i18n.t('En cours')}
															</span>
														{/if}
													</div>
												{/each}
											</div>
										{:else}
											<p class="texte-muet p-4">{$i18n.t('Aucune section disponible')}</p>
										{/if}
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{:else}
					<p class="texte-centre texte-muet">{$i18n.t('Aucun chapitre disponible')}</p>
				{/if}
			</div>
		</div>

		<!-- ACTION BAR -->
		<div class="barre-action">
			<button class="btn-primaire btn-grand" on:click={demarrerApprentissage}>
				{#if cours.chat_id && progressPct > 0}
					{$i18n.t('Reprendre le cours')}
				{:else}
					{$i18n.t("Commencer l'apprentissage")}
				{/if}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="20" height="20">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2.5"
						d="M13 7l5 5m0 0l-5 5m5-5H6"
					/>
				</svg>
			</button>
		</div>
	</div>
{/if}

<style>
	:global(body) {
		background-color: #f8fafc;
		margin: 0;
		padding: 0;
	}

	.page-conteneur {
		font-family:
			'Nunito',
			-apple-system,
			BlinkMacSystemFont,
			sans-serif;
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		color: #334155;
	}
	.flex-centre {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 60vh;
	}

	.btn-retour {
		background: transparent;
		border: none;
		color: #64748b;
		font-family: inherit;
		font-weight: 600;
		font-size: 0.9rem;
		cursor: pointer;
		padding: 0.5rem 0;
		margin-bottom: 1.5rem;
		transition: color 0.2s;
	}
	.btn-retour:hover {
		color: #3b82f6;
	}

	.grille-bento {
		display: grid;
		grid-template-columns: repeat(12, 1fr);
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	.col-4 {
		grid-column: span 4;
	}
	.col-6 {
		grid-column: span 6;
	}
	.col-8 {
		grid-column: span 8;
	}
	.col-12 {
		grid-column: span 12;
	}
	@media (max-width: 1024px) {
		.col-4,
		.col-6,
		.col-8 {
			grid-column: span 12;
		}
	}

	.carte {
		background: #ffffff;
		border-radius: 16px;
		padding: 1.75rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
		border: 1px solid #e2e8f0;
		display: flex;
		flex-direction: column;
	}
	.carte-hero {
		background: linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%);
		border: 1px solid #dbeafe;
	}
	.centre-contenu {
		align-items: center;
		justify-content: center;
		text-align: center;
	}

	.en-tete-hero {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.25rem;
		flex-wrap: wrap;
		gap: 0.75rem;
	}
	.info-prof {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	.avatar {
		width: 40px;
		height: 40px;
		background: linear-gradient(135deg, #3b82f6, #1d4ed8);
		border-radius: 50%;
		display: flex;
		justify-content: center;
		align-items: center;
		font-size: 0.85rem;
		font-weight: 700;
		color: white;
		overflow: hidden;
		flex-shrink: 0;
	}
	.avatar-img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		border-radius: 50%;
	}
	.nom-prof {
		font-size: 0.9rem;
		font-weight: 600;
		color: #475569;
	}
	.badges {
		display: flex;
		gap: 0.5rem;
	}
	.etiquette-categorie {
		background: #dbeafe;
		color: #1e40af;
		padding: 0.3rem 0.75rem;
		border-radius: 20px;
		font-size: 0.75rem;
		font-weight: 700;
	}
	.etiquette-langue {
		background: #f1f5f9;
		color: #64748b;
		padding: 0.3rem 0.75rem;
		border-radius: 20px;
		font-size: 0.75rem;
		font-weight: 600;
	}
	.titre-cours {
		font-size: 1.75rem;
		font-weight: 800;
		color: #1e293b;
		margin: 0 0 0.75rem 0;
		line-height: 1.2;
	}
	.texte-bienvenue {
		font-size: 0.95rem;
		line-height: 1.6;
		color: #475569;
		margin: 0 0 1.25rem 0;
	}

	/* ── PROGRESS BAR ── */
	.progress-section {
		background: rgba(255, 255, 255, 0.7);
		border-radius: 12px;
		padding: 1rem 1.25rem;
		margin-bottom: 1.25rem;
		border: 1px solid rgba(219, 234, 254, 0.6);
	}
	.progress-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.6rem;
	}
	.progress-label-text {
		font-size: 0.8rem;
		font-weight: 700;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	.progress-pct-badge {
		font-size: 0.875rem;
		font-weight: 800;
	}
	.progress-track {
		width: 100%;
		height: 10px;
		background: #e2e8f0;
		border-radius: 9999px;
		overflow: hidden;
		margin-bottom: 0.4rem;
	}
	.progress-fill {
		height: 100%;
		border-radius: 9999px;
		transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
	}
	.progress-detail {
		font-size: 0.75rem;
		color: #94a3b8;
	}

	.statistiques {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		padding-top: 1.25rem;
		border-top: 1px solid #dbeafe;
	}
	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: center;
	}
	.stat-nombre {
		font-size: 1.5rem;
		font-weight: 800;
		color: #1e40af;
	}
	.stat-libelle {
		font-size: 0.75rem;
		font-weight: 600;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}
	.stat-separateur {
		width: 1px;
		height: 40px;
		background: #dbeafe;
	}

	.titre-carte {
		font-size: 1.05rem;
		font-weight: 700;
		color: #334155;
		text-align: center;
		margin: 0 0 1rem 0;
	}
	.separateur {
		border: none;
		border-top: 1px solid #e2e8f0;
		width: 60%;
		margin: 0 auto 1.25rem auto;
	}
	.texte-carte {
		font-size: 0.9rem;
		line-height: 1.6;
		color: #475569;
	}
	.texte-centre {
		text-align: center;
	}
	.texte-muet {
		color: #94a3b8;
		font-size: 0.9rem;
	}
	.mt-auto {
		margin-top: auto;
	}
	.mb-4 {
		margin-bottom: 1rem;
	}
	.p-4 {
		padding: 1rem;
	}

	.btn-outline {
		background: transparent;
		border: 2px solid #cbd5e1;
		color: #475569;
		padding: 0.6rem 1.5rem;
		border-radius: 10px;
		font-weight: 700;
		font-size: 0.85rem;
		font-family: inherit;
		cursor: pointer;
		transition: all 0.2s;
	}
	.btn-outline:hover {
		border-color: #f59e0b;
		color: #d97706;
		background: #fffbeb;
	}

	.liste-ressources {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	.item-ressource {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.875rem;
		background: #f8fafc;
		border-radius: 10px;
		transition: background 0.2s;
	}
	.item-ressource:hover {
		background: #eff6ff;
	}
	.icone-ressource {
		color: #3b82f6;
	}
	.info-ressource {
		flex: 1;
	}
	.nom-ressource {
		font-size: 0.875rem;
		font-weight: 600;
		color: #334155;
		margin: 0 0 0.15rem 0;
	}
	.meta-ressource {
		font-size: 0.75rem;
		color: #94a3b8;
		margin: 0;
	}

	.liste-objectifs {
		margin: 0;
		padding: 0 0 0 1.25rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	.liste-objectifs li {
		font-size: 0.9rem;
		color: #475569;
		line-height: 1.5;
	}

	.liste-chapitres {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	.bloc-chapitre {
		border: 1px solid #e2e8f0;
		border-radius: 12px;
		overflow: hidden;
		transition: border-color 0.2s;
	}
	.bloc-chapitre:hover {
		border-color: #93c5fd;
	}

	.en-tete-chapitre {
		display: flex;
		align-items: center;
		gap: 1rem;
		width: 100%;
		padding: 1rem 1.25rem;
		background: #f8fafc;
		border: none;
		cursor: pointer;
		text-align: left;
		font-family: inherit;
		transition: background 0.2s;
	}
	.en-tete-chapitre:hover,
	.en-tete-chapitre.developpe {
		background: #eff6ff;
	}

	.numero-chapitre {
		width: 32px;
		height: 32px;
		background: linear-gradient(135deg, #3b82f6, #1d4ed8);
		color: white;
		border-radius: 8px;
		display: flex;
		justify-content: center;
		align-items: center;
		font-size: 0.85rem;
		font-weight: 700;
		flex-shrink: 0;
	}

	.ch-title-group {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		min-width: 0;
	}
	.titre-chapitre {
		font-size: 0.95rem;
		font-weight: 600;
		color: #1e293b;
	}

	/* per-chapter mini progress */
	.ch-mini-progress {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.ch-mini-track {
		flex: 1;
		height: 4px;
		background: #e2e8f0;
		border-radius: 9999px;
		overflow: hidden;
		max-width: 120px;
	}
	.ch-mini-fill {
		height: 100%;
		border-radius: 9999px;
		transition: width 0.5s ease;
	}
	.ch-mini-label {
		font-size: 0.7rem;
		color: #94a3b8;
		white-space: nowrap;
	}

	.nombre-sections {
		font-size: 0.75rem;
		font-weight: 600;
		color: #94a3b8;
		background: #f1f5f9;
		padding: 0.25rem 0.6rem;
		border-radius: 12px;
		white-space: nowrap;
	}
	.fleche {
		color: #94a3b8;
		transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		flex-shrink: 0;
	}
	.fleche.tournee {
		transform: rotate(90deg);
		color: #3b82f6;
	}

	.contenu-chapitre {
		background: #ffffff;
		border-top: 1px solid #e2e8f0;
	}
	.liste-sections {
		padding: 0.75rem 1rem 0.75rem 2.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	.item-section {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.55rem 0.875rem;
		border-radius: 8px;
		transition: background 0.2s;
	}
	.item-section:hover {
		background: #f8fafc;
	}

	.status-icon {
		font-size: 0.9rem;
		font-weight: 700;
		width: 18px;
		text-align: center;
		flex-shrink: 0;
	}
	.titre-section {
		flex: 1;
		font-size: 0.875rem;
		color: #475569;
		font-weight: 500;
	}
	.statut-section {
		font-size: 0.7rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.02em;
	}

	.barre-action {
		display: flex;
		justify-content: center;
		padding-top: 0.5rem;
	}

	.btn-primaire {
		background: linear-gradient(135deg, #3b82f6, #1d4ed8);
		color: white;
		border: none;
		padding: 0.75rem 1.75rem;
		border-radius: 12px;
		font-weight: 700;
		font-size: 0.95rem;
		font-family: inherit;
		cursor: pointer;
		box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35);
		transition:
			transform 0.2s,
			box-shadow 0.2s;
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
	}
	.btn-primaire:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(59, 130, 246, 0.45);
	}
	.btn-grand {
		padding: 1rem 2.5rem;
		font-size: 1.05rem;
	}

	.boite-erreur {
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 12px;
		padding: 2rem;
		text-align: center;
	}
	.chargeur {
		width: 44px;
		height: 44px;
		border: 4px solid #e2e8f0;
		border-top: 4px solid #3b82f6;
		border-radius: 50%;
		animation: tourner 0.8s linear infinite;
	}
	@keyframes tourner {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	@media (max-width: 640px) {
		.page-conteneur {
			padding: 1rem;
		}
		.titre-cours {
			font-size: 1.35rem;
		}
		.statistiques {
			flex-wrap: wrap;
			gap: 1rem;
		}
		.stat-separateur {
			display: none;
		}
		.en-tete-hero {
			flex-direction: column;
			align-items: flex-start;
		}
	}
</style>
