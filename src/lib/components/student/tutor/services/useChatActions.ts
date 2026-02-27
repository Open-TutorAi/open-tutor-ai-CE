import { get } from 'svelte/store';
import { tick } from 'svelte';
import { v4 as uuidv4 } from 'uuid';
import { toast } from 'svelte-sonner';

import {
	chatId,
	models,
	settings,
	socket,
	temporaryChatEnabled,
	currentChatPage,
	chats,
	config,
	user,
	type Model
} from '$lib/stores';

import { generateOpenAIChatCompletion } from '$lib/apis/openai';
import { getChatList, updateChatById } from '$lib/apis/chats';
import { generateMoACompletion, stopTask, chatAction } from '$lib/apis';
import { createOpenAITextStream } from '$lib/apis/streaming';
import { queryMemory } from '$lib/apis/memories';
import { getAndUpdateUserLocation } from '$lib/apis/users';
import { TUTOR_BASE_URL } from '$lib/constants';

import {
	createMessagesList,
	copyToClipboard,
	getPromptVariables
} from '$lib/utils';

import type { ChatHistory, ChatMessage } from './types';

import {
	createUserMessage,
	createResponseMessage,
	addMessageToHistory,
	getAvatarPersonality,
	buildSystemMessage,
	prepareMessagesForApi,
	handleChatCompleted,
	cloneHistory,
	getCombinedSystemPrompt,
	dispatchFinalTTSEvent
} from './index';

export interface ChatActionsConfig {
	history: ChatHistory;
	selectedModels: string[];
	atSelectedModel?: Model;
	selectedToolIds: string[];
	chatFiles: any[];
	params: any;
	avatarActive: boolean;
	imageGenerationEnabled: boolean;
	codeInterpreterEnabled: boolean;
	webSearchEnabled: boolean;
	eventTarget: EventTarget;
	onHistoryUpdate: (history: ChatHistory) => void;
	onTaskIdUpdate: (taskId: string | null) => void;
	scrollToBottom: () => void;
}

/**
 * Regenerates a response for a message
 */
export async function regenerateResponse(
	message: ChatMessage,
	config: ChatActionsConfig,
	sendPromptFn: (history: ChatHistory, prompt: string, parentId: string, options?: any) => Promise<void>
): Promise<void> {
	if (!config.history.currentId) return;

	const userMessage = config.history.messages[message.parentId!];
	const userPrompt = userMessage.content;

	const userModels = userMessage?.models ?? [...config.selectedModels];

	if (userModels.length === 1) {
		// Single model - sendPrompt will auto-select
		await sendPromptFn(config.history, userPrompt, userMessage.id);
	} else {
		// Multiple models - use the response message's model
		await sendPromptFn(config.history, userPrompt, userMessage.id, {
			modelId: message.model,
			modelIdx: message.modelIdx
		});
	}
}

/**
 * Continues generating a response
 */
export async function continueResponse(
	config: ChatActionsConfig,
	sendPromptSocketFn: (history: ChatHistory, model: Model, responseMessageId: string, chatIdValue: string) => Promise<void>
): Promise<void> {
	const _chatId = get(chatId);
	const $models = get(models);

	if (!config.history.currentId) return;

	const responseMessage = config.history.messages[config.history.currentId];
	if (!responseMessage.done) return;

	// Mark as not done to continue
	responseMessage.done = false;
	config.onHistoryUpdate(config.history);
	await tick();

	const model = $models.find(
		(m) => m.id === (responseMessage?.selectedModelId ?? responseMessage.model)
	);

	if (model) {
		await sendPromptSocketFn(config.history, model, responseMessage.id, _chatId);
	}
}

/**
 * Submits a new message in the conversation
 */
export async function submitMessage(
	parentId: string,
	messagePrompt: string,
	config: ChatActionsConfig,
	sendPromptFn: (history: ChatHistory, prompt: string, parentId: string, options?: any) => Promise<void>
): Promise<void> {
	const userMessage = createUserMessage(messagePrompt, parentId, [], config.selectedModels);

	// Update parent's children
	if (parentId && config.history.messages[parentId]) {
		config.history.messages[parentId].childrenIds.push(userMessage.id);
	}

	config.history.messages[userMessage.id] = userMessage;
	config.history.currentId = userMessage.id;
	config.onHistoryUpdate(config.history);

	await tick();
	await sendPromptFn(config.history, messagePrompt, userMessage.id);
}

/**
 * Merges multiple model responses
 */
