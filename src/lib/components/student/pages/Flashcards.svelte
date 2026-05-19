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
		updateFlashcardSet,
		type FlashcardSet,
		type Flashcard
	} from '$lib/apis/flashcards';
	import { getSupportRequests, type SupportResponse } from '$lib/apis/supports';
	import { getChatById } from '$lib/apis/chats';

	import Plus from '$lib/components/icons/Plus.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import ArrowLeft from '$lib/components/icons/ArrowLeft.svelte';
	import ChevronLeft from '$lib/components/icons/ChevronLeft.svelte';
	import ChevronRight from '$lib/components/icons/ChevronRight.svelte';
	import Check from '$lib/components/icons/Check.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import BookOpen from '$lib/components/icons/BookOpen.svelte';
	import ArrowPath from '$lib/components/icons/ArrowPath.svelte';
	import ArrowsPointingOut from '$lib/components/icons/ArrowsPointingOut.svelte';
	import Keyboard from '$lib/components/icons/Keyboard.svelte';
	import QuestionMarkCircle from '$lib/components/icons/QuestionMarkCircle.svelte';
	import Pencil from '$lib/components/icons/Pencil.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';

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
	let focusMode = false;
	let showShortcuts = false;

	// ── edit state ────────────────────────────────────────────
	// originalIdx is null for cards added during this edit session (not used
	// yet — we only support edit/delete/reorder for Sprint 2). It maps each
	// editable row back to its position in `activeSet.cards` so we can
	// re-derive `known_indices` against the new order on save.
	type EditCard = Flashcard & { originalIdx: number | null; key: string };
	let editMode = false;
	let editCards: EditCard[] = [];
	let editSaving = false;

	// ── keyboard ──────────────────────────────────────────────
	let keyHandler: (e: KeyboardEvent) => void;

	// ── derived ───────────────────────────────────────────────
	$: if ($models.length && !selectedModel) selectedModel = $models[0]?.id ?? '';

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
			if (editMode) return;
			if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
			if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); flip(); }
			else if (e.key === 'ArrowRight') { e.preventDefault(); next(); }
			else if (e.key === 'ArrowLeft')  { e.preventDefault(); prev(); }
			else if (e.key === 'k' || e.key === 'K') { if (currentCard.flipped) markKnown(); }
			else if (e.key === 'u' || e.key === 'U') { if (currentCard.flipped) markUnknown(); }
			else if (e.key === '?') { showShortcuts = !showShortcuts; }
			else if (e.key === 'Escape') {
				if (showShortcuts) showShortcuts = false;
				else if (focusMode) focusMode = false;
			}
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
		catch { toast.error($i18n.t('Could not load your flashcard sets')); }
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
		if (!selectedModel) { toast.error($i18n.t('Please select a model first')); return; }

		let messages: { role: string; content: string }[] = [];
		let title = customTitle.trim();
		let source_label: string | undefined;
		let support_id: string | undefined;

		if (selectedSupportId) {
			const sup = supports.find((s) => s.id === selectedSupportId);
			if (!sup?.chat_id) { toast.error($i18n.t('This support has no chat session yet')); return; }
			try {
				const chatData = await getChatById(token, sup.chat_id);
				messages = extractMessages(chatData);
			} catch { toast.error($i18n.t('Could not load the chat for this support')); return; }
			if (!title) title = sup.title;
			source_label = `Support: ${sup.subject}`;
			support_id = sup.id;
		} else if (manualText.trim()) {
			messages = [{ role: 'user', content: manualText.trim() }];
			if (!title) title = $i18n.t('Manual set');
			source_label = $i18n.t('Manual');
		} else {
			toast.error($i18n.t('Select a support session or paste some text first'));
			return;
		}

		if (!messages.length) { toast.error($i18n.t('No messages found in this session')); return; }

		generating = true;
		try {
			const newSet = await generateFlashcards(token, messages, selectedModel, title, source_label, support_id);
			sets = [newSet, ...sets];
			toast.success(`"${newSet.title}" — ${newSet.card_count} ${$i18n.t('cards')}`);
			openSet(newSet);
			selectedSupportId = '';
			manualText = '';
			customTitle = '';
		} catch (e: any) {
			toast.error(e?.message ?? $i18n.t('Failed to generate flashcards'));
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
		editMode = false;
		editCards = [];
		view = 'study';
	}

	function isKnown(idx: number) {
		return activeSet?.known_indices.includes(idx) ?? false;
	}

	function flip() {
		if (!currentCard) return;
		const card = studyCards.find((c) => c.idx === currentCard!.idx);
		if (card) { card.flipped = !card.flipped; studyCards = studyCards; }
	}

	function next() { if (currentPos < displayCards.length - 1) currentPos++; }
	function prev() { if (currentPos > 0) currentPos--; }

	// Jumps to the card with the given original index. If we're in "unknowns
	// only" mode and the target is filtered out, switch back to all-cards mode
	// so the jump is reachable. Also resets the flip state of the target card.
	function jumpToCard(idx: number) {
		const pos = displayCards.findIndex((c) => c.idx === idx);
		if (pos !== -1) {
			currentPos = pos;
		} else {
			reviewUnknownsOnly = false;
			currentPos = idx;
		}
		const card = studyCards.find((c) => c.idx === idx);
		if (card) { card.flipped = false; studyCards = studyCards; }
	}

	async function markKnown() {
		if (!activeSet || !currentCard) return;
		const idx = currentCard.idx;
		const wasAlreadyKnown = activeSet.known_indices.includes(idx);
		if (!wasAlreadyKnown) {
			const previous = activeSet.known_indices;
			activeSet.known_indices = [...previous, idx];
			activeSet.known_count = activeSet.known_indices.length;
			sets = sets.map((s) => s.id === activeSet!.id ? activeSet! : s);
			const ok = await saveProgress(previous);
			if (!ok) return;
		}
		const card = studyCards.find((c) => c.idx === idx);
		if (card) { card.flipped = false; studyCards = studyCards; }

		// In "unknowns only" mode, the card we just marked known is now filtered
		// out of displayCards — the next unknown has already shifted into the
		// current position, so we shouldn't increment. We only clamp in case we
		// were on the last unknown (currentPos would otherwise point past the end
		// and currentCard would become null, making the card "disappear").
		if (reviewUnknownsOnly && !wasAlreadyKnown) {
			if (currentPos > displayCards.length - 1 && displayCards.length > 0) {
				currentPos = displayCards.length - 1;
			}
		} else if (currentPos < displayCards.length - 1) {
			currentPos++;
		}
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
			toast.error($i18n.t('Could not save progress — change reverted'));
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

	// ── edit ──────────────────────────────────────────────────
	function enterEditMode() {
		if (!activeSet) return;
		editCards = activeSet.cards.map((c, idx) => ({
			question: c.question,
			answer: c.answer,
			originalIdx: idx,
			key: `o${idx}`
		}));
		editMode = true;
	}

	function exitEditMode() {
		editMode = false;
		editCards = [];
	}

	function moveCard(from: number, to: number) {
		if (to < 0 || to >= editCards.length) return;
		const next = editCards.slice();
		const [moved] = next.splice(from, 1);
		next.splice(to, 0, moved);
		editCards = next;
	}

	function deleteEditCard(at: number) {
		if (editCards.length <= 3) {
			toast.error($i18n.t('A set must keep at least 3 cards'));
			return;
		}
		editCards = editCards.filter((_, i) => i !== at);
	}

	async function saveEdits() {
		if (!activeSet) return;

		const trimmed = editCards.map((c) => ({
			...c,
			question: c.question.trim(),
			answer: c.answer.trim()
		}));
		const empty = trimmed.find((c) => !c.question || !c.answer);
		if (empty) {
			toast.error($i18n.t('Every card must have a question and an answer'));
			return;
		}
		if (trimmed.length < 3 || trimmed.length > 10) {
			toast.error($i18n.t('A set must have between 3 and 10 cards'));
			return;
		}

		// Re-derive known_indices against the new positional order.
		const oldKnown = new Set(activeSet.known_indices);
		const newKnownIndices: number[] = [];
		trimmed.forEach((c, newIdx) => {
			if (c.originalIdx !== null && oldKnown.has(c.originalIdx)) {
				newKnownIndices.push(newIdx);
			}
		});

		const newCards = trimmed.map(({ question, answer }) => ({ question, answer }));

		editSaving = true;
		const token = localStorage.getItem('token') ?? '';
		try {
			const updated = await updateFlashcardSet(token, activeSet.id, newCards, newKnownIndices);
			activeSet = updated;
			sets = sets.map((s) => (s.id === updated.id ? updated : s));
			studyCards = updated.cards.map((c, idx) => ({ ...c, idx, flipped: false }));
			currentPos = 0;
			reviewUnknownsOnly = false;
			exitEditMode();
			toast.success($i18n.t('Changes saved'));
		} catch (e: any) {
			toast.error(e?.message ?? $i18n.t('Could not save changes'));
		} finally {
			editSaving = false;
		}
	}

	function startReviewUnknowns() {
		const hasUnknown = studyCards.some((c) => !isKnown(c.idx));
		if (!hasUnknown) { toast.success($i18n.t('All cards are known. Reset to start again.')); return; }
		reviewUnknownsOnly = true;
		currentPos = 0;
	}

	// ── delete (two-click confirm) ────────────────────────────
	async function handleDelete(id: string) {
		if (pendingDeleteId !== id) {
			if (deleteTimer) clearTimeout(deleteTimer);
			pendingDeleteId = id;
			deleteTimer = setTimeout(() => { pendingDeleteId = null; }, 3000);
			return;
		}
		if (deleteTimer) { clearTimeout(deleteTimer); deleteTimer = null; }
		pendingDeleteId = null;
		const token = localStorage.getItem('token') ?? '';
		try {
			await deleteFlashcardSet(token, id);
			sets = sets.filter((s) => s.id !== id);
			if (activeSet?.id === id) { activeSet = null; view = 'list'; }
			toast.success($i18n.t('Set deleted'));
		} catch { toast.error($i18n.t('Could not delete the set')); }
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
	<!-- visible on md+ always (unless focus mode); on mobile only when listing -->
	<aside
		class="w-full md:w-72 md:shrink-0 flex-col border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-y-auto
			{focusMode && view === 'study'
				? 'hidden'
				: view === 'list'
					? 'flex'
					: 'hidden md:flex'}"
	>
		<div class="px-5 py-5 border-b border-gray-100 dark:border-gray-700">
			<h1 class="text-base font-semibold text-gray-900 dark:text-white">{$i18n.t('Flashcards')}</h1>
			<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{$i18n.t('Your revision card sets')}</p>
		</div>

		<div class="p-3">
			<button
				on:click={() => { activeSet = null; view = 'create'; }}
				class="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors shadow-sm"
			>
				<Plus className="w-4 h-4" strokeWidth="2" />
				{$i18n.t('New set')}
			</button>
		</div>

		<div class="flex-1 overflow-y-auto px-2 pb-4 space-y-1">
			{#if loadingSets}
				{#each Array(3) as _}
					<div class="h-16 rounded-lg bg-gray-100 dark:bg-gray-700/60 animate-pulse mx-1 my-1"></div>
				{/each}
			{:else if sets.length === 0}
				<div class="text-center py-10 px-4">
					<div class="mx-auto w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mb-3">
						<BookOpen className="w-5 h-5 text-gray-400 dark:text-gray-500" strokeWidth="1.5" />
					</div>
					<p class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('No sets yet')}</p>
					<p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{$i18n.t('Create one to start studying')}</p>
				</div>
			{:else}
				{#each sets as set (set.id)}
					{@const active = activeSet?.id === set.id}
					{@const pct = set.card_count ? Math.round((set.known_count / set.card_count) * 100) : 0}
					<div
						class="group relative flex flex-col gap-1.5 px-3 py-2.5 rounded-lg cursor-pointer transition-colors
							{active
								? 'bg-gray-100 dark:bg-gray-700/60 ring-1 ring-gray-200 dark:ring-gray-600'
								: 'hover:bg-gray-50 dark:hover:bg-gray-700/40'}"
						role="button"
						tabindex="0"
						on:click={() => openSet(set)}
						on:keydown={(e) => e.key === 'Enter' && openSet(set)}
					>
						<div class="flex items-start justify-between gap-2 min-w-0">
							<span class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate leading-snug">
								{set.title}
							</span>
							<button
								on:click|stopPropagation={() => handleDelete(set.id)}
								class="shrink-0 rounded p-1 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity
									{pendingDeleteId === set.id
										? 'text-red-600 dark:text-red-400 opacity-100'
										: 'text-gray-400 hover:text-red-500 dark:text-gray-500 dark:hover:text-red-400'}"
								title={pendingDeleteId === set.id ? $i18n.t('Click again to confirm') : $i18n.t('Delete set')}
								aria-label={$i18n.t('Delete set')}
							>
								<GarbageBin className="w-4 h-4" strokeWidth="1.75" />
							</button>
						</div>

						{#if set.source_label}
							<span class="text-xs text-gray-500 dark:text-gray-400 truncate">{set.source_label}</span>
						{/if}

						<div class="flex items-center gap-2">
							<div class="flex-1 h-1 rounded-full bg-gray-200 dark:bg-gray-600 overflow-hidden">
								<div class="h-full rounded-full bg-gray-700 dark:bg-gray-300 transition-all" style="width:{pct}%"></div>
							</div>
							<span class="text-xs text-gray-500 dark:text-gray-400 shrink-0 tabular-nums">
								{set.known_count}/{set.card_count}
							</span>
						</div>

						{#if pendingDeleteId === set.id}
							<p class="text-xs text-red-600 dark:text-red-400 mt-0.5">{$i18n.t('Click delete again to confirm')}</p>
						{/if}
					</div>
				{/each}
			{/if}
		</div>
	</aside>

	<!-- ── RIGHT PANEL ────────────────────────────────────────── -->
	<main
		class="flex-1 overflow-y-auto
			{view === 'list' ? 'hidden md:block' : 'block'}"
	>

		<!-- ════ EMPTY / WELCOME ════ -->
		{#if view === 'list'}
			<div class="flex flex-col items-center justify-center h-full min-h-96 text-center px-8 py-16">
				<div class="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
					<BookOpen className="w-6 h-6 text-gray-500 dark:text-gray-400" strokeWidth="1.5" />
				</div>
				<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">{$i18n.t('Start studying')}</h2>
				<p class="text-sm text-gray-500 dark:text-gray-400 max-w-sm mb-6 leading-relaxed">
					{$i18n.t('Select a saved set from the left, or generate a new one from a tutoring session or lesson text.')}
				</p>
				<button
					on:click={() => { view = 'create'; }}
					class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors shadow-sm"
				>
					<Plus className="w-4 h-4" strokeWidth="2" />
					{$i18n.t('Generate my first set')}
				</button>
			</div>

		<!-- ════ CREATE FORM ════ -->
		{:else if view === 'create'}
			<div class="max-w-2xl mx-auto px-6 py-8">

				<div class="flex items-center gap-3 mb-6">
					<button
						on:click={() => view = 'list'}
						class="p-1.5 rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 dark:hover:text-gray-200 dark:hover:bg-gray-800 transition-colors"
						aria-label={$i18n.t('Back')}
					>
						<ArrowLeft className="w-5 h-5" strokeWidth="2" />
					</button>
					<div>
						<h2 class="text-xl font-semibold text-gray-900 dark:text-white">{$i18n.t('New flashcard set')}</h2>
						<p class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('AI will extract key concepts and create revision cards.')}</p>
					</div>
				</div>

				<div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-6">

					<!-- Title -->
					<div>
						<label for="fc-title" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{$i18n.t('Set name')}</label>
						<input
							id="fc-title"
							type="text"
							bind:value={customTitle}
							placeholder={$i18n.t('Auto-filled from source if left blank')}
							class="w-full rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						/>
					</div>

					<!-- Model -->
					<div>
						<label for="fc-model" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{$i18n.t('Model')}</label>
						<select
							id="fc-model"
							bind:value={selectedModel}
							class="w-full rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						>
							{#each $models as m}
								<option value={m.id}>{m.name ?? m.id}</option>
							{/each}
						</select>
						{#if !$models.length}
							<p class="text-xs text-amber-600 dark:text-amber-400 mt-1.5">{$i18n.t('No models available. Check that Ollama is running and has at least one model pulled.')}</p>
						{/if}
					</div>

					<!-- Section: source -->
					<div class="pt-2">
						<p class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-3">{$i18n.t('Source')}</p>

						<!-- Support session -->
						<div>
							<label for="fc-support" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
								{$i18n.t('From a support session')}
							</label>
							{#if supports.filter(s => s.chat_id).length === 0}
								<p class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('No support sessions with a chat found.')}</p>
							{:else}
								<select
									id="fc-support"
									bind:value={selectedSupportId}
									class="w-full rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
								>
									<option value="">{$i18n.t('— select a session —')}</option>
									{#each supports.filter(s => s.chat_id) as s}
										<option value={s.id}>{s.title} ({s.subject})</option>
									{/each}
								</select>
							{/if}
						</div>

						<!-- Divider -->
						<div class="flex items-center gap-3 my-5">
							<div class="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
							<span class="text-xs uppercase tracking-wide text-gray-400 dark:text-gray-500">{$i18n.t('or')}</span>
							<div class="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
						</div>

						<!-- Manual text -->
						<div>
							<label for="fc-manual" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
								{$i18n.t('Paste lesson or conversation text')}
							</label>
							<textarea
								id="fc-manual"
								bind:value={manualText}
								rows="6"
								placeholder={$i18n.t('Paste a lesson, notes, or a conversation here…')}
								disabled={!!selectedSupportId}
								class="w-full rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none disabled:opacity-50"
							></textarea>
							{#if selectedSupportId}
								<p class="text-xs text-gray-500 dark:text-gray-400 mt-1.5">{$i18n.t('Deselect the session above to use manual text instead.')}</p>
							{/if}
						</div>
					</div>

					<!-- Generate -->
					<button
						on:click={generate}
						disabled={generating || !selectedModel}
						class="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gray-900 hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed dark:bg-white dark:hover:bg-gray-100 dark:disabled:bg-gray-600 dark:text-gray-900 text-white text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
					>
						{#if generating}
							<svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
							</svg>
							{$i18n.t('Generating cards…')}
						{:else}
							<Sparkles className="w-4 h-4" strokeWidth="1.75" />
							{$i18n.t('Generate flashcards')}
						{/if}
					</button>

					<p class="text-xs text-center text-gray-500 dark:text-gray-400">{$i18n.t('The set is saved automatically once generated.')}</p>
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
							class="p-1.5 rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 dark:hover:text-gray-200 dark:hover:bg-gray-800 transition-colors shrink-0"
							aria-label={$i18n.t('Back to list')}
						>
							<ArrowLeft className="w-5 h-5" strokeWidth="2" />
						</button>
						<div class="min-w-0">
							<h2 class="text-base font-semibold text-gray-900 dark:text-white truncate">{activeSet.title}</h2>
							{#if activeSet.source_label}
								<p class="text-xs text-gray-500 dark:text-gray-400">{activeSet.source_label} · {formatDate(activeSet.created_at)}</p>
							{/if}
						</div>
					</div>
					<div class="flex items-center gap-1 shrink-0">
						{#if !reviewUnknownsOnly}
							<button
								on:click={() => { reviewUnknownsOnly = true; currentPos = 0; }}
								class="px-2.5 py-1.5 text-xs rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
							>{$i18n.t('All cards')}</button>
						{:else}
							<button
								on:click={startReviewUnknowns}
								class="px-2.5 py-1.5 text-xs rounded-md text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors font-medium"
							>{$i18n.t('Review unknowns')}</button>
						{/if}
						<button
							on:click={resetSet}
							disabled={editMode}
							class="p-1.5 rounded-md text-gray-500 hover:text-gray-800 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
							title={$i18n.t('Reset progress')}
							aria-label={$i18n.t('Reset progress')}
						>
							<ArrowPath className="w-4 h-4" strokeWidth="1.75" />
						</button>
						<button
							on:click={editMode ? exitEditMode : enterEditMode}
							class="p-1.5 rounded-md transition-colors
								{editMode
									? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30'
									: 'text-gray-500 hover:text-gray-800 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800'}"
							title={editMode ? $i18n.t('Cancel edit') : $i18n.t('Edit cards')}
							aria-label={editMode ? $i18n.t('Cancel edit') : $i18n.t('Edit cards')}
							aria-pressed={editMode}
						>
							<Pencil className="w-4 h-4" strokeWidth="1.75" />
						</button>
						<button
							on:click={() => focusMode = !focusMode}
							class="p-1.5 rounded-md text-gray-500 hover:text-gray-800 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800 transition-colors hidden md:inline-flex"
							title={focusMode ? $i18n.t('Exit focus mode') : $i18n.t('Focus mode')}
							aria-label={focusMode ? $i18n.t('Exit focus mode') : $i18n.t('Focus mode')}
							aria-pressed={focusMode}
						>
							<ArrowsPointingOut className="size-4" strokeWidth="1.75" />
						</button>
						<button
							on:click={() => showShortcuts = !showShortcuts}
							class="p-1.5 rounded-md text-gray-500 hover:text-gray-800 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800 transition-colors"
							title={$i18n.t('Keyboard shortcuts')}
							aria-label={$i18n.t('Keyboard shortcuts')}
							aria-expanded={showShortcuts}
						>
							<QuestionMarkCircle className="w-4 h-4" strokeWidth="1.75" />
						</button>
					</div>
				</div>

				{#if editMode}
					<!-- ════ EDIT MODE ════ -->
					<div class="space-y-3">
						<p class="text-xs text-gray-500 dark:text-gray-400">
							{$i18n.t('Edit, delete or reorder cards. Progress is preserved per card.')}
						</p>

						{#each editCards as card, i (card.key)}
							<div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
								<div class="flex items-start gap-3">
									<div class="flex flex-col gap-1 shrink-0 pt-1">
										<button
											on:click={() => moveCard(i, i - 1)}
											disabled={i === 0}
											class="p-1 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100 dark:hover:text-gray-200 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
											title={$i18n.t('Move up')}
											aria-label={$i18n.t('Move up')}
										>
											<ChevronUp className="w-4 h-4" strokeWidth="2" />
										</button>
										<span class="text-[10px] text-gray-400 dark:text-gray-500 text-center tabular-nums">{i + 1}</span>
										<button
											on:click={() => moveCard(i, i + 1)}
											disabled={i === editCards.length - 1}
											class="p-1 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100 dark:hover:text-gray-200 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
											title={$i18n.t('Move down')}
											aria-label={$i18n.t('Move down')}
										>
											<ChevronDown className="w-4 h-4" strokeWidth="2" />
										</button>
									</div>

									<div class="flex-1 min-w-0 space-y-2">
										<div>
											<label class="block text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">
												{$i18n.t('Question')}
											</label>
											<textarea
												bind:value={card.question}
												rows="2"
												maxlength="500"
												class="w-full rounded-md border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
											></textarea>
										</div>
										<div>
											<label class="block text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">
												{$i18n.t('Answer')}
											</label>
											<textarea
												bind:value={card.answer}
												rows="3"
												maxlength="1500"
												class="w-full rounded-md border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
											></textarea>
										</div>
									</div>

									<button
										on:click={() => deleteEditCard(i)}
										disabled={editCards.length <= 3}
										class="shrink-0 p-1.5 rounded text-gray-400 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
										title={editCards.length <= 3 ? $i18n.t('At least 3 cards required') : $i18n.t('Delete card')}
										aria-label={$i18n.t('Delete card')}
									>
										<GarbageBin className="w-4 h-4" strokeWidth="1.75" />
									</button>
								</div>
							</div>
						{/each}

						<div class="flex justify-end gap-2 pt-2 sticky bottom-0 bg-gray-50 dark:bg-gray-900 py-3">
							<button
								on:click={exitEditMode}
								disabled={editSaving}
								class="px-4 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50 transition-colors"
							>{$i18n.t('Cancel')}</button>
							<button
								on:click={saveEdits}
								disabled={editSaving}
								class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-900 hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 dark:text-gray-900 text-white text-sm font-medium disabled:opacity-50 transition-colors"
							>
								{#if editSaving}
									<svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
										<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
										<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
									</svg>
									{$i18n.t('Saving…')}
								{:else}
									<Check className="w-4 h-4" strokeWidth="2.5" />
									{$i18n.t('Save changes')}
								{/if}
							</button>
						</div>
					</div>
				{:else}
				<!-- segmented progress / card-nav bar -->
				<div class="mb-6">
					<div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-2 tabular-nums">
						<span>{knownCount} / {totalCount} {$i18n.t('known')}</span>
						<span>{progressPct}%</span>
					</div>
					<div
						class="flex items-center gap-1"
						role="group"
						aria-label={$i18n.t('Card progress')}
					>
						{#each activeSet.cards as _card, idx}
							{@const known = isKnown(idx)}
							{@const isCurrent = displayCards[currentPos]?.idx === idx}
							<button
								on:click={() => jumpToCard(idx)}
								class="flex-1 h-2 rounded-full transition-colors
									{known
										? 'bg-green-500 hover:bg-green-600 dark:bg-green-500 dark:hover:bg-green-400'
										: 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600'}
									{isCurrent
										? 'ring-1 ring-offset-2 ring-gray-500 dark:ring-gray-100'
										: ''}"
								title="{$i18n.t('Card')} {idx + 1}{known ? ` · ${$i18n.t('known')}` : ''}"
								aria-label="{$i18n.t('Card')} {idx + 1} {known ? $i18n.t('known') : $i18n.t('not yet known')}"
								aria-current={isCurrent ? 'true' : undefined}
							></button>
						{/each}
					</div>
				</div>

				<!-- ── flip card ── -->
				{#if displayCards.length === 0}
					<div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
						<div class="mx-auto w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mb-3">
							<Check className="w-5 h-5 text-gray-500 dark:text-gray-400" strokeWidth="2" />
						</div>
						<p class="text-sm text-gray-900 dark:text-gray-100 font-medium">{$i18n.t('All unknown cards reviewed.')}</p>
						<button
							on:click={() => { reviewUnknownsOnly = false; currentPos = 0; }}
							class="mt-4 px-3 py-1.5 text-sm rounded-md text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
						>{$i18n.t('See all cards')}</button>
					</div>
				{:else}
					<!-- position indicator -->
					<p class="text-center text-xs text-gray-500 dark:text-gray-400 mb-3 tabular-nums">
						{currentPos + 1} / {displayCards.length}{reviewUnknownsOnly ? ` · ${$i18n.t('unknowns only')}` : ''}
					</p>

					<!-- THE CARD (3D flip) -->
					{#if currentCard}
						<div
							class="card-scene mb-4"
							role="button"
							tabindex="0"
							aria-label={currentCard.flipped ? $i18n.t('Show question') : $i18n.t('Show answer')}
							on:click={flip}
							on:keydown={(e) => (e.key === ' ' || e.key === 'Enter') && flip()}
						>
							<div class="card-inner {currentCard.flipped ? 'is-flipped' : ''} {isKnown(currentCard.idx) ? 'is-known' : ''}">
								<!-- FRONT -->
								<div class="card-face card-front">
									<div class="card-label">{$i18n.t('Question')}</div>
									<p class="card-text">{currentCard.question}</p>
									<div class="card-hint">{$i18n.t('Click or press Space to reveal')}</div>
								</div>
								<!-- BACK -->
								<div class="card-face card-back">
									<div class="card-back-accent"></div>
									<div class="card-label answer-label">{$i18n.t('Answer')}</div>
									<p class="card-text">{currentCard.answer}</p>
									{#if savingProgress}
										<div class="absolute top-3 right-3 w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" aria-label={$i18n.t('Saving')}></div>
									{/if}
								</div>
							</div>
						</div>

						<!-- known/unknown (shown only on back) -->
						{#if currentCard.flipped}
							<div class="grid grid-cols-2 gap-3 mb-5">
								<button
									on:click={markUnknown}
									class="inline-flex items-center justify-center gap-2 py-2.5 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 text-sm font-medium transition-colors"
								>
									<XMark className="w-4 h-4" strokeWidth="2" />
									{$i18n.t('Still learning')}
									<kbd class="ml-1 text-[10px] px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 font-mono">U</kbd>
								</button>
								<button
									on:click={markKnown}
									class="inline-flex items-center justify-center gap-2 py-2.5 rounded-lg bg-gray-900 hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 dark:text-gray-900 text-white text-sm font-medium transition-colors"
								>
									<Check className="w-4 h-4" strokeWidth="2.5" />
									{$i18n.t('Got it')}
									<kbd class="ml-1 text-[10px] px-1 py-0.5 rounded bg-white/20 dark:bg-gray-900/10 text-white/80 dark:text-gray-900/70 font-mono">K</kbd>
								</button>
							</div>
						{/if}

						<!-- prev / next -->
						<div class="flex justify-between">
							<button
								on:click={prev}
								disabled={currentPos === 0}
								class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
							>
								<ChevronLeft className="w-4 h-4" strokeWidth="2" />
								{$i18n.t('Previous')}
							</button>
							<button
								on:click={next}
								disabled={currentPos === displayCards.length - 1}
								class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
							>
								{$i18n.t('Next')}
								<ChevronRight className="w-4 h-4" strokeWidth="2" />
							</button>
						</div>
					{/if}

					<!-- (the all-cards list lived here; replaced by the segmented progress bar above) -->
				{/if}
				{/if}
			</div>
		{/if}
	</main>
</div>

<!-- ── Keyboard shortcuts popover ────────────────────────── -->
{#if showShortcuts}
	<div
		class="fixed bottom-6 right-6 z-50 w-72 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg p-4"
		role="dialog"
		aria-label={$i18n.t('Keyboard shortcuts')}
	>
		<div class="flex items-center justify-between mb-3">
			<div class="inline-flex items-center gap-2">
				<Keyboard className="w-4 h-4 text-gray-500 dark:text-gray-400" strokeWidth="1.75" />
				<p class="text-sm font-semibold text-gray-900 dark:text-gray-100">{$i18n.t('Shortcuts')}</p>
			</div>
			<button
				on:click={() => showShortcuts = false}
				class="p-1 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100 dark:hover:text-gray-200 dark:hover:bg-gray-700"
				aria-label={$i18n.t('Close')}
			>
				<XMark className="w-4 h-4" strokeWidth="2" />
			</button>
		</div>
		<ul class="space-y-2 text-sm">
			{#each [
				{ keys: ['Space'], label: $i18n.t('Flip card') },
				{ keys: ['←', '→'], label: $i18n.t('Previous / next') },
				{ keys: ['K'], label: $i18n.t('Mark known') },
				{ keys: ['U'], label: $i18n.t('Mark unknown') },
				{ keys: ['?'], label: $i18n.t('Toggle this panel') },
				{ keys: ['Esc'], label: $i18n.t('Close / exit focus mode') }
			] as row}
				<li class="flex items-center justify-between">
					<span class="text-gray-600 dark:text-gray-300">{row.label}</span>
					<span class="inline-flex items-center gap-1">
						{#each row.keys as k}
							<kbd class="text-[11px] px-1.5 py-0.5 rounded border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-700 dark:text-gray-200 font-mono">{k}</kbd>
						{/each}
					</span>
				</li>
			{/each}
		</ul>
	</div>
{/if}

<style>
	/* ── 3D flip card ─────────────────────────────────────── */
	.card-scene {
		perspective: 1200px;
		cursor: pointer;
		user-select: none;
	}

	.card-inner {
		position: relative;
		min-height: 260px;
		transform-style: preserve-3d;
		transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
		border-radius: 0.75rem;
	}

	.card-inner.is-flipped {
		transform: rotateY(180deg);
	}

	.card-face {
		position: absolute;
		inset: 0;
		backface-visibility: hidden;
		-webkit-backface-visibility: hidden;
		border-radius: 0.75rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 2.5rem 2rem;
		text-align: center;
		border: 1px solid #e5e7eb;
		background: #ffffff;
		transition: border-color 0.2s;
	}

	:global(.dark) .card-face {
		background: #1f2937;
		border-color: #374151;
	}

	.card-back {
		transform: rotateY(180deg);
	}

	/* subtle accent strip on the answer face — calmer than a full blue fill */
	.card-back-accent {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 3px;
		background: #2563eb;
		border-top-left-radius: 0.75rem;
		border-top-right-radius: 0.75rem;
	}

	/* known cards get a quiet green border instead of a loud highlight */
	.card-inner.is-known .card-front,
	.card-inner.is-known .card-back {
		border-color: #86efac;
	}
	:global(.dark) .card-inner.is-known .card-front,
	:global(.dark) .card-inner.is-known .card-back {
		border-color: #166534;
	}

	.card-label {
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		margin-bottom: 1rem;
		color: #9ca3af;
	}

	.answer-label {
		color: #2563eb;
	}
	:global(.dark) .answer-label {
		color: #60a5fa;
	}

	.card-text {
		font-size: 1.05rem;
		font-weight: 500;
		line-height: 1.6;
		color: #111827;
		max-width: 44ch;
	}

	:global(.dark) .card-text {
		color: #f3f4f6;
	}

	.card-hint {
		position: absolute;
		bottom: 1rem;
		font-size: 0.7rem;
		color: #9ca3af;
	}

	:global(.dark) .card-hint {
		color: #6b7280;
	}
</style>
