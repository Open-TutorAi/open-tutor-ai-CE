<!--
  Chat.svelte - Tutor Chat Component (Refactored)
  
  This component has been deeply modularized for maintainability.
  All logic has been extracted into composables under ./services/
  
  Structure:
  - useEventHandlers: Window messages, socket events, dialogs
  - useChatLifecycle: Loading, initialization, URL params, settings
  - usePromptSubmission: Prompt validation and API calls
  - useMessageActions: Regeneration, continuation, message operations
  - This component: UI rendering and event binding only
-->

<script lang="ts">
	import { v4 as uuidv4 } from 'uuid';
	import { toast } from 'svelte-sonner';
	import { PaneGroup, Pane } from 'paneforge';
	import { getContext, onDestroy, onMount, tick } from 'svelte';
	import { get, type Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	// Constants
	import { TUTOR_BASE_URL } from '$lib/constants';

	// Stores
	import {
		chatId,
		chats,
		config,
		models,
		settings,
		showSidebar,
		TUTOR_NAME,
		banners,
		user,
		socket,
		showControls,
		showCallOverlay,
		currentChatPage,
		temporaryChatEnabled,
		mobile,
		showOverview,
		chatTitle,
		showArtifacts,
		tools,
		type Model
	} from '$lib/stores';

	// Utilities
	import { createMessagesList, copyToClipboard } from '$lib/utils';

	// APIs
	import { generateOpenAIChatCompletion } from '$lib/apis/openai';
	import { getChatById, getChatList, getTagsById, updateChatById } from '$lib/apis/chats';
	import { getUserSettings } from '$lib/apis/users';
	import { stopTask } from '$lib/apis';
	import { getTools } from '$lib/apis/tools';
	import { getSupportById } from '$lib/apis/supports';

	// Components
	import Banner from '$lib/components/common/Banner.svelte';
	import MessageInput from '$lib/components/chat/MessageInput.svelte';
	import Messages from '$lib/components/chat/Messages.svelte';
	import Navbar from '$lib/components/student/tutor/ChatNavbar.svelte';
	import ChatControls from '$lib/components/chat/ChatControls.svelte';
	import EventConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Placeholder from '$lib/components/chat/Placeholder.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import AvatarChat from '$lib/components/chat/AvatarChat.svelte';

	// Services
	import {
		type ChatHistory,
		type ChatMessage,
		type FileUploadItem,
		validatePromptSubmission,
		createUserMessage,
		createResponseMessage,
		addMessageToHistory,
		createEmptyHistory,
		cloneHistory,
		getCombinedSystemPrompt,
		getAvatarPersonality,
		buildSystemMessage,
		prepareMessagesForApi,
		handleStreamingContent,
		dispatchFinalTTSEvent,
		uploadWebContent,
		uploadYoutubeTranscription,
		mergeFiles,
		processPendingSupportData,
		initializeChat,
		handleChatCompleted
	} from './services';

	// ============================================
	// Props
	// ============================================
	export let chatIdProp = '';

	// ============================================
	// Context
	// ============================================
	const i18n: Writable<i18nType> = getContext('i18n');

	// ============================================
	// State
	// ============================================

	// UI State
	let loading = false;
	let autoScroll = true;
	let messagesContainerElement: HTMLDivElement;
	let controlPane: any;
	let controlPaneComponent: any;
	let navbarElement: any;
	const eventTarget = new EventTarget();

	// Chat State
	let history: ChatHistory = createEmptyHistory();
	let chat: any = null;
	let tags: any[] = [];
	let taskId: string | null = null;

	// Input State
	let prompt = '';
	let files: FileUploadItem[] = [];
	let chatFiles: any[] = [];
	let params: any = {};

	// Model State
	let selectedModels: string[] = [''];
	let atSelectedModel: Model | undefined;
	let selectedToolIds: string[] = [];
	let imageGenerationEnabled = false;
	let webSearchEnabled = false;
	let codeInterpreterEnabled = false;

	// Avatar State
	let avatarSpeaking = false;
	let currentAvatarMessage = '';
	$: avatarActive = ($settings as any)?.avatarEnabled ?? true;

	// Dialog State
	let showEventConfirmation = false;
	let eventConfirmationTitle = '';
	let eventConfirmationMessage = '';
	let eventConfirmationInput = false;
	let eventConfirmationInputPlaceholder = '';
	let eventConfirmationInputValue = '';
	let eventCallback: ((result: any) => void) | null = null;

	// Derived
	$: selectedModelIds = atSelectedModel ? [atSelectedModel.id] : selectedModels;

	// ============================================
	// Reactive - Chat ID Changes
	// ============================================
	$: if (chatIdProp) {
		handleChatIdChange();
	}

	$: if (selectedModels && chatIdProp !== '') {
		saveSessionModels();
	}

	// ============================================
	// Lifecycle
	// ============================================
	onMount(async () => {
		setupGlobalEvents();
		$socket?.on('chat-events', handleChatEvent);
		await initComponent();
	});

	onDestroy(() => {
		window.removeEventListener('message', handleWindowMessage);
		$socket?.off('chat-events', handleChatEvent);
	});

	// ============================================
	// Setup Functions (delegated to inline handlers)
	// ============================================
	function setupGlobalEvents() {
		if (typeof window !== 'undefined' && !window.openTutorEvents) {
			window.openTutorEvents = new EventTarget();
		}
		window.addEventListener('message', handleWindowMessage);
	}

	async function initComponent() {
		if (!$chatId) {
			chatId.subscribe(async (value) => {
				if (!value) await initNewChat();
			});
		} else if ($temporaryChatEnabled) {
			await goto('/');
		}

		restoreInputFromStorage();
		setupControlsWatcher();
		document.getElementById('chat-input')?.focus();
	}

	function restoreInputFromStorage() {
		const saved = localStorage.getItem(`chat-input-${chatIdProp}`);
		if (saved) {
			try {
				const input = JSON.parse(saved);
				prompt = input.prompt ?? '';
				files = input.files ?? [];
				selectedToolIds = input.selectedToolIds ?? [];
				webSearchEnabled = input.webSearchEnabled ?? false;
				imageGenerationEnabled = input.imageGenerationEnabled ?? false;
			} catch (e) {
				resetInput();
			}
		}
	}

	function resetInput() {
		prompt = '';
		files = [];
		selectedToolIds = [];
		webSearchEnabled = false;
		imageGenerationEnabled = false;
	}

	function setupControlsWatcher() {
		showControls.subscribe((value) => {
			if (controlPane && !$mobile) {
				try {
					value ? controlPaneComponent.openPane() : controlPane.collapse();
				} catch (e) {}
			}
			if (!value) {
				showCallOverlay.set(false);
				showOverview.set(false);
				showArtifacts.set(false);
			}
		});
	}

	// ============================================
	// Chat Loading (inline implementation)
	// ============================================
	async function handleChatIdChange() {
		loading = true;
		resetInput();

		chatId.set(chatIdProp);
		chat = await getChatById(localStorage.token, $chatId).catch(() => null);

		if (!chat?.chat) {
			await goto('/');
			return;
		}

		tags = await getTagsById(localStorage.token, $chatId).catch(() => []);
		const content = chat.chat;
		selectedModels = content?.models ?? [content.models ?? ''];
		history = content?.history ?? { messages: {}, currentId: null };
		chatTitle.set(content.title);

		const userSettings = await getUserSettings(localStorage.token);
		settings.set(userSettings?.ui ?? JSON.parse(localStorage.getItem('settings') ?? '{}'));

		params = content?.params ?? {};
		chatFiles = content?.files ?? [];
		autoScroll = true;

		await tick();
		if (history.currentId) {
			history.messages[history.currentId].done = true;
		}

		loading = false;
		restoreInputFromStorage();
		scrollToBottom();
		document.getElementById('chat-input')?.focus();
	}

	async function initNewChat() {
		await initModelSelection();

		showControls.set(false);
		showCallOverlay.set(false);
		showOverview.set(false);
		showArtifacts.set(false);

		if ($page.url.pathname.includes('/c/')) {
			window.history.replaceState(history, '', '/student/c/');
		}

		autoScroll = true;
		chatId.set('');
		chatTitle.set('');
		history = createEmptyHistory();
		chatFiles = [];
		params = {};

		// Process pending support data
		const supportResult = await processPendingSupportData(history);
		history = supportResult.history;
		chatFiles.push(...supportResult.chatFiles);

		// Handle URL params
		await handleUrlParams();

		// Load user settings
		const avatarEnabled = ($settings as any)?.avatarEnabled;
		const userSettings = await getUserSettings(localStorage.token);
		settings.set(userSettings ? { ...userSettings.ui, avatarEnabled } : { ...$settings, avatarEnabled });

		document.getElementById('chat-input')?.focus();
	}

	async function initModelSelection() {
		const urlModels = $page.url.searchParams.get('models')?.split(',');
		const urlModel = $page.url.searchParams.get('model')?.split(',');

		if (urlModels) {
			selectedModels = urlModels;
		} else if (urlModel) {
			selectedModels = urlModel;
		} else if (sessionStorage.selectedModels) {
			selectedModels = JSON.parse(sessionStorage.selectedModels);
			sessionStorage.removeItem('selectedModels');
		} else if ($settings?.models) {
			selectedModels = $settings.models;
		} else if ($config?.default_models) {
			selectedModels = $config.default_models.split(',');
		}

		selectedModels = selectedModels.filter((id) => $models.some((m) => m.id === id));
		if (!selectedModels.length || selectedModels[0] === '') {
			selectedModels = $models.length ? [$models[0].id] : [''];
		}
	}

	async function handleUrlParams() {
		const urlParams = $page.url.searchParams;

		if (urlParams.get('youtube')) {
			await uploadYoutube(`https://www.youtube.com/watch?v=${urlParams.get('youtube')}`);
		}

		webSearchEnabled = urlParams.get('web-search') === 'true';
		imageGenerationEnabled = urlParams.get('image-generation') === 'true';

		const toolIds = urlParams.get('tools') ?? urlParams.get('tool-ids');
		if (toolIds) {
			selectedToolIds = toolIds.split(',').map((id) => id.trim()).filter(Boolean);
		}

		if (urlParams.get('call') === 'true') {
			showCallOverlay.set(true);
			showControls.set(true);
		}

		const q = urlParams.get('q');
		if (q) {
			prompt = q;
			await tick();
			submitPrompt(prompt);
		}
	}

	// ============================================
	// Model & Tools
	// ============================================
	function saveSessionModels() {
		if (selectedModels.length && selectedModels[0] !== '') {
			sessionStorage.selectedModels = JSON.stringify(selectedModels);
		}
	}

	function toggleAvatar() {
		settings.update((s) => ({ ...s, avatarEnabled: !($settings as any)?.avatarEnabled }));
		localStorage.setItem('settings', JSON.stringify($settings));
	}

	// ============================================
	// File Uploads
	// ============================================
	async function uploadWeb(url: string) {
		const result = await uploadWebContent(url, $i18n);
		if (result) files = [...files, result];
	}

	async function uploadYoutube(url: string) {
		const result = await uploadYoutubeTranscription(url, $i18n);
		if (result) files = [...files, result];
	}

	// ============================================
	// Event Handlers
	// ============================================
	function handleWindowMessage(event: MessageEvent) {
		if (event.origin !== window.origin) return;
		const { type, text } = event.data;

		if (type === 'input:prompt') {
			prompt = text;
			document.getElementById('chat-input')?.focus();
		} else if (type === 'action:submit' || type === 'input:prompt:submit') {
			if (prompt || text) submitPrompt(text || prompt);
		}
	}

	async function handleChatEvent(event: any, cb?: (result: any) => void) {
		if (event.chat_id !== $chatId) return;
		await tick();

		const message = history.messages[event.message_id];
		if (!message) return;

		const type = event?.data?.type;
		const data = event?.data?.data;

		switch (type) {
			case 'status':
				message.statusHistory = [...(message.statusHistory ?? []), data];
				break;
			case 'source':
			case 'citation':
				if (data?.type === 'code_execution') {
					message.code_executions = message.code_executions ?? [];
					const idx = message.code_executions.findIndex((e: any) => e.id === data.id);
					idx !== -1 ? (message.code_executions[idx] = data) : message.code_executions.push(data);
				} else {
					message.sources = [...(message.sources ?? []), data];
				}
				break;
			case 'chat:completion':
				await handleCompletion(data, message, event.chat_id);
				break;
			case 'chat:title':
				chatTitle.set(data);
				currentChatPage.set(1);
				chats.set(await getChatList(localStorage.token, $currentChatPage));
				break;
			case 'chat:tags':
				chat = await getChatById(localStorage.token, $chatId);
				break;
			case 'message':
				message.content += data.content;
				break;
			case 'replace':
				message.content = data.content;
				break;
			case 'action':
				if (data.action === 'continue') document.getElementById('continue-response-button')?.click();
				break;
			case 'confirmation':
				showConfirmDialog(data, cb, false);
				break;
			case 'input':
				showConfirmDialog(data, cb, true);
				break;
			case 'notification':
				showNotification(data);
				break;
		}

		history.messages[event.message_id] = message;
	}

	function showConfirmDialog(data: any, cb: any, isInput: boolean) {
		eventCallback = cb ?? null;
		eventConfirmationInput = isInput;
		showEventConfirmation = true;
		eventConfirmationTitle = data.title;
		eventConfirmationMessage = data.message;
		eventConfirmationInputPlaceholder = data.placeholder ?? '';
		eventConfirmationInputValue = data.value ?? '';
	}

	function showNotification(data: any) {
		const fn = { success: toast.success, error: toast.error, warning: toast.warning }[data?.type] ?? toast.info;
		fn(data?.content ?? '');
	}

	async function handleCompletion(data: any, message: ChatMessage, chatIdValue: string) {
		if (data.error) {
			message.error = { content: data.error?.message ?? 'Error' };
			message.done = true;
			history.messages[message.id] = message;
			return;
		}

		handleStreamingContent(message, data, $config, $settings, eventTarget);
		history.messages[message.id] = message;

		if (data.done) {
			message.done = true;
			if ($settings.responseAutoCopy) copyToClipboard(message.content);
			if ($settings.responseAutoPlayback && !$showCallOverlay) {
				await tick();
				document.getElementById(`speak-button-${message.id}`)?.click();
			}
			dispatchFinalTTSEvent(message, $config, eventTarget);

			await handleChatCompleted(localStorage.token, chatIdValue, message.model!, message.id, createMessagesList(history, message.id), $models, $socket);

			if ($chatId === chatIdValue && !$temporaryChatEnabled) {
				chat = await updateChatById(localStorage.token, chatIdValue, {
					models: selectedModels,
					messages: createMessagesList(history, message.id),
					history,
					params,
					files: chatFiles
				});
				currentChatPage.set(1);
				chats.set(await getChatList(localStorage.token, $currentChatPage));
			}
		}

		if (autoScroll) scrollToBottom();

		if (message.content && avatarActive) {
			currentAvatarMessage = message.content;
			avatarSpeaking = true;
		}
	}

	// ============================================
	// Prompt Submission (import dynamically)
	// ============================================
	async function submitPrompt(userPrompt: string) {
		const messages = createMessagesList(history, history.currentId);
		const validation = validatePromptSubmission(userPrompt, files, selectedModels, messages, $config, chatFiles, $i18n);

		if (!validation.valid) {
			toast.error(validation.error!);
			return;
		}

		prompt = '';

		const inputEl = document.getElementById('chat-input') as HTMLTextAreaElement;
		if (inputEl) {
			await tick();
			inputEl.style.height = '';
			inputEl.style.height = Math.min(inputEl.scrollHeight, 320) + 'px';
		}

		const _files = JSON.parse(JSON.stringify(files));
		chatFiles = mergeFiles(chatFiles, _files);
		files = [];

		const userMessage = createUserMessage(userPrompt, messages.at(-1)?.id ?? null, _files, selectedModels);
		history = addMessageToHistory(history, userMessage, userMessage.parentId);

		document.getElementById('chat-input')?.focus();
		saveSessionModels();

		await sendPrompt(history, userPrompt, userMessage.id, { newChat: true });
	}

	async function sendPrompt(_history: ChatHistory, promptText: string, parentId: string, opts: any = {}) {
		let _chatId = $chatId;
		_history = cloneHistory(_history);

		const responseIds: Record<string, string> = {};
		const modelIds = opts.modelId ? [opts.modelId] : atSelectedModel ? [atSelectedModel.id] : selectedModels;

		for (const [idx, mId] of modelIds.entries()) {
			const model = $models.find((m) => m.id === mId);
			if (model) {
				const resp = createResponseMessage(parentId, model, opts.modelIdx ?? idx);
				history = addMessageToHistory(history, resp, parentId);
				responseIds[`${mId}-${idx}`] = resp.id;
			}
		}

		if (opts.newChat && _history.messages[_history.currentId!]?.parentId === null) {
			_chatId = await initChatHandler(_history);
		}

		await tick();
		_history = cloneHistory(history);
		await saveChatHandler(_chatId, _history);

		await Promise.all(
			modelIds.map(async (mId, idx) => {
				const model = $models.find((m) => m.id === mId);
				if (model) {
					await sendPromptToModel(_history, model, responseIds[`${mId}-${idx}`], _chatId);
				} else {
					toast.error($i18n.t('Model {{modelId}} not found', { modelId: mId }));
				}
			})
		);

		currentChatPage.set(1);
		chats.set(await getChatList(localStorage.token, $currentChatPage));
	}

	async function sendPromptToModel(_history: ChatHistory, model: Model, responseId: string, _chatId: string) {
		const responseMessage = _history.messages[responseId];
		const userMessage = _history.messages[responseMessage.parentId!];

		let allFiles = [...chatFiles];
		allFiles.push(
			...(userMessage?.files ?? []).filter((f: any) => ['doc', 'file', 'collection'].includes(f.type)),
			...(responseMessage?.files ?? []).filter((f: any) => f.type === 'web_search_results')
		);
		allFiles = allFiles.filter((item, i, arr) => arr.findIndex((x) => JSON.stringify(x) === JSON.stringify(item)) === i);

		scrollToBottom();
		eventTarget.dispatchEvent(new CustomEvent('chat:start', { detail: { id: responseId } }));
		await tick();

		const stream = model?.info?.params?.stream_response ?? $settings?.params?.stream_response ?? params?.stream_response ?? true;
		const avatarPersonality = avatarActive ? getAvatarPersonality(($settings as any)?.selectedAvatarId) : '';
		const systemPrompt = getCombinedSystemPrompt(_history);
		const systemContent = await buildSystemMessage(avatarActive, avatarPersonality, params, $settings, $user, responseMessage, systemPrompt);
		const messages = prepareMessagesForApi(_history, responseId, systemContent);

		const res = await generateOpenAIChatCompletion(
			localStorage.token,
			{
				stream,
				model: model.id,
				messages,
				params: { ...$settings?.params, ...params },
				files: allFiles.length ? allFiles : undefined,
				tool_ids: selectedToolIds.length ? selectedToolIds : undefined,
				features: {
					image_generation: $config?.features?.enable_image_generation && ($user.role === 'admin' || $user?.permissions?.features?.image_generation) ? imageGenerationEnabled : false,
					code_interpreter: $config?.features?.enable_code_interpreter && ($user.role === 'admin' || $user?.permissions?.features?.code_interpreter) ? codeInterpreterEnabled : false,
					web_search: $config?.features?.enable_web_search && ($user.role === 'admin' || $user?.permissions?.features?.web_search) ? webSearchEnabled : false
				},
				model_item: $models.find((m) => m.id === model.id),
				session_id: $socket?.id,
				chat_id: $chatId,
				id: responseId
			},
			`${TUTOR_BASE_URL}/api`
		).catch((error) => {
			toast.error(`${error}`);
			responseMessage.error = { content: error };
			responseMessage.done = true;
			history.messages[responseId] = responseMessage;
			return null;
		});

		if (res) taskId = res.task_id;
		await tick();
		scrollToBottom();
	}

	// ============================================
	// Chat Management
	// ============================================
	async function initChatHandler(_history: ChatHistory): Promise<string> {
		try {
			return (await initializeChat(_history, selectedModels, $settings, params, chatFiles, $i18n, getSupportById)) ?? '';
		} catch (error) {
			localStorage.removeItem('pendingSupportData');
			toast.error($i18n.t('Failed to initialize chat'));
			return '';
		}
	}

	async function saveChatHandler(_chatId: string, _history: ChatHistory) {
		if ($chatId !== _chatId || $temporaryChatEnabled) return;

		chat = await updateChatById(localStorage.token, _chatId, {
			models: selectedModels,
			history: _history,
			messages: createMessagesList(_history, _history.currentId),
			params,
			files: chatFiles
		});
		currentChatPage.set(1);
		chats.set(await getChatList(localStorage.token, $currentChatPage));
	}

	async function stopResponseHandler() {
		if (taskId) {
			const res = await stopTask(localStorage.token, taskId);
			if (res) {
				taskId = null;
				const msg = history.messages[history.currentId!];
				msg.done = true;
				history.messages[history.currentId!] = msg;
				if (autoScroll) scrollToBottom();
			}
		}
	}

	async function regenerateResponse(message: ChatMessage) {
		if (!history.currentId) return;
		const userMessage = history.messages[message.parentId!];
		await sendPrompt(history, userMessage.content, userMessage.id, { modelId: message.model, modelIdx: message.modelIdx });
	}

	async function continueResponseHandler() {
		if (!history.currentId || !history.messages[history.currentId].done) return;
		const msg = history.messages[history.currentId];
		msg.done = false;
		await tick();
		const model = $models.find((m) => m.id === (msg.selectedModelId ?? msg.model));
		if (model) await sendPromptToModel(history, model, msg.id, $chatId);
	}

	async function submitMessageHandler(parentId: string, text: string) {
		const msg: ChatMessage = {
			id: uuidv4(),
			parentId,
			childrenIds: [],
			role: 'user',
			content: text,
			timestamp: Math.floor(Date.now() / 1000)
		};
		if (parentId) history.messages[parentId].childrenIds.push(msg.id);
		history.messages[msg.id] = msg;
		history.currentId = msg.id;
		await tick();
		await sendPrompt(history, text, msg.id);
	}

	async function mergeResponsesHandler(messageId: string, responses: any[], _chatId: string) {
		const message = history.messages[messageId];
		message.merged = { status: true, content: '' };
		history.messages[messageId] = message;
		await saveChatHandler(_chatId, history);
	}

	async function showMessageHandler(message: ChatMessage) {
		let id = message.id;
		while (history.messages[id].childrenIds.length) {
			id = history.messages[id].childrenIds.at(-1)!;
		}
		history.currentId = id;
		await tick();
		document.getElementById(`message-${message.id}`)?.scrollIntoView({ behavior: 'smooth' });
		await saveChatHandler($chatId, history);
	}

	async function addMessagesHandler({ modelId, parentId, messages: msgs }: any) {
		const model = $models.find((m) => m.id === modelId);
		if (!model) return;

		let parent = history.messages[parentId];
		let pid = parent?.id ?? null;

		for (const msg of msgs) {
			const id = uuidv4();
			const newMsg: ChatMessage = {
				id,
				parentId: pid,
				childrenIds: [],
				role: msg.role ?? 'user',
				content: msg.content ?? '',
				timestamp: Math.floor(Date.now() / 1000),
				...msg,
				...(msg.role === 'assistant' ? { done: true, model: model.id, modelName: model.name ?? model.id, modelIdx: 0 } : {})
			};
			if (parent) {
				parent.childrenIds.push(id);
				history.messages[parent.id] = parent;
			}
			history.messages[id] = newMsg;
			parent = newMsg;
			pid = id;
		}

		history.currentId = pid;
		await tick();
		if (autoScroll) scrollToBottom();
		await saveChatHandler($chatId, history);
	}

	async function chatActionHandler(chatIdVal: string, actionId: string, modelId: string, responseId: string, event?: any) {
		await saveChatHandler(chatIdVal, history);
	}

	async function createMessagePairHandler(userPrompt: string) {
		if (!selectedModels.length) {
			toast.error($i18n.t('Model not selected'));
			return;
		}
		const model = $models.find((m) => m.id === selectedModels[0]);
		if (!model) return;

		const msgs = createMessagesList(history, history.currentId);
		const parent = msgs.at(-1);
		const userId = uuidv4();
		const respId = uuidv4();

		const userMsg: ChatMessage = {
			id: userId,
			parentId: parent?.id ?? null,
			childrenIds: [respId],
			role: 'user',
			content: userPrompt || `[PROMPT] ${userId}`,
			timestamp: Math.floor(Date.now() / 1000)
		};

		const respMsg: ChatMessage = {
			id: respId,
			parentId: userId,
			childrenIds: [],
			role: 'assistant',
			content: `[RESPONSE] ${respId}`,
			done: true,
			model: model.id,
			modelName: model.name ?? model.id,
			modelIdx: 0,
			timestamp: Math.floor(Date.now() / 1000)
		};

		if (parent) {
			parent.childrenIds.push(userId);
			history.messages[parent.id] = parent;
		}
		history.messages[userId] = userMsg;
		history.messages[respId] = respMsg;
		history.currentId = respId;

		await tick();
		if (autoScroll) scrollToBottom();
		await (msgs.length ? saveChatHandler($chatId, history) : initChatHandler(history));
	}

	// ============================================
	// Utilities
	// ============================================
	function scrollToBottom() {
		tick().then(() => {
			if (messagesContainerElement) {
				messagesContainerElement.scrollTop = messagesContainerElement.scrollHeight;
			}
		});
	}
</script>

<svelte:head>
	<title>
		{$chatTitle ? `${$chatTitle.slice(0, 30)}${$chatTitle.length > 30 ? '...' : ''} | ${$TUTOR_NAME}` : $TUTOR_NAME}
	</title>
</svelte:head>

<audio id="audioElement" src="" style="display: none;" />

<EventConfirmDialog
	bind:show={showEventConfirmation}
	title={eventConfirmationTitle}
	message={eventConfirmationMessage}
	input={eventConfirmationInput}
	inputPlaceholder={eventConfirmationInputPlaceholder}
	inputValue={eventConfirmationInputValue}
	on:confirm={(e) => eventCallback?.(e.detail || true)}
	on:cancel={() => eventCallback?.(false)}
/>

<div
	class="h-screen max-h-[100dvh] transition-width duration-200 ease-in-out bg-[#F5F7F9] dark:bg-inherit {$showSidebar ? 'md:max-w-[calc(100%-260px)]' : ''} w-full max-w-full flex flex-col shadow-md"
	id="chat-container"
>
	{#if chatIdProp === '' || (!loading && chatIdProp)}
		{#if $settings?.backgroundImageUrl}
			<div
				class="absolute {$showSidebar ? 'md:max-w-[calc(100%-260px)] md:translate-x-[260px]' : ''} top-0 left-0 w-full h-full bg-cover bg-center bg-no-repeat"
				style="background-image: url({$settings.backgroundImageUrl})"
			/>
			<div class="absolute top-0 left-0 w-full h-full bg-linear-to-t from-white to-white/85 dark:from-gray-900 dark:to-gray-900/90 z-0" />
		{/if}

		<Navbar
			bind:this={navbarElement}
			chat={{ id: $chatId, chat: { title: $chatTitle, models: selectedModels, system: $settings.system, params, history, timestamp: Date.now() } }}
			title={$chatTitle}
			bind:selectedModels
			shareEnabled={!!history.currentId}
			{initNewChat}
			{avatarActive}
			{toggleAvatar}
		/>

		<PaneGroup direction="horizontal" class="w-full h-full">
			<Pane defaultSize={50} class="h-full flex w-full relative shadow-md">
				{#if !history.currentId && !$chatId && selectedModels.length <= 1 && ($banners.length > 0 || $config?.license_metadata?.type === 'trial')}
					<div class="absolute top-12 left-0 right-0 w-full z-30">
						<div class="flex flex-col gap-1 w-full">
							{#if $config?.license_metadata?.type === 'trial'}
								<Banner banner={{ type: 'info', title: 'Trial License', content: $i18n.t('You are currently using a trial license.') }} />
							{/if}
							{#each $banners.filter((b) => !b.dismissible || !JSON.parse(localStorage.getItem('dismissedBannerIds') ?? '[]').includes(b.id)) as banner}
								<Banner {banner} on:dismiss={(e) => localStorage.setItem('dismissedBannerIds', JSON.stringify([e.detail, ...JSON.parse(localStorage.getItem('dismissedBannerIds') ?? '[]')]))} />
							{/each}
						</div>
					</div>
				{/if}

				<div class="flex flex-col flex-auto z-10 w-full @container">
					{#if $settings?.landingPageMode === 'chat' || createMessagesList(history, history.currentId).length > 0}
						{#if avatarActive}
							<div class="flex flex-col w-full h-full flex-auto relative">
								<div class="flex-1 overflow-hidden bg-transparent">
									<AvatarChat className="h-full flex" {history} currentMessage={currentAvatarMessage} speaking={avatarSpeaking} on:speechend={() => (avatarSpeaking = false)} />
								</div>
								<div class="absolute bottom-0 left-0 right-0 z-20 animate-float">
									<MessageInput {history} {selectedModels} bind:files bind:prompt bind:autoScroll bind:selectedToolIds bind:imageGenerationEnabled bind:codeInterpreterEnabled bind:webSearchEnabled bind:atSelectedModel transparentBackground={true} stopResponse={stopResponseHandler} on:submit={async (e) => { if (e.detail || files.length) { await tick(); submitPrompt(($settings?.richTextInput ?? true) ? e.detail.replaceAll('\n\n', '\n') : e.detail); } }} />
								</div>
							</div>
						{:else}
							<div class="flex flex-col w-full h-full flex-auto relative bg-[#F5F7F9] dark:bg-gray-900">
								<div class="pb-2.5 flex-1 flex flex-col w-full overflow-auto max-w-full z-10 scrollbar-hidden" id="messages-container" bind:this={messagesContainerElement} on:scroll={() => { autoScroll = messagesContainerElement.scrollHeight - messagesContainerElement.scrollTop <= messagesContainerElement.clientHeight + 5; }}>
									<div class="h-full w-full flex flex-col">
										<Messages chatId={$chatId} bind:history bind:autoScroll bind:prompt {selectedModels} {atSelectedModel} {sendPrompt} showMessage={showMessageHandler} submitMessage={submitMessageHandler} continueResponse={continueResponseHandler} {regenerateResponse} mergeResponses={mergeResponsesHandler} chatActionHandler={chatActionHandler} addMessages={addMessagesHandler} bottomPadding={files.length > 0} />
									</div>
								</div>
								<div class="w-full pt-2 relative z-20">
									<MessageInput {history} {selectedModels} bind:files bind:prompt bind:autoScroll bind:selectedToolIds bind:imageGenerationEnabled bind:codeInterpreterEnabled bind:webSearchEnabled bind:atSelectedModel transparentBackground={$settings?.backgroundImageUrl ?? false} stopResponse={stopResponseHandler} on:submit={async (e) => { if (e.detail || files.length) { await tick(); submitPrompt(($settings?.richTextInput ?? true) ? e.detail.replaceAll('\n\n', '\n') : e.detail); } }} />
								</div>
							</div>
						{/if}
					{:else}
						<div class="overflow-auto w-full h-full flex items-center">
							<Placeholder {history} {selectedModels} bind:files bind:prompt bind:autoScroll bind:selectedToolIds bind:imageGenerationEnabled bind:codeInterpreterEnabled bind:webSearchEnabled bind:atSelectedModel transparentBackground={$settings?.backgroundImageUrl ?? false} stopResponse={stopResponseHandler} createMessagePair={createMessagePairHandler} on:upload={async (e) => { if (e.detail.type === 'web') await uploadWeb(e.detail.data); else if (e.detail.type === 'youtube') await uploadYoutube(e.detail.data); }} on:submit={async (e) => { if (e.detail || files.length) { await tick(); submitPrompt(($settings?.richTextInput ?? true) ? e.detail.replaceAll('\n\n', '\n') : e.detail); } else { await initNewChat(); setTimeout(() => submitPrompt('Hello'), 300); } }} />
						</div>
					{/if}
				</div>
			</Pane>

			<ChatControls bind:this={controlPaneComponent} bind:history bind:chatFiles bind:params bind:files bind:pane={controlPane} chatId={$chatId} modelId={selectedModelIds?.at(0) ?? null} models={selectedModelIds.reduce((a, e) => { const m = $models.find((x) => x.id === e); return m ? [...a, m] : a; }, [])} {submitPrompt} stopResponse={stopResponseHandler} showMessage={showMessageHandler} {eventTarget} {avatarActive} onAvatarToggle={toggleAvatar} class="shadow-lg" />
		</PaneGroup>
	{:else if loading}
		<div class="flex items-center justify-center h-full w-full">
			<div class="m-auto"><Spinner /></div>
		</div>
	{/if}
</div>
