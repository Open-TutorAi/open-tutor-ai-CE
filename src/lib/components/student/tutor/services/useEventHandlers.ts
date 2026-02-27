import { get, type Writable } from 'svelte/store';
import { tick } from 'svelte';
import { toast } from 'svelte-sonner';
import { goto } from '$app/navigation';
import type { i18n as i18nType } from 'i18next';

import { getChatById, getChatList, updateChatById } from '$lib/apis/chats';
import { copyToClipboard, createMessagesList } from '$lib/utils';

import type { ChatHistory, ChatMessage } from './types';
import { handleStreamingContent, dispatchFinalTTSEvent } from './socketHandler';
import { handleChatCompleted } from './promptSubmission';

export interface EventHandlersOptions {
	chatId: Writable<string>;
	chats: Writable<any[]>;
	config: Writable<any>;
	settings: Writable<any>;
	socket: Writable<any>;
	models: Writable<any[]>;
	currentChatPage: Writable<number>;
	temporaryChatEnabled: Writable<boolean>;
	showCallOverlay: Writable<boolean>;
	chatTitle: Writable<string>;
	i18n: Writable<i18nType>;
}

export interface EventHandlersState {
	history: ChatHistory;
	selectedModels: string[];
	params: any;
	chatFiles: any[];
	autoScroll: boolean;
	avatarActive: boolean;
}

export interface DialogState {
	showEventConfirmation: boolean;
	eventConfirmationTitle: string;
	eventConfirmationMessage: string;
	eventConfirmationInput: boolean;
	eventConfirmationInputPlaceholder: string;
	eventConfirmationInputValue: string;
	eventCallback: ((result: any) => void) | null;
}

