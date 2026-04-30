<!-- Teacher Layout with Form Blur Effect -->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { get, writable, derived } from 'svelte/store';

	import Sidebar from '$lib/components/teacher/elements/SidebarTeacher.svelte';
	import Navbar from '$lib/components/teacher/elements/Navbar.svelte';
	import DemoModeBanner from '$lib/components/DemoModeBanner.svelte';

	import { getModels } from '$lib/apis';
	import {
		config,
		user,
		settings,
		models,
		theme,
		isDemo,
		demoData,
		originalUserData,
		isFullscreenAvatar
	} from '$lib/stores';
	import { generateDemoData } from '$lib/utils/mockData';
	import { toast } from 'svelte-sonner';

	// Add form state management for blur effect
	export let isFormOpen = false;
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
	const unsubscribeFormBlur = formBlurStore.subscribe((value) => {
		currentFormBlur = value;
	});

	const activePage = writable('dashboard');

	// Extract first name from user's full name
	$: if ($user && $user.name) {
		username = $user.name.split(' ')[0];
	}

	// Derive isDarkMode from theme store
	const isDarkMode = derived(theme, ($theme) => {
		if (typeof window === 'undefined') return false;
		return (
			$theme === 'dark' ||
			($theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
		);
	});

	let currentIsDarkMode = false;
	const unsubscribeTheme = isDarkMode.subscribe((value) => {
		currentIsDarkMode = value;
		if (typeof document !== 'undefined') {
			document.documentElement.classList.toggle('dark', value);
		}
	});

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
			if ($originalUserData) {
				user.set($originalUserData);
				originalUserData.set(null);
			}
			demoData.set({
				dashboard: {
					progress: 0,
					coursesCompleted: 0,
					currentStreak: 0,
					weeklyGoal: { completed: 0, target: 5 },
					totalLearningHours: 0,
					achievements: 0
				},
				chats: [],
				supports: [],
				assignments: [],
				courses: []
			});
			isDemo.set(false);
			localStorage.removeItem('demoMode');
			toast.success('Demo mode deactivated. Back to your real data.');
		} else {
			originalUserData.set($user);
			const mockData = generateDemoData();
			demoData.set(mockData);
			isDemo.set(true);
			localStorage.setItem('demoMode', 'true');
			toast.success("Demo mode activated. You're now exploring with sample data.");
		}
	}

	const handleResize = () => {
		if (typeof window === 'undefined') return;
		windowWidth = window.innerWidth;
		isMobile = windowWidth < 768;

		if (isMobile && isSidebarOpen) {
			isSidebarOpen = false;
		} else if (!isMobile && !isSidebarOpen) {
			isSidebarOpen = true;
		}
	};

	onMount(async () => {
		console.log('teacher layout mounted');

		const currentUser = get(user);
		if (!currentUser) {
			goto('/auth');
			return;
		}

		// Check if demo mode was previously active
		const wasDemoMode = localStorage.getItem('demoMode') === 'true';
		if (wasDemoMode && !$isDemo) {
			const mockData = generateDemoData();
			originalUserData.set($user);
			demoData.set(mockData);
			isDemo.set(true);
		} else if ($isDemo && $demoData.chats.length === 0) {
			const mockData = generateDemoData();
			demoData.set(mockData);
		}

		models.set(
			await getModels(
				localStorage.token,
				$config?.features?.enable_direct_connections ? ($settings?.directConnections ?? null) : null
			)
		);

		handleResize();
		window.addEventListener('resize', handleResize);
		loading = false;
	});

	onDestroy(() => {
		unsubscribeFormBlur();
		unsubscribeTheme();
		if (typeof window !== 'undefined') {
			window.removeEventListener('resize', handleResize);
		}
	});
</script>

{#if !loading}
	<div
		class="flex h-screen overflow-hidden bg-[#F4F7FE] dark:bg-gray-900 transition-colors duration-200 ease-in-out"
	>
		<!-- Sidebar -->
		{#if !$isFullscreenAvatar}
			<div
				class={`sidebar-container ${isSidebarOpen ? '' : 'collapsed'} ${currentFormBlur ? 'form-blur' : ''}`}
			>
				<Sidebar {isSidebarOpen} {activePage} isDarkMode={currentIsDarkMode} />
			</div>
		{/if}

		<!-- Main content area -->
		<div class="flex-1 flex flex-col overflow-hidden relative z-10 bg-[#F4F7FE] dark:bg-gray-900">
			<!-- Navbar -->
			{#if !$isFullscreenAvatar}
				<div class={`navbar-container ${currentFormBlur ? 'form-blur' : ''}`}>
					<Navbar
						role="teacher"
						username={$user?.name || username}
						{toggleSidebar}
						isDarkMode={currentIsDarkMode}
						on:darkModeToggle={toggleDarkMode}
					/>
				</div>
			{/if}

			{#if $isDemo}
				<DemoModeBanner on:toggle={toggleDemoMode} />
			{/if}

			<!-- Main content with proper scrolling -->
			<div
				class={`flex-1 overflow-y-auto p-4 md:p-6 bg-[#F4F7FE] dark:bg-gray-900 text-gray-800 dark:text-gray-100 ${currentFormBlur ? 'form-blur' : ''}`}
			>
				<slot {setFormBlur} {formBlurStore} />
			</div>
		</div>

		<!-- Mobile sidebar overlay -->
		{#if isMobile && isSidebarOpen && !$isFullscreenAvatar}
			<div
				class="fixed inset-0 bg-black bg-opacity-50 z-20 backdrop-blur-sm"
				on:click={() => (isSidebarOpen = false)}
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
{/if}

<style>
	:global(.flex-1) {
		min-height: 0;
	}

	:global(body, html) {
		height: 100%;
		margin: 0;
		padding: 0;
		overflow: hidden;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
			'Open Sans', 'Helvetica Neue', sans-serif;
	}

	:global(body) {
		background-color: #f4f7fe;
	}

	:global(.dark body) {
		background-color: #111827;
	}

	.sidebar-container {
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		z-index: 30;
		position: relative;
		width: 256px;
		flex-shrink: 0;
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

	@media (max-width: 767px) {
		.sidebar-container {
			position: fixed;
			height: 100%;
			z-index: 40;
		}
		.sidebar-container.collapsed {
			transform: translateX(-100%);
			margin-left: 0;
		}
	}

	.sidebar-container,
	.navbar-container {
		transition:
			filter 0.3s ease-in-out,
			opacity 0.3s ease-in-out,
			transform 0.3s ease-in-out;
	}
</style>
