<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getNotifications, marquerLue } from '$lib/apis/parent';

	let data: any = null;
	let loading = true;
	let filtre = 'Toutes';
	const filtres = ['Toutes','Résultats','Recommandations IA','Alertes','Rapports'];

	// Compteurs calculés en script (pas dans le template)
	$: nbResultats    = data ? data.notifications.filter((n: any) => n.type === 'resultat').length : 0;
	$: nbAlertes      = data ? data.notifications.filter((n: any) => n.type === 'alerte').length : 0;
	$: nbIa           = data ? data.notifications.filter((n: any) => n.type === 'ia').length : 0;
	$: notifsFiltrees = data ? data.notifications.filter((n: any) => {
		if (filtre === 'Toutes') return true;
		if (filtre === 'Résultats') return n.type === 'resultat';
		if (filtre === 'Recommandations IA') return n.type === 'ia';
		if (filtre === 'Alertes') return n.type === 'alerte';
		if (filtre === 'Rapports') return n.type === 'rapport';
		return true;
	}) : [];

	onMount(async () => {
		if (!browser) return;
		const token = localStorage.getItem('token');
		if (!token) { goto('/auth'); return; }
		try {
			data = await getNotifications(token);
		} catch (e: any) { toast.error(e.message); }
		finally { loading = false; }
	});

	async function marquer(id: string) {
		const token = localStorage.getItem('token') ?? '';
		await marquerLue(token, id);
		data.notifications = data.notifications.map((n: any) => n.id === id ? { ...n, lu: true } : n);
		data.stats.non_lues = Math.max(0, data.stats.non_lues - 1);
		data = data; // trigger reactivity
	}

	async function toutMarquerLu() {
		const token = localStorage.getItem('token') ?? '';
		for (const n of data.notifications) {
			if (!n.lu) await marquerLue(token, n.id);
		}
		data.notifications = data.notifications.map((n: any) => ({ ...n, lu: true }));
		data.stats.non_lues = 0;
		data = data;
		toast.success('Toutes les notifications marquées comme lues');
	}

	function iconNotif(type: string) {
		return type === 'resultat' ? '🏆' : type === 'ia' ? '🤖' : type === 'soutien' ? '✅' : type === 'alerte' ? '⚠️' : '📊';
	}
	function bgNotif(type: string) {
		return type === 'resultat' ? '#D1FAE5' : type === 'ia' ? '#DBEAFE' : type === 'soutien' ? '#D1FAE5' : type === 'alerte' ? '#FEF3C7' : '#F3F4F6';
	}
	function actionLabel(type: string) {
		return type === 'alerte' ? '✦ Créer un soutien →' : type === 'resultat' ? '📊 Voir les évaluations →' : 'Voir →';
	}
	function naviguer(n: any) {
		if (!n.lu) marquer(n.id);
		if (n.action_url) goto(n.action_url);
	}
</script>