export async function mergeResponses(
	messageId: string,
	responses: any[],
	_chatId: string,
	config: ChatActionsConfig,
	saveChatFn: (chatId: string, history: ChatHistory) => Promise<void>
): Promise<void> {
	const $settings = get(settings);
	const message = config.history.messages[messageId];

	const mergedResponse = { status: true, content: '' };
	message.merged = mergedResponse;
	config.history.messages[messageId] = message;
	config.onHistoryUpdate(config.history);

	try {
		const [res] = await generateMoACompletion(
			localStorage.token,
			message.model!,
			config.history.messages[message.parentId!].content,
			responses
		);

		if (res?.ok && res.body) {
			const textStream = await createOpenAITextStream(res.body, $settings.splitLargeChunks);

			for await (const update of textStream) {
				const { value, done, error } = update;
				if (error || done) break;

				if (mergedResponse.content === '' && value === '\n') continue;

				mergedResponse.content += value;
				config.history.messages[messageId] = message;
				config.onHistoryUpdate(config.history);

				config.scrollToBottom();
			}

			await saveChatFn(_chatId, config.history);
		}
	} catch (e) {
		console.error('Error merging responses:', e);
	}
}

/**
 * Stops the current response generation
 */
export async function stopResponseGeneration(
	taskId: string | null,
	config: ChatActionsConfig
): Promise<void> {
	if (!taskId) return;

	const res = await stopTask(localStorage.token, taskId).catch(() => null);

	if (res) {
		config.onTaskIdUpdate(null);

		if (config.history.currentId) {
			const responseMessage = config.history.messages[config.history.currentId];
			responseMessage.done = true;
			config.history.messages[config.history.currentId] = responseMessage;
			config.onHistoryUpdate(config.history);
			config.scrollToBottom();
		}
	}
}

/**
 * Handles chat action events (like feedback, etc.)
 */
export async function handleChatAction(
	chatIdValue: string,
	actionId: string,
	modelId: string,
	responseMessageId: string,
	config: ChatActionsConfig,
	event?: any
): Promise<void> {
	const $models = get(models);
	const $socket = get(socket);
	const $temporaryChatEnabled = get(temporaryChatEnabled);

	const messages = createMessagesList(config.history, responseMessageId);

	const res = await chatAction(localStorage.token, actionId, {
		model: modelId,
		messages: messages.map((m) => ({
			id: m.id,
			role: m.role,
			content: m.content,
			info: m.info ?? undefined,
			timestamp: m.timestamp,
			...(m.sources ? { sources: m.sources } : {})
		})),
		...(event ? { event } : {}),
		model_item: $models.find((m) => m.id === modelId),
		chat_id: chatIdValue,
		session_id: $socket?.id,
		id: responseMessageId
	}).catch((error) => {
		toast.error(`${error}`);
		return null;
	});

	if (res?.messages) {
		for (const message of res.messages) {
			config.history.messages[message.id] = {
				...config.history.messages[message.id],
				...(config.history.messages[message.id]?.content !== message.content
					? { originalContent: config.history.messages[message.id]?.content }
					: {}),
				...message
			};
		}
		config.onHistoryUpdate(config.history);
	}

	// Save chat if not temporary
	if (get(chatId) === chatIdValue && !$temporaryChatEnabled) {
		await updateChatById(localStorage.token, chatIdValue, {
			models: config.selectedModels,
			messages,
			history: config.history,
			params: config.params,
			files: config.chatFiles
		});

		currentChatPage.set(1);
		chats.set(await getChatList(localStorage.token, get(currentChatPage)));
	}
}

/**
 * Creates a message pair (user + assistant placeholder)
 */
