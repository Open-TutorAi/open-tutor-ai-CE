/**
 * Chat Services Index
 * 
 * Central export point for all chat-related service modules.
 * These modules were extracted from Chat.svelte to improve
 * maintainability, testability, and code organization.
 * 
 * Usage:
 * ```typescript
 * import { 
 *   validatePromptSubmission,
 *   createUserMessage,
 *   addMessageToHistory,
 *   useChatState,
 *   useModelSelection
 * } from './services';
 * ```
 */

// Type exports
export * from './types';

// Composables / State Management
export { useChatState, createChatState, resetChatState, type ChatState, type ChatStateActions } from './useChatState';
export { useModelSelection, createModelSelection, resetModelSelection, getModelById, modelSupportsVision, modelSupportsUsage, getModelStreamSetting, type ModelSelectionState, type ModelSelectionActions } from './useModelSelection';

// Chat Actions
export {
	regenerateResponse,
	continueResponse,
	submitMessage,
	mergeResponses,
	stopResponseGeneration,
	handleChatAction,
	createMessagePair as createMessagePairAction,
	addMessages,
	showMessage,
	handleOpenAIError,
	type ChatActionsConfig
} from './useChatActions';

// Prompt Submission Service
export {
	validatePromptSubmission,
	createUserMessage,
	createResponseMessage,
	addMessageToHistory,
	getAvatarPersonality,
	getAvatarAnimationInstructions,
	buildSystemMessage,
	prepareMessagesForApi,
	handleChatCompleted,
	initializeChat,
	saveChat,
	stopResponse,
	createChatEventEmitter
} from './promptSubmission';

// Chat History Helpers
export {
	createEmptyHistory,
	getMessageThread,
	getLastMessage,
	getSystemMessages,
	getCombinedSystemPrompt,
	addSystemMessage,
	appendChildMessage,
	updateMessage,
	markMessageDone,
	markMessageError,
	getParentMessage,
	getChildrenMessages,
	getSiblingMessages,
	navigateToSibling,
	getMessageCount,
	hasUserMessages,
	isResponseInProgress,
	createMessagePair,
	cloneHistory
} from './chatHistory';

// Socket Event Handlers
export {
	createChatEventHandler,
	handleStreamingContent,
	dispatchFinalTTSEvent,
	createIframeMessageHandler,
	type ChatEventHandlerConfig
} from './socketHandler';

// File Upload Helpers
export {
	createFileItem,
	uploadGoogleDriveFile,
	uploadWebContent,
	uploadYoutubeTranscription,
	validateFile,
	formatFileSize,
	getFileExtension,
	getFileType,
	deduplicateFiles,
	filterFilesByType,
	hasUploadingFiles,
	getReadyFiles,
	mergeFiles
} from './fileUpload';

// Support Context Helpers
export {
	generateSupportSystemPrompt,
	processPendingSupportData,
	getSupportTitle,
	clearPendingSupportData,
	hasPendingSupportData,
	getPendingSupportId
} from './supportContext';

// Event Handlers Composable
export {
	createEventHandlers,
	type EventHandlersOptions,
	type EventHandlersState,
	type DialogState
} from './useEventHandlers';

// Chat Lifecycle Composable
export {
	createChatLifecycle,
	type LifecycleOptions,
	type LifecycleState
} from './useChatLifecycle';

// Prompt Submission Composable
export {
	createPromptSubmission,
	type PromptSubmissionOptions,
	type PromptSubmissionState
} from './usePromptSubmission';

// Message Actions Composable
export {
	createMessageActions,
	type MessageActionsOptions,
	type MessageActionsState
} from './useMessageActions';
