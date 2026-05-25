<script lang="ts">
    import { createEventDispatcher, onMount, getContext } from 'svelte';
    const i18n = getContext('i18n');
    import { user, theme } from '$lib/stores';
    import i18next from 'i18next';

    export let username: string = '';
    export let toggleSidebar: () => void;
    export let isDarkMode: boolean = false;

    let searchQuery: string = '';
    let notificationCount: number = 0;
    let isSearchFocused: boolean = false;
    let showNotifications: boolean = false;
    let showMobileMenu: boolean = false;
    let showLanguageMenu: boolean = false;
    let currentLanguage: string = 'fr-FR';
    let showUserDropdown: boolean = false;
    let currentTheme: 'light' | 'dark' | 'system' = 'system';
	$: userName = $user?.name || 'User';
	$: userEmail = $user?.email || '';
	$: displayName = $user?.name || username || 'Professor';
    
	let avatarRefreshKey = 0;
	let userAvatar = '/static/student-avatar.png';

	const isBrowser = typeof window !== 'undefined';

	$: userAvatar = `${normalizeAvatarPath(
	$user?.profile_image_url || (isBrowser ? localStorage.getItem('profile_avatar') : null)
	)}?t=${avatarRefreshKey}`;

	function normalizeAvatarPath(url?: string | null) {
	if (!url || url.trim() === '') return '/static/student-avatar.png';

	const clean = url.split('?')[0].trim();

	if (
		clean.startsWith('http://') ||
		clean.startsWith('https://') ||
		clean.startsWith('/static/') ||
		clean.startsWith('/uploads/') ||
		clean.startsWith('/api/')
	) {
		return clean;
	}

	if (clean.startsWith('/')) return clean;

	return `/uploads/avatars/${clean}`;
	}

    function toggleUserDropdown() { showUserDropdown = !showUserDropdown; }
    function toggleLanguageMenu() { showLanguageMenu = !showLanguageMenu; }
    function changeLanguage(lang: string) { i18next.changeLanguage(lang); currentLanguage = lang; showLanguageMenu = false; }
    const dispatch = createEventDispatcher();
    function toggleDarkMode() { isDarkMode = !isDarkMode; dispatch('darkModeToggle', { isDarkMode }); }
    function handleSearch(e: KeyboardEvent) { if (e.key === 'Enter') dispatch('search', { query: searchQuery }); }
    function toggleNotificationPanel() { showNotifications = !showNotifications; }
    function toggleMobileMenu() { showMobileMenu = !showMobileMenu; }

    let notificationRef: HTMLDivElement;
    let mobileMenuRef: HTMLDivElement;

    async function hydrateProfileFromServer() {
        try {
            const res = await fetch('/api/v1/settings/profile');
            if (!res.ok) return;
            const p = await res.json();
            const fullName = `${p.firstName || ''} ${p.lastName || ''}`.trim();
            const avatar = p.avatar || '/static/student-avatar.png';
            user.update(u => ({ ...u, name: fullName || u?.name, email: p.email || u?.email, profile_image_url: avatar, _avatar_ts: Date.now() }));
            localStorage.setItem('profile_avatar', avatar);
            avatarRefreshKey = Date.now();
        } catch (e) { console.error(e); }
    }

    onMount(() => {
        hydrateProfileFromServer();

        const handleClickOutside = (event: MouseEvent) => {
            if (notificationRef && !notificationRef.contains(event.target as Node) && showNotifications) showNotifications = false;
            if (mobileMenuRef && !mobileMenuRef.contains(event.target as Node) && showMobileMenu) showMobileMenu = false;
            const userDropdownRef = document.getElementById('user-dropdown-container');
            if (userDropdownRef && !userDropdownRef.contains(event.target as Node) && showUserDropdown) showUserDropdown = false;
            const langDropdownRef = document.getElementById('language-dropdown-container');
            if (langDropdownRef && !langDropdownRef.contains(event.target as Node) && showLanguageMenu) showLanguageMenu = false;
        };

        const handleAvatarUpdate = (event: CustomEvent) => {
            const newUrl = event.detail.url;
            user.update(u => ({ ...u, profile_image_url: newUrl, _avatar_ts: Date.now() }));
            avatarRefreshKey = Date.now();
            localStorage.setItem('profile_avatar', newUrl);
        };
        window.addEventListener('avatar-updated', handleAvatarUpdate as EventListener);

        currentLanguage = i18next.language || 'fr-FR';
        currentTheme = $theme || (localStorage.getItem('theme') as any) || 'system';
        const handleLanguageChange = (lng: string) => { currentLanguage = lng; };
        i18next.on('languageChanged', handleLanguageChange);
        const unsubscribeTheme = theme.subscribe((newTheme) => { if (newTheme) currentTheme = newTheme; });

        document.addEventListener('click', handleClickOutside);
        return () => {
            document.removeEventListener('click', handleClickOutside);
            i18next.off('languageChanged', handleLanguageChange);
            unsubscribeTheme();
            window.removeEventListener('avatar-updated', handleAvatarUpdate as EventListener);
        };
    });
