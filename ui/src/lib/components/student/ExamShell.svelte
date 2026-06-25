<script lang="ts">
	import { createEventDispatcher, onMount, onDestroy, getContext } from 'svelte';
	import { reportViolation, submitExam, terminateExam, type ExamConfig } from '$lib/apis/exams';
	import { submitAssignment, downloadAssignmentAttachment } from '$lib/apis/assignments';

	export let assignment: {
		id: string;
		title: string;
		instructions?: string | null;
		attachment_id?: string | null;
		attachment_name?: string | null;
	};
	export let config: ExamConfig;
	export let violations = 0;
	export let startedAt: string | null = null;

	const i18n: any = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';
	const dispatch = createEventDispatcher();

	let content = '';
	let warning = '';
	let ended = false;
	let endedMsg = '';
	let submitting = false;
	const max = config.max_violations;

	// ── timers: exam duration + per-warning "away" grace ──────────────────────
	let now = Date.now();
	let clock: ReturnType<typeof setInterval>;
	// The server sends `started_at` as naive UTC (no timezone). `new Date('…')` would
	// read that as *local* time, so we append 'Z' to parse it as UTC.
	function parseUtcMs(ts: string | null): number {
		if (!ts) return 0;
		const hasTz = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(ts);
		return new Date(hasTz ? ts : ts + 'Z').getTime();
	}
	const deadlineMs =
		config.time_limit_minutes && startedAt
			? parseUtcMs(startedAt) + config.time_limit_minutes * 60000
			: 0;
	$: remainingMs = deadlineMs ? Math.max(0, deadlineMs - now) : 0;
	$: timeLeft = deadlineMs
		? `${Math.floor(remainingMs / 60000)}:${String(Math.floor((remainingMs % 60000) / 1000)).padStart(2, '0')}`
		: '';
	$: timeLow = deadlineMs > 0 && remainingMs <= 60000;

	// Per-warning "away" grace: a deadline checked by the main 1s clock — robust against
	// background-tab timer throttling, and re-checked the instant the tab refocuses.
	let graceDeadline = 0;
	$: graceLeftMs = graceDeadline ? Math.max(0, graceDeadline - now) : 0;
	$: graceLeft = graceDeadline
		? `${Math.floor(graceLeftMs / 60000)}:${String(Math.floor((graceLeftMs % 60000) / 1000)).padStart(2, '0')}`
		: '';
	function startGrace(seconds: number) {
		graceDeadline = Date.now() + seconds * 1000;
	}
	function clearGrace() {
		graceDeadline = 0;
	}
	function checkDeadlines() {
		now = Date.now();
		if (deadlineMs && now >= deadlineMs && !ended) terminate('time_expired');
		else if (graceDeadline && now >= graceDeadline && !ended) terminate('away_timeout');
	}

	async function terminate(reason: string) {
		if (ended) return;
		ended = true;
		clearGrace();
		endedMsg =
			reason === 'time_expired'
				? $i18n.t('Time is up — your exam was submitted.')
				: $i18n.t('Your exam was submitted — you stayed away too long.');
		try {
			await submitAssignment(token(), assignment.id, content.trim());
		} catch (_) {}
		try {
			await terminateExam(token(), assignment.id, reason);
		} catch (_) {}
		dispatch('done', { terminated: true });
	}

	// Exam paper (PDF or other attachment) shown alongside the answer area.
	let attachmentUrl = '';
	$: isPdf = (assignment.attachment_name ?? '').toLowerCase().endsWith('.pdf');
	async function loadAttachment() {
		if (!assignment.attachment_id) return;
		try {
			const blob = await downloadAssignmentAttachment(token(), assignment.id);
			attachmentUrl = URL.createObjectURL(blob);
		} catch (_) {
			/* ignore — student can still answer */
		}
	}

	async function enterFullscreen() {
		try {
			if (config.require_fullscreen && !document.fullscreenElement)
				await document.documentElement.requestFullscreen();
		} catch (_) {
			/* needs a gesture; the Start click provides it */
		}
	}

	async function flag(type: string) {
		if (ended) return;
		try {
			const res = await reportViolation(token(), assignment.id, type);
			violations = res.session.violation_count;
			if (res.action === 'terminated') {
				ended = true;
				clearGrace();
				endedMsg = $i18n.t('Your exam was ended after too many warnings.');
				try {
					await submitAssignment(token(), assignment.id, content.trim());
				} catch (_) {}
				dispatch('done', { terminated: true });
			} else {
				// Graced warning: a deadline starts; returning to compliance clears it.
				if (res.grace_seconds > 0) startGrace(res.grace_seconds);
				warning = max
					? $i18n
							.t('You left the exam — this was recorded. Warning {{n}} of {{m}}.')
							.replace('{{n}}', String(violations))
							.replace('{{m}}', String(max))
					: $i18n
							.t('You left the exam — this was recorded ({{n}}).')
							.replace('{{n}}', String(violations));
			}
		} catch (_) {}
	}

	function dismissWarning() {
		clearGrace();
		warning = '';
		// If fullscreen is required and we're out of it, the click re-enters it.
		if (config.require_fullscreen && !document.fullscreenElement) enterFullscreen();
	}

	function onVisibility() {
		if (document.hidden) {
			flag('left_page');
		} else {
			checkDeadlines(); // auto-submit if the grace already expired while away
			if (!ended) clearGrace(); // back in time → stop the countdown
		}
	}
	function onFullscreenChange() {
		if (!config.require_fullscreen) return;
		if (!document.fullscreenElement && !ended) flag('fullscreen_exit');
		else if (document.fullscreenElement) clearGrace(); // re-entered → stop the countdown
	}
	function onBeforeUnload(e: BeforeUnloadEvent) {
		if (!ended) {
			e.preventDefault();
			e.returnValue = '';
		}
	}
	function onOverlayClick() {
		if (config.require_fullscreen && !document.fullscreenElement && !ended) enterFullscreen();
	}

	async function submit() {
		if (!content.trim() || submitting || ended) return;
		submitting = true;
		try {
			await submitAssignment(token(), assignment.id, content.trim());
			await submitExam(token(), assignment.id).catch(() => {});
			ended = true;
			endedMsg = $i18n.t('Your exam has been submitted.');
			dispatch('done', { terminated: false });
		} catch (e: any) {
			warning = typeof e === 'string' ? e : $i18n.t('Could not submit your work');
		} finally {
			submitting = false;
		}
	}

	function exitFullscreen() {
		try {
			if (document.fullscreenElement) document.exitFullscreen();
		} catch (_) {}
	}

	onMount(() => {
		enterFullscreen();
		loadAttachment();
		clock = setInterval(checkDeadlines, 1000);
		document.addEventListener('visibilitychange', onVisibility);
		document.addEventListener('fullscreenchange', onFullscreenChange);
		window.addEventListener('beforeunload', onBeforeUnload);
	});
	onDestroy(() => {
		clearInterval(clock);
		clearGrace();
		document.removeEventListener('visibilitychange', onVisibility);
		document.removeEventListener('fullscreenchange', onFullscreenChange);
		window.removeEventListener('beforeunload', onBeforeUnload);
		if (attachmentUrl) URL.revokeObjectURL(attachmentUrl);
		exitFullscreen();
	});
</script>

<!-- E10: full-screen proctored exam shell -->
<div
	class="fixed inset-0 z-[9998] flex flex-col bg-gray-900 text-white"
	role="application"
	on:click={onOverlayClick}
>
	<!-- Top bar -->
	<div class="flex items-center justify-between px-6 py-4 border-b border-white/10 shrink-0">
		<div class="flex items-center gap-3">
			<span class="h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse"></span>
			<span class="font-semibold">{$i18n.t('Exam in progress')}</span>
			<span class="text-white/50 text-sm">· {assignment.title}</span>
		</div>
		<div class="flex items-center gap-5 text-sm">
			{#if deadlineMs}
				<span
					class={`inline-flex items-center gap-1.5 font-mono font-semibold ${timeLow ? 'text-red-400' : 'text-white/80'}`}
				>
					⏱ {timeLeft}
				</span>
			{/if}
			<span class="text-white/70">
				{#if max}
					{$i18n.t('Warnings')}: {violations}/{max}
				{:else}
					{$i18n.t('Warnings')}: {violations}
				{/if}
			</span>
		</div>
	</div>

	{#if warning && !ended}
		<!-- Centered red warning — always on top, never hidden behind the sidebar -->
		<div class="fixed inset-0 z-[10000] flex items-center justify-center bg-black/70 p-4">
			<div
				class="w-full max-w-md rounded-2xl bg-white dark:bg-gray-800 border-t-4 border-red-600 shadow-2xl p-7 text-center"
			>
				<div class="text-5xl mb-3">⚠️</div>
				<h2 class="text-xl font-bold text-red-600 dark:text-red-400 mb-2">
					{$i18n.t('Warning')}
				</h2>
				<p class="text-gray-700 dark:text-gray-200 mb-4">{warning}</p>
				{#if graceDeadline}
					<div class="mb-5">
						<div class="text-xs uppercase tracking-wide text-gray-400 mb-1">
							{$i18n.t('Auto-submitting in')}
						</div>
						<div class="text-4xl font-mono font-bold text-red-600 dark:text-red-400">
							{graceLeft}
						</div>
						<p class="text-xs text-gray-400 mt-2">
							{$i18n.t('Return to your exam now to keep going.')}
						</p>
					</div>
				{/if}
				<button
					class="px-6 py-2.5 rounded-full bg-red-600 hover:bg-red-700 text-white font-semibold text-sm"
					on:click={dismissWarning}
				>
					{$i18n.t('Return to exam')}
				</button>
			</div>
		</div>
	{/if}

	{#if ended}
		<!-- Body: ended -->
		<div class="flex-1 overflow-y-auto px-6 py-6">
			<div class="max-w-2xl mx-auto text-center py-20">
				<div class="text-4xl mb-4">{endedMsg.includes('ended') ? '🚫' : '✅'}</div>
				<h2 class="text-xl font-semibold mb-2">{endedMsg}</h2>
				<p class="text-white/60 mb-8">{$i18n.t('You can now leave this page.')}</p>
				<button
					class="px-6 py-2.5 rounded-full bg-white/10 hover:bg-white/20 text-sm font-medium"
					on:click={() => dispatch('close')}
				>
					{$i18n.t('Close')}
				</button>
			</div>
		</div>
	{:else}
		<!-- Body: exam paper (left) + answer (right) -->
		<div class="flex-1 min-h-0 flex flex-col lg:flex-row">
			{#if attachmentUrl}
				<div
					class="lg:w-1/2 lg:border-r border-white/10 bg-white/5 flex flex-col min-h-[45vh] lg:min-h-0"
				>
					<div class="px-4 py-2 text-xs text-white/50 border-b border-white/10 shrink-0">
						📄 {assignment.attachment_name ?? $i18n.t('Exam paper')}
					</div>
					{#if isPdf}
						<iframe title={$i18n.t('Exam paper')} src={attachmentUrl} class="w-full flex-1 bg-white"
						></iframe>
					{:else}
						<div class="m-auto text-center text-white/70 p-6">
							<a href={attachmentUrl} download={assignment.attachment_name} class="underline">
								📎 {assignment.attachment_name ?? $i18n.t('Download attachment')}
							</a>
						</div>
					{/if}
				</div>
			{/if}

			<div class="flex-1 overflow-y-auto px-6 py-6">
				<div class="max-w-2xl mx-auto">
					<p class="text-white/60 text-sm mb-4">
						{$i18n.t(
							'Stay on this page until you submit. Leaving the page or exiting full screen is recorded and your teacher is notified.'
						)}
					</p>
					{#if assignment.instructions}
						<div class="rounded-xl bg-white/5 p-4 text-sm whitespace-pre-wrap mb-5">
							{assignment.instructions}
						</div>
					{/if}
					<label class="block text-sm text-white/70 mb-1">{$i18n.t('Your answer')}</label>
					<textarea
						rows="12"
						bind:value={content}
						placeholder={$i18n.t('Type your answer…')}
						class="w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-blue-400"
					></textarea>
					<div class="flex justify-end mt-5">
						<button
							class="px-6 py-2.5 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-90 text-sm font-semibold disabled:opacity-50"
							on:click={submit}
							disabled={submitting || !content.trim()}
						>
							{submitting ? $i18n.t('Submitting…') : $i18n.t('Submit exam')}
						</button>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
