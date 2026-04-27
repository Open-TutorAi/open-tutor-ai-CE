<!-- Teacher Layout with Form Blur Effect -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get, writable, derived } from 'svelte/store';
	import Sidebar from '$lib/components/common/OpenTutorElements/Sidebar.svelte';
	import Navbar from '$lib/components/common/OpenTutorElements/Navbar.svelte';
	
	import { getModels, getVersionUpdates } from '$lib/apis';
	import { config, user, settings, models, theme } from '$lib/stores';
	
	const activePage = writable('dashboard');
	
	// Add form state management for blur effect
	export let isFormOpen = false; // This can be passed from parent or managed internally
	const formBlurStore = writable(false);
	
	// Function to toggle form blur state - can be called from child components
	export function setFormBlur(isOpen: boolean) {
		formBlurStore.set(isOpen);
		isFormOpen = isOpen;
	}
	
	let isSidebarOpen = true;
	let username = 'Karim';
	let windowWidth: number;
	let isMobile: boolean = false;
	let loading = true;
	let currentFormBlur = false;
	
	// Subscribe to form blur state
	formBlurStore.subscribe(value => {
		currentFormBlur = value;
	});
	
<!-- teacher Layout -->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get, writable, derived } from 'svelte/store';

	import Sidebar from '$lib/components/teacher/elements/SidebarTeacher.svelte';
	import Navbar from '$lib/components/teacher/elements/Navbar.svelte';
	import DemoModeBanner from '$lib/components/DemoModeBanner.svelte';

	import { getModels, getVersionUpdates } from '$lib/apis';
	import { config, user, settings, models, theme, isDemo, demoData, originalUserData, isFullscreenAvatar} from '$lib/stores';
	import { generateDemoData } from '$lib/utils/mockData';
	import { toast } from 'svelte-sonner';
