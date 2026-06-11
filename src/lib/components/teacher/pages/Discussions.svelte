<script lang="ts">
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { user } from '$lib/stores';
	import { TUTOR_API_BASE_URL } from '$lib/constants';

	const i18n = getContext<Writable<i18nType>>('i18n');
	import { browser } from '$app/environment';

	// --- 1. Dark Mode Logic ---
	let isDarkMode = false;
	onMount(async () => {
		if (browser) {
			isDarkMode =
				localStorage.theme === 'dark' ||
				(!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
			applyTheme();

			// Parse query params for active course chat
			const params = new URLSearchParams(window.location.search);
			const courseId = params.get('courseId') || params.get('chatId');
			if (courseId) {
				activeChannelId = courseId;
			}
		}
		// Fetch course discussion rooms on mount
		await fetchRooms();
	});

	function applyTheme() {
		if (isDarkMode) {
			document.documentElement.classList.add('dark');
			localStorage.theme = 'dark';
		} else {
			document.documentElement.classList.remove('dark');
			localStorage.theme = 'light';
		}
	}

	// --- 2. Real Course Channels (Rooms) Data ---
	let channels: any[] = [];
	let activeChannelId = '';

	// Fetch teacher's courses from backend
	async function fetchRooms() {
		try {
			const token = localStorage.token;
			if (!token) return;

			const res = await fetch(`${TUTOR_API_BASE_URL}/discussions/courses`, {
				headers: {
					Authorization: `Bearer ${token}`
				}
			});
			if (res.ok) {
				channels = await res.json();
				if (channels.length > 0 && !activeChannelId) {
					activeChannelId = channels[0].id;
				}
			}
		} catch (error) {
			console.error('Error fetching course channels', error);
		}
	}

	// --- 3. Messages Logic (REAL DATA FROM BACKEND) ---
	let currentMessages: any[] = [];
	let isLoading = false;

	// Fetch message history for the active course room
	async function fetchDiscussions(roomId: string) {
		if (!roomId) return;
		try {
			isLoading = true;
			const token = localStorage.token;
			if (!token) return;

			const res = await fetch(`${TUTOR_API_BASE_URL}/discussions/rooms/${roomId}/messages`, {
				headers: {
					Authorization: `Bearer ${token}`
				}
			});
			if (res.ok) {
				currentMessages = await res.json();
			}
		} catch (error) {
			console.error('Backend offline or CORS error', error);
		} finally {
			isLoading = false;
		}
	}

	// Send message to the course channel
	const handleSend = async () => {
		if (!newMessage.trim() || !activeChannelId) return;

		const token = localStorage.token;
		if (!token) {
			toast.error('Authentication required!');
			return;
		}

		try {
			const res = await fetch(`${TUTOR_API_BASE_URL}/discussions/rooms/${activeChannelId}/send`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`
				},
				body: JSON.stringify({ content: newMessage })
			});
			if (res.ok) {
				newMessage = '';
				await fetchDiscussions(activeChannelId); // Refresh messages list
				toast.success('Message sent! 🚀');
			} else {
				const errorData = await res.json().catch(() => ({}));
				const errorMessage = errorData.detail || 'Error sending message';
				toast.error(`Error: ${errorMessage}`);
			}
		} catch (error) {
			toast.error('Backend offline!');
		}
	};

	// Fetch discussion messages when active channel changes
	$: if (activeChannelId) {
		fetchDiscussions(activeChannelId);
	}

	$: activeChannel = channels.find((ch) => ch.id === activeChannelId);

	// --- 4. State & Filtering ---
	let searchQuery = '';
	let newMessage = '';
	let showInviteModal = false;

	// Filter by course title (which is in student_name field)
	$: filteredChannels = channels.filter((ch) =>
		ch.student_name.toLowerCase().includes(searchQuery.toLowerCase())
	);

	const copyChannelLink = () => {
		const link = `https://opentutorai.com/join/${activeChannelId}`;
		navigator.clipboard.writeText(link).then(() => {
			toast.success($i18n.t('Link copied! 📋'));
			showInviteModal = false;
		});
	};
</script>

<div
	class="flex h-screen max-h-screen w-full bg-white dark:bg-[#030712] overflow-hidden font-sans transition-colors duration-500"
>
	<!-- Sidebar / Channels list -->
	<aside
		class="w-72 border-r border-slate-100 dark:border-slate-800 flex flex-col bg-slate-50/20 dark:bg-[#030712]"
	>
		<div class="p-4 bg-white dark:bg-[#030712] border-b border-slate-100 dark:border-slate-800">
			<div class="flex justify-between items-center mb-4">
				<h2 class="text-xl font-bold text-slate-800 dark:text-slate-100 tracking-tight">
					{$i18n.t('Discussions')}
				</h2>
				<button class="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-400"
					>📝</button
				>
			</div>
			<div class="relative">
				<span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs">🔍</span>
				<input
					type="text"
					bind:value={searchQuery}
					placeholder={$i18n.t('Search...')}
					class="w-full pl-9 pr-4 py-2 bg-slate-100 dark:bg-[#111827] dark:text-slate-200 border-none rounded-xl text-xs focus:ring-2 focus:ring-indigo-500/20 outline-none"
				/>
			</div>
		</div>

		<div class="flex-1 overflow-y-auto p-3 space-y-1">
			<p
				class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest px-3 py-2"
			>
				{$i18n.t('Course Channels')}
			</p>
			{#each filteredChannels as ch}
				<button
					on:click={() => (activeChannelId = ch.id)}
					class="w-full flex items-center gap-3 p-3 rounded-2xl transition-all
                    {activeChannelId === ch.id
						? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/10'
						: 'hover:bg-white dark:hover:bg-[#111827] text-slate-600 dark:text-slate-400'}"
				>
					<div
						class="w-10 h-10 rounded-xl {activeChannelId === ch.id
							? 'bg-white/20'
							: 'bg-indigo-500 dark:bg-slate-800'} text-white flex flex-shrink-0 items-center justify-center font-bold"
					>
						{ch.student_name.charAt(0).toUpperCase()}
					</div>
					<div class="flex-1 text-left min-w-0">
						<span class="font-bold text-sm truncate block dark:text-slate-100"
							>{ch.student_name}</span
						>
						<p class="text-[10px] opacity-70 truncate">{ch.last_message}</p>
					</div>
				</button>
			{/each}
		</div>

		<div class="p-3">
			<button
				on:click={() => goto('/teacher/settings')}
				class="w-full p-3 bg-white dark:bg-[#111827] border border-slate-100 dark:border-slate-800 rounded-2xl flex items-center gap-3 text-[11px] font-bold text-slate-600 dark:text-slate-300 hover:shadow-sm transition-all shadow-sm"
			>
				<span>⚙️</span>
				{$i18n.t('Preferences')}
			</button>
		</div>
	</aside>

	<!-- Main Chat Window -->
	<main class="flex-1 flex flex-col h-full max-h-screen bg-white dark:bg-[#030712] overflow-hidden">
		<header
			class="h-16 px-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between sticky top-0 bg-white/90 dark:bg-[#030712]/90 backdrop-blur-md z-10"
		>
			<div class="flex items-center gap-3">
				<div>
					<h3 class="text-base font-bold text-slate-800 dark:text-slate-100 tracking-tight">
						{activeChannel ? activeChannel.student_name : $i18n.t('Selection')}
					</h3>
				</div>
			</div>
		</header>

		<!-- Messages Area -->
		<div class="flex-1 min-h-0 overflow-y-auto p-6 space-y-8 bg-slate-50/20 dark:bg-[#030712]">
			{#if isLoading}
				<div class="text-center text-slate-400 text-sm py-10">
					{$i18n.t('Loading discussion...')}
				</div>
			{:else}
				{#each currentMessages as m}
					<div class="flex gap-4 group relative">
						<div
							class="w-10 h-10 rounded-2xl {m.sender_role === 'teacher'
								? 'bg-indigo-600'
								: 'bg-emerald-600'} text-white flex flex-shrink-0 items-center justify-center font-bold shadow-sm transition-transform group-hover:scale-105"
						>
							{m.sender_name.charAt(0).toUpperCase()}
						</div>
						<div class="flex-1 space-y-1.5">
							<div class="flex justify-between items-center">
								<span class="font-bold text-sm text-slate-800 dark:text-slate-200"
									>{m.sender_name}</span
								>
								<span class="text-[10px] text-slate-400 dark:text-slate-600">
									{new Date(m.timestamp).toLocaleTimeString([], {
										hour: '2-digit',
										minute: '2-digit'
									})}
								</span>
							</div>
							<div
								class="bg-white dark:bg-[#111827] border border-slate-100 dark:border-slate-800 p-4 rounded-2xl rounded-tl-none shadow-sm text-sm text-slate-600 dark:text-slate-300 transition-colors"
							>
								{m.content}
							</div>
						</div>
					</div>
				{/each}
			{/if}
		</div>

		<!-- Chat Input Footer -->
		<footer class="p-6 bg-white dark:bg-[#030712] border-t border-slate-100 dark:border-slate-800">
			<div
				class="max-w-4xl mx-auto bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-[28px] p-2 shadow-sm focus-within:ring-4 focus-within:ring-indigo-500/5 transition-all"
			>
				<textarea
					bind:value={newMessage}
					placeholder={$i18n.t('Send a message...')}
					on:keydown={(e) => {
						if (e.key === 'Enter' && !e.shiftKey) {
							e.preventDefault();
							handleSend();
						}
					}}
					class="w-full p-4 bg-transparent border-none focus:ring-0 text-sm dark:text-slate-200 resize-none h-24 outline-none"
				></textarea>
				<div
					class="flex justify-between items-center pt-2 px-3 pb-2 border-t border-slate-50 dark:border-slate-800/50"
				>
					<button
						on:click={handleSend}
						class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-7 py-2.5 rounded-full text-sm font-bold shadow-lg shadow-indigo-500/20 transition-all active:scale-95"
					>
						{$i18n.t('Send 🚀')}
					</button>
				</div>
			</div>
		</footer>
	</main>

	<!-- Sidebar Members right side -->
	<aside
		class="w-64 border-l border-slate-100 dark:border-slate-800 p-6 hidden xl:flex flex-col bg-white dark:bg-[#030712]"
	>
		<div class="flex justify-between items-center mb-8">
			<h4 class="font-bold text-xs text-slate-800 dark:text-slate-100 uppercase tracking-tight">
				{$i18n.t('Members')}
			</h4>
			<span
				class="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-500 px-2 py-0.5 rounded-full font-bold"
			>
				{activeChannel?.members_count || 1}
			</span>
		</div>

		<div class="flex-1 space-y-6 overflow-y-auto">
			<div>
				<p
					class="text-[10px] font-bold text-slate-400 dark:text-slate-600 uppercase tracking-widest mb-4"
				>
					{$i18n.t('Teachers')}
				</p>
				<div class="flex items-center gap-3 group cursor-pointer">
					<div class="relative">
						<div
							class="w-8 h-8 rounded-xl bg-green-500 text-white flex items-center justify-center font-bold text-xs"
						>
							{$user?.name ? $user.name.charAt(0).toUpperCase() : 'P'}
						</div>
						<div
							class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 border-2 border-white dark:border-[#030712] rounded-full"
						></div>
					</div>
					<span
						class="text-sm font-semibold text-slate-700 dark:text-slate-300 group-hover:text-indigo-500 transition-colors"
					>
						{$user?.name || 'Professeur'}
					</span>
				</div>
			</div>

			<button
				on:click={() => (showInviteModal = true)}
				class="mt-4 w-full py-3 bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 rounded-full text-[11px] font-bold text-slate-500 dark:text-slate-400 hover:bg-indigo-600 hover:text-white transition-all shadow-sm"
			>
				{$i18n.t('👥 Invite members')}
			</button>
		</div>
	</aside>

	<!-- Invite Modal -->
	{#if showInviteModal}
		<div
			class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm transition-all"
		>
			<div
				class="bg-white dark:bg-[#111827] w-full max-w-md rounded-[32px] p-8 shadow-2xl relative border border-slate-100 dark:border-slate-800 transition-colors"
			>
				<h2 class="text-xl font-bold text-slate-800 dark:text-slate-100 text-center mb-2">
					{$i18n.t('Invite members')}
				</h2>
				<p class="text-xs text-slate-400 dark:text-slate-500 text-center mb-8">
					{$i18n.t('Share this link with your students.')}
				</p>

				<div class="space-y-6">
					<div
						class="flex items-center gap-2 p-3 bg-slate-50 dark:bg-[#030712] border border-slate-100 dark:border-slate-800 rounded-2xl"
					>
						<input
							type="text"
							readonly
							value="https://opentutorai.com/join/{activeChannelId}"
							class="flex-1 bg-transparent border-none text-xs text-slate-500 outline-none truncate"
						/>
						<button
							on:click={copyChannelLink}
							class="bg-indigo-600 text-white px-4 py-2 rounded-xl text-[10px] font-bold transition-all"
							>{$i18n.t('Copy')}</button
						>
					</div>

					<button
						on:click={copyChannelLink}
						class="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-full font-bold text-sm shadow-lg shadow-indigo-500/20 transition-all hover:scale-[1.02] active:scale-95"
					>
						{$i18n.t('Copy link 🔗')}
					</button>
					<button
						on:click={() => (showInviteModal = false)}
						class="w-full text-xs text-slate-400 hover:text-slate-600 transition-colors text-center"
						>{$i18n.t('Close')}</button
					>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	:global(.dark) ::-webkit-scrollbar {
		width: 5px;
	}
	:global(.dark) ::-webkit-scrollbar-track {
		background: #030712;
	}
	:global(.dark) ::-webkit-scrollbar-thumb {
		background: #1e293b;
		border-radius: 10px;
	}
</style>
