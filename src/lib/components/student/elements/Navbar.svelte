<!-- Navbar.svelte -->
<script lang="ts">
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	const i18n = getContext('i18n');
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';

	// Props
	export let username: string = 'Karim';
	export let toggleSidebar: () => void;
	export let isDarkMode: boolean = false;

	// State
	let searchQuery: string = '';
	let notificationCount: number = 2;
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
				<span class="hidden sm:inline">{$i18n.t('Hello') + ' ' + username}</span>
			</h1>
			<p class={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'} hidden sm:block`}>
				{$i18n.t("Let's learn something new today!")}
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
							on:click={() => (notificationCount = 0)}
						>
							{$i18n.t('Mark all as read')}
						</button>
					</div>
					<div class="p-2 max-h-64 overflow-y-auto">
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
					</div>
					<div class={`p-2 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-100'}`}>
						<button
							class={`w-full text-center text-sm ${isDarkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-500 hover:text-blue-700'}`}
						>
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
				<img src="/static/student-avatar.png" alt="User" class="h-full w-full object-cover" />
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
									d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
								/>
							</svg>
							{$i18n.t('Learning Progress')}
						</a>
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
				<img src="/static/student-avatar.png" alt="User" class="h-full w-full object-cover" />
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
							</svg>
							{$i18n.t('Help Center')}
						</a>
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
</style>
