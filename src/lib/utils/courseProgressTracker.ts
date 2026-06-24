import { getCourseById, updateSectionProgress } from '$lib/apis/courses';

export type CourseSectionStatus = 'not-started' | 'in-progress' | 'completed';

export interface CourseProgressSignal {
	chapter_id: string;
	section_id: string;
	status: CourseSectionStatus;
	confidence?: number;
	reason?: string;
}

// ── IMPORTANT: do NOT use /g flag on a module-level regex — it has state ──────
// Always create a fresh regex instance per call.
function makeCourseProgressRegex() {
	return /<COURSE_PROGRESS>\s*([\s\S]*?)\s*<\/COURSE_PROGRESS>/i;
}

function safeLocalStorageGet(key: string): string | null {
	if (typeof window === 'undefined') return null;
	try {
		return window.localStorage.getItem(key);
	} catch {
		return null;
	}
}

function normaliseStatus(status: any): CourseSectionStatus | null {
	const s = String(status ?? '').trim().toLowerCase();
	if (['in-progress', 'in_progress', 'progress', 'started', 'start', 'current'].includes(s))
		return 'in-progress';
	if (
		['completed', 'complete', 'done', 'finished', 'finish', 'termine', 'terminé', 'fini'].includes(
			s
		)
	)
		return 'completed';
	if (['not-started', 'not_started', 'pending'].includes(s)) return 'not-started';
	return null;
}

function normaliseSignal(raw: any): CourseProgressSignal | null {
	if (!raw || typeof raw !== 'object') return null;
	const chapterId = raw.chapter_id ?? raw.chapterId ?? raw.chapter;
	const sectionId = raw.section_id ?? raw.sectionId ?? raw.section;
	const status = normaliseStatus(raw.status);
	if (!chapterId || !sectionId || !status) return null;
	return {
		chapter_id: String(chapterId),
		section_id: String(sectionId),
		status,
		confidence:
			typeof raw.confidence === 'number'
				? raw.confidence
				: raw.confidence
					? Number(raw.confidence)
					: undefined,
		reason: raw.reason ? String(raw.reason) : undefined
	};
}

function pushSignalFromPayload(payload: any, output: CourseProgressSignal[]) {
	if (!payload) return;
	if (Array.isArray(payload)) {
		for (const item of payload) {
			const signal = normaliseSignal(item);
			if (signal) output.push(signal);
		}
		return;
	}
	if (payload.updates && Array.isArray(payload.updates)) {
		pushSignalFromPayload(payload.updates, output);
		return;
	}
	if (payload.course_progress) { pushSignalFromPayload(payload.course_progress, output); return; }
	if (payload.courseProgress) { pushSignalFromPayload(payload.courseProgress, output); return; }
	const signal = normaliseSignal(payload);
	if (signal) output.push(signal);
}

// ─────────────────────────────────────────────────────────────────────────────
// resolveCourseIdForChat
// Called from Chat.svelte getActiveCourseId() on every AI response.
// MUST return a non-empty string for progress tracking to work.
// ─────────────────────────────────────────────────────────────────────────────
export function resolveCourseIdForChat(args: {
	courseIdProp?: string;
	chatId?: string;
	pathname?: string;
}): string {
	// 1. Explicit prop (learn/+page.svelte always passes this)
	const propId = args.courseIdProp?.trim();
	if (propId) return propId;

	// 2. URL pattern  /student/classrooms/<courseId>/learn
	const pathname = args.pathname ?? '';
	const routeMatch = pathname.match(/\/student\/classrooms\/([^/]+)\/learn/);
	if (routeMatch?.[1]) return decodeURIComponent(routeMatch[1]);

	// 3. localStorage mapping  course-chat-<chatId> → courseId  (resume case)
	const chatId = args.chatId?.trim();
	if (chatId && chatId !== 'local') {
		const mappedCourseId = safeLocalStorageGet(`course-chat-${chatId}`);
		if (mappedCourseId) return mappedCourseId;
	}

	// 4. Pending course data (new session, before chatCreated fires)
	const pendingCourseData = safeLocalStorageGet('pendingCourseData');
	if (pendingCourseData) {
		try {
			const parsed = JSON.parse(pendingCourseData);
			if (parsed?.id) return String(parsed.id);
		} catch {
			// ignore
		}
	}

	return '';
}

