<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { TUTOR_API_BASE_URL } from '$lib/constants';

	let data: any = null;
	let loading = true;
	let studentId = '';

	onMount(async () => {
		if (!browser) return;
		const token = localStorage.getItem('token');
		if (!token) { goto('/auth'); return; }
		studentId = localStorage.getItem('parent_student_id') ?? 'e7081ab6-fce1-4111-ae63-74c0e6ae46b6';

		try {
			const res = await fetch(`${TUTOR_API_BASE_URL}/parent/sessions-real/${studentId}`, {
				headers: { authorization: `Bearer ${token}` }
			});
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			data = await res.json();
		} catch (e: any) {
			toast.error(e.message ?? 'Erreur chargement sessions');
		} finally {
			loading = false;
		}
	});

	function meterColor(score: number) {
		return score >= 8 ? '#16A34A' : score >= 6 ? '#2563EB' : '#D97706';
	}
	function statutBg(s: string) { return s === 'complete' ? '#D1FAE5' : '#FEF3C7'; }
	function statutColor(s: string) { return s === 'complete' ? '#065F46' : '#92400E'; }
	function statutText(s: string) { return s === 'complete' ? '✓ Complète' : '⚠️ Partielle'; }
	function subjectIcon(m: string) {
		const map: Record<string, string> = {
			mathematiques:'🔢', francais:'🌍', chimie:'⚗️', physique:'⚛️',
			anglais:'🗣️', histoire:'🏛️', informatique:'💻', svt:'🧬',
			sciences:'🔬', biologie:'🌿'
		};
		return map[m?.toLowerCase()] ?? '📖';
	}
	// Filtrer les themes valides - calculé en script, pas dans le template
	function validThemes(themes: string[]) {
		return themes.filter(t => t && t.length > 0);
	}

	function subjectBg(m: string) {
		const map: Record<string, string> = {
			mathematiques:'#DBEAFE', francais:'#D1FAE5', chimie:'#FEF3C7',
			physique:'#F5F3FF', anglais:'#EDE9FE', informatique:'#DBEAFE',
		};
		return map[m?.toLowerCase()] ?? '#F3F4F6';
	}
</script>

<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:22px;">
	<div>
		<h1 style="font-size:22px;font-weight:700;color:#111827;">Sessions IA</h1>
		<p style="font-size:13px;color:#6B7280;margin-top:4px;">Conversations réelles avec le tuteur IA</p>
	</div>
</div>

