<script lang="ts">
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import { onMount, getContext } from 'svelte';
	import DashboardSidebar from '$lib/components/common/DashboardSidebar.svelte';
	import ParentMessages from '$lib/components/teacher/ParentMessages.svelte';
	import AnnouncementsPage from '$lib/components/teacher/AnnouncementsPage.svelte';

	const i18n = getContext('i18n');

	let loading = true;
	let error: string | null = null;
	let activeSection = 'messages';
	let unreadCount = 0;
	let sidebarOpen = true;

	$: initials =
		$user?.name
			?.split(' ')
			.map((w: string) => w[0])
			.slice(0, 2)
			.join('')
			.toUpperCase() ?? '?';

	onMount(async () => {
		try {
			if (!$user) { goto('/auth'); return; }
			if ($user.role !== 'teacher') { await goto(`/${$user.role}`); return; }
			loading = false;
		} catch (err: any) {
			error = err?.message || 'Une erreur est survenue';
			loading = false;
		}
	});
</script>

{#if loading}
	<div class="flex justify-center items-center min-h-screen bg-white dark:bg-gray-900">
		<div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
	</div>
{:else if error}
	<div class="flex items-center justify-center min-h-screen bg-white dark:bg-gray-900 p-6">
		<div class="bg-white dark:bg-gray-850 rounded-xl border border-gray-100 dark:border-gray-800 shadow-md p-8 max-w-sm w-full text-center">
			<div class="text-5xl mb-4">⚠️</div>
			<h2 class="text-lg font-bold text-red-600 mb-2">{$i18n.t('Error Loading Teacher Page')}</h2>
			<p class="text-gray-500 dark:text-gray-400 text-sm mb-4">{error}</p>
			<button
				class="inline-flex items-center justify-center px-4 py-2 text-sm font-semibold bg-gradient-to-r from-blue-500 to-blue-600 hover:opacity-90 text-white rounded-lg transition"
				on:click={() => goto('/auth')}
			>
				{$i18n.t('Return to Login')}
			</button>
		</div>
	</div>
{:else}
	<div class="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-900">
		<DashboardSidebar
			role="teacher"
			{activeSection}
			{unreadCount}
			bind:isSidebarOpen={sidebarOpen}
			on:navigate={(e) => (activeSection = e.detail.section)}
		/>

		<main class="flex-1 flex flex-col min-w-0 overflow-hidden">
			<!-- Header -->
			<header class="bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 px-4 py-3 flex items-center gap-3 z-10">
				{#if !sidebarOpen}
					<button
						class="cursor-pointer p-[7px] flex rounded-xl hover:bg-gray-100 dark:hover:bg-gray-900 transition text-gray-600 dark:text-gray-400 flex-shrink-0"
						on:click={() => (sidebarOpen = true)}
						aria-label="Ouvrir le menu"
					>
						<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="size-5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
						</svg>
					</button>
				{/if}
				<div class="flex-1 min-w-0">
					{#if activeSection === 'dashboard'}
						<h1 class="text-base font-semibold text-gray-800 dark:text-gray-100">Tableau de bord</h1>
						<p class="text-xs text-gray-500 dark:text-gray-400">Bonjour {$user?.name}</p>
					{:else if activeSection === 'messages'}
						<h1 class="text-base font-semibold text-gray-800 dark:text-gray-100">Messages des parents</h1>
						<p class="text-xs text-gray-500 dark:text-gray-400">Gérez vos échanges avec les familles</p>
					{:else if activeSection === 'announcements'}
						<h1 class="text-base font-semibold text-gray-800 dark:text-gray-100">Annonces</h1>
						<p class="text-xs text-gray-500 dark:text-gray-400">Publiez des annonces pour les familles</p>
					{:else if activeSection === 'profile'}
						<h1 class="text-base font-semibold text-gray-800 dark:text-gray-100">Mon profil</h1>
						<p class="text-xs text-gray-500 dark:text-gray-400">Informations de votre compte</p>
					{/if}
				</div>
				<button
					class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 hover:opacity-90 transition"
					on:click={() => (activeSection = 'profile')}
					title="Mon profil"
				>
					{initials}
				</button>
			</header>

			<div class="flex-1 overflow-auto p-6 bg-gray-50 dark:bg-gray-900">
				{#if activeSection === 'dashboard'}
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-6">
						<!-- Unread messages card -->
						<div class="bg-white dark:bg-gray-850 rounded-xl border border-gray-100 dark:border-gray-800 p-6 flex flex-col justify-between min-h-[140px]">
							<div class="flex items-center justify-between mb-4">
								<p class="text-sm font-medium text-gray-600 dark:text-gray-400">Messages non lus</p>
								<span class="p-2.5 rounded-lg bg-blue-50 dark:bg-blue-900/20">
									<svg class="size-5 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
									</svg>
								</span>
							</div>
							<p class="text-3xl font-bold text-gray-900 dark:text-white">{unreadCount}</p>
						</div>

						<!-- Role card -->
						<div class="bg-white dark:bg-gray-850 rounded-xl border border-gray-100 dark:border-gray-800 p-6 flex flex-col justify-between min-h-[140px]">
							<div class="flex items-center justify-between mb-4">
								<p class="text-sm font-medium text-gray-600 dark:text-gray-400">Rôle</p>
								<span class="p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-900/20">
									<svg class="size-5 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
									</svg>
								</span>
							</div>
							<p class="text-xl font-bold text-gray-900 dark:text-white">Enseignant</p>
						</div>

						<!-- Quick access card -->
						<div class="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white sm:col-span-2 lg:col-span-1">
							<p class="text-xs font-medium text-blue-100 mb-1">Accès rapide</p>
							<p class="text-sm font-bold mb-3">Communiquer avec les familles</p>
							<div class="flex flex-wrap gap-2">
								<button
									class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white/20 hover:bg-white/30 text-white rounded-lg transition"
									on:click={() => (activeSection = 'messages')}
								>
									Messages →
								</button>
								<button
									class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white/20 hover:bg-white/30 text-white rounded-lg transition"
									on:click={() => (activeSection = 'announcements')}
								>
									Annonces →
								</button>
							</div>
						</div>
					</div>

				{:else if activeSection === 'messages'}
					<div class="h-full">
						<ParentMessages bind:totalUnread={unreadCount} />
					</div>

				{:else if activeSection === 'announcements'}
					<div class="h-full">
						<AnnouncementsPage />
					</div>

				{:else if activeSection === 'profile'}
					<div class="max-w-lg">
						<div class="bg-white dark:bg-gray-850 rounded-xl border border-gray-100 dark:border-gray-800 p-6">
							<div class="flex items-center gap-4 mb-6">
								<div class="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-xl font-bold">
									{initials}
								</div>
								<div>
									<h2 class="text-lg font-bold text-gray-900 dark:text-white">{$user?.name}</h2>
									<p class="text-sm text-gray-500 dark:text-gray-400">{$user?.email}</p>
									<span class="inline-block mt-1 px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-xs font-medium rounded-lg">
										Enseignant
									</span>
								</div>
							</div>
							<div class="divide-y divide-gray-100 dark:divide-gray-800">
								<div class="flex items-center justify-between py-3">
									<span class="text-sm text-gray-500 dark:text-gray-400">Nom complet</span>
									<span class="text-sm font-medium text-gray-900 dark:text-white">{$user?.name}</span>
								</div>
								<div class="flex items-center justify-between py-3">
									<span class="text-sm text-gray-500 dark:text-gray-400">Email</span>
									<span class="text-sm font-medium text-gray-900 dark:text-white">{$user?.email}</span>
								</div>
								<div class="flex items-center justify-between py-3">
									<span class="text-sm text-gray-500 dark:text-gray-400">Rôle</span>
									<span class="text-sm font-medium text-gray-900 dark:text-white">Enseignant</span>
								</div>
							</div>
						</div>
					</div>
				{/if}
			</div>
		</main>
	</div>
{/if}
