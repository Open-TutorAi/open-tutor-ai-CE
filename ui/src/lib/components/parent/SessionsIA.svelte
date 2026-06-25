<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { user } from '$lib/stores';
	import {
		getIASessions,
		getIASessionDetail,
		getIASessionTranscript,
		type SessionSummary,
		type SessionStats,
		type SessionDetail
	} from '$lib/apis/ia-sessions';

	const i18n = getContext('i18n');

	// ── État ──────────────────────────────────────────────────────────────────
	let loading = true;
	let error: string | null = null;
	let sessions: SessionSummary[] = [];
	let stats: SessionStats = { total: 0, avec_alerte: 0, score_moyen: 0 };
	let selectedSession: SessionDetail | null = null;
	let transcript: string | null = null;
	let showTranscript = false;
	let loadingDetail = false;
	let filterSubject = '';

	// Demo child_id — à remplacer par sélecteur enfant réel
	const CHILD_ID = 'demo-child-001';

	// ── Chargement ────────────────────────────────────────────────────────────
	onMount(async () => {
		await loadSessions();
	});

	async function loadSessions() {
		loading = true;
		error = null;
		try {
			const token = localStorage.getItem('token') ?? '';
			const data = await getIASessions(token, CHILD_ID, filterSubject || undefined);
			if (data) {
				sessions = data.sessions;
				stats = data.stats;
			} else {
				error = 'Impossible de charger les sessions.';
			}
		} catch (e) {
			error = 'Erreur réseau.';
		} finally {
			loading = false;
		}
	}

	async function openDetail(session: SessionSummary) {
		loadingDetail = true;
		selectedSession = null;
		transcript = null;
		showTranscript = false;
		const token = localStorage.getItem('token') ?? '';
		const detail = await getIASessionDetail(token, session.id, CHILD_ID);
		selectedSession = detail;
		loadingDetail = false;
	}

	async function loadTranscript() {
		if (!selectedSession) return;
		showTranscript = true;
		const token = localStorage.getItem('token') ?? '';
		const result = await getIASessionTranscript(token, selectedSession.id, CHILD_ID);
		transcript = result?.transcript_text ?? 'Transcription indisponible.';
	}

	function closeDetail() {
		selectedSession = null;
		transcript = null;
		showTranscript = false;
	}

	function qualiteColor(score: number): string {
		if (score >= 8) return 'text-green-600 dark:text-green-400';
		if (score >= 6) return 'text-yellow-600 dark:text-yellow-400';
		return 'text-red-600 dark:text-red-400';
	}

	function qualiteBg(score: number): string {
		if (score >= 8)
			return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
		if (score >= 6)
			return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
		return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
	}
</script>

<!-- ── KPI Cards ──────────────────────────────────────────────────────────── -->
<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
	<div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow text-center">
		<p class="text-2xl font-bold text-blue-600">{stats.total}</p>
		<p class="text-sm text-gray-500 dark:text-gray-400">Sessions totales</p>
	</div>
	<div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow text-center">
		<p class="text-2xl font-bold {qualiteColor(stats.score_moyen)}">{stats.score_moyen}/10</p>
		<p class="text-sm text-gray-500 dark:text-gray-400">Score moyen</p>
	</div>
	<div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow text-center">
		<p class="text-2xl font-bold text-red-500">{stats.avec_alerte}</p>
		<p class="text-sm text-gray-500 dark:text-gray-400">Alertes</p>
	</div>
	<div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow text-center">
		<p class="text-2xl font-bold text-purple-600">{stats.total}</p>
		<p class="text-sm text-gray-500 dark:text-gray-400">Ce mois</p>
	</div>
</div>

<!-- ── Filtre ─────────────────────────────────────────────────────────────── -->
<div class="flex gap-3 mb-6">
	<input
		type="text"
		placeholder="Filtrer par matière..."
		bind:value={filterSubject}
		class="flex-1 px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700
		       bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200
		       focus:outline-none focus:ring-2 focus:ring-blue-400"
	/>
	<button
		on:click={loadSessions}
		class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition"
	>
		Rechercher
	</button>
</div>

