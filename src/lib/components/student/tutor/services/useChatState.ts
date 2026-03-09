import { writable, derived, get, type Writable, type Readable } from 'svelte/store';
import { tick } from 'svelte';
import { v4 as uuidv4 } from 'uuid';

import { chatId, chatTitle, settings, temporaryChatEnabled, currentChatPage, chats } from '$lib/stores';
import { getChatById, getChatList, getTagsById, updateChatById } from '$lib/apis/chats';
import { getUserSettings } from '$lib/apis/users';
import { convertMessagesToHistory } from '$lib/utils';

import type { ChatHistory, ChatMessage, FileUploadItem, ChatFile } from './types';
import { createEmptyHistory, cloneHistory, processPendingSupportData } from './index';

export interface ChatState {
	// Core state
	history: Writable<ChatHistory>;
	chat: Writable<any>; // Chat object from API
	tags: Writable<any[]>; // Tag objects from API
	
	// Input state
	prompt: Writable<string>;
	files: Writable<FileUploadItem[]>;
	chatFiles: Writable<ChatFile[]>;
	params: Writable<Record<string, any>>; // URL parameters
	
	// UI state
	loading: Writable<boolean>;
	autoScroll: Writable<boolean>;
	taskId: Writable<string | null>;
	
	// Derived state
	currentMessage: Readable<ChatMessage | null>;
	hasMessages: Readable<boolean>;
	isResponseInProgress: Readable<boolean>;
}

export interface ChatStateActions {
	// History management
	resetHistory: () => void;
	updateMessage: (messageId: string, updates: Partial<ChatMessage>) => void;
	addMessage: (message: ChatMessage, parentId: string | null) => void;
	setCurrentId: (messageId: string) => void;
	
	// Chat management
	loadChat: (chatIdValue: string, token: string) => Promise<boolean>;
	saveChat: (chatIdValue: string, selectedModels: string[]) => Promise<void>;
	initNewChat: () => Promise<void>;
	
	// Input management
	resetInput: () => void;
	setPrompt: (value: string) => void;
	addFile: (file: FileUploadItem) => void;
	removeFile: (itemId: string) => void;
	clearFiles: () => void;
	mergeChatFiles: (newFiles: FileUploadItem[]) => void;
	
	// UI management
	setLoading: (value: boolean) => void;
	setAutoScroll: (value: boolean) => void;
	setTaskId: (value: string | null) => void;
}

/**
 * Creates a chat state composable with all necessary state and actions
 */
