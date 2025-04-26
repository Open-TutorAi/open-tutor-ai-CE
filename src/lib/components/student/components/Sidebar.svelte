<!-- Sidebar.svelte -->
<script lang="ts">
	import { TUTOR_BASE_URL } from '$lib/constants';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount, getContext } from 'svelte';
	import Settings from '$lib/components/icons/Settings.svelte';
	import Dashboard from '$lib/components/icons/Dashboard.svelte';
	import Classroom from '$lib/components/icons/Classroom.svelte';
	import Assignment from '$lib/components/icons/Assignment.svelte';
	import Message from '$lib/components/icons/Messages.svelte';
	import type { ComponentType } from 'svelte';
	import { writable, type Writable } from 'svelte/store';
	const i18n = getContext('i18n');

	// Use a simple boolean for sidebar state instead of a store
	export let isSidebarOpen = true;
	export let isDarkMode: boolean = false;

	// Accept either a string or a Writable<string> for activePage
	export let activePage: string | Writable<string> = 'dashboard';

	// Create a local variable to track active page
	let currentActivePage: string;

	// Subscribe to activePage if it's a store, or use the value directly
	$: {
		if (typeof activePage === 'object' && 'subscribe' in activePage) {
			const unsubscribe = activePage.subscribe((value) => {
				currentActivePage = value;
			});
			// Clean up subscription when component is destroyed
			onMount(() => {
				return () => unsubscribe();
			});
		} else {
			currentActivePage = activePage as string;
		}
	}

	// For mobile detection
	let isMobile = false;

	onMount(() => {
		// Check if we're on mobile
		checkMobile();

		// Add window resize listener
		window.addEventListener('resize', checkMobile);

		// Set active page based on URL path when component mounts
		const pathSegments = $page.url.pathname.split('/');
		if (pathSegments.length >= 3) {
			let pageFromUrl = pathSegments[2]; // student/dashboard -> "dashboard"

			// Map chat routes to support
			if (pageFromUrl === 'tutor' || pageFromUrl === 'c') {
				pageFromUrl = 'support';
			}

			// Update the activePage store if it's a store
			if (typeof activePage === 'object' && 'subscribe' in activePage) {
				(activePage as Writable<string>).set(pageFromUrl);
			} else {
				currentActivePage = pageFromUrl;
			}
		}

		return () => {
			window.removeEventListener('resize', checkMobile);
		};
	});

	// Also update active page whenever the URL changes
	$: {
		const pathSegments = $page.url.pathname.split('/');
		if (pathSegments.length >= 3) {
			let pageFromUrl = pathSegments[2];
			
			// Map chat routes to support
			if (pageFromUrl === 'tutor' || pageFromUrl === 'c') {
				pageFromUrl = 'support';
			}

			// Only update if it has changed to avoid loops
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
		// Auto-close on mobile initially, but don't change state if already set
		if (isMobile && isSidebarOpen === true) {
			isSidebarOpen = false;
		}
	}

	// Determine current role from the URL path
	$: currentRole = $page.url.pathname.split('/')[1] || 'student';

	function toggleSidebar() {
		isSidebarOpen = !isSidebarOpen;
	}

	function setActivePage(role: string, page: string) {
		// First close the sidebar on mobile to avoid black overlay issue
		if (isMobile) {
			isSidebarOpen = false;
		}

		// Update the activePage store if it's a store
		if (typeof activePage === 'object' && 'subscribe' in activePage) {
			(activePage as Writable<string>).set(page);
		} else {
			currentActivePage = page;
		}

		// Add small delay to ensure sidebar is closed before navigation
		setTimeout(() => {
			goto(`/${role}/${page}`);
		}, 10);
	}

	// Define the types for navigation items
	type NavItem = {
		id: string;
		label: string;
		icon: ComponentType;
	};

	type NavItems = Record<string, NavItem[]>;

	// Navigation items organized by role
	const navItems: NavItems = {
		student: [
			{ id: 'dashboard', label: 'Dashboard', icon: Dashboard },
			{ id: 'classrooms', label: 'My Classrooms', icon: Classroom },
			{ id: 'support', label: 'Support', icon: Classroom },
			{ id: 'assignments', label: 'Assignments', icon: Assignment },
			{ id: 'messages', label: 'Messages', icon: Message },
			{ id: 'settings', label: 'Profile & Settings', icon: Settings }
		],
		teacher: [],
		parent: []
	};
</script>

<div class="relative flex h-full">
	<!-- Main content area - padding makes room for the fixed sidebar -->
	<div class={`w-full transition-all duration-300 ${isSidebarOpen ? 'md:ml-64' : 'md:ml-16'}`}>
		<!-- Mobile toggle button - visible only on mobile -->
		<button
			on:click={toggleSidebar}
			class={`md:hidden fixed top-4 left-4 z-50 ${isDarkMode ? 'bg-gray-800 text-gray-300 border-gray-700' : 'bg-white text-gray-600 border-gray-200'} shadow-md rounded-full h-10 w-10 flex items-center justify-center border hover:text-blue-500 focus:outline-none`}
			aria-label={isSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="20"
				height="20"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				{#if isSidebarOpen}
					<path d="M18 6L6 18M6 6l12 12"></path>
				{:else}
					<path d="M3 12h18M3 6h18M3 18h18"></path>
				{/if}
			</svg>
		</button>
		
		<slot />
	</div>

	<!-- Sidebar -->
	<aside
		class={`${isDarkMode ? 'bg-gray-900 text-gray-100' : 'bg-[#F5F7F9]'} shadow-md transition-all duration-300 h-full fixed left-0 top-0 z-30 overflow-y-auto ${isSidebarOpen ? 'w-64 translate-x-0' : 'w-0 md:w-16 -translate-x-full md:translate-x-0'}`}
		style="min-height: 100vh;"
	>
		<div class="p-4">
			<div class="flex items-center justify-center h-12">
				{#if isSidebarOpen}
					<a href="/" class="flex items-center">
						<img src="{TUTOR_BASE_URL}/static/favicon.png" alt="Logo" class="h-20 mr-2" />
					</a>
				{:else}
					<a href="/" class="flex items-center md:block hidden">
						<img src="{TUTOR_BASE_URL}/static/favicon.png" alt="Logo" class="h-8" />
					</a>
				{/if}
			</div>
		</div>

		<div class="px-4 py-2">
			{#if isSidebarOpen}
				<div
					class={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'} uppercase font-semibold mb-1`}
				>
					{$i18n.t(currentRole.charAt(0).toUpperCase() + currentRole.slice(1)) + ' Portal'}
				</div>
			{/if}
		</div>

		<nav class="mt-2">
			{#if navItems[currentRole] && navItems[currentRole].length > 0}
				<ul>
					{#each navItems[currentRole] as item}
						<li class="mb-1 px-2">
							<button
								on:click={() => setActivePage(currentRole, item.id)}
								class={`flex items-center px-4 py-3 rounded-lg w-full text-left transition-colors duration-200 ${currentActivePage === item.id ? 'bg-blue-500 text-white' : isDarkMode ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-800 hover:bg-gray-200'}`}
								title={$i18n.t(item.label)}
							>
								<span class="grid place-items-center w-6 h-6">
									<svelte:component this={item.icon} />
								</span>
								{#if isSidebarOpen}
									<span class="ml-3 text-sm font-medium">{$i18n.t(item.label)}</span>
								{/if}
							</button>
						</li>
					{/each}
				</ul>
			{:else}
				<div class={`px-4 py-3 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'} text-sm italic`}>
					{isSidebarOpen ? 'No navigation items available' : ''}
				</div>
			{/if}
		</nav>

		{#if isSidebarOpen}
			<div class="absolute bottom-0 left-0 right-0 p-4 hidden md:block">
				<div
					class={`flex items-center justify-between text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}
				>
					<span>© 2025 OpenTutorAI</span>
					<button class={`hover:${isDarkMode ? 'text-gray-300' : 'text-gray-800'}`}
						>{$i18n.t('Help')}</button
					>
				</div>
			</div>
		{/if}
	</aside>

	<!-- Desktop toggle button -->
	<button
		on:click={toggleSidebar}
		class={`hidden md:flex absolute top-4 z-50 ${isDarkMode ? 'bg-gray-800 text-gray-300 border-gray-700' : 'bg-white text-gray-600 border-gray-200'} shadow-md rounded-full h-6 w-6 items-center justify-center border hover:text-blue-500 focus:outline-none`}
		style={isSidebarOpen ? 'left: 15.1rem;' : 'left: 3.5rem;'}
		aria-label={isSidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
	>
		<svg
			xmlns="http://www.w3.org/2000/svg"
			width="14"
			height="14"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
		>
			<path d={isSidebarOpen ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6'}></path>
		</svg>
	</button>

	<!-- Overlay to close sidebar when clicked (mobile only) -->
	{#if isSidebarOpen && isMobile}
		<div
		class="fixed inset-0 backdrop-blur-sm bg-opacity-50 z-20 md:hidden"
		on:click={toggleSidebar}
		></div>
	{/if}
</div>