<!-- Teacher Layout -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { get, writable, derived } from 'svelte/store';

	import Sidebar from '$lib/components/teacher/elements/Sidebar.svelte';
	import Navbar from '$lib/components/teacher/elements/Navbar.svelte';

	import { user, theme } from '$lib/stores';

	const activePage = writable('dashboard');
	let isSidebarOpen = true;
	let username = '';

	// Extract first name from user's full name
	$: if ($user && $user.name) {
		// Split the name and get the first part as the first name
		username = $user.name.split(' ')[0];
	}

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
	
	let currentIsDarkMode = false;
	isDarkMode.subscribe((value) => {
		currentIsDarkMode = value;
		document.documentElement.classList.toggle('dark', value);
	});
	
	function toggleSidebar() {
		isSidebarOpen = !isSidebarOpen;
	}
	

	function toggleSidebar() {
		isSidebarOpen = !isSidebarOpen;
	}

	function toggleDarkMode(event: CustomEvent) {
		const newTheme = event.detail.isDarkMode ? 'dark' : 'light';
		theme.set(newTheme);
		localStorage.setItem('theme', newTheme);
	}

	function toggleDemoMode() {
		if ($isDemo) {
			// Exit demo mode
			if ($originalUserData) {
				user.set($originalUserData);
				originalUserData.set(null);
			}
			demoData.set({
				dashboard: null,
				chats: [],
				supports: [],
				assignments: [],
				courses: []
			});
			isDemo.set(false);
			localStorage.removeItem('demoMode');
			toast.success('Demo mode deactivated. Back to your real data.');
		} else {
			// Enter demo mode
			originalUserData.set($user);
			const mockData = generateDemoData();
			demoData.set(mockData);
			isDemo.set(true);
			localStorage.setItem('demoMode', 'true');
			toast.success('Demo mode activated. You\'re now exploring with sample data.');
		}
	}

	onMount(async () => {
		console.log('teacher layout mounted');
		
		// Check if demo mode was previously active
		const wasDemoMode = localStorage.getItem('demoMode') === 'true';
		if (wasDemoMode && !$isDemo) {
			console.log('Restoring demo mode from localStorage');
			const mockData = generateDemoData();
			originalUserData.set($user);
			demoData.set(mockData);
			isDemo.set(true);
		} else if ($isDemo && $demoData.chats.length === 0) {
			// Ensure demo data is loaded
			const mockData = generateDemoData();
			demoData.set(mockData);
		}
		
		models.set(
			await getModels(
				localStorage.token,
				$config?.features?.enable_direct_connections ? ($settings?.directConnections ?? null) : null
			)
		);
		// Role protection logic


	onMount(() => {
		const currentUser = get(user);
		if (!currentUser) {
			goto('/auth');
			return;
		}
		if (currentUser.role !== 'user') {
			console.log('User is not a teacher, redirecting to home');
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
		if (currentUser.role !== 'teacher') {
			goto(`/${currentUser.role}`);
			return;
		}

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
	});

	const handleResize = () => {
		windowWidth = window.innerWidth;
		isMobile = windowWidth < 768;

		if (isMobile && isSidebarOpen) {
			isSidebarOpen = false;
		} else if (!isMobile && !isSidebarOpen) {
			isSidebarOpen = true;
		}
	};

	onDestroy(() => {
		if (typeof window !== 'undefined') {
			window.removeEventListener('resize', handleResize);
		}
	});
</script>

<div
	class="flex h-screen overflow-hidden bg-[#F4F7FE] dark:bg-gray-900 transition-colors duration-200 ease-in-out"
>
	<!-- Sidebar with adaptive behavior - hide in fullscreen -->
	{#if !$isFullscreenAvatar}
		<div class={`sidebar-container ${isSidebarOpen ? '' : 'collapsed'}`}>
			<Sidebar {isSidebarOpen} {activePage} isDarkMode={currentIsDarkMode} />
		</div>
	{/if}

	<!-- Main content area with navbar and slot -->
	<div class="flex-1 flex flex-col overflow-hidden relative z-10 bg-[#F4F7FE] dark:bg-gray-900">
		<!-- Hide navbar in fullscreen -->
		{#if !$isFullscreenAvatar}
			<Navbar
				{username}
				{toggleSidebar}
				isDarkMode={currentIsDarkMode}
				on:darkModeToggle={toggleDarkMode}
			/>
		{/if}

		{#if $isDemo}
			<DemoModeBanner on:toggle={toggleDemoMode} />
		{/if}

		<!-- Main content with proper scrolling -->
		<div
			class="flex-1 overflow-y-auto {$isFullscreenAvatar ? '' : 'p-4 md:p-6'} bg-[#F4F7FE] dark:bg-gray-900 text-gray-800 dark:text-gray-100"
		>

		window.addEventListener('resize', handleResize);
		handleResize();

		return () => {
			window.removeEventListener('resize', handleResize);
		};
	});
</script>


<div class="flex h-screen overflow-hidden bg-[#F4F7FE] dark:bg-gray-900 transition-colors duration-200 ease-in-out">
	<div class={`sidebar-container ${isSidebarOpen ? '' : 'collapsed'}`}>
		<Sidebar {isSidebarOpen} {activePage} isDarkMode={currentIsDarkMode} />
	</div>

	<div class="flex-1 flex flex-col overflow-hidden relative z-10 bg-[#F4F7FE] dark:bg-gray-900">
		<Navbar
			{username}
			{toggleSidebar}
			isDarkMode={currentIsDarkMode}
			on:darkModeToggle={toggleDarkMode}
		/>

		<div class="flex-1 overflow-y-auto p-4 md:p-6 bg-[#F4F7FE] dark:bg-gray-900 text-gray-800 dark:text-gray-100">
			<slot />
		</div>
	</div>

	<!-- Mobile sidebar overlay when open on mobile - lower z-index than content - hide in fullscreen -->
	{#if isMobile && isSidebarOpen && !$isFullscreenAvatar}

	{#if isMobile && isSidebarOpen}
		<div
			class="fixed inset-0 bg-black bg-opacity-70 z-5"
			on:click={() => {
				isSidebarOpen = false;
			}}
			aria-hidden="true"
		></div>
	{/if}
	
	<!-- Form overlay backdrop when form is open -->
	{#if currentFormBlur}
		<div
			class="fixed inset-0 bg-black bg-opacity-30 z-40 backdrop-blur-sm"
			aria-hidden="true"
		></div>
	{/if}
</div>

<style>
	:global(.flex-1) {
		min-height: 0; 
	}
	
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
	
	:global(.dark) {
		color-scheme: dark;
	}
	:global(.dark *:focus) {
		outline-color: #60a5fa;
	}
	
	.sidebar-container {
		transition: all 0.3s ease;
		z-index: 20;
		position: relative;
	}
	
	.sidebar-container.collapsed {
		margin-left: -256px; 
	}
	
	.navbar-container {
		transition: all 0.3s ease;
		position: relative;
		z-index: 15;
	}
	
	.form-blur {
		filter: blur(4px);
		pointer-events: none;
		user-select: none;
	}
	
	.form-blur-backdrop {
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
		opacity: 0.7;
		pointer-events: none;
		user-select: none;
	}
	
	.sidebar-container {
		transition: all 0.3s ease;
		z-index: 20;
	}

	.sidebar-container.collapsed {
		margin-left: -256px; /* Match sidebar width when closed */
	}

	/* Mobile styles */
		margin-left: -256px;
	}

	@media (max-width: 767px) {
		.sidebar-container {
			position: fixed;
			height: 100%;
			z-index: 30;
		}
		.sidebar-container.collapsed {
			margin-left: -100%; 
		}
		
		.form-blur {
			filter: blur(2px);
		}
	}
	
	@media (min-width: 768px) and (max-width: 1023px) {
		.sidebar-container:not(.collapsed) {
			width: auto;
		}
	}
	
	.sidebar-container,
	.navbar-container {
		transition: 
			filter 0.3s ease-in-out,
			opacity 0.3s ease-in-out,
			transform 0.3s ease-in-out;
	}
	
	.form-blur * {
		pointer-events: none !important;
	}
</style>
