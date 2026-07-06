<!-- Parent Layout -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { get, derived } from 'svelte/store';
	import { user, theme } from '$lib/stores';
	import { page } from '$app/stores';
	import { TUTOR_FRONT_URL } from '$lib/constants';

	let isSidebarOpen = true;
	let isMobile = false;
	let loading = true;
	let currentActivePage = 'dashboard';

	const isDarkMode = derived(theme, ($theme) => {
		return (
			$theme === 'dark' ||
			($theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
		);
	});

	let currentIsDarkMode = false;
	isDarkMode.subscribe((value) => {
		currentIsDarkMode = value;
		document.documentElement.classList.toggle('dark', value);
	});

	// Sync active page from URL
	$: {
		const segments = $page.url.pathname.split('/');
		currentActivePage = segments[2] || 'dashboard';
	}

	const navItems = [
		{ id: 'dashboard', label: 'Tableau de bord', emoji: '⊞' },
		{ id: 'create-support', label: 'Créer un soutien', emoji: '+' },
		{ id: 'evaluations', label: 'Évaluations', emoji: '📋' },
		{ id: 'sessions', label: 'Sessions IA', emoji: '🤖' },
		{ id: 'notifications', label: 'Notifications', emoji: '🔔' },
		{ id: 'settings', label: 'Profil et paramètres', emoji: '⚙' }
	];

	function toggleSidebar() {
		isSidebarOpen = !isSidebarOpen;
	}

	function navigate(id: string) {
		if (isMobile) isSidebarOpen = false;
		goto(`/parent/${id}`);
	}

	onMount(() => {
		const currentUser = get(user);
		if (!currentUser) {
			goto('/auth');
			return;
		}
		if (currentUser.role !== 'parent') {
			goto(`/${currentUser.role}`);
			return;
		}

		const handleResize = () => {
			isMobile = window.innerWidth < 768;
			if (isMobile && isSidebarOpen) isSidebarOpen = false;
			else if (!isMobile && !isSidebarOpen) isSidebarOpen = true;
		};
		window.addEventListener('resize', handleResize);
		handleResize();
		loading = false;
		return () => window.removeEventListener('resize', handleResize);
	});
</script>

{#if loading}
	<div class="flex justify-center items-center min-h-screen">
		<div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
	</div>
{:else}
	<div class="flex h-screen overflow-hidden bg-[#F4F7FE] dark:bg-gray-900">
		<!-- Sidebar -->
		<aside
			class="
		{isSidebarOpen ? 'w-64' : 'w-0 md:w-16'}
		bg-[#F5F7F9] dark:bg-gray-900 shadow-md fixed left-0 top-0 h-full z-30
		transition-all duration-300 overflow-hidden flex flex-col
	"
		>
			<!-- Logo -->
			<div
				class="p-4 flex items-center justify-center h-16 border-b border-gray-200 dark:border-gray-700"
			>
				{#if isSidebarOpen}
					<a href="/parent">
						<img src="{TUTOR_FRONT_URL}/static/favicon.png" alt="Logo" class="h-10" />
					</a>
				{:else}
					<a href="/parent" class="hidden md:block">
						<img src="{TUTOR_FRONT_URL}/static/favicon.png" alt="Logo" class="h-8" />
					</a>
				{/if}
			</div>

			<!-- Label -->
			{#if isSidebarOpen}
				<div class="px-4 py-3 text-xs text-gray-500 uppercase font-semibold">Parent Portal</div>
			{/if}

			<!-- Nav -->
			<nav class="flex-1 mt-1">
				<ul>
					{#each navItems as item}
						<li class="mb-1 px-2">
							<button
								on:click={() => navigate(item.id)}
								class="flex items-center px-4 py-3 rounded-full w-full text-left text-sm font-semibold transition duration-100
								{currentActivePage === item.id
									? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white'
									: 'text-gray-800 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-800'}"
							>
								<span class="w-6 h-6 flex items-center justify-center text-base">{item.emoji}</span>
								{#if isSidebarOpen}
									<span class="ml-3">{item.label}</span>
								{/if}
							</button>
						</li>
					{/each}
				</ul>
			</nav>

			<!-- Footer -->
			{#if isSidebarOpen}
				<div
					class="p-4 text-xs text-gray-400 border-t border-gray-200 dark:border-gray-700 flex justify-between"
				>
					<span>© 2025 OpenTutorAI</span>
					<button class="hover:text-gray-600">Aide</button>
				</div>
			{/if}
		</aside>

		<!-- Toggle sidebar button -->
		<button
			on:click={toggleSidebar}
			class="hidden md:flex fixed top-4 z-50 bg-white dark:bg-gray-800 shadow-md rounded-full h-6 w-6
		       items-center justify-center border border-gray-200 dark:border-gray-700 hover:text-blue-500"
			style={isSidebarOpen ? 'left: 15.1rem;' : 'left: 3.5rem;'}
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="14"
				height="14"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
			>
				<path d={isSidebarOpen ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6'} />
			</svg>
		</button>

		<!-- Main content -->
		<div
			class="flex-1 flex flex-col overflow-hidden {isSidebarOpen
				? 'md:ml-64'
				: 'md:ml-16'} transition-all duration-300"
		>
			<!-- Navbar -->
			<header
				class="bg-white dark:bg-gray-900 shadow-sm px-6 py-3 flex items-center justify-between z-20"
			>
				<button class="md:hidden" on:click={toggleSidebar}>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-6 w-6 text-gray-500"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M4 6h16M4 12h16M4 18h16"
						/>
					</svg>
				</button>
				<div class="flex-1" />
				<!-- Search -->
				<div
					class="hidden md:flex items-center bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full px-4 py-2 gap-2 w-56"
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
						placeholder="Recherche"
						class="bg-transparent border-none outline-none text-sm w-full text-gray-700 dark:text-gray-300"
					/>
				</div>
				<!-- Icons -->
				<div class="flex items-center gap-3 ml-4">
					<button class="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
						>🔔</button
					>
					<button class="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
						>🌙</button
					>
					<button class="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
						>ℹ</button
					>
					<!-- Avatar -->
					<button
						on:click={() => {
							localStorage.removeItem('token');
							location.href = '/auth';
						}}
						class="h-8 w-8 rounded-full bg-blue-600 text-white text-sm font-bold flex items-center justify-center"
					>
						{$user?.name?.charAt(0) ?? 'P'}
					</button>
				</div>
			</header>

			<!-- Page content -->
			<div class="flex-1 overflow-y-auto p-4 md:p-6 bg-[#F4F7FE] dark:bg-gray-900">
				<slot />
			</div>
		</div>

		<!-- Mobile overlay -->
		{#if isMobile && isSidebarOpen}
			<div class="fixed inset-0 bg-black/50 z-20 md:hidden" on:click={toggleSidebar}></div>
		{/if}
	</div>
{/if}
