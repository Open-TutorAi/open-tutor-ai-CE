/**
 * usePromptSubmission.ts - Prompt submission composable
 * 
 * Handles prompt validation, user message creation, and API calls
 */

import { v4 as uuidv4 } from 'uuid';
import { get, type Writable } from 'svelte/store';
import { tick } from 'svelte';
import { toast } from 'svelte-sonner';
import type { i18n as i18nType } from 'i18next';

import { TUTOR_BASE_URL } from '$lib/constants';
import { generateOpenAIChatCompletion } from '$lib/apis/openai';
import { getChatList, updateChatById } from '$lib/apis/chats';
import { getSupportById } from '$lib/apis/supports';

import type { ChatHistory, ChatMessage, FileUploadItem } from './types';
import {
	validatePromptSubmission,
	createUserMessage,
	createResponseMessage,
	initializeChat,
	addMessageToHistory,
	getAvatarPersonality,
	buildSystemMessage,
	prepareMessagesForApi
} from './promptSubmission';
import { cloneHistory, getCombinedSystemPrompt } from './chatHistory';
import { mergeFiles } from './fileUpload';

export interface PromptSubmissionOptions {
	chatId: Writable<string>;
	chats: Writable<any[]>;
	config: Writable<any>;
	settings: Writable<any>;
	user: Writable<any>;
	socket: Writable<any>;
	models: Writable<any[]>;
	currentChatPage: Writable<number>;
	temporaryChatEnabled: Writable<boolean>;
	i18n: Writable<i18nType>;
}

export interface PromptSubmissionState {
	history: ChatHistory;
	selectedModels: string[];
	atSelectedModel: any | undefined;
	params: any;
	chatFiles: any[];
	files: FileUploadItem[];
	prompt: string;
	selectedToolIds: string[];
	imageGenerationEnabled: boolean;
	webSearchEnabled: boolean;
	codeInterpreterEnabled: boolean;
	avatarActive: boolean;
	autoScroll: boolean;
	taskId: string | null;
}

