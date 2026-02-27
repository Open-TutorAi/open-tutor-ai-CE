import { v4 as uuidv4 } from 'uuid';
import { get } from 'svelte/store';
import { tick } from 'svelte';
import { toast } from 'svelte-sonner';

import { generateOpenAIChatCompletion } from '$lib/apis/openai';
import { createNewChat, updateChatById, getChatList } from '$lib/apis/chats';
import { getAndUpdateUserLocation } from '$lib/apis/users';
import { chatCompleted, chatAction, stopTask as stopTaskApi } from '$lib/apis';
import { TUTOR_BASE_URL } from '$lib/constants';

import {
	chatId,
	chats,
	models,
	settings,
	socket,
	user,
	temporaryChatEnabled,
	currentChatPage,
	chatTitle
} from '$lib/stores';

import {
	createMessagesList,
	promptTemplate,
	removeDetails,
	getPromptVariables,
	getMessageContentParts
} from '$lib/utils';

import type { Model } from '$lib/stores';
import type { ChatHistory, ChatMessage, PromptSubmissionConfig, SendPromptOptions } from './types';

/**
 * Validates prompt submission requirements
 */
export function validatePromptSubmission(
	userPrompt: string,
	files: any[],
	selectedModels: string[],
	messages: ChatMessage[],
	config: any,
	chatFiles: any[],
	i18n: any
): { valid: boolean; error?: string } {
	if (userPrompt === '' && files.length === 0) {
		return { valid: false, error: i18n.t('Please enter a prompt') };
	}

	if (selectedModels.includes('')) {
		return { valid: false, error: i18n.t('Model not selected') };
	}

	if (messages.length !== 0 && messages.at(-1)?.done !== true) {
		return { valid: false, error: 'Response not done' };
	}

	if (messages.length !== 0 && messages.at(-1)?.error && !messages.at(-1)?.content) {
		return { valid: false, error: i18n.t('Oops! There was an error in the previous response.') };
	}

	if (
		files.length > 0 &&
		files.filter((file) => file.type !== 'image' && file.status === 'uploading').length > 0
	) {
		return {
			valid: false,
			error: i18n.t('Oops! There are files still uploading. Please wait for the upload to complete.')
		};
	}

	const maxCount = config?.file?.max_count ?? null;
	if (maxCount !== null && files.length + chatFiles.length > maxCount) {
		return {
			valid: false,
			error: i18n.t('You can only chat with a maximum of {{maxCount}} file(s) at a time.', {
				maxCount
			})
		};
	}

	return { valid: true };
}

/**
 * Creates a user message object
 */
export function createUserMessage(
	userPrompt: string,
	parentId: string | null,
	files: any[],
	selectedModels: string[]
): ChatMessage {
	return {
		id: uuidv4(),
		parentId,
		childrenIds: [],
		role: 'user',
		content: userPrompt,
		files: files.length > 0 ? files : undefined,
		timestamp: Math.floor(Date.now() / 1000),
		models: selectedModels
	};
}

/**
 * Creates a response message object for a model
 */
export function createResponseMessage(
	parentId: string,
	model: Model,
	modelIdx: number
): ChatMessage {
	return {
		parentId,
		id: uuidv4(),
		childrenIds: [],
		role: 'assistant',
		content: '',
		model: model.id,
		modelName: model.name ?? model.id,
		modelIdx,
		userContext: null,
		timestamp: Math.floor(Date.now() / 1000)
	};
}

/**
 * Adds a message to history and updates relationships
 */
export function addMessageToHistory(
	history: ChatHistory,
	message: ChatMessage,
	parentId: string | null
): ChatHistory {
	// Add message to history
	history.messages[message.id] = message;
	history.currentId = message.id;

	// Update parent's childrenIds if parent exists
	if (parentId !== null && history.messages[parentId]) {
		history.messages[parentId].childrenIds = [
			...history.messages[parentId].childrenIds,
			message.id
		];
	}

	return history;
}

/**
 * Gets the avatar personality prompt based on selected avatar
 */