export function createEventHandlers(
	options: EventHandlersOptions,
	getState: () => EventHandlersState,
	setState: (updates: Partial<EventHandlersState>) => void,
	getDialogState: () => DialogState,
	setDialogState: (updates: Partial<DialogState>) => void,
	eventTarget: EventTarget,
	scrollToBottom: () => void
) {
	const {
		chatId,
		chats,
		config,
		settings,
		socket,
		models,
		currentChatPage,
		temporaryChatEnabled,
		showCallOverlay,
		chatTitle
	} = options;

	// Window message handler
	function handleWindowMessage(
		event: MessageEvent,
		submitPrompt: (prompt: string) => void,
		getCurrentPrompt: () => string,
		setPrompt: (value: string) => void
	) {
		if (event.origin !== window.origin) return;
		const { type, text } = event.data;

		if (type === 'input:prompt') {
			setPrompt(text);
			document.getElementById('chat-input')?.focus();
		} else if (type === 'action:submit' || type === 'input:prompt:submit') {
			const prompt = getCurrentPrompt();
			if (prompt || text) submitPrompt(text || prompt);
		}
	}

	// Socket chat event handler
	async function handleChatEvent(event: any, cb?: (result: any) => void) {
		const state = getState();
		const $chatId = get(chatId);
		
		if (event.chat_id !== $chatId) return;
		await tick();

		const message = state.history.messages[event.message_id];
		if (!message) return;

		const type = event?.data?.type;
		const data = event?.data?.data;

		switch (type) {
			case 'status':
				message.statusHistory = [...(message.statusHistory ?? []), data];
				break;
			case 'source':
			case 'citation':
				handleSourceOrCitation(message, data);
				break;
			case 'chat:completion':
				await handleCompletion(data, message, event.chat_id);
				break;
			case 'chat:title':
				await handleTitleUpdate(data);
				break;
			case 'chat:tags':
				await getChatById(localStorage.token, $chatId);
				break;
			case 'message':
				message.content += data.content;
				break;
			case 'replace':
				message.content = data.content;
				break;
			case 'action':
				if (data.action === 'continue') {
					document.getElementById('continue-response-button')?.click();
				}
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

		// Update history
		const newHistory = { ...state.history };
		newHistory.messages[event.message_id] = message;
		setState({ history: newHistory });
	}

	function handleSourceOrCitation(message: ChatMessage, data: any) {
		if (data?.type === 'code_execution') {
			message.code_executions = message.code_executions ?? [];
			const idx = message.code_executions.findIndex((e: any) => e.id === data.id);
			if (idx !== -1) {
				message.code_executions[idx] = data;
			} else {
				message.code_executions.push(data);
			}
		} else {
			message.sources = [...(message.sources ?? []), data];
		}
	}

	async function handleTitleUpdate(data: string) {
		chatTitle.set(data);
		currentChatPage.set(1);
		chats.set(await getChatList(localStorage.token, get(currentChatPage)));
	}

	function showConfirmDialog(data: any, cb: any, isInput: boolean) {
		setDialogState({
			eventCallback: cb ?? null,
			eventConfirmationInput: isInput,
			showEventConfirmation: true,
			eventConfirmationTitle: data.title,
			eventConfirmationMessage: data.message,
			eventConfirmationInputPlaceholder: data.placeholder ?? '',
			eventConfirmationInputValue: data.value ?? ''
		});
	}

	function showNotification(data: any) {
		const notifyFn = {
			success: toast.success,
			error: toast.error,
			warning: toast.warning
		}[data?.type as string] ?? toast.info;
		
		notifyFn(data?.content ?? '');
	}

	async function handleCompletion(data: any, message: ChatMessage, chatIdValue: string) {
		const state = getState();
		const $config = get(config);
		const $settings = get(settings);
		const $models = get(models);
		const $socket = get(socket);
		const $chatId = get(chatId);
		const $temporaryChatEnabled = get(temporaryChatEnabled);
		const $showCallOverlay = get(showCallOverlay);

		if (data.error) {
			message.error = { content: data.error?.message ?? 'Error' };
			message.done = true;
			const newHistory = { ...state.history };
			newHistory.messages[message.id] = message;
			setState({ history: newHistory });
			return;
		}

		handleStreamingContent(message, data, $config, $settings, eventTarget);
		
		const newHistory = { ...state.history };
		newHistory.messages[message.id] = message;
		setState({ history: newHistory });

		if (data.done) {
			message.done = true;
			
			if ($settings.responseAutoCopy) {
				copyToClipboard(message.content);
			}
			
			if ($settings.responseAutoPlayback && !$showCallOverlay) {
				await tick();
				document.getElementById(`speak-button-${message.id}`)?.click();
			}
			
			dispatchFinalTTSEvent(message, $config, eventTarget);

			await handleChatCompleted(
				localStorage.token,
				chatIdValue,
				message.model!,
				message.id,
				createMessagesList(state.history, message.id),
				$models,
				$socket
			);

			if ($chatId === chatIdValue && !$temporaryChatEnabled) {
				await updateChatById(localStorage.token, chatIdValue, {
					models: state.selectedModels,
					messages: createMessagesList(state.history, message.id),
					history: state.history,
					params: state.params,
					files: state.chatFiles
				});
				currentChatPage.set(1);
				chats.set(await getChatList(localStorage.token, get(currentChatPage)));
			}
		}

		if (state.autoScroll) scrollToBottom();

		if (message.content && state.avatarActive) {
			return {
				avatarMessage: message.content,
				avatarSpeaking: true
			};
		}

		return null;
	}

	// Setup functions
	function setupWindowListener(
		submitPrompt: (prompt: string) => void,
		getCurrentPrompt: () => string,
		setPrompt: (value: string) => void
	) {
		const handler = (event: MessageEvent) => handleWindowMessage(event, submitPrompt, getCurrentPrompt, setPrompt);
		window.addEventListener('message', handler);
		return () => window.removeEventListener('message', handler);
	}

	function setupSocketListener() {
		const $socket = get(socket);
		$socket?.on('chat-events', handleChatEvent);
		return () => $socket?.off('chat-events', handleChatEvent);
	}

	return {
		handleWindowMessage,
		handleChatEvent,
		showConfirmDialog,
		showNotification,
		handleCompletion,
		setupWindowListener,
		setupSocketListener
	};
}
