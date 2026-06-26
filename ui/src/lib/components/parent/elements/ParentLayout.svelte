<script lang="ts">
	import { user } from '$lib/stores';
	import { goto } from '$app/navigation';
	export let activePage: string = 'dashboard';

	const navItems = [
		{ key: 'dashboard',   href: '/parent/dashboard',      icon: '⊞', label: 'Tableau de bord'    },
		{ key: 'create',      href: '/parent/support/create', icon: '✦', label: 'Créer un soutien'   },
		{ key: 'evaluations', href: '/parent/evaluations',    icon: '📋', label: 'Évaluations'         },
		{ key: 'sessions',    href: '/parent/sessions',       icon: '🤖', label: 'Sessions IA'          },
		{ key: 'notifications',href: '/parent/notifications', icon: '🔔', label: 'Notifications'        },
		{ key: 'settings',    href: '/parent/settings',       icon: '⚙',  label: 'Profil et paramètres' },
	];

	$: initials = ($user?.name ?? 'PA').split(' ').map((n: string) => n[0]).join('').slice(0,2).toUpperCase();
	$: firstName = $user?.name?.split(' ')[0] ?? 'Pro';
</script>

<div style="display:flex; min-height:100vh; background:#F3F4F6; font-family:'Segoe UI',system-ui,sans-serif; font-size:14px;">

	<!-- SIDEBAR -->
	<aside style="width:220px; background:#fff; border-right:1px solid #E5E7EB; display:flex; flex-direction:column; position:fixed; top:0; left:0; bottom:0; z-index:50; overflow-y:auto;">
		<div style="padding:16px 20px; border-bottom:1px solid #E5E7EB; flex-shrink:0;">
			<a href="/parent/dashboard" style="text-decoration:none; display:inline-flex; align-items:center; justify-content:center; width:38px; height:38px; background:#2563EB; border-radius:10px; font-weight:900; font-size:14px; letter-spacing:-1px;">
				<span style="color:#fff;">O</span><span style="color:#93C5FD;">T</span>
			</a>
		</div>
		<div style="font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.8px; color:#9CA3AF; padding:14px 20px 6px;">PARENT PORTAL</div>
		<nav style="flex:1;">
			{#each navItems as item}
				<a href={item.href}
					style="display:flex; align-items:center; gap:10px; padding:9px 20px; text-decoration:none; font-size:13.5px; font-weight:500; transition:all .15s;
					{activePage === item.key ? 'background:#2563EB; color:#fff;' : 'color:#6B7280;'}">
					<span style="width:18px; text-align:center; font-size:15px;">{item.icon}</span>
					{item.label}
				</a>
			{/each}
		</nav>
		<div style="padding:14px 20px; font-size:11px; color:#9CA3AF; border-top:1px solid #E5E7EB; flex-shrink:0;">
			© 2025 OpenTutorAI &nbsp;<a href="#" style="color:#9CA3AF;">Aide</a>
		</div>
	</aside>

	<!-- MAIN -->
	<div style="margin-left:220px; flex:1; display:flex; flex-direction:column; min-height:100vh;">
		<!-- HEADER -->
		<header style="background:#fff; border-bottom:1px solid #E5E7EB; height:60px; display:flex; align-items:center; padding:0 28px; gap:14px; position:sticky; top:0; z-index:40; flex-shrink:0;">
			<div style="flex:1;">
				<div style="font-size:16px; font-weight:700;">Bonjour {firstName} 👋</div>
				<div style="font-size:12px; color:#6B7280;"><slot name="subtitle">Bienvenue dans votre espace parent</slot></div>
			</div>
			<div style="display:flex; align-items:center; gap:8px; border:1px solid #E5E7EB; border-radius:20px; padding:6px 14px; background:#F3F4F6; width:180px;">
				<span style="color:#9CA3AF; font-size:13px;">🔍</span>
				<input placeholder="Recherche" style="border:none; background:none; font-size:13px; outline:none; width:100%;"/>
			</div>
			<a href="/parent/notifications" style="width:34px; height:34px; border-radius:50%; border:1px solid #E5E7EB; display:flex; align-items:center; justify-content:center; text-decoration:none; font-size:15px; color:#6B7280; position:relative;">
				🔔
			</a>
			<div style="width:34px; height:34px; border-radius:50%; background:#2563EB; color:white; font-weight:700; font-size:12px; display:flex; align-items:center; justify-content:center; cursor:pointer; flex-shrink:0;">
				{initials}
			</div>
		</header>

		<!-- PAGE CONTENT -->
		<main style="flex:1; padding:28px; overflow-y:auto;">
			<slot />
		</main>
	</div>
</div>