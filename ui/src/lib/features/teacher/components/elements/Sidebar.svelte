<!-- Teacher Sidebar -->
<script lang="ts">
	import { TUTOR_FRONT_URL } from '$lib/constants';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount, getContext } from 'svelte';
	import Settings from '$lib/icons/Settings.svelte';
	import Dashboard from '$lib/icons/Dashboard.svelte';
	import Classroom from '$lib/icons/Classroom.svelte';
	import Assignment from '$lib/icons/Assignment.svelte';
	import Message from '$lib/icons/Messages.svelte';
	import type { ComponentType } from 'svelte';
	import { writable, type Writable } from 'svelte/store';
	const i18n = getContext('i18n');

	export let isSidebarOpen = true;
	export let isDarkMode: boolean = false;
	export let activePage: string | Writable<string> = 'dashboard';

	let currentActivePage: string;

	$: {
		if (typeof activePage === 'object' && 'subscribe' in activePage) {
			const unsubscribe = activePage.subscribe((value) => {
				currentActivePage = value;
			});
			onMount(() => () => unsubscribe());
		} else {
			currentActivePage = activePage as string;
		}
	}

	let isMobile = false;

	onMount(() => {
		checkMobile();
		window.addEventListener('resize', checkMobile);

		const pathSegments = $page.url.pathname.split('/');
		if (pathSegments.length >= 3) {
			const pageFromUrl = pathSegments[2];
			if (typeof activePage === 'object' && 'subscribe' in activePage) {
				(activePage as Writable<string>).set(pageFromUrl);
			} else {
				currentActivePage = pageFromUrl;
			}
		}

		return () => window.removeEventListener('resize', checkMobile);
	});

	$: {
		const pathSegments = $page.url.pathname.split('/');
		if (pathSegments.length >= 3) {
			const pageFromUrl = pathSegments[2];
			if (currentActivePage !== pageFromUrl) {
				if (typeof activePage === 'object' && 'subscribe' in activePage) {
					(activePage as Writable<string>).set(pageFromUrl);
				} else {
					currentActivePage = pageFromUrl;
				}
			}
		}
	}

	function checkMobile() {
		isMobile = window.innerWidth < 768;
		if (isMobile && isSidebarOpen === true) {
			isSidebarOpen = false;
		}
	}

	function toggleSidebar() {
		isSidebarOpen = !isSidebarOpen;
	}

	function setActivePage(p: string) {
		if (isMobile) isSidebarOpen = false;

		if (typeof activePage === 'object' && 'subscribe' in activePage) {
			(activePage as Writable<string>).set(p);
		} else {
			currentActivePage = p;
		}

		setTimeout(() => goto(`/teacher/${p}`), 10);
	}

	type NavItem = { id: string; label: string; icon: ComponentType };

	const navItems: NavItem[] = [
		{ id: 'dashboard',   label: 'Dashboard',          icon: Dashboard  },
		{ id: 'classrooms',  label: 'My Classrooms',      icon: Classroom  },
		{ id: 'support',     label: 'Support',            icon: Message    },
		{ id: 'assignments', label: 'Assignments',        icon: Assignment },
		{ id: 'messages',    label: 'Messages',           icon: Message    },
		{ id: 'settings',    label: 'Profile & Settings', icon: Settings   },
	];

	function isActive(id: string): boolean {
		const path = $page.url.pathname;
		if (id === 'classrooms') return path.includes('/teacher/classrooms') || path.includes('/teacher/students');
		return currentActivePage === id;
	}
</script>

