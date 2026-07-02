<script lang="ts">
	import { onMount, getContext, createEventDispatcher } from 'svelte';
	import { getChatList, deleteChatById, deleteAllChats } from '$lib/apis/chats';
	import { page } from '$app/stores';

	const i18n: any = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let currentChatId: string | null = null;

	let chats: any[] = [];
	let loading = true;
	let searchQuery = '';
	let collapsed = false;
	let deletingId: string | null = null;
	let confirmDeleteId: string | null = null;
	let confirmDeleteAll = false;
	let deletingAll = false;

	$: activeChatId = currentChatId ?? $page.params.id ?? null;

	$: filteredChats = searchQuery.trim()
		? chats.filter(c => (c.title || '').toLowerCase().includes(searchQuery.toLowerCase()))
		: chats;

	onMount(async () => {
		await loadChats();
	});

	async function loadChats() {
		loading = true;
		try {
			const token = localStorage.token || '';
			const data = await getChatList(token);
			chats = Array.isArray(data) ? data : [];
		} catch (e) {
			chats = [];
		} finally {
			loading = false;
		}
	}

	function startNewChat() {
		// Use location.href to force full navigation, avoiding avatar/SPA state issues
		window.location.href = '/student/chat';
	}

	function openChat(chatId: string) {
		confirmDeleteId = null;
		// Use location.href to force clean navigation to the chat (avoids avatar redirect)
		window.location.href = `/student/c/${chatId}`;
		dispatch('selectChat', chatId);
	}

	async function deleteChat(e: MouseEvent, chatId: string) {
		e.stopPropagation();
		if (confirmDeleteId !== chatId) {
			confirmDeleteId = chatId;
			return;
		}
		deletingId = chatId;
		confirmDeleteId = null;
		try {
			await deleteChatById(localStorage.token || '', chatId);
			chats = chats.filter(c => c.id !== chatId);
			if (activeChatId === chatId) {
				window.location.href = '/student/chat';
			}
		} catch (e) {
			console.error('Delete failed', e);
		} finally {
			deletingId = null;
		}
	}

	function cancelDelete(e: MouseEvent) {
		e.stopPropagation();
		confirmDeleteId = null;
	}

	async function deleteAll() {
		if (!confirmDeleteAll) {
			confirmDeleteAll = true;
			return;
		}
		deletingAll = true;
		confirmDeleteAll = false;
		try {
			await deleteAllChats(localStorage.token || '');
			chats = [];
			window.location.href = '/student/chat';
		} catch (e) {
			console.error('Delete all failed', e);
		} finally {
			deletingAll = false;
		}
	}

	function formatDate(ts: number): string {
		if (!ts) return '';
		const d = new Date(ts * 1000);
		const now = new Date();
		const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000);
		if (diffDays === 0) return "Aujourd'hui";
		if (diffDays === 1) return 'Hier';
		if (diffDays < 7) return `Il y a ${diffDays}j`;
		return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
	}

	$: groupedChats = (() => {
		const groups: Record<string, any[]> = {};
		for (const chat of filteredChats) {
			const label = formatDate(chat.created_at || chat.updated_at);
			if (!groups[label]) groups[label] = [];
			groups[label].push(chat);
		}
		return groups;
	})();
</script>

