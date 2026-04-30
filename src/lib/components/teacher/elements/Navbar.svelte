<!-- Navbar.svelte -->
<script lang="ts">
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	const i18n = getContext('i18n');
	import { goto } from '$app/navigation';
	import { user, isDemo, demoData, originalUserData } from '$lib/stores';
	import { generateDemoData } from '$lib/utils/mockData';
	import { toast } from 'svelte-sonner';
	import { generateInitialsImage } from '$lib/utils';
	import { get } from 'svelte/store';
	import { user } from '$lib/stores';
	import i18next from 'i18next';

	// Props
	export let username: string = '';
	export let toggleSidebar: () => void;
	export let isDarkMode: boolean = false;

	// State
	let searchQuery: string = '';
	let notificationCount: number = 0;
	let isSearchFocused: boolean = false;
	let showNotifications: boolean = false;
	let showMobileMenu: boolean = false;

	let showUserDropdown: boolean = false;

	let profileImageUrl = '';

	// reactive assignment to update when store changes
	$: profileImageUrl = $user?.profile_image_url || generateInitialsImage($user?.name || 'User');

	// Add this function around line 43 with other toggle functions
	let showLanguageMenu: boolean = false;
	let currentLanguage: string = 'fr-FR';
	let showUserDropdown: boolean = false;

	function toggleUserDropdown() {
		showUserDropdown = !showUserDropdown;
	}

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Functions
	function toggleLanguageMenu() {
		showLanguageMenu = !showLanguageMenu;
	}

	function changeLanguage(lang: string) {
		// Properly change language and trigger the event
		i18next.changeLanguage(lang);
		currentLanguage = lang;
		showLanguageMenu = false;
	}

	const dispatch = createEventDispatcher();

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
			toast.success($i18n.t('Demo mode deactivated. Back to your real data.'));
		} else {
			// Enter demo mode
			originalUserData.set($user);
			const mockData = generateDemoData();
			demoData.set(mockData);
			isDemo.set(true);
			localStorage.setItem('demoMode', 'true');
			toast.success($i18n.t('Demo mode activated. You\'re now exploring with sample data.'));
		}
		showUserDropdown = false;
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
			const langDropdownRef = document.getElementById('language-dropdown-container');
			if (langDropdownRef && !langDropdownRef.contains(event.target as Node) && showLanguageMenu) {
				showLanguageMenu = false;
			}
		};

		// Initialize language on mount
		currentLanguage = i18next.language || 'fr-FR';

		// Listen for language changes from other components
		const handleLanguageChange = (lng: string) => {
			currentLanguage = lng;
		};
		i18next.on('languageChanged', handleLanguageChange);

		document.addEventListener('click', handleClickOutside);
		return () => {
			document.removeEventListener('click', handleClickOutside);
			i18next.off('languageChanged', handleLanguageChange);
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
<header class={`navbar-root ${isDarkMode ? 'navbar-dark' : 'navbar-light'}`}>

	<!-- Left: toggle + greeting -->
	<div class="flex items-center">
		<button
			class={`btn-mobile-toggle md:hidden ${isDarkMode ? 'icon-dark' : 'icon-light'}`}
			on:click={toggleSidebar}
			aria-label="Toggle navigation menu"
		>
			<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
			</svg>
		</button>

		<div class="ml-4">
			<h1
				class={`text-xl font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-800'} flex items-center gap-2`}
			>
				<span class="hidden sm:inline">
					{username ? $i18n.t('Hello') + ' ' + username + ' 👋': $i18n.t('Hello')}
				</span>
			</h1>
			<p class={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'} hidden sm:block`}>
				{$i18n.t("Let's learn something new today!")}
			<h1 class={`navbar-title ${isDarkMode ? 'text-dark' : 'text-light'}`}>
				<span class="hidden sm:inline inline-flex items-center gap-2">
					{username ? $i18n.t('Hello Professor') + ' ' + username : $i18n.t('Hello Professor')}
					<span class="animate-wave" aria-hidden="true">👋</span>
				</span>
			</h1>
			<p class={`navbar-subtitle ${isDarkMode ? 'subtext-dark' : 'subtext-light'} hidden sm:block`}>
				{$i18n.t("Here's what's happening in your classes today")}
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
	<!-- Desktop nav -->
	<div class="hidden md:flex items-center gap-4">

		<!-- Search -->
		<div class={`search-wrapper ${isSearchFocused ? 'search-focused' : 'search-idle'}`}>
			<div class={`search-inner ${isDarkMode ? 'search-dark' : 'search-light'} ${isSearchFocused ? 'search-ring' : ''}`}>
				<svg xmlns="http://www.w3.org/2000/svg" class="search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<input
					type="text"
					placeholder={$i18n.t('Search')}
					class={`bg-transparent border-none outline-none focus:ring-0 px-2 py-1 w-full text-sm ${isDarkMode ? 'text-gray-100 placeholder-gray-400' : 'text-gray-700'}`}
					class={`search-input ${isDarkMode ? 'search-input-dark' : 'search-input-light'}`}
					bind:value={searchQuery}
					on:keydown={handleSearch}
					on:focus={() => (isSearchFocused = true)}
					on:blur={() => (isSearchFocused = false)}
					aria-label="Search"
					aria-label={$i18n.t('Search')}
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
						class={`search-clear ${isDarkMode ? 'icon-dark' : 'icon-light'}`}
						aria-label={$i18n.t('Clear search')}
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
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
			<!-- Notification panel -->
			{#if showNotifications}
				<div
					class={`absolute right-0 mt-2 w-64 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-100'} rounded-lg shadow-lg z-50 border`}
				>
					<div
						class={`p-3 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-100'} flex justify-between items-center`}
					>
						<h3 class={`font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-800'}`}>
							{$i18n.t('Notifications')}
						</h3>
						<button
							class={`text-xs ${isDarkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-500 hover:text-blue-700'}`}

		<!-- Notifications -->
		<div class="relative" bind:this={notificationRef}>
			<button
				class={`btn-icon ${isDarkMode ? 'btn-icon-dark' : 'btn-icon-light'}`}
				on:click={toggleNotificationPanel}
				aria-label={`${$i18n.t('Notifications')}${notificationCount > 0 ? ` (${notificationCount} ${$i18n.t('unread')})` : ''}`}
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
				</svg>
				{#if notificationCount > 0}
					<span class="badge-count">{notificationCount}</span>
				{/if}
			</button>

			{#if showNotifications}
				<div class={`dropdown-panel ${isDarkMode ? 'dropdown-dark' : 'dropdown-light'}`}>
					<div class={`dropdown-header ${isDarkMode ? 'dropdown-divider-dark' : 'dropdown-divider-light'}`}>
						<h3 class={`dropdown-title ${isDarkMode ? 'text-dark' : 'text-light'}`}>
							{$i18n.t('Notifications')}
						</h3>
						<button
							class={`link-btn ${isDarkMode ? 'link-dark' : 'link-light'}`}
							on:click={() => (notificationCount = 0)}
						>
							{$i18n.t('Mark all as read')}
						</button>
					</div>
					<!-- <div class="p-2 max-h-64 overflow-y-auto">
						<div class={`p-2 ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-50'} rounded-lg`}>
							<p class={`text-sm font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-800'}`}>
								{$i18n.t('New course available')}
							</p>
							<p class={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
								{$i18n.t('React Advanced Patterns')}
							</p>
							<p class={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-400'} mt-1`}>
								{$i18n.t('2 hours ago')}
							</p>
						</div>
						<div class={`p-2 ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-50'} rounded-lg`}>
							<p class={`text-sm font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-800'}`}>
								{$i18n.t('Assignment feedback')}
							</p>
							<p class={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
								{$i18n.t('Your JavaScript project has been reviewed')}
							</p>
							<p class={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-400'} mt-1`}>
								{$i18n.t('Yesterday')}
							</p>
						</div>
					</div> -->
					<div class={`p-2 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-100'}`}>
						<button
							class={`w-full text-center text-sm ${isDarkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-500 hover:text-blue-700'}`}
						>
					<div class={`dropdown-footer ${isDarkMode ? 'dropdown-divider-dark' : 'dropdown-divider-light'}`}>
						<button class={`link-btn-full ${isDarkMode ? 'link-dark' : 'link-light'}`}>
							{$i18n.t('View all notifications')}
						</button>
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Dark mode toggle -->
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

		<!-- Dark mode toggle -->
		<button
			class={`btn-icon ${isDarkMode ? 'btn-icon-dark' : 'btn-icon-light'}`}
			on:click={toggleDarkMode}
			aria-label={isDarkMode ? $i18n.t('Switch to light mode') : $i18n.t('Switch to dark mode')}
		>
			{#if isDarkMode}
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
				</svg>
			{:else}
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
				</svg>
			{/if}
		</button>

		<!-- Help/Info -->
		<button
			class={`p-2 ${isDarkMode ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' : 'text-gray-500 hover:text-gray-600 hover:bg-gray-50'} rounded-full focus:outline-none focus:ring-2 focus:ring-blue-300`}
			aria-label="Help and information"
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
					d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
		</button>
		
		<!-- User Avatar dropdown -->
		<div class="relative" id="user-dropdown-container">
			<button
				class={`h-8 w-8 overflow-hidden rounded-full ${isDarkMode ? 'bg-gray-700' : 'bg-green-100'} flex items-center justify-center ring-2 ring-transparent hover:ring-blue-300 focus:outline-none focus:ring-blue-300 transition-all duration-200`}
				aria-label="User profile"
				aria-expanded={showUserDropdown}
				on:click={toggleUserDropdown}
			>
				<img src={profileImageUrl} alt="User" crossorigin="anonymous" class="h-full w-full object-cover" />
			</button>
			{#if showUserDropdown}
				<div
					class={`absolute right-0 mt-2 w-48 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-100'} rounded-lg shadow-lg transition-all duration-200 z-50 border`}
				>
					<div class={`p-3 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-100'}`}>
						<p class={`font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-800'}`}>
							{$user.name}
						</p>
						<p class={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
							{$user.email}
						</p>
					</div>
					<div class="py-1">
						<a
							href="/teacher/settings"
							class={`flex items-center px-4 py-2 text-sm ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'}`}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4 mr-2"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
								/>
							</svg>
							{$i18n.t('My Profile')}
						</a>
						<a
							href="/teacher/settings"
							class={`flex items-center px-4 py-2 text-sm ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'}`}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4 mr-2"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
								/>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
								/>
							</svg>
							{$i18n.t('Account Settings')}
						</a>
						<a
							href="/teacher/progress"
							class={`flex items-center px-4 py-2 text-sm ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'}`}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4 mr-2"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
								/>
							</svg>
							{$i18n.t('Learning Progress')}
						</a>
					</div>
					<div class={`py-1 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-100'}`}>
						<button
							on:click={toggleDemoMode}
							class={`flex w-full items-center justify-between px-4 py-2 text-sm ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'}`}
						>
							<div class="flex items-center">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-4 w-4 mr-2"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
									/>
								</svg>
								<span>{$i18n.t('Demo Mode')}</span>
							</div>
							<div class={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${$isDemo ? 'bg-blue-600' : isDarkMode ? 'bg-gray-600' : 'bg-gray-300'}`}>
								<span class={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${$isDemo ? 'translate-x-5' : 'translate-x-1'}`}></span>
							</div>
						</button>
					</div>
					<div class={`py-1 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-100'}`}>
						<button
							on:click={() => {
								localStorage.removeItem('token');
								location.href = '/auth';
							}}
							class={`flex w-full items-center px-4 py-2 text-sm ${isDarkMode ? 'text-red-400 hover:bg-gray-700' : 'text-red-600 hover:bg-gray-50'}`}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4 mr-2"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
								/>
		<!-- Language selector -->
		<div class="relative" id="language-dropdown-container">
			<button
				class={`btn-icon ${isDarkMode ? 'btn-icon-dark' : 'btn-icon-light'}`}
				on:click={toggleLanguageMenu}
				aria-label={$i18n.t('Change language')}
				title={$i18n.t('Change language')}
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 016-.371m0 0c1.12 0 2.233.038 3.334.114M9 5.25V3m3.334 2.364C11.176 10.658 7.69 15.08 3 17.502m9.334-12.138c.896.061 1.785.147 2.666.257m-4.589 8.495a18.023 18.023 0 01-3.827-5.802" />
				</svg>
			</button>

			{#if showLanguageMenu}
				<div class={`dropdown-panel dropdown-narrow ${isDarkMode ? 'dropdown-dark' : 'dropdown-light'}`}>
					<div class={`dropdown-header ${isDarkMode ? 'dropdown-divider-dark' : 'dropdown-divider-light'}`}>
						<p class={`dropdown-label ${isDarkMode ? 'subtext-dark' : 'subtext-light'}`}>
							{$i18n.t('Language')}
						</p>
					</div>
					<div class="py-1">
						<button
							on:click={() => changeLanguage('en-US')}
							class={`lang-btn ${currentLanguage === 'en-US' ? isDarkMode ? 'lang-active-dark' : 'lang-active-light' : isDarkMode ? 'lang-idle-dark' : 'lang-idle-light'}`}
						>
							{$i18n.t('English')}
						</button>
						<button
							on:click={() => changeLanguage('fr-FR')}
							class={`lang-btn ${currentLanguage === 'fr-FR' ? isDarkMode ? 'lang-active-dark' : 'lang-active-light' : isDarkMode ? 'lang-idle-dark' : 'lang-idle-light'}`}
						>
							{$i18n.t('Français')}
						</button>
						<button
							on:click={() => changeLanguage('ar-MA')}
							class={`lang-btn ${currentLanguage === 'ar-MA' ? isDarkMode ? 'lang-active-dark' : 'lang-active-light' : isDarkMode ? 'lang-idle-dark' : 'lang-idle-light'}`}
						>
							{$i18n.t('العربية')}
						</button>
					</div>
				</div>
			{/if}
		</div>

		<!-- Help -->
		<button
			class={`btn-icon ${isDarkMode ? 'btn-icon-dark' : 'btn-icon-light'}`}
			aria-label={$i18n.t('Help and information')}
		>
			<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
		</button>

		<!-- User avatar dropdown -->
		<div class="relative" id="user-dropdown-container">
			<button
				class={`avatar-btn ${isDarkMode ? 'avatar-dark' : 'avatar-light'}`}
				aria-label={$i18n.t('User profile')}
				aria-expanded={showUserDropdown}
				on:click={toggleUserDropdown}
			>
				<img src="/static/student-avatar.png" alt="User" class="avatar-img" />
			</button>

			{#if showUserDropdown}
				<div class={`dropdown-panel ${isDarkMode ? 'dropdown-dark' : 'dropdown-light'}`}>
					<div class={`dropdown-header ${isDarkMode ? 'dropdown-divider-dark' : 'dropdown-divider-light'}`}>
						<p class={`dropdown-title ${isDarkMode ? 'text-dark' : 'text-light'}`}>{$user.name}</p>
						<p class={`dropdown-email ${isDarkMode ? 'subtext-dark' : 'subtext-light'}`}>{$user.email}</p>
					</div>
					<div class="py-1">
						<a href="/teacher/settings" class={`dropdown-item ${isDarkMode ? 'dropdown-item-dark' : 'dropdown-item-light'}`}>
							<svg xmlns="http://www.w3.org/2000/svg" class="dropdown-item-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
							</svg>
							{$i18n.t('My Profile')}
						</a>
						<a href="/teacher/settings" class={`dropdown-item ${isDarkMode ? 'dropdown-item-dark' : 'dropdown-item-light'}`}>
							<svg xmlns="http://www.w3.org/2000/svg" class="dropdown-item-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
							{$i18n.t('Account Settings')}
						</a>
					</div>
					<div class={`dropdown-footer-section ${isDarkMode ? 'dropdown-divider-dark' : 'dropdown-divider-light'}`}>
						<button
							on:click={() => { localStorage.removeItem('token'); location.href = '/auth'; }}
							class={`dropdown-item ${isDarkMode ? 'danger-dark' : 'danger-light'}`}
						>
							<svg xmlns="http://www.w3.org/2000/svg" class="dropdown-item-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
							</svg>
							{$i18n.t('Sign Out')}
						</button>
					</div>
				</div>
			{/if}
		</div>
	</div>

	<!-- Mobile action buttons -->
	<div class="flex items-center gap-3 md:hidden">
		<!-- Notification icon for mobile -->
		<div class="relative">
			<button
				class={`p-2 ${isDarkMode ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' : 'text-gray-500 hover:text-gray-600 hover:bg-gray-100'} rounded-full`}
				on:click={toggleNotificationPanel}
				aria-label="Notifications"
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
	<!-- Mobile actions -->
	<div class="flex items-center gap-3 md:hidden">

		<!-- Notification mobile -->
		<div class="relative">
			<button
				class={`btn-icon ${isDarkMode ? 'btn-icon-dark' : 'btn-icon-light'}`}
				on:click={toggleNotificationPanel}
				aria-label={$i18n.t('Notifications')}
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
				</svg>
				{#if notificationCount > 0}
					<span class="badge-count">{notificationCount}</span>
				{/if}
			</button>
		</div>

		<!-- Dark mode toggle button for mobile -->
		<button
			class={`p-2 ${isDarkMode ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800' : 'text-gray-500 hover:text-gray-600 hover:bg-gray-100'} rounded-full`}
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
		<!-- Dark mode mobile -->
		<button
			class={`btn-icon ${isDarkMode ? 'btn-icon-dark' : 'btn-icon-light'}`}
			on:click={toggleDarkMode}
			aria-label={isDarkMode ? $i18n.t('Switch to light mode') : $i18n.t('Switch to dark mode')}
		>
			{#if isDarkMode}
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
				</svg>
			{:else}
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
				</svg>
			{/if}
		</button>

		<!-- User Avatar for mobile -->
		<div class="relative" bind:this={mobileMenuRef}>
			<button
				class={`h-8 w-8 overflow-hidden rounded-full ${isDarkMode ? 'bg-gray-700' : 'bg-green-100'} flex items-center justify-center border-2 border-transparent focus:border-blue-300`}
				on:click={toggleMobileMenu}
				aria-label="User menu"
			>
				<img src={profileImageUrl} alt="User" crossorigin="anonymous" class="h-full w-full object-cover" />
			</button>

			<!-- Mobile menu (dropdown style instead of slide-in) -->
			{#if showMobileMenu}
				<div
					class={`absolute right-0 mt-2 w-48 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-100'} rounded-lg shadow-lg z-[200] border`}
				>
					<div class={`p-3 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-100'}`}>
						<p class={`font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-800'}`}>
							{$user.name}
						</p>
						<p class={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
							{$user.email}
						</p>
					</div>
					<div class="py-1">
						<a
							href="/student/settings"
							class={`flex items-center px-4 py-2 text-sm ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'}`}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4 mr-2"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
								/>
							</svg>
							{$i18n.t('My Profile')}
						</a>
						<a
							href="/student/settings"
							class={`flex items-center px-4 py-2 text-sm ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'}`}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4 mr-2"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
								/>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
								/>
							</svg>
							{$i18n.t('Account Settings')}
						</a>
						<a
							href="#"
							class={`flex items-center px-4 py-2 text-sm ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'}`}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4 mr-2"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
		<!-- Avatar mobile -->
		<div class="relative" bind:this={mobileMenuRef}>
			<button
				class={`avatar-btn ${isDarkMode ? 'avatar-dark' : 'avatar-light'}`}
				on:click={toggleMobileMenu}
				aria-label={$i18n.t('User menu')}
			>
				<img src="/static/student-avatar.png" alt="User" class="avatar-img" />
			</button>

			{#if showMobileMenu}
				<div class={`dropdown-panel dropdown-mobile ${isDarkMode ? 'dropdown-dark' : 'dropdown-light'}`}>
					<div class={`dropdown-header ${isDarkMode ? 'dropdown-divider-dark' : 'dropdown-divider-light'}`}>
						<p class={`dropdown-title ${isDarkMode ? 'text-dark' : 'text-light'}`}>{$user.name}</p>
						<p class={`dropdown-email ${isDarkMode ? 'subtext-dark' : 'subtext-light'}`}>{$user.email}</p>
					</div>
					<div class="py-1">
						<a href="/student/settings" class={`dropdown-item ${isDarkMode ? 'dropdown-item-dark' : 'dropdown-item-light'}`}>
							<svg xmlns="http://www.w3.org/2000/svg" class="dropdown-item-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
							</svg>
							{$i18n.t('My Profile')}
						</a>
						<a href="/student/settings" class={`dropdown-item ${isDarkMode ? 'dropdown-item-dark' : 'dropdown-item-light'}`}>
							<svg xmlns="http://www.w3.org/2000/svg" class="dropdown-item-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
							{$i18n.t('Account Settings')}
						</a>
						<a href="#" class={`dropdown-item ${isDarkMode ? 'dropdown-item-dark' : 'dropdown-item-light'}`}>
							<svg xmlns="http://www.w3.org/2000/svg" class="dropdown-item-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							{$i18n.t('Help Center')}
						</a>
					</div>
					<div class={`py-1 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-100'}`}>
						<button
							on:click={toggleDemoMode}
							class={`flex w-full items-center justify-between px-4 py-2 text-sm ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-50'}`}
						>
							<div class="flex items-center">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-4 w-4 mr-2"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
									/>
								</svg>
								<span>{$i18n.t('Demo Mode')}</span>
							</div>
							<div class={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${$isDemo ? 'bg-blue-600' : isDarkMode ? 'bg-gray-600' : 'bg-gray-300'}`}>
								<span class={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${$isDemo ? 'translate-x-5' : 'translate-x-1'}`}></span>
							</div>
						</button>
					</div>
					<div class={`py-1 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-100'}`}>
						<button
							on:click={() => {
								localStorage.removeItem('token');
								location.href = '/auth';
							}}
							class={`flex w-full items-center px-4 py-2 text-sm ${isDarkMode ? 'text-red-400 hover:bg-gray-700' : 'text-red-600 hover:bg-gray-50'}`}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4 mr-2"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
								/>
					<div class={`dropdown-footer-section ${isDarkMode ? 'dropdown-divider-dark' : 'dropdown-divider-light'}`}>
						<button
							on:click={() => { localStorage.removeItem('token'); location.href = '/auth'; }}
							class={`dropdown-item ${isDarkMode ? 'danger-dark' : 'danger-light'}`}
						>
							<svg xmlns="http://www.w3.org/2000/svg" class="dropdown-item-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
							</svg>
							{$i18n.t('Sign Out')}
						</button>
					</div>
				</div>
			{/if}
		</div>
	</div>

	<!-- Mobile search drawer - REMOVED -->
</header>

<style>
	@keyframes slideDown {
		from {
			transform: translateY(-100%);
		}
		to {
			transform: translateY(0);
		}
	}

	.animate-slideDown {
		animation: slideDown 0.3s ease-out forwards;
	}
</header>

<style>
	/* ─── Animations ─────────────────────────────────────────── */
	@keyframes slideDown {
		from { transform: translateY(-100%); }
		to   { transform: translateY(0); }
	}
	.animate-slideDown {
		animation: slideDown 0.3s ease-out forwards;
	}

	@keyframes wave-animation {
		0%   { transform: rotate(0deg) }
		10%  { transform: rotate(14deg) }
		20%  { transform: rotate(-8deg) }
		30%  { transform: rotate(14deg) }
		40%  { transform: rotate(-4deg) }
		50%  { transform: rotate(10deg) }
		60%  { transform: rotate(0deg) }
		100% { transform: rotate(0deg) }
	}
	.animate-wave {
		display: inline-block;
		animation: wave-animation 2.5s infinite;
		transform-origin: 70% 70%;
	}

	/* ─── Header root ────────────────────────────────────────── */
	.navbar-root {
		box-shadow: 0 1px 2px rgba(0,0,0,.06);
		padding: 1rem;
		display: flex;
		align-items: center;
		justify-content: space-between;
		transition: background-color .2s ease, color .2s ease;
		z-index: 999;
	}
	.navbar-light { background-color: #ffffff; color: #1f2937; }
	.navbar-dark  { background-color: #111827; color: #f3f4f6; }

	/* ─── Title / subtitle ───────────────────────────────────── */
	.navbar-title    { font-size: 1.25rem; font-weight: 600; display: flex; align-items: center; gap: .5rem; }
	.navbar-subtitle { font-size: .875rem; }
	.text-light    { color: #1f2937; }
	.text-dark     { color: #f3f4f6; }
	.subtext-light { color: #6b7280; }
	.subtext-dark  { color: #9ca3af; }

	/* ─── Icon buttons ───────────────────────────────────────── */
	.btn-icon {
		padding: .5rem;
		border-radius: 9999px;
		position: relative;
		transition: background-color .15s, color .15s;
	}
	.btn-icon:focus { outline: none; box-shadow: 0 0 0 2px #93c5fd; }

	.btn-icon-light       { color: #6b7280; }
	.btn-icon-light:hover { color: #4b5563; background-color: #f9fafb; }
	.btn-icon-dark        { color: #9ca3af; }
	.btn-icon-dark:hover  { color: #e5e7eb; background-color: #1f2937; }

	.icon-light       { color: #6b7280; }
	.icon-light:hover { color: #374151; }
	.icon-dark        { color: #9ca3af; }
	.icon-dark:hover  { color: #e5e7eb; }

	.btn-mobile-toggle {
		margin-right: .75rem;
		border-radius: .375rem;
		padding: .25rem;
		transition: color .15s;
	}
	.btn-mobile-toggle:focus { outline: none; box-shadow: 0 0 0 2px #93c5fd; }

	/* ─── Badge ──────────────────────────────────────────────── */
	.badge-count {
		position: absolute;
		top: 0; right: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		height: 1rem; width: 1rem;
		border-radius: 9999px;
		background-color: #ef4444;
		font-size: .75rem;
		color: #fff;
	}

	/* ─── Search ─────────────────────────────────────────────── */
	.search-wrapper { position: relative; transition: width .3s; }
	.search-idle    { width: 10rem; }
	.search-focused { width: 16rem; }

	.search-inner {
		display: flex;
		align-items: center;
		border-radius: 9999px;
		padding: .5rem 1rem;
		border: 1px solid;
		box-shadow: 0 1px 2px rgba(0,0,0,.05);
	}
	.search-light { background-color: #f9fafb; border-color: #e5e7eb; }
	.search-dark  { background-color: #1f2937; border-color: #374151; }
	.search-ring  { box-shadow: 0 0 0 2px #93c5fd, 0 2px 6px rgba(0,0,0,.1); }

	.search-icon { height: 1rem; width: 1rem; color: #9ca3af; }

	.search-input {
		background: transparent;
		border: none;
		outline: none;
		padding: .25rem .5rem;
		width: 100%;
		font-size: .875rem;
	}
	.search-input-light { color: #374151; }
	.search-input-dark  { color: #f3f4f6; }
	.search-input::placeholder { color: #9ca3af; }

	.search-clear { transition: color .15s; }

	/* ─── Dropdowns ──────────────────────────────────────────── */
	.dropdown-panel {
		position: absolute;
		right: 0;
		margin-top: .5rem;
		width: 16rem;
		border-radius: .5rem;
		box-shadow: 0 4px 12px rgba(0,0,0,.12);
		z-index: 50;
		border: 1px solid;
	}
	.dropdown-narrow { width: 10rem; }
	.dropdown-mobile { z-index: 200; }

	.dropdown-light { background-color: #ffffff; border-color: #f3f4f6; }
	.dropdown-dark  { background-color: #1f2937; border-color: #374151; }

	.dropdown-header {
		padding: .75rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		border-bottom: 1px solid;
	}
	.dropdown-footer { padding: .5rem; border-top: 1px solid; }
	.dropdown-footer-section { border-top: 1px solid; padding: .25rem 0; }

	.dropdown-divider-light { border-color: #f3f4f6; }
	.dropdown-divider-dark  { border-color: #374151; }

	.dropdown-title { font-weight: 500; }
	.dropdown-email { font-size: .75rem; margin-top: .1rem; }
	.dropdown-label { font-size: .75rem; font-weight: 600; text-transform: uppercase; }

	/* ─── Dropdown items ─────────────────────────────────────── */
	.dropdown-item {
		display: flex;
		align-items: center;
		padding: .5rem 1rem;
		font-size: .875rem;
		width: 100%;
		text-align: left;
		transition: background-color .15s;
	}
	.dropdown-item-icon { height: 1rem; width: 1rem; margin-right: .5rem; flex-shrink: 0; }

	.dropdown-item-light       { color: #374151; }
	.dropdown-item-light:hover { background-color: #f9fafb; }
	.dropdown-item-dark        { color: #d1d5db; }
	.dropdown-item-dark:hover  { background-color: #374151; }

	.danger-light       { color: #dc2626; }
	.danger-light:hover { background-color: #f9fafb; }
	.danger-dark        { color: #f87171; }
	.danger-dark:hover  { background-color: #374151; }

	/* ─── Link buttons ───────────────────────────────────────── */
	.link-btn      { font-size: .75rem; transition: color .15s; }
	.link-btn-full { width: 100%; text-align: center; font-size: .875rem; transition: color .15s; }
	.link-light       { color: #3b82f6; }
	.link-light:hover { color: #1d4ed8; }
	.link-dark        { color: #60a5fa; }
	.link-dark:hover  { color: #93c5fd; }

	/* ─── Language buttons ───────────────────────────────────── */
	.lang-btn {
		width: 100%;
		text-align: left;
		padding: .5rem 1rem;
		font-size: .875rem;
		transition: background-color .15s, color .15s;
	}
	.lang-active-light { background-color: #eff6ff; color: #2563eb; }
	.lang-active-dark  { background-color: #374151; color: #60a5fa; }
	.lang-idle-light       { color: #374151; }
	.lang-idle-light:hover { background-color: #f9fafb; }
	.lang-idle-dark        { color: #d1d5db; }
	.lang-idle-dark:hover  { background-color: #374151; }

	/* ─── Avatar ─────────────────────────────────────────────── */
	.avatar-btn {
		height: 2rem; width: 2rem;
		border-radius: 9999px;
		overflow: hidden;
		display: flex;
		align-items: center;
		justify-content: center;
		border: 2px solid transparent;
		transition: border-color .2s;
	}
	.avatar-btn:hover { border-color: #93c5fd; }
	.avatar-btn:focus { outline: none; border-color: #93c5fd; }
	.avatar-light { background-color: #dcfce7; }
	.avatar-dark  { background-color: #374151; }
	.avatar-img   { height: 100%; width: 100%; object-fit: cover; }
</style>