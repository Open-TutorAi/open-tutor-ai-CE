<script lang="ts">
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { onMount, getContext, tick } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { user } from '$lib/stores';
	import { TUTOR_API_BASE_URL } from '$lib/constants';

	const i18n = getContext<Writable<i18nType>>('i18n');

	onMount(async () => {
		const params = new URLSearchParams(window.location.search);
		const courseId = params.get('courseId') || params.get('chatId');
		if (courseId) activeChannelId = courseId;
		await fetchRooms();
	});

	// --- 2. Channels ---
	let channels: any[] = [];
	let activeChannelId = '';

	async function fetchRooms() {
		try {
			const token = localStorage.token;
			if (!token) return;
			const res = await fetch(`${TUTOR_API_BASE_URL}/discussions/courses`, {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				channels = await res.json();
				if (channels.length > 0 && !activeChannelId) activeChannelId = channels[0].id;
			}
		} catch (error) {
			console.error('Error fetching course channels', error);
		}
	}

	// --- 3. Messages ---
	let currentMessages: any[] = [];
	let isLoading = false;
	let messagesContainer: HTMLElement;

	async function scrollToBottom() {
		await tick();
		if (messagesContainer) messagesContainer.scrollTop = messagesContainer.scrollHeight;
	}

	async function fetchDiscussions(roomId: string) {
		if (!roomId) return;
		try {
			isLoading = true;
			const token = localStorage.token;
			if (!token) return;
			const res = await fetch(`${TUTOR_API_BASE_URL}/discussions/rooms/${roomId}/messages`, {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				currentMessages = await res.json();
				await scrollToBottom();
			}
		} catch (error) {
			console.error('Backend offline or CORS error', error);
		} finally {
			isLoading = false;
		}
	}

	// --- 4. Send ---
	const handleSend = async () => {
		if (!newMessage.trim() || !activeChannelId) return;
		const token = localStorage.token;
		if (!token) { toast.error('Authentication required!'); return; }
		try {
			const res = await fetch(`${TUTOR_API_BASE_URL}/discussions/rooms/${activeChannelId}/send`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
				body: JSON.stringify({ content: newMessage })
			});
			if (res.ok) {
				newMessage = '';
				await fetchDiscussions(activeChannelId);
			} else {
				const errorData = await res.json().catch(() => ({}));
				toast.error(`Error: ${errorData.detail || 'Error sending message'}`);
			}
		} catch {
			toast.error('Backend offline!');
		}
	};

	// --- 5. Edit / Delete / Kick ---
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
				headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
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
				{ method: 'DELETE', headers: { Authorization: `Bearer ${token}` } }
			);
			if (res.ok) {
				toast.success('Étudiant retiré du cours avec succès');
				await fetchRooms();
			}
		} catch (error) {
			console.error('Error removing student', error);
		}
	}

	// --- 6. Emoji picker ---
	let showEmojiPicker = false;
	const EMOJIS = [
		'😀','😂','😍','🥰','😎','😭','😅','🤔','😊','😉',
		'👍','👎','❤️','🔥','✅','🎉','🙏','💪','👏','🤝',
		'😢','😡','🥳','😴','🤣','😜','🤩','😏','😬','🫡',
		'📚','💡','✏️','📝','🖊️','📖','🎓','🏆','⭐','💯',
		'👋','🤗','💬','💭','📣','🔔','✨','🌟','💫','🎯'
	];

	let textareaEl: HTMLTextAreaElement;

	function wrapSelection(marker: string) {
		if (!textareaEl) return;
		const start = textareaEl.selectionStart;
		const end = textareaEl.selectionEnd;
		const selected = newMessage.slice(start, end);
		const before = newMessage.slice(0, start);
		const after = newMessage.slice(end);
		if (selected) {
			newMessage = `${before}${marker}${selected}${marker}${after}`;
			tick().then(() => {
				textareaEl.selectionStart = start + marker.length;
				textareaEl.selectionEnd = end + marker.length;
				textareaEl.focus();
			});
		} else {
			newMessage = `${before}${marker}${marker}${after}`;
			tick().then(() => {
				textareaEl.selectionStart = start + marker.length;
				textareaEl.selectionEnd = start + marker.length;
				textareaEl.focus();
			});
		}
	}

	function insertEmoji(emoji: string) {
		if (!textareaEl) return;
		const pos = textareaEl.selectionStart;
		newMessage = newMessage.slice(0, pos) + emoji + newMessage.slice(pos);
		showEmojiPicker = false;
		tick().then(() => {
			textareaEl.selectionStart = pos + emoji.length;
			textareaEl.selectionEnd = pos + emoji.length;
			textareaEl.focus();
		});
	}

	// --- 7. Render bold/italic markdown ---
	function renderContent(text: string): string {
		if (!text) return '';
		return text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
			.replace(/\*(.+?)\*/g, '<em>$1</em>');
	}

	// --- 8. Reactive ---
	$: if (activeChannelId) { fetchDiscussions(activeChannelId); activeMenuId = null; }
	$: activeChannel = channels.find((ch) => ch.id === activeChannelId);

	let searchQuery = '';
	let newMessage = '';
	let showInviteModal = false;
	let showSidebar = false;

	function formatMsgDate(ts: string): string {
		const d = new Date(ts);
		const today = new Date();
		const yest = new Date(today);
		yest.setDate(yest.getDate() - 1);
		if (d.toDateString() === today.toDateString()) return "Aujourd'hui";
		if (d.toDateString() === yest.toDateString()) return 'Hier';
		return d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
	}
	function sameMsgDay(ts1: string, ts2: string): boolean {
		return new Date(ts1).toDateString() === new Date(ts2).toDateString();
	}

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
	class="msg-page flex h-full w-full bg-white dark:bg-[#030712] overflow-hidden transition-colors duration-500"
	on:click={() => { showEmojiPicker = false; activeMenuId = null; showSidebar = false; }}