// ─────────────────────────────────────────────────────────────────────────────
// extractCourseProgressSignalsFromContent
// Parses ALL <COURSE_PROGRESS>…</COURSE_PROGRESS> blocks from a string.
// Uses a fresh regex each call to avoid /g lastIndex bugs.
// ─────────────────────────────────────────────────────────────────────────────
export function extractCourseProgressSignalsFromContent(content: string): {
	cleanedContent: string;
	updates: CourseProgressSignal[];
} {
	const updates: CourseProgressSignal[] = [];
	let cleanedContent = content ?? '';

	// Extract all tags with a loop + fresh regex each iteration
	let safetyLimit = 50; // prevent infinite loops
	while (safetyLimit-- > 0) {
		const regex = /<COURSE_PROGRESS>\s*([\s\S]*?)\s*<\/COURSE_PROGRESS>/i;
		const match = regex.exec(cleanedContent);
		if (!match) break;

		const jsonText = match[1]?.trim();
		if (jsonText) {
			try {
				const payload = JSON.parse(jsonText);
				pushSignalFromPayload(payload, updates);
			} catch (e) {
				console.warn('[CourseProgress] Invalid JSON in COURSE_PROGRESS tag:', jsonText);
			}
		}

		// Remove this specific tag from content
		cleanedContent = cleanedContent.slice(0, match.index) + cleanedContent.slice(match.index + match[0].length);
	}

	// Also handle JSON responses where course_progress is a top-level key
	const trimmed = cleanedContent.trim();
	if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
		try {
			const obj = JSON.parse(trimmed);
			let changed = false;
			if (obj.course_progress) { pushSignalFromPayload(obj.course_progress, updates); delete obj.course_progress; changed = true; }
			if (obj.courseProgress) { pushSignalFromPayload(obj.courseProgress, updates); delete obj.courseProgress; changed = true; }
			if (changed) cleanedContent = JSON.stringify(obj);
		} catch {
			// not JSON, ignore
		}
	}

	// Deduplicate: keep highest-rank status per section
	const unique = new Map<string, CourseProgressSignal>();
	const rank = (s: CourseSectionStatus) => (s === 'completed' ? 2 : s === 'in-progress' ? 1 : 0);
	for (const u of updates) {
		const key = `${u.chapter_id}:${u.section_id}`;
		const existing = unique.get(key);
		if (!existing || rank(u.status) > rank(existing.status)) unique.set(key, u);
	}

	return {
		cleanedContent: cleanedContent.replace(/\n{3,}/g, '\n\n').trim(),
		updates: [...unique.values()]
	};
}

