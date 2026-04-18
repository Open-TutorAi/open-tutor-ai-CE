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
		console.log('Teacher layout mounted');
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
		if (currentUser.role !== 'teacher') {
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
	
	:global(#chat-container) {
		display: flex;
		flex-direction: column;
		height: 100%;
		overflow: hidden;
	}
	
	:global(body, html) {
		height: 100%;
		margin: 0;
		padding: 0;
		overflow: hidden;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
			'Open Sans', 'Helvetica Neue', sans-serif;
	}
	
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