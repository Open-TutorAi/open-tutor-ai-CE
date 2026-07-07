<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext, createEventDispatcher } from 'svelte';

	import {
		getQuerySettings,
		updateQuerySettings,
		resetVectorDB,
		getEmbeddingConfig,
		updateEmbeddingConfig,
		getRerankingConfig,
		updateRerankingConfig,
		resetUploadDir,
		getRAGConfig,
		updateRAGConfig
	} from '$lib/apis/retrieval';

	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Switch from '$lib/components/common/Switch.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';

	const dispatch = createEventDispatcher();
	const i18n = getContext<Writable<i18nType>>('i18n');

	// --- state ---
	let loading = false;
	let saving = false;
	let showAdvanced = false;
	let showResetVectorConfirm = false;
	let showResetUploadConfirm = false;

	// embedding
	let embeddingEngine = '';
	let embeddingModel = '';
	let embeddingBatchSize = 1;
	let OpenAIUrl = '';
	let OpenAIKey = '';
	let OllamaUrl = '';
	let OllamaKey = '';

	// reranking
	let rerankingModel = '';

	// query
	let querySettings = { template: '', r: 0.0, k: 4, hybrid: false };

	// rag config
	let pdfExtractImages = true;
	let RAG_FULL_CONTEXT = false;
	let textSplitter = '';
	let chunkSize = 1000;
	let chunkOverlap = 100;
	let contentExtractionEngine = 'default';
	let tikaServerUrl = '';
	let fileMaxSize: number | null = null;
	let fileMaxCount: number | null = null;

	onMount(async () => {
		loading = true;
		const [embCfg, rerankCfg, qSettings, ragCfg] = await Promise.all([
			getEmbeddingConfig(localStorage.token),
			getRerankingConfig(localStorage.token),
			getQuerySettings(localStorage.token),
			getRAGConfig(localStorage.token)
		]);
		if (embCfg) {
			embeddingEngine = embCfg.embedding_engine;
			embeddingModel = embCfg.embedding_model;
			embeddingBatchSize = embCfg.embedding_batch_size ?? 1;
			OpenAIKey = embCfg.openai_config?.key ?? '';
			OpenAIUrl = embCfg.openai_config?.url ?? '';
			OllamaKey = embCfg.ollama_config?.key ?? '';
			OllamaUrl = embCfg.ollama_config?.url ?? '';
		}
		if (rerankCfg) rerankingModel = rerankCfg.reranking_model;
		if (qSettings) querySettings = qSettings;
		if (ragCfg) {
			pdfExtractImages = ragCfg.pdf_extract_images;
			RAG_FULL_CONTEXT = ragCfg.RAG_FULL_CONTEXT;
			textSplitter = ragCfg.chunk.text_splitter;
			chunkSize = ragCfg.chunk.chunk_size;
			chunkOverlap = ragCfg.chunk.chunk_overlap;
			contentExtractionEngine = ragCfg.content_extraction.engine;
			tikaServerUrl = ragCfg.content_extraction.tika_server_url;
			fileMaxSize = ragCfg.file?.max_size ?? null;
			fileMaxCount = ragCfg.file?.max_count ?? null;
		}
		loading = false;
	});

	const save = async () => {
		saving = true;
		try {
			await updateEmbeddingConfig(localStorage.token, {
				embedding_engine: embeddingEngine,
				embedding_model: embeddingModel,
				embedding_batch_size: embeddingBatchSize,
				ollama_config: { key: OllamaKey, url: OllamaUrl },
				openai_config: { key: OpenAIKey, url: OpenAIUrl }
			});

			if (querySettings.hybrid) {
				await updateRerankingConfig(localStorage.token, { reranking_model: rerankingModel });
			}

			await updateRAGConfig(localStorage.token, {
				pdf_extract_images: pdfExtractImages,
				RAG_FULL_CONTEXT,
				chunk: { text_splitter: textSplitter, chunk_size: chunkSize, chunk_overlap: chunkOverlap },
				content_extraction: { engine: contentExtractionEngine, tika_server_url: tikaServerUrl },
				file: { max_size: fileMaxSize ?? null, max_count: fileMaxCount ?? null }
			});

			await updateQuerySettings(localStorage.token, querySettings);

			toast.success($i18n.t('RAG settings saved.'));
			dispatch('save');
		} catch (e) {
			toast.error(`${e}`);
		} finally {
			saving = false;
		}
	};
</script>

<ConfirmDialog
	bind:show={showResetVectorConfirm}
	on:confirm={async () => {
		await resetVectorDB(localStorage.token).catch((e) => toast.error(`${e}`));
		toast.success($i18n.t('Vector DB reset.'));
	}}
