import { v4 as uuidv4 } from 'uuid';
import { get, type Writable } from 'svelte/store';
import { tick } from 'svelte';
import { toast } from 'svelte-sonner';
import type { i18n as i18nType } from 'i18next';
import type { Model } from '$lib/stores';

import { stopTask } from '$lib/apis';

import type { ChatHistory, ChatMessage } from './types';

export interface MessageActionsOptions {
	chatId: Writable<string>;
	models: Writable<Model[]>;
	i18n: Writable<i18nType>;
}

export interface MessageActionsState {
	history: ChatHistory;
	selectedModels: string[];
	taskId: string | null;
	autoScroll: boolean;
}

export function createMessageActions(
	options: MessageActionsOptions,
	getState: () => MessageActionsState,
	setState: (updates: Partial<MessageActionsState>) => void,
	sendPrompt: (history: ChatHistory, prompt: string, parentId: string, opts?: any) => Promise<void>,
	sendPromptToModel: (history: ChatHistory, model: any, responseId: string, chatId: string) => Promise<void>,
	saveChatHandler: (chatId: string, history: ChatHistory) => Promise<void>,
	initChatHandler: (history: ChatHistory) => Promise<string>,
	scrollToBottom: () => void
) {
	const { chatId, models, i18n } = options;

	// ============================================
	// Stop Response
	// ============================================
	function stopResponseHandler(): void {
		const state = getState();
		
		if (state.taskId) {
			stopTask(localStorage.token, state.taskId).then((res) => {
				if (res) {
					setState({ taskId: null });
					
					const newHistory = { ...state.history };
					if (newHistory.currentId) {
						newHistory.messages[newHistory.currentId].done = true;
						setState({ history: newHistory });
					}
					
					if (state.autoScroll) scrollToBottom();
				}
			});
		}
	}

	// ============================================
	// Regenerate Response
	// ============================================
	async function regenerateResponse(message: ChatMessage): Promise<void> {
		const state = getState();
		if (!state.history.currentId) return;
		
		const userMessage = state.history.messages[message.parentId!];
		await sendPrompt(state.history, userMessage.content, userMessage.id, {
			modelId: message.model,
			modelIdx: message.modelIdx
		});
	}

	// ============================================
	// Continue Response
	// ============================================
	async function continueResponseHandler(): Promise<void> {
		const state = getState();
		const $models = get(models);
		const $chatId = get(chatId);

		if (!state.history.currentId || !state.history.messages[state.history.currentId].done) {
			return;
		}

		const msg = state.history.messages[state.history.currentId];
		const newHistory = { ...state.history };
		newHistory.messages[state.history.currentId] = { ...msg, done: false };
		setState({ history: newHistory });

		await tick();

		const model = $models.find((m: any) => m.id === (msg.selectedModelId ?? msg.model));
		if (model) {
			await sendPromptToModel(newHistory, model, msg.id, $chatId);
		}
	}

	// ============================================
	// Submit Message (from Messages component)
	// ============================================
	async function submitMessageHandler(parentId: string, text: string): Promise<void> {
		const state = getState();

		const msg: ChatMessage = {
			id: uuidv4(),
			parentId,
			childrenIds: [],
			role: 'user',
			content: text,
			timestamp: Math.floor(Date.now() / 1000)
		};

		const newHistory = { ...state.history };
		if (parentId) {
			newHistory.messages[parentId].childrenIds.push(msg.id);
		}
		newHistory.messages[msg.id] = msg;
		newHistory.currentId = msg.id;
		setState({ history: newHistory });

		await tick();
		await sendPrompt(newHistory, text, msg.id);
	}

	// ============================================
	// Show Message (navigate to message)
	// ============================================
	async function showMessageHandler(message: ChatMessage): Promise<void> {
		const state = getState();
		const $chatId = get(chatId);

		let id = message.id;
		while (state.history.messages[id].childrenIds.length) {
			id = state.history.messages[id].childrenIds.at(-1)!;
		}

		const newHistory = { ...state.history, currentId: id };
		setState({ history: newHistory });

		await tick();
		document.getElementById(`message-${message.id}`)?.scrollIntoView({ behavior: 'smooth' });
		await saveChatHandler($chatId, newHistory);
	}

	// ============================================
	// Merge Responses (MoA)
	// ============================================
	async function mergeResponsesHandler(messageId: string, responses: any[], _chatId: string): Promise<void> {
		const state = getState();

		const message = state.history.messages[messageId];
		const newHistory = { ...state.history };
		newHistory.messages[messageId] = {
			...message,
			merged: { status: true, content: '' }
		};
		setState({ history: newHistory });

		await saveChatHandler(_chatId, newHistory);
	}

	// ============================================
	// Add Messages (bulk add)
	// ============================================
	async function addMessagesHandler({ modelId, parentId, messages: msgs }: any): Promise<void> {
		const state = getState();
		const $models = get(models);
		const $chatId = get(chatId);

		const model = $models.find((m: any) => m.id === modelId);
		if (!model) return;

		const newHistory = { ...state.history };
		let parent = newHistory.messages[parentId];
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
				...(msg.role === 'assistant'
					? { done: true, model: model.id, modelName: model.name ?? model.id, modelIdx: 0 }
					: {})
			};

			if (parent) {
				parent.childrenIds.push(id);
				newHistory.messages[parent.id] = parent;
			}
			newHistory.messages[id] = newMsg;
			parent = newMsg;
			pid = id;
		}

		newHistory.currentId = pid;
		setState({ history: newHistory });

		await tick();
		if (state.autoScroll) scrollToBottom();
		await saveChatHandler($chatId, newHistory);
	}

	// ============================================
	// Create Message Pair (for templates)
	// ============================================
	async function createMessagePairHandler(userPrompt: string): Promise<void> {
		const state = getState();
		const $models = get(models);
		const $chatId = get(chatId);
		const $i18n = get(i18n);

		if (!state.selectedModels.length) {
			toast.error($i18n.t('Model not selected'));
			return;
		}

		const model = $models.find((m: any) => m.id === state.selectedModels[0]);
		if (!model) return;

		const msgs = createMessagesListFromHistory(state.history, state.history.currentId);
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

		const newHistory = { ...state.history };
		if (parent) {
			parent.childrenIds.push(userId);
			newHistory.messages[parent.id] = parent;
		}
		newHistory.messages[userId] = userMsg;
		newHistory.messages[respId] = respMsg;
		newHistory.currentId = respId;
		setState({ history: newHistory });

		await tick();
		if (state.autoScroll) scrollToBottom();

		if (msgs.length) {
			await saveChatHandler($chatId, newHistory);
		} else {
			await initChatHandler(newHistory);
		}
	}

	// ============================================
	// Chat Action Handler (generic)
	// ============================================
	async function chatActionHandler(
		chatIdVal: string,
		actionId: string,
		modelId: string,
		responseId: string,
		event?: any
	): Promise<void> {
		const state = getState();
		await saveChatHandler(chatIdVal, state.history);
	}

	// ============================================
	// Utility
	// ============================================
	function createMessagesListFromHistory(history: ChatHistory, endId: string | null): ChatMessage[] {
		const messages: ChatMessage[] = [];
		if (!endId) return messages;

		let currentId: string | null = endId;
		while (currentId) {
			const msg = history.messages[currentId];
			if (msg) {
				messages.unshift(msg);
				currentId = msg.parentId;
			} else {
				break;
			}
		}
		return messages;
	}

	return {
		stopResponseHandler,
		regenerateResponse,
		continueResponseHandler,
		submitMessageHandler,
		showMessageHandler,
		mergeResponsesHandler,
		addMessagesHandler,
		createMessagePairHandler,
		chatActionHandler
	};
}
