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

	// ✅ ADDED: Teacher Space Action Logic (Edit, Save, Delete, Kick)
	let editingMessageId: number | null = null;
	let editingContent = '';
	let activeMenuId: number | null = null;

	function editMessage(msgId: number, oldContent: string) {
		editingMessageId = msgId;
		editingContent = oldContent;
	}

	async function saveEdit(msgId: number) {
		if (!editingContent.trim()) return;
		const token = localStorage.token;
		try {
			const res = await fetch(`${TUTOR_API_BASE_URL}/discussions/messages/${msgId}`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`
				},
				body: JSON.stringify({ content: editingContent.trim() })
			});
			if (res.ok) {
				editingMessageId = null;
				await fetchDiscussions(activeChannelId);
				toast.success('Message modifié !');
			}
		} catch (error) {
			console.error('Error updating message', error);
		}
	}

	async function deleteMessage(msgId: number) {
		if (!confirm('Voulez-vous vraiment supprimer ce message ?')) return;
		const token = localStorage.token;
		try {
			const res = await fetch(`${TUTOR_API_BASE_URL}/discussions/messages/${msgId}`, {
				method: 'DELETE',
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				await fetchDiscussions(activeChannelId);
				toast.success('Message supprimé !');
			}
		} catch (error) {
			console.error('Error deleting message', error);
		}
	}

	async function kickStudent(studentId: string) {
		if (!confirm('Voulez-vous vraiment retirer cet étudiant de ce cours ?')) return;
		const token = localStorage.token;
		try {
			const res = await fetch(
				`${TUTOR_API_BASE_URL}/discussions/rooms/${activeChannelId}/students/${studentId}`,
				{
					method: 'DELETE',
					headers: { Authorization: `Bearer ${token}` }
				}
			);
			if (res.ok) {
				toast.success('Étudiant retiré du cours avec succès');
				await fetchRooms(); // Refresh code views
			}
		} catch (error) {
			console.error('Error removing student', error);
		}
	}

	// Fetch discussion messages when active channel changes
	$: if (activeChannelId) {
		fetchDiscussions(activeChannelId);
		activeMenuId = null;
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
						<p class="text-[10px] opacity-70 truncate">{ch.last_message || 'Pas de message...'}</p>
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

	<main class="flex-1 flex flex-col h-full max-h-screen bg-white dark:bg-[#030712] overflow-hidden">
		<!-- Main Chat Header with Embedded Members Badge -->
		<header
			class="h-16 px-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between sticky top-0 bg-white/90 dark:bg-[#030712]/90 backdrop-blur-md z-10"
		>
			<div class="flex items-center gap-3">
				<h3 class="text-base font-bold text-slate-800 dark:text-slate-100 tracking-tight">
					{activeChannel ? activeChannel.student_name : $i18n.t('Selection')}
				</h3>

				<!-- ✅ FIXED: Members count badge is now embedded right next to the course title -->
				<span
					class="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 px-2.5 py-1 rounded-full font-bold flex items-center gap-1"
				>
					👥 {activeChannel?.members_count || 1}
					{activeChannel?.members_count > 1 ? $i18n.t('Membres') : $i18n.t('Membre')}
				</span>
			</div>
		</header>

		<div class="flex-1 min-h-0 overflow-y-auto p-6 space-y-8 bg-slate-50/20 dark:bg-[#030712]">
			{#if isLoading}
				<div class="text-center text-slate-400 text-sm py-10">
					{$i18n.t('Loading discussion...')}
				</div>
			{:else}
				{#each currentMessages as m}
					{@const isTeacherMessage = m.sender_role === 'teacher'}

					<div
						class="flex gap-3 items-start w-full p-2 rounded-2xl transition-all {isTeacherMessage
							? 'flex-row-reverse'
							: 'flex-row'} hover:bg-slate-50/50 dark:hover:bg-slate-800/20"
					>
						<!-- Sender Avatar -->
						<div
							class="w-9 h-9 rounded-2xl text-white flex flex-shrink-0 items-center justify-center font-bold shadow-sm text-xs
            {isTeacherMessage ? 'bg-indigo-600' : 'bg-emerald-600'}"
						>
							{m.sender_name ? m.sender_name.charAt(0).toUpperCase() : '?'}
						</div>

						<!-- Message Body Container -->
						<div
							class="flex flex-col max-w-[75%] min-w-0 space-y-1 {isTeacherMessage
								? 'items-start'
								: 'items-end'}"
						>
							<!-- Header Info: Sender Name & Timestamp & 3-Dots -->
							<div
								class="flex items-center gap-2 flex-wrap {isTeacherMessage
									? 'flex-row'
									: 'flex-row-reverse'}"
							>
								<span class="font-bold text-xs text-slate-700 dark:text-slate-300">
									{m.sender_name}
									{#if m.sender_id && $user?.id && String(m.sender_id)
											.trim()
											.toLowerCase() === String($user.id).trim().toLowerCase()}
										<span class="text-[10px] text-indigo-500 font-normal">({$i18n.t('Moi')})</span>
									{/if}
								</span>
								<span class="text-[9px] text-slate-400 dark:text-slate-500 font-medium">
									{new Date(m.timestamp).toLocaleTimeString([], {
										hour: '2-digit',
										minute: '2-digit'
									})}
								</span>

								<!-- 3-Dots Action Menu for Teachers (Always visible next to header text) -->
								<div class="relative inline-block">
									<button
										on:click|stopPropagation={() =>
											(activeMenuId = activeMenuId === m.id ? null : m.id)}
										class="px-1 py-0.5 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-400 dark:text-slate-500 rounded-md font-extrabold text-[10px] outline-none"
									>
										•••
									</button>

									{#if activeMenuId === m.id}
										<div
											class="absolute {isTeacherMessage
												? 'right-0'
												: 'left-0'} mt-1 w-40 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-xl shadow-xl z-30 py-1 font-medium overflow-hidden"
										>
											<!-- ✏️ Modifier: Only if the message truly belongs to current logged user -->
											{#if m.sender_id && $user?.id && String(m.sender_id)
													.trim()
													.toLowerCase() === String($user.id).trim().toLowerCase()}
												<button
													on:click={() => {
														editMessage(m.id, m.content);
														activeMenuId = null;
													}}
													class="w-full text-left px-4 py-2 text-xs text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2 transition-colors"
												>
													Modifier
												</button>
											{/if}

											<!-- 🗑️ Supprimer: Allowed for teacher's own messages AND any student text -->
											<button
												on:click={() => {
													deleteMessage(m.id);
													activeMenuId = null;
												}}
												class="w-full text-left px-4 py-2 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/20 flex items-center gap-2 transition-colors border-t border-slate-50 dark:border-slate-800/50"
											>
												Supprimer
											</button>

											<!-- 🥾 Retirer du cours: Displays only on student messages -->
											{#if m.sender_role === 'student'}
												<button
													on:click={() => {
														kickStudent(m.sender_id);
														activeMenuId = null;
													}}
													class="w-full text-left px-4 py-2 text-xs text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-950/20 flex items-center gap-2 transition-colors border-t border-slate-50 dark:border-slate-800/50"
												>
													Retirer du cours
												</button>
											{/if}
										</div>
									{/if}
								</div>
							</div>

							<!-- Editing Form / Bubble Content -->
							{#if editingMessageId === m.id}
								<div class="mt-1 flex flex-col gap-2 w-full min-w-[250px]">
									<input
										type="text"
										bind:value={editingContent}
										class="w-full text-xs p-2 bg-white dark:bg-[#111827] border border-indigo-500 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500/20 dark:text-slate-200"
										on:keydown={(e) => e.key === 'Enter' && saveEdit(m.id)}
									/>
									<div class="flex gap-2 justify-end">
										<button
											on:click={() => (editingMessageId = null)}
											class="px-2.5 py-1 text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-lg font-medium"
											>Annuler</button
										>
										<button
											on:click={() => saveEdit(m.id)}
											class="px-2.5 py-1 text-[11px] bg-indigo-600 text-white rounded-lg font-medium shadow-sm"
											>Enregistrer</button
										>
									</div>
								</div>
							{:else}
								<div
									class="p-3 shadow-sm text-xs transition-colors break-words inline-block
                    {isTeacherMessage
										? 'bg-indigo-600 text-white rounded-2xl rounded-tr-none'
										: 'bg-white dark:bg-[#111827] border border-slate-100 dark:border-slate-800 text-slate-700 dark:text-slate-300 rounded-2xl rounded-tl-none'}"
								>
									{m.content}
								</div>
							{/if}
						</div>
					</div>
				{/each}
			{/if}
		</div>

		<!-- ── CHAT INPUT FOOTER (COMPACT & MODERN SLICK DESIGN) ── -->
		<footer
			class="p-4 bg-white dark:bg-[#030712] border-t border-slate-100 dark:border-slate-800 shrink-0"
		>
			<div
				class="max-w-4xl mx-auto flex items-center gap-2 bg-slate-50 dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-[22px] px-4 py-1.5 focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-500/50 transition-all"
			>
				<!-- Compact Textarea with dynamic auto-resize spirit -->
				<textarea
					bind:value={newMessage}
					placeholder={$i18n.t('Send a message...')}
					on:keydown={(e) => {
						if (e.key === 'Enter' && !e.shiftKey) {
							e.preventDefault();
							// If teacher page use handleSend(), if student use sendMessage()
							typeof handleSend === 'function' ? handleSend() : sendMessage();
						}
					}}
					class="flex-1 bg-transparent border-none focus:ring-0 text-sm dark:text-slate-200 resize-none h-9 py-2 outline-none min-h-[36px] max-h-[120px]"
				></textarea>

				<!-- Right Aligned Compact Send Button -->
				<button
					on:click={typeof handleSend === 'function' ? handleSend : sendMessage}
					class="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white h-9 px-5 rounded-xl text-xs font-bold shadow-md shadow-indigo-500/10 transition-all active:scale-95 shrink-0 flex items-center justify-center gap-1"
				>
					<span>{typeof handleSend === 'function' ? $i18n.t('Send') : $i18n.t('Send')}</span>
				</button>
			</div>
		</footer>
	</main>

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
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	/* ==========================================================================
       1. RESET, BASE STYLES & FONTS (CUSTOM EMBED)
       ========================================================================== */
	*,
	*::before,
	*::after {
		box-sizing: border-box;
	}

	.discussion-page {
		font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
		font-size: 14px;
	}

	::-webkit-scrollbar {
		width: 5px;
		height: 5px;
	}
	::-webkit-scrollbar-track {
		background: transparent;
	}
	:global(.dark) ::-webkit-scrollbar-track {
		background: #030712;
	}
	::-webkit-scrollbar-thumb {
		background: #cbd5e1;
		border-radius: 10px;
	}
	:global(.dark) ::-webkit-scrollbar-thumb {
		background: #1e293b;
	}
</style>
