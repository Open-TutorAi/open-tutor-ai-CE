<!-- +layout.svelte -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';
	import Sidebar from '$lib/components/student/components/Sidebar.svelte';
	import Navbar from '$lib/components/student/components/Navbar.svelte';

	// Create a store for active page
	const activePage = writable('dashboard');
	let isSidebarOpen = true;
	let isDarkMode = false;
	let username = 'Karim';

	function toggleSidebar() {
		isSidebarOpen = !isSidebarOpen;
	}

	function toggleDarkMode(event: CustomEvent) {
		isDarkMode = event.detail.isDarkMode;
		document.documentElement.classList.toggle('dark', isDarkMode);
	}

	// For mobile responsiveness
	let windowWidth: number;
	let isMobile: boolean = false;

	onMount(() => {
		// Handle resize events for responsive design
		const handleResize = () => {
			windowWidth = window.innerWidth;
			isMobile = windowWidth < 768;

			// Auto-close sidebar on small screens initially
			if (isMobile && isSidebarOpen) {
				isSidebarOpen = false;
			} else if (!isMobile && !isSidebarOpen) {
				isSidebarOpen = true;
			}
		};

		window.addEventListener('resize', handleResize);
		handleResize(); // Initialize

		return () => {
			window.removeEventListener('resize', handleResize);
		};
	});
</script>

<div class="flex h-screen overflow-hidden bg-[#F4F7FE] transition-colors duration-200 ease-in-out">
	<!-- Sidebar with adaptive behavior -->
	<div class={`sidebar-container ${isSidebarOpen ? '' : 'collapsed'}`}>
		<Sidebar {isSidebarOpen} {activePage} />
	</div>

	<!-- Main content area with navbar and slot -->
	<div class="flex-1 flex flex-col overflow-hidden relative z-10 bg-[#F4F7FE]">
		<Navbar {username} {toggleSidebar} {isDarkMode} on:darkModeToggle={toggleDarkMode} />

		<!-- Main content with proper scrolling -->
		<div class="flex-1 overflow-y-auto p-4 md:p-6 bg-[#F4F7FE] text-gray-800">
			<slot />
		</div>
	</div>

	<!-- Mobile sidebar overlay when open on mobile - lower z-index than content -->
	{#if isMobile && isSidebarOpen}
		<div
			class="fixed inset-0 bg-black bg-opacity-50 z-5"
			on:click={() => {
				isSidebarOpen = false;
			}}
			aria-hidden="true"
		></div>
	{/if}
</div>

<style>
	/* Base styles */
	:global(body, html) {
		height: 100%;
		margin: 0;
		padding: 0;
		overflow: hidden;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
			'Open Sans', 'Helvetica Neue', sans-serif;
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
