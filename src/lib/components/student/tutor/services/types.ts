/**
 * Type Definitions for Chat Services
 * 
 * Shared types used across all chat-related service modules.
 */

export interface ChatMessage {
	id: string;
	parentId: string | null;
	childrenIds: string[];
	role: 'user' | 'assistant' | 'system';
	content: string;
	files?: any[];
	timestamp?: number;
	models?: string[];
	model?: string;
	modelName?: string;
	modelIdx?: number;
	userContext?: string | null;
	done?: boolean;
	error?: { content: string };
	sources?: any[];
	code_executions?: any[];
	statusHistory?: any[];
	lastSentence?: string;
	merged?: { status: boolean; content: string };
	selectedModelId?: string;
	arena?: boolean;
	usage?: any;
	info?: any;
	originalContent?: string;
}

export interface ChatHistory {
	messages: Record<string, ChatMessage>;
	currentId: string | null;
}

export interface ChatFile {
	id?: string;
	type: string;
	name: string;
	file?: any;
	url?: string;
	collection_name?: string;
	status?: string;
	error?: string;
	size?: number;
	from_support?: boolean;
}

export interface FileUploadItem {
	type: 'file' | 'doc' | 'image' | string;
	file?: any;
	id?: string | null;
	url?: string;
	name: string;
	collection_name?: string;
	status: 'uploading' | 'uploaded' | 'error';
	error?: string;
	itemId?: string;
	size?: number;
	context?: string;
}

export interface PromptSubmissionConfig {
	selectedModels: string[];
	files: FileUploadItem[];
	chatFiles: ChatFile[];
	params: any;
	settings: any;
	config: any;
	user: any;
	i18n: any;
}

export interface SendPromptOptions {
	modelId?: string | null;
	modelIdx?: number | null;
	newChat?: boolean;
}

export interface ChatEventData {
	chat_id: string;
	message_id: string;
	data?: {
		type?: string;
		data?: any;
	};
}

export interface SupportFile {
	id: string;
	filename: string;
	file_type?: string;
	file_size?: number;
}

export interface SupportDetails {
	id: string;
	title: string;
	subject?: string;
	custom_subject?: string;
	short_description?: string;
	learning_objective?: string;
	learning_type?: 'exam' | 'course' | 'skill' | string;
	level?: 'primary' | 'middle' | 'high' | 'university' | string;
	content_language?: string;
	keywords?: string[];
	files?: SupportFile[];
	estimated_duration?: string;
}

export interface AvatarPersonality {
	id: string;
	name: string;
	description: string;
	prompt: string;
}

export interface ChatCompletionOptions {
	stream: boolean;
	model: string;
	messages: any[];
	params?: any;
	files?: ChatFile[];
	tool_ids?: string[];
	avatar_type?: string;
	features?: {
		image_generation?: boolean;
		code_interpreter?: boolean;
		web_search?: boolean;
	};
	variables?: Record<string, any>;
	model_item?: any;
	session_id?: string;
	chat_id?: string;
	id?: string;
	background_tasks?: {
		title_generation?: boolean;
		tags_generation?: boolean;
	};
	stream_options?: {
		include_usage?: boolean;
	};
}

export interface ChatCompletionResponse {
	id?: string;
	done?: boolean;
	choices?: Array<{
		message?: { content: string };
		delta?: { content: string };
	}>;
	content?: string;
	sources?: any[];
	selected_model_id?: string;
	error?: any;
	usage?: any;
	task_id?: string;
}

export interface EventConfirmationState {
	show: boolean;
	title: string;
	message: string;
	input: boolean;
	inputPlaceholder: string;
	inputValue: string;
	callback: ((result: any) => void) | null;
}

export interface ModelSelection {
	selectedModels: string[];
	atSelectedModel?: any;
	selectedModelIds: string[];
}

/**
 * Type guard to check if a message is a user message
 */
export function isUserMessage(message: ChatMessage): boolean {
	return message.role === 'user';
}

/**
 * Type guard to check if a message is an assistant message
 */
export function isAssistantMessage(message: ChatMessage): boolean {
	return message.role === 'assistant';
}

/**
 * Type guard to check if a message is a system message
 */
export function isSystemMessage(message: ChatMessage): boolean {
	return message.role === 'system';
}

/**
 * Type guard to check if a message is done
 */
export function isMessageDone(message: ChatMessage): boolean {
	return message.done === true;
}

/**
 * Type guard to check if a message has an error
 */
export function hasMessageError(message: ChatMessage): boolean {
	return message.error !== undefined && message.error !== null;
}