export function getAvatarPersonality(selectedAvatarId: string | undefined): string {
	if (!selectedAvatarId) return '';

	const avatarPersonalities: Record<string, string> = {
		'The Scholar':
			'You are The Scholar: analytical, detail-oriented, methodical, and patient. You emphasize deep understanding of fundamental concepts and provide comprehensive explanations with historical context and precise terminology. Your communication style is clear, formal, and structured with thoughtful pauses. You use academic language and reference research when appropriate. If someone asks if you are a different avatar (like The Mentor, The Coach, or The Innovator), clearly state that you are The Scholar.',
		'The Mentor':
			'You are The Mentor: encouraging, warm, supportive, and insightful. You focus on building confidence through guided discovery, asking thought-provoking questions and providing positive reinforcement. Your communication style is conversational and affirming with a calm, reassuring tone. You use relatable examples and analogies to help explain concepts. If someone asks if you are a different avatar (like The Scholar, The Coach, or The Innovator), clearly state that you are The Mentor.',
		'The Coach':
			'You are The Coach: energetic, motivational, direct, and goal-oriented. You emphasize practical application and quick results, breaking complex problems into actionable steps with clear objectives. Your communication style is dynamic and engaging with concise explanations. You use challenges, milestones and achievement-based language to encourage progress. If someone asks if you are a different avatar (like The Scholar, The Mentor, or The Innovator), clearly state that you are The Coach.',
		'The Innovator':
			'You are The Innovator: creative, adaptable, curious, and thought-provoking. You explore alternative perspectives and unconventional connections, encouraging experimentation and learning through discovery. Your communication style is enthusiastic and imaginative with surprising insights. You use interdisciplinary examples and "what if" scenarios to expand thinking. If someone asks if you are a different avatar (like The Scholar, The Mentor, or The Coach), clearly state that you are The Innovator.'
	};

	return avatarPersonalities[selectedAvatarId] || '';
}

/**
 * Gets the JSON animation instructions for avatar mode
 */
export function getAvatarAnimationInstructions(): string {
	return `
IMPORTANT: Format ALL responses as valid JSON with these fields:
- Don't ever answer in markdown, always answer in JSON
- "response": Your text answer to the user's question (REQUIRED, minimum 5 words)
- "animation": Animation codes for basic expressions (OPTIONAL)
- "glbAnimation": Name or array of animation names from the library (OPTIONAL)
- "glbAnimationCategory": Category for the animation (OPTIONAL, defaults to "expression")

Your animations should precisely match the content and emotion of your response. Always include multiple animations when possible to make your avatar more expressive and engaging.

Available animation options are:

1. SIMPLE ANIMATION CODES (use in "animation" object):
- facial_expression: 
	0=neutral, 1=smile, 2=frown, 3=raised_eyebrows, 4=surprise, 5=wink, 6=sad, 7=angry
- head_movement: 
	0=no_move, 1=nod_small, 2=shake, 3=tilt, 4=look_down, 5=look_up, 6=turn_left, 7=turn_right
- hand_gesture: 
	0=no_move, 1=open_hand, 2=pointing, 3=wave, 4=open_palm, 5=thumbs_up, 6=fist, 7=peace_sign, 8=finger_snap
- eye_movement: 
	0=no_move, 1=look_up, 2=look_down, 3=look_left, 4=look_right, 5=blink, 6=wide_open, 7=squint
- body_posture: 
	0=neutral, 1=forward_lean, 2=lean_back, 3=shoulders_up, 4=rest_arms, 5=hands_on_hips, 6=sit, 7=stand

2. GLB ANIMATIONS (use in "glbAnimation" field with appropriate category):

A. EXPRESSION ANIMATIONS ("glbAnimationCategory": "expression")
		"M_Talking_Variations_001" through "M_Talking_Variations_010"
		"M_Standing_Expressions_001" through "M_Standing_Expressions_018"
	- Also available with friendly names:
		"talking_neutral", "talking_happy", "talking_excited", "talking_thoughtful", "talking_concerned",
		"expression_smile", "expression_sad", "expression_surprise", "expression_thinking", "expression_angry"

B. IDLE ANIMATIONS ("glbAnimationCategory": "idle")
		"M_Standing_Idle_001", "M_Standing_Idle_002",
		"M_Standing_Idle_Variations_001" through "M_Standing_Idle_Variations_010"
	- Also available with friendly names:
		"idle_normal", "idle_shift_weight", "idle_look_around", "idle_stretch", "idle_impatient"

C. LOCOMOTION ANIMATIONS ("glbAnimationCategory": "locomotion")
		Walk, Jog, Run, Crouch animations with directional variants
	- Also available with friendly names:
		"walk_forward", "walk_backward", "jog_forward", "run_forward", "jump", "crouch"

D. DANCE ANIMATIONS ("glbAnimationCategory": "dance")
		"M_Dances_001" through "M_Dances_011"
	- Also available with friendly names:
		"dance_casual", "dance_energetic", "dance_rhythmic", "dance_silly"

Match animations to the emotional context and content of your response.

Example JSON response:
{
  "response": "Hello! I'm excited to help you with any questions you might have today.",
  "animation": {
    "facial_expression": 1,
    "head_movement": 1,
    "hand_gesture": 3,
    "eye_movement": 5
  },
  "glbAnimation": "talking_happy",
  "glbAnimationCategory": "expression"
}`;
}