<div class="relative flex h-full">
	<div class={`w-full transition-all duration-300 ${isSidebarOpen ? 'md:ml-64' : 'md:ml-16'}`}>
		<!-- Mobile toggle -->
		<button
			on:click={toggleSidebar}
			class="md:hidden fixed top-4 left-4 z-50 bg-[#1a2744] text-gray-300 rounded-xl h-10 w-10 flex items-center justify-center hover:text-indigo-400 focus:outline-none"
			aria-label={isSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
		>
			<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
				fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				{#if isSidebarOpen}
					<path d="M18 6L6 18M6 6l12 12"></path>
				{:else}
					<path d="M3 12h18M3 6h18M3 18h18"></path>
				{/if}
			</svg>
		</button>

		<slot />
	</div>

	<!-- Sidebar dark navy -->
	<aside
		class="bg-[#1a2744] shadow-xl transition-all duration-300 h-full fixed left-0 top-0 z-30 overflow-y-auto flex flex-col
			{isSidebarOpen ? 'w-64 translate-x-0' : 'w-0 md:w-16 -translate-x-full md:translate-x-0'}"
		style="min-height: 100vh;"
	>
		<!-- Logo -->
		<div class="p-4 border-b border-white/10">
			<div class="flex items-center justify-center h-12">
				{#if isSidebarOpen}
					<a href="/" class="flex items-center gap-2">
						<div class="h-8 w-8 rounded-lg bg-white flex items-center justify-center">
							<img src="{TUTOR_FRONT_URL}/static/favicon.png" alt="Logo" class="h-6" />
						</div>
						<span class="text-white font-bold text-base">OpenTutorAI</span>
					</a>
				{:else}
					<a href="/" class="flex items-center md:block hidden">
						<div class="h-8 w-8 rounded-lg bg-white flex items-center justify-center">
							<img src="{TUTOR_FRONT_URL}/static/favicon.png" alt="Logo" class="h-6" />
						</div>
					</a>
				{/if}
			</div>
		</div>

		<!-- Portal label -->
		{#if isSidebarOpen}
			<div class="px-5 pt-4 pb-1">
				<span class="text-xs text-indigo-400 uppercase font-bold tracking-widest">{$i18n.t('Teacher Portal')}</span>
			</div>
		{/if}

		<!-- Navigation -->
		<nav class="mt-2 flex-1">
			<ul class="space-y-0.5 px-2">
				{#each navItems as item}
					<li>
						<button
							on:click={() => setActivePage(item.id)}
							class="flex items-center px-3 py-2.5 rounded-xl w-full text-left text-sm font-medium transition-all duration-150
								{isActive(item.id)
									? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/40'
									: 'text-gray-300 hover:bg-white/10 hover:text-white'}"
							title={$i18n.t(item.label)}
						>
							<span class="grid place-items-center w-5 h-5 shrink-0">
								<svelte:component this={item.icon} />
							</span>
							{#if isSidebarOpen}
								<span class="ml-3">{$i18n.t(item.label)}</span>
							{/if}
						</button>
					</li>
				{/each}
			</ul>
		</nav>

		<!-- Need help section -->
		{#if isSidebarOpen}
			<div class="p-4 border-t border-white/10 mt-auto">
				<div class="bg-white/5 rounded-xl p-3 text-center">
					<p class="text-xs text-gray-400 mb-2">{$i18n.t('Need help?')}</p>
					<button class="w-full px-3 py-1.5 rounded-lg border border-indigo-500 text-indigo-400 hover:bg-indigo-500 hover:text-white text-xs font-semibold transition">
						{$i18n.t('Contact Support')}
					</button>
				</div>
				<p class="text-center text-xs text-gray-600 mt-3">© 2025 OpenTutorAI</p>
			</div>
		{/if}
	</aside>

	<!-- Desktop collapse toggle -->
	<button
		on:click={toggleSidebar}
		class="hidden md:flex absolute top-4 z-50 bg-[#1a2744] border border-white/20 text-gray-400 shadow-md rounded-full h-6 w-6 items-center justify-center hover:text-white focus:outline-none transition"
		style={isSidebarOpen ? 'left: 15.1rem;' : 'left: 3.5rem;'}
		aria-label={isSidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
	>
		<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"
			fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
			<path d={isSidebarOpen ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6'}></path>
		</svg>
	</button>

	{#if isSidebarOpen && isMobile}
		<button
			class="fixed inset-0 bg-black/40 backdrop-blur-sm z-20 md:hidden w-full h-full cursor-default"
			on:click={toggleSidebar}
			aria-label="Close sidebar"
		></button>
	{/if}
</div>
