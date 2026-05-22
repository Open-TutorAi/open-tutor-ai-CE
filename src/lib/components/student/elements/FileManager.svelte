<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';

	interface I18n {
		t: (key: string) => string;
	}
	const i18n = getContext<Writable<I18n>>('i18n');


        // Props
	export let files: File[] = [];

	// Accepted file types & their display config
	const ACCEPTED_TYPES = '.pdf,.doc,.docx,.pptx,.mp4';
	const MAX_SIZE_MB = 50;

	// Error state
	let errorMessage = '';

	// Drag state
	let isDragging = false;

	// ─── Helpers ────────────────────────────────────────────────────────────────

	function formatSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	function getFileCategory(file: File): 'pdf' | 'doc' | 'ppt' | 'video' | 'other' {
		const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
		if (ext === 'pdf') return 'pdf';
		if (['doc', 'docx'].includes(ext)) return 'doc';
		if (['ppt', 'pptx'].includes(ext)) return 'ppt';
		if (['mp4', 'avi', 'mov'].includes(ext)) return 'video';
		return 'other';
	}

	// ─── File ingestion ──────────────────────────────────────────────────────────

	function ingestFiles(incoming: FileList | File[]) {
		errorMessage = '';
		const newFiles: File[] = [];
		const skipped: string[] = [];

		Array.from(incoming).forEach((file) => {
			// Size check
			if (file.size > MAX_SIZE_MB * 1024 * 1024) {
				skipped.push(`${file.name} (exceeds ${MAX_SIZE_MB} MB)`);
				return;
			}
			// Duplicate check
			if (files.some((f) => f.name === file.name && f.size === file.size)) {
				skipped.push(`${file.name} (already added)`);
				return;
			}
			newFiles.push(file);
		});

		if (skipped.length) {
			errorMessage = `Skipped: ${skipped.join(', ')}`;
		}

		files = [...files, ...newFiles];
	}

	function handleInput(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files) ingestFiles(input.files);
		// Reset input so the same file can be re-added after removal
		input.value = '';
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		isDragging = false;
		if (event.dataTransfer?.files) ingestFiles(event.dataTransfer.files);
	}

	function removeFile(index: number) {
		files = files.filter((_, i) => i !== index);
	}

	function clearAll() {
		files = [];
		errorMessage = '';
	}

	// ─── Drag feedback ───────────────────────────────────────────────────────────

	function onDragOver(e: DragEvent) { e.preventDefault(); isDragging = true; }
	function onDragLeave() { isDragging = false; }
</script>

<!-- ════════════════════════════════ TEMPLATE ════════════════════════════════ -->