/**
 * Builds the system message content for a chat request
 */
export async function buildSystemMessage(
	avatarActive: boolean,
	avatarPersonality: string,
	params: any,
	settingsStore: any,
	userStore: any,
	responseMessage: ChatMessage,
	combinedSystemPrompt: string
): Promise<string> {
	const userLocation = settingsStore?.userLocation
		? await getAndUpdateUserLocation(localStorage.token).catch((err) => {
				console.error(err);
				return undefined;
			})
		: undefined;

	if (combinedSystemPrompt) {
		return combinedSystemPrompt;
	}

	const baseSystemContent =
		avatarActive && avatarPersonality
			? `${avatarPersonality}\n\n${getAvatarAnimationInstructions()}\n\n${
					params?.system || settingsStore.system
						? `Additional instructions: ${promptTemplate(
								params?.system ?? settingsStore?.system ?? '',
								userStore.name,
								userLocation
							)}`
						: ''
				}${
					responseMessage?.userContext ?? null
						? `\n\nUser Context:\n${responseMessage?.userContext ?? ''}`
						: ''
				}`
			: `${promptTemplate(params?.system ?? settingsStore?.system ?? '', userStore.name, userLocation)}${
					responseMessage?.userContext ?? null
						? `\n\nUser Context:\n${responseMessage?.userContext ?? ''}`
						: ''
				}`;

	return baseSystemContent;
}

/**
 * Prepares messages for API submission
 */
export function prepareMessagesForApi(
	history: ChatHistory,
	responseMessageId: string,
	systemContent: string
): any[] {
	let messages = [
		{
			role: 'system',
			content: systemContent
		},
		...createMessagesList(history, responseMessageId)
			.filter((message) => message.role !== 'system')
			.map((message) => ({
				...message,
				content: removeDetails(message.content, ['reasoning', 'code_interpreter'])
			}))
	].filter((message) => message && message.content && message.content.trim() !== '');

	// Format messages with image support
	messages = messages
		.map((message) => ({
			role: message.role,
			...((message.files?.filter((file: any) => file.type === 'image').length > 0 ?? false) &&
			message.role === 'user'
				? {
						content: [
							{
								type: 'text',
								text: message?.merged?.content ?? message.content
							},
							...message.files
								.filter((file: any) => file.type === 'image')
								.map((file: any) => ({
									type: 'image_url',
									image_url: {
										url: file.url
									}
								}))
						]
					}
				: {
						content: message?.merged?.content ?? message.content
					})
		}))
		.filter((message) => message?.role === 'user' || message?.content?.trim());

	return messages;
}

/**
 * Handles chat completion callback
 */
export async function handleChatCompleted(
	token: string,
	chatIdValue: string,
	modelId: string,
	responseMessageId: string,
	messages: ChatMessage[],
	modelsStore: Model[],
	socketStore: any
): Promise<any> {
	const res = await chatCompleted(token, {
		model: modelId,
		messages: messages.map((m) => ({
			id: m.id,
			role: m.role,
			content: m.content,
			info: m.info ? m.info : undefined,
			timestamp: m.timestamp,
			...(m.usage ? { usage: m.usage } : {}),
			...(m.sources ? { sources: m.sources } : {})
		})),
		model_item: modelsStore.find((m) => m.id === modelId),
		chat_id: chatIdValue,
		session_id: socketStore?.id,
		id: responseMessageId
	}).catch((error) => {
		toast.error(`${error}`);
		return null;
	});

	return res;
}

