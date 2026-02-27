import { tick } from 'svelte';
import { toast } from 'svelte-sonner';
import { get } from 'svelte/store';

import { getAllTags } from '$lib/apis/chats';
import { getChatById, getChatList } from '$lib/apis/chats';
import { chatId, chats, currentChatPage, chatTitle, tags as allTags } from '$lib/stores';
import { getMessageContentParts } from '$lib/utils';

import type { ChatHistory, ChatMessage, ChatEventData } from './types';

export interface ChatEventHandlerConfig {
	history: ChatHistory;
	config: any;
	settings: any;
	autoScroll: boolean;
	eventTarget: EventTarget;
	onHistoryUpdate: (history: ChatHistory) => void;
	onAutoScrollUpdate: (autoScroll: boolean) => void;
	onChatCompletionEvent: (data: any, message: ChatMessage, chatId: string) => Promise<void>;
	scrollToBottom: () => void;
}

/**
 * Creates a chat event handler function
 */
export function createChatEventHandler(config: ChatEventHandlerConfig) {
	return async (event: ChatEventData, cb?: (result: any) => void) => {
		console.log('Chat event received:', event);
		const currentChatId = get(chatId);

		if (event.chat_id !== currentChatId) {
			return;
		}

		await tick();
		const message = config.history.messages[event.message_id];

		if (!message) {
			return;
		}

		const type = event?.data?.type ?? null;
		const data = event?.data?.data ?? null;

		switch (type) {
			case 'status':
				handleStatusEvent(message, data, config);
				break;

			case 'source':
			case 'citation':
				handleSourceEvent(message, data, config);
				break;

			case 'chat:completion':
				await config.onChatCompletionEvent(data, message, event.chat_id);
				break;

			case 'chat:title':
				await handleTitleEvent(data);
				break;

			case 'chat:tags':
				await handleTagsEvent(currentChatId);
				break;

			case 'message':
				handleMessageEvent(message, data, config);
				break;

			case 'replace':
				handleReplaceEvent(message, data, config);
				break;

			case 'action':
				handleActionEvent(data);
				break;

			case 'confirmation':
				return handleConfirmationEvent(data, cb);

			case 'execute':
				return await handleExecuteEvent(data, cb);

			case 'input':
				return handleInputEvent(data, cb);

			case 'notification':
				handleNotificationEvent(data);
				break;

			default:
				console.log('Unknown message type', data);
		}

		config.history.messages[event.message_id] = message;
		config.onHistoryUpdate(config.history);
	};
}

/**
 * Handles status update events
 */
function handleStatusEvent(message: ChatMessage, data: any, config: ChatEventHandlerConfig): void {
	if (message.statusHistory) {
		message.statusHistory.push(data);
	} else {
		message.statusHistory = [data];
	}
}

/**
 * Handles source/citation events
 */
function handleSourceEvent(message: ChatMessage, data: any, config: ChatEventHandlerConfig): void {
	if (data?.type === 'code_execution') {
		// Code execution; update existing or add new
		if (!message.code_executions) {
			message.code_executions = [];
		}

		const existingIndex = message.code_executions.findIndex(
			(execution: any) => execution.id === data.id
		);

		if (existingIndex !== -1) {
			message.code_executions[existingIndex] = data;
		} else {
			message.code_executions.push(data);
		}
	} else {
		// Regular source
		if (message.sources) {
			message.sources.push(data);
		} else {
			message.sources = [data];
		}
	}
}

/**
 * Handles chat title update events
 */
async function handleTitleEvent(data: string): Promise<void> {
	chatTitle.set(data);
	currentChatPage.set(1);
	await chats.set(await getChatList(localStorage.token, get(currentChatPage)));
}

/**
 * Handles chat tags update events
 */
async function handleTagsEvent(currentChatId: string): Promise<void> {
	await getChatById(localStorage.token, currentChatId);
	allTags.set(await getAllTags(localStorage.token));
}

/**
 * Handles message content append events
 */
function handleMessageEvent(
	message: ChatMessage,
	data: { content: string },
	config: ChatEventHandlerConfig
): void {
	message.content += data.content;
}

/**
 * Handles message content replace events
 */
function handleReplaceEvent(
	message: ChatMessage,
	data: { content: string },
	config: ChatEventHandlerConfig
): void {
	message.content = data.content;
}

/**
 * Handles action events (like continue)
 */
function handleActionEvent(data: { action: string }): void {
	if (data.action === 'continue') {
		const continueButton = document.getElementById('continue-response-button');
		continueButton?.click();
	}
}

/**
 * Handles confirmation dialog events
 */
function handleConfirmationEvent(
	data: { title: string; message: string },
	cb?: (result: any) => void
): { type: 'confirmation'; data: typeof data; callback: typeof cb } {
	return {
		type: 'confirmation',
		data,
		callback: cb
	};
}

