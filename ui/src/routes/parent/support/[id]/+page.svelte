<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { toast } from 'svelte-sonner';
	import { getChildSupportDetail } from '$lib/apis/parent';

	let support: any = null;
	let loading = true;
	$: supportId = $page.params.id;

	onMount(async () => {
		if (!browser) return;
		const token = localStorage.getItem('token');
		if (!token) { goto('/auth'); return; }
		try {
			support = await getChildSupportDetail(token, supportId);
		} catch (e: any) {
			toast.error(e.message ?? 'Erreur');
		} finally {
			loading = false;
		}
	});

	function subjectIcon(s: string) {
		const map: Record<string, string> = {
			mathematiques:'📊', informatique:'💻', francais:'📚',
			anglais:'🗣️', sciences:'🔬', histoire:'🏛️', physique:'⚛️',
			chimie:'⚗️', biologie:'🌿', svt:'🧬', geographie:'🌍',
		};
		return map[s?.toLowerCase()] ?? '📖';
	}
	function statusLabel(s: string) {
		return s === 'active' ? '🟢 Actif' : s === 'completed' ? '✅ Terminé' : '🟡 En attente';
	}
	function formatDate(d: string) {
		return d ? new Date(d).toLocaleDateString('fr-FR', {day:'2-digit', month:'long', year:'numeric'}) : '';
	}
</script>

<!-- BREADCRUMB -->
<div style="display:flex;align-items:center;gap:8px;margin-bottom:20px;font-size:13px;color:#6B7280;">
	<a href="/parent/dashboard" style="color:#2563EB;text-decoration:none;">← Tableau de bord</a>
	<span>/</span>
	<span>Détail du soutien</span>
</div>

