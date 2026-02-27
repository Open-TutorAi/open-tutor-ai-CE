import { writable, derived, get, type Writable, type Readable } from 'svelte/store';
import { page } from '$app/stores';

import { models, settings, config, tools, type Model } from '$lib/stores';
import { getTools } from '$lib/apis/tools';

export interface ModelSelectionState {
	selectedModels: Writable<string[]>;
	atSelectedModel: Writable<Model | undefined>;
	selectedToolIds: Writable<string[]>;
	imageGenerationEnabled: Writable<boolean>;
	webSearchEnabled: Writable<boolean>;
	codeInterpreterEnabled: Writable<boolean>;
	
	// Derived
	selectedModelIds: Readable<string[]>;
	hasValidModels: Readable<boolean>;
}

export interface ModelSelectionActions {
	initializeModels: () => Promise<void>;
	setSelectedModels: (modelIds: string[]) => void;
	setAtSelectedModel: (model: Model | undefined) => void;
	updateToolIds: () => Promise<void>;
	validateAndFilterModels: () => void;
	saveToSession: () => void;
	restoreFromSession: () => boolean;
	toggleImageGeneration: () => void;
	toggleWebSearch: () => void;
	toggleCodeInterpreter: () => void;
}

/**
 * Creates a model selection composable
 */
