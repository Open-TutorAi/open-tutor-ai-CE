<!-- Student Layout -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get, writable, derived } from 'svelte/store';

	import Sidebar from '$lib/components/student/elements/Sidebar.svelte';
	import Navbar from '$lib/components/student/elements/Navbar.svelte';

	import { getModels, getVersionUpdates } from '$lib/apis';
	import { config, user, settings, models, theme } from '$lib/stores';

	const activePage = writable('dashboard');
	let isSidebarOpen = true;
	let username = 'Karim';

	let windowWidth: number;
	let isMobile: boolean = false;
	let loading = true;

	// Derive isDarkMode from theme store
	const isDarkMode = derived(theme, ($theme) => {
		return (
			$theme === 'dark' ||
			($theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
		);
	});

	// Subscribe to isDarkMode to get the actual boolean value
	let currentIsDarkMode = false;
	isDarkMode.subscribe((value) => {
		currentIsDarkMode = value;
		document.documentElement.classList.toggle('dark', value);
	});

	function toggleSidebar() {
		isSidebarOpen = !isSidebarOpen;
	}

	function toggleDarkMode(event: CustomEvent) {
		const newTheme = event.detail.isDarkMode ? 'dark' : 'light';
		theme.set(newTheme);
		localStorage.setItem('theme', newTheme);
	}

	onMount(async () => {
		console.log('Student layout mounted');
		models.set(
			await getModels(
				localStorage.token,
				$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
			)
		);
		// Role protection logic
		const currentUser = get(user);
		if (!currentUser) {
			goto('/auth');
			return;
		}
		if (currentUser.role !== 'user') {
			console.log('User is not a student, redirecting to home');
			goto(`/${currentUser.role}`);
			return;
		}
		loading = false;

		// Initialize dark mode based on global theme
		const currentTheme = get(theme);
		const isDark =
			currentTheme === 'dark' ||
			(currentTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
		document.documentElement.classList.toggle('dark', isDark);

		// Handle resize events for responsive design
		const handleResize = () => {
			windowWidth = window.innerWidth;
			isMobile = windowWidth < 768;

			if (isMobile && isSidebarOpen) {
				isSidebarOpen = false;
			} else if (!isMobile && !isSidebarOpen) {
				isSidebarOpen = true;
			}
		};

		window.addEventListener('resize', handleResize);
		handleResize();

		return () => {
			window.removeEventListener('resize', handleResize);
		};
	});
</script>

<div
	class="flex h-screen overflow-hidden bg-[#F4F7FE] dark:bg-gray-900 transition-colors duration-200 ease-in-out"
>
	<!-- Sidebar with adaptive behavior -->
	<div class={`sidebar-container ${isSidebarOpen ? '' : 'collapsed'}`}>
		<Sidebar {isSidebarOpen} {activePage} isDarkMode={currentIsDarkMode} />
	</div>

	<!-- Main content area with navbar and slot -->
	<div class="flex-1 flex flex-col overflow-hidden relative z-10 bg-[#F4F7FE] dark:bg-gray-900">
		<Navbar
			{username}
			{toggleSidebar}
			isDarkMode={currentIsDarkMode}
			on:darkModeToggle={toggleDarkMode}
		/>

		<!-- Main content with proper scrolling -->
		<div
			class="flex-1 overflow-y-auto p-4 md:p-6 bg-[#F4F7FE] dark:bg-gray-900 text-gray-800 dark:text-gray-100"
		>
			<slot />
		</div>
	</div>

	<!-- Mobile sidebar overlay when open on mobile - lower z-index than content -->
	{#if isMobile && isSidebarOpen}
		<div
			class="fixed inset-0 bg-black bg-opacity-70 z-5"
			on:click={() => {
				isSidebarOpen = false;
			}}
			aria-hidden="true"
		></div>
	{/if}
</div>

<style>
	/* Add this to ensure nested layouts work properly */
	:global(.flex-1) {
		min-height: 0; /* This is crucial for proper flex behavior */
	}

	/* Make sure content containers have proper layout */
	:global(#chat-container) {
		display: flex;
		flex-direction: column;
		height: 100%;
		overflow: hidden;
	}
	/* Base styles */
	:global(body, html) {
		height: 100%;
		margin: 0;
		padding: 0;
		overflow: hidden;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
			'Open Sans', 'Helvetica Neue', sans-serif;
	}

	/* Add dark mode transition for smoother theme switching */
	:global(body),
	:global(body *) {
		transition:
			background-color 0.3s ease,
			color 0.3s ease;
	}

	/* Ensure proper contrast in dark mode */
	:global(.dark) {
		color-scheme: dark;
	}

	:global(.dark *:focus) {
		outline-color: #60a5fa;
	}

	/* Sidebar container responsive styles */
	.sidebar-container {
		transition: all 0.3s ease;
		z-index: 20;
	}

	.sidebar-container.collapsed {
		margin-left: -256px; /* Match sidebar width when closed */
	}

	/* Mobile styles */
	@media (max-width: 767px) {
		.sidebar-container {
			position: fixed;
			height: 100%;
			z-index: 30;
		}

		.sidebar-container.collapsed {
			margin-left: -100%; /* Fully hide on mobile */
		}
	}

	/* Tablet adjustments */
	@media (min-width: 768px) and (max-width: 1023px) {
		.sidebar-container:not(.collapsed) {
			width: auto;
		}
	}
</style>
