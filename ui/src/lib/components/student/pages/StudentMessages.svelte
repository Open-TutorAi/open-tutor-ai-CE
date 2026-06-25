<script lang="ts">
	import { onMount, onDestroy, tick, getContext } from 'svelte';
	import { socket, user, messagesUnread } from '$lib/stores';
	import {
		getConversations,
		getMessages,
		sendMessage,
		startConversation,
		downloadMessageAttachment,
		type Conversation,
		type Message
	} from '$lib/apis/messaging';
	import { getMyTeachers, type MyTeacher } from '$lib/apis/classrooms';
	import { uploadFile } from '$lib/apis/files';

	const i18n: any = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';

	let conversations: Conversation[] = [];
	let loading = true;
	let active: Conversation | null = null;
	let messages: Message[] = [];
	let draft = '';
	let attachment: File | null = null;
	let sending = false;
	let threadEl: HTMLDivElement;

	function onPickFile(e: Event) {
		const input = e.target as HTMLInputElement;
		attachment = input.files && input.files.length ? input.files[0] : null;
	}
	async function downloadAtt(m: Message) {
		if (!active || !m.attachment_id) return;
		try {
			const blob = await downloadMessageAttachment(token(), active.id, m.id);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = m.attachment_name ?? 'attachment';
			a.click();
			URL.revokeObjectURL(url);
		} catch (err) {
			/* ignore */
		}
	}

	// New-message picker (the student's teachers)
	let showPicker = false;
	let teachers: MyTeacher[] = [];

	// Keep the sidebar badge in sync as conversations load / are read.
	$: messagesUnread.set(conversations.reduce((sum, c) => sum + (c.unread || 0), 0));

	function fmtTime(ts: string | null): string {
		return ts ? new Date(ts).toLocaleString() : '';
	}

	async function loadConversations() {
		try {
			conversations = await getConversations(token());
		} catch (err) {
			/* leave */
		} finally {
			loading = false;
		}
	}

	async function openConversation(c: Conversation) {
		active = c;
		try {
			const thread = await getMessages(token(), c.id);
			messages = thread.messages;
			conversations = conversations.map((x) => (x.id === c.id ? { ...x, unread: 0 } : x));
			await tick();
			scrollToBottom();
		} catch (err) {
			messages = [];
		}
	}

	function scrollToBottom() {
		if (threadEl) threadEl.scrollTop = threadEl.scrollHeight;
	}

	async function send() {
		if (!active || (!draft.trim() && !attachment)) return;
		sending = true;
		const body = draft.trim();
		try {
			let attachmentId: string | undefined;
			if (attachment) {
				const uploaded = await uploadFile(token(), attachment);
				attachmentId = uploaded.id;
			}
			const msg = await sendMessage(token(), active.id, body, attachmentId);
			messages = [...messages, msg];
			draft = '';
			attachment = null;
			const preview = body || `📎 ${msg.attachment_name ?? 'Attachment'}`;
			conversations = conversations.map((x) =>
				x.id === active!.id ? { ...x, last_message: preview, last_message_at: msg.created_at } : x
			);
			await tick();
			scrollToBottom();
		} catch (err) {
			/* keep draft */
		} finally {
			sending = false;
		}
	}

	async function openPicker() {
		showPicker = true;
		if (teachers.length === 0) {
			try {
				teachers = await getMyTeachers(token());
			} catch (err) {
				teachers = [];
			}
		}
	}

	async function startWith(t: MyTeacher) {
		showPicker = false;
		try {
			const conv = await startConversation(token(), t.teacher_id);
			if (!conversations.find((c) => c.id === conv.id)) {
				conversations = [conv, ...conversations];
			}
			await openConversation(conv);
		} catch (err) {
			/* ignore */
		}
	}

	function onIncoming(data: any) {
		if (!data) return;
		if (active && data.conversation_id === active.id) {
			messages = [...messages, data.message];
			tick().then(scrollToBottom);
			getMessages(token(), active.id).catch(() => {});
		}
		loadConversations();
	}

	onMount(() => {
		loadConversations();
		$socket?.on('message:new', onIncoming);
	});
	onDestroy(() => {
		$socket?.off('message:new', onIncoming);
	});
</script>

<div class="flex flex-col gap-4 h-[calc(100vh-9rem)]">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-gray-800 dark:text-white">{$i18n.t('Messages')}</h1>
			<p class="text-gray-500 dark:text-gray-400 mt-1">
				{$i18n.t('Direct messages with your teachers.')}
			</p>
		</div>
		<button
			class="px-4 py-2 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm hover:opacity-90"
			on:click={openPicker}>+ {$i18n.t('New message')}</button
		>
	</div>

	<div class="flex flex-1 min-h-0 gap-4">
		<!-- Conversation list -->
		<div
			class="w-full sm:w-80 shrink-0 rounded-2xl bg-white dark:bg-gray-800 shadow-sm overflow-y-auto {active
				? 'hidden sm:block'
				: ''}"
		>
			{#if loading}
				<div class="flex justify-center py-12">
					<div
						class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"
					></div>
				</div>
			{:else if conversations.length === 0}
				<div class="p-6 text-center text-gray-500 dark:text-gray-400 text-sm">
					{$i18n.t('No conversations yet — start one.')}
				</div>
			{:else}
				<ul class="divide-y divide-gray-100 dark:divide-gray-700">
					{#each conversations as c (c.id)}
						<li>
							<button
								class="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/40 {active?.id ===
								c.id
									? 'bg-blue-50 dark:bg-blue-900/20'
									: ''}"
								on:click={() => openConversation(c)}
							>
								<div class="flex items-center justify-between gap-2">
									<span class="font-medium text-gray-800 dark:text-white truncate"
										>{c.other_name ?? c.other_email ?? '—'}</span
									>
									{#if c.unread > 0}<span
											class="text-xs bg-blue-600 text-white rounded-full px-2 py-0.5 shrink-0"
											>{c.unread}</span
										>{/if}
								</div>
								<div class="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
									{c.last_message ?? $i18n.t('No messages yet')}
								</div>
							</button>
						</li>
					{/each}
				</ul>
			{/if}
		</div>

		<!-- Thread -->
		<div
			class="flex-1 min-w-0 rounded-2xl bg-white dark:bg-gray-800 shadow-sm flex flex-col {active
				? ''
				: 'hidden sm:flex'}"
		>
			{#if !active}
				<div class="flex-1 flex items-center justify-center text-gray-400 text-sm">
					{$i18n.t('Select a conversation')}
				</div>
			{:else}
				<div
					class="px-5 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center gap-2"
				>
					<button class="sm:hidden text-gray-500" on:click={() => (active = null)} aria-label="Back"
						>‹</button
					>
					<div class="font-semibold text-gray-800 dark:text-white">
						{active.other_name ?? active.other_email ?? '—'}
					</div>
				</div>
				<div bind:this={threadEl} class="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-2">
					{#each messages as m (m.id)}
						{@const mine = m.sender_id === $user?.id}
						<div class="max-w-[75%] {mine ? 'self-end' : 'self-start'}">
							<div
								class="px-3 py-2 rounded-2xl text-sm {mine
									? 'bg-blue-600 text-white rounded-br-sm'
									: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-bl-sm'}"
							>
								{#if m.body}<div class="whitespace-pre-wrap">{m.body}</div>{/if}
								{#if m.attachment_id}
									<button
										class="inline-flex items-center gap-1 underline {m.body ? 'mt-1' : ''} {mine
											? 'text-white/90'
											: 'text-blue-600 dark:text-blue-400'}"
										on:click={() => downloadAtt(m)}
									>
										📎 {m.attachment_name ?? $i18n.t('Attachment')}
									</button>
								{/if}
							</div>
							<div class="text-[10px] text-gray-400 mt-0.5 {mine ? 'text-right' : ''}">
								{fmtTime(m.created_at)}
							</div>
						</div>
					{/each}
				</div>
				<form
					class="px-4 py-3 border-t border-gray-100 dark:border-gray-700 flex items-center gap-2"
					on:submit|preventDefault={send}
				>
					<label
						class="shrink-0 cursor-pointer text-gray-400 hover:text-blue-600 text-xl px-1"
						title={$i18n.t('Attach a file')}
					>
						📎<input type="file" class="hidden" on:change={onPickFile} />
					</label>
					<div class="flex-1 min-w-0">
						<input
							class="w-full rounded-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300"
							placeholder={$i18n.t('Write a message…')}
							bind:value={draft}
						/>
						{#if attachment}<div
								class="text-xs text-gray-500 dark:text-gray-400 mt-1 px-2 truncate"
							>
								📎 {attachment.name}
								<button type="button" class="text-red-400 ml-1" on:click={() => (attachment = null)}
									>✕</button
								>
							</div>{/if}
					</div>
					<button
						type="submit"
						class="px-4 py-2 rounded-full bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-50"
						disabled={sending || (!draft.trim() && !attachment)}>{$i18n.t('Send')}</button
					>
				</form>
			{/if}
		</div>
	</div>
</div>

{#if showPicker}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
		on:click|self={() => (showPicker = false)}
		role="presentation"
	>
		<div class="w-full max-w-md rounded-2xl bg-white dark:bg-gray-800 shadow-xl p-6">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-lg font-semibold text-gray-800 dark:text-white">
					{$i18n.t('Message a teacher')}
				</h2>
				<button
					class="text-gray-400 hover:text-gray-600"
					on:click={() => (showPicker = false)}
					aria-label="Close">✕</button
				>
			</div>
			<div class="max-h-72 overflow-y-auto divide-y divide-gray-100 dark:divide-gray-700">
				{#if teachers.length === 0}
					<div class="py-6 text-center text-gray-500 dark:text-gray-400 text-sm">
						{$i18n.t('No teachers yet — join a class first.')}
					</div>
				{:else}
					{#each teachers as t (t.teacher_id)}
						<button
							class="w-full text-left px-2 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/40"
							on:click={() => startWith(t)}
						>
							<div class="text-gray-800 dark:text-white text-sm">{t.name ?? t.email ?? '—'}</div>
							<div class="text-xs text-gray-400">{t.classes.map((c) => c.name).join(', ')}</div>
						</button>
					{/each}
				{/if}
			</div>
		</div>
	</div>
{/if}