<aside class="chat-history-sidebar" class:collapsed>
	<div class="sidebar-header">
		{#if !collapsed}
			<span class="sidebar-title">💬 {$i18n.t('Historique')}</span>
		{/if}
		<button class="collapse-btn" title="Toggle sidebar" on:click={() => (collapsed = !collapsed)}>
			{collapsed ? '›' : '‹'}
		</button>
	</div>

	{#if !collapsed}
		<button class="new-chat-btn" on:click={startNewChat}>
			<svg xmlns="http://www.w3.org/2000/svg" class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
				<path d="M12 5v14M5 12h14" stroke-linecap="round"/>
			</svg>
			{$i18n.t('Nouvelle discussion')}
		</button>

		<div class="search-wrapper">
			<svg xmlns="http://www.w3.org/2000/svg" class="search-icon" viewBox="0 0 20 20" fill="currentColor">
				<path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
			</svg>
			<input type="text" class="search-input" placeholder={$i18n.t('Rechercher...')} bind:value={searchQuery}/>
		</div>

		<div class="chat-list">
			{#if loading}
				<div class="state-msg"><div class="spinner"></div><span>{$i18n.t('Chargement...')}</span></div>
			{:else if filteredChats.length === 0}
				<div class="state-msg empty">
					<svg xmlns="http://www.w3.org/2000/svg" class="empty-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
					</svg>
					<p>{searchQuery ? $i18n.t('Aucun résultat') : $i18n.t('Aucune conversation')}</p>
				</div>
			{:else}
				{#each Object.entries(groupedChats) as [dateLabel, group]}
					<div class="date-group">
						<div class="date-label">{dateLabel}</div>
						{#each group as chat}
							<div
								class="chat-item"
								class:active={chat.id === activeChatId}
								class:confirming={confirmDeleteId === chat.id}
							>
								<button class="chat-item-body" on:click={() => openChat(chat.id)} title={chat.title || 'Nouvelle conversation'}>
									<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="chat-icon">
										<path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z"/>
									</svg>
									<span class="chat-title">{chat.title || $i18n.t('Nouvelle conversation')}</span>
								</button>

								{#if confirmDeleteId === chat.id}
									<div class="delete-confirm">
										<button class="btn-confirm-yes" on:click={(e) => deleteChat(e, chat.id)} title="Confirmer">✓</button>
										<button class="btn-confirm-no" on:click={cancelDelete} title="Annuler">✕</button>
									</div>
								{:else}
									<button class="delete-btn" on:click={(e) => deleteChat(e, chat.id)} title={$i18n.t('Supprimer')} disabled={deletingId === chat.id}>
										{#if deletingId === chat.id}
											<div class="mini-spinner"></div>
										{:else}
											<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="trash-icon">
												<path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
											</svg>
										{/if}
									</button>
								{/if}
							</div>
						{/each}
					</div>
				{/each}
			{/if}
		</div>

		<!-- Delete all button -->
		<div class="delete-all-area">
			{#if confirmDeleteAll}
				<p class="confirm-all-msg">⚠️ {$i18n.t('Supprimer tout ?')}</p>
				<div class="confirm-all-btns">
					<button class="btn-all-yes" on:click={deleteAll} disabled={deletingAll}>
						{#if deletingAll}<div class="mini-spinner"></div>{:else}✓ {$i18n.t('Oui, tout supprimer')}{/if}
					</button>
					<button class="btn-all-no" on:click={() => confirmDeleteAll = false}>✕ {$i18n.t('Annuler')}</button>
				</div>
			{:else}
				<button class="delete-all-btn" on:click={deleteAll} disabled={chats.length === 0}>
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="trash-icon-sm">
						<path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
					</svg>
					{$i18n.t('Effacer tout l\'historique')}
				</button>
			{/if}
		</div>
	{/if}
</aside>

<style>
	.chat-history-sidebar {
		display: flex; flex-direction: column;
		height: 100%; width: 220px; min-width: 220px;
		background: rgba(255,255,255,0.65);
		border-right: 1px solid rgba(0,0,0,0.07);
		border-radius: 16px 0 0 16px;
		overflow: hidden;
		transition: width 0.25s cubic-bezier(0.4,0,0.2,1), min-width 0.25s;
		backdrop-filter: blur(12px);
		flex-shrink: 0;
	}
	:global(.dark) .chat-history-sidebar { background: rgba(17,24,39,0.75); border-color: rgba(255,255,255,0.07); }
	.chat-history-sidebar.collapsed { width: 44px; min-width: 44px; }

	.sidebar-header {
		display: flex; align-items: center; justify-content: space-between;
		padding: 14px 8px 10px 12px;
		border-bottom: 1px solid rgba(0,0,0,0.06);
		flex-shrink: 0;
	}
	:global(.dark) .sidebar-header { border-color: rgba(255,255,255,0.06); }
	.sidebar-title { font-size: 13px; font-weight: 700; color: #374151; white-space: nowrap; }
	:global(.dark) .sidebar-title { color: #e5e7eb; }
	.collapse-btn {
		flex-shrink: 0; width: 26px; height: 26px;
		border: 1px solid rgba(0,0,0,0.1); border-radius: 8px;
		background: rgba(0,0,0,0.04); color: #6b7280; font-size: 16px;
		cursor: pointer; display: flex; align-items: center; justify-content: center;
		transition: all 0.2s;
	}
	.collapse-btn:hover { background: rgba(0,0,0,0.1); color: #111; }
	:global(.dark) .collapse-btn { border-color: rgba(255,255,255,0.1); background: rgba(255,255,255,0.06); color: #9ca3af; }

	.new-chat-btn {
		margin: 10px 8px 6px; padding: 9px 12px;
		background: linear-gradient(135deg, #3b82f6, #6366f1);
		color: white; border: none; border-radius: 12px;
		font-size: 12.5px; font-weight: 600; cursor: pointer;
		display: flex; align-items: center; gap: 7px;
		transition: opacity 0.2s, transform 0.15s;
		white-space: nowrap; flex-shrink: 0;
	}
	.new-chat-btn:hover { opacity: 0.88; transform: translateY(-1px); }
	.icon { width: 14px; height: 14px; flex-shrink: 0; }

	.search-wrapper { position: relative; margin: 0 8px 6px; flex-shrink: 0; }
	.search-icon { position: absolute; left: 8px; top: 50%; transform: translateY(-50%); width: 13px; height: 13px; color: #9ca3af; pointer-events: none; }
	.search-input {
		width: 100%; padding: 6px 8px 6px 28px; font-size: 12px;
		border: 1px solid rgba(0,0,0,0.1); border-radius: 10px;
		background: rgba(0,0,0,0.03); color: #374151; outline: none;
		box-sizing: border-box; transition: border-color 0.2s;
	}
	.search-input:focus { border-color: #3b82f6; }
	:global(.dark) .search-input { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.1); color: #e5e7eb; }

	.chat-list { flex: 1; overflow-y: auto; padding: 0 4px 6px; }
	.chat-list::-webkit-scrollbar { width: 3px; }
	.chat-list::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 2px; }

	.date-group { margin-bottom: 4px; }
	.date-label { font-size: 9.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #9ca3af; padding: 8px 8px 3px; }

	.chat-item { display: flex; align-items: center; border-radius: 10px; overflow: hidden; margin-bottom: 1px; transition: background 0.15s; }
	.chat-item:hover { background: rgba(59,130,246,0.07); }
	.chat-item.active { background: rgba(59,130,246,0.12); }
	.chat-item.confirming { background: rgba(239,68,68,0.08); }
	:global(.dark) .chat-item:hover { background: rgba(99,102,241,0.12); }
	:global(.dark) .chat-item.active { background: rgba(99,102,241,0.2); }

	.chat-item-body { flex: 1; display: flex; align-items: center; gap: 6px; padding: 7px 6px; background: transparent; border: none; cursor: pointer; text-align: left; color: #374151; min-width: 0; }
	:global(.dark) .chat-item-body { color: #d1d5db; }
	.chat-item.active .chat-item-body { color: #1d4ed8; font-weight: 600; }
	:global(.dark) .chat-item.active .chat-item-body { color: #818cf8; }
	.chat-icon { width: 13px; height: 13px; flex-shrink: 0; color: #9ca3af; }
	.chat-title { font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }

	.delete-btn { flex-shrink: 0; width: 26px; height: 26px; margin-right: 3px; background: transparent; border: none; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #9ca3af; opacity: 0; transition: opacity 0.15s, background 0.15s, color 0.15s; }
	.chat-item:hover .delete-btn { opacity: 1; }
	.delete-btn:hover { background: rgba(239,68,68,0.1); color: #ef4444; }
	.trash-icon { width: 13px; height: 13px; }

	.delete-confirm { display: flex; gap: 3px; margin-right: 4px; flex-shrink: 0; }
	.btn-confirm-yes, .btn-confirm-no { width: 24px; height: 24px; border: none; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; }
	.btn-confirm-yes { background: #ef4444; color: white; }
	.btn-confirm-yes:hover { background: #dc2626; }
	.btn-confirm-no { background: rgba(0,0,0,0.08); color: #6b7280; }

	/* Delete all area */
	.delete-all-area {
		flex-shrink: 0; padding: 8px;
		border-top: 1px solid rgba(0,0,0,0.06);
	}
	:global(.dark) .delete-all-area { border-color: rgba(255,255,255,0.06); }
	.delete-all-btn {
		width: 100%; padding: 7px 10px;
		background: transparent;
		border: 1px solid rgba(239,68,68,0.3);
		border-radius: 10px;
		color: #ef4444; font-size: 11.5px; font-weight: 600;
		cursor: pointer; display: flex; align-items: center; gap: 6px;
		transition: background 0.15s, border-color 0.15s;
	}
	.delete-all-btn:hover { background: rgba(239,68,68,0.07); border-color: #ef4444; }
	.delete-all-btn:disabled { opacity: 0.4; cursor: not-allowed; }
	.trash-icon-sm { width: 13px; height: 13px; flex-shrink: 0; }
	.confirm-all-msg { font-size: 11px; color: #ef4444; font-weight: 700; margin: 0 0 6px; text-align: center; }
	.confirm-all-btns { display: flex; gap: 6px; }
	.btn-all-yes { flex: 1; padding: 7px; background: #ef4444; color: white; border: none; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 4px; }
	.btn-all-yes:hover { background: #dc2626; }
	.btn-all-no { flex: 1; padding: 7px; background: rgba(0,0,0,0.07); border: none; border-radius: 8px; font-size: 11px; font-weight: 600; color: #6b7280; cursor: pointer; }

	.state-msg { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 24px 12px; color: #9ca3af; font-size: 12px; text-align: center; }
	.empty-icon { width: 36px; height: 36px; opacity: 0.3; }
	.spinner { width: 20px; height: 20px; border: 2px solid rgba(59,130,246,0.2); border-top-color: #3b82f6; border-radius: 50%; animation: spin 0.8s linear infinite; }
	.mini-spinner { width: 10px; height: 10px; border: 1.5px solid rgba(239,68,68,0.2); border-top-color: #ef4444; border-radius: 50%; animation: spin 0.8s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }
</style>