</script>

<header class={`navbar-root ${isDarkMode ? 'navbar-dark' : 'navbar-light'}`}>

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
			<h1 class={`navbar-title ${isDarkMode ? 'text-dark' : 'text-light'}`}>
				<span class="hidden sm:inline inline-flex items-center gap-2">
					{displayName ? $i18n.t('Hello Professor') + ' ' + displayName : $i18n.t('Hello Professor')}
					<span class="animate-wave" aria-hidden="true">👋</span>
				</span>
			</h1>
			<p class={`navbar-subtitle ${isDarkMode ? 'subtext-dark' : 'subtext-light'} hidden sm:block`}>
				{$i18n.t("Here's what's happening in your classes today")}
			</p>
		</div>
	</div>

	<div class="hidden md:flex items-center gap-4">

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
					<div class={`dropdown-footer ${isDarkMode ? 'dropdown-divider-dark' : 'dropdown-divider-light'}`}>
						<button class={`link-btn-full ${isDarkMode ? 'link-dark' : 'link-light'}`}>
							{$i18n.t('View all notifications')}
						</button>
					</div>
				</div>
			{/if}
		</div>

		<button
			class={`btn-icon ${isDarkMode ? 'btn-icon-dark' : 'btn-icon-light'}`}
			on:click={toggleDarkMode}
			aria-label={isDarkMode ? $i18n.t('Switch to light mode') : $i18n.t('Switch to dark mode')}
			title={isDarkMode ? $i18n.t('Switch to light mode') : $i18n.t('Switch to dark mode')}
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

		<button
			class={`btn-icon ${isDarkMode ? 'btn-icon-dark' : 'btn-icon-light'}`}
			aria-label={$i18n.t('Help and information')}
		>
			<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
		</button>

		<div class="relative" id="user-dropdown-container">
			<button
				class={`avatar-btn ${isDarkMode ? 'avatar-dark' : 'avatar-light'}`}
				aria-label={$i18n.t('User profile')}
				aria-expanded={showUserDropdown}
				on:click={toggleUserDropdown}
			>
				<img src={userAvatar} alt="User" class="avatar-img" />
			</button>

			{#if showUserDropdown}
				<div class={`dropdown-panel ${isDarkMode ? 'dropdown-dark' : 'dropdown-light'}`}>
					<div class={`dropdown-header ${isDarkMode ? 'dropdown-divider-dark' : 'dropdown-divider-light'}`} style="flex-direction: column; align-items: flex-start; gap: 4px;">
						<p class={`dropdown-title ${isDarkMode ? 'text-dark' : 'text-light'}`}>{userName}</p>
						<p class={`dropdown-email ${isDarkMode ? 'subtext-dark' : 'subtext-light'}`}>{userEmail}</p>
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

	<div class="flex items-center gap-3 md:hidden">

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

		<button
			class={`btn-icon ${isDarkMode ? 'btn-icon-dark' : 'btn-icon-light'}`}
			on:click={toggleDarkMode}
			aria-label={isDarkMode ? $i18n.t('Switch to light mode') : $i18n.t('Switch to dark mode')}
			title={isDarkMode ? $i18n.t('Switch to light mode') : $i18n.t('Switch to dark mode')}
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

		<div class="relative" bind:this={mobileMenuRef}>
			<button
				class={`avatar-btn ${isDarkMode ? 'avatar-dark' : 'avatar-light'}`}
				on:click={toggleMobileMenu}
				aria-label={$i18n.t('User menu')}
			>
				<img src={userAvatar} alt="User" class="avatar-img" />
			</button>

			{#if showMobileMenu}
				<div class={`dropdown-panel dropdown-mobile ${isDarkMode ? 'dropdown-dark' : 'dropdown-light'}`}>
					<div class={`dropdown-header ${isDarkMode ? 'dropdown-divider-dark' : 'dropdown-divider-light'}`} style="flex-direction: column; align-items: flex-start; gap: 4px;">
						<p class={`dropdown-title ${isDarkMode ? 'text-dark' : 'text-light'}`}>{userName}</p>
						<p class={`dropdown-email ${isDarkMode ? 'subtext-dark' : 'subtext-light'}`}>{userEmail}</p>
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