export function createModelSelection(): ModelSelectionState & ModelSelectionActions {
	// State stores
	const selectedModels = writable<string[]>(['']);
	const atSelectedModel = writable<Model | undefined>(undefined);
	const selectedToolIds = writable<string[]>([]);
	const imageGenerationEnabled = writable<boolean>(false);
	const webSearchEnabled = writable<boolean>(false);
	const codeInterpreterEnabled = writable<boolean>(false);
	
	// Derived state
	const selectedModelIds = derived(
		[selectedModels, atSelectedModel],
		([$selectedModels, $atSelectedModel]) => {
			return $atSelectedModel !== undefined ? [$atSelectedModel.id] : $selectedModels;
		}
	);
	
	const hasValidModels = derived(selectedModels, ($selectedModels) => {
		return $selectedModels.length > 0 && !$selectedModels.includes('');
	});
	
	// Actions
	async function initializeModels(): Promise<void> {
		const $page = get(page);
		const $models = get(models);
		const $settings = get(settings);
		const $config = get(config);
		
		let newSelectedModels: string[] = [''];
		
		// Check URL parameters first
		const urlModels = $page.url.searchParams.get('models');
		const urlModel = $page.url.searchParams.get('model');
		
		if (urlModels) {
			newSelectedModels = urlModels.split(',');
		} else if (urlModel) {
			newSelectedModels = urlModel.split(',');
		} else if (sessionStorage.selectedModels) {
			// Restore from session
			try {
				newSelectedModels = JSON.parse(sessionStorage.selectedModels);
				sessionStorage.removeItem('selectedModels');
			} catch (e) {
				console.error('Failed to parse session models:', e);
			}
		} else if ($settings?.models) {
			newSelectedModels = $settings.models;
		} else if ($config?.default_models) {
			newSelectedModels = $config.default_models.split(',');
		}
		
		// Filter to valid models only
		const validModelIds = $models.map((m) => m.id);
		newSelectedModels = newSelectedModels.filter((id) => validModelIds.includes(id));
		
		// Fallback to first model if none valid
		if (newSelectedModels.length === 0 || (newSelectedModels.length === 1 && newSelectedModels[0] === '')) {
			newSelectedModels = $models.length > 0 ? [$models[0].id] : [''];
		}
		
		selectedModels.set(newSelectedModels);
		
		// Update tool IDs based on selected model
		await updateToolIds();
	}
	
	function setSelectedModels(modelIds: string[]): void {
		selectedModels.set(modelIds);
	}
	
	function setAtSelectedModel(model: Model | undefined): void {
		atSelectedModel.set(model);
	}
	
	async function updateToolIds(): Promise<void> {
		const $tools = get(tools);
		const $models = get(models);
		const $selectedModels = get(selectedModels);
		const $atSelectedModel = get(atSelectedModel);
		
		// Ensure tools are loaded
		if (!$tools) {
			tools.set(await getTools(localStorage.token));
		}
		
		// Only update for single model selection
		if ($selectedModels.length !== 1 && !$atSelectedModel) {
			return;
		}
		
		const model = $atSelectedModel ?? $models.find((m) => m.id === $selectedModels[0]);
		
		if (model) {
			const modelToolIds = model?.info?.meta?.toolIds ?? [];
			const currentTools = get(tools) ?? [];
			
			const validToolIds = modelToolIds.filter((id: string) =>
				currentTools.find((t: any) => t.id === id)
			);
			
			selectedToolIds.set(validToolIds);
		}
	}
	
	function validateAndFilterModels(): void {
		const $models = get(models);
		const validModelIds = $models.map((m) => m.id);
		
		selectedModels.update(($selectedModels) => {
			const filtered = $selectedModels.filter((id) => validModelIds.includes(id));
			
			if (filtered.length === 0) {
				return $models.length > 0 ? [$models[0].id] : [''];
			}
			
			return filtered;
		});
	}
	
	function saveToSession(): void {
		const $selectedModels = get(selectedModels);
		
		if ($selectedModels.length === 0 || ($selectedModels.length === 1 && $selectedModels[0] === '')) {
			return;
		}
		
		sessionStorage.selectedModels = JSON.stringify($selectedModels);
	}
	
	function restoreFromSession(): boolean {
		const saved = sessionStorage.selectedModels;
		
		if (saved) {
			try {
				const parsed = JSON.parse(saved);
				selectedModels.set(parsed);
				sessionStorage.removeItem('selectedModels');
				return true;
			} catch (e) {
				console.error('Failed to restore models from session:', e);
			}
		}
		
		return false;
	}
	
	function toggleImageGeneration(): void {
		imageGenerationEnabled.update((v) => !v);
	}
	
	function toggleWebSearch(): void {
		webSearchEnabled.update((v) => !v);
	}
	
	function toggleCodeInterpreter(): void {
		codeInterpreterEnabled.update((v) => !v);
	}
	
	return {
		// State
		selectedModels,
		atSelectedModel,
		selectedToolIds,
		imageGenerationEnabled,
		webSearchEnabled,
		codeInterpreterEnabled,
		selectedModelIds,
		hasValidModels,
		
		// Actions
		initializeModels,
		setSelectedModels,
		setAtSelectedModel,
		updateToolIds,
		validateAndFilterModels,
		saveToSession,
		restoreFromSession,
		toggleImageGeneration,
		toggleWebSearch,
		toggleCodeInterpreter
	};
}

/**
 * Gets the model by ID from the models store
 */
export function getModelById(modelId: string): Model | undefined {
	const $models = get(models);
	return $models.find((m) => m.id === modelId);
}

/**
 * Checks if a model supports vision/images
 */
export function modelSupportsVision(model: Model): boolean {
	return model.info?.meta?.capabilities?.vision ?? true;
}

/**
 * Checks if a model supports usage tracking
 */
export function modelSupportsUsage(model: Model): boolean {
	return model.info?.meta?.capabilities?.usage ?? false;
}

/**
 * Gets the stream response setting for a model
 */
export function getModelStreamSetting(model: Model, settingsParams: any, chatParams: any): boolean {
	return (
		model?.info?.params?.stream_response ??
		settingsParams?.stream_response ??
		chatParams?.stream_response ??
		true
	);
}

// Singleton instance
let modelSelectionInstance: (ModelSelectionState & ModelSelectionActions) | null = null;

export function useModelSelection(): ModelSelectionState & ModelSelectionActions {
	if (!modelSelectionInstance) {
		modelSelectionInstance = createModelSelection();
	}
	return modelSelectionInstance;
}

export function resetModelSelection(): void {
	modelSelectionInstance = null;
}
