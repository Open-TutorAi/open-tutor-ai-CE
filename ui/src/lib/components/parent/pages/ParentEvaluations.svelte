<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { TUTOR_API_BASE_URL } from '$lib/constants';

	let evaluations: any[] = [];
	let sessions: any[] = [];
	let loading = true;
	let generating = false;
	let studentId = '';
	let showGenerateModal = false;
	let selectedSession: any = null;

	onMount(async () => {
		if (!browser) return;
		const token = localStorage.getItem('token');
		if (!token) { goto('/auth'); return; }
		studentId = localStorage.getItem('parent_student_id') ?? 'e7081ab6-fce1-4111-ae63-74c0e6ae46b6';
		await loadAll(token);
	});

	async function loadAll(token: string) {
		loading = true;
		try {
			const [evalRes, sessRes] = await Promise.all([
				fetch(`${TUTOR_API_BASE_URL}/parent/evaluations/by-student/${studentId}`, { headers: { authorization: `Bearer ${token}` } }),
				fetch(`${TUTOR_API_BASE_URL}/parent/sessions-real/${studentId}`, { headers: { authorization: `Bearer ${token}` } }),
			]);
			if (evalRes.ok) evaluations = await evalRes.json();
			if (sessRes.ok) { const d = await sessRes.json(); sessions = d.sessions ?? []; }
		} catch (e: any) { toast.error(e.message); }
		finally { loading = false; }
	}

	async function generateEval(session: any) {
		const token = localStorage.getItem('token');
		if (!token) return;
		generating = true;
		showGenerateModal = false;
		toast.info('🤖 L\'IA génère les questions... (30-60 secondes)');
		try {
			const res = await fetch(`${TUTOR_API_BASE_URL}/parent/evaluations/generate`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json', authorization: `Bearer ${token}` },
				body: JSON.stringify({
					chat_id: session.id,
					support_id: session.support_id,
					student_id: studentId
				})
			});
			if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
			const newEval = await res.json();
			evaluations = [newEval, ...evaluations];
			toast.success('✅ Évaluation générée ! Cliquez pour la passer.');
		} catch (e: any) {
			toast.error(e.message ?? 'Erreur génération');
		} finally { generating = false; }
	}

	// Variables réactives calculées en script
	$: completedCount = evaluations.filter(e => e.status === 'completed').length;
	$: avgScore = (() => {
		const scored = evaluations.filter(e => e.score != null);
		return scored.length > 0 ? Math.round(scored.reduce((a, e) => a + e.score, 0) / scored.length) + '/100' : '—';
	})();

	function scoreColor(s: number) {
		return s >= 80 ? '#16A34A' : s >= 60 ? '#D97706' : '#DC2626';
	}
	function scoreBg(s: number) {
		return s >= 80 ? '#D1FAE5' : s >= 60 ? '#FEF3C7' : '#FEE2E2';
	}
	function formatDate(d: string) {
		return d ? new Date(d).toLocaleDateString('fr-FR', { day:'2-digit', month:'short', year:'numeric' }) : '';
	}
</script>

