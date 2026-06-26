<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { page } from '$app/stores';
	import { user, models, settings, config } from '$lib/stores';
	import { getModels } from '$lib/apis';
	import { get } from 'svelte/store';

	const navItems = [
		{ key: 'dashboard',     href: '/parent/dashboard',      icon: '⊞', label: 'Tableau de bord'     },
		{ key: 'create',        href: '/parent/support/create', icon: '✦', label: 'Créer un soutien'    },
		{ key: 'evaluations',   href: '/parent/evaluations',    icon: '📋', label: 'Évaluations'          },
		{ key: 'sessions',      href: '/parent/sessions',       icon: '🤖', label: 'Sessions IA'           },
		{ key: 'notifications', href: '/parent/notifications',  icon: '🔔', label: 'Notifications'         },
		{ key: 'settings',      href: '/parent/settings',       icon: '⚙',  label: 'Profil et paramètres' },
	];

	$: currentPath = $page.url.pathname;
	$: activeKey = navItems.find(n => currentPath.startsWith(n.href))?.key ?? '';
	$: firstName = $user?.name?.split(' ')[0] ?? 'Pro';
	$: initials = ($user?.name ?? 'PA').split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase();
	let showMenu = false;

	function signOut() {
		localStorage.removeItem('token');
		window.location.href = '/auth';
	}

	onMount(async () => {
		if (!browser) return;
		// Forcer le scroll — le student layout bloque overflow sur html et body
		document.documentElement.style.setProperty('overflow-y', 'auto', 'important');
		document.documentElement.style.setProperty('height', 'auto', 'important');
		document.body.style.setProperty('overflow-y', 'auto', 'important');
		document.body.style.setProperty('height', 'auto', 'important');
		document.documentElement.classList.remove('overflow-hidden');
		document.body.classList.remove('overflow-hidden', 'h-screen');

		const token = localStorage.getItem('token');
		if (!token) { goto('/auth'); return; }

		// Charger les modèles IA — même logique que le student layout
		try {
			const cfg = get(config);
			const sett = get(settings);
			models.set(
				await getModels(
					token,
					cfg?.features?.enable_direct_connections && (sett?.directConnections ?? null)
				)
			);
		} catch (e) {
			console.error('Erreur chargement modèles parent:', e);
		}
	});

	onDestroy(() => {
		if (!browser) return;
		document.documentElement.style.removeProperty('overflow-y');
		document.documentElement.style.removeProperty('height');
		document.body.style.removeProperty('overflow-y');
		document.body.style.removeProperty('height');
	});
</script>

<svelte:head>
	<style>
		html, body { overflow-y: auto !important; height: auto !important; }
	</style>
</svelte:head>

<div style="display:flex;background:#F3F4F6;font-family:'Segoe UI',system-ui,sans-serif;font-size:14px;">

	<!-- SIDEBAR fixe -->
	<aside style="width:220px;background:#fff;border-right:1px solid #E5E7EB;display:flex;flex-direction:column;position:fixed;top:0;left:0;bottom:0;z-index:50;overflow-y:auto;">
		<div style="padding:16px 20px;border-bottom:1px solid #E5E7EB;flex-shrink:0;">
			<a href="/parent/dashboard" style="text-decoration:none;display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;background:#2563EB;border-radius:10px;font-weight:900;font-size:14px;letter-spacing:-1px;">
				<span style="color:#fff;">O</span><span style="color:#93C5FD;">T</span>
			</a>
		</div>
		<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:#9CA3AF;padding:14px 20px 6px;">PARENT PORTAL</div>
		<nav style="flex:1;">
			{#each navItems as item}
				<a href={item.href}
					style="display:flex;align-items:center;gap:10px;padding:9px 20px;text-decoration:none;font-size:13.5px;font-weight:500;
					{activeKey === item.key ? 'background:#2563EB;color:#fff;' : 'color:#6B7280;'}">
					<span style="width:18px;text-align:center;font-size:15px;">{item.icon}</span>
					{item.label}
				</a>
			{/each}
		</nav>
		<div style="padding:14px 20px;font-size:11px;color:#9CA3AF;border-top:1px solid #E5E7EB;flex-shrink:0;">
			© 2025 OpenTutorAI
		</div>
	</aside>

	<!-- MAIN -->
	<div style="margin-left:220px;flex:1;display:flex;flex-direction:column;">
		<!-- HEADER sticky -->
		<header style="background:#fff;border-bottom:1px solid #E5E7EB;height:60px;display:flex;align-items:center;padding:0 28px;gap:14px;position:sticky;top:0;z-index:40;flex-shrink:0;">
			<div style="flex:1;">
				<div style="font-size:16px;font-weight:700;">Bonjour {firstName} 👋</div>
				<div style="font-size:12px;color:#6B7280;">Bienvenue dans votre espace parent</div>
			</div>
			<div style="display:flex;align-items:center;gap:8px;border:1px solid #E5E7EB;border-radius:20px;padding:6px 14px;background:#F3F4F6;width:180px;">
				<span style="color:#9CA3AF;font-size:13px;">🔍</span>
				<input placeholder="Recherche" style="border:none;background:none;font-size:13px;outline:none;width:100%;"/>
			</div>
			<a href="/parent/notifications" style="width:34px;height:34px;border-radius:50%;border:1px solid #E5E7EB;display:flex;align-items:center;justify-content:center;text-decoration:none;font-size:15px;color:#6B7280;">🔔</a>
			<!-- AVATAR + DROPDOWN -->
			<div style="position:relative;">
				<button on:click={() => showMenu = !showMenu}
					style="width:34px;height:34px;border-radius:50%;background:#2563EB;color:white;font-weight:700;font-size:12px;display:flex;align-items:center;justify-content:center;border:none;cursor:pointer;">
					{initials}
				</button>
				{#if showMenu}
					<!-- Overlay pour fermer -->
					<button on:click={() => showMenu = false}
						style="position:fixed;inset:0;z-index:49;background:transparent;border:none;cursor:default;"
						aria-label="Fermer le menu">
					</button>
					<!-- Dropdown -->
					<div style="position:absolute;right:0;top:42px;background:#fff;border:1px solid #E5E7EB;border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,.12);width:220px;z-index:50;overflow:hidden;">
						<!-- Infos user -->
						<div style="padding:14px 16px;border-bottom:1px solid #F3F4F6;">
							<div style="font-size:13px;font-weight:700;color:#111827;">{$user?.name ?? '—'}</div>
							<div style="font-size:12px;color:#6B7280;margin-top:2px;">{$user?.email ?? '—'}</div>
						</div>
						<!-- Bouton déconnexion -->
						<button on:click={signOut}
							style="display:flex;align-items:center;gap:10px;width:100%;padding:12px 16px;border:none;background:#fff;cursor:pointer;font-family:inherit;font-size:13px;color:#DC2626;font-weight:600;transition:background .15s;"
							on:mouseover={(e) => e.currentTarget.style.background='#FEF2F2'}
							on:mouseout={(e) => e.currentTarget.style.background='#fff'}>
							<span>→</span> Déconnexion
						</button>
					</div>
				{/if}
			</div>
		</header>

		<!-- PAGE -->
		<div style="padding:28px;">
			<slot />
		</div>
	</div>
</div>