<div class="file-manager">

	<!-- Drop zone -->
	<div
		class="drop-zone"
		class:dragging={isDragging}
		on:click={() => document.getElementById('fm-file-input')?.click()}
		on:dragover={onDragOver}
		on:dragleave={onDragLeave}
		on:drop={handleDrop}
		role="button"
		tabindex="0"
		on:keypress={(e) => e.key === 'Enter' && document.getElementById('fm-file-input')?.click()}
		aria-label={$i18n.t('Upload files')}
	>
		<input
			type="file"
			id="fm-file-input"
			class="hidden"
			multiple
			accept={ACCEPTED_TYPES}
			on:change={handleInput}
		/>

		<div class="drop-zone__inner">
			<!-- Upload icon -->
			<div class="upload-icon" class:bounce={isDragging}>
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
					<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
					<polyline points="17 8 12 3 7 8"/>
					<line x1="12" y1="3" x2="12" y2="15"/>
				</svg>
			</div>

			<p class="drop-zone__primary">
				{#if isDragging}
					{$i18n.t('Drop files here')}
				{:else}
					<span class="link-text">{$i18n.t('Click to upload')}</span>
					{$i18n.t(' or drag and drop')}
				{/if}
			</p>
			<p class="drop-zone__sub">{$i18n.t('PDF · DOCX · PPTX · MP4 — max 50 MB each')}</p>
		</div>
	</div>

	<!-- Error banner -->
	{#if errorMessage}
		<div class="error-banner" role="alert">
			<svg class="error-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
				<path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
			</svg>
			<span>{errorMessage}</span>
			<button class="error-close" on:click={() => (errorMessage = '')} aria-label="Dismiss">✕</button>
		</div>
	{/if}

	<!-- File list -->
	{#if files.length > 0}
		<div class="file-list">
			<div class="file-list__header">
				<span class="file-list__count">
					{files.length} {files.length === 1 ? $i18n.t('file') : $i18n.t('files')} {$i18n.t('selected')}
				</span>
				<button class="btn-clear" on:click={clearAll}>
					{$i18n.t('Clear all')}
				</button>
			</div>

			<ul class="file-list__items">
				{#each files as file, index}
					{@const cat = getFileCategory(file)}
					<li class="file-item file-item--{cat}">
						<!-- Type badge -->
						<div class="file-item__badge">
							{#if cat === 'pdf'}
								<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M5 4a2 2 0 00-2 2v12a2 2 0 002 2h14a2 2 0 002-2V8.414A2 2 0 0020.414 7L17 3.586A2 2 0 0015.586 3H7a2 2 0 00-2 1zm0 2h10v3a1 1 0 001 1h3v8H5V6zm6.5 4a.5.5 0 00-.5.5v1h-.5a.5.5 0 000 1H11v1.5a.5.5 0 001 0V13h.5a.5.5 0 000-1H12v-1h.5a.5.5 0 000-1H11.5z"/></svg>
							{:else if cat === 'doc'}
								<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z"/></svg>
							{:else if cat === 'ppt'}
								<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm-7 3a4 4 0 110 8 4 4 0 010-8zm0 2a2 2 0 100 4 2 2 0 000-4zm-5 9h10v1H7v-1z"/></svg>
							{:else if cat === 'video'}
								<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M15 8v8H5V8h10m1-2H4a1 1 0 00-1 1v10a1 1 0 001 1h12a1 1 0 001-1v-3.5l4 4v-11l-4 4V7a1 1 0 00-1-1z"/></svg>
							{:else}
								<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z"/></svg>
							{/if}
						</div>

						<!-- File info -->
						<div class="file-item__info">
							<span class="file-item__name" title={file.name}>{file.name}</span>
							<span class="file-item__meta">{formatSize(file.size)}</span>
						</div>

						<!-- Remove button -->
						<button
							class="file-item__remove"
							on:click|stopPropagation={() => removeFile(index)}
							aria-label={`Remove ${file.name}`}
							title={$i18n.t('Remove file')}
						>
							<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
								<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
							</svg>
						</button>
					</li>
				{/each}
			</ul>
		</div>
	{/if}
</div>


<!-- ════════════════════════════════ STYLES ══════════════════════════════════ -->

<style>
	/* ── Layout ── */
	.file-manager {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	/* ── Drop zone ── */
	.drop-zone {
		border: 2px dashed #d1d5db;
		border-radius: 0.75rem;
		padding: 2rem 1.5rem;
		cursor: pointer;
		text-align: center;
		transition: border-color 0.2s, background-color 0.2s;
		background-color: transparent;
	}

	:global(.dark) .drop-zone {
		border-color: #4b5563;
	}

	.drop-zone:hover,
	.drop-zone.dragging {
		border-color: #3b82f6;
		background-color: #eff6ff;
	}

	:global(.dark) .drop-zone:hover,
	:global(.dark) .drop-zone.dragging {
		background-color: rgba(59, 130, 246, 0.08);
	}

	.drop-zone__inner {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	/* Upload icon */
	.upload-icon {
		width: 3rem;
		height: 3rem;
		color: #3b82f6;
		margin-bottom: 0.25rem;
		transition: transform 0.2s;
	}

	.upload-icon svg {
		width: 100%;
		height: 100%;
	}

	.upload-icon.bounce {
		animation: bounceUp 0.5s ease infinite alternate;
	}

	@keyframes bounceUp {
		from { transform: translateY(0); }
		to   { transform: translateY(-6px); }
	}

	.drop-zone__primary {
		font-size: 0.875rem;
		color: #374151;
	}

	:global(.dark) .drop-zone__primary { color: #d1d5db; }

	.link-text {
		color: #3b82f6;
		font-weight: 600;
		text-decoration: underline;
		text-underline-offset: 2px;
	}

	.drop-zone__sub {
		font-size: 0.75rem;
		color: #9ca3af;
	}

	/* ── Error banner ── */
	.error-banner {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.625rem 0.875rem;
		background-color: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 0.5rem;
		font-size: 0.8125rem;
		color: #b91c1c;
	}

	:global(.dark) .error-banner {
		background-color: rgba(239, 68, 68, 0.1);
		border-color: rgba(239, 68, 68, 0.3);
		color: #fca5a5;
	}

	.error-icon {
		width: 1rem;
		height: 1rem;
		flex-shrink: 0;
	}

	.error-banner span {
		flex: 1;
	}

	.error-close {
		background: none;
		border: none;
		cursor: pointer;
		color: inherit;
		opacity: 0.7;
		padding: 0 0.25rem;
		font-size: 0.875rem;
		line-height: 1;
	}

	.error-close:hover { opacity: 1; }

	/* ── File list ── */
	.file-list {
		background-color: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 0.75rem;
		overflow: hidden;
	}

	:global(.dark) .file-list {
		background-color: rgba(55, 65, 81, 0.4);
		border-color: #374151;
	}

	.file-list__header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.625rem 1rem;
		border-bottom: 1px solid #e5e7eb;
	}

	:global(.dark) .file-list__header { border-color: #374151; }

	.file-list__count {
		font-size: 0.8125rem;
		font-weight: 600;
		color: #374151;
	}

	:global(.dark) .file-list__count { color: #d1d5db; }

	.btn-clear {
		font-size: 0.75rem;
		font-weight: 500;
		color: #ef4444;
		background: none;
		border: none;
		cursor: pointer;
		padding: 0.25rem 0.5rem;
		border-radius: 0.375rem;
		transition: background-color 0.15s;
	}

	.btn-clear:hover {
		background-color: #fee2e2;
	}

	:global(.dark) .btn-clear:hover { background-color: rgba(239, 68, 68, 0.15); }

	/* ── File items ── */
	.file-list__items {
		list-style: none;
		margin: 0;
		padding: 0.375rem 0;
	}

	.file-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 1rem;
		transition: background-color 0.15s;
	}

	.file-item:hover { background-color: #f3f4f6; }

	:global(.dark) .file-item:hover { background-color: rgba(255, 255, 255, 0.05); }

	/* Coloured badge by type */
	.file-item__badge {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2.25rem;
		height: 2.25rem;
		border-radius: 0.5rem;
		flex-shrink: 0;
	}

	.file-item__badge svg {
		width: 1.25rem;
		height: 1.25rem;
	}

	.file-item--pdf   .file-item__badge { background-color: #fee2e2; color: #dc2626; }
	.file-item--doc   .file-item__badge { background-color: #dbeafe; color: #2563eb; }
	.file-item--ppt   .file-item__badge { background-color: #ffedd5; color: #ea580c; }
	.file-item--video .file-item__badge { background-color: #f3e8ff; color: #9333ea; }
	.file-item--other .file-item__badge { background-color: #f3f4f6; color: #6b7280; }

	:global(.dark) .file-item--pdf   .file-item__badge { background-color: rgba(220,38,38,.15);  color: #fca5a5; }
	:global(.dark) .file-item--doc   .file-item__badge { background-color: rgba(37,99,235,.15);  color: #93c5fd; }
	:global(.dark) .file-item--ppt   .file-item__badge { background-color: rgba(234,88,12,.15);  color: #fdba74; }
	:global(.dark) .file-item--video .file-item__badge { background-color: rgba(147,51,234,.15); color: #d8b4fe; }
	:global(.dark) .file-item--other .file-item__badge { background-color: rgba(107,114,128,.15); color: #9ca3af; }

	.file-item__info {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-width: 0;
	}

	.file-item__name {
		font-size: 0.8125rem;
		font-weight: 500;
		color: #111827;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	:global(.dark) .file-item__name { color: #f3f4f6; }

	.file-item__meta {
		font-size: 0.6875rem;
		color: #9ca3af;
		margin-top: 0.1rem;
	}

	/* Remove button */
	.file-item__remove {
		width: 1.75rem;
		height: 1.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: none;
		border: none;
		cursor: pointer;
		color: #9ca3af;
		border-radius: 50%;
		flex-shrink: 0;
		transition: background-color 0.15s, color 0.15s;
		padding: 0;
	}

	.file-item__remove svg {
		width: 1rem;
		height: 1rem;
	}

	.file-item__remove:hover {
		background-color: #fee2e2;
		color: #dc2626;
	}

	:global(.dark) .file-item__remove:hover {
		background-color: rgba(220, 38, 38, 0.15);
		color: #fca5a5;
	}

	/* ── Utility ── */
	.hidden { display: none; }
</style>