<div>

	<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:22px;">
		<div>
			<h1 style="font-size:20px;font-weight:700;">Notifications</h1>
			{#if data}<p style="font-size:13px;color:#6B7280;margin-top:2px;">{data.stats.non_lues} non lue{data.stats.non_lues > 1 ? 's' : ''} sur {data.stats.total}</p>{/if}
		</div>
		{#if data?.stats?.non_lues > 0}
			<button on:click={toutMarquerLu} style="padding:8px 16px;border-radius:8px;border:1px solid #E5E7EB;background:#fff;color:#2563EB;font-size:13px;font-weight:600;cursor:pointer;">✓ Tout marquer comme lu</button>
		{/if}
	</div>

	{#if loading}
		<div style="display:flex;align-items:center;justify-content:center;height:200px;color:#6B7280;">⏳ Chargement...</div>
	{:else if data}

		<!-- STATS -->
		<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:12px;">
				<div style="width:38px;height:38px;border-radius:8px;background:#DBEAFE;display:flex;align-items:center;justify-content:center;font-size:17px;">🔵</div>
				<div><div style="font-size:22px;font-weight:800;color:#1E40AF;">{data.stats.non_lues}</div><div style="font-size:11px;color:#6B7280;">Non lues</div></div>
			</div>
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:12px;">
				<div style="width:38px;height:38px;border-radius:8px;background:#D1FAE5;display:flex;align-items:center;justify-content:center;font-size:17px;">🏆</div>
				<div><div style="font-size:22px;font-weight:800;color:#065F46;">{nbResultats}</div><div style="font-size:11px;color:#6B7280;">Résultats</div></div>
			</div>
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:12px;">
				<div style="width:38px;height:38px;border-radius:8px;background:#FEF3C7;display:flex;align-items:center;justify-content:center;font-size:17px;">⚠️</div>
				<div><div style="font-size:22px;font-weight:800;color:#92400E;">{nbAlertes}</div><div style="font-size:11px;color:#6B7280;">Alertes</div></div>
			</div>
			<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:12px;">
				<div style="width:38px;height:38px;border-radius:8px;background:#F5F3FF;display:flex;align-items:center;justify-content:center;font-size:17px;">🤖</div>
				<div><div style="font-size:22px;font-weight:800;color:#6D28D9;">{nbIa}</div><div style="font-size:11px;color:#6B7280;">Reco. IA</div></div>
			</div>
		</div>

		<!-- FILTRES -->
		<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
			{#each filtres as f}
				<button on:click={() => filtre = f}
					style="padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;border:1px solid #E5E7EB;transition:all .15s;
					{filtre === f ? 'background:#2563EB;color:#fff;border-color:#2563EB;' : 'background:#fff;color:#6B7280;'}">
					{f}
				</button>
			{/each}
		</div>

		<!-- LISTE -->
		<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;overflow:hidden;">
			{#if notifsFiltrees.length === 0}
				<div style="padding:48px;text-align:center;color:#6B7280;">
					<div style="font-size:36px;margin-bottom:12px;">🔔</div>
					<div style="font-size:14px;font-weight:600;">Aucune notification</div>
				</div>
			{:else}
				{#each notifsFiltrees as n}
					<button on:click={() => naviguer(n)}
						style="display:flex;align-items:flex-start;gap:14px;padding:16px 20px;border-bottom:1px solid #F3F4F6;width:100%;background:{!n.lu ? '#F8FAFF' : '#fff'};border-left:none;border-right:none;border-top:none;cursor:pointer;text-align:left;">
						<div style="width:42px;height:42px;border-radius:10px;background:{bgNotif(n.type)};display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;">{iconNotif(n.type)}</div>
						<div style="flex:1;">
							<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;">
								<div style="font-size:14px;font-weight:{n.lu ? '500' : '700'};color:#111827;">{n.titre}</div>
								<div style="font-size:11px;color:#9CA3AF;white-space:nowrap;flex-shrink:0;">{n.date}</div>
							</div>
							<div style="font-size:13px;color:#6B7280;margin-top:4px;line-height:1.5;">{n.desc}</div>
							{#if n.action_url}
								<div style="margin-top:8px;font-size:12px;color:#2563EB;font-weight:600;">{actionLabel(n.type)}</div>
							{/if}
						</div>
						{#if !n.lu}<div style="width:10px;height:10px;border-radius:50%;background:#2563EB;flex-shrink:0;margin-top:4px;"></div>{/if}
					</button>
				{/each}
			{/if}
		</div>

		<!-- PRÉFÉRENCES -->
		<div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;overflow:hidden;margin-top:16px;">
			<div style="padding:14px 20px;border-bottom:1px solid #E5E7EB;font-size:14px;font-weight:600;">⚙️ Préférences de notification</div>
			<div style="padding:16px 20px;display:flex;flex-direction:column;gap:14px;">
				{#each [
					{label:"Résultats d'évaluation", desc:'Recevoir une notification pour chaque nouvelle note', on:true},
					{label:'Recommandations IA',      desc:'Suggestions du tuteur après chaque session',          on:true},
					{label:'Alertes de progression',  desc:'Alerte si le score descend sous 60/100',             on:true},
					{label:'Rapport hebdomadaire',    desc:'Résumé de la semaine chaque lundi matin',            on:false},
				] as pref}
					<div style="display:flex;align-items:center;justify-content:space-between;gap:16px;">
						<div>
							<div style="font-size:13px;font-weight:600;color:#111827;">{pref.label}</div>
							<div style="font-size:12px;color:#6B7280;margin-top:1px;">{pref.desc}</div>
						</div>
						<div style="width:44px;height:24px;border-radius:12px;background:{pref.on ? '#2563EB' : '#D1D5DB'};position:relative;cursor:pointer;flex-shrink:0;">
							<div style="width:20px;height:20px;border-radius:50%;background:#fff;position:absolute;top:2px;left:{pref.on ? '22px' : '2px'};transition:left .2s;"></div>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>