<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:24px;">
	<div>
		<h1 style="font-size:22px;font-weight:700;color:#111827;">Évaluations</h1>
		<p style="font-size:13px;color:#6B7280;margin-top:4px;">QCM générés par l'IA depuis les sessions</p>
	</div>
	<button on:click={() => showGenerateModal = true} disabled={sessions.length === 0 || generating}
		style="display:flex;align-items:center;gap:8px;padding:10px 18px;background:#2563EB;color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;">
		{#if generating}
			<div style="width:16px;height:16px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;"></div>
			Génération...
		{:else}
			🤖 Générer une évaluation IA
		{/if}
	</button>
</div>

<!-- MODAL CHOIX SESSION -->
{#if showGenerateModal}
<div style="position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;display:flex;align-items:center;justify-content:center;" on:click={() => showGenerateModal=false} role="dialog" aria-modal="true">
	<div style="background:#fff;border-radius:12px;padding:24px;width:560px;max-height:80vh;overflow-y:auto;" on:click|stopPropagation role="presentation">
		<h3 style="font-size:16px;font-weight:700;margin-bottom:6px;">Choisir une session</h3>
		<p style="font-size:13px;color:#6B7280;margin-bottom:16px;">L'IA va lire la conversation et générer 10 questions QCM.</p>
		<div style="display:flex;flex-direction:column;gap:10px;">
			{#each sessions as s}
				<button on:click={() => generateEval(s)}
					style="display:flex;align-items:center;gap:14px;padding:14px;border:1px solid #E5E7EB;border-radius:8px;background:#fff;cursor:pointer;text-align:left;font-family:inherit;transition:border-color .15s;"
	>
					<div style="width:42px;height:42px;border-radius:10px;background:#EFF6FF;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;">📚</div>
					<div style="flex:1;">
						<div style="font-size:14px;font-weight:600;">{s.titre}</div>
						<div style="font-size:12px;color:#6B7280;margin-top:2px;">{s.date} · {s.duree_min} min · {s.nb_messages_ia} réponses IA</div>
					</div>
					<div style="font-size:22px;">→</div>
				</button>
			{/each}
		</div>
		<button on:click={() => showGenerateModal=false} style="margin-top:14px;width:100%;padding:9px;border:1px solid #E5E7EB;border-radius:8px;background:#F9FAFB;color:#374151;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;">Annuler</button>
	</div>
</div>
{/if}

{#if loading}
	<div style="display:flex;align-items:center;justify-content:center;height:200px;color:#6B7280;gap:10px;">
		<div style="width:20px;height:20px;border:2px solid #2563EB;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;"></div>
		Chargement...
	</div>

{:else if evaluations.length === 0}
	<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:60px;text-align:center;">
		<div style="font-size:48px;margin-bottom:16px;">📝</div>
		<h3 style="font-size:16px;font-weight:600;margin-bottom:8px;">Aucune évaluation pour l'instant</h3>
		<p style="font-size:13px;color:#6B7280;margin-bottom:20px;">Générez une évaluation depuis une session IA</p>
		{#if sessions.length > 0}
			<button on:click={() => showGenerateModal=true}
				style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;background:#2563EB;color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;">
				🤖 Générer ma première évaluation
			</button>
		{:else}
			<p style="font-size:13px;color:#9CA3AF;">Commencez par démarrer une session IA depuis le tableau de bord</p>
		{/if}
	</div>

{:else}
	<!-- STATS RAPIDES -->
	<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;">
		{#each [
			{label:'Total évaluations', value:evaluations.length, color:'#2563EB'},
			{label:'Terminées', value:completedCount, color:'#16A34A'},
			{label:'Score moyen', value: avgScore, color:'#D97706'},
		] as s}
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:16px;border-top:3px solid {s.color};">
				<div style="font-size:11px;color:#6B7280;text-transform:uppercase;font-weight:600;letter-spacing:.5px;margin-bottom:6px;">{s.label}</div>
				<div style="font-size:26px;font-weight:800;color:{s.color};">{s.value}</div>
			</div>
		{/each}
	</div>

	<!-- LISTE ÉVALUATIONS -->
	<div style="display:flex;flex-direction:column;gap:12px;">
		{#each evaluations as ev}
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;overflow:hidden;">
				<div style="padding:16px 20px;display:flex;align-items:center;gap:16px;">
					<!-- ICÔNE SCORE -->
					<div style="width:56px;height:56px;border-radius:12px;background:{ev.status==='completed' ? scoreBg(ev.score) : '#F3F4F6'};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
						{#if ev.status === 'completed'}
							<div style="text-align:center;">
								<div style="font-size:18px;font-weight:900;color:{scoreColor(ev.score)};line-height:1;">{ev.score}</div>
								<div style="font-size:8px;color:{scoreColor(ev.score)};font-weight:700;">/100</div>
							</div>
						{:else}
							<span style="font-size:22px;">📝</span>
						{/if}
					</div>

					<!-- INFOS -->
					<div style="flex:1;">
						<div style="font-size:15px;font-weight:600;color:#111827;margin-bottom:4px;">{ev.title}</div>
						<div style="font-size:12px;color:#6B7280;display:flex;gap:14px;flex-wrap:wrap;">
							{#if ev.subject}<span>📖 {ev.subject}</span>{/if}
							<span>❓ {ev.questions?.length ?? 0} questions</span>
							<span>📅 {formatDate(ev.created_at)}</span>
							{#if ev.status === 'completed'}
								<span style="color:#16A34A;font-weight:600;">✓ {ev.nb_correct}/{ev.nb_total} correctes</span>
							{/if}
						</div>
					</div>

					<!-- STATUT + BOUTON -->
					<div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;flex-shrink:0;">
						{#if ev.status === 'pending'}
							<span style="font-size:11px;background:#FEF3C7;color:#92400E;padding:3px 10px;border-radius:20px;font-weight:600;">En attente</span>
							<a href="/parent/evaluation/{ev.id}"
								style="padding:8px 16px;background:#2563EB;color:#fff;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;">
								▶ Passer le QCM
							</a>
						{:else}
							<span style="font-size:11px;background:{scoreBg(ev.score)};color:{scoreColor(ev.score)};padding:3px 10px;border-radius:20px;font-weight:700;">
								{ev.score >= 80 ? '🎉 Excellent' : ev.score >= 60 ? '👍 Bien' : '💪 À retravailler'}
							</span>
							<a href="/parent/evaluation/{ev.id}"
								style="padding:8px 16px;background:#F3F4F6;color:#374151;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;">
								📋 Voir les résultats
							</a>
						{/if}
					</div>
				</div>
			</div>
		{/each}
	</div>
{/if}

<style>
	@keyframes spin { to { transform: rotate(360deg); } }
</style>