<!-- Navbar.svelte -->
<script lang="ts">
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { user, isDemo, demoData, originalUserData } from '$lib/stores';
	import { generateDemoData } from '$lib/utils/mockData';
	import { toast } from 'svelte-sonner';
	import { generateInitialsImage } from '$lib/utils';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import i18next from 'i18next';

	// Contexts
	const i18n = getContext<Writable<i18nType>>('i18n');

	// Props
	export let role: string = 'teacher';
	export let username: string = '';
	export let toggleSidebar: () => void;
	export let isDarkMode: boolean = false;

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// State
	let searchQuery: string = '';
	let notificationCount: number = 2; // Demo count
	let isSearchFocused: boolean = false;
	let showNotifications: boolean = false;
	let showMobileMenu: boolean = false;
	let showUserDropdown: boolean = false;
	let showLanguageMenu: boolean = false;
	let currentLanguage: string = 'fr-FR';

	// Refs for click-outside
	let notificationRef: HTMLDivElement;
	let userDropdownRef: HTMLDivElement;
	let languageDropdownRef: HTMLDivElement;
	let mobileMenuRef: HTMLDivElement;

	// reactive assignment to update when store changes
	$: profileImageUrl = $user?.profile_image_url || generateInitialsImage($user?.name || 'User');

	// Functions
	function toggleUserDropdown() {
		showUserDropdown = !showUserDropdown;
		if (showUserDropdown) {
			showNotifications = false;
			showLanguageMenu = false;
			showMobileMenu = false;
		}
	}

	function toggleLanguageMenu() {
		showLanguageMenu = !showLanguageMenu;
		if (showLanguageMenu) {
			showNotifications = false;
			showUserDropdown = false;
			showMobileMenu = false;
		}
	}

	function changeLanguage(lang: string) {
		i18next.changeLanguage(lang);
		currentLanguage = lang;
		showLanguageMenu = false;
		localStorage.setItem('lang', lang);
	}

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
		if (showNotifications) {
			showUserDropdown = false;
			showLanguageMenu = false;
			showMobileMenu = false;
		}
	}

	function toggleMobileMenu() {
		showMobileMenu = !showMobileMenu;
		if (showMobileMenu) {
			showNotifications = false;
			showUserDropdown = false;
			showLanguageMenu = false;
		}
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
		showMobileMenu = false;
	}

	onMount(() => {
		currentLanguage = i18next.language || 'fr-FR';

		const handleClickOutside = (event: MouseEvent) => {
			const target = event.target as Node;
			if (notificationRef && !notificationRef.contains(target) && showNotifications) {
				showNotifications = false;
			}
			if (userDropdownRef && !userDropdownRef.contains(target) && showUserDropdown) {
				showUserDropdown = false;
			}
			if (languageDropdownRef && !languageDropdownRef.contains(target) && showLanguageMenu) {
				showLanguageMenu = false;
			}
			if (mobileMenuRef && !mobileMenuRef.contains(target) && showMobileMenu) {
				showMobileMenu = false;
			}
		};

		const handleLanguageChange = (lng: string) => {
			currentLanguage = lng;
		};

		if (browser) {
			document.addEventListener('click', handleClickOutside);
			i18next.on('languageChanged', handleLanguageChange);
		}

		return () => {
			if (browser) {
				document.removeEventListener('click', handleClickOutside);
				i18next.off('languageChanged', handleLanguageChange);
			}
		};
	});
