<!-- Navbar.svelte -->
<script lang="ts">
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	const i18n = getContext('i18n');
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';

	// Props
	export let username: string = 'Prof. Youssef ES-SAADY';
	export let toggleSidebar: () => void;
	export let isDarkMode: boolean = false;

	// State
	let searchQuery: string = '';
	let notificationCount: number = 0;
	let isSearchFocused: boolean = false;
	let showNotifications: boolean = false;
	let showMobileMenu: boolean = false;

	let showUserDropdown: boolean = false;

	// Add this function around line 43 with other toggle functions
	function toggleUserDropdown() {
		showUserDropdown = !showUserDropdown;
	}

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Functions
	function toggleDarkMode() {
		isDarkMode = !isDarkMode;
		dispatch('darkModeToggle', { isDarkMode });
	}

	function handleSearch(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			dispatch('search', { query: searchQuery });
		}
	}

	function toggleNotificationPanel() {
		showNotifications = !showNotifications;
	}

	function toggleMobileMenu() {
		showMobileMenu = !showMobileMenu;
	}

	function createNewCourse() {
		// TODO: Implement create new course functionality
		console.log('Create new course clicked');
	}

	// Click outside for notifications panel
	let notificationRef: HTMLDivElement;
	let mobileMenuRef: HTMLDivElement;

	onMount(() => {
		const handleClickOutside = (event: MouseEvent) => {
			// Keep your existing code for notification and mobile menu
			if (notificationRef && !notificationRef.contains(event.target as Node) && showNotifications) {
				showNotifications = false;
			}
			if (mobileMenuRef && !mobileMenuRef.contains(event.target as Node) && showMobileMenu) {
				showMobileMenu = false;
			}
			// Add this new condition for the user dropdown
			const userDropdownRef = document.getElementById('user-dropdown-container');
			if (userDropdownRef && !userDropdownRef.contains(event.target as Node) && showUserDropdown) {
				showUserDropdown = false;
			}
		};

		document.addEventListener('click', handleClickOutside);

		return () => {
			document.removeEventListener('click', handleClickOutside);
		};
	});
</script>

<header
	class={`${isDarkMode ? 'bg-gray-900 text-gray-100' : 'bg-white text-gray-800'} shadow-sm p-4 flex items-center justify-between transition-colors duration-200 ease-in-out  z-[999]`}