// ─────────────────────────────────────────────────────────────────────────────
// buildCourseProgressTrackingPrompt
// Fetches current course state and returns instructions injected into system prompt.
// ─────────────────────────────────────────────────────────────────────────────
export async function buildCourseProgressTrackingPrompt(
	token: string,
	courseId: string
): Promise<string> {
	if (!token || !courseId) return '';

	try {
		const course = await getCourseById(token, courseId);

		const flatSections =
			course.chapters?.flatMap((chapter: any, chapterIndex: number) =>
				chapter.sections.map((section: any, sectionIndex: number) => ({
					chapter,
					section,
					chapterIndex,
					sectionIndex
				}))
			) ?? [];

		const currentItem =
			flatSections.find((item: any) => item.section.status === 'in-progress') ??
			flatSections.find((item: any) => item.section.status !== 'completed') ??
			flatSections[0];

		const planText = flatSections
			.map((item: any) => {
				const statusEmoji =
					item.section.status === 'completed'
						? '✅'
						: item.section.status === 'in-progress'
							? '▶️'
							: '⬜';
				return `  ${statusEmoji} Chapter ${item.chapterIndex + 1}: "${item.chapter.title}" [chapter_id=${item.chapter.id}]\n     Section ${item.sectionIndex + 1}: "${item.section.title}" [section_id=${item.section.id}] [status=${item.section.status}]`;
			})
			.join('\n');

		const completedCount = flatSections.filter(
			(item: any) => item.section.status === 'completed'
		).length;
		const totalCount = flatSections.length;

		return `
=========================================================
COURSE_PROGRESS_TRACKING_INSTRUCTIONS (MANDATORY - READ CAREFULLY)
=========================================================

You are teaching inside a course management system.
The system tracks progress PER SECTION via hidden markers you emit.

Course ID: ${course.id}
Progress: ${completedCount}/${totalCount} sections completed

FULL COURSE PLAN (use EXACT IDs):
${planText || '  (no sections defined)'}

CURRENT TEACHING TARGET:
${
	currentItem
		? `  Chapter: "${currentItem.chapter.title}" [chapter_id=${currentItem.chapter.id}]
  Section:  "${currentItem.section.title}" [section_id=${currentItem.section.id}]
  Status:   ${currentItem.section.status}`
		: '  (none)'
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY RULES FOR PROGRESS MARKERS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULE 1: When you START teaching a section → emit in-progress marker.
RULE 2: When you FINISH a section (explained + example + summary, OR you move to next section) → emit completed marker.
RULE 3: You MUST emit at least one marker per response (unless it's purely a greeting with zero teaching).
RULE 4: NEVER downgrade a completed section.
RULE 5: Use ONLY the exact chapter_id and section_id values from the plan above.
RULE 6: Markers are INVISIBLE to the student. NEVER mention COURSE_PROGRESS to them.
RULE 7: Place ALL markers at the VERY END of your response, each on its own line.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXACT FORMAT (copy exactly, no spaces inside tags):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<COURSE_PROGRESS>{"chapter_id":"EXACT_ID","section_id":"EXACT_ID","status":"in-progress"}</COURSE_PROGRESS>
<COURSE_PROGRESS>{"chapter_id":"EXACT_ID","section_id":"EXACT_ID","status":"completed"}</COURSE_PROGRESS>

EXAMPLES:
• You explained sec1-1 fully and move to sec1-2:
<COURSE_PROGRESS>{"chapter_id":"ch1","section_id":"sec1-1","status":"completed"}</COURSE_PROGRESS>
<COURSE_PROGRESS>{"chapter_id":"ch1","section_id":"sec1-2","status":"in-progress"}</COURSE_PROGRESS>

• You just started sec2-1:
<COURSE_PROGRESS>{"chapter_id":"ch2","section_id":"sec2-1","status":"in-progress"}</COURSE_PROGRESS>

• You finished the last section sec5-2:
<COURSE_PROGRESS>{"chapter_id":"ch5","section_id":"sec5-2","status":"completed"}</COURSE_PROGRESS>
=========================================================`.trim();
	} catch (e) {
		console.error('[CourseProgress] Failed to build tracking prompt:', e);
		return '';
	}
}

// ─────────────────────────────────────────────────────────────────────────────
// Plan index helpers for heuristic detection
// ─────────────────────────────────────────────────────────────────────────────
interface PlanIndex {
	bySectionId: Map<string, { chapterId: string; sectionTitle: string; chapterTitle: string }>;
	bySectionTitle: Array<{
		chapterId: string;
		sectionId: string;
		sectionTitle: string;
		chapterTitle: string;
	}>;
	currentStatusMap: Map<string, CourseSectionStatus>;
	chaptersOrdered: Array<{ chapterId: string; sections: string[] }>;
}

async function buildPlanIndex(token: string, courseId: string): Promise<PlanIndex> {
	const index: PlanIndex = {
		bySectionId: new Map(),
		bySectionTitle: [],
		currentStatusMap: new Map(),
		chaptersOrdered: []
	};
	try {
		const course = await getCourseById(token, courseId);
		for (const chapter of course.chapters ?? []) {
			const sectionIds: string[] = [];

			for (const section of chapter.sections ?? []) {
				sectionIds.push(section.id);

				const key = `${chapter.id}:${section.id}`;
				index.bySectionId.set(section.id, {
					chapterId: chapter.id,
					sectionTitle: section.title,
					chapterTitle: chapter.title
				});
				index.bySectionTitle.push({
					chapterId: chapter.id,
					sectionId: section.id,
					sectionTitle: section.title,
					chapterTitle: chapter.title
				});
				index.currentStatusMap.set(key, section.status);
			}

			index.chaptersOrdered.push({
				chapterId: chapter.id,
				sections: sectionIds
			});
		}
	} catch (e) {
		console.warn('[CourseProgress] Could not load plan for heuristic detection:', e);
	}
	return index;
}

function normaliseForMatch(text: string): string {
	return text
		.toLowerCase()
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
		.replace(/[^a-z0-9]+/g, ' ')
		.trim();
}