export async function createMessagePair(
	userPrompt: string,
	config: ChatActionsConfig,
	initChatFn: (history: ChatHistory) => Promise<string | null>,
	saveChatFn: (chatId: string, history: ChatHistory) => Promise<void>,
	i18n: any
): Promise<{ userMessageId: string; responseMessageId: string } | null> {
	const $models = get(models);

	if (config.selectedModels.length === 0) {
		toast.error(i18n.t('Model not selected'));
		return null;
	}

	const modelId = config.selectedModels[0];
	const model = $models.find((m) => m.id === modelId);
	if (!model) return null;

	const messages = createMessagesList(config.history, config.history.currentId);
	const parentMessage = messages.at(-1) ?? null;

	const userMessageId = uuidv4();
	const responseMessageId = uuidv4();

	const userMessage: ChatMessage = {
		id: userMessageId,
		parentId: parentMessage?.id ?? null,
		childrenIds: [responseMessageId],
		role: 'user',
		content: userPrompt || `[PROMPT] ${userMessageId}`,
		timestamp: Math.floor(Date.now() / 1000)
	};

	const responseMessage: ChatMessage = {
		id: responseMessageId,
		parentId: userMessageId,
		childrenIds: [],
		role: 'assistant',
		content: `[RESPONSE] ${responseMessageId}`,
		done: true,
		model: modelId,
		modelName: model.name ?? model.id,
		modelIdx: 0,
		timestamp: Math.floor(Date.now() / 1000)
	};

	// Update parent
	if (parentMessage) {
		parentMessage.childrenIds.push(userMessageId);
		config.history.messages[parentMessage.id] = parentMessage;
	}

	config.history.messages[userMessageId] = userMessage;
	config.history.messages[responseMessageId] = responseMessage;
	config.history.currentId = responseMessageId;
	config.onHistoryUpdate(config.history);

	await tick();
	config.scrollToBottom();

	// Initialize or save
	if (messages.length === 0) {
		await initChatFn(config.history);
	} else {
		await saveChatFn(get(chatId), config.history);
	}

	return { userMessageId, responseMessageId };
}

/**
 * Adds multiple messages to the conversation
 */
export async function addMessages(
	options: { modelId: string; parentId: string; messages: Partial<ChatMessage>[] },
	config: ChatActionsConfig,
	initChatFn: (history: ChatHistory) => Promise<string | null>,
	saveChatFn: (chatId: string, history: ChatHistory) => Promise<void>
): Promise<void> {
	const $models = get(models);
	const model = $models.find((m) => m.id === options.modelId);
	if (!model) return;

	let parentMessage = config.history.messages[options.parentId];
	let currentParentId = parentMessage?.id ?? null;

	for (const message of options.messages) {
		const messageId = uuidv4();

		const newMessage: ChatMessage = {
			id: messageId,
			parentId: currentParentId,
			childrenIds: [],
			role: message.role ?? 'user',
			content: message.content ?? '',
			timestamp: Math.floor(Date.now() / 1000),
			...message,
			...(message.role === 'assistant'
				? { done: true, model: model.id, modelName: model.name ?? model.id, modelIdx: 0 }
				: {})
		};

		if (parentMessage) {
			parentMessage.childrenIds.push(messageId);
			config.history.messages[parentMessage.id] = parentMessage;
		}

		config.history.messages[messageId] = newMessage;
		parentMessage = newMessage;
		currentParentId = messageId;
	}

	config.history.currentId = currentParentId;
	config.onHistoryUpdate(config.history);

	await tick();
	config.scrollToBottom();

	if (options.messages.length === 0) {
		await initChatFn(config.history);
	} else {
		await saveChatFn(get(chatId), config.history);
	}
}

/**
 * Shows a specific message and navigates to it
 */
export async function showMessage(
	message: ChatMessage,
	config: ChatActionsConfig,
	saveChatFn: (chatId: string, history: ChatHistory) => Promise<void>
): Promise<void> {
	const _chatId = get(chatId);
	let _messageId = message.id;

	// Navigate to deepest child
	while (config.history.messages[_messageId].childrenIds.length !== 0) {
		_messageId = config.history.messages[_messageId].childrenIds.at(-1)!;
	}

	config.history.currentId = _messageId;
	config.onHistoryUpdate(config.history);

	await tick();
	await tick();
	await tick();

	document.getElementById(`message-${message.id}`)?.scrollIntoView({ behavior: 'smooth' });

	await tick();
	await saveChatFn(_chatId, config.history);
}

/**
 * Handles OpenAI API errors
 */
export function handleOpenAIError(
	error: any,
	responseMessage: ChatMessage,
	config: ChatActionsConfig,
	i18n: any
): void {
	let errorMessage = '';

	if (error?.detail) {
		toast.error(error.detail);
		errorMessage = error.detail;
	} else if (error?.error?.message) {
		toast.error(error.error.message);
		errorMessage = error.error.message;
	} else if (error?.error) {
		toast.error(error.error);
		errorMessage = error.error;
	} else if (error?.message) {
		toast.error(error.message);
		errorMessage = error.message;
	}

	responseMessage.error = {
		content: i18n.t('Uh-oh! There was an issue with the response.') + '\n' + errorMessage
	};
	responseMessage.done = true;

	if (responseMessage.statusHistory) {
		responseMessage.statusHistory = responseMessage.statusHistory.filter(
			(status: any) => status.action !== 'knowledge_search'
		);
	}

	config.history.messages[responseMessage.id] = responseMessage;
	config.onHistoryUpdate(config.history);
}
