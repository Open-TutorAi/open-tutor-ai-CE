<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { listChildSupports } from '$lib/apis/parent';

	let supports: any[] = [];
	let loading = true;
	let studentId = '';
	let studentName = '';
	let filtre = 'tous';

	const filtres = [
		{ key: 'tous',      label: 'Tous'       },
		{ key: 'pending',   label: 'En attente' },
		{ key: 'active',    label: 'Actifs'     },
		{ key: 'completed', label: 'Terminés'   },
	];

	$: supportsFiltres = filtre === 'tous'
		? supports
		: supports.filter(s => s.status === filtre);

	onMount(async () => {
		if (!browser) return;
		const token = localStorage.getItem('token');
		if (!token) { goto('/auth'); return; }
		studentId = localStorage.getItem('parent_student_id') ?? 'e7081ab6-fce1-4111-ae63-74c0e6ae46b6';
		studentName = localStorage.getItem('parent_student_name') ?? '';
		try {
			supports = await listChildSupports(token, studentId);
		} catch (e: any) {
			toast.error(e.message ?? 'Erreur lors du chargement');
		} finally {
			loading = false;
		}
	});

	// ── Ouvrir le chat IA pour ce soutien ──────────────────────────────────
	function ouvrirChatIA(support: any) {
		if (support.chat_id) {
			// Chat déjà existant → voir la conversation
			goto(`/parent/c/${support.chat_id}`);
		} else {
			// Pas encore de chat → en démarrer un nouveau
			// Même mécanisme que SupportDetails.svelte
			localStorage.setItem('pendingSupportData', JSON.stringify({
				id: support.id,
				title: support.title,
				timestamp: Date.now(),
				attempts: 0
			}));
			goto('/parent/chat');
		}
	}

	function subjectIcon(s: string) {
		const map: Record<string, string> = {
			mathematiques:'📊', informatique:'💻', francais:'📚',
			anglais:'🗣️', sciences:'🔬', histoire:'🏛️', physique:'⚛️',
			chimie:'⚗️', biologie:'🌿', svt:'🧬', geographie:'🌍',
		};
		return map[s?.toLowerCase()] ?? '📖';
	}

	function statusStyle(s: string) {
		if (s === 'active')    return { bg:'#D1FAE5', color:'#065F46', label:'Actif' };
		if (s === 'completed') return { bg:'#DBEAFE', color:'#1E40AF', label:'Terminé' };
		return { bg:'#FEF3C7', color:'#92400E', label:'En attente' };
	}

	function formatDate(d: string) {
		return new Date(d).toLocaleDateString('fr-FR', { day:'2-digit', month:'short', year:'numeric' });
	}
</script>

<!-- TITRE + BOUTON CRÉER -->
<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:24px;">
	<div>
		<h1 style="font-size:22px;font-weight:700;color:#111827;">Tableau de bord</h1>
		<p style="font-size:13px;color:#6B7280;margin-top:4px;">
			Soutiens créés pour <strong>{studentName || 'votre enfant'}</strong>
		</p>
	</div>
	<a href="/parent/support/create"
		style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;background:#2563EB;color:#fff;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;">
		✦ Créer un soutien
	</a>
</div>

<!-- STATS -->
{#if !loading}
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px;">
	{#each [
		{ label:'Total soutiens',  value:supports.length,                                        color:'#2563EB' },
		{ label:'Actifs',          value:supports.filter(s=>s.status==='active').length,          color:'#16A34A' },
		{ label:'En attente',      value:supports.filter(s=>s.status==='pending').length,         color:'#D97706' },
		{ label:'Terminés',        value:supports.filter(s=>s.status==='completed').length,       color:'#7C3AED' },
	] as stat}
		<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:16px;border-top:3px solid {stat.color};">
			<div style="font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">{stat.label}</div>
			<div style="font-size:28px;font-weight:800;color:{stat.color};">{stat.value}</div>
		</div>
	{/each}
</div>
{/if}

