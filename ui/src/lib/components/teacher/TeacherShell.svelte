<!-- Shared chrome (sidebar + auth guard) for every /teacher and /classrooms page. -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { get, derived, writable } from 'svelte/store';

	import Sidebar from '$lib/components/student/elements/Sidebar.svelte';
	import Navbar from '$lib/components/student/elements/Navbar.svelte';
	import { user, theme } from '$lib/stores';

	const activePage = writable('dashboard');
	let isSidebarOpen = true;
	let isMobile = false;
	let loading = true;
	let username = '';

	$: if ($user?.name) {
		username = $user.name.split(' ')[0];
	}

	const isDarkMode = derived(theme, ($theme) => {
		if (typeof window === 'undefined') return false;
		return (
			$theme === 'dark' ||
			($theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
		);
	});

	let currentIsDarkMode = false;
	isDarkMode.subscribe((value) => {
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

	onMount(() => {
		const currentUser = get(user);
		if (!currentUser) {
			goto('/auth');
			return;
		}
		if (currentUser.role !== 'teacher') {
			goto(`/${currentUser.role}`);
			return;
		}
		loading = false;

		const handleResize = () => {
			isMobile = window.innerWidth < 768;
			if (isMobile && isSidebarOpen) {
				isSidebarOpen = false;
			} else if (!isMobile && !isSidebarOpen) {
				isSidebarOpen = true;
			}
		};
		window.addEventListener('resize', handleResize);
		handleResize();

		return () => window.removeEventListener('resize', handleResize);
	});
</script>

{#if loading}
	<div class="flex justify-center items-center min-h-screen bg-[#F4F7FE] dark:bg-gray-900">
		<div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
	</div>
{:else}
	<div
		class="flex h-screen overflow-hidden bg-[#F4F7FE] dark:bg-gray-900 transition-colors duration-200 ease-in-out"
	>
		<div class={`sidebar-container ${isSidebarOpen ? '' : 'collapsed'}`}>
			<Sidebar bind:isSidebarOpen {activePage} isDarkMode={currentIsDarkMode} forceRole="teacher" />
		</div>

		<div class="flex-1 flex flex-col overflow-hidden relative z-10 bg-[#F4F7FE] dark:bg-gray-900">
			<Navbar
				{username}
				{toggleSidebar}
				isDarkMode={currentIsDarkMode}
				subtitle="Manage your classrooms and track student progress"
				on:darkModeToggle={toggleDarkMode}
			/>

			<div
				class="flex-1 overflow-y-auto p-4 md:p-6 bg-[#F4F7FE] dark:bg-gray-900 text-gray-800 dark:text-gray-100"
			>
				<slot />
			</div>
		</div>

		{#if isMobile && isSidebarOpen}
			<div
				class="fixed inset-0 bg-black bg-opacity-70 z-5"
				on:click={() => (isSidebarOpen = false)}
				aria-hidden="true"
			></div>
		{/if}
	</div>
{/if}

<style>
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
