<script lang="ts">
	import { getContext, tick, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { user } from '$lib/stores';
	import { page } from '$app/stores';

	const i18n = getContext<Writable<i18nType>>('i18n');

	let channels: any[] = [];
	let activeChannelId: string = '';
	let newMessage = '';
	let messagesContainer: HTMLElement;
	let currentMessages: any[] = [];
	let isLoading = false;
	let searchQuery = '';
	let showInviteModal = false;

	// ✅ DEFINING VARIABLES FOR EDIT & MENU WITH PROPER TYPES
	let editingMessageId: number | null = null;
	let editingContent = '';
	let activeMenuId: number | null = null; // Controls the 3 dots dropdown display

	onMount(async () => {
		const currentCourseId = $page.params.id;
		if (currentCourseId) {
			activeChannelId = currentCourseId;
		}
		await fetchStudentRooms();
	});

	// 📡 Fetch student enrolled courses from backend
	async function fetchStudentRooms() {
		try {
			const token = localStorage.getItem('token') ?? '';
			if (!token) return;

			const res = await fetch('http://localhost:8080/api/v1/discussions/student/courses', {
				headers: { Authorization: `Bearer ${token}` }
			});

			if (res.ok) {
				channels = await res.json();
				if (channels.length > 0 && !activeChannelId) {
					activeChannelId = channels[0].id;
				}
			} else {
				console.error('Backend returned an error:', res.status);
			}
		} catch (error) {
			console.error('Error loading student channels', error);
		}
	}

	// 📡 Fetch discussion messages for active room
	async function fetchDiscussions(roomId: string) {
		if (!roomId) return;
		try {
			isLoading = true;
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`http://localhost:8080/api/v1/discussions/rooms/${roomId}/messages`, {
				headers: { Authorization: `Bearer ${token}` }
			});
		} catch (error) {
			console.error('Error fetching chat history', error);
		} finally {
			isLoading = false;
		}
	}

	// 📩 Send message to current channel
	async function sendMessage() {
		if (!newMessage.trim() || !activeChannelId) return;

		const token = localStorage.getItem('token') ?? '';
		try {
			const res = await fetch(
				`http://localhost:8080/api/v1/discussions/rooms/${activeChannelId}/send`,
				{
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${token}`
					},
					body: JSON.stringify({ content: newMessage.trim() })
				}
			);

			if (res.ok) {
				newMessage = '';
				await fetchDiscussions(activeChannelId);
			} else {
				console.error('Failed to send message:', res.status);
			}
		} catch (error) {
			console.error('Error sending message', error);
		}
	}

	// ✅ DEFINED: Explicitly defined editMessage function
	function editMessage(msgId: number, oldContent: string) {
		editingMessageId = msgId;
		editingContent = oldContent;
	}

	// 📡 Save the edited message to database
	async function saveEdit(msgId: number) {
		if (!editingContent.trim()) return;
		const token = localStorage.getItem('token') ?? '';
		try {
			const res = await fetch(`http://localhost:8080/api/v1/discussions/messages/${msgId}`, {
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
			}
		} catch (error) {
			console.error('Error updating message', error);
		}
	}

	// 📡 Delete message from database
	async function deleteMessage(msgId: number) {
		if (!confirm('Voulez-vous vraiment supprimer ce message ?')) return;
		const token = localStorage.getItem('token') ?? '';
		try {
			const res = await fetch(`http://localhost:8080/api/v1/discussions/messages/${msgId}`, {
				method: 'DELETE',
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				await fetchDiscussions(activeChannelId);
			}
		} catch (error) {
			console.error('Error deleting message', error);
		}
	}

	function copyChannelLink() {
		const link = `https://opentutorai.com/join/${activeChannelId}`;
		navigator.clipboard.writeText(link);
		alert('Lien copié !');
	}

	// 🔍 Reactive channel filtering based on search input
	$: filteredChannels = channels.filter((ch) =>
		ch.student_name.toLowerCase().includes(searchQuery.toLowerCase())
	);

	$: if (activeChannelId) {
		fetchDiscussions(activeChannelId);
		activeMenuId = null; // Reset menu dropdown on channel change
	}

	$: activeChannel = channels.find((c) => c.id === activeChannelId) || {
		student_name: 'Discussion',
		members_count: 1
	};

	async function scrollToBottom() {
		await tick();
		if (messagesContainer) {
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}
	}
</script>

<div
	class="flex h-screen max-h-screen w-full bg-white dark:bg-[#030712] overflow-hidden font-sans transition-colors duration-500"
>
	<aside
		class="w-72 border-r border-slate-100 dark:border-slate-800 flex flex-col bg-slate-50/20 dark:bg-[#030712] shrink-0"
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
				on:click={() => goto('/student/settings')}
				class="w-full p-3 bg-white dark:bg-[#111827] border border-slate-100 dark:border-slate-800 rounded-2xl flex items-center gap-3 text-[11px] font-bold text-slate-600 dark:text-slate-300 hover:shadow-sm transition-all shadow-sm"
			>
				<span>⚙️</span>
				{$i18n.t('Preferences')}
			</button>
		</div>
	</aside>

	<main class="flex-1 flex flex-col h-full max-h-screen bg-white dark:bg-[#030712] overflow-hidden">
		<header
			class="h-16 px-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between sticky top-0 bg-white/90 dark:bg-[#030712]/90 backdrop-blur-md z-10"
		>
			<div class="flex items-center gap-3">
				<h3 class="text-base font-bold text-slate-800 dark:text-slate-100 tracking-tight">
					{activeChannel ? activeChannel.student_name : $i18n.t('Selection')}
				</h3>

				<span
					class="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 px-2.5 py-1 rounded-full font-bold flex items-center gap-1"
				>
					👥 {activeChannel?.members_count || 1}
					{activeChannel?.members_count > 1 ? 'Membres' : 'Membre'}
				</span>
			</div>
		</header>

		<div
			bind:this={messagesContainer}
			class="flex-1 min-h-0 overflow-y-auto p-6 space-y-8 bg-slate-50/20 dark:bg-[#030712]"
		>
			{#if isLoading}
				<div class="text-center text-slate-400 text-sm py-10">
					{$i18n.t('Loading discussion...')}
				</div>
			{:else}
				{#each currentMessages as m}
					<div
						class="flex gap-4 items-start hover:bg-slate-50/50 dark:hover:bg-slate-800/20 p-2 rounded-2xl transition-all"
					>
						<!-- Sender Avatar -->
						<div
							class="w-10 h-10 rounded-2xl {m.sender_role === 'teacher'
								? 'bg-indigo-600'
								: 'bg-emerald-600'} text-white flex flex-shrink-0 items-center justify-center font-bold shadow-sm"
						>
							{m.sender_name ? m.sender_name.charAt(0).toUpperCase() : '?'}
						</div>

						<!-- Message Content Container -->
						<div class="flex-1 space-y-1.5 min-w-0 relative">
							<div class="flex items-center justify-between">
								<!-- Header Info: Sender Name, Timestamp & 3-Dots Menu -->
								<div class="flex items-center gap-2 flex-wrap">
									<span class="font-bold text-sm text-slate-800 dark:text-slate-200"
										>{m.sender_name}</span
									>
									<span
										class="text-[10px] text-slate-400 dark:text-slate-500 font-medium bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md"
									>
										{new Date(m.timestamp).toLocaleDateString([], {
											day: '2-digit',
											month: '2-digit',
											year: 'numeric'
										})} • {new Date(m.timestamp).toLocaleTimeString([], {
											hour: '2-digit',
											minute: '2-digit'
										})}
									</span>

									<!-- ✅ FIXED: 3-Dots Menu is now placed right next to the timestamp and is ALWAYS visible (No hover needed) -->
									{#if m.sender_id && $user?.id && String(m.sender_id).trim() === String($user.id).trim()}
										<div class="relative inline-block">
											<button
												on:click|stopPropagation={() =>
													(activeMenuId = activeMenuId === m.id ? null : m.id)}
												class="px-1.5 py-0.5 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 rounded-md font-extrabold text-xs transition-colors outline-none"
												title="Options"
											>
												•••
											</button>

											{#if activeMenuId === m.id}
												<div
													class="absolute left-0 mt-1 w-32 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-xl shadow-xl z-30 py-1 font-medium overflow-hidden"
												>
													<button
														on:click={() => {
															editMessage(m.id, m.content);
															activeMenuId = null;
														}}
														class="w-full text-left px-4 py-2 text-xs text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2 transition-colors"
													>
														Modifier
													</button>
													<button
														on:click={() => {
															deleteMessage(m.id);
															activeMenuId = null;
														}}
														class="w-full text-left px-4 py-2 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/20 flex items-center gap-2 transition-colors border-t border-slate-50 dark:border-slate-800/50"
													>
														Supprimer
													</button>
												</div>
											{/if}
										</div>
									{/if}
								</div>
							</div>

							<!-- Editing Form / Text view -->
							{#if editingMessageId === m.id}
								<div class="mt-1 flex flex-col gap-2 w-full">
									<input
										type="text"
										bind:value={editingContent}
										class="w-full text-sm p-2.5 bg-white dark:bg-[#111827] border border-indigo-500 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500/20 dark:text-slate-200"
										on:keydown={(e) => e.key === 'Enter' && saveEdit(m.id)}
									/>
									<div class="flex gap-2 justify-end">
										<button
											on:click={() => (editingMessageId = null)}
											class="px-3 py-1 text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-lg font-medium"
											>Annuler</button
										>
										<button
											on:click={() => saveEdit(m.id)}
											class="px-3 py-1 text-xs bg-indigo-600 text-white rounded-lg font-medium shadow-sm shadow-indigo-500/10"
											>Enregistrer</button
										>
									</div>
								</div>
							{:else}
								<div
									class="bg-white dark:bg-[#111827] border border-slate-100 dark:border-slate-800 p-4 rounded-2xl rounded-tl-none shadow-sm text-sm text-slate-600 dark:text-slate-300 transition-colors max-w-[85%] inline-block break-words"
								>
									{m.content}
								</div>
							{/if}
						</div>
					</div>
				{/each}
			{/if}
		</div>

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
							sendMessage();
						}
					}}
					class="w-full p-4 bg-transparent border-none focus:ring-0 text-sm dark:text-slate-200 resize-none h-24 outline-none"
				></textarea>
				<div
					class="flex justify-between items-center pt-2 px-3 pb-2 border-t border-slate-50 dark:border-slate-800/50"
				>
					<button
						on:click={sendMessage}
						class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-7 py-2.5 rounded-full text-sm font-bold shadow-lg shadow-indigo-500/20 transition-all active:scale-95"
					>
						{$i18n.t('Send')}
					</button>
				</div>
			</div>
		</footer>
	</main>
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