<!-- FILTRES -->
<div style="display:flex;gap:8px;margin-bottom:16px;">
	{#each filtres as f}
		<button on:click={() => filtre = f.key}
			style="padding:6px 16px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;border:1px solid #E5E7EB;
			{filtre === f.key ? 'background:#2563EB;color:#fff;border-color:#2563EB;' : 'background:#fff;color:#6B7280;'}">
			{f.label}
		</button>
	{/each}
</div>

<!-- LISTE DES SOUTIENS -->
{#if loading}
	<div style="display:flex;align-items:center;justify-content:center;height:200px;color:#6B7280;gap:10px;">
		<div style="width:20px;height:20px;border:2px solid #2563EB;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;"></div>
		Chargement...
	</div>

{:else if supportsFiltres.length === 0}
	<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:60px;text-align:center;">
		<div style="font-size:48px;margin-bottom:16px;">📚</div>
		<h3 style="font-size:16px;font-weight:600;color:#111827;margin-bottom:8px;">Aucun soutien trouvé</h3>
		<a href="/parent/support/create"
			style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;background:#2563EB;color:#fff;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;margin-top:12px;">
			✦ Créer le premier soutien
		</a>
	</div>

{:else}
	<div style="display:flex;flex-direction:column;gap:12px;">
		{#each supportsFiltres as support}
			{@const st = statusStyle(support.status)}
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;overflow:hidden;">

				<div style="padding:16px 20px;display:flex;align-items:flex-start;gap:16px;">
					<!-- ICÔNE -->
					<div style="width:48px;height:48px;border-radius:12px;background:#EFF6FF;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">
						{subjectIcon(support.subject)}
					</div>

					<!-- INFOS -->
					<div style="flex:1;min-width:0;">
						<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
							<h3 style="font-size:15px;font-weight:600;color:#111827;">{support.title}</h3>
							<span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:20px;background:{st.bg};color:{st.color};flex-shrink:0;">{st.label}</span>
						</div>
						{#if support.short_description}
							<p style="font-size:13px;color:#6B7280;margin-bottom:8px;">{support.short_description}</p>
						{/if}
						<div style="display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:#6B7280;">
							{#if support.subject}<span>📖 {support.subject}</span>{/if}
							{#if support.level}<span>🎓 {support.level}</span>{/if}
							{#if support.estimated_duration}<span>⏱️ {support.estimated_duration}</span>{/if}
							<span>📅 {formatDate(support.created_at)}</span>
						</div>
					</div>

					<!-- ACTIONS -->
					<div style="display:flex;flex-direction:column;gap:8px;flex-shrink:0;min-width:160px;">

						<!-- BOUTON PRINCIPAL : Ouvrir / Démarrer le chat IA -->
						<button on:click={() => ouvrirChatIA(support)}
							style="display:flex;align-items:center;justify-content:center;gap:6px;padding:9px 14px;border-radius:8px;border:none;cursor:pointer;font-size:13px;font-weight:700;width:100%;
							background:{support.chat_id ? '#16A34A' : '#2563EB'};color:#fff;">
							{#if support.chat_id}
								💬 Voir la session IA
							{:else}
								🚀 Démarrer la session IA
							{/if}
						</button>

						<!-- Voir les détails -->
						<a href="/parent/support/{support.id}"
							style="display:flex;align-items:center;justify-content:center;gap:6px;padding:8px 14px;border-radius:8px;border:1px solid #E5E7EB;background:#fff;color:#374151;font-size:12px;font-weight:600;text-decoration:none;width:100%;box-sizing:border-box;">
							📋 Voir les détails
						</a>
					</div>
				</div>

				<!-- OBJECTIF -->
				{#if support.learning_objective}
					<div style="padding:10px 20px;background:#F9FAFB;border-top:1px solid #F3F4F6;font-size:12px;color:#6B7280;display:flex;gap:8px;">
						<span style="color:#2563EB;flex-shrink:0;">🎯</span>
						<span><strong style="color:#374151;">Objectif :</strong> {support.learning_objective}</span>
					</div>
				{/if}
			</div>
		{/each}
	</div>
{/if}

<style>
	@keyframes spin { to { transform: rotate(360deg); } }
</style>