>
	<div class="flex items-center">
		<!-- Mobile menu button - visible on mobile only -->
		<button
			class={`md:hidden mr-3 ${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'} focus:outline-none focus:ring-2 focus:ring-blue-300 rounded-md`}
			on:click={toggleSidebar}
			aria-label="Toggle navigation menu"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-6 w-6"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M4 6h16M4 12h16M4 18h16"
				/>
			</svg>
		</button>

		<div class="ml-4">
			<h1
				class={`text-xl font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-800'} flex items-center gap-2`}
			>
				<span class="hidden sm:inline">
					{$i18n.t('Hello')} {username}
				</span>
			</h1>
			<p class={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'} hidden sm:block`}>
				{$i18n.t('Welcome to your Teacher Dashboard')}
			</p>
		</div>
	</div>

	<!-- Desktop Navigation Menu -->
	<div class="hidden md:flex items-center gap-4">
		<!-- Search -->
		<div class={`relative ${isSearchFocused ? 'md:w-64 transition-all duration-300' : 'md:w-40'}`}>
			<div
				class={`flex items-center ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'} rounded-full px-4 py-2 border shadow-sm ${isSearchFocused ? 'ring-2 ring-blue-300 shadow-md' : ''}`}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class={`h-4 w-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-400'}`}
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
					/>
				</svg>
				<input
					type="text"
					placeholder={$i18n.t('Search')}
					class={`bg-transparent border-none outline-none focus:ring-0 px-2 py-1 w-full text-sm ${isDarkMode ? 'text-gray-100 placeholder-gray-400' : 'text-gray-700'}`}
					bind:value={searchQuery}
					on:keydown={handleSearch}
					on:focus={() => (isSearchFocused = true)}
					on:blur={() => (isSearchFocused = false)}
					aria-label="Search"
				/>
				{#if searchQuery}
					<button
						on:click={() => (searchQuery = '')}
						class={`${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-400 hover:text-gray-600'}`}
						aria-label="Clear search"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-4 w-4"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M6 18L18 6M6 6l12 12"
							/>
						</svg>
					</button>
				{/if}
			</div>
		</div>

		<!-- Notification -->
		<div class="relative" bind:this={notificationRef}>
			<button
				class={`p-2 ${isDarkMode ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' : 'text-gray-500 hover:text-gray-600 hover:bg-gray-50'} rounded-full focus:outline-none focus:ring-2 focus:ring-blue-300`}
				on:click={toggleNotificationPanel}
				aria-label={`Notifications${notificationCount > 0 ? ` (${notificationCount} unread)` : ''}`}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
					/>
				</svg>
				{#if notificationCount > 0}
					<span
						class="absolute top-0 right-0 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-xs text-white"
						>{notificationCount}</span
					>
				{/if}
			</button>

			<!-- Notification Panel -->
			{#if showNotifications}
				<div
					class={`absolute right-0 mt-2 w-80 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg shadow-lg border z-50`}
				>
					<div class={`p-4 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
						<h3 class={`font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-800'}`}>
							{$i18n.t('Notifications')}
						</h3>
					</div>
					<div class="max-h-64 overflow-y-auto">
						<!-- Placeholder for notifications -->
						<div class={`p-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'} text-center`}>
							{$i18n.t('No new notifications')}
						</div>
					</div>
				</div>
			{/if}
		</div>

		<!-- Dark Mode Toggle -->
		<button
			class={`p-2 ${isDarkMode ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' : 'text-gray-500 hover:text-gray-600 hover:bg-gray-50'} rounded-full focus:outline-none focus:ring-2 focus:ring-blue-300`}
			on:click={toggleDarkMode}
			aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
		>
			{#if isDarkMode}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
					/>
				</svg>
			{:else}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
					/>
				</svg>
			{/if}
		</button>

		<!-- User Menu -->
		<div class="relative" id="user-dropdown-container">
			<button
				class={`flex items-center gap-2 p-2 ${isDarkMode ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' : 'text-gray-500 hover:text-gray-600 hover:bg-gray-50'} rounded-full focus:outline-none focus:ring-2 focus:ring-blue-300`}
				on:click={toggleUserDropdown}
				aria-label="User menu"
			>
				<div
					class={`w-8 h-8 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-200'} rounded-full flex items-center justify-center`}
				>
					<span class={`text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
						{username.charAt(0).toUpperCase()}
					</span>
				</div>
			</button>

			<!-- User Dropdown -->
			{#if showUserDropdown}
				<div
					class={`absolute right-0 mt-2 w-48 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg shadow-lg border z-50`}
				>
					<div class={`p-4 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
						<p class={`font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-800'}`}>
							{username}
						</p>
						<p class={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
							{$i18n.t('Teacher')}
						</p>
					</div>
					<div class="py-1">
						<button
							class={`w-full text-left px-4 py-2 ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'} transition-colors duration-200`}
							on:click={() => goto('/teacher/settings')}
						>
							{$i18n.t('Profile & Settings')}
						</button>
						<button
							class={`w-full text-left px-4 py-2 ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'} transition-colors duration-200`}
							on:click={() => goto('/auth')}
						>
							{$i18n.t('Sign Out')}
						</button>
					</div>
				</div>
			{/if}
		</div>
	</div>

	<!-- Mobile Menu -->
	<div class="md:hidden" bind:this={mobileMenuRef}>
		<button
			class={`p-2 ${isDarkMode ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' : 'text-gray-500 hover:text-gray-600 hover:bg-gray-50'} rounded-full focus:outline-none focus:ring-2 focus:ring-blue-300`}
			on:click={toggleMobileMenu}
			aria-label="Mobile menu"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-6 w-6"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
				/>
			</svg>
		</button>

		<!-- Mobile Menu Panel -->
		{#if showMobileMenu}
			<div
				class={`absolute right-4 top-16 w-48 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg shadow-lg border z-50`}
			>
				<div class="py-1">
					<button
						class={`w-full text-left px-4 py-2 ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'} transition-colors duration-200`}
						on:click={() => goto('/teacher/settings')}
					>
						{$i18n.t('Profile & Settings')}
					</button>
					<button
						class={`w-full text-left px-4 py-2 ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'} transition-colors duration-200`}
						on:click={toggleDarkMode}
					>
						{isDarkMode ? $i18n.t('Light Mode') : $i18n.t('Dark Mode')}
					</button>
					<button
						class={`w-full text-left px-4 py-2 ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'} transition-colors duration-200`}
						on:click={() => goto('/auth')}
					>
						{$i18n.t('Sign Out')}
					</button>
				</div>
			</div>
		{/if}
	</div>
</header>