{#if loading}
	<div style="display:flex;align-items:center;justify-content:center;height:200px;color:#6B7280;gap:10px;">
		<div style="width:20px;height:20px;border:2px solid #2563EB;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;"></div>
		Chargement des sessions...
	</div>

{:else if !data || data.sessions.length === 0}
	<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:60px;text-align:center;">
		<div style="font-size:48px;margin-bottom:16px;">🤖</div>
		<h3 style="font-size:16px;font-weight:600;margin-bottom:8px;">Aucune session IA pour l'instant</h3>
		<p style="font-size:13px;color:#6B7280;margin-bottom:20px;">Démarrez une session depuis le tableau de bord</p>
		<a href="/parent/dashboard" style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;background:#2563EB;color:#fff;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;">
			← Tableau de bord
		</a>
	</div>

{:else}
	<!-- STATS -->
	<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
		{#each [
			{icon:'🤖', label:'Sessions',          value:data.stats.total_sessions,          color:'#2563EB'},
			{icon:'⏱️', label:'Temps total',        value:data.stats.temps_total,             color:'#2563EB'},
			{icon:'⭐', label:'Score qualité moy.', value:data.stats.score_qualite_moyen,     color:'#16A34A'},
			{icon:'💬', label:'Questions posées',   value:data.stats.total_questions,         color:'#D97706'},
		] as s}
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:12px;">
				<div style="width:40px;height:40px;border-radius:10px;background:#F3F4F6;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">{s.icon}</div>
				<div>
					<div style="font-size:20px;font-weight:800;color:{s.color};">{s.value}</div>
					<div style="font-size:11px;color:#6B7280;">{s.label}</div>
				</div>
			</div>
		{/each}
	</div>

	<!-- CARTES SESSIONS -->
	<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:14px;">
		{#each data.sessions as s}
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;overflow:hidden;">

				<!-- EN-TÊTE -->
				<div style="padding:14px 16px;border-bottom:1px solid #E5E7EB;display:flex;align-items:flex-start;gap:12px;">
					<div style="width:40px;height:40px;border-radius:10px;background:{subjectBg(s.matiere)};display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">{subjectIcon(s.matiere)}</div>
					<div style="flex:1;">
						<div style="font-size:14px;font-weight:600;margin-bottom:3px;">{s.titre}</div>
						<div style="font-size:11px;color:#6B7280;display:flex;gap:10px;">
							<span>📅 {s.date}</span>
							<span>⏱️ {s.duree_min} min</span>
							<span>💬 {s.nb_messages_ia} réponses IA</span>
						</div>
					</div>
					<div style="text-align:right;flex-shrink:0;">
						<div style="font-size:20px;font-weight:800;color:{meterColor(s.score_qualite)};line-height:1;">{s.score_qualite}</div>
						<div style="font-size:9px;font-weight:700;text-transform:uppercase;color:{meterColor(s.score_qualite)};">Qualité</div>
					</div>
				</div>

				<!-- CORPS -->
				<div style="padding:14px 16px;">
					<!-- TAGS -->
					{#if validThemes(s.themes).length > 0}
					<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
						{#each validThemes(s.themes) as t}
							<span style="padding:3px 9px;border-radius:4px;font-size:11px;font-weight:600;background:#DBEAFE;color:#1E40AF;">{t}</span>
						{/each}
					</div>
					{/if}

					<!-- QUESTIONS -->
					{#if s.questions.length > 0}
					<div style="font-size:10px;font-weight:700;text-transform:uppercase;color:#6B7280;letter-spacing:.5px;margin-bottom:7px;">💬 Questions posées</div>
					{#each s.questions as q, i}
						<div style="display:flex;gap:6px;margin-bottom:5px;">
							<div style="width:17px;height:17px;border-radius:50%;background:#F3F4F6;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;flex-shrink:0;color:#6B7280;">{i+1}</div>
							<div style="font-size:12px;line-height:1.4;color:#374151;">{q}</div>
						</div>
					{/each}
					{/if}

					<!-- RÉSUMÉ / DERNIÈRE RÉPONSE IA -->
					{#if s.resume}
					<div style="background:{s.statut === 'complete' ? '#EFF6FF' : '#FFFBEB'};border:1px solid {s.statut === 'complete' ? '#BFDBFE' : '#FCD34D'};border-radius:6px;padding:10px 12px;margin:10px 0;">
						<div style="font-size:11px;font-weight:700;color:{s.statut === 'complete' ? '#1E40AF' : '#92400E'};margin-bottom:4px;">🤖 Dernière réponse IA</div>
						<div style="font-size:12px;color:{s.statut === 'complete' ? '#1E40AF' : '#78350F'};line-height:1.5;">{s.resume}</div>
					</div>
					{/if}

					<!-- PROGRESSION -->
					<div style="margin-bottom:8px;">
						<div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px;">
							<span style="color:#6B7280;">Progression</span>
							<span style="font-weight:700;color:{meterColor(s.progress/10)};">{s.progress}%</span>
						</div>
						<div style="height:5px;background:#F3F4F6;border-radius:10px;overflow:hidden;">
							<div style="height:100%;width:{s.progress}%;background:{meterColor(s.progress/10)};border-radius:10px;transition:width .5s;"></div>
						</div>
					</div>

					<!-- INDICATEURS -->
					{#each [['Engagement', s.engagement],['Compréhension', s.comprehension],['Autonomie', s.autonomie]] as [label, val]}
						<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
							<div style="font-size:11px;color:#6B7280;width:90px;flex-shrink:0;">{label}</div>
							<div style="flex:1;height:5px;background:#F3F4F6;border-radius:10px;overflow:hidden;">
								<div style="height:100%;width:{val*10}%;background:{meterColor(val)};border-radius:10px;"></div>
							</div>
							<div style="font-size:11px;font-weight:700;color:{meterColor(val)};width:28px;text-align:right;">{val}</div>
						</div>
					{/each}
				</div>

				<!-- PIED -->
				<div style="padding:10px 16px;border-top:1px solid #E5E7EB;background:#F9FAFB;display:flex;align-items:center;justify-content:space-between;">
					<a href="/parent/c/{s.id}" style="font-size:12px;font-weight:600;color:#2563EB;text-decoration:none;">Voir la conversation →</a>
					<span style="font-size:11px;font-weight:700;padding:3px 8px;border-radius:4px;background:{statutBg(s.statut)};color:{statutColor(s.statut)};">{statutText(s.statut)}</span>
				</div>
			</div>
		{/each}
	</div>
{/if}

<style>
	@keyframes spin { to { transform: rotate(360deg); } }
</style>