function detectHeuristicSignals(content: string, planIndex: PlanIndex): CourseProgressSignal[] {
	if (!content || planIndex.bySectionTitle.length === 0) return [];

	const results: CourseProgressSignal[] = [];
	const seen = new Set<string>();
	const normalisedFull = normaliseForMatch(content);

	// Patterns indicating a section was COMPLETED
	const completionPatterns = [
		/(nous avons|on a|j'?ai|vous avez)\s+(termin[ée]|fini|complet[ée]|boucl[ée])\s+(la\s+)?(section|partie|le[cç]on)\s*\d*\s*[:\-]?\s*([^\n.!?]{3,60})/gi,
		/(termin[ée]|fini|complet[ée]|boucl[ée])\s+(la\s+)?(section|partie|le[cç]on)\s*\d*\s*[:\-]?\s*([^\n.!?]{3,60})/gi,
		/(end|completed|finished)\s+(of\s+)?section\s*\d*\s*[:\-]?\s*([^\n.!?]{3,60})/gi,
		/passons\s+(maintenant\s+)?(à|a)\s+(?:la\s+)?(?:section|partie)\s*\d*\s*[:\-]?\s*([^\n.!?]{3,60})/gi
	];

	// Patterns indicating a section is IN PROGRESS
	const inProgressPatterns = [
		/(commen[cç]ons|d[ée]marrons|abordons|voyons|[ée]tudions)\s+(?:maintenant\s+)?([^\n.!?,]{3,60})/gi,
		/(let'?s\s+(?:start|begin|explore|study|look\s+at))\s+([^\n.!?,]{3,60})/gi,
		/(?:section|partie|le[cç]on)\s+\d+\s*[:\-]\s*([^\n.!?]{3,60})/gi,
		/chapitre\s+\d+\s*[:\-]\s*([^\n.!?]{3,60})/gi
	];

	function matchTitleToPlan(rawTitle: string): { chapterId: string; sectionId: string } | null {
		const normTitle = normaliseForMatch(rawTitle);
		if (!normTitle || normTitle.length < 3) return null;

		let best: { chapterId: string; sectionId: string; score: number } | null = null;

		for (const item of planIndex.bySectionTitle) {
			const normSection = normaliseForMatch(item.sectionTitle);
			if (!normSection) continue;

			let score = 0;
			if (normSection === normTitle) {
				score = 1000;
			} else if (normTitle.includes(normSection)) {
				score = normSection.length * 2;
			} else if (normSection.includes(normTitle) && normTitle.length >= 4) {
				score = normTitle.length;
			} else {
				const words = normSection.split(' ').filter((w) => w.length >= 4);
				if (words.length > 0) {
					const matched = words.filter((w) => normTitle.includes(w)).length;
					if (matched >= Math.max(2, Math.ceil(words.length * 0.6))) {
						score = matched * 5;
					}
				}
			}

			if (score > 0 && (!best || score > best.score)) {
				best = { chapterId: item.chapterId, sectionId: item.sectionId, score };
			}
		}

		return best && best.score >= 10 ? { chapterId: best.chapterId, sectionId: best.sectionId } : null;
	}

	function addSignal(signal: CourseProgressSignal) {
		const key = `${signal.chapter_id}:${signal.section_id}:${signal.status}`;
		if (seen.has(key)) return;
		seen.add(key);
		results.push(signal);
	}

	for (const pattern of completionPatterns) {
		let m: RegExpExecArray | null;
		pattern.lastIndex = 0;
		while ((m = pattern.exec(content)) !== null) {
			const rawTitle = m[m.length - 1] ?? '';
			const matched = matchTitleToPlan(rawTitle);
			if (matched) addSignal({ chapter_id: matched.chapterId, section_id: matched.sectionId, status: 'completed', reason: 'heuristic:completion' });
		}
	}

	for (const pattern of inProgressPatterns) {
		let m: RegExpExecArray | null;
		pattern.lastIndex = 0;
		while ((m = pattern.exec(content)) !== null) {
			const rawTitle = m[m.length - 1] ?? '';
			const matched = matchTitleToPlan(rawTitle);
			if (matched) addSignal({ chapter_id: matched.chapterId, section_id: matched.sectionId, status: 'in-progress', reason: 'heuristic:in-progress' });
		}
	}

	// Fallback: section title mentioned in content and currently not-started
	if (results.length === 0) {
		for (const item of planIndex.bySectionTitle) {
			const normSection = normaliseForMatch(item.sectionTitle);
			if (!normSection || normSection.length < 4) continue;
			if (normalisedFull.includes(normSection)) {
				const currentStatus = planIndex.currentStatusMap.get(`${item.chapterId}:${item.sectionId}`);
				if (currentStatus === 'not-started') {
					addSignal({ chapter_id: item.chapterId, section_id: item.sectionId, status: 'in-progress', reason: 'heuristic:title-mention' });
				}
			}
		}
	}

	return results;
}
function detectOrdinalSignals(content: string, planIndex: PlanIndex): CourseProgressSignal[] {
	if (!content || planIndex.chaptersOrdered.length === 0) return [];

	const out: CourseProgressSignal[] = [];
	const seen = new Set<string>();

	// ex: "terminé la section 3 du chapitre 2"
	const regex =
		/(termin[ée]|fini|completed|finished)[^.!?\n]{0,120}?(section|partie)\s*(\d+)[^.!?\n]{0,120}?(chapitre|chapter)\s*(\d+)/gi;

	let m: RegExpExecArray | null;
	while ((m = regex.exec(content)) !== null) {
		const sectionNum = Number(m[3]);
		const chapterNum = Number(m[5]);

		if (!Number.isFinite(sectionNum) || !Number.isFinite(chapterNum)) continue;
		if (chapterNum < 1 || sectionNum < 1) continue;

		const ch = planIndex.chaptersOrdered[chapterNum - 1];
		if (!ch) continue;

		const secId = ch.sections[sectionNum - 1];
		if (!secId) continue;

		const key = `${ch.chapterId}:${secId}:completed`;
		if (seen.has(key)) continue;
		seen.add(key);

		out.push({
			chapter_id: ch.chapterId,
			section_id: secId,
			status: 'completed',
			reason: 'heuristic:ordinal-completion'
		});
	}

	return out;
}

// ─────────────────────────────────────────────────────────────────────────────
// applyCourseProgressSignalsFromContent  ← called from Chat.svelte
// ─────────────────────────────────────────────────────────────────────────────
export async function applyCourseProgressSignalsFromContent(args: {
	token: string;
	courseId: string;
	content: string;
}): Promise<{
	cleanedContent: string;
	extracted: CourseProgressSignal[];
	heuristic: CourseProgressSignal[];
	applied: CourseProgressSignal[];
	skipped: CourseProgressSignal[];
}> {
	const { token, courseId, content } = args;

	// Step 1: extract explicit markers from AI response
	const { cleanedContent, updates } = extractCourseProgressSignalsFromContent(content);

	const applied: CourseProgressSignal[] = [];
	const skipped: CourseProgressSignal[] = [];

	if (!token || !courseId) {
		console.warn('[CourseProgress] Missing token or courseId — skipping progress update');
		return { cleanedContent, extracted: updates, heuristic: [], applied, skipped: updates };
	}

	// Step 2: build plan index for heuristic fallback AND for number-to-ID mapping
	const planIndex = await buildPlanIndex(token, courseId);

	// NEW: Map numeric chapter/section indices to actual IDs
	const mappedUpdates = updates.map(update => {
		const chapterId = update.chapter_id;
		const sectionId = update.section_id;
		
		// Check if chapter_id looks like a number (1, 2, 3)
		const chapterNum = parseInt(chapterId, 10);
		const sectionNum = parseInt(sectionId, 10);
		
		if (!isNaN(chapterNum) && !isNaN(sectionNum)) {
			// Try to find matching chapter/section by index
			const chapterIndex = chapterNum - 1; // 1-based to 0-based
			const sectionIndex = sectionNum - 1;
			
			const matchingItem = planIndex.bySectionTitle.find((item: any, idx: number) => {
				// Find by position in the flat list (approximate)
				let currentChapterIdx = 0;
				let currentSectionIdx = 0;
				let prevChapterId = '';
				
				for (let i = 0; i < planIndex.bySectionTitle.length; i++) {
					const current = planIndex.bySectionTitle[i];
					if (current.chapterId !== prevChapterId) {
						currentChapterIdx++;
						currentSectionIdx = 0;
						prevChapterId = current.chapterId;
					} else {
						currentSectionIdx++;
					}
					
					if (currentChapterIdx === chapterNum && currentSectionIdx === sectionNum) {
						return true;
					}
				}
				return false;
			});
			
			if (matchingItem) {
				console.log(`[CourseProgress] Mapped numeric ${chapterNum}.${sectionNum} → ${matchingItem.chapterId}:${matchingItem.sectionId}`);
				return {
					...update,
					chapter_id: matchingItem.chapterId,
					section_id: matchingItem.sectionId
				};
			}
		}
		
		return update;
	});

	// Step 3: heuristic detection from text when no explicit markers found
	const heuristic =
		updates.length === 0
			? [...detectHeuristicSignals(content, planIndex), ...detectOrdinalSignals(content, planIndex)]
			: [];

	// Step 4: merge, AI markers win over heuristic on conflict
	const rank = (s: CourseSectionStatus) => (s === 'completed' ? 2 : s === 'in-progress' ? 1 : 0);
	const merged = new Map<string, CourseProgressSignal>();

	function addToMerged(signal: CourseProgressSignal) {
		const key = `${signal.chapter_id}:${signal.section_id}`;
		const existing = merged.get(key);
		if (!existing || rank(signal.status) > rank(existing.status)) merged.set(key, signal);
	}

	for (const s of heuristic) addToMerged(s);
	for (const s of mappedUpdates) addToMerged(s); // AI markers override heuristic

	console.log(`[CourseProgress] courseId=${courseId} extracted=${updates.length} mapped=${mappedUpdates.length} heuristic=${heuristic.length} toApply=${merged.size}`);

	// Auto-complete previous chapters AND previous sections within the same chapter
	let maxAdvancedChapterIdx = -1;

	// Track the earliest "in-progress" or "completed" section per chapter
	const activeChapterSections = new Map<string, number>(); // chapterId → earliest active section index

	for (const u of merged.values()) {
		const chIdx = planIndex.chaptersOrdered.findIndex((c) => c.chapterId === u.chapter_id);
		if (chIdx < 0) continue;

		if (u.status === 'in-progress' || u.status === 'completed') {
			if (chIdx > maxAdvancedChapterIdx) maxAdvancedChapterIdx = chIdx;

			// Track the section index within this chapter
			const ch = planIndex.chaptersOrdered[chIdx];
			const secIdx = ch.sections.indexOf(u.section_id);
			if (secIdx > 0) {
				const existing = activeChapterSections.get(u.chapter_id) ?? -1;
				if (secIdx > existing) activeChapterSections.set(u.chapter_id, secIdx);
			}
		}
	}

	// Complete all sections of previous chapters
	if (maxAdvancedChapterIdx > 0) {
		for (let i = 0; i < maxAdvancedChapterIdx; i++) {
			const ch = planIndex.chaptersOrdered[i];
			for (const secId of ch.sections) {
				const key = `${ch.chapterId}:${secId}`;
				const current = planIndex.currentStatusMap.get(key);
				if (current !== 'completed') {
					merged.set(key, {
						chapter_id: ch.chapterId,
						section_id: secId,
						status: 'completed',
						reason: 'auto-complete-previous-chapters'
					});
				}
			}
		}
	}

	// Complete previous sections within the same chapter
	for (const [chapterId, activeSecIdx] of activeChapterSections.entries()) {
		const ch = planIndex.chaptersOrdered.find((c) => c.chapterId === chapterId);
		if (!ch) continue;
		for (let i = 0; i < activeSecIdx; i++) {
			const secId = ch.sections[i];
			if (!secId) continue;
			const key = `${chapterId}:${secId}`;
			const current = planIndex.currentStatusMap.get(key);
			if (current !== 'completed') {
				merged.set(key, {
					chapter_id: chapterId,
					section_id: secId,
					status: 'completed',
					reason: 'auto-complete-previous-sections'
				});
			}
		}
	}
	// Step 5: apply each update via backend API
	for (const update of merged.values()) {
		if (update.status === 'not-started') {
			skipped.push(update);
			continue;
		}

		const key = `${update.chapter_id}:${update.section_id}`;
		const currentStatus = planIndex.currentStatusMap.get(key);

		// Don't downgrade completed sections
		if (currentStatus === 'completed' && update.status !== 'completed') {
			console.log(`[CourseProgress] Skipping downgrade: ${key} is already completed`);
			skipped.push(update);
			continue;
		}

		// Skip no-ops
		if (currentStatus === update.status) {
			skipped.push(update);
			continue;
		}

		try {
			await updateSectionProgress(token, courseId, update.chapter_id, update.section_id, update.status);
			console.log(`[CourseProgress] ✅ Applied: ${key} → ${update.status}`);
			applied.push(update);
			
			// NEW: Dispatch event to refresh UI immediately
			if (typeof window !== 'undefined') {
				window.dispatchEvent(new CustomEvent('sectionProgressUpdated', { 
					detail: { courseId, chapterId: update.chapter_id, sectionId: update.section_id, status: update.status }
				}));
			}
		} catch (e) {
			console.error(`[CourseProgress] ❌ Failed to apply: ${key} → ${update.status}`, e);
			skipped.push(update);
		}
	}

	return { cleanedContent, extracted: updates, heuristic, applied, skipped };
}