/>
<ConfirmDialog
	bind:show={showResetUploadConfirm}
	on:confirm={async () => {
		await resetUploadDir(localStorage.token).catch((e) => toast.error(`${e}`));
		toast.success($i18n.t('Upload directory reset.'));
	}}
/>

{#if loading}
	<div class="text-xs text-gray-400 py-4">{$i18n.t('Loading...')}</div>
{:else}
	<form class="flex flex-col gap-4 text-sm" on:submit|preventDefault={save}>
		<!-- Embedding model -->
		<div class="flex flex-col gap-2">
			<div class="font-medium">{$i18n.t('Embedding')}</div>

			<div class="flex w-full justify-between items-center">
				<span class="text-xs">{$i18n.t('Engine')}</span>
				<select
					class="dark:bg-gray-900 rounded-sm px-2 py-1 text-xs bg-transparent outline-none text-right"
					bind:value={embeddingEngine}
					on:change={() => {
						if (embeddingEngine === 'openai') embeddingModel = 'text-embedding-3-small';
						else if (embeddingEngine === '')
							embeddingModel = 'sentence-transformers/all-MiniLM-L6-v2';
						else embeddingModel = '';
					}}
				>
					<option value="">{$i18n.t('Default (SentenceTransformers)')}</option>
					<option value="ollama">{$i18n.t('Ollama')}</option>
					<option value="openai">{$i18n.t('OpenAI')}</option>
				</select>
			</div>

			{#if embeddingEngine === 'openai'}
				<div class="flex gap-2">
					<input
						class="flex-1 rounded-lg py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-850 outline-none"
						placeholder={$i18n.t('API Base URL')}
						bind:value={OpenAIUrl}
					/>
					<SensitiveInput placeholder={$i18n.t('API Key')} bind:value={OpenAIKey} />
				</div>
			{:else if embeddingEngine === 'ollama'}
				<div class="flex gap-2">
					<input
						class="flex-1 rounded-lg py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-850 outline-none"
						placeholder={$i18n.t('API Base URL')}
						bind:value={OllamaUrl}
					/>
					<SensitiveInput
						placeholder={$i18n.t('API Key')}
						bind:value={OllamaKey}
						required={false}
					/>
				</div>
			{/if}

			<div class="flex w-full justify-between items-center">
				<span class="text-xs">{$i18n.t('Model')}</span>
				<input
					class="w-56 rounded-lg py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-850 outline-none text-right"
					bind:value={embeddingModel}
					placeholder={$i18n.t('Embedding model name')}
				/>
			</div>
		</div>

		<hr class="border-gray-100 dark:border-gray-800" />

		<!-- Search settings -->
		<div class="flex flex-col gap-2">
			<div class="font-medium">{$i18n.t('Search')}</div>

			<div class="flex w-full justify-between items-center">
				<span class="text-xs">{$i18n.t('Hybrid Search')}</span>
				<Switch bind:state={querySettings.hybrid} />
			</div>

			{#if querySettings.hybrid}
				<div class="flex w-full justify-between items-center">
					<span class="text-xs">{$i18n.t('Reranking Model')}</span>
					<input
						class="w-56 rounded-lg py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-850 outline-none text-right"
						bind:value={rerankingModel}
						placeholder={$i18n.t('e.g. BAAI/bge-reranker-v2-m3')}
					/>
				</div>
			{/if}

			<div class="flex w-full justify-between items-center">
				<span class="text-xs">{$i18n.t('Top K Results')}</span>
				<input
					type="number"
					min="1"
					max="100"
					class="w-20 rounded-lg py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-850 outline-none text-right"
					bind:value={querySettings.k}
				/>
			</div>

			<div class="flex w-full justify-between items-center">
				<span class="text-xs">{$i18n.t('Relevance Threshold')}</span>
				<input
					type="number"
					min="0"
					max="1"
					step="0.01"
					class="w-20 rounded-lg py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-850 outline-none text-right"
					bind:value={querySettings.r}
				/>
			</div>
		</div>

		<hr class="border-gray-100 dark:border-gray-800" />

		<!-- OCR + reset -->
		<div class="flex flex-col gap-2">
			<div class="flex w-full justify-between items-center">
				<span class="text-xs font-medium">{$i18n.t('PDF Image Extraction (OCR)')}</span>
				<Switch bind:state={pdfExtractImages} />
			</div>

			<div class="flex gap-2">
				<button
					type="button"
					class="flex-1 py-1.5 text-xs rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-850 transition"
					on:click={() => (showResetVectorConfirm = true)}
				>
					{$i18n.t('Reset Vector DB')}
				</button>
				<button
					type="button"
					class="flex-1 py-1.5 text-xs rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-850 transition"
					on:click={() => (showResetUploadConfirm = true)}
				>
					{$i18n.t('Reset Upload Dir')}
				</button>
			</div>
		</div>

		<!-- Advanced section (collapsed) -->
		<div class="border border-gray-100 dark:border-gray-800 rounded-lg overflow-hidden">
			<button
				type="button"
				class="w-full flex justify-between items-center px-4 py-2.5 text-xs font-medium bg-gray-50 dark:bg-gray-850 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
				on:click={() => (showAdvanced = !showAdvanced)}
			>
				<span>{$i18n.t('Advanced')}</span>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="w-3.5 h-3.5 transition-transform {showAdvanced ? 'rotate-180' : ''}"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M19 9l-7 7-7-7"
					/>
				</svg>
			</button>

			{#if showAdvanced}
				<div class="px-4 py-3 flex flex-col gap-3">
					<div class="flex w-full justify-between items-center">
						<span class="text-xs">{$i18n.t('Full Context Mode')}</span>
						<Tooltip
							content={$i18n.t('Inject the full document as context instead of retrieved chunks.')}
						>
							<Switch bind:state={RAG_FULL_CONTEXT} />
						</Tooltip>
					</div>

					<div class="flex w-full justify-between items-center">
						<span class="text-xs">{$i18n.t('Text Splitter')}</span>
						<select
							class="dark:bg-gray-900 rounded-sm px-2 py-1 text-xs bg-transparent outline-none text-right"
							bind:value={textSplitter}
						>
							<option value="">{$i18n.t('Default')}</option>
							<option value="character">{$i18n.t('Character')}</option>
							<option value="token">{$i18n.t('Token')}</option>
						</select>
					</div>

					<div class="flex w-full justify-between items-center">
						<span class="text-xs">{$i18n.t('Chunk Size')}</span>
						<input
							type="number"
							min="1"
							class="w-24 rounded-lg py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-850 outline-none text-right"
							bind:value={chunkSize}
						/>
					</div>

					<div class="flex w-full justify-between items-center">
						<span class="text-xs">{$i18n.t('Chunk Overlap')}</span>
						<input
							type="number"
							min="0"
							class="w-24 rounded-lg py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-850 outline-none text-right"
							bind:value={chunkOverlap}
						/>
					</div>

					<div class="flex w-full justify-between items-center">
						<span class="text-xs">{$i18n.t('Content Extraction Engine')}</span>
						<select
							class="dark:bg-gray-900 rounded-sm px-2 py-1 text-xs bg-transparent outline-none text-right"
							bind:value={contentExtractionEngine}
						>
							<option value="default">{$i18n.t('Default')}</option>
							<option value="tika">{$i18n.t('Apache Tika')}</option>
						</select>
					</div>

					{#if contentExtractionEngine === 'tika'}
						<div class="flex w-full justify-between items-center">
							<span class="text-xs">{$i18n.t('Tika Server URL')}</span>
							<input
								class="w-56 rounded-lg py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-850 outline-none text-right"
								bind:value={tikaServerUrl}
								placeholder="http://tika:9998"
							/>
						</div>
					{/if}

					<div class="flex w-full justify-between items-center">
						<span class="text-xs">{$i18n.t('Max File Size (MB)')}</span>
						<input
							type="number"
							min="1"
							class="w-24 rounded-lg py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-850 outline-none text-right"
							bind:value={fileMaxSize}
							placeholder={$i18n.t('Unlimited')}
						/>
					</div>

					<div class="flex w-full justify-between items-center">
						<span class="text-xs">{$i18n.t('Max File Count')}</span>
						<input
							type="number"
							min="1"
							class="w-24 rounded-lg py-1.5 px-3 text-xs bg-gray-50 dark:bg-gray-850 outline-none text-right"
							bind:value={fileMaxCount}
							placeholder={$i18n.t('Unlimited')}
						/>
					</div>
				</div>
			{/if}
		</div>

		<div class="flex justify-end">
			<button
				type="submit"
				class="px-4 py-2 rounded-lg bg-black dark:bg-white text-white dark:text-black text-sm font-medium disabled:opacity-50 transition"
				disabled={saving}
			>
				{saving ? $i18n.t('Saving...') : $i18n.t('Save')}
			</button>
		</div>
	</form>
{/if}
