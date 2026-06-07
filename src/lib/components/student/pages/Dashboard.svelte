<!-- Dashboard.svelte -->
<script lang="ts">
	import { getContext, onMount, onDestroy } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { chatId as storeChatId } from '$lib/stores';
	import CourseCard from '../elements/CourseCard.svelte';
    import EngagementChart from '$lib/components/student/elements/EngagementChart.svelte';
	import { getSupportRequests, type SupportResponse, updateSupportChatId } from '$lib/apis/supports';
	import { page } from '$app/stores';

	const i18n = getContext<Writable<i18nType>>('i18n');
	type PerfFilter = 'weekly' | 'monthly';
	const perfOptions: PerfFilter[] = ['weekly', 'monthly'];
	// ─── SUPPORT / COURSE STATE ───────────────────────────────────────────────
	let userSupports: SupportResponse[] = [];
	let isLoading = true;
	let pendingSupportId = '';
	let chatIdSubscription: Function;
	let urlCheckInterval: ReturnType<typeof setInterval>;
	let currentPath = '';
	let chatIdFromURL = '';

	// ─── PERFORMANCE DASHBOARD STATE ─────────────────────────────────────────
	let perfFilter: 'monthly' | 'weekly' = 'monthly';

	const statsByFilter = {
		monthly: { participation: 90, tasksExam: 70, quiz: 85, gradesCompleted: 75 },
		weekly:  { participation: 72, tasksExam: 55, quiz: 68, gradesCompleted: 60 }
	};
	const pointsByFilter    = { monthly: 8966, weekly: 3241 };
	const maxPointsByFilter = { monthly: 12000, weekly: 5000 };

	$: perfStats     = statsByFilter[perfFilter];
	$: perfPoints    = pointsByFilter[perfFilter];
	$: perfMaxPoints = maxPointsByFilter[perfFilter];

	// Animated values
	let animGrades        = 0;
	let animPoints        = 0;
	let animNeedle        = 0;
	let animParticipation = 0;
	let animTasksExam     = 0;
	let animQuiz          = 0;

	let rafGrades: number;
	let rafPoints: number;

	function animateTo(from: number, to: number, duration: number, setter: (v: number) => void): number {
		const t0 = performance.now();
		const step = (now: number) => {
			const p = Math.min((now - t0) / duration, 1);
			const ease = 1 - Math.pow(1 - p, 3);
			setter(from + (to - from) * ease);
			if (p < 1) requestAnimationFrame(step);
		};
		return requestAnimationFrame(step);
	}

	function triggerPerfAnimations() {
		cancelAnimationFrame(rafGrades);
		cancelAnimationFrame(rafPoints);
		const pg = animGrades, pp = animPoints, pn = animNeedle;
		const ppar = animParticipation, pte = animTasksExam, pq = animQuiz;
		rafGrades = animateTo(pg, perfStats.gradesCompleted, 1000, v => animGrades = v);
		rafPoints = animateTo(pp, perfPoints, 1000, v => animPoints = v);
		animateTo(pn, perfPoints / perfMaxPoints, 1000, v => animNeedle = v);
		animateTo(ppar, perfStats.participation, 900, v => animParticipation = v);
		animateTo(pte, perfStats.tasksExam, 900, v => animTasksExam = v);
		animateTo(pq, perfStats.quiz, 900, v => animQuiz = v);
	}

	$: if (browser && perfFilter) triggerPerfAnimations();

	// SVG ring for grades
	const ringR    = 52;
	const ringCirc = 2 * Math.PI * ringR;
	$: ringOffset  = ringCirc - (animGrades / 100) * ringCirc;

	// SVG gauge (half-circle)
	const gcx = 100, gcy = 90, gR = 70;
	function polar(deg: number, r: number) {
		const rad = (deg * Math.PI) / 180;
		return { x: gcx + r * Math.cos(rad), y: gcy - r * Math.sin(rad) };
	}
	const gArcStart = polar(180, gR);
	const gArcEnd   = polar(0,   gR);
	const gBgPath   = `M ${gArcStart.x} ${gArcStart.y} A ${gR} ${gR} 0 0 1 ${gArcEnd.x} ${gArcEnd.y}`;

	$: gNeedleAngle = 180 - animNeedle * 180;
	$: gNeedleTip   = polar(gNeedleAngle, gR - 12);
	$: gFillEnd     = polar(gNeedleAngle, gR);
	$: gFillLarge   = animNeedle > 0.5 ? 1 : 0;
	$: gFillPath    = `M ${gArcStart.x} ${gArcStart.y} A ${gR} ${gR} 0 ${gFillLarge} 1 ${gFillEnd.x} ${gFillEnd.y}`;

	function zoneArc(from: number, to: number, r: number) {
		const s = polar(from, r), e = polar(to, r);
		return `M ${s.x} ${s.y} A ${r} ${r} 0 0 1 ${e.x} ${e.y}`;
	}

	// ─── CALENDAR STATE ───────────────────────────────────────────────────────
	const today   = new Date();
	let calYear   = today.getFullYear();
	let calMonth  = today.getMonth();
	let calSelected = today.getDate();
	const eventDays = [3, 10, 17, 24];
	const DOW  = ['SUN','MON','TUE','WED','THU','FRI','SAT'];
	const MONS = ['January','February','March','April','May','June','July','August','September','October','November','December'];

	$: calDays  = new Date(calYear, calMonth + 1, 0).getDate();
	$: calFirst = new Date(calYear, calMonth, 1).getDay();
	$: calCells = [...Array(calFirst).fill(null), ...Array.from({ length: calDays }, (_, i) => i + 1)];

	function calPrev() { if (calMonth === 0) { calMonth = 11; calYear--; } else calMonth--; calSelected = 0; }
	function calNext() { if (calMonth === 11) { calMonth = 0; calYear++; } else calMonth++; calSelected = 0; }
	function isToday(d: number) { return d === today.getDate() && calMonth === today.getMonth() && calYear === today.getFullYear(); }
	function isSunSat(d: number | null) {
		if (!d) return false;
		return new Date(calYear, calMonth, d).getDay() % 6 === 0;
	}

	// ─── DATE RANGE LABEL ─────────────────────────────────────────────────────
	$: dateRange = (() => {
		const now = new Date();
		if (perfFilter === 'monthly') return `${MONS[now.getMonth()]} ${now.getFullYear()}`;
		const day = now.getDay();
		const diff = now.getDate() - day + (day === 0 ? -6 : 1);
		const ws = new Date(now); ws.setDate(diff);
		const we = new Date(ws); we.setDate(ws.getDate() + 6);
		return `${ws.toLocaleDateString('en-US',{month:'short',day:'numeric'})} – ${we.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})}`;
	})();

	// ─── SUPPORT LOGIC ────────────────────────────────────────────────────────
	onMount(async () => {
		if (browser) {
			storeChatId.set('');
			if (sessionStorage.selectedModels) sessionStorage.removeItem('selectedModels');
			if (localStorage.getItem('pendingSupportData')) localStorage.removeItem('pendingSupportData');
			const keysToRemove: string[] = [];
			for (let i = 0; i < localStorage.length; i++) {
				const key = localStorage.key(i);
				if (key?.startsWith('chat-input-')) keysToRemove.push(key);
			}
			keysToRemove.forEach(k => localStorage.removeItem(k));

			const token = localStorage.getItem('token');
			if (token) {
				try {
					const supports = await getSupportRequests(token);
					if (supports && Array.isArray(supports)) userSupports = supports;
				} catch { userSupports = []; } finally { isLoading = false; }
			} else { isLoading = false; }

			if (!window.openTutorEvents) window.openTutorEvents = new EventTarget();
			window.openTutorEvents.addEventListener('chatCreated', ((e: CustomEvent) => {
				const newChatId = e.detail?.chatId;
				if (newChatId && pendingSupportId) updateSupportWithChatId(pendingSupportId, newChatId);
			}) as EventListener);

			chatIdSubscription = storeChatId.subscribe((newChatId) => {
				if (newChatId && newChatId !== 'local' && pendingSupportId) updateSupportWithChatId(pendingSupportId, newChatId);
			});

			urlCheckInterval = setInterval(() => {
				try {
					const d = localStorage.getItem('pendingSupportData');
					if (!d) { clearInterval(urlCheckInterval); return; }
					const sd = JSON.parse(d);
					if (Date.now() - (sd.timestamp || 0) >= 30 * 60 * 1000) { localStorage.removeItem('pendingSupportData'); clearInterval(urlCheckInterval); return; }
					const cur = window.location.pathname;
					if (cur.startsWith('/student/c/')) {
						const cid = cur.split('/student/c/')[1].split('/')[0];
						if (cid && sd.id) updateSupportWithChatId(sd.id, cid);
					}
				} catch { localStorage.removeItem('pendingSupportData'); clearInterval(urlCheckInterval); }
			}, 1000);

			triggerPerfAnimations();
		}
	});

	onDestroy(() => {
		if (browser) {
			if (chatIdSubscription) chatIdSubscription();
			if (urlCheckInterval) clearInterval(urlCheckInterval);
			cancelAnimationFrame(rafGrades);
			cancelAnimationFrame(rafPoints);
		}
	});

	$: if ($page && $page.url && browser) {
		currentPath = $page.url.pathname || '';
		if (currentPath.startsWith('/student/c/')) {
			chatIdFromURL = currentPath.replace('/student/c/', '').split('/')[0];
			if (chatIdFromURL && localStorage.getItem('pendingSupportData')) {
				try {
					const sd = JSON.parse(localStorage.getItem('pendingSupportData') || '{}');
					if (sd.id && Date.now() - (sd.timestamp || 0) < 30 * 60 * 1000) updateSupportWithChatId(sd.id, chatIdFromURL);
					else localStorage.removeItem('pendingSupportData');
				} catch { localStorage.removeItem('pendingSupportData'); }
			}
		}
	}

	async function updateSupportWithChatId(supportId: string, chatId: string) {
		if (!supportId || !chatId || !browser || chatId === 'local' || chatId === 'undefined') return;
		let pendingSupportData: string | null;
		try {
			pendingSupportData = localStorage.getItem('pendingSupportData');
			if (!pendingSupportData) return;
			const sd = JSON.parse(pendingSupportData);
			if (sd.id !== supportId) return;
			if (Date.now() - (sd.timestamp || 0) >= 30 * 60 * 1000) { localStorage.removeItem('pendingSupportData'); return; }
		} catch { localStorage.removeItem('pendingSupportData'); return; }
		try {
			const token = localStorage.getItem('token');
			if (!token) return;
			await updateSupportChatId(token, supportId, chatId);
			localStorage.removeItem('pendingSupportData');
			pendingSupportId = '';
		} catch {
			try {
				const sd = JSON.parse(pendingSupportData || '{}');
				const attempts = (sd.attempts || 0) + 1;
				if (attempts >= 3) localStorage.removeItem('pendingSupportData');
				else { sd.attempts = attempts; localStorage.setItem('pendingSupportData', JSON.stringify(sd)); }
			} catch { localStorage.removeItem('pendingSupportData'); }
		}
	}

	// Pagination
	let currentPage = 0;
	const cardsPerPage = 4;
	$: totalPages      = Math.ceil(userSupports.length / cardsPerPage);
	$: currentSupports = userSupports.slice(currentPage * cardsPerPage, (currentPage + 1) * cardsPerPage);
	let animationDirection = 'right';
	function nextPage()     { if (currentPage < totalPages - 1) { animationDirection = 'right'; currentPage++; } }
	function previousPage() { if (currentPage > 0)              { animationDirection = 'left';  currentPage--; } }

	// Popups
	let showJoinCoursePopup = false;
	let showSupportPopup    = false;
	function toggleSupportPopup() { showSupportPopup = !showSupportPopup; if (showSupportPopup) showJoinCoursePopup = false; }
	let courseCode     = '';
	let dontShowAgain  = false;

	function handleJoinCourse() {
		if (courseCode === '0000') { goto('/student/chat'); showJoinCoursePopup = false; }
		else if (courseCode.trim() !== '') showJoinCoursePopup = false;
	}
	function handleCreateSupport() { goto('/student/support/create'); showSupportPopup = false; }
	function handleCardClick(support: SupportResponse) { goto(`/student/support/${support.id}`); }
