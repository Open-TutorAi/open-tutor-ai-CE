<script lang="ts">
	import { onMount, onDestroy, afterUpdate, getContext, createEventDispatcher } from 'svelte';
	import { user } from '$lib/stores';
	import { getMessages, sendMessage, uploadAttachment, getAttachmentDownloadUrl } from '$lib/apis/messages';
	import type { Message, Attachment } from '$lib/apis/messages';
	import { getTeacherAvailability } from '$lib/apis/teachers';
	import type { TeacherAvailability } from '$lib/apis/teachers';
	import { formatMessageTime } from '$lib/utils/time';

	export let conversationId: string = '';
	export let receiverId: string = '';
	export let studentId: string = '';
	export let displayName: string = '';
	export let studentName: string = '';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher<{ conversationCreated: { conversationId: string } }>();

	let messages: Message[] = [];
	let newMessage = '';
	let sending = false;
	let sendError: string | null = null;
	let loading = true;
	let messagesContainer: HTMLElement;
	let pollInterval: ReturnType<typeof setInterval> | null = null;
	let activeConversationId = conversationId;
	let pendingId = '';

	// Attachment state
	let pendingFiles: File[] = [];
	let uploadedAttachments: Attachment[] = [];
	let uploading = false;
	let uploadProgress: number[] = [];
	let fileInputEl: HTMLInputElement;

	// Teacher availability
	let availability: TeacherAvailability | null = null;

	const ALLOWED_TYPES = [
		'image/jpeg', 'image/png', 'image/gif', 'image/webp',
		'video/mp4', 'video/quicktime', 'video/webm',
		'application/pdf', 'application/msword',
		'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
		'application/vnd.ms-excel',
		'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		'application/vnd.ms-powerpoint',
		'application/vnd.openxmlformats-officedocument.presentationml.presentation',
		'text/plain', 'application/zip'
	];

	const loadMessages = async () => {
		if (!activeConversationId || !$user) return;
		try {
			const fresh = await getMessages(localStorage.token, activeConversationId);
			messages = fresh;
			if (pendingId) pendingId = '';
			sendError = null;
		} catch (_) {}
	};

	const loadAvailability = async () => {
		if (!receiverId) return;
		try {
			availability = await getTeacherAvailability(localStorage.token, receiverId);
		} catch (_) {}
	};

	const startPolling = () => {
		if (pollInterval) return;
		pollInterval = setInterval(loadMessages, 10000);
	};

	const handleFiles = async (files: FileList | null) => {
		if (!files || !activeConversationId) return;
		for (const file of Array.from(files)) {
			if (!ALLOWED_TYPES.includes(file.type)) {
				sendError = `Type de fichier non autorisé : ${file.name}`;
				continue;
			}
			if (file.size > 100 * 1024 * 1024) {
				sendError = `Fichier trop volumineux : ${file.name} (max 100 Mo)`;
				continue;
			}
			pendingFiles = [...pendingFiles, file];
			uploadProgress = [...uploadProgress, 0];
			const idx = pendingFiles.length - 1;
			uploading = true;
			try {
				const att = await uploadAttachment(
					localStorage.token,
					activeConversationId,
					file,
					(pct) => { uploadProgress[idx] = pct; uploadProgress = [...uploadProgress]; }
				);
				uploadedAttachments = [...uploadedAttachments, att];
			} catch (err: any) {
				sendError = String(err);
				pendingFiles = pendingFiles.filter((_, i) => i !== idx);
				uploadProgress = uploadProgress.filter((_, i) => i !== idx);
			} finally {
				uploading = false;
			}
		}
	};

	const removeAttachment = (idx: number) => {
		pendingFiles = pendingFiles.filter((_, i) => i !== idx);
		uploadedAttachments = uploadedAttachments.filter((_, i) => i !== idx);
		uploadProgress = uploadProgress.filter((_, i) => i !== idx);
	};

	const handleSend = async () => {
		const content = newMessage.trim();
		if ((!content && uploadedAttachments.length === 0) || sending || !$user) return;

		const optimisticMsg: Message = {
			id: '__pending__',
			conversation_id: activeConversationId,
			sender_id: $user.id,
			content: content || ' ',
			is_read: false,
			attachments: [],
			created_at: new Date().toISOString()
		};
		messages = [...messages, optimisticMsg];
		pendingId = '__pending__';
		const savedContent = newMessage;
		const savedAttIds = uploadedAttachments.map((a) => a.id);
		newMessage = '';
		pendingFiles = [];
		uploadedAttachments = [];
		uploadProgress = [];
		sending = true;
		sendError = null;

		try {
			const result = await sendMessage(
				localStorage.token,
				receiverId,
				studentId,
				content || ' ',
				savedAttIds.length > 0 ? savedAttIds : undefined
			);
			messages = messages.map((m) => (m.id === '__pending__' ? result.message : m));
			pendingId = '';

			if (!activeConversationId) {
				activeConversationId = result.message.conversation_id;
				dispatch('conversationCreated', { conversationId: activeConversationId });
				startPolling();
			}
		} catch (err: any) {
			messages = messages.filter((m) => m.id !== '__pending__');
			pendingId = '';
			sendError = "Échec de l'envoi. Réessayez.";
			newMessage = savedContent;
		} finally {
			sending = false;
		}
	};

	const handleKeydown = (e: KeyboardEvent) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	};

	const isImage = (mime: string) => mime.startsWith('image/');
	const isVideo = (mime: string) => mime.startsWith('video/');
	const formatSize = (bytes: number) => {
		if (bytes < 1024) return `${bytes} o`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
	};

	const availabilityColor = (s: string | undefined) => {
		if (s === 'available') return 'bg-green-400';
		if (s === 'busy') return 'bg-yellow-400';
		return 'bg-gray-400';
	};
	const availabilityLabel = (s: string | undefined) => {
		if (s === 'available') return 'Disponible';
		if (s === 'busy') return 'Occupé';
		return 'Hors ligne';
	};

	const isOutsideOfficeHours = () => {
		if (!availability?.office_hours_start || !availability?.office_hours_end) return false;
		const now = new Date();
		const [sh, sm] = availability.office_hours_start.split(':').map(Number);
		const [eh, em] = availability.office_hours_end.split(':').map(Number);
		const nowMins = now.getHours() * 60 + now.getMinutes();
		return nowMins < sh * 60 + sm || nowMins > eh * 60 + em;
	};

	onMount(async () => {
		if (activeConversationId) {
			await loadMessages();
			startPolling();
		}
		await loadAvailability();
		loading = false;
	});

	onDestroy(() => {
		if (pollInterval) clearInterval(pollInterval);
	});

	afterUpdate(() => {
		if (messagesContainer) {
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}
	});
</script>

<div class="flex flex-col h-full bg-white dark:bg-gray-850 overflow-hidden">
	<!-- Chat header with availability -->
	<div class="px-5 py-3.5 border-b border-gray-100 dark:border-gray-800 flex items-center gap-3 bg-white dark:bg-gray-850 flex-shrink-0">
		<div class="relative flex-shrink-0">
			<div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-semibold text-sm">
				{displayName ? displayName[0].toUpperCase() : '?'}
			</div>
			{#if availability}
				<span class="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white {availabilityColor(availability.status)}"></span>
			{/if}
		</div>
		<div class="min-w-0 flex-1">
			<p class="font-semibold text-gray-900 dark:text-white text-sm truncate">
				{displayName || 'Conversation'}
			</p>
			<div class="flex items-center gap-2">
				{#if studentName}
					<p class="text-xs text-gray-500 dark:text-gray-400 truncate">
						À propos de <span class="font-medium text-gray-700 dark:text-gray-300">{studentName}</span>
					</p>
				{/if}
				{#if availability}
					<span class="text-xs text-gray-500 dark:text-gray-400">·</span>
					<span class="text-xs text-gray-500 dark:text-gray-400">{availabilityLabel(availability.status)}</span>
				{/if}
			</div>
		</div>
	</div>

	<!-- Out-of-office-hours notice -->
	{#if availability && isOutsideOfficeHours()}
		<div class="px-4 py-2 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-100 dark:border-amber-800">
			<p class="text-xs text-amber-700 dark:text-amber-400">
				En dehors des heures de bureau ({availability.office_hours_start} – {availability.office_hours_end}). La réponse peut être retardée.
			</p>
		</div>
	{/if}

	<!-- Messages area -->
	<div bind:this={messagesContainer} class="flex-1 overflow-y-auto px-5 py-4 space-y-4 min-h-0">
		{#if loading}
			<div class="flex justify-center items-center h-full">
				<div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
			</div>
		{:else if messages.length === 0}
			<div class="flex flex-col items-center justify-center h-full text-center py-12">
				<svg class="w-10 h-10 text-indigo-400 dark:text-indigo-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
				</svg>
				<p class="text-sm font-medium text-gray-800 dark:text-white mb-2">Démarrez la conversation</p>
				<p class="text-sm text-gray-600 dark:text-gray-400">en envoyant un message.</p>
			</div>
		{:else}
			{#each messages as msg (msg.id)}
				{@const isOwn = msg.sender_id === $user?.id}
				{@const isPending = msg.id === '__pending__'}
				<div class="flex {isOwn ? 'justify-end' : 'justify-start'}">
					<div class="max-w-[78%] space-y-1">
						<!-- Text bubble -->
						{#if msg.content && msg.content.trim() && msg.content.trim() !== ' '}
							<div
								class="px-4 py-2.5 rounded-2xl text-sm leading-relaxed
									{isOwn
										? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-md'
										: 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100 rounded-bl-md'}
									{isPending ? 'opacity-60' : ''}"
							>
								{msg.content}
							</div>
						{/if}

						<!-- Attachments -->
						{#if msg.attachments && msg.attachments.length > 0}
							{#each msg.attachments as att}
								{@const dlUrl = `${getAttachmentDownloadUrl(att.id)}?token=${localStorage.token}`}
								<a
									href={dlUrl}
									target="_blank"
									rel="noopener noreferrer"
									download={att.original_filename}
									class="flex items-center gap-2 px-3 py-2 rounded-xl text-sm no-underline
										{isOwn
											? 'bg-blue-700/80 text-white hover:bg-blue-800/80'
											: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700'}
										transition"
								>
									{#if isImage(att.mime_type)}
										<svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
										</svg>
									{:else if isVideo(att.mime_type)}
										<svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
										</svg>
									{:else}
										<svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
										</svg>
									{/if}
									<span class="flex-1 truncate text-xs">{att.original_filename}</span>
									<span class="text-[10px] opacity-70 flex-shrink-0">{formatSize(att.file_size)}</span>
								</a>
							{/each}
						{/if}

						<div class="flex items-center gap-1 {isOwn ? 'justify-end' : 'justify-start'}">
							<span class="text-[11px] text-gray-400 dark:text-gray-500">
								{formatMessageTime(msg.created_at)}
							</span>
							{#if isOwn && !isPending}
								<span class="text-[11px] {msg.is_read ? 'text-blue-400' : 'text-gray-400 dark:text-gray-500'}">
									{msg.is_read ? '✓✓' : '✓'}
								</span>
							{:else if isPending}
								<span class="text-[11px] text-gray-400 dark:text-gray-500">⏳</span>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		{/if}
	</div>

	<!-- Message composer -->
	<div class="px-4 py-3 border-t border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-850 flex-shrink-0">
		{#if sendError}
			<div class="flex items-center gap-2 mb-2 px-3 py-2 bg-red-50 dark:bg-red-900/20 rounded-xl">
				<svg class="w-4 h-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				<p class="text-xs text-red-600 dark:text-red-400">{sendError}</p>
			</div>
		{/if}

		<!-- Pending attachment previews -->
		{#if pendingFiles.length > 0}
			<div class="flex flex-wrap gap-2 mb-2">
				{#each pendingFiles as f, idx}
					<div class="flex items-center gap-1.5 bg-gray-100 dark:bg-gray-900 rounded-lg px-2.5 py-1.5 text-xs text-gray-700 dark:text-gray-200 max-w-[180px]">
						<span class="truncate flex-1">{f.name}</span>
						{#if uploadProgress[idx] < 100}
							<span class="text-[10px] text-blue-500">{uploadProgress[idx]}%</span>
						{:else}
							<svg class="w-3 h-3 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
							</svg>
						{/if}
						<button
							on:click={() => removeAttachment(idx)}
							class="text-gray-400 hover:text-red-500 flex-shrink-0 ml-0.5"
						>
							<svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
								<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
				{/each}
			</div>
		{/if}

		<div class="flex items-end gap-2">
			<!-- Attach button -->
			<button
				on:click={() => fileInputEl.click()}
				disabled={uploading || !activeConversationId}
				class="p-2.5 text-gray-400 hover:text-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition flex-shrink-0"
				title="Joindre un fichier"
			>
				<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
				</svg>
			</button>
			<input
				bind:this={fileInputEl}
				type="file"
				multiple
				accept=".pdf,.jpg,.jpeg,.png,.gif,.webp,.mp4,.mov,.webm,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip"
				class="hidden"
				on:change={(e) => handleFiles(e.currentTarget.files)}
			/>

			<div
				class="flex-1 flex items-center bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-lg px-3 py-2 focus-within:ring-2 focus-within:ring-blue-400/40 transition"
			>
				<textarea
					bind:value={newMessage}
					on:keydown={handleKeydown}
					placeholder="Écrire un message…"
					rows="1"
					disabled={sending}
					class="flex-1 resize-none bg-transparent border-none outline-none focus:ring-0 text-sm text-gray-800 dark:text-white placeholder-gray-400 disabled:opacity-60"
				></textarea>
			</div>
			<button
				on:click={handleSend}
				disabled={sending || uploading || (!newMessage.trim() && uploadedAttachments.length === 0)}
				class="p-2.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition flex-shrink-0"
				title="Envoyer"
			>
				{#if sending}
					<svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
					</svg>
				{:else}
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
					</svg>
				{/if}
			</button>
		</div>
	</div>
</div>