<!-- ── Contenu principal ──────────────────────────────────────────────────── -->
{#if loading}
	<div class="flex justify-center py-16">
		<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
	</div>
{:else if error}
	<div
		class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center"
	>
		<p class="text-red-600 dark:text-red-400">{error}</p>
		<button
			on:click={loadSessions}
			class="mt-3 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
		>
			Réessayer
		</button>
	</div>
{:else if sessions.length === 0}
	<div class="text-center py-16 text-gray-400">
		<p class="text-4xl mb-3">📚</p>
		<p>Aucune session trouvée.</p>
	</div>
{:else}
	<!-- Liste des sessions -->
	<div class="space-y-3">
		{#each sessions as session}
			<button
				class="w-full text-left border rounded-xl p-4 transition hover:shadow-md {qualiteBg(
					session.quality_score
				)}"
				on:click={() => openDetail(session)}
			>
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-3">
						{#if session.alerte_difficulte}
							<span class="text-red-500 text-lg" title="Difficulté détectée">⚠️</span>
						{:else}
							<span class="text-green-500 text-lg">✅</span>
						{/if}
						<div>
							<p class="font-semibold text-gray-800 dark:text-gray-200">{session.matiere}</p>
							<p class="text-xs text-gray-500 dark:text-gray-400">{session.duree_minutes} min</p>
						</div>
					</div>
					<div class="text-right">
						<p class="text-xl font-bold {qualiteColor(session.quality_score)}">
							{session.quality_score}/10
						</p>
						<p class="text-xs text-gray-400 capitalize">{session.statut}</p>
					</div>
				</div>
				{#if session.themes.length > 0}
					<div class="mt-2 flex flex-wrap gap-1">
						{#each session.themes as theme}
							<span
								class="text-xs bg-white/60 dark:bg-gray-700/60 px-2 py-0.5 rounded-full text-gray-600 dark:text-gray-300"
							>
								{theme}
							</span>
						{/each}
					</div>
				{/if}
			</button>
		{/each}
	</div>
{/if}

<!-- ── Panneau de détail ──────────────────────────────────────────────────── -->
{#if loadingDetail}
	<div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
		<div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-400"></div>
	</div>
{/if}

{#if selectedSession}
	<div class="fixed inset-0 bg-black/50 flex items-end md:items-center justify-center z-50 p-4">
		<div
			class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto"
		>
			<!-- Header -->
			<div
				class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700"
			>
				<div>
					<h2 class="text-xl font-bold text-gray-800 dark:text-white">{selectedSession.matiere}</h2>
					<p class="text-sm text-gray-500">
						{selectedSession.duree_minutes} min · {selectedSession.statut}
					</p>
				</div>
				<button
					on:click={closeDetail}
					class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl">✕</button
				>
			</div>

			<!-- Corps -->
			<div class="p-6 space-y-5">
				<!-- Score -->
				<div class="flex items-center gap-4">
					<div class="text-4xl font-bold {qualiteColor(selectedSession.quality_score)}">
						{selectedSession.quality_score}/10
					</div>
					{#if selectedSession.alerte_difficulte}
						<span
							class="px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-full text-sm font-medium"
						>
							⚠️ Difficulté détectée
						</span>
					{/if}
				</div>

				<!-- Métriques -->
				{#if selectedSession.metriques}
					<div class="grid grid-cols-3 gap-3">
						<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center">
							<p class="text-lg font-bold text-blue-600">
								{selectedSession.metriques.engagement}/10
							</p>
							<p class="text-xs text-gray-500">Engagement</p>
						</div>
						<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center">
							<p class="text-lg font-bold text-purple-600">
								{selectedSession.metriques.comprehension}/10
							</p>
							<p class="text-xs text-gray-500">Compréhension</p>
						</div>
						<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center">
							<p class="text-lg font-bold text-green-600">
								{selectedSession.metriques.autonomie}/10
							</p>
							<p class="text-xs text-gray-500">Autonomie</p>
						</div>
					</div>
				{/if}

				<!-- Résumé IA -->
				{#if selectedSession.resume}
					<div class="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
						<p class="text-sm font-semibold text-blue-700 dark:text-blue-300 mb-1">📝 Résumé IA</p>
						<p class="text-sm text-gray-700 dark:text-gray-300">{selectedSession.resume}</p>
					</div>
				{/if}

				<!-- Questions posées -->
				{#if selectedSession.questions.length > 0}
					<div>
						<p class="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">
							❓ Questions posées
						</p>
						<ul class="space-y-1">
							{#each selectedSession.questions as q}
								<li
									class="text-sm text-gray-700 dark:text-gray-300 pl-3 border-l-2 border-blue-300"
								>
									{q}
								</li>
							{/each}
						</ul>
					</div>
				{/if}

				<!-- Transcription -->
				{#if !showTranscript}
					<button
						on:click={loadTranscript}
						class="w-full py-2 border border-blue-300 dark:border-blue-700 text-blue-600 dark:text-blue-400
						       rounded-lg text-sm hover:bg-blue-50 dark:hover:bg-blue-900/20 transition"
					>
						Voir la transcription complète
					</button>
				{:else if transcript}
					<div class="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 max-h-48 overflow-y-auto">
						<p class="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">
							💬 Transcription
						</p>
						<p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{transcript}</p>
					</div>
				{:else}
					<div class="flex justify-center py-4">
						<div class="animate-spin rounded-full h-6 w-6 border-t-2 border-blue-400"></div>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
