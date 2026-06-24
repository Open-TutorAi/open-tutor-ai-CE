<!-- Teacher Layout -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get, writable, derived } from 'svelte/store';

	import Sidebar from '$lib/components/teacher/elements/Sidebar.svelte';
	import Navbar from '$lib/components/teacher/elements/Navbar.svelte';

	import { getModels, getVersionUpdates } from '$lib/apis';
	import { config, user, settings, models, theme} from '$lib/stores';
	

	const activePage = writable('dashboard');
	let isSidebarOpen = true;
	let username = '';

	// Extract first name from user's full name
	$: if ($user && $user.name) {
		username = $user.name.split(' ')[0];
	}

	let windowWidth: number;
	let isMobile: boolean = false;

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

	function toggleDarkMode(event: CustomEvent) {
		const newTheme = event.detail.isDarkMode ? 'dark' : 'light';
		theme.set(newTheme);
		localStorage.setItem('theme', newTheme);
	}

	onMount(async () => {
		
		models.set(
			await getModels(
				localStorage.token,
				$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
			)
		);

		const currentUser = get(user);
		if (!currentUser) {
			goto('/auth');
			return;
		}
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

		<div class="flex-1 overflow-y-auto {$page.url.pathname.startsWith('/teacher/messages') ? '' : 'p-4 md:p-6'} bg-[#F4F7FE] dark:bg-gray-900 text-gray-800 dark:text-gray-100">
			<slot />
		</div>
	</div>

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
	:global(.flex-1) {
		min-height: 0;
	}

	.sidebar-container {
		transition: all 0.3s ease;
		z-index: 20;
	}

	.sidebar-container.collapsed {
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
	}
</style>