>
	<!-- Mobile overlay -->
	{#if showSidebar}
		<div class="fixed inset-0 bg-black/60 z-30 md:hidden" on:click|stopPropagation={() => showSidebar = false}></div>
	{/if}

	<!-- SIDEBAR -->
	<aside class="{showSidebar ? 'flex' : 'hidden'} md:flex fixed md:relative left-0 top-0 h-full z-40 md:z-auto w-72 flex-col border-r border-slate-100 dark:border-slate-800 bg-white dark:bg-[#030712] shrink-0" on:click|stopPropagation>

		<!-- Sidebar hero header -->
		<div class="msg-sidebar-hero">
			<div class="msg-sidebar-hero-inner">
				<div class="msg-sidebar-hero-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="20" height="20">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
					</svg>
				</div>
				<div style="flex:1;min-width:0">
					<h2 class="msg-sidebar-hero-title">{$i18n.t('Discussions')}</h2>
					<p class="msg-sidebar-hero-sub">{channels.length} {$i18n.t('cours')}</p>
				</div>
				<button class="md:hidden msg-sidebar-close" on:click={() => showSidebar = false} aria-label="Close">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/>
					</svg>
				</button>
			</div>
			<!-- Search -->
			<div class="msg-sidebar-search-wrap">
				<svg class="msg-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
				</svg>
				<input
					type="text"
					bind:value={searchQuery}
					placeholder={$i18n.t('Search...')}
					class="msg-sidebar-search"
				/>
			</div>
		</div>

		<div class="flex-1 overflow-y-auto p-3 space-y-1">
			<p class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest px-3 py-2">
				{$i18n.t('Course Channels')}
			</p>
			{#each filteredChannels as ch}
				<button
					on:click={() => { activeChannelId = ch.id; showSidebar = false; }}
					class="w-full flex items-center gap-3 p-3 rounded-lg transition-all
                    {activeChannelId === ch.id
						? 'bg-blue-700 text-white shadow-lg shadow-blue-700/10'
						: 'hover:bg-white dark:hover:bg-[#111827] text-slate-600 dark:text-slate-400'}"
				>
					<div class="w-10 h-10 rounded-lg {activeChannelId === ch.id ? 'bg-white/20' : 'bg-blue-700 dark:bg-slate-800'} text-white flex flex-shrink-0 items-center justify-center font-bold text-sm">
						{ch.student_name?.charAt(0).toUpperCase() ?? '?'}
					</div>
					<div class="flex-1 text-left min-w-0">
						<span class="font-bold text-sm truncate block dark:text-slate-100">{ch.student_name}</span>
						<p class="text-[10px] opacity-70 truncate">{ch.last_message || $i18n.t('Pas de message...')}</p>
					</div>
				</button>
			{/each}

			{#if filteredChannels.length === 0}
				<div class="text-center py-8 text-slate-400 text-xs">
					{$i18n.t('Aucun cours trouvé')}
				</div>
			{/if}
		</div>

		<div class="p-3">
			<button
				on:click={() => goto('/teacher/settings')}
				class="w-full p-3 bg-white dark:bg-[#111827] border border-slate-100 dark:border-slate-800 rounded-lg flex items-center gap-3 text-[11px] font-bold text-slate-600 dark:text-slate-300 hover:shadow-sm transition-all shadow-sm"
			>
				<span>⚙️</span>
				{$i18n.t('Preferences')}
			</button>
		</div>
	</aside>

	<!-- MAIN CHAT -->
	<main class="flex-1 flex flex-col min-h-0 bg-white dark:bg-[#030712] overflow-hidden">
		<!-- Header -->
		<header class="msg-chat-header">
			<div class="flex items-center gap-2 md:gap-3 min-w-0">
				<!-- Hamburger (mobile only) -->
				<button
					class="md:hidden p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl text-slate-600 dark:text-slate-400 flex-shrink-0"
					on:click|stopPropagation={() => showSidebar = true}
					aria-label="Open sidebar"
				>
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
						<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
					</svg>
				</button>
				<div class="relative flex-shrink-0">
					<div class="msg-chat-header-avatar">
						{(activeChannel?.student_name ?? 'D').charAt(0).toUpperCase()}
					</div>
					<div class="msg-online-dot"></div>
				</div>
				<div class="min-w-0">
					<h3 class="msg-chat-header-title truncate">
						{activeChannel ? activeChannel.student_name : $i18n.t('Selection')}
					</h3>
					<p class="msg-chat-header-sub">
						👥 {activeChannel?.members_count || 1}
						{(activeChannel?.members_count || 1) > 1 ? $i18n.t('Membres') : $i18n.t('Membre')}
					</p>
				</div>
			</div>
		</header>

		<!-- Messages -->
		<div
			bind:this={messagesContainer}
			class="msg-area flex-1 min-h-0 overflow-y-auto"
		>
			{#if isLoading}
				<div class="flex flex-col gap-4 animate-pulse p-6">
					{#each [1,2,3] as _}
						<div class="flex gap-4 items-start">
							<div class="w-10 h-10 rounded-2xl bg-slate-200 dark:bg-slate-700 flex-shrink-0"></div>
							<div class="flex-1 space-y-2">
								<div class="h-3 bg-slate-200 dark:bg-slate-700 rounded w-32"></div>
								<div class="h-12 bg-slate-200 dark:bg-slate-700 rounded-2xl w-3/4"></div>
							</div>
						</div>
					{/each}
				</div>
			{:else if currentMessages.length === 0}
				<div class="flex flex-col items-center justify-center h-full gap-5">
					<div class="msg-empty-icon">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="32" height="32">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
						</svg>
					</div>
					<p class="text-sm font-semibold text-slate-400">{$i18n.t('Aucun message. Soyez le premier à écrire !')}</p>
				</div>
			{:else}
				{#each currentMessages as m, i}
					{#if i === 0 || !sameMsgDay(m.timestamp, currentMessages[i - 1].timestamp)}
						<div class="msg-date-pill">
							<span class="msg-date-pill-text">{formatMsgDate(m.timestamp)}</span>
						</div>
					{/if}
					{@const isTeacherMessage = m.sender_role === 'teacher'}
					<div class="msg-row {isTeacherMessage ? 'msg-row-own' : 'msg-row-other'} group" on:click|stopPropagation>

						<!-- Avatar -->
						<div class="msg-avatar {isTeacherMessage ? 'msg-avatar-own' : 'msg-avatar-other'}">
							{m.sender_name ? m.sender_name.charAt(0).toUpperCase() : '?'}
						</div>

						<!-- Body -->
						<div class="msg-body {isTeacherMessage ? 'msg-body-own' : 'msg-body-other'}">
							<!-- Meta row -->
							<div class="msg-meta {isTeacherMessage ? 'msg-meta-own' : ''}">
								<span class="msg-sender">
									{m.sender_name}
									{#if m.sender_id && $user?.id && String(m.sender_id).trim().toLowerCase() === String($user.id).trim().toLowerCase()}
										<span class="msg-sender-me">({$i18n.t('Moi')})</span>
									{/if}
								</span>
								<span class="msg-time">
									{new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
								</span>

								<!-- 3-dots menu -->
								<div class="relative inline-block" on:click|stopPropagation>
									<button
										on:click={() => (activeMenuId = activeMenuId === m.id ? null : m.id)}
										class="msg-menu-btn opacity-0 group-hover:opacity-100"
									>•••</button>
									{#if activeMenuId === m.id}
										<div class="msg-dropdown {isTeacherMessage ? 'right-0' : 'left-0'}">
											{#if m.sender_id && $user?.id && String(m.sender_id).trim().toLowerCase() === String($user.id).trim().toLowerCase()}
												<button on:click={() => { editMessage(m.id, m.content); activeMenuId = null; }}
													class="msg-dropdown-item">✏️ {$i18n.t('Modifier')}</button>
											{/if}
											<button on:click={() => { deleteMessage(m.id); activeMenuId = null; }}
												class="msg-dropdown-item msg-dropdown-danger">🗑️ {$i18n.t('Supprimer')}</button>
											{#if m.sender_role === 'student'}
												<button on:click={() => { kickStudent(m.sender_id); activeMenuId = null; }}
													class="msg-dropdown-item msg-dropdown-warn">🚫 {$i18n.t('Retirer du cours')}</button>
											{/if}
										</div>
									{/if}
								</div>
							</div>

							<!-- Edit form or bubble -->
							{#if editingMessageId === m.id}
								<div class="mt-1 flex flex-col gap-2 w-full min-w-0">
									<input type="text" bind:value={editingContent}
										class="w-full text-xs p-2.5 bg-white dark:bg-[#111827] border border-blue-700 rounded-xl outline-none focus:ring-2 focus:ring-blue-700/20 dark:text-slate-200 font-[inherit]"
										on:keydown={(e) => e.key === 'Enter' && saveEdit(m.id)}
									/>
									<div class="flex gap-2 justify-end">
										<button on:click={() => (editingMessageId = null)}
											class="px-3 py-1.5 text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-lg font-semibold"
										>{$i18n.t('Annuler')}</button>
										<button on:click={() => saveEdit(m.id)}
											class="px-3 py-1.5 text-[11px] bg-blue-700 text-white rounded-lg font-semibold shadow-sm"
										>{$i18n.t('Enregistrer')}</button>
									</div>
								</div>
							{:else}
								<div class="msg-bubble {isTeacherMessage ? 'msg-bubble-own' : 'msg-bubble-other'}">
									{@html renderContent(m.content)}
								</div>
							{/if}
						</div>
					</div>
				{/each}
			{/if}
		</div>

		<!-- Input area -->
		<footer class="msg-footer">
			<div class="msg-input-wrap" on:click|stopPropagation>

				<!-- Textarea -->
				<textarea
					bind:this={textareaEl}
					bind:value={newMessage}
					placeholder={$i18n.t('Écrire un message...')}
					on:keydown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
					rows="2"
					class="msg-textarea"
				></textarea>

				<!-- Bottom bar: format tools + send -->
				<div class="msg-input-bottom">
					<div class="msg-format-tools">
						<button type="button" on:click={() => wrapSelection('**')} title={$i18n.t('Gras')} class="msg-fmt-btn" style="font-weight:700">B</button>
						<button type="button" on:click={() => wrapSelection('*')}  title={$i18n.t('Italique')} class="msg-fmt-btn" style="font-style:italic">I</button>
						<div class="msg-fmt-sep"></div>
						<div class="relative">
							<button type="button" on:click|stopPropagation={() => (showEmojiPicker = !showEmojiPicker)} title={$i18n.t('Emojis')} class="msg-fmt-btn" style="font-size:1rem">😊</button>
							{#if showEmojiPicker}
								<div class="msg-emoji-picker" on:click|stopPropagation>
									<div class="grid grid-cols-10 gap-0.5">
										{#each EMOJIS as emoji}
											<button type="button" on:click={() => insertEmoji(emoji)}
												class="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-lg leading-none"
											>{emoji}</button>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					</div>

					<button on:click={handleSend} disabled={!newMessage.trim()} class="msg-send-btn">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
						</svg>
						{$i18n.t('Envoyer')}
					</button>
				</div>
			</div>
		</footer>
	</main>

	{#if showInviteModal}
		<div class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm transition-all">
			<div class="bg-white dark:bg-[#111827] w-full max-w-md rounded-[32px] p-8 shadow-2xl relative border border-slate-100 dark:border-slate-800 transition-colors">
				<h2 class="text-xl font-bold text-slate-800 dark:text-slate-100 text-center mb-2">
					{$i18n.t('Invite members')}
				</h2>
				<p class="text-xs text-slate-400 dark:text-slate-500 text-center mb-8">
					{$i18n.t('Share this link with your students.')}
				</p>
				<div class="space-y-6">
					<div class="flex items-center gap-2 p-3 bg-slate-50 dark:bg-[#030712] border border-slate-100 dark:border-slate-800 rounded-2xl">
						<input
							type="text"
							readonly
							value="https://opentutorai.com/join/{activeChannelId}"
							class="flex-1 bg-transparent border-none text-xs text-slate-500 outline-none truncate"
						/>
						<button
							on:click={copyChannelLink}
							class="bg-indigo-600 text-white px-4 py-2 rounded-xl text-[10px] font-bold transition-all"
						>{$i18n.t('Copy')}</button>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

	:global(strong) { font-weight: 700; }
	:global(em)     { font-style: italic; }

	.msg-page { font-family: 'Plus Jakarta Sans', sans-serif; }

	/* ── Sidebar background ── */
	aside { background: #eff6ff !important; }
	:global(.dark) aside { background: #04060e !important; }

	/* ── Sidebar hero ── */
	.msg-sidebar-hero {
		background: linear-gradient(150deg, #0d2fa0 0%, #1b4fd8 45%, #2563eb 100%);
		padding: 1.375rem 1.125rem 1.125rem;
		flex-shrink: 0;
		position: relative;
		overflow: hidden;
	}
	.msg-sidebar-hero::after {
		content: '';
		position: absolute;
		top: -40%; right: -20%;
		width: 180px; height: 180px;
		background: radial-gradient(circle, rgba(255,255,255,0.13) 0%, transparent 70%);
		border-radius: 50%;
		pointer-events: none;
	}
	.msg-sidebar-hero-inner {
		display: flex; align-items: center; gap: 0.75rem;
		margin-bottom: 0.875rem; position: relative;
	}
	.msg-sidebar-hero-icon {
		width: 42px; height: 42px;
		background: rgba(255,255,255,0.18);
		border-radius: 0.875rem;
		display: flex; align-items: center; justify-content: center;
		flex-shrink: 0; color: white;
		backdrop-filter: blur(4px);
		border: 1px solid rgba(255,255,255,0.2);
	}
	.msg-sidebar-hero-title {
		font-size: 1rem; font-weight: 800;
		color: white; margin: 0 0 0.1rem;
		line-height: 1.2; letter-spacing: -0.01em;
	}
	.msg-sidebar-hero-sub {
		font-size: 0.7rem; color: rgba(255,255,255,0.65);
		margin: 0; font-weight: 500;
	}
	.msg-sidebar-close {
		background: rgba(255,255,255,0.15);
		border: 1px solid rgba(255,255,255,0.15);
		border-radius: 0.625rem;
		width: 28px; height: 28px;
		display: flex; align-items: center; justify-content: center;
		color: white; cursor: pointer; flex-shrink: 0;
	}
	.msg-sidebar-close:hover { background: rgba(255,255,255,0.28); }

	/* ── Sidebar search ── */
	.msg-sidebar-search-wrap { position: relative; }
	.msg-search-icon {
		position: absolute; left: 0.75rem; top: 50%;
		transform: translateY(-50%);
		color: rgba(255,255,255,0.55); pointer-events: none;
	}
	.msg-sidebar-search {
		width: 100%;
		padding: 0.55rem 0.875rem 0.55rem 2.25rem;
		background: rgba(255,255,255,0.13);
		border: 1px solid rgba(255,255,255,0.18);
		border-radius: 0.75rem;
		color: white; font-size: 0.78rem;
		font-family: inherit; outline: none;
		transition: background 0.15s, border-color 0.15s;
	}
	.msg-sidebar-search::placeholder { color: rgba(255,255,255,0.5); }
	.msg-sidebar-search:focus {
		background: rgba(255,255,255,0.22);
		border-color: rgba(255,255,255,0.38);
	}

	/* ── Chat header ── */
	.msg-chat-header {
		height: 68px;
		padding: 0 1.25rem;
		border-bottom: 1px solid #dbeafe;
		display: flex; align-items: center;
		justify-content: space-between;
		position: sticky; top: 0;
		background: rgba(255,255,255,0.95);
		backdrop-filter: blur(16px);
		z-index: 10; gap: 0.75rem;
	}
	:global(.dark) .msg-chat-header {
		border-bottom-color: #111827;
		background: rgba(4,6,14,0.96);
	}
	.msg-chat-header-avatar {
		width: 38px; height: 38px;
		border-radius: 0.875rem;
		background: linear-gradient(135deg, #1341b8, #2563eb);
		color: white;
		display: flex; align-items: center; justify-content: center;
		font-weight: 800; font-size: 0.92rem;
	}
	.msg-online-dot {
		position: absolute; bottom: -2px; right: -2px;
		width: 11px; height: 11px;
		background: #22c55e;
		border-radius: 50%;
		border: 2.5px solid white;
		box-shadow: 0 0 0 1px rgba(34,197,94,0.3);
	}
	:global(.dark) .msg-online-dot { border-color: #04060e; }
	.msg-chat-header-title {
		font-size: 0.95rem; font-weight: 800;
		color: #1e293b; margin: 0 0 0.1rem;
		line-height: 1.2; letter-spacing: -0.01em;
	}
	:global(.dark) .msg-chat-header-title { color: #f1f5f9; }
	.msg-chat-header-sub {
		font-size: 0.7rem; color: #94a3b8;
		margin: 0; font-weight: 500;
	}

	/* ── Messages area (dot-grid background) ── */
	.msg-area {
		padding: 1.5rem;
		display: flex; flex-direction: column; gap: 0.5rem;
		background-color: #eff6ff;
		background-image: radial-gradient(circle, #bfdbfe 1px, transparent 1px);
		background-size: 28px 28px;
	}
	:global(.dark) .msg-area {
		background-color: #060a18;
		background-image: radial-gradient(circle, #1e2240 1px, transparent 1px);
		background-size: 28px 28px;
	}

	/* ── Date separator ── */
	.msg-date-pill {
		display: flex; align-items: center; gap: 0.75rem;
		margin: 0.625rem 0;
	}
	.msg-date-pill::before,
	.msg-date-pill::after {
		content: ''; flex: 1; height: 1px;
		background: linear-gradient(to right, transparent, #bfdbfe 40%, #bfdbfe 60%, transparent);
	}
	:global(.dark) .msg-date-pill::before,
	:global(.dark) .msg-date-pill::after {
		background: linear-gradient(to right, transparent, #1e3060 40%, #1e3060 60%, transparent);
	}
	.msg-date-pill-text {
		font-size: 0.67rem; font-weight: 700;
		color: #1d4ed8; letter-spacing: 0.06em;
		text-transform: uppercase;
		background: #dbeafe;
		padding: 0.22rem 0.8rem;
		border-radius: 100px;
		border: 1px solid #bfdbfe;
		white-space: nowrap;
		flex-shrink: 0;
	}
	:global(.dark) .msg-date-pill-text {
		color: #60a5fa; background: #0f172a; border-color: #1e3a8a;
	}

	/* ── Empty state ── */
	.msg-empty-icon {
		width: 72px; height: 72px;
		border-radius: 1.5rem;
		background: linear-gradient(135deg, #1b4fd8, #2563eb);
		display: flex; align-items: center; justify-content: center;
		color: white;
		box-shadow: 0 8px 28px rgba(27,79,216,0.38);
	}

	/* ── Message row ── */
	.msg-row {
		display: flex; align-items: flex-end; gap: 0.625rem;
		padding: 0.25rem 0.5rem;
		border-radius: 0.75rem;
		transition: background 0.15s;
	}
	.msg-row:hover { background: rgba(27,79,216,0.06); }
	.msg-row-own  { flex-direction: row-reverse; }
	.msg-row-other { flex-direction: row; }

	/* ── Avatar ── */
	.msg-avatar {
		width: 34px; height: 34px;
		border-radius: 50%;
		display: flex; align-items: center; justify-content: center;
		font-weight: 800; font-size: 0.8rem;
		color: white; flex-shrink: 0;
		box-shadow: 0 2px 10px rgba(0,0,0,0.18);
		transition: transform 0.15s;
	}
	.msg-row:hover .msg-avatar { transform: scale(1.1); }
	.msg-avatar-own   { background: linear-gradient(135deg, #1341b8, #2563eb); }
	.msg-avatar-other { background: linear-gradient(135deg, #059669, #1d4ed8); }

	/* ── Body ── */
	.msg-body {
		display: flex; flex-direction: column;
		max-width: 72%; min-width: 0; gap: 0.3rem;
	}
	.msg-body-own   { align-items: flex-end; }
	.msg-body-other { align-items: flex-start; }

	/* ── Meta ── */
	.msg-meta {
		display: flex; align-items: center; gap: 0.4rem;
		flex-direction: row; padding: 0 0.25rem;
	}
	.msg-meta-own { flex-direction: row-reverse; }
	.msg-sender { font-size: 0.71rem; font-weight: 700; color: #475569; }
	:global(.dark) .msg-sender { color: #94a3b8; }
	.msg-sender-me { font-size: 0.65rem; color: #818cf8; font-weight: 500; }
	.msg-time { font-size: 0.64rem; color: #94a3b8; font-weight: 500; }

	/* ── Menu button ── */
	.msg-menu-btn {
		padding: 0.15rem 0.4rem;
		border-radius: 0.375rem;
		font-size: 0.65rem; font-weight: 900;
		color: #94a3b8; background: none; border: none;
		cursor: pointer; transition: background 0.1s, opacity 0.15s; line-height: 1;
	}
	.msg-menu-btn:hover { background: #dbeafe; color: #1b4fd8; }
	:global(.dark) .msg-menu-btn:hover { background: #1e293b; color: #60a5fa; }

	/* ── Dropdown ── */
	.msg-dropdown {
		position: absolute; top: calc(100% + 4px);
		min-width: 160px; background: white;
		border: 1px solid #dbeafe;
		border-radius: 0.625rem;
		box-shadow: 0 8px 30px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.05);
		z-index: 50; overflow: hidden; padding: 0.3rem 0;
	}
	:global(.dark) .msg-dropdown { background: #1a2238; border-color: #2e3a54; }
	.msg-dropdown-item {
		width: 100%; text-align: left;
		padding: 0.5rem 1rem;
		font-size: 0.74rem; font-weight: 600;
		color: #475569; background: none; border: none;
		cursor: pointer; display: flex; align-items: center; gap: 0.5rem;
		transition: background 0.1s;
	}
	.msg-dropdown-item:hover { background: #dbeafe; }
	:global(.dark) .msg-dropdown-item { color: #cbd5e1; }
	:global(.dark) .msg-dropdown-item:hover { background: #1e293b; }
	.msg-dropdown-danger { color: #dc2626 !important; }
	:global(.dark) .msg-dropdown-danger { color: #f87171 !important; }
	.msg-dropdown-danger:hover { background: #fff1f2 !important; }
	:global(.dark) .msg-dropdown-danger:hover { background: rgba(239,68,68,0.1) !important; }
	.msg-dropdown-warn { color: #d97706 !important; }
	:global(.dark) .msg-dropdown-warn { color: #fbbf24 !important; }
	.msg-dropdown-warn:hover { background: #fffbeb !important; }

	/* ── Bubbles ── */
	.msg-bubble {
		padding: 0.7rem 1rem;
		font-size: 0.83rem; line-height: 1.6;
		word-break: break-word; max-width: 100%;
	}
	.msg-bubble-own {
		background: linear-gradient(140deg, #1b4fd8 0%, #1341b8 50%, #2563eb 100%);
		color: white; border-radius: 1rem;
		box-shadow: 0 6px 20px rgba(27,79,216,0.42), 0 2px 8px rgba(27,79,216,0.18);
	}
	.msg-bubble-other {
		background: white; color: #1e293b; border-radius: 1rem;
		box-shadow: 0 2px 12px rgba(0,0,0,0.07), 0 1px 4px rgba(0,0,0,0.04);
	}
	:global(.dark) .msg-bubble-other {
		background: #1a2238; color: #e2e8f0;
		box-shadow: 0 2px 12px rgba(0,0,0,0.3);
	}

	/* ── Footer ── */
	.msg-footer {
		padding: 0.75rem 1rem 0.875rem;
		background: rgba(255,255,255,0.97);
		border-top: 1px solid #dbeafe;
		flex-shrink: 0;
	}
	:global(.dark) .msg-footer {
		background: rgba(4,6,14,0.97);
		border-top-color: #111827;
	}

	.msg-input-wrap {
		max-width: 900px; margin: 0 auto;
		background: white;
		border: 1.5px solid #bfdbfe;
		border-radius: 0.875rem;
		box-shadow: 0 4px 18px rgba(27,79,216,0.08), 0 1px 4px rgba(0,0,0,0.04);
		transition: border-color 0.15s, box-shadow 0.15s; overflow: hidden;
	}
	.msg-input-wrap:focus-within {
		border-color: #60a5fa;
		box-shadow: 0 0 0 4px rgba(27,79,216,0.1), 0 4px 18px rgba(27,79,216,0.15);
	}
	:global(.dark) .msg-input-wrap {
		background: #0d1117; border-color: #1e293b;
		box-shadow: 0 4px 18px rgba(0,0,0,0.3);
	}
	:global(.dark) .msg-input-wrap:focus-within {
		border-color: #1b4fd8;
		box-shadow: 0 0 0 4px rgba(27,79,216,0.15), 0 4px 18px rgba(0,0,0,0.3);
	}

	.msg-textarea {
		width: 100%; padding: 0.875rem 1rem 0.5rem;
		background: transparent; border: none; resize: none; outline: none;
		font-size: 0.875rem; font-family: inherit; color: #1e293b;
		line-height: 1.6; min-height: 52px; max-height: 160px; display: block;
	}
	:global(.dark) .msg-textarea { color: #e2e8f0; }
	.msg-textarea::placeholder { color: #93c5fd; }

	.msg-input-bottom {
		display: flex; align-items: center;
		justify-content: space-between;
		padding: 0.4rem 0.75rem 0.5rem;
		border-top: 1px solid #dbeafe; gap: 0.5rem;
	}
	:global(.dark) .msg-input-bottom { border-top-color: #1e293b; }

	.msg-format-tools { display: flex; align-items: center; gap: 0.15rem; }
	.msg-fmt-btn {
		width: 30px; height: 30px;
		display: flex; align-items: center; justify-content: center;
		border-radius: 0.5rem; background: none; border: none;
		cursor: pointer; color: #94a3b8; font-size: 0.85rem;
		transition: background 0.1s, color 0.1s; font-family: inherit;
	}
	.msg-fmt-btn:hover { background: #dbeafe; color: #1b4fd8; }
	:global(.dark) .msg-fmt-btn { color: #64748b; }
	:global(.dark) .msg-fmt-btn:hover { background: #1e293b; color: #60a5fa; }

	.msg-fmt-sep {
		width: 1px; height: 16px; background: #bfdbfe;
		margin: 0 0.25rem; flex-shrink: 0;
	}
	:global(.dark) .msg-fmt-sep { background: #1e293b; }

	.msg-send-btn {
		display: flex; align-items: center; gap: 0.4rem;
		padding: 0.55rem 1.125rem;
		background: linear-gradient(135deg, #1b4fd8, #2563eb);
		color: white; border: none; border-radius: 0.625rem;
		font-size: 0.78rem; font-weight: 700;
		cursor: pointer;
		box-shadow: 0 4px 14px rgba(27,79,216,0.4);
		transition: transform 0.12s, box-shadow 0.12s, opacity 0.1s;
		font-family: inherit; white-space: nowrap;
	}
	.msg-send-btn:hover:not(:disabled) {
		transform: translateY(-1px);
		box-shadow: 0 6px 20px rgba(27,79,216,0.5);
	}
	.msg-send-btn:active:not(:disabled) { transform: scale(0.97); }
	.msg-send-btn:disabled { opacity: 0.35; cursor: not-allowed; }

	.msg-emoji-picker {
		position: absolute; bottom: calc(100% + 8px); left: 0;
		width: 288px; background: white;
		border: 1px solid #dbeafe;
		border-radius: 0.75rem;
		box-shadow: 0 12px 36px rgba(0,0,0,0.13);
		padding: 0.75rem; z-index: 50;
	}
	:global(.dark) .msg-emoji-picker { background: #1a2238; border-color: #2e3a54; }

	/* ── Scrollbar ── */
	.msg-area::-webkit-scrollbar       { width: 4px; }
	.msg-area::-webkit-scrollbar-track  { background: transparent; }
	.msg-area::-webkit-scrollbar-thumb  { background: #bfdbfe; border-radius: 4px; }
	:global(.dark) .msg-area::-webkit-scrollbar-thumb { background: #1e2240; }
</style>
