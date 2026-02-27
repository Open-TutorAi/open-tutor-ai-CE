import { v4 as uuidv4 } from 'uuid';
import type { ChatHistory, ChatMessage } from './types';

export function createEmptyHistory(): ChatHistory {
	return {
		messages: {},
		currentId: null
	};
}

/**
 * Gets all messages in a conversation thread from root to the specified message
 */
export function getMessageThread(history: ChatHistory, messageId: string | null): ChatMessage[] {
	if (!messageId || !history.messages[messageId]) {
		return [];
	}

	const thread: ChatMessage[] = [];
	let currentId: string | null = messageId;

	// Traverse up to root
	const messageIds: string[] = [];
	while (currentId && history.messages[currentId]) {
		messageIds.unshift(currentId);
		currentId = history.messages[currentId].parentId;
	}

	// Build thread from root to message
	for (const id of messageIds) {
		thread.push(history.messages[id]);
	}

	return thread;
}

/**
 * Gets the last message in the current conversation thread
 */
export function getLastMessage(history: ChatHistory): ChatMessage | null {
	if (!history.currentId) return null;

	let currentId: string | null = history.currentId;
	let lastMessage = history.messages[currentId];

	// Find the deepest child in the current branch
	while (lastMessage.childrenIds.length > 0) {
		currentId = lastMessage.childrenIds[lastMessage.childrenIds.length - 1];
		lastMessage = history.messages[currentId];
	}

	return lastMessage;
}

/**
 * Gets all system messages from history
 */
export function getSystemMessages(history: ChatHistory): ChatMessage[] {
	return Object.values(history.messages).filter((msg) => msg.role === 'system');
}

/**
 * Gets combined system prompt from all system messages
 */
export function getCombinedSystemPrompt(history: ChatHistory): string {
	const systemMessages = getSystemMessages(history);
	if (systemMessages.length === 0) return '';

	// Sort by timestamp if available
	systemMessages.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));

	return systemMessages.map((msg) => msg.content).join('\n\n');
}

/**
 * Adds a system message to history
 */
export function addSystemMessage(history: ChatHistory, content: string): ChatHistory {
	const systemMessageId = uuidv4();
	history.messages[systemMessageId] = {
		id: systemMessageId,
		parentId: null,
		childrenIds: [],
		role: 'system',
		content,
		done: true,
		timestamp: Date.now()
	};

	console.log('Added system message to chat history');
	return history;
}

/**
 * Appends a child message to a parent message
 */
export function appendChildMessage(
	history: ChatHistory,
	parentId: string,
	childMessage: ChatMessage
): ChatHistory {
	if (parentId && history.messages[parentId]) {
		history.messages[parentId].childrenIds.push(childMessage.id);
	}

	history.messages[childMessage.id] = childMessage;
	history.currentId = childMessage.id;

	return history;
}

/**
 * Updates a message in history
 */
export function updateMessage(
	history: ChatHistory,
	messageId: string,
	updates: Partial<ChatMessage>
): ChatHistory {
	if (history.messages[messageId]) {
		history.messages[messageId] = {
			...history.messages[messageId],
			...updates
		};
	}

	return history;
}

/**
 * Marks a message as done
 */
export function markMessageDone(history: ChatHistory, messageId: string): ChatHistory {
	return updateMessage(history, messageId, { done: true });
}

/**
 * Marks a message with an error
 */
export function markMessageError(
	history: ChatHistory,
	messageId: string,
	errorContent: string
): ChatHistory {
	return updateMessage(history, messageId, {
		done: true,
		error: { content: errorContent }
	});
}

/**
 * Gets the parent message of a given message
 */
export function getParentMessage(history: ChatHistory, messageId: string): ChatMessage | null {
	const message = history.messages[messageId];
	if (!message || !message.parentId) return null;

	return history.messages[message.parentId] || null;
}

/**
 * Gets all children messages of a given message
 */
export function getChildrenMessages(history: ChatHistory, messageId: string): ChatMessage[] {
	const message = history.messages[messageId];
	if (!message) return [];

	return message.childrenIds
		.map((id) => history.messages[id])
		.filter((msg): msg is ChatMessage => msg !== undefined);
}

/**
 * Gets sibling messages (messages with the same parent)
 */
export function getSiblingMessages(history: ChatHistory, messageId: string): ChatMessage[] {
	const message = history.messages[messageId];
	if (!message || !message.parentId) return [];

	const parent = history.messages[message.parentId];
	if (!parent) return [];

	return parent.childrenIds
		.map((id) => history.messages[id])
		.filter((msg): msg is ChatMessage => msg !== undefined);
}

/**
 * Navigates to a sibling message (for branching conversations)
 */
export function navigateToSibling(
	history: ChatHistory,
	messageId: string,
	direction: 'next' | 'prev'
): ChatHistory {
	const siblings = getSiblingMessages(history, messageId);
	const currentIndex = siblings.findIndex((msg) => msg.id === messageId);

	if (currentIndex === -1) return history;

	let newIndex: number;
	if (direction === 'next') {
		newIndex = currentIndex < siblings.length - 1 ? currentIndex + 1 : currentIndex;
	} else {
		newIndex = currentIndex > 0 ? currentIndex - 1 : currentIndex;
	}

	if (newIndex !== currentIndex) {
		// Navigate to the deepest child of the sibling
		let targetId = siblings[newIndex].id;
		while (history.messages[targetId].childrenIds.length > 0) {
			targetId = history.messages[targetId].childrenIds[
				history.messages[targetId].childrenIds.length - 1
			];
		}
		history.currentId = targetId;
	}

	return history;
}

/**
 * Gets the message count in history (excluding system messages)
 */
export function getMessageCount(history: ChatHistory): number {
	return Object.values(history.messages).filter((msg) => msg.role !== 'system').length;
}

/**
 * Checks if history has any user messages
 */
export function hasUserMessages(history: ChatHistory): boolean {
	return Object.values(history.messages).some((msg) => msg.role === 'user');
}

/**
 * Checks if the current response is still being generated
 */
export function isResponseInProgress(history: ChatHistory): boolean {
	if (!history.currentId) return false;

	const currentMessage = history.messages[history.currentId];
	return currentMessage?.role === 'assistant' && currentMessage?.done !== true;
}

/**
 * Creates a message pair (user + assistant placeholder)
 */
export function createMessagePair(
	history: ChatHistory,
	userPrompt: string,
	modelId: string,
	modelName: string
): {
	history: ChatHistory;
	userMessageId: string;
	responseMessageId: string;
} {
	const messages = getMessageThread(history, history.currentId);
	const parentMessage = messages.length !== 0 ? messages.at(-1) : null;

	const userMessageId = uuidv4();
	const responseMessageId = uuidv4();

	const userMessage: ChatMessage = {
		id: userMessageId,
		parentId: parentMessage ? parentMessage.id : null,
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
		modelName: modelName,
		modelIdx: 0,
		timestamp: Math.floor(Date.now() / 1000)
	};

	// Update parent if exists
	if (parentMessage) {
		parentMessage.childrenIds.push(userMessageId);
		history.messages[parentMessage.id] = parentMessage;
	}

	history.messages[userMessageId] = userMessage;
	history.messages[responseMessageId] = responseMessage;
	history.currentId = responseMessageId;

	return { history, userMessageId, responseMessageId };
}

/**
 * Clones history for safe manipulation
 */
export function cloneHistory(history: ChatHistory): ChatHistory {
	return JSON.parse(JSON.stringify(history));
}