export function createPromptSubmission(
	options: PromptSubmissionOptions,
	getState: () => PromptSubmissionState,
	setState: (updates: Partial<PromptSubmissionState>) => void,
	eventTarget: EventTarget,
	scrollToBottom: () => void,
	saveSessionModels: () => void
) {
	const {
		chatId,
		chats,
		config,
		settings,
		user,
		socket,
		models,
		currentChatPage,
		temporaryChatEnabled,
		i18n
	} = options;

	// ============================================
	// Main Submit Function
	// ============================================
	async function submitPrompt(userPrompt: string): Promise<void> {
		const state = getState();
		const $config = get(config);
		const $i18n = get(i18n);

		const messages = createMessagesList(state.history, state.history.currentId);
		const validation = validatePromptSubmission(
			userPrompt,
			state.files,
			state.selectedModels,
			messages,
			$config,
			state.chatFiles,
			$i18n
		);

		if (!validation.valid) {
			toast.error(validation.error!);
			return;
		}

		setState({ prompt: '' });

		// Resize input
		const inputEl = document.getElementById('chat-input') as HTMLTextAreaElement;
		if (inputEl) {
			await tick();
			inputEl.style.height = '';
			inputEl.style.height = Math.min(inputEl.scrollHeight, 320) + 'px';
		}

		// Process files
		const _files = JSON.parse(JSON.stringify(state.files));
		const chatFiles = mergeFiles(state.chatFiles, _files);
		setState({ chatFiles, files: [] });

		// Create user message
		const userMessage = createUserMessage(userPrompt, messages.at(-1)?.id ?? null, _files, state.selectedModels);
		let history = addMessageToHistory(state.history, userMessage, userMessage.parentId);
		setState({ history });

		document.getElementById('chat-input')?.focus();
		saveSessionModels();

		await sendPrompt(history, userPrompt, userMessage.id, { newChat: true });
	}

	// ============================================
	// Send Prompt to Models
	// ============================================
	async function sendPrompt(
		_history: ChatHistory,
		promptText: string,
		parentId: string,
		opts: { newChat?: boolean; modelId?: string; modelIdx?: number } = {}
	): Promise<void> {
		const state = getState();
		let _chatId = get(chatId);
		const $models = get(models);

		_history = cloneHistory(_history);

		const responseIds: Record<string, string> = {};
		const modelIds = opts.modelId
			? [opts.modelId]
			: state.atSelectedModel
				? [state.atSelectedModel.id]
				: state.selectedModels;

		// Create response messages for each model
		for (const [idx, mId] of modelIds.entries()) {
			const model = $models.find((m: any) => m.id === mId);
			if (model) {
				const resp = createResponseMessage(parentId, model, opts.modelIdx ?? idx);
				_history = addMessageToHistory(_history, resp, parentId);
				responseIds[`${mId}-${idx}`] = resp.id;
			}
		}

		setState({ history: _history });

		// Initialize chat if new
		if (opts.newChat && _history.messages[_history.currentId!]?.parentId === null) {
			_chatId = await initChatHandler(_history);
		}

		await tick();
		_history = cloneHistory(getState().history);
		await saveChatHandler(_chatId, _history);

		// Send to all models in parallel
		await Promise.all(
			modelIds.map(async (mId, idx) => {
				const model = $models.find((m: any) => m.id === mId);
				if (model) {
					await sendPromptToModel(_history, model, responseIds[`${mId}-${idx}`], _chatId);
				} else {
					const $i18n = get(i18n);
					toast.error($i18n.t('Model {{modelId}} not found', { modelId: mId }));
				}
			})
		);

		currentChatPage.set(1);
		chats.set(await getChatList(localStorage.token, get(currentChatPage)));
	}

	// ============================================
	// Send to Single Model
	// ============================================
	async function sendPromptToModel(
		_history: ChatHistory,
		model: any,
		responseId: string,
		_chatId: string
	): Promise<void> {
		const state = getState();
		const $config = get(config);
		const $settings = get(settings);
		const $user = get(user);
		const $models = get(models);
		const $socket = get(socket);

		const responseMessage = _history.messages[responseId];
		const userMessage = _history.messages[responseMessage.parentId!];

		// Gather all files
		let allFiles = [...state.chatFiles];
		allFiles.push(
			...(userMessage?.files ?? []).filter((f: any) => ['doc', 'file', 'collection'].includes(f.type)),
			...(responseMessage?.files ?? []).filter((f: any) => f.type === 'web_search_results')
		);
		allFiles = allFiles.filter(
			(item, i, arr) => arr.findIndex((x) => JSON.stringify(x) === JSON.stringify(item)) === i
		);

		scrollToBottom();
		eventTarget.dispatchEvent(new CustomEvent('chat:start', { detail: { id: responseId } }));
		await tick();

		// Build request
		const stream = model?.info?.params?.stream_response ?? $settings?.params?.stream_response ?? state.params?.stream_response ?? true;
		const avatarPersonality = state.avatarActive ? getAvatarPersonality(($settings as any)?.selectedAvatarId) : '';
		const systemPrompt = getCombinedSystemPrompt(_history);
		const systemContent = await buildSystemMessage(
			state.avatarActive,
			avatarPersonality,
			state.params,
			$settings,
			$user,
			responseMessage,
			systemPrompt
		);
		const messages = prepareMessagesForApi(_history, responseId, systemContent);

		const res = await generateOpenAIChatCompletion(
			localStorage.token,
			{
				stream,
				model: model.id,
				messages,
				params: { ...$settings?.params, ...state.params },
				files: allFiles.length ? allFiles : undefined,
				tool_ids: state.selectedToolIds.length ? state.selectedToolIds : undefined,
				features: {
					image_generation:
						$config?.features?.enable_image_generation &&
						($user.role === 'admin' || $user?.permissions?.features?.image_generation)
							? state.imageGenerationEnabled
							: false,
					code_interpreter:
						$config?.features?.enable_code_interpreter &&
						($user.role === 'admin' || $user?.permissions?.features?.code_interpreter)
							? state.codeInterpreterEnabled
							: false,
					web_search:
						$config?.features?.enable_web_search &&
						($user.role === 'admin' || $user?.permissions?.features?.web_search)
							? state.webSearchEnabled
							: false
				},
				model_item: $models.find((m: any) => m.id === model.id),
				session_id: $socket?.id,
				chat_id: get(chatId),
				id: responseId
			},
			`${TUTOR_BASE_URL}/api`
		).catch((error) => {
			toast.error(`${error}`);
			const newHistory = { ...getState().history };
			newHistory.messages[responseId].error = { content: error };
			newHistory.messages[responseId].done = true;
			setState({ history: newHistory });
			return null;
		});

		if (res) {
			setState({ taskId: res.task_id });
		}
		await tick();
		scrollToBottom();
	}

	// ============================================
	// Chat Management Helpers
	// ============================================
	async function initChatHandler(_history: ChatHistory): Promise<string> {
		const state = getState();
		const $settings = get(settings);
		const $i18n = get(i18n);

		try {
			const newChatId = await initializeChat(
				_history,
				state.selectedModels,
				$settings,
				state.params,
				state.chatFiles,
				$i18n,
				getSupportById
			);
			return newChatId ?? '';
		} catch (error) {
			localStorage.removeItem('pendingSupportData');
			toast.error($i18n.t('Failed to initialize chat'));
			return '';
		}
	}

	async function saveChatHandler(_chatId: string, _history: ChatHistory): Promise<void> {
		const state = getState();
		const $chatId = get(chatId);
		const $temporaryChatEnabled = get(temporaryChatEnabled);

		if ($chatId !== _chatId || $temporaryChatEnabled) return;

		await updateChatById(localStorage.token, _chatId, {
			models: state.selectedModels,
			history: _history,
			messages: createMessagesList(_history, _history.currentId),
			params: state.params,
			files: state.chatFiles
		});

		currentChatPage.set(1);
		chats.set(await getChatList(localStorage.token, get(currentChatPage)));
	}

	// ============================================
	// Utility
	// ============================================
	function createMessagesList(history: ChatHistory, endId: string | null): ChatMessage[] {
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
		submitPrompt,
		sendPrompt,
		sendPromptToModel,
		initChatHandler,
		saveChatHandler,
		createMessagesList
	};
}