/**
 * Initializes a new chat
 */
export async function initializeChat(
	history: ChatHistory,
	selectedModels: string[],
	settingsStore: any,
	params: any,
	chatFiles: any[],
	i18n: any,
	getSupportById: any
): Promise<string | null> {
	const modelsStore = get(models);
	const tempChatEnabled = get(temporaryChatEnabled);

	// Validate models
	let validModels = selectedModels;
	if (selectedModels.length === 0 || selectedModels.some((model) => !model)) {
		console.error('Invalid model selection. Setting default model...');
		if (modelsStore.length > 0) {
			validModels = [modelsStore[0].id];
		} else {
			throw new Error('No models available');
		}
	}

	if (!tempChatEnabled) {
		// Check for pending support data
		let supportId = null;
		let supportTitle = null;

		try {
			const pendingSupportData = localStorage.getItem('pendingSupportData');
			if (pendingSupportData) {
				const supportData = JSON.parse(pendingSupportData);
				supportId = supportData?.id || null;

				if (supportId) {
					try {
						const token = localStorage.getItem('token');
						const supportDetails = await getSupportById(token, supportId);
						if (supportDetails?.title) {
							supportTitle = supportDetails.title;
							console.log(`Using support title for chat: ${supportTitle}`);
						}
					} catch (titleError) {
						console.error('Error getting support title:', titleError);
					}
				}
			}
		} catch (error) {
			console.error('Error parsing pendingSupportData:', error);
		}

		const chat = await createNewChat(localStorage.token, {
			id: get(chatId),
			title: supportTitle || i18n.t('New Chat'),
			models: validModels,
			system: settingsStore.system ?? undefined,
			params,
			history,
			messages: createMessagesList(history, history.currentId),
			tags: [],
			files: chatFiles,
			support_id: supportId,
			timestamp: Date.now()
		});

		const newChatId = chat.id;
		chatId.set(newChatId);

		chats.set(await getChatList(localStorage.token, get(currentChatPage)));
		currentChatPage.set(1);

		// Dispatch chat created event
		if (typeof window !== 'undefined' && window.openTutorEvents) {
			console.log('Dispatching chatCreated event with ID:', newChatId);
			window.openTutorEvents.dispatchEvent(
				new CustomEvent('chatCreated', {
					detail: {
						chatId: newChatId,
						timestamp: Date.now(),
						success: true
					}
				})
			);
		}

		window.history.replaceState(history, '', `/student/c/${newChatId}`);
		return newChatId;
	} else {
		chatId.set('local');
		return 'local';
	}
}

/**
 * Saves chat state
 */
export async function saveChat(
	chatIdValue: string,
	history: ChatHistory,
	selectedModels: string[],
	params: any,
	chatFiles: any[]
): Promise<any> {
	const currentChatId = get(chatId);
	const tempChatEnabled = get(temporaryChatEnabled);

	if (currentChatId === chatIdValue && !tempChatEnabled) {
		const chat = await updateChatById(localStorage.token, chatIdValue, {
			models: selectedModels,
			history,
			messages: createMessagesList(history, history.currentId),
			params,
			files: chatFiles
		});

		currentChatPage.set(1);
		chats.set(await getChatList(localStorage.token, get(currentChatPage)));

		return chat;
	}

	return null;
}

/**
 * Stops an ongoing response generation
 */
export async function stopResponse(taskId: string | null): Promise<boolean> {
	if (!taskId) return false;

	const res = await stopTaskApi(localStorage.token, taskId).catch(() => null);
	return res !== null;
}

/**
 * Creates a chat event emitter for usage tracking
 */
export function createChatEventEmitter(modelId: string, chatIdValue: string): NodeJS.Timeout {
	const socketStore = get(socket);
	return setInterval(() => {
		socketStore?.emit('usage', {
			action: 'chat',
			model: modelId,
			chat_id: chatIdValue
		});
	}, 1000);
}