</script>

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

		<div class="ml-2 md:ml-4">
			<h1 class={`navbar-title ${isDarkMode ? 'text-dark' : 'text-light'}`}>
				<span class="hidden sm:inline-flex items-center gap-2">
					{username ? $i18n.t('Hello Professor') + ' ' + username : $i18n.t('Hello Professor')}
					<span class="animate-wave" aria-hidden="true">👋</span>
				</span>
				<span class="sm:hidden text-lg">
					Open TutorAI
				</span>
			</h1>
			<p class={`navbar-subtitle ${isDarkMode ? 'subtext-dark' : 'subtext-light'} hidden sm:block`}>
				{$i18n.t("Here's what's happening in your classes today")}
			</p>
		</div>
	</div>

	<!-- Center/Right: Desktop nav -->
	<div class="hidden md:flex items-center gap-4 flex-1 justify-end">
		<!-- Search -->
		<div class={`search-wrapper ${isSearchFocused ? 'search-focused' : 'search-idle'}`}>
			<div class={`search-inner ${isDarkMode ? 'search-dark' : 'search-light'} ${isSearchFocused ? 'search-ring' : ''}`}>
				<svg xmlns="http://www.w3.org/2000/svg" class="search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<input
					type="text"
					placeholder={$i18n.t('Search')}
					class={`search-input ${isDarkMode ? 'search-input-dark' : 'search-input-light'}`}
					bind:value={searchQuery}
					on:keydown={handleSearch}
					on:focus={() => (isSearchFocused = true)}
					on:blur={() => (isSearchFocused = false)}
					aria-label={$i18n.t('Search')}
				/>
				{#if searchQuery}
					<button
						on:click={() => (searchQuery = '')}
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
					<div class="p-2 max-h-64 overflow-y-auto">
						<div class={`p-2 ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-50'} rounded-lg cursor-pointer transition-colors`}>
							<p class={`text-sm font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-800'}`}>
								{$i18n.t('New course available')}
							</p>
							<p class={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
								React Advanced Patterns
							</p>
							<p class={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-400'} mt-1`}>
								{$i18n.t('2 hours ago')}
							</p>
						</div>
					</div>
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

		<!-- Language selector -->
		<div class="relative" bind:this={languageDropdownRef}>
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
							class={`lang-btn ${currentLanguage === 'en-US' ? (isDarkMode ? 'lang-active-dark' : 'lang-active-light') : (isDarkMode ? 'lang-idle-dark' : 'lang-idle-light')}`}
						>
							{$i18n.t('English')}
						</button>
						<button
							on:click={() => changeLanguage('fr-FR')}
							class={`lang-btn ${currentLanguage === 'fr-FR' ? (isDarkMode ? 'lang-active-dark' : 'lang-active-light') : (isDarkMode ? 'lang-idle-dark' : 'lang-idle-light')}`}
						>
							{$i18n.t('Français')}
						</button>
						<button
							on:click={() => changeLanguage('ar-MA')}
							class={`lang-btn ${currentLanguage === 'ar-MA' ? (isDarkMode ? 'lang-active-dark' : 'lang-active-light') : (isDarkMode ? 'lang-idle-dark' : 'lang-idle-light')}`}
						>
							{$i18n.t('العربية')}
						</button>
					</div>
				</div>
			{/if}
		</div>

		<!-- User avatar dropdown -->
		<div class="relative" bind:this={userDropdownRef}>
			<button
				class={`avatar-btn ${isDarkMode ? 'avatar-dark' : 'avatar-light'}`}
				aria-label={$i18n.t('User profile')}
				aria-expanded={showUserDropdown}
				on:click={toggleUserDropdown}
			>
				<img src={profileImageUrl} alt="User" crossorigin="anonymous" class="avatar-img" />
			</button>

			{#if showUserDropdown}
				<div class={`dropdown-panel ${isDarkMode ? 'dropdown-dark' : 'dropdown-light'}`}>
					<div class={`dropdown-header ${isDarkMode ? 'dropdown-divider-dark' : 'dropdown-divider-light'}`}>
						<div>
							<p class={`dropdown-title ${isDarkMode ? 'text-dark' : 'text-light'}`}>{$user?.name}</p>
							<p class={`dropdown-email ${isDarkMode ? 'subtext-dark' : 'subtext-light'}`}>{$user?.email}</p>
						</div>
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
							on:click={toggleDemoMode}
							class={`dropdown-item ${isDarkMode ? 'dropdown-item-dark' : 'dropdown-item-light'} justify-between`}
						>
							<div class="flex items-center">
								<svg xmlns="http://www.w3.org/2000/svg" class="dropdown-item-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
								</svg>
								<span>{$i18n.t('Demo Mode')}</span>
							</div>
							<div class={`relative inline-flex h-4 w-8 items-center rounded-full transition-colors ${$isDemo ? 'bg-blue-600' : (isDarkMode ? 'bg-gray-600' : 'bg-gray-300')}`}>
								<span class={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${$isDemo ? 'translate-x-4' : 'translate-x-1'}`}></span>
							</div>
						</button>
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

	<!-- Mobile actions -->
	<div class="flex items-center gap-2 md:hidden">
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

		<!-- Avatar mobile -->
		<div class="relative" bind:this={mobileMenuRef}>
			<button
				class={`avatar-btn ${isDarkMode ? 'avatar-dark' : 'avatar-light'}`}
				on:click={toggleMobileMenu}
				aria-label={$i18n.t('User menu')}
			>
				<img src={profileImageUrl} alt="User" crossorigin="anonymous" class="avatar-img" />
			</button>

			{#if showMobileMenu}
				<div class={`dropdown-panel dropdown-mobile ${isDarkMode ? 'dropdown-dark' : 'dropdown-light'}`}>
					<div class={`dropdown-header ${isDarkMode ? 'dropdown-divider-dark' : 'dropdown-divider-light'}`}>
						<div>
							<p class={`dropdown-title ${isDarkMode ? 'text-dark' : 'text-light'}`}>{$user?.name}</p>
							<p class={`dropdown-email ${isDarkMode ? 'subtext-dark' : 'subtext-light'}`}>{$user?.email}</p>
						</div>
					</div>
					<div class="py-1">
						<a href="/teacher/settings" class={`dropdown-item ${isDarkMode ? 'dropdown-item-dark' : 'dropdown-item-light'}`}>
							<svg xmlns="http://www.w3.org/2000/svg" class="dropdown-item-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
							</svg>
							{$i18n.t('My Profile')}
						</a>
						<button
							on:click={toggleDarkMode}
							class={`dropdown-item ${isDarkMode ? 'dropdown-item-dark' : 'dropdown-item-light'}`}
						>
							{#if isDarkMode}
								<svg xmlns="http://www.w3.org/2000/svg" class="dropdown-item-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
								</svg>
								{$i18n.t('Light Mode')}
							{:else}
								<svg xmlns="http://www.w3.org/2000/svg" class="dropdown-item-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
								</svg>
								{$i18n.t('Dark Mode')}
							{/if}
						</button>
						<button
							on:click={toggleDemoMode}
							class={`dropdown-item ${isDarkMode ? 'dropdown-item-dark' : 'dropdown-item-light'}`}
						>
							<svg xmlns="http://www.w3.org/2000/svg" class="dropdown-item-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
							</svg>
							{$i18n.t('Demo Mode')}: {$isDemo ? $i18n.t('ON') : $i18n.t('OFF')}
						</button>
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
</header>

<style>
	/* ─── Animations ─────────────────────────────────────────── */
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
		padding: 0.75rem 1rem;
		display: flex;
		align-items: center;
		justify-content: space-between;
		transition: background-color .2s ease, color .2s ease;
		z-index: 999;
		height: 4.5rem;
	}
	.navbar-light { background-color: #ffffff; color: #1f2937; border-bottom: 1px solid #f3f4f6; }
	.navbar-dark  { background-color: #111827; color: #f3f4f6; border-bottom: 1px solid #1f2937; }

	/* ─── Title / subtitle ───────────────────────────────────── */
	.navbar-title    { font-size: 1.125rem; font-weight: 700; display: flex; align-items: center; gap: .5rem; }
	.navbar-subtitle { font-size: .8125rem; margin-top: -2px; }
	.text-light    { color: #1e293b; }
	.text-dark     { color: #f8fafc; }
	.subtext-light { color: #64748b; }
	.subtext-dark  { color: #94a3b8; }

	/* ─── Icon buttons ───────────────────────────────────────── */
	.btn-icon {
		padding: .5rem;
		border-radius: 9999px;
		position: relative;
		transition: all .2s;
	}
	.btn-icon:focus { outline: none; box-shadow: 0 0 0 2px #3b82f6; }

	.btn-icon-light       { color: #64748b; }
	.btn-icon-light:hover { color: #2563eb; background-color: #f1f5f9; }
	.btn-icon-dark        { color: #94a3b8; }
	.btn-icon-dark:hover  { color: #60a5fa; background-color: #1e293b; }

	.icon-light       { color: #64748b; }
	.icon-light:hover { color: #1e293b; }
	.icon-dark        { color: #94a3b8; }
	.icon-dark:hover  { color: #f1f5f9; }

	.btn-mobile-toggle {
		margin-right: .5rem;
		border-radius: .5rem;
		padding: .375rem;
		transition: all .2s;
	}

	/* ─── Badge ──────────────────────────────────────────────── */
	.badge-count {
		position: absolute;
		top: 2px; right: 2px;
		display: flex;
		align-items: center;
		justify-content: center;
		height: 1rem; width: 1rem;
		border-radius: 9999px;
		background-color: #ef4444;
		font-size: .625rem;
		font-weight: 700;
		color: #fff;
		border: 2px solid white;
	}
	.navbar-dark .badge-count { border-color: #111827; }

	/* ─── Search ─────────────────────────────────────────────── */
	.search-wrapper { position: relative; transition: all .3s cubic-bezier(0.4, 0, 0.2, 1); }
	.search-idle    { width: 12rem; }
	.search-focused { width: 18rem; }

	.search-inner {
		display: flex;
		align-items: center;
		border-radius: 9999px;
		padding: .5rem 1rem;
		border: 1px solid;
		transition: all .2s;
	}
	.search-light { background-color: #f8fafc; border-color: #e2e8f0; }
	.search-dark  { background-color: #1e293b; border-color: #334155; }
	.search-ring  { border-color: #3b82f6; box-shadow: 0 0 0 1px #3b82f6; }

	.search-icon { height: 1rem; width: 1rem; color: #94a3b8; }

	.search-input {
		background: transparent;
		border: none;
		outline: none !important;
		padding: .125rem .5rem;
		width: 100%;
		font-size: .875rem;
	}
	.search-input-light { color: #1e293b; }
	.search-input-dark  { color: #f8fafc; }
	.search-input::placeholder { color: #94a3b8; }

	.search-clear { margin-left: .25rem; }

	/* ─── Dropdowns ──────────────────────────────────────────── */
	.dropdown-panel {
		position: absolute;
		right: 0;
		margin-top: .75rem;
		width: 18rem;
		border-radius: 1rem;
		box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
		z-index: 100;
		border: 1px solid;
		overflow: hidden;
		animation: dropdown-fade-in 0.2s ease-out;
	}
	@keyframes dropdown-fade-in {
		from { opacity: 0; transform: translateY(-10px); }
		to { opacity: 1; transform: translateY(0); }
	}

	.dropdown-narrow { width: 12rem; }
	.dropdown-mobile { width: 16rem; top: 100%; right: 0; margin-top: 0.5rem; }

	.dropdown-light { background-color: #ffffff; border-color: #f1f5f9; }
	.dropdown-dark  { background-color: #1e293b; border-color: #334155; }

	.dropdown-header {
		padding: 1rem;
		border-bottom: 1px solid;
	}
	.dropdown-footer { padding: .75rem; border-top: 1px solid; }
	.dropdown-footer-section { border-top: 1px solid; padding: .25rem 0; }

	.dropdown-divider-light { border-color: #f1f5f9; }
	.dropdown-divider-dark  { border-color: #334155; }

	.dropdown-title { font-weight: 700; font-size: 0.875rem; }
	.dropdown-email { font-size: .75rem; color: #64748b; }
	.dropdown-label { font-size: .625rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; }

	/* ─── Dropdown items ─────────────────────────────────────── */
	.dropdown-item {
		display: flex;
		align-items: center;
		padding: .75rem 1rem;
		font-size: .875rem;
		font-weight: 500;
		width: 100%;
		text-align: left;
		transition: all .2s;
	}
	.dropdown-item-icon { height: 1.125rem; width: 1.125rem; margin-right: .75rem; flex-shrink: 0; }

	.dropdown-item-light       { color: #334155; }
	.dropdown-item-light:hover { background-color: #f8fafc; color: #2563eb; }
	.dropdown-item-dark        { color: #cbd5e1; }
	.dropdown-item-dark:hover  { background-color: #334155; color: #60a5fa; }

	.danger-light       { color: #ef4444; }
	.danger-light:hover { background-color: #fef2f2; color: #dc2626; }
	.danger-dark        { color: #f87171; }
	.danger-dark:hover  { background-color: #452727; color: #ef4444; }

	/* ─── Link buttons ───────────────────────────────────────── */
	.link-btn      { font-size: .75rem; font-weight: 600; transition: color .15s; }
	.link-btn-full { width: 100%; text-align: center; font-size: .8125rem; font-weight: 600; transition: color .15s; padding: .25rem; }
	.link-light       { color: #3b82f6; }
	.link-light:hover { color: #2563eb; }
	.link-dark        { color: #60a5fa; }
	.link-dark:hover  { color: #93c5fd; }

	/* ─── Language buttons ───────────────────────────────────── */
	.lang-btn {
		width: 100%;
		text-align: left;
		padding: .75rem 1rem;
		font-size: .875rem;
		font-weight: 500;
		transition: all .2s;
	}
	.lang-active-light { background-color: #eff6ff; color: #2563eb; font-weight: 700; }
	.lang-active-dark  { background-color: #334155; color: #60a5fa; font-weight: 700; }
	.lang-idle-light       { color: #334155; }
	.lang-idle-light:hover { background-color: #f8fafc; }
	.lang-idle-dark        { color: #cbd5e1; }
	.lang-idle-dark:hover  { background-color: #334155; }

	/* ─── Avatar ─────────────────────────────────────────────── */
	.avatar-btn {
		height: 2.25rem; width: 2.25rem;
		border-radius: 9999px;
		overflow: hidden;
		display: flex;
		align-items: center;
		justify-content: center;
		border: 2px solid transparent;
		transition: all .2s;
		box-shadow: 0 1px 2px rgba(0,0,0,0.05);
	}
	.avatar-btn:hover { border-color: #3b82f6; transform: scale(1.05); }
	.avatar-btn:focus { outline: none; border-color: #3b82f6; }
	.avatar-light { background-color: #f1f5f9; }
	.avatar-dark  { background-color: #1e293b; }
	.avatar-img   { height: 100%; width: 100%; object-fit: cover; }
</style>