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

	let editingMessageId: number | null = null;
	let editingContent = '';
	let activeMenuId: number | null = null;

	onMount(async () => {
		const currentCourseId = $page.params.id;
		if (currentCourseId) {
			activeChannelId = currentCourseId;
		}
		await fetchStudentRooms();
	});

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
			}
		} catch (error) {
			console.error('Error loading student channels', error);
		}
	}

	async function fetchDiscussions(roomId: string) {
		if (!roomId) return;
		try {
			isLoading = true;
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`http://localhost:8080/api/v1/discussions/rooms/${roomId}/messages`, {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				// ✅ FIXED: عطينا البيانات للمصفوفة باش تفركع ف الشاشة دابا
				currentMessages = await res.json();
				await scrollToBottom();
			}
		} catch (error) {
			console.error('Error fetching chat history', error);
		} finally {
			isLoading = false;
		}
	}

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
			}
		} catch (error) {
			console.error('Error sending message', error);
		}
	}

	function editMessage(msgId: number, oldContent: string) {
		editingMessageId = msgId;
		editingContent = oldContent;
	}

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

	$: filteredChannels = channels.filter((ch) =>
		ch.student_name.toLowerCase().includes(searchQuery.toLowerCase())
	);

	$: if (activeChannelId) {
		fetchDiscussions(activeChannelId);
		activeMenuId = null;
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
			class="flex-1 min-h-0 overflow-y-auto p-6 space-y-4 bg-slate-50/20 dark:bg-[#030712]"
		>
			{#if isLoading}
				<div class="text-center text-slate-400 text-sm py-10">
					{$i18n.t('Loading discussion...')}
				</div>
			{:else}
				{#each currentMessages as m}
					{@const isMyMessage =
						m.sender_id &&
						$user?.id &&
						String(m.sender_id).trim().toLowerCase() === String($user.id).trim().toLowerCase()}

					<div
						class="flex gap-3 items-start w-full p-1 rounded-2xl transition-all {isMyMessage
							? 'flex-row-reverse'
							: 'flex-row'}"
					>
						<div
							class="w-9 h-9 rounded-2xl text-white flex flex-shrink-0 items-center justify-center font-bold text-xs {isMyMessage
								? 'bg-gradient-to-br from-blue-500 to-indigo-600'
								: m.sender_role === 'teacher'
									? 'bg-indigo-600'
									: 'bg-emerald-600'}"
						>
							{m.sender_name ? m.sender_name.charAt(0).toUpperCase() : '?'}
						</div>

						<div
							class="flex flex-col max-w-[75%] min-w-0 space-y-1 {isMyMessage
								? 'items-end'
								: 'items-start'}"
						>
							<div class="flex items-center gap-2 flex-wrap flex-row">
								<span class="font-bold text-xs text-slate-700 dark:text-slate-300"
									>{isMyMessage ? $i18n.t('Moi') : m.sender_name}</span
								>
								<span class="text-[9px] text-slate-400 dark:text-slate-500 font-medium">
									{new Date(m.timestamp).toLocaleTimeString([], {
										hour: '2-digit',
										minute: '2-digit'
									})}
								</span>

								{#if isMyMessage}
									<div class="relative inline-block">
										<button
											on:click|stopPropagation={() =>
												(activeMenuId = activeMenuId === m.id ? null : m.id)}
											class="px-1 py-0.5 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-400 dark:text-slate-500 rounded-md font-extrabold text-[10px] outline-none"
											>•••</button
										>
										{#if activeMenuId === m.id}
											<div
												class="absolute right-0 mt-1 w-32 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-xl shadow-xl z-30 py-1 font-medium overflow-hidden"
											>
												<button
													on:click={() => {
														editMessage(m.id, m.content);
														activeMenuId = null;
													}}
													class="w-full text-left px-4 py-2 text-xs text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2 transition-colors"
													>Modifier</button
												>
												<button
													on:click={() => {
														deleteMessage(m.id);
														activeMenuId = null;
													}}
													class="w-full text-left px-4 py-2 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/20 flex items-center gap-2 transition-colors border-t border-slate-50 dark:border-slate-800/50"
													>Supprimer</button
												>
											</div>
										{/if}
									</div>
								{/if}
							</div>

							{#if editingMessageId === m.id}
								<div class="mt-1 flex flex-col gap-2 w-full min-w-[220px]">
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
									class="p-3 shadow-sm text-xs transition-colors break-words w-fit text-left min-w-[50px]
									{isMyMessage
										? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl rounded-tr-none'
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

		<footer class="p-4 bg-white dark:bg-[#030712] border-t border-slate-100 dark:border-slate-800">
			<div
				class="max-w-4xl mx-auto bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-2xl p-2 flex items-center gap-2 shadow-sm focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all"
			>
				<input
					type="text"
					bind:value={newMessage}
					placeholder={$i18n.t('Send a message...')}
					on:keydown={(e) => e.key === 'Enter' && sendMessage()}
					class="flex-1 p-2 bg-transparent border-none focus:ring-0 text-xs dark:text-slate-200 outline-none"
				/>
				<button
					on:click={sendMessage}
					class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-5 py-2 rounded-xl text-xs font-bold shadow-md shadow-indigo-500/10 active:scale-95 transition-all"
				>
					{$i18n.t('Send')}
				</button>
			</div>
		</footer>
	</main>
</div>

<style>
	::-webkit-scrollbar {
		width: 4px;
	}
	::-webkit-scrollbar-thumb {
		background: #cbd5e1;
		border-radius: 10px;
	}
	:global(.dark) ::-webkit-scrollbar-thumb {
		background: #334155;
	}
</style>
