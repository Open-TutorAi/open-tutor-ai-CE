<!-- Flashcards.svelte -->
<script lang="ts">
	import { getContext, onMount, onDestroy } from 'svelte';
	import type { Writable } from 'svelte/store';
	import { browser } from '$app/environment';
	import { toast } from 'svelte-sonner';
	import { models } from '$lib/stores';
	import {
		generateFlashcards,
		getFlashcardSets,
		deleteFlashcardSet,
		updateProgress,
		type FlashcardSet,
		type Flashcard
	} from '$lib/apis/flashcards';
	import { getSupportRequests, type SupportResponse } from '$lib/apis/supports';
	import { getChatById } from '$lib/apis/chats';

	interface I18n { t: (key: string) => string }
	const i18n = getContext<Writable<I18n>>('i18n');

	// ── view state ────────────────────────────────────────────
	type View = 'list' | 'create' | 'study';
	let view: View = 'list';

	// ── saved sets ────────────────────────────────────────────
	let sets: FlashcardSet[] = [];
	let loadingSets = true;
	let activeSet: FlashcardSet | null = null;

	// ── delete confirmation (two-click) ───────────────────────
	let pendingDeleteId: string | null = null;
	let deleteTimer: ReturnType<typeof setTimeout> | null = null;

	// ── create form ───────────────────────────────────────────
	let supports: SupportResponse[] = [];
	let selectedSupportId = '';
	let manualText = '';
	let selectedModel = '';
	let customTitle = '';
	let generating = false;

	// ── study state ───────────────────────────────────────────
	type CardState = Flashcard & { idx: number; flipped: boolean };
	let studyCards: CardState[] = [];
	let currentPos = 0;
	let reviewUnknownsOnly = false;
	let savingProgress = false;

	// ── keyboard ──────────────────────────────────────────────
	let keyHandler: (e: KeyboardEvent) => void;

	// ── derived ───────────────────────────────────────────────
	$: if ($models?.length && !selectedModel) selectedModel = $models[0]?.id ?? '';

	$: displayCards = reviewUnknownsOnly
		? studyCards.filter((c) => !isKnown(c.idx))
		: studyCards;

	$: currentCard = displayCards[currentPos] ?? null;

	$: knownCount = activeSet ? activeSet.known_indices.length : 0;
	$: totalCount = activeSet ? activeSet.cards.length : 0;
	$: progressPct = totalCount ? Math.round((knownCount / totalCount) * 100) : 0;

	// ── lifecycle ─────────────────────────────────────────────
	onMount(async () => {
		if (!browser) return;
		const token = localStorage.getItem('token') ?? '';
		await Promise.all([loadSets(token), loadSupports(token)]);

		keyHandler = (e: KeyboardEvent) => {
			if (view !== 'study' || !currentCard) return;
			if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
			if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); flip(); }
			else if (e.key === 'ArrowRight') { e.preventDefault(); next(); }
			else if (e.key === 'ArrowLeft')  { e.preventDefault(); prev(); }
			else if (e.key === 'k' || e.key === 'K') { if (currentCard.flipped) markKnown(); }
			else if (e.key === 'u' || e.key === 'U') { if (currentCard.flipped) markUnknown(); }
		};
		window.addEventListener('keydown', keyHandler);
	});

	onDestroy(() => {
		if (keyHandler) window.removeEventListener('keydown', keyHandler);
		if (deleteTimer) clearTimeout(deleteTimer);
	});

	// ── data loading ──────────────────────────────────────────
	async function loadSets(token: string) {
		loadingSets = true;
		try { sets = await getFlashcardSets(token); }
		catch { toast.error('Could not load your flashcard sets'); }
		finally { loadingSets = false; }
	}

	async function loadSupports(token: string) {
		try { supports = await getSupportRequests(token); }
		catch { /* non-critical */ }
	}

	// ── create ────────────────────────────────────────────────
	function extractMessages(chatData: any): { role: string; content: string }[] {
		const msgMap = chatData?.chat?.history?.messages ?? chatData?.chat?.history ?? {};
		if (typeof msgMap !== 'object' || Array.isArray(msgMap)) return [];
		return Object.values(msgMap)
			.filter((m: any) => (m.role === 'user' || m.role === 'assistant') && m.content?.trim())
			.map((m: any) => ({ role: m.role, content: m.content.trim() }));
	}

	async function generate() {
		const token = localStorage.getItem('token') ?? '';
		if (!selectedModel) { toast.error('Please select a model first'); return; }

		let messages: { role: string; content: string }[] = [];
		let title = customTitle.trim();
		let source_label: string | undefined;
		let support_id: string | undefined;

		if (selectedSupportId) {
			const sup = supports.find((s) => s.id === selectedSupportId);
			if (!sup?.chat_id) { toast.error('This support has no chat session yet'); return; }
			try {
				const chatData = await getChatById(token, sup.chat_id);
				messages = extractMessages(chatData);
			} catch { toast.error('Could not load the chat for this support'); return; }
			if (!title) title = sup.title;
			source_label = `Support: ${sup.subject}`;
			support_id = sup.id;
		} else if (manualText.trim()) {
			messages = [{ role: 'user', content: manualText.trim() }];
			if (!title) title = 'Manual set';
			source_label = 'Manual';
		} else {
			toast.error('Select a support session or paste some text first');
			return;
		}

		if (!messages.length) { toast.error('No messages found in this session'); return; }

		generating = true;
		try {
			const newSet = await generateFlashcards(token, messages, selectedModel, title, source_label, support_id);
			sets = [newSet, ...sets];
			toast.success(`"${newSet.title}" created — ${newSet.card_count} cards`);
			openSet(newSet);
			// reset form
			selectedSupportId = '';
			manualText = '';
			customTitle = '';
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to generate flashcards');
		} finally {
			generating = false;
		}
	}

	// ── study ─────────────────────────────────────────────────
	function openSet(s: FlashcardSet) {
		activeSet = s;
		studyCards = s.cards.map((c, idx) => ({ ...c, idx, flipped: false }));
		currentPos = 0;
		reviewUnknownsOnly = false;
		view = 'study';
	}

	function isKnown(idx: number) {
		return activeSet?.known_indices.includes(idx) ?? false;
	}

	function flip() {
		if (!currentCard) return;
		// mutate the card in studyCards
		const card = studyCards.find((c) => c.idx === currentCard!.idx);
		if (card) { card.flipped = !card.flipped; studyCards = studyCards; }
	}

	function next() { if (currentPos < displayCards.length - 1) currentPos++; }
	function prev() { if (currentPos > 0) currentPos--; }

	async function markKnown() {
		if (!activeSet || !currentCard) return;
		const idx = currentCard.idx;
		if (!activeSet.known_indices.includes(idx)) {
			const previous = activeSet.known_indices;
			activeSet.known_indices = [...previous, idx];
			activeSet.known_count = activeSet.known_indices.length;
			sets = sets.map((s) => s.id === activeSet!.id ? activeSet! : s);
			const ok = await saveProgress(previous);
			if (!ok) return; // revert handled in saveProgress; don't advance
		}
		// reset flip then advance
		const card = studyCards.find((c) => c.idx === idx);
		if (card) { card.flipped = false; studyCards = studyCards; }
		// skip past known cards in review mode
		if (currentPos < displayCards.length - 1) currentPos++;
	}

	async function markUnknown() {
		if (!activeSet || !currentCard) return;
		const idx = currentCard.idx;
		const previous: number[] = activeSet.known_indices;
		activeSet.known_indices = previous.filter((i: number) => i !== idx);
		activeSet.known_count = activeSet.known_indices.length;
		sets = sets.map((s) => s.id === activeSet!.id ? activeSet! : s);
		const card = studyCards.find((c) => c.idx === idx);
		if (card) { card.flipped = false; studyCards = studyCards; }
		const ok = await saveProgress(previous);
		if (!ok) return;
		if (currentPos < displayCards.length - 1) currentPos++;
	}

	// Persists known_indices to the backend. On failure, reverts the optimistic
	// update to `previous` so UI and server stay in sync. Returns true on success.
	async function saveProgress(previous: number[]): Promise<boolean> {
		if (!activeSet) return false;
		savingProgress = true;
		const token = localStorage.getItem('token') ?? '';
		try {
			const updated = await updateProgress(token, activeSet.id, activeSet.known_indices);
			activeSet = { ...activeSet, updated_at: updated.updated_at };
			return true;
		} catch {
			if (activeSet) {
				activeSet.known_indices = previous;
				activeSet.known_count = previous.length;
				sets = sets.map((s) => s.id === activeSet!.id ? activeSet! : s);
			}
			toast.error('Could not save progress — change reverted');
			return false;
		} finally {
			savingProgress = false;
		}
	}

	async function resetSet() {
		if (!activeSet) return;
		const previous = activeSet.known_indices;
		activeSet.known_indices = [];
		activeSet.known_count = 0;
		studyCards = studyCards.map((c) => ({ ...c, flipped: false }));
		currentPos = 0;
		reviewUnknownsOnly = false;
		sets = sets.map((s) => s.id === activeSet!.id ? activeSet! : s);
		await saveProgress(previous);
	}

	function startReviewUnknowns() {
		const hasUnknown = studyCards.some((c) => !isKnown(c.idx));
		if (!hasUnknown) { toast.success('All cards are known! Reset to start again.'); return; }
		reviewUnknownsOnly = true;
		currentPos = 0;
	}

	// ── delete (two-click confirm) ────────────────────────────
	async function handleDelete(id: string) {
		if (pendingDeleteId !== id) {
			// first click
			if (deleteTimer) clearTimeout(deleteTimer);
			pendingDeleteId = id;
			deleteTimer = setTimeout(() => { pendingDeleteId = null; }, 3000);
			return;
		}
		// second click → confirmed
		if (deleteTimer) { clearTimeout(deleteTimer); deleteTimer = null; }
		pendingDeleteId = null;
		const token = localStorage.getItem('token') ?? '';
		try {
			await deleteFlashcardSet(token, id);
			sets = sets.filter((s) => s.id !== id);
			if (activeSet?.id === id) { activeSet = null; view = 'list'; }
			toast.success('Set deleted');
		} catch { toast.error('Could not delete the set'); }
	}

	function formatDate(iso: string) {
		return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
	}