export function createChatState(): ChatState & ChatStateActions {
	// Core state stores
	const history = writable<ChatHistory>(createEmptyHistory());
	const chat = writable<any>(null);
	const tags = writable<any[]>([]);
	
	// Input state stores
	const prompt = writable<string>('');
	const files = writable<FileUploadItem[]>([]);
	const chatFiles = writable<ChatFile[]>([]);
	const params = writable<any>({});
	
	// UI state stores
	const loading = writable<boolean>(false);
	const autoScroll = writable<boolean>(true);
	const taskId = writable<string | null>(null);
	
	// Derived state
	const currentMessage = derived(history, ($history) => {
		if (!$history.currentId) return null;
		return $history.messages[$history.currentId] ?? null;
	});
	
	const hasMessages = derived(history, ($history) => {
		return Object.keys($history.messages).filter(
			(id) => $history.messages[id].role !== 'system'
		).length > 0;
	});
	
	const isResponseInProgress = derived([history, currentMessage], ([$history, $currentMessage]) => {
		if (!$currentMessage) return false;
		return $currentMessage.role === 'assistant' && $currentMessage.done !== true;
	});
	
	// Actions
	function resetHistory() {
		history.set(createEmptyHistory());
	}
	
	function updateMessage(messageId: string, updates: Partial<ChatMessage>) {
		history.update(($history) => {
			if ($history.messages[messageId]) {
				$history.messages[messageId] = {
					...$history.messages[messageId],
					...updates
				};
			}
			return $history;
		});
	}
	
	function addMessage(message: ChatMessage, parentId: string | null) {
		history.update(($history) => {
			// Add message to history
			$history.messages[message.id] = message;
			$history.currentId = message.id;
			
			// Update parent's childrenIds
			if (parentId && $history.messages[parentId]) {
				$history.messages[parentId].childrenIds = [
					...$history.messages[parentId].childrenIds,
					message.id
				];
			}
			
			return $history;
		});
	}
	
	function setCurrentId(messageId: string) {
		history.update(($history) => {
			$history.currentId = messageId;
			return $history;
		});
	}
	
	async function loadChat(chatIdValue: string, token: string): Promise<boolean> {
		chatId.set(chatIdValue);
		
		const chatData = await getChatById(token, chatIdValue).catch(() => null);
		if (!chatData) return false;
		
		chat.set(chatData);
		
		const chatTags = await getTagsById(token, chatIdValue).catch(() => []);
		tags.set(chatTags);
		
		const chatContent = chatData.chat;
		if (!chatContent) return false;
		
		// Set history
		const loadedHistory = chatContent?.history ?? convertMessagesToHistory(chatContent.messages);
		history.set(loadedHistory);
		
		// Set title
		chatTitle.set(chatContent.title);
		
		// Load user settings
		const userSettings = await getUserSettings(token);
		const settingsData = userSettings?.ui ?? JSON.parse(localStorage.getItem('settings') ?? '{}');
		settings.set(settingsData);
		
		// Set other state
		params.set(chatContent?.params ?? {});
		chatFiles.set(chatContent?.files ?? []);
		autoScroll.set(true);
		
		// Mark current message as done
		await tick();
		const currentHistory = get(history);
		if (currentHistory.currentId) {
			updateMessage(currentHistory.currentId, { done: true });
		}
		
		return true;
	}
	
	async function saveChat(chatIdValue: string, selectedModels: string[]): Promise<void> {
		const currentChatId = get(chatId);
		const tempEnabled = get(temporaryChatEnabled);
		
		if (currentChatId !== chatIdValue || tempEnabled) return;
		
		const currentHistory = get(history);
		const currentParams = get(params);
		const currentChatFiles = get(chatFiles);
		
		const updatedChat = await updateChatById(localStorage.token, chatIdValue, {
			models: selectedModels,
			history: currentHistory,
			messages: createMessagesList(currentHistory, currentHistory.currentId),
			params: currentParams,
			files: currentChatFiles
		});
		
		chat.set(updatedChat);
		currentChatPage.set(1);
		chats.set(await getChatList(localStorage.token, get(currentChatPage)));
	}
	
	async function initNewChat(): Promise<void> {
		autoScroll.set(true);
		chatId.set('');
		chatTitle.set('');
		
		resetHistory();
		chatFiles.set([]);
		params.set({});
		
		// Process pending support data
		const currentHistory = get(history);
		const supportResult = await processPendingSupportData(currentHistory);
		history.set(supportResult.history);
		
		if (supportResult.chatFiles.length > 0) {
			chatFiles.update(($files) => [...$files, ...supportResult.chatFiles]);
		}
	}
	
	function resetInput() {
		prompt.set('');
		files.set([]);
	}
	
	function setPrompt(value: string) {
		prompt.set(value);
	}
	
	function addFile(file: FileUploadItem) {
		files.update(($files) => [...$files, file]);
	}
	
	function removeFile(itemId: string) {
		files.update(($files) => $files.filter((f) => f.itemId !== itemId));
	}
	
	function clearFiles() {
		files.set([]);
	}
	
	function mergeChatFiles(newFiles: FileUploadItem[]) {
		const docTypes = ['doc', 'file', 'collection'];
		const filteredFiles = newFiles.filter((f) => docTypes.includes(f.type));
		
		chatFiles.update(($chatFiles) => {
			const merged = [...$chatFiles, ...filteredFiles];
			// Remove duplicates
			return merged.filter(
				(item, index, array) =>
					array.findIndex((i) => JSON.stringify(i) === JSON.stringify(item)) === index
			);
		});
	}
	
	function setLoading(value: boolean) {
		loading.set(value);
	}
	
	function setAutoScroll(value: boolean) {
		autoScroll.set(value);
	}
	
	function setTaskId(value: string | null) {
		taskId.set(value);
	}
	
	return {
		// State
		history,
		chat,
		tags,
		prompt,
		files,
		chatFiles,
		params,
		loading,
		autoScroll,
		taskId,
		currentMessage,
		hasMessages,
		isResponseInProgress,
		
		// Actions
		resetHistory,
		updateMessage,
		addMessage,
		setCurrentId,
		loadChat,
		saveChat,
		initNewChat,
		resetInput,
		setPrompt,
		addFile,
		removeFile,
		clearFiles,
		mergeChatFiles,
		setLoading,
		setAutoScroll,
		setTaskId
	};
}

// Helper function (imported in main file)
function createMessagesList(history: ChatHistory, currentId: string | null): ChatMessage[] {
	if (!currentId) return [];
	
	const messages: ChatMessage[] = [];
	let id: string | null = currentId;
	
	while (id && history.messages[id]) {
		messages.unshift(history.messages[id]);
		id = history.messages[id].parentId;
	}
	
	return messages;
}

/**
 * Singleton instance for use across the chat component
 */
let chatStateInstance: (ChatState & ChatStateActions) | null = null;

export function useChatState(): ChatState & ChatStateActions {
	if (!chatStateInstance) {
		chatStateInstance = createChatState();
	}
	return chatStateInstance;
}

export function resetChatState(): void {
	chatStateInstance = null;
}
