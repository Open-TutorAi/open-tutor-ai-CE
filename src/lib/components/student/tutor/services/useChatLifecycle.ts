import { get, type Writable } from 'svelte/store';
import { tick } from 'svelte';
import { goto } from '$app/navigation';
import { page } from '$app/stores';
import type { i18n as i18nType } from 'i18next';
import type { Config, Settings, Model } from '$lib/stores';

import { getChatById, getTagsById } from '$lib/apis/chats';
import { getUserSettings } from '$lib/apis/users';
import { getTools } from '$lib/apis/tools';

import type { ChatHistory } from './types';
import { createEmptyHistory } from './chatHistory';
import { processPendingSupportData } from './supportContext';

export interface LifecycleOptions {
	chatId: Writable<string>;
	chatTitle: Writable<string>;
	settings: Writable<Settings>;
	config: Writable<Config | undefined>;
	models: Writable<Model[]>;
	tools: Writable<any[]>; // Tool objects - structure varies
	temporaryChatEnabled: Writable<boolean>;
	showControls: Writable<boolean>;
	showCallOverlay: Writable<boolean>;
	showOverview: Writable<boolean>;
	showArtifacts: Writable<boolean>;
	mobile: Writable<boolean>;
	i18n: Writable<i18nType>;
}

export interface LifecycleState {
	history: ChatHistory;
	selectedModels: string[];
	params: Record<string, any>; // URL parameters
	chatFiles: any[]; // File metadata from chat history
	tags: any[]; // Tag objects from API
	chat: any; // Chat object from API
	autoScroll: boolean;
	loading: boolean;
}

export function createChatLifecycle(
	options: LifecycleOptions,
	getState: () => LifecycleState,
	setState: (updates: Partial<LifecycleState>) => void,
	uploadYoutube: (url: string) => Promise<void>,
	submitPrompt: (prompt: string) => void
) {
	const {
		chatId,
		chatTitle,
		settings,
		config,
		models,
		tools,
		temporaryChatEnabled,
		showControls,
		showCallOverlay,
		showOverview,
		showArtifacts,
		mobile
	} = options;

	// ============================================
	// Chat Loading
	// ============================================
	async function handleChatIdChange(chatIdProp: string): Promise<boolean> {
		setState({ loading: true });
		resetInput();

		if (chatIdProp && (await loadChat(chatIdProp))) {
			await tick();
			setState({ loading: false });
			restoreInputFromStorage(chatIdProp);
			document.getElementById('chat-input')?.focus();
			return true;
		} else {
			await goto('/');
			return false;
		}
	}

	async function loadChat(chatIdProp: string): Promise<boolean> {
		chatId.set(chatIdProp);
		const $chatId = get(chatId);
		
		const chat = await getChatById(localStorage.token, $chatId).catch(() => null);
		if (!chat?.chat) return false;

		const tags = await getTagsById(localStorage.token, $chatId).catch(() => []);
		const content = chat.chat;

		const selectedModels = content?.models ?? [content.models ?? ''];
		const history = content?.history ?? { messages: {}, currentId: null };
		chatTitle.set(content.title);

		const userSettings = await getUserSettings(localStorage.token);
		settings.set(userSettings?.ui ?? JSON.parse(localStorage.getItem('settings') ?? '{}'));

		const params = content?.params ?? {};
		const chatFiles = content?.files ?? [];

		await tick();
		if (history.currentId) {
			history.messages[history.currentId].done = true;
		}

		setState({
			chat,
			tags,
			selectedModels,
			history,
			params,
			chatFiles,
			autoScroll: true
		});

		return true;
	}

	async function initNewChat(setPrompt: (value: string) => void): Promise<void> {
		await initModelSelection();

		showControls.set(false);
		showCallOverlay.set(false);
		showOverview.set(false);
		showArtifacts.set(false);

		const $page = get(page);
		if ($page.url.pathname.includes('/c/')) {
			window.history.replaceState(getState().history, '', '/student/c/');
		}

		chatId.set('');
		chatTitle.set('');

		const emptyHistory = createEmptyHistory();
		const supportResult = await processPendingSupportData(emptyHistory);

		setState({
			autoScroll: true,
			history: supportResult.history,
			chatFiles: supportResult.chatFiles,
			params: {}
		});

		await handleUrlParams(setPrompt);
		await loadUserSettings();

		document.getElementById('chat-input')?.focus();
	}

	// ============================================
	// Model Selection
	// ============================================
	async function initModelSelection(): Promise<void> {
		const $page = get(page);
		const $settings = get(settings);
		const $config = get(config);
		const $models = get(models);

		let selectedModels: string[];

		const urlModels = $page.url.searchParams.get('models')?.split(',');
		const urlModel = $page.url.searchParams.get('model')?.split(',');

		if (urlModels) {
			selectedModels = urlModels;
		} else if (urlModel) {
			selectedModels = urlModel;
		} else if (sessionStorage.selectedModels) {
			selectedModels = JSON.parse(sessionStorage.selectedModels);
			sessionStorage.removeItem('selectedModels');
		} else if ($settings?.models) {
			selectedModels = $settings.models;
		} else if ($config?.default_models) {
			selectedModels = $config.default_models.split(',');
		} else {
			selectedModels = [''];
		}

		selectedModels = selectedModels.filter((id: string) => $models.some((m: any) => m.id === id));
		if (!selectedModels.length || selectedModels[0] === '') {
			selectedModels = $models.length ? [$models[0].id] : [''];
		}

		setState({ selectedModels });
	}

	async function updateToolIds(): Promise<void> {
		const state = getState();
		const $tools = get(tools);
		const $models = get(models);

		if (!$tools) {
			tools.set(await getTools(localStorage.token));
		}

		if (state.selectedModels.length !== 1) return;

		const model = $models.find((m: any) => m.id === state.selectedModels[0]);
		if (model) {
			(model?.info?.meta?.toolIds ?? []).filter((id: string) =>
				get(tools)?.find((t: any) => t.id === id)
			);
		}
	}

	function saveSessionModels(): void {
		const state = getState();
		if (state.selectedModels.length && state.selectedModels[0] !== '') {
			sessionStorage.selectedModels = JSON.stringify(state.selectedModels);
		}
	}

	// ============================================
	// URL Parameters
	// ============================================
	async function handleUrlParams(setPrompt: (value: string) => void): Promise<{
		webSearchEnabled: boolean;
		imageGenerationEnabled: boolean;
		selectedToolIds: string[];
	}> {
		const $page = get(page);
		const params = $page.url.searchParams;

		if (params.get('youtube')) {
			await uploadYoutube(`https://www.youtube.com/watch?v=${params.get('youtube')}`);
		}

		const webSearchEnabled = params.get('web-search') === 'true';
		const imageGenerationEnabled = params.get('image-generation') === 'true';

		const toolIds = params.get('tools') ?? params.get('tool-ids');
		const selectedToolIds = toolIds
			? toolIds.split(',').map((id) => id.trim()).filter(Boolean)
			: [];

		if (params.get('call') === 'true') {
			showCallOverlay.set(true);
			showControls.set(true);
		}

		const q = params.get('q');
		if (q) {
			setPrompt(q);
			await tick();
			submitPrompt(q);
		}

		return { webSearchEnabled, imageGenerationEnabled, selectedToolIds };
	}

	// ============================================
	// Settings & Input
	// ============================================
	async function loadUserSettings(): Promise<void> {
		const $settings = get(settings);
		const avatarEnabled = ($settings as any)?.avatarEnabled;
		const userSettings = await getUserSettings(localStorage.token);

		if (userSettings) {
			settings.set({ ...userSettings.ui, avatarEnabled });
		} else {
			const stored = JSON.parse(localStorage.getItem('settings') ?? '{}');
			settings.set({ ...stored, avatarEnabled });
		}
	}

	function restoreInputFromStorage(chatIdProp: string): {
		prompt: string;
		files: any[];
		selectedToolIds: string[];
		webSearchEnabled: boolean;
		imageGenerationEnabled: boolean;
	} | null {
		const saved = localStorage.getItem(`chat-input-${chatIdProp}`);
		if (saved) {
			try {
				return JSON.parse(saved);
			} catch (e) {
				return null;
			}
		}
		return null;
	}

	function resetInput(): void {
		setState({
			params: {},
			chatFiles: []
		});
	}

	// ============================================
	// Controls
	// ============================================
	function setupControlsWatcher(
		controlPane: any,
		controlPaneComponent: any
	): () => void {
		const unsubscribe = showControls.subscribe((value) => {
			const $mobile = get(mobile);
			if (controlPane && !$mobile) {
				try {
					if (value) {
						controlPaneComponent.openPane();
					} else {
						controlPane.collapse();
					}
				} catch (e) {}
			}
			if (!value) {
				showCallOverlay.set(false);
				showOverview.set(false);
				showArtifacts.set(false);
			}
		});
		return unsubscribe;
	}

	return {
		handleChatIdChange,
		loadChat,
		initNewChat,
		initModelSelection,
		updateToolIds,
		saveSessionModels,
		handleUrlParams,
		loadUserSettings,
		restoreInputFromStorage,
		resetInput,
		setupControlsWatcher
	};
}