</script>

<!-- ═══════════════════════════════════════════════════════════ -->
<!-- LAYOUT                                                      -->
<!-- ═══════════════════════════════════════════════════════════ -->
<div class="flex h-full min-h-screen bg-gray-50 dark:bg-gray-900">

	<!-- ── LEFT PANEL: set list ──────────────────────────────── -->
	<aside class="w-72 shrink-0 flex flex-col border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-y-auto">

		<div class="px-4 py-5 border-b border-gray-100 dark:border-gray-700">
			<h1 class="text-lg font-bold text-gray-900 dark:text-white">Flashcards</h1>
			<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Your revision card sets</p>
		</div>

		<div class="p-3">
			<button
				on:click={() => { activeSet = null; view = 'create'; }}
				class="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
			>
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
				</svg>
				New set
			</button>
		</div>

		<!-- set list -->
		<div class="flex-1 overflow-y-auto px-2 pb-4 space-y-1">
			{#if loadingSets}
				{#each Array(3) as _}
					<div class="h-16 rounded-lg bg-gray-100 dark:bg-gray-700 animate-pulse mx-1 my-1"></div>
				{/each}
			{:else if sets.length === 0}
				<div class="text-center py-10 px-4">
					<div class="text-3xl mb-2">🗂️</div>
					<p class="text-sm text-gray-400 dark:text-gray-500">No sets yet.<br/>Click "New set" to generate one.</p>
				</div>
			{:else}
				{#each sets as set (set.id)}
					{@const active = activeSet?.id === set.id}
					{@const pct = set.card_count ? Math.round((set.known_count / set.card_count) * 100) : 0}
					<div
						class="group relative flex flex-col gap-1 px-3 py-2.5 rounded-lg cursor-pointer transition-colors
							{active
								? 'bg-blue-50 dark:bg-blue-900/30 ring-1 ring-blue-300 dark:ring-blue-700'
								: 'hover:bg-gray-100 dark:hover:bg-gray-700/50'}"
						role="button"
						tabindex="0"
						on:click={() => openSet(set)}
						on:keydown={(e) => e.key === 'Enter' && openSet(set)}
					>
						<div class="flex items-start justify-between gap-1 min-w-0">
							<span class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate leading-snug">
								{set.title}
							</span>
							<!-- delete button -->
							<button
								on:click|stopPropagation={() => handleDelete(set.id)}
								class="shrink-0 rounded p-0.5 opacity-0 group-hover:opacity-100 transition-opacity
									{pendingDeleteId === set.id
										? 'text-red-500 opacity-100'
										: 'text-gray-400 hover:text-red-500 dark:text-gray-500 dark:hover:text-red-400'}"
								title={pendingDeleteId === set.id ? 'Click again to confirm delete' : 'Delete set'}
							>
								{#if pendingDeleteId === set.id}
									<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
										<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
									</svg>
								{:else}
									<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
								{/if}
							</button>
						</div>

						{#if set.source_label}
							<span class="text-xs text-gray-400 dark:text-gray-500 truncate">{set.source_label}</span>
						{/if}

						<div class="flex items-center gap-2 mt-0.5">
							<!-- mini progress bar -->
							<div class="flex-1 h-1 rounded-full bg-gray-200 dark:bg-gray-600 overflow-hidden">
								<div class="h-full rounded-full bg-green-500 transition-all" style="width:{pct}%"></div>
							</div>
							<span class="text-xs text-gray-500 dark:text-gray-400 shrink-0">
								{set.known_count}/{set.card_count}
							</span>
						</div>

						{#if pendingDeleteId === set.id}
							<p class="text-xs text-red-500 font-medium mt-0.5">Click trash again to confirm</p>
						{/if}
					</div>
				{/each}
			{/if}
		</div>
	</aside>

	<!-- ── RIGHT PANEL ────────────────────────────────────────── -->
	<main class="flex-1 overflow-y-auto">

		<!-- ════ EMPTY / WELCOME ════ -->
		{#if view === 'list'}
			<div class="flex flex-col items-center justify-center h-full min-h-96 text-center px-8 py-16">
				<div class="text-6xl mb-4">📚</div>
				<h2 class="text-xl font-semibold text-gray-700 dark:text-gray-200 mb-2">Start studying</h2>
				<p class="text-sm text-gray-400 dark:text-gray-500 max-w-xs mb-6">
					Select a saved set from the left, or generate a new one from a tutoring session or lesson text.
				</p>
				<button
					on:click={() => { view = 'create'; }}
					class="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
				>
					Generate my first set
				</button>
			</div>

		<!-- ════ CREATE FORM ════ -->
		{:else if view === 'create'}
			<div class="max-w-2xl mx-auto px-6 py-8">

				<div class="flex items-center gap-3 mb-6">
					<button
						on:click={() => view = sets.length ? 'list' : 'list'}
						class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
					>
						<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
						</svg>
					</button>
					<div>
						<h2 class="text-xl font-bold text-gray-900 dark:text-white">New flashcard set</h2>
						<p class="text-sm text-gray-500 dark:text-gray-400">AI will extract key concepts and create revision cards</p>
					</div>
				</div>

				<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-5">

					<!-- Title -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Set name</label>
						<input
							type="text"
							bind:value={customTitle}
							placeholder="Auto-filled from source if left blank"
							class="w-full rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- Model -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Model</label>
						<select
							bind:value={selectedModel}
							class="w-full rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							{#each $models ?? [] as m}
								<option value={m.id}>{m.name ?? m.id}</option>
							{/each}
						</select>
						{#if !($models?.length)}
							<p class="text-xs text-amber-500 mt-1">No models available. Check that Ollama is running and has at least one model pulled.</p>
						{/if}
					</div>

					<!-- Support session -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							From a support session
						</label>
						{#if supports.filter(s => s.chat_id).length === 0}
							<p class="text-sm text-gray-400 dark:text-gray-500">No support sessions with a chat found.</p>
						{:else}
							<select
								bind:value={selectedSupportId}
								class="w-full rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							>
								<option value="">— select a session —</option>
								{#each supports.filter(s => s.chat_id) as s}
									<option value={s.id}>{s.title} ({s.subject})</option>
								{/each}
							</select>
						{/if}
					</div>

					<!-- Divider -->
					<div class="flex items-center gap-3">
						<div class="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
						<span class="text-xs text-gray-400">or paste text directly</span>
						<div class="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
					</div>

					<!-- Manual text -->
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Paste lesson or conversation text
						</label>
						<textarea
							bind:value={manualText}
							rows="6"
							placeholder="Paste a lesson, notes, or a conversation here…"
							disabled={!!selectedSupportId}
							class="w-full rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none disabled:opacity-40"
						></textarea>
						{#if selectedSupportId}
							<p class="text-xs text-gray-400 mt-1">Deselect the session above to use manual text instead.</p>
						{/if}
					</div>

					<!-- Generate -->
					<button
						on:click={generate}
						disabled={generating || !selectedModel}
						class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-semibold transition-colors shadow-sm"
					>
						{#if generating}
							<svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
							</svg>
							Generating cards…
						{:else}
							✨ Generate flashcards
						{/if}
					</button>

					<p class="text-xs text-center text-gray-400">The set is saved automatically once generated.</p>
				</div>
			</div>

		<!-- ════ STUDY VIEW ════ -->
		{:else if view === 'study' && activeSet}
			<div class="max-w-2xl mx-auto px-4 py-6">

				<!-- top bar -->
				<div class="flex items-center justify-between mb-5 flex-wrap gap-2">
					<div class="flex items-center gap-3 min-w-0">
						<button
							on:click={() => view = 'list'}
							class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 shrink-0"
						>
							<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
							</svg>
						</button>
						<div class="min-w-0">
							<h2 class="text-base font-bold text-gray-900 dark:text-white truncate">{activeSet.title}</h2>
							{#if activeSet.source_label}
								<p class="text-xs text-gray-400 dark:text-gray-500">{activeSet.source_label} · {formatDate(activeSet.created_at)}</p>
							{/if}
						</div>
					</div>
					<div class="flex gap-2 shrink-0">
						{#if reviewUnknownsOnly}
							<button
								on:click={() => { reviewUnknownsOnly = false; currentPos = 0; }}
								class="px-3 py-1.5 text-xs rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 transition-colors"
							>All cards</button>
						{:else}
							<button
								on:click={startReviewUnknowns}
								class="px-3 py-1.5 text-xs rounded-lg bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 hover:bg-amber-100 transition-colors font-medium"
							>Review unknowns</button>
						{/if}
						<button
							on:click={resetSet}
							class="px-3 py-1.5 text-xs rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 transition-colors"
						>Reset</button>
					</div>
				</div>

				<!-- progress bar -->
				<div class="mb-5">
					<div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1.5">
						<span>{knownCount} known</span>
						<span>{progressPct}%</span>
						<span>{totalCount - knownCount} to review</span>
					</div>
					<div class="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
						<div
							class="h-full rounded-full bg-green-500 transition-all duration-500"
							style="width:{progressPct}%"
						></div>
					</div>
				</div>

				<!-- ── flip card ── -->
				{#if displayCards.length === 0}
					<div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-12 text-center shadow-sm">
						<div class="text-4xl mb-3">🎉</div>
						<p class="text-gray-700 dark:text-gray-200 font-semibold">All unknown cards reviewed!</p>
						<button
							on:click={() => { reviewUnknownsOnly = false; currentPos = 0; }}
							class="mt-4 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
						>See all cards</button>
					</div>
				{:else}
					<!-- position indicator -->
					<p class="text-center text-xs text-gray-400 dark:text-gray-500 mb-3">
						{currentPos + 1} / {displayCards.length}{reviewUnknownsOnly ? ' (unknowns only)' : ''}
					</p>

					<!-- THE CARD (3D flip) -->
					{#if currentCard}
						<div
							class="card-scene mb-4"
							role="button"
							tabindex="0"
							on:click={flip}
							on:keydown={(e) => (e.key === ' ' || e.key === 'Enter') && flip()}
						>
							<div class="card-inner {currentCard.flipped ? 'is-flipped' : ''} {isKnown(currentCard.idx) ? 'is-known' : ''}">
								<!-- FRONT -->
								<div class="card-face card-front">
									<div class="card-label">Question</div>
									<p class="card-text">{currentCard.question}</p>
									<div class="card-hint">
										<svg class="w-4 h-4 mr-1 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5" />
										</svg>
										Click or press Space to reveal
									</div>
								</div>
								<!-- BACK -->
								<div class="card-face card-back">
									<div class="card-label answer-label">Answer</div>
									<p class="card-text">{currentCard.answer}</p>
									{#if savingProgress}
										<div class="absolute top-3 right-3 w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
									{/if}
								</div>
							</div>
						</div>

						<!-- known/unknown (shown only on back) -->
						{#if currentCard.flipped}
							<div class="flex gap-3 mb-5">
								<button
									on:click={markUnknown}
									class="flex-1 py-3 rounded-xl border-2 border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950 font-semibold text-sm transition-colors"
								>
									✗ Still learning
									<span class="block text-xs font-normal opacity-60 mt-0.5">(U)</span>
								</button>
								<button
									on:click={markKnown}
									class="flex-1 py-3 rounded-xl border-2 border-green-200 dark:border-green-800 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-950 font-semibold text-sm transition-colors"
								>
									✓ Got it
									<span class="block text-xs font-normal opacity-60 mt-0.5">(K)</span>
								</button>
							</div>
						{/if}

						<!-- prev / next -->
						<div class="flex justify-between">
							<button
								on:click={prev}
								disabled={currentPos === 0}
								class="px-4 py-2 text-sm rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 disabled:opacity-40 transition-colors flex items-center gap-1"
							>
								<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
								</svg>
								Previous
							</button>
							<button
								on:click={next}
								disabled={currentPos === displayCards.length - 1}
								class="px-4 py-2 text-sm rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 disabled:opacity-40 transition-colors flex items-center gap-1"
							>
								Next
								<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
								</svg>
							</button>
						</div>
					{/if}

					<!-- keyboard hint -->
					<p class="text-center text-xs text-gray-300 dark:text-gray-600 mt-4">
						Space · flip &nbsp;|&nbsp; ←/→ · navigate &nbsp;|&nbsp; K · known &nbsp;|&nbsp; U · unknown
					</p>

					<!-- all-cards list -->
					<div class="mt-8">
						<p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">All cards</p>
						<div class="space-y-1.5">
							{#each activeSet.cards as card, idx}
								{@const known = isKnown(idx)}
								{@const isCurrent = displayCards[currentPos]?.idx === idx}
								<button
									on:click={() => {
										const pos = displayCards.findIndex(c => c.idx === idx);
										if (pos !== -1) { currentPos = pos; }
										else { reviewUnknownsOnly = false; currentPos = idx; }
									}}
									class="w-full text-left px-4 py-2.5 rounded-lg border text-sm transition-colors
										{isCurrent ? 'ring-2 ring-blue-400 ring-offset-1 dark:ring-offset-gray-900' : ''}
										{known
											? 'border-green-100 dark:border-green-900 bg-green-50 dark:bg-green-950/40 text-green-800 dark:text-green-300'
											: 'border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}"
								>
									<span class="mr-2 text-xs">{known ? '✓' : '·'}</span>
									{card.question}
								</button>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</main>
</div>

<style>
	/* ── 3D flip card ─────────────────────────────────────── */
	.card-scene {
		perspective: 900px;
		cursor: pointer;
		user-select: none;
	}

	.card-inner {
		position: relative;
		min-height: 240px;
		transform-style: preserve-3d;
		transition: transform 0.45s cubic-bezier(0.4, 0, 0.2, 1);
		border-radius: 1rem;
	}

	.card-inner.is-flipped {
		transform: rotateY(180deg);
	}

	.card-face {
		position: absolute;
		inset: 0;
		backface-visibility: hidden;
		-webkit-backface-visibility: hidden;
		border-radius: 1rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 2rem;
		text-align: center;
		border: 2px solid;
		transition: border-color 0.3s;
	}

	/* front */
	.card-front {
		background: white;
		border-color: #e5e7eb;
	}

	:global(.dark) .card-front {
		background: #1f2937;
		border-color: #374151;
	}

	.card-inner.is-known .card-front {
		border-color: #86efac;
	}
	:global(.dark) .card-inner.is-known .card-front {
		border-color: #166534;
	}

	/* back */
	.card-back {
		background: #1d4ed8;
		border-color: #1d4ed8;
		transform: rotateY(180deg);
	}

	:global(.dark) .card-back {
		background: #1e3a8a;
		border-color: #1e3a8a;
	}

	.card-label {
		font-size: 0.65rem;
		font-weight: 700;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		margin-bottom: 0.75rem;
		color: #9ca3af;
	}

	.answer-label {
		color: #93c5fd;
	}

	.card-text {
		font-size: 1.05rem;
		font-weight: 500;
		line-height: 1.6;
		color: #111827;
		max-width: 42ch;
	}

	:global(.dark) .card-text {
		color: #f3f4f6;
	}

	.card-back .card-text {
		color: #ffffff;
	}

	.card-hint {
		position: absolute;
		bottom: 1rem;
		display: flex;
		align-items: center;
		font-size: 0.7rem;
		color: #d1d5db;
	}
</style>
