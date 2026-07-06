<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import Robot from '$lib/components/icons/Robot.svelte';
	import Clock from '$lib/components/icons/Clock.svelte';
	import Star from '$lib/components/icons/Star.svelte';
	import ChartBar from '$lib/components/icons/ChartBar.svelte';
	import AlertTriangle from '$lib/components/icons/AlertTriangle.svelte';
	import ChatBubble from '$lib/components/icons/ChatBubble.svelte';
	const i18n = getContext('i18n');
	import { user } from '$lib/stores';
	import {
		getIASessions,
		getIASessionDetail,
		getIASessionTranscript,
		type SessionSummary,
		type SessionStats,
		type SessionDetail
	} from '$lib/apis/ia-sessions';

	// ── État ──────────────────────────────────────────────────────────────────
	let loading = true;
	let error: string | null = null;
	let sessions: SessionSummary[] = [];
	let stats: SessionStats = { total: 0, avec_alerte: 0, score_moyen: 0 };
	let selectedSession: SessionDetail | null = null;
	let transcript: string | null = null;
	let showTranscript = false;
	let loadingDetail = false;
	let activeFilter = 'Toutes';
	let searchQuery = '';
	let visibleCount = 8;

	const CHILD_ID = 'demo-child-001';
	const CHILD_NAME = $user?.name ? $user.name.split(' ')[0] : 'votre enfant';

	const filters = ['Toutes', 'Maths', 'Français', 'Physique', 'Anglais'];

	// ── Sessions filtrées ─────────────────────────────────────────────────────
	$: filteredSessions = sessions.filter((s) => {
		const matchFilter =
			activeFilter === 'Toutes' || s.matiere.toLowerCase().includes(activeFilter.toLowerCase());
		const matchSearch = !searchQuery || s.matiere.toLowerCase().includes(searchQuery.toLowerCase());
		return matchFilter && matchSearch;
	});

	$: visibleSessions = filteredSessions.slice(0, visibleCount);
	$: remaining = filteredSessions.length - visibleSessions.length;

	// ── KPI dérivés ───────────────────────────────────────────────────────────
	$: totalMinutes = sessions.reduce((acc, s) => acc + s.duree_minutes, 0);
	$: totalQuestions = sessions.reduce((acc, s) => acc + s.questions.length, 0);
	$: heures = Math.floor(totalMinutes / 60);
	$: mins = totalMinutes % 60;

	onMount(async () => {
		await loadLinkedStudent();
		if (CHILD_ID) await loadSessions();
	});

	async function loadSessions() {
		loading = true;
		error = null;
		try {
			const token = localStorage.getItem('token') ?? '';
			const data = await getIASessions(token, CHILD_ID);
			if (data) {
				sessions = data.sessions;
				stats = data.stats;
			} else {
				error = 'Impossible de charger les sessions.';
			}
		} catch {
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
		selectedSession = await getIASessionDetail(token, session.id, CHILD_ID);
		loadingDetail = false;
	}

	async function loadTranscript() {
		if (!selectedSession) return;
		showTranscript = true;
		const token = localStorage.getItem('token') ?? '';
		const res = await getIASessionTranscript(token, selectedSession.id, CHILD_ID);
		transcript = res?.transcript_text ?? 'Transcription indisponible.';
	}

	function closeDetail() {
		selectedSession = null;
		transcript = null;
		showTranscript = false;
	}

	function scoreColor(score: number) {
		if (score >= 8) return 'text-green-500';
		if (score >= 6) return 'text-orange-400';
		return 'text-red-500';
	}

	function barColor(score: number) {
		if (score >= 8) return 'bg-green-400';
		if (score >= 6) return 'bg-orange-400';
		return 'bg-red-400';
	}

	function matiereIcon(matiere: string) {
		if (matiere.toLowerCase().includes('math')) return '📐';
		if (matiere.toLowerCase().includes('physique')) return '⚗️';
		if (matiere.toLowerCase().includes('français')) return '📖';
		if (matiere.toLowerCase().includes('anglais')) return '🌐';
		if (matiere.toLowerCase().includes('histoire')) return '🏛️';
		return '📚';
	}
</script>

<!-- ── Header ──────────────────────────────────────────────────────────────── -->
<div class="mb-6">
	<h1 class="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
		Sessions IA de {CHILD_NAME} 🤖
	</h1>
	<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
		Résumés générés automatiquement après chaque session
	</p>
</div>

<!-- ── KPI Cards ──────────────────────────────────────────────────────────── -->
<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
	<div class="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm flex items-center gap-3">
		<Robot className="size-8 text-blue-600" />
		<div>
			<p class="text-2xl font-bold text-gray-800 dark:text-white">{stats.total}</p>
			<p class="text-xs text-gray-500">{$i18n.t('Sessions this month')}</p>
		</div>
	</div>
	<div class="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm flex items-center gap-3">
		<Clock className="size-8 text-blue-600" />
		<div>
			<p class="text-2xl font-bold text-gray-800 dark:text-white">
				{heures}h{mins > 0 ? mins : ''}
			</p>
			<p class="text-xs text-gray-500">{$i18n.t('Total AI time')}</p>
		</div>
	</div>
	<div class="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm flex items-center gap-3">
		<Star className="size-8 text-yellow-500" />
		<div>
			<p class="text-2xl font-bold {scoreColor(stats.score_moyen)}">{stats.score_moyen}</p>
			<p class="text-xs text-gray-500">{$i18n.t('Avg quality score')}</p>
		</div>
	</div>
	<div class="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm flex items-center gap-3">
		<ChartBar className="size-8 text-purple-600" />
		<div>
			<p class="text-2xl font-bold text-gray-800 dark:text-white">{totalQuestions}</p>
			<p class="text-xs text-gray-500">{$i18n.t('Questions asked')}</p>
		</div>
	</div>
</div>

<!-- ── Filtres + Recherche ────────────────────────────────────────────────── -->
<div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 mb-6">
	<div class="flex gap-2 flex-wrap">
		{#each filters as f}
			<button
				on:click={() => (activeFilter = f)}
				class="px-4 py-1.5 rounded-full text-sm font-medium transition
					{activeFilter === f
					? 'bg-blue-600 text-white'
					: 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'}"
			>
				{f}{activeFilter === f && stats.total > 0 ? ` (${filteredSessions.length})` : ''}
			</button>
		{/each}
	</div>
	<div
		class="flex items-center bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full px-4 py-2 gap-2 w-full md:w-56"
	>
		<svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
			/>
		</svg>
		<input
			type="text"
			placeholder="Rechercher..."
			bind:value={searchQuery}
			class="bg-transparent border-none outline-none text-sm w-full text-gray-700 dark:text-gray-300"
		/>
	</div>
</div>

<!-- ── Contenu ────────────────────────────────────────────────────────────── -->
{#if loading}
	<div class="flex justify-center py-16">
		<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-gray-300 dark:border-gray-600"></div>
	</div>
{:else if error}
	<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-xl p-6 text-center">
		<p class="text-red-600">{error}</p>
		<button on:click={loadSessions} class="mt-3 px-4 py-2 bg-red-500 text-white rounded-lg"
			>Réessayer</button
		>
	</div>
{:else if visibleSessions.length === 0}
	<div class="text-center py-16 text-gray-400">
		<p class="text-4xl mb-3">📚</p>
		<p>{$i18n.t('No sessions found.')}</p>
	</div>
{:else}
	<!-- Grille 4 colonnes -->
	<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
		{#each visibleSessions as session (session.id)}
			<div
				class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 flex flex-col gap-3 hover:shadow-md transition cursor-pointer"
				on:click={() => openDetail(session)}
			>
				<!-- Header carte -->
				<div class="flex items-start justify-between">
					<div class="flex items-center gap-2">
						<span class="text-xl">{matiereIcon(session.matiere)}</span>
						<div>
							<p class="font-semibold text-gray-800 dark:text-white text-sm leading-tight">
								{session.matiere}
							</p>
							<p class="text-xs text-gray-400">{session.duree_minutes} min</p>
						</div>
					</div>
					<div class="text-right">
						<p class="text-lg font-bold {scoreColor(session.quality_score)}">
							{session.quality_score}
						</p>
						<p class="text-xs text-gray-400 uppercase tracking-wide">Qualité</p>
					</div>
				</div>

				<!-- Alerte -->
				{#if session.alerte_difficulte}
					<div
						class="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-2"
					>
						<p class="text-xs text-orange-700 dark:text-orange-300 font-medium">
							⚠️ Attention requise
						</p>
					</div>
				{/if}

				<!-- Thèmes -->
				{#if session.themes.length > 0}
					<div class="flex flex-wrap gap-1">
						{#each session.themes.slice(0, 3) as theme}
							<span
								class="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-full"
								>{theme}</span
							>
						{/each}
					</div>
				{/if}

				<!-- Questions -->
				{#if session.questions.length > 0}
					<div>
						<p class="text-xs text-gray-500 font-medium mb-1">
							QUESTIONS POSÉES ({session.questions.length})
						</p>
						<ul class="space-y-1">
							{#each session.questions.slice(0, 2) as q}
								<li class="text-xs text-gray-600 dark:text-gray-400 flex gap-1">
									<span class="text-gray-400 flex-shrink-0">›</span>
									<span class="line-clamp-2">{q}</span>
								</li>
							{/each}
						</ul>
					</div>
				{/if}

				<!-- Résumé IA -->
				{#if session.resume}
					<div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-2">
						<p class="text-xs text-blue-600 dark:text-blue-400 font-medium mb-1">
							🤖 Résumé automatique
						</p>
						<p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-3">{session.resume}</p>
					</div>
				{/if}

				<!-- Métriques barres -->
				{#if session.metriques}
					<div class="space-y-1.5">
						{#each [['Engagement', session.metriques.engagement], ['Compréhension', session.metriques.comprehension], ['Autonomie', session.metriques.autonomie]] as [label, val]}
							<div class="flex items-center gap-2">
								<span class="text-xs text-gray-500 w-24 flex-shrink-0">{label}</span>
								<div class="flex-1 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
									<div
										class="h-full {barColor(Number(val))} rounded-full transition-all"
										style="width: {Number(val) * 10}%"
									></div>
								</div>
								<span class="text-xs font-medium text-gray-600 dark:text-gray-400 w-6 text-right"
									>{val}</span
								>
							</div>
						{/each}
					</div>
				{/if}

				<!-- Footer -->
				<div
					class="flex items-center justify-between pt-1 border-t border-gray-100 dark:border-gray-700"
				>
					<span class="text-xs text-gray-600 dark:text-gray-400 hover:underline">Voir la transcription →</span>
					<span
						class="text-xs {session.statut === 'terminee' ? 'text-green-500' : 'text-orange-400'}"
					>
						{session.statut === 'terminee' ? '✓ Complète' : '⚠ Partielle'}
					</span>
				</div>
			</div>
		{/each}
	</div>

	<!-- Afficher plus -->
	{#if remaining > 0}
		<div class="flex justify-center mt-6">
			<button
				on:click={() => (visibleCount += 8)}
				class="px-6 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700
				       text-gray-700 dark:text-gray-300 rounded-full text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition shadow-sm"
			>
				Afficher plus ({remaining} restantes)
			</button>
		</div>
	{/if}
{/if}

<!-- ── Modal détail ───────────────────────────────────────────────────────── -->
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
			<div
				class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700"
			>
				<div>
					<h2 class="text-xl font-bold text-gray-800 dark:text-white">
						{matiereIcon(selectedSession.matiere)}
						{selectedSession.matiere}
					</h2>
					<p class="text-sm text-gray-500">
						{selectedSession.duree_minutes} min · {selectedSession.statut}
					</p>
				</div>
				<button on:click={closeDetail} class="text-gray-400 hover:text-gray-600 text-2xl">✕</button>
			</div>

			<div class="p-6 space-y-5">
				<div class="flex items-center gap-4">
					<p class="text-4xl font-bold {scoreColor(selectedSession.quality_score)}">
						{selectedSession.quality_score}/10
					</p>
					{#if selectedSession.alerte_difficulte}
						<span
							class="px-3 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-600 rounded-full text-sm font-medium"
							>⚠️ Difficulté détectée</span
						>
					{/if}
				</div>

				{#if selectedSession.metriques}
					<div class="grid grid-cols-3 gap-3">
						{#each [['Engagement', selectedSession.metriques.engagement, 'blue'], ['Compréhension', selectedSession.metriques.comprehension, 'purple'], ['Autonomie', selectedSession.metriques.autonomie, 'green']] as [label, val, color]}
							<div class="bg-gray-50 dark:bg-gray-800 rounded-xl p-3 text-center">
								<p class="text-lg font-bold text-{color}-600">{val}</p>
								<p class="text-xs text-gray-500">{label}</p>
							</div>
						{/each}
					</div>
				{/if}

				{#if selectedSession.resume}
					<div class="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
						<p class="text-sm font-semibold text-blue-700 dark:text-blue-300 mb-1">🤖 Résumé IA</p>
						<p class="text-sm text-gray-700 dark:text-gray-300">{selectedSession.resume}</p>
					</div>
				{/if}

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

				{#if !showTranscript}
					<button
						on:click={loadTranscript}
						class="w-full py-2 border border-blue-300 dark:border-blue-700 text-blue-600 dark:text-blue-400
						       rounded-lg text-sm hover:bg-blue-50 dark:hover:bg-blue-900/20 transition"
					>
						Voir la transcription complète →
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