/**
 * Handles code execution events
 */
async function handleExecuteEvent(
	data: { code: string },
	cb?: (result: any) => void
): Promise<void> {
	try {
		// Use Function constructor to evaluate code safely
		const asyncFunction = new Function(`return (async () => { ${data.code} })()`);
		const result = await asyncFunction();

		if (cb) {
			cb(result);
		}
	} catch (error) {
		console.error('Error executing code:', error);
	}
}

/**
 * Handles input dialog events
 */
function handleInputEvent(
	data: { title: string; message: string; placeholder?: string; value?: string },
	cb?: (result: any) => void
): { type: 'input'; data: typeof data; callback: typeof cb } {
	return {
		type: 'input',
		data,
		callback: cb
	};
}

/**
 * Handles notification toast events
 */
function handleNotificationEvent(data: { type?: string; content?: string }): void {
	const toastType = data?.type ?? 'info';
	const toastContent = data?.content ?? '';

	switch (toastType) {
		case 'success':
			toast.success(toastContent);
			break;
		case 'error':
			toast.error(toastContent);
			break;
		case 'warning':
			toast.warning(toastContent);
			break;
		default:
			toast.info(toastContent);
	}
}

/**
 * Handles chat completion streaming events
 */
export function handleStreamingContent(
	message: ChatMessage,
	data: any,
	config: any,
	settings: any,
	eventTarget: EventTarget
): void {
	const { choices, content, sources, selected_model_id, usage } = data;

	if (sources) {
		message.sources = sources;
	}

	if (choices) {
		if (choices[0]?.message?.content) {
			// Non-stream response
			message.content += choices[0].message.content;
		} else {
			// Stream response
			const value = choices[0]?.delta?.content ?? '';
			if (message.content === '' && value === '\n') {
				console.log('Empty response');
			} else {
				message.content += value;

				// Haptic feedback
				if (navigator.vibrate && (settings?.hapticFeedback ?? false)) {
					navigator.vibrate(5);
				}

				// TTS event dispatch
				dispatchTTSEvent(message, config, eventTarget);
			}
		}
	}

	if (content) {
		message.content = content;

		if (navigator.vibrate && (settings?.hapticFeedback ?? false)) {
			navigator.vibrate(5);
		}

		dispatchTTSEvent(message, config, eventTarget);
	}

	if (selected_model_id) {
		message.selectedModelId = selected_model_id;
		message.arena = true;
	}

	if (usage) {
		message.usage = usage;
	}
}

/**
 * Dispatches TTS events for sentence-by-sentence reading
 */
function dispatchTTSEvent(message: ChatMessage, config: any, eventTarget: EventTarget): void {
	const splitOn = config?.audio?.tts?.split_on ?? 'punctuation';
	const messageContentParts = getMessageContentParts(message.content, splitOn);
	messageContentParts.pop();

	// Dispatch only the last sentence if it hasn't been dispatched before
	if (
		messageContentParts.length > 0 &&
		messageContentParts[messageContentParts.length - 1] !== message.lastSentence
	) {
		message.lastSentence = messageContentParts[messageContentParts.length - 1];
		eventTarget.dispatchEvent(
			new CustomEvent('chat', {
				detail: {
					id: message.id,
					content: messageContentParts[messageContentParts.length - 1]
				}
			})
		);
	}
}

/**
 * Dispatches final TTS event when message is complete
 */
export function dispatchFinalTTSEvent(
	message: ChatMessage,
	config: any,
	eventTarget: EventTarget
): void {
	const splitOn = config?.audio?.tts?.split_on ?? 'punctuation';
	const lastPart = getMessageContentParts(message.content, splitOn)?.at(-1) ?? '';

	if (lastPart) {
		eventTarget.dispatchEvent(
			new CustomEvent('chat', {
				detail: { id: message.id, content: lastPart }
			})
		);
	}

	eventTarget.dispatchEvent(
		new CustomEvent('chat:finish', {
			detail: {
				id: message.id,
				content: message.content
			}
		})
	);
}

/**
 * Creates a message handler for iframe communication
 */
export function createIframeMessageHandler(
	onPromptInput: (text: string) => void,
	onPromptSubmit: (text: string) => void
) {
	return async (event: MessageEvent) => {
		if (event.origin !== window.origin) {
			return;
		}

		const { type, text } = event.data;

		switch (type) {
			case 'input:prompt':
				console.debug('Iframe prompt input:', text);
				onPromptInput(text);
				break;

			case 'action:submit':
				console.debug('Iframe submit action');
				onPromptSubmit(text);
				break;

			case 'input:prompt:submit':
				console.debug('Iframe prompt submit:', text);
				onPromptSubmit(text);
				break;
		}
	};
}