{#if loading}
	<div style="display:flex;align-items:center;justify-content:center;height:200px;color:#6B7280;gap:10px;">
		<div style="width:20px;height:20px;border:2px solid #2563EB;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;"></div>
		Chargement...
	</div>

{:else if !support}
	<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:48px;text-align:center;">
		<div style="font-size:40px;margin-bottom:12px;">❌</div>
		<h3 style="font-weight:600;margin-bottom:8px;">Soutien introuvable</h3>
		<a href="/parent/dashboard" style="color:#2563EB;">← Retour au tableau de bord</a>
	</div>

{:else}

	<!-- EN-TÊTE -->
	<div style="background:linear-gradient(135deg,#1E3A8A,#2563EB);border-radius:10px;padding:24px 28px;color:#fff;margin-bottom:20px;">
		<div style="display:flex;align-items:flex-start;gap:16px;">
			<div style="width:56px;height:56px;border-radius:14px;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0;">
				{subjectIcon(support.subject)}
			</div>
			<div style="flex:1;">
				<h1 style="font-size:20px;font-weight:700;margin-bottom:6px;">{support.title}</h1>
				<div style="display:flex;gap:10px;flex-wrap:wrap;opacity:.9;font-size:13px;">
					{#if support.subject}<span>📖 {support.subject}</span>{/if}
					{#if support.level}<span>🎓 {support.level}</span>{/if}
					{#if support.estimated_duration}<span>⏱️ {support.estimated_duration}</span>{/if}
					<span>{statusLabel(support.status)}</span>
				</div>
			</div>
			<!-- Bouton chat IA -->
			{#if support.chat_id}
				<a href="/parent/c/{support.chat_id}"
					style="display:flex;align-items:center;gap:8px;padding:10px 18px;background:#fff;color:#2563EB;border-radius:8px;font-size:13px;font-weight:700;text-decoration:none;flex-shrink:0;">
					🤖 Voir la session IA
				</a>
			{:else}
				<div style="padding:10px 18px;background:rgba(255,255,255,.15);border-radius:8px;font-size:12px;color:rgba(255,255,255,.8);flex-shrink:0;text-align:center;">
					🤖 Session IA<br>pas encore démarrée
				</div>
			{/if}
		</div>
	</div>

	<!-- GRILLE DÉTAILS -->
	<div style="display:grid;grid-template-columns:2fr 1fr;gap:16px;">

		<!-- COLONNE GAUCHE -->
		<div style="display:flex;flex-direction:column;gap:16px;">

			<!-- DESCRIPTION -->
			{#if support.short_description}
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:20px;">
				<h3 style="font-size:13px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;">Description</h3>
				<p style="font-size:14px;color:#374151;line-height:1.7;">{support.short_description}</p>
			</div>
			{/if}

			<!-- OBJECTIF PÉDAGOGIQUE -->
			{#if support.learning_objective}
			<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;padding:20px;">
				<h3 style="font-size:13px;font-weight:700;color:#1E40AF;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;">🎯 Objectif pédagogique</h3>
				<p style="font-size:14px;color:#1E40AF;line-height:1.7;">{support.learning_objective}</p>
			</div>
			{/if}

			<!-- FICHIERS JOINTS -->
			{#if support.files && support.files.length > 0}
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:20px;">
				<h3 style="font-size:13px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px;">📎 Ressources jointes ({support.files.length})</h3>
				<div style="display:flex;flex-direction:column;gap:8px;">
					{#each support.files as file}
						<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:#F9FAFB;border:1px solid #E5E7EB;border-radius:6px;">
							<span style="font-size:18px;">📄</span>
							<span style="font-size:13px;color:#374151;">{file.filename}</span>
						</div>
					{/each}
				</div>
			</div>
			{/if}

			<!-- STATUT CHAT IA -->
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:20px;">
				<h3 style="font-size:13px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px;">🤖 Session IA</h3>
				{#if support.chat_id}
					<div style="background:#D1FAE5;border-radius:6px;padding:14px;display:flex;align-items:center;gap:12px;">
						<span style="font-size:22px;">✅</span>
						<div>
							<div style="font-size:13px;font-weight:600;color:#065F46;">Session démarrée !</div>
							<div style="font-size:12px;color:#065F46;margin-top:2px;">Votre enfant a déjà commencé à utiliser le tuteur IA.</div>
						</div>
						<a href="/parent/c/{support.chat_id}"
							style="margin-left:auto;padding:8px 14px;background:#16A34A;color:#fff;border-radius:6px;font-size:12px;font-weight:600;text-decoration:none;">
							Voir le chat →
						</a>
					</div>
				{:else}
					<div style="background:#FEF3C7;border-radius:6px;padding:14px;display:flex;align-items:center;gap:12px;">
						<span style="font-size:22px;">⏳</span>
						<div>
							<div style="font-size:13px;font-weight:600;color:#92400E;">En attente de démarrage</div>
							<div style="font-size:12px;color:#92400E;margin-top:2px;">Votre enfant n'a pas encore démarré la session avec le tuteur IA.</div>
						</div>
					</div>
				{/if}
			</div>
		</div>

		<!-- COLONNE DROITE -->
		<div style="display:flex;flex-direction:column;gap:16px;">

			<!-- INFOS -->
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:20px;">
				<h3 style="font-size:13px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.5px;margin-bottom:14px;">Informations</h3>
				<div style="display:flex;flex-direction:column;gap:12px;">
					{#each [
						{label:'Statut', value: statusLabel(support.status)},
						{label:'Type', value: support.learning_type ?? '—'},
						{label:'Langue', value: support.content_language ?? '—'},
						{label:'Durée', value: support.estimated_duration ?? '—'},
						{label:'Créé le', value: formatDate(support.created_at)},
						{label:'Mis à jour', value: formatDate(support.updated_at)},
					] as info}
						<div style="display:flex;justify-content:space-between;align-items:center;padding-bottom:10px;border-bottom:1px solid #F3F4F6;">
							<span style="font-size:12px;color:#6B7280;">{info.label}</span>
							<span style="font-size:12px;font-weight:600;color:#111827;">{info.value}</span>
						</div>
					{/each}
				</div>
			</div>

			<!-- MOTS-CLÉS -->
			{#if support.keywords}
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:20px;">
				<h3 style="font-size:13px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;">Mots-clés</h3>
				<div style="display:flex;flex-wrap:wrap;gap:6px;">
					{#each (typeof support.keywords === 'string' ? support.keywords.split(',') : support.keywords) as kw}
						<span style="background:#DBEAFE;color:#1E40AF;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;">{kw.trim()}</span>
					{/each}
				</div>
			</div>
			{/if}

			<!-- ACTIONS -->
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:20px;">
				<h3 style="font-size:13px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.5px;margin-bottom:14px;">Actions</h3>
				<div style="display:flex;flex-direction:column;gap:10px;">
					<a href="/parent/support/create"
						style="display:flex;align-items:center;justify-content:center;gap:8px;padding:10px;background:#2563EB;color:#fff;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;">
						✦ Créer un autre soutien
					</a>
					<a href="/parent/dashboard"
						style="display:flex;align-items:center;justify-content:center;gap:8px;padding:10px;background:#F3F4F6;color:#374151;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;">
						← Retour au tableau de bord
					</a>
				</div>
			</div>
		</div>
	</div>

{/if}

<style>
	@keyframes spin { to { transform: rotate(360deg); } }
</style>