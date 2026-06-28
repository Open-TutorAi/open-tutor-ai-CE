<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { user } from '$lib/stores';

	export let activeSection: string = 'messages';
	export let role: 'teacher' | 'parent' = 'teacher';
	export let unreadCount: number = 0;

	const dispatch = createEventDispatcher<{ navigate: { section: string } }>();

	export let isSidebarOpen = true;

	const navigate = (section: string) => {
		dispatch('navigate', { section });
		if (window.innerWidth < 768) isSidebarOpen = false;
	};

	const logout = () => {
		localStorage.removeItem('token');
		location.href = '/auth';
	};

	type NavItem = { id: string; label: string; icon: 'home' | 'chat' | 'user' | 'academic' | 'megaphone' };

	const teacherNav: NavItem[] = [
		{ id: 'dashboard', label: 'Tableau de bord', icon: 'home' },
		{ id: 'messages', label: 'Messages', icon: 'chat' },
		{ id: 'announcements', label: 'Annonces', icon: 'megaphone' },
		{ id: 'profile', label: 'Profil', icon: 'user' }
	];

	const parentNav: NavItem[] = [
		{ id: 'dashboard', label: 'Tableau de bord', icon: 'home' },
		{ id: 'teachers', label: 'Enseignants', icon: 'academic' },
		{ id: 'messages', label: 'Messages', icon: 'chat' },
		{ id: 'announcements', label: 'Annonces', icon: 'megaphone' },
		{ id: 'profile', label: 'Profil', icon: 'user' }
	];

	$: navItems = role === 'teacher' ? teacherNav : parentNav;
	$: initials =
		$user?.name
			?.split(' ')
			.map((w: string) => w[0])
			.slice(0, 2)
			.join('')
			.toUpperCase() ?? '?';
</script>

<!-- Mobile overlay -->
{#if isSidebarOpen}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div
		class="fixed md:hidden z-40 top-0 right-0 left-0 bottom-0 bg-black/60 w-full min-h-screen h-screen flex justify-center overflow-hidden overscroll-contain"
		on:mousedown={() => (isSidebarOpen = false)}
	/>
{/if}

<!-- Sidebar -->
<div
	id="sidebar"
	class="h-screen max-h-[100dvh] min-h-screen select-none
		{isSidebarOpen ? 'md:relative w-[260px] max-w-[260px]' : '-translate-x-[260px] w-[0px]'}
		transition-width duration-200 ease-in-out shrink-0
		bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-200
		text-sm fixed z-50 top-0 left-0 overflow-x-hidden"
>
	<div
		class="py-2 my-auto flex flex-col justify-between h-screen max-h-[100dvh] w-[260px] overflow-x-hidden z-50
			{isSidebarOpen ? '' : 'invisible'}"
	>
		<!-- Top: toggle + logo -->
		<div>
			<div class="px-1.5 flex justify-between space-x-1 text-gray-600 dark:text-gray-400">
				<button
					class="cursor-pointer p-[7px] flex rounded-xl hover:bg-gray-100 dark:hover:bg-gray-900 transition"
					on:click={() => (isSidebarOpen = false)}
					aria-label="Fermer le menu"
				>
					<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="size-5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
					</svg>
				</button>

				<div class="flex items-center flex-1 px-2 py-1">
					<div class="self-center mx-1.5">
						<img src="/static/favicon.png" class="size-5 rounded-full" alt="logo" />
					</div>
					<div class="self-center font-medium text-sm text-gray-850 dark:text-white font-primary">
						OpenTutorAI
					</div>
				</div>
			</div>

			<!-- Nav items -->
			<div class="px-1.5 mt-3 flex flex-col space-y-0.5">
				{#each navItems as item (item.id)}
					{@const isActive = activeSection === item.id}
					<button
						class="grow flex items-center space-x-3 rounded-lg px-2 py-[7px] w-full text-left transition
							{isActive
								? 'bg-gray-200 dark:bg-gray-900 text-gray-900 dark:text-white'
								: 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-900'}"
						on:click={() => navigate(item.id)}
					>
						<span class="relative size-5 flex-shrink-0 flex items-center justify-center">
							{#if item.icon === 'home'}
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="size-5">
									<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
								</svg>
							{:else if item.icon === 'chat'}
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="size-5">
									<path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
								</svg>
							{:else if item.icon === 'user'}
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="size-5">
									<path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
								</svg>
							{:else if item.icon === 'academic'}
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="size-5">
									<path d="M12 14l9-5-9-5-9 5 9 5z" />
									<path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0112 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
								</svg>
							{:else if item.icon === 'megaphone'}
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="size-5">
									<path d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
								</svg>
							{/if}
							{#if item.icon === 'chat' && unreadCount > 0}
								<span class="absolute -top-0.5 -right-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-red-500 text-[8px] text-white font-bold leading-none">
									{unreadCount > 9 ? '9+' : unreadCount}
								</span>
							{/if}
						</span>
						<span class="text-sm font-medium truncate">{item.label}</span>
						{#if item.icon === 'chat' && unreadCount > 0}
							<span class="ml-auto flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-red-500 text-[10px] text-white font-bold px-1">
								{unreadCount > 9 ? '9+' : unreadCount}
							</span>
						{/if}
					</button>
				{/each}
			</div>
		</div>

		<!-- Bottom: user + logout -->
		<div class="px-1.5 pb-1">
			<div class="border-t border-gray-100 dark:border-gray-900 pt-2">
				<div class="flex items-center rounded-xl py-2 px-2 w-full hover:bg-gray-100 dark:hover:bg-gray-900 transition cursor-default">
					<div class="w-7 h-7 flex-shrink-0 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold mr-2.5">
						{initials}
					</div>
					<div class="min-w-0 flex-1">
						<p class="text-sm font-medium text-gray-800 dark:text-white truncate leading-none mb-0.5">
							{$user?.name ?? ''}
						</p>
						<p class="text-xs text-gray-400 dark:text-gray-500 truncate leading-none">
							{$user?.email ?? ''}
						</p>
					</div>
				</div>
				<button
					class="w-full flex items-center space-x-3 rounded-lg px-2 py-[7px] text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-900 transition mt-0.5"
					on:click={logout}
				>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="size-5 flex-shrink-0">
						<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
					</svg>
					<span class="font-medium">Déconnexion</span>
				</button>
			</div>
		</div>
	</div>
</div>

<!-- Mobile hamburger (only when sidebar closed) -->
{#if !isSidebarOpen}
	<button
		class="fixed top-3 left-3 z-40 cursor-pointer p-[7px] flex rounded-xl bg-gray-50 dark:bg-gray-950 hover:bg-gray-100 dark:hover:bg-gray-900 transition shadow-sm"
		on:click={() => (isSidebarOpen = true)}
		aria-label="Ouvrir le menu"
	>
		<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="size-5 text-gray-600 dark:text-gray-400">
			<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
		</svg>
	</button>
{/if}
