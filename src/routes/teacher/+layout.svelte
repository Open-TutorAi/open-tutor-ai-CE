<<<<<<< HEAD
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
	
=======
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

>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
	// Derive isDarkMode from theme store
	const isDarkMode = derived(theme, ($theme) => {
		return (
			$theme === 'dark' ||
			($theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
		);
	});
<<<<<<< HEAD
	
=======

>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
	// Subscribe to isDarkMode to get the actual boolean value
	let currentIsDarkMode = false;
	isDarkMode.subscribe((value) => {
		currentIsDarkMode = value;
		document.documentElement.classList.toggle('dark', value);
	});
<<<<<<< HEAD
	
	function toggleSidebar() {
		isSidebarOpen = !isSidebarOpen;
	}
	
=======

	function toggleSidebar() {
		isSidebarOpen = !isSidebarOpen;
	}

>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
	function toggleDarkMode(event: CustomEvent) {
		const newTheme = event.detail.isDarkMode ? 'dark' : 'light';
		theme.set(newTheme);
		localStorage.setItem('theme', newTheme);
	}
<<<<<<< HEAD
	
	onMount(async () => {
		console.log('Teacher layout mounted');
		models.set(
			await getModels(
				localStorage.token,
				$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
			)
		);
		
=======

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
>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
		// Role protection logic
		const currentUser = get(user);
		if (!currentUser) {
			goto('/auth');
			return;
		}
<<<<<<< HEAD
		if (currentUser.role !== 'teacher') {
=======
		if (currentUser.role !== 'user') {
>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
			console.log('User is not a teacher, redirecting to home');
			goto(`/${currentUser.role}`);
			return;
		}
		loading = false;
<<<<<<< HEAD
		
=======

>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
		// Initialize dark mode based on global theme
		const currentTheme = get(theme);
		const isDark =
			currentTheme === 'dark' ||
			(currentTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
		document.documentElement.classList.toggle('dark', isDark);
<<<<<<< HEAD
		
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
=======

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
>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
	});
</script>

<div
	class="flex h-screen overflow-hidden bg-[#F4F7FE] dark:bg-gray-900 transition-colors duration-200 ease-in-out"
>
<<<<<<< HEAD
	<!-- Sidebar with adaptive behavior and blur effect -->
	<div class={`sidebar-container ${isSidebarOpen ? '' : 'collapsed'} ${currentFormBlur ? 'form-blur' : ''}`}>
		<Sidebar {isSidebarOpen} {activePage} isDarkMode={currentIsDarkMode} />
	</div>

	<!-- Main content area with navbar and slot -->
	<div class="flex-1 flex flex-col overflow-hidden relative z-10 bg-[#F4F7FE] dark:bg-gray-900">
		<!-- Navbar with blur effect when form is open -->
		<div class={`navbar-container ${currentFormBlur ? 'form-blur' : ''}`}>
			<Navbar
				role="teacher"
				username={$user.name}
				toggleSidebar={toggleSidebar}
				isDarkMode={currentIsDarkMode}
				on:darkModeToggle={toggleDarkMode}
			/>
		</div>

		<!-- Main content with proper scrolling -->
		<div
			class="flex-1 overflow-y-auto p-4 md:p-6 bg-[#F4F7FE] dark:bg-gray-900 text-gray-800 dark:text-gray-100"
		>
			<slot {setFormBlur} {formBlurStore} />
		</div>
	</div>

	<!-- Mobile sidebar overlay when open on mobile - lower z-index than content -->
	{#if isMobile && isSidebarOpen}
=======
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
			<slot />
		</div>
	</div>

	<!-- Mobile sidebar overlay when open on mobile - lower z-index than content - hide in fullscreen -->
	{#if isMobile && isSidebarOpen && !$isFullscreenAvatar}
>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
		<div
			class="fixed inset-0 bg-black bg-opacity-70 z-5"
			on:click={() => {
				isSidebarOpen = false;
			}}
			aria-hidden="true"
		></div>
	{/if}
<<<<<<< HEAD
	
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
	
=======
</div>

<style>
	/* Add this to ensure nested layouts work properly */
	:global(.flex-1) {
		min-height: 0; /* This is crucial for proper flex behavior */
	}

	/* Make sure content containers have proper layout */
>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
	:global(#chat-container) {
		display: flex;
		flex-direction: column;
		height: 100%;
		overflow: hidden;
	}
<<<<<<< HEAD
	
=======
	/* Base styles */
>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
	:global(body, html) {
		height: 100%;
		margin: 0;
		padding: 0;
		overflow: hidden;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
			'Open Sans', 'Helvetica Neue', sans-serif;
	}
<<<<<<< HEAD
	
=======

	/* Add dark mode transition for smoother theme switching */
>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
	:global(body),
	:global(body *) {
		transition:
			background-color 0.3s ease,
			color 0.3s ease;
	}
<<<<<<< HEAD
	
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
	
=======

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
>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
	@media (max-width: 767px) {
		.sidebar-container {
			position: fixed;
			height: 100%;
			z-index: 30;
		}
<<<<<<< HEAD
		.sidebar-container.collapsed {
			margin-left: -100%; 
		}
		
		.form-blur {
			filter: blur(2px);
		}
	}
	
=======

		.sidebar-container.collapsed {
			margin-left: -100%; /* Fully hide on mobile */
		}
	}

	/* Tablet adjustments */
>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
	@media (min-width: 768px) and (max-width: 1023px) {
		.sidebar-container:not(.collapsed) {
			width: auto;
		}
	}
<<<<<<< HEAD
	
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
=======
</style>
>>>>>>> 11814d0 (feat: implement teacher screens using mock data to validate UX, navigation, i18n, and reusable components.)