</script>

<!-- ══════════════════════════════════════════ TEMPLATE ══════════════════════════════════════════ -->
<div class="flex flex-col gap-6">
	<!-- Dashboard Header -->
	<div class="dashboard-header">
		<h1>{$i18n ? $i18n.t('Dashboard') : 'Dashboard'}</h1>
		<p class="subtitle">{$i18n ? $i18n.t('Overview of your learning journey') : 'Vue d\'ensemble de votre parcours'}</p>
	</div>

	<!-- Sprint 2: Engagement Tracking v1.1.0 -->
	<EngagementChart />

	<!-- ████████████████████████ PERFORMANCE DASHBOARD ████████████████████████ -->
	<section aria-label={$i18n.t('Student Performance Dashboard')}>
		<!-- Header + filter -->
		<div class="flex items-center justify-between mb-3">
			<div>
				<h2 class="text-base font-semibold text-gray-700 dark:text-gray-200">{$i18n.t('Your Performance')}</h2>
				<p class="text-xs text-gray-400 dark:text-gray-500">{dateRange}</p>
			</div>
			<div class="flex items-center gap-1 bg-gray-100 dark:bg-gray-700/60 rounded-full p-1" role="group" aria-label={$i18n.t('Time filter')}>
				{#each perfOptions as opt}
					<button
						class="px-3 py-1 text-xs font-semibold rounded-full transition-all duration-200
							{perfFilter === opt
								? 'bg-white dark:bg-gray-600 text-indigo-600 dark:text-indigo-300 shadow-sm'
								: 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}"
						on:click={() => { perfFilter = opt; }}
						aria-pressed={perfFilter === opt}
					>{$i18n.t(opt === 'monthly' ? 'Monthly' : 'Weekly')}</button>
				{/each}
			</div>
		</div>

		<!-- 3-column grid -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

			<!-- ▌1. STATISTICS PANEL ▐ -->
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 p-5 flex flex-col gap-4">
				<h3 class="text-base font-bold text-gray-800 dark:text-white">{$i18n.t('Statistics')}</h3>
				<div class="flex flex-col sm:flex-row items-center gap-5">
					<!-- Stat bars -->
					<div class="flex flex-col gap-3 flex-1 w-full">
						<!-- Participation -->
						<div class="flex items-center gap-3">
							<div class="w-9 h-9 rounded-full flex items-center justify-center bg-indigo-100 dark:bg-indigo-900/30 shrink-0">
								<svg class="w-5 h-5 text-indigo-500" fill="currentColor" viewBox="0 0 24 24">
									<path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
								</svg>
							</div>
							<div class="flex-1">
								<div class="flex justify-between mb-1">
									<span class="text-xs font-medium text-gray-600 dark:text-gray-300">{$i18n.t('Participation')}</span>
									<span class="text-xs font-bold text-indigo-500">{Math.round(animParticipation)}%</span>
								</div>
								<div class="h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
									<div class="h-full rounded-full bg-indigo-500" style="width:{animParticipation}%"></div>
								</div>
							</div>
						</div>
						<!-- Tasks & Exam -->
						<div class="flex items-center gap-3">
							<div class="w-9 h-9 rounded-full flex items-center justify-center bg-emerald-100 dark:bg-emerald-900/30 shrink-0">
								<svg class="w-5 h-5 text-emerald-500" fill="currentColor" viewBox="0 0 24 24">
									<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
								</svg>
							</div>
							<div class="flex-1">
								<div class="flex justify-between mb-1">
									<span class="text-xs font-medium text-gray-600 dark:text-gray-300">{$i18n.t('Tasks & Exam')}</span>
									<span class="text-xs font-bold text-emerald-500">{Math.round(animTasksExam)}%</span>
								</div>
								<div class="h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
									<div class="h-full rounded-full bg-emerald-500" style="width:{animTasksExam}%"></div>
								</div>
							</div>
						</div>
						<!-- Quiz -->
						<div class="flex items-center gap-3">
							<div class="w-9 h-9 rounded-full flex items-center justify-center bg-amber-100 dark:bg-amber-900/30 shrink-0">
								<svg class="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
									<path d="M11 7h2v2h-2zm0 4h2v6h-2zm1-9C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
								</svg>
							</div>
							<div class="flex-1">
								<div class="flex justify-between mb-1">
									<span class="text-xs font-medium text-gray-600 dark:text-gray-300">{$i18n.t('Quiz')}</span>
									<span class="text-xs font-bold text-amber-500">{Math.round(animQuiz)}%</span>
								</div>
								<div class="h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
									<div class="h-full rounded-full bg-amber-500" style="width:{animQuiz}%"></div>
								</div>
							</div>
						</div>
					</div>

					<!-- Circular grades ring -->
					<div class="flex flex-col items-center shrink-0">
						<div class="relative w-28 h-28">
							<svg class="w-full h-full -rotate-90" viewBox="0 0 128 128">
								<circle cx="64" cy="64" r={ringR} fill="none" stroke="#e5e7eb" class="dark:stroke-gray-700" stroke-width="10"/>
								<circle cx="64" cy="64" r={ringR} fill="none" stroke="#6366f1" stroke-width="10"
									stroke-linecap="round" stroke-dasharray={ringCirc} stroke-dashoffset={ringOffset}/>
							</svg>
							<div class="absolute inset-0 flex flex-col items-center justify-center">
								<span class="text-xl font-extrabold text-gray-800 dark:text-white">{Math.round(animGrades)}%</span>
								<span class="text-[9px] text-gray-400 dark:text-gray-500 text-center leading-tight px-1">{$i18n.t('Grades Completed')}</span>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- ▌2. PERFORMANCE GAUGE ▐ -->
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 p-5 flex flex-col gap-2">
				<h3 class="text-base font-bold text-gray-800 dark:text-white">{$i18n.t('Performance')}</h3>
				<div class="flex items-center gap-2 mb-1">
					<span class="w-3 h-3 rounded-sm bg-indigo-500 inline-block"></span>
					<span class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Point Progress')}</span>
				</div>
				<div class="flex flex-col items-center flex-1 justify-center">
					<svg viewBox="0 0 200 105" class="w-full max-w-[200px]" aria-label={$i18n.t('Performance gauge')}>
						<defs>
							<linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
								<stop offset="0%"   stop-color="#ef4444"/>
								<stop offset="50%"  stop-color="#f59e0b"/>
								<stop offset="100%" stop-color="#10b981"/>
							</linearGradient>
						</defs>
						<path d={zoneArc(180,120,gR)} fill="none" stroke="#ef4444" stroke-width="13" opacity="0.15"/>
						<path d={zoneArc(120, 60,gR)} fill="none" stroke="#f59e0b" stroke-width="13" opacity="0.15"/>
						<path d={zoneArc( 60,  0,gR)} fill="none" stroke="#10b981" stroke-width="13" opacity="0.15"/>
						<path d={gBgPath}   fill="none" stroke="#e5e7eb" class="dark:stroke-gray-700" stroke-width="13" stroke-linecap="round" opacity="0.5"/>
						<path d={gFillPath} fill="none" stroke="url(#gaugeGrad)" stroke-width="13" stroke-linecap="round"/>
						<line x1={gcx} y1={gcy} x2={gNeedleTip.x} y2={gNeedleTip.y}
							stroke="#374151" class="dark:stroke-gray-200" stroke-width="2.5" stroke-linecap="round"/>
						<circle cx={gcx} cy={gcy} r="5"   fill="#374151" class="dark:fill-gray-200"/>
						<circle cx={gcx} cy={gcy} r="2.5" fill="white"   class="dark:fill-gray-800"/>
						<text x="20"  y="103" font-size="7" fill="#ef4444" text-anchor="middle" font-family="sans-serif">Low</text>
						<text x="100" y="16"  font-size="7" fill="#f59e0b" text-anchor="middle" font-family="sans-serif">Mid</text>
						<text x="180" y="103" font-size="7" fill="#10b981" text-anchor="middle" font-family="sans-serif">High</text>
					</svg>
					<div class="text-center mt-2">
						<p class="text-xs text-gray-400 dark:text-gray-500">{$i18n.t('Your Point')}</p>
						<p class="text-2xl font-extrabold text-gray-800 dark:text-white tracking-tight">
							{Math.round(animPoints).toLocaleString()}
						</p>
					</div>
				</div>
			</div>

			<!-- ▌3. CALENDAR WIDGET ▐ -->
			<div class="sm:col-span-2 lg:col-span-1 rounded-2xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 p-5 flex flex-col gap-3">
				<div class="flex items-center justify-between">
					<button on:click={calPrev}
						class="w-7 h-7 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-500 dark:text-gray-400"
						aria-label={$i18n.t('Previous month')}>
						<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/>
						</svg>
					</button>
					<h3 class="text-sm font-bold text-gray-800 dark:text-white">{MONS[calMonth]} {calYear}</h3>
					<button on:click={calNext}
						class="w-7 h-7 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-500 dark:text-gray-400"
						aria-label={$i18n.t('Next month')}>
						<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
						</svg>
					</button>
				</div>
				<div class="grid grid-cols-7 text-center">
					{#each DOW as d, i}
						<span class="text-[10px] font-semibold uppercase {i === 0 || i === 6 ? 'text-red-400' : 'text-gray-400 dark:text-gray-500'}">{d}</span>
					{/each}
				</div>
				<div class="grid grid-cols-7 gap-y-1 text-center">
					{#each calCells as day}
						{#if day === null}
							<span></span>
						{:else}
							<button
								on:click={() => calSelected = day}
								class="relative mx-auto w-7 h-7 flex items-center justify-center rounded-full text-xs font-medium transition-all duration-150
									{isToday(day)
										? 'bg-indigo-500 text-white shadow-md hover:bg-indigo-600'
										: calSelected === day
										? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-300'
										: isSunSat(day)
										? 'text-red-500 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700'
										: 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}"
								aria-pressed={calSelected === day}
								aria-label="{day} {MONS[calMonth]} {calYear}"
							>
								{day}
								{#if eventDays.includes(day) && !isToday(day)}
									<span class="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-indigo-400"></span>
								{/if}
							</button>
						{/if}
					{/each}
				</div>
			</div>
		</div>
	</section>
	<!-- ████████████████████████ END PERFORMANCE DASHBOARD ████████████████████████ -->

	<!-- Support button -->
	<div class="flex justify-end">
		<button
			class="flex items-center gap-2 bg-indigo-500 dark:bg-indigo-600 text-white py-3 px-6 rounded-full hover:bg-indigo-600 dark:hover:bg-indigo-700 transition-colors"
			on:click={toggleSupportPopup}
		>
			<span class="text-xl font-bold">+</span>
			<span>{$i18n.t('Support')}</span>
		</button>
	</div>

	<!-- Support cards -->
	<div class="flex flex-col gap-6">
		{#if isLoading}
			<div class="flex justify-center items-center py-12">
				<div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
				<span class="ml-3 text-gray-600 dark:text-gray-300">{$i18n.t('Loading your supports...')}</span>
			</div>
		{:else if userSupports.length === 0}
			<div class="flex flex-col items-center justify-center py-6 text-center">
				<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-indigo-400 dark:text-indigo-300 mb-3">
					<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
				</svg>
				<h3 class="text-lg font-medium text-gray-800 dark:text-white mb-2">{$i18n.t('No supports found')}</h3>
				<p class="text-sm text-gray-600 dark:text-gray-400">{$i18n.t('Create a support to get personalized learning assistance')}</p>
			</div>
		{:else}
			<div class="relative">
				{#if currentPage > 0}
					<button
						class="absolute left-0 top-1/2 transform -translate-y-1/2 -translate-x-4 sm:-translate-x-6 p-2 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-all"
						on:click={previousPage} aria-label={$i18n.t('Previous supports')}>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/>
						</svg>
					</button>
				{/if}
				{#if currentPage < totalPages - 1}
					<button
						class="absolute right-0 top-1/2 transform -translate-y-1/2 translate-x-4 sm:translate-x-6 p-2 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-all"
						on:click={nextPage} aria-label={$i18n.t('Next supports')}>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
						</svg>
					</button>
				{/if}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 card-container">
					{#each currentSupports as support, index (support.id)}
						<div
							class="cursor-pointer card-item h-full"
							class:card-slide-enter-from-right={animationDirection === 'right'}
							class:card-slide-enter-from-left={animationDirection === 'left'}
							on:click={() => handleCardClick(support)}
							on:keypress={(e) => e.key === 'Enter' && handleCardClick(support)}
							tabindex="0" role="button"
							style="animation-delay: {index * 0.05}s"
						>
							<CourseCard title={support.title} subject={support.subject || 'mathematics'} progress={0} href="#"/>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>

<!-- ═══ SUPPORT POPUP ═══ -->
{#if showSupportPopup}
	<div class="fixed inset-0 backdrop-blur-sm bg-white/30 dark:bg-black/30 flex items-center justify-center z-50">
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 w-full max-w-md mx-auto relative">
			<button class="absolute top-3 right-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" on:click={toggleSupportPopup}>
				<span class="text-2xl font-light">×</span>
			</button>
			<div class="flex justify-center mb-8"><img src="/favicon.png" alt="OT Logo" class="w-26 h-26"/></div>
			<h2 class="text-center text-xl font-bold text-gray-900 dark:text-white">{$i18n.t('Create Personalized Tutorials for any Subject or Topic')}</h2>
			<div class="my-8"><hr class="border-gray-200 dark:border-gray-600"/></div>
			<h3 class="text-center text-lg font-medium mb-6 text-gray-900 dark:text-white">{$i18n.t('Create Tour Learning Path')}</h3>
			<div class="space-y-4 mb-10 px-4">
				{#each [$i18n.t('Choose your topic and difficulty level'), $i18n.t('Set your learning objectives'), $i18n.t('Enjoy AI-powered personalized learning')] as step, i}
					<div class="flex items-center gap-4">
						<div class="flex-shrink-0 bg-[#004AAD] text-white rounded-full w-7 h-7 flex items-center justify-center">
							<span class="font-bold">{i+1}</span>
						</div>
						<span class="text-gray-800 dark:text-gray-200">{step}</span>
					</div>
				{/each}
			</div>
			<div class="flex justify-center mb-8">
				<button class="bg-indigo-600 hover:bg-indigo-700 text-white py-3 px-12 rounded-full font-medium" on:click={handleCreateSupport}>{$i18n.t('Create My support')}</button>
			</div>
			<div class="flex items-center justify-center gap-2 mt-4">
				<input type="checkbox" id="dontShow" bind:checked={dontShowAgain}
					class="h-4 w-4 text-indigo-600 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded focus:ring-indigo-500"/>
				<label for="dontShow" class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t("Don't show me again")}</label>
			</div>
		</div>
	</div>
{/if}

<style>
	.card-container { position: relative; overflow: hidden; }
	.card-item { transform-origin: center center; backface-visibility: hidden; transition: transform 0.2s ease; display: flex; }
	.card-item > :global(*) { flex: 1; height: 100%; }
	.card-item:hover { transform: translateY(-3px); }
	.card-slide-enter-from-right { animation: slideInFromRight 0.5s cubic-bezier(0.25,0.1,0.25,1) forwards; }
	.card-slide-enter-from-left  { animation: slideInFromLeft  0.5s cubic-bezier(0.25,0.1,0.25,1) forwards; }

	@keyframes slideInFromRight { from { transform: translateX(30px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
	@keyframes slideInFromLeft  { from { transform: translateX(-30px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

		.dashboard-header {
		margin-bottom: 0.5rem;
	}

	.dashboard-header h1 {
		font-size: 1.875rem;
		font-weight: 700;
		color: #1a202c;
		margin: 0;
	}

	.subtitle {
		color: #718096;
		margin-top: 0.25rem;
		margin-bottom: 0;
	}
</style>