<!-- Dashboard.svelte -->
<script lang="ts">
	import { getContext, onMount, onDestroy } from 'svelte';
	import { derived } from 'svelte/store';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { chatId as storeChatId, isDemo, demoData } from '$lib/stores';
	import CourseCard from '../elements/CourseCard.svelte';
	import {
		getSupportRequests,
		type SupportResponse,
		updateSupportChatId
	} from '$lib/apis/supports';
	import { page } from '$app/stores';
	import { fade, scale, fly } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import { toast } from 'svelte-sonner';
	import { TUTOR_FRONT_URL } from '$lib/constants';

	const i18n = getContext<Writable<i18nType>>('i18n');
	const _ = derived(i18n, ($i18n) => (key: string, options?: any) => $i18n.t(key, options));

	// ── TYPES ──────────────────────────────────────────────
	interface EnrolledCourse {
		id: string;
		title: string;
		language: string;
		category: string | null;
		level: string;
		teacher_name: string;
		teacher_profile_image_url?: string;
		enrolled_at: string;
		status: string;
	}

	// ── STATE supports ──────────────────────────────────────
	let userSupports: SupportResponse[] = [];
	let isLoadingSupports = true;

	// ── STATE courses ───────────────────────────────────────
	let userCourses: EnrolledCourse[] = [];
	let isLoadingCourses = true;

	// ── STATE quizzes ───────────────────────────────────────
	let userQuizzes: any[] = [];
	let isLoadingQuizzes = true;

	$: isLoading = isLoadingSupports || isLoadingCourses || isLoadingQuizzes;

	$: displaySupports = $isDemo
		? $demoData.supports.map((s) => ({
				id: s.id,
				title: s.title,
				description: s.description,
				status: s.progress < 30 ? 'not-started' : s.progress < 100 ? 'in-progress' : 'completed',
				category: s.category,
				difficulty: s.difficulty,
				progress: s.progress
			}))
		: userSupports;

	// Track pending support and chat linkage
	let pendingSupportId = '';
	let chatIdSubscription: Function;
	let urlCheckInterval: ReturnType<typeof setInterval>;
	let currentPath = '';
	let chatIdFromURL = '';

	// ── HELPERS courses ─────────────────────────────────────
	function levelColor(level: string): string {
		const map: Record<string, string> = {
			'primary-school': '#22c55e',
			'middle-school': '#0ea5e9',
			'high-school': '#f59e0b',
			university: '#ef4444'
		};
		return map[level] ?? '#94a3b8';
	}
	function normalizeAvatarPath(url?: string | null) {
		if (!url || url.trim() === '') return null;
		const clean = url.split('?')[0].trim();
		if (
			clean.startsWith('http://') ||
			clean.startsWith('https://') ||
			clean.startsWith('/static/') ||
			clean.startsWith('/uploads/') ||
			clean.startsWith('/api/')
		) {
			return clean;
		}
		if (clean.startsWith('/')) return clean;
		return `/uploads/avatars/${clean}`;
	}

	function levelLabel(level: string): string {
		const map: Record<string, string> = {
			'primary-school': $_('Primary school'),
			'middle-school': $_('Middle school'),
			'high-school': $_('High school'),
			university: $_('University')
		};
		return map[level] ?? level;
	}

	function langFlag(lang: string): string {
		const map: Record<string, string> = {
			'fr-FR': '🇫🇷',
			'en-US': '🇺🇸',
			'ar-MA': '🇲🇦'
		};
		return map[lang] ?? '🌐';
	}

	// ── FETCH COURSES ───────────────────────────────────────
	async function fetchCourses() {
		isLoadingCourses = true;
		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch('/api/v1/student/courses/', {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (!res.ok) throw new Error(`Error ${res.status}`);
			userCourses = await res.json();
		} catch (e) {
			console.error('Error fetching courses:', e);
			userCourses = [];
		} finally {
			isLoadingCourses = false;
		}
	}

	// ── FETCH QUIZZES ───────────────────────────────────────
	async function fetchQuizzes() {
		isLoadingQuizzes = true;
		try {
			const token = localStorage.getItem('token') ?? '';
			const userStr = localStorage.getItem('user');
			const user = userStr ? JSON.parse(userStr) : {};
			const role: string = user.role || 'student';

			let endpoint: string;
			if (role === 'teacher') {
				endpoint = '/api/v1/quizzes/teacher';
			} else {
				let joinedCodes: string[] = [];
				try {
					joinedCodes = JSON.parse(localStorage.getItem('joined_quiz_codes') || '[]');
				} catch (e) {}
				const codesParam = joinedCodes.join(',');
				endpoint = `/api/v1/student/assignments${codesParam ? `?codes=${codesParam}` : ''}`;
			}

			console.log('🔗 [QUIZZES] Fetching from:', endpoint);
			console.log('👤 [QUIZZES] Role:', role);
			console.log('🔑 [QUIZZES] Token exists:', !!token);
			console.log('📋 [QUIZZES] Joined codes:', localStorage.getItem('joined_quiz_codes'));

			const res = await fetch(endpoint, {
				headers: { Authorization: `Bearer ${token}` }
			});

			console.log('📡 [QUIZZES] Response status:', res.status);

			if (res.ok) {
				const data = await res.json();
				console.log('📦 [QUIZZES] Raw data received:', data);
				console.log('📊 [QUIZZES] Number of quizzes:', data.length);

				if (role === 'teacher') {
					userQuizzes = data;
				} else {
					userQuizzes = data.map((a: any) => ({
						...a,
						quiz_id: a.quiz_id || a.id,
						_displayStatus:
							a.score !== undefined && a.score !== null ? 'completed' : a.status || 'pending'
					}));

					console.log(`✅ [QUIZZES] Final count: ${userQuizzes.length}`);
					console.log('✅ [QUIZZES] Final data:', userQuizzes);
				}
			} else {
				const errText = await res.text();
				console.error('❌ [QUIZZES] API error:', res.status, errText);
				userQuizzes = [];
			}
		} catch (e: any) {
			console.error('💥 [QUIZZES] Network error:', e);
			userQuizzes = [];
		} finally {
			isLoadingQuizzes = false;
		}
	}

	// ── PAGINATION courses ──────────────────────────────────
	let currentCoursePage = 0;
	const coursesPerPage = 4;
	$: totalCoursePages = Math.ceil(userCourses.length / coursesPerPage);
	$: currentCourses = userCourses.slice(
		currentCoursePage * coursesPerPage,
		(currentCoursePage + 1) * coursesPerPage
	);
	let courseAnimDir = 'right';

	function nextCoursePage() {
		if (currentCoursePage < totalCoursePages - 1) {
			courseAnimDir = 'right';
			currentCoursePage += 1;
		}
	}
	function prevCoursePage() {
		if (currentCoursePage > 0) {
			courseAnimDir = 'left';
			currentCoursePage -= 1;
		}
	}

	// ── JOIN QUIZ MODAL ─────────────────────────────────────
	let showJoinQuizModal = false;
	let joinQuizCode = '';
	let isJoiningQuiz = false;
	let joinQuizError = '';

	function openJoinQuizModal() {
		joinQuizCode = '';
		joinQuizError = '';
		showJoinQuizModal = true;
	}

	function closeJoinQuizModal() {
		if (isJoiningQuiz) return;
		showJoinQuizModal = false;
		joinQuizCode = '';
		joinQuizError = '';
	}

	async function handleJoinQuiz() {
		const code = joinQuizCode.trim().toUpperCase();
		if (!code) {
			joinQuizError = $_('Please enter a code');
			return;
		}
		if (code.length !== 6) {
			joinQuizError = $_('The code must be exactly 6 characters.');
			return;
		}
		isJoiningQuiz = true;
		joinQuizError = '';
		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`/api/v1/quizzes/join/${code}`, {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? $_('Invalid or expired quiz code'));
			}

			try {
				const existingCodes = JSON.parse(localStorage.getItem('joined_quiz_codes') || '[]');
				if (!existingCodes.includes(code)) {
					existingCodes.push(code);
					localStorage.setItem('joined_quiz_codes', JSON.stringify(existingCodes));
					console.log(`🔐 Quiz code ${code} saved to localStorage`);
				}
			} catch (e) {
				console.warn('Failed to save quiz code to localStorage:', e);
			}

			showJoinQuizModal = false;
			goto(`/student/assignments?code=${code}`);
		} catch (e: any) {
			joinQuizError = e?.message ?? $_('Code validation error');
		} finally {
			isJoiningQuiz = false;
		}
	}

	// ── JOIN MODAL ──────────────────────────────────────────
	let showJoinModal = false;
	let joinCourseCode = '';
	let isJoining = false;
	let joinError = '';
	let joinSuccess = false;
	let newlyJoinedId = '';

	function openJoinModal() {
		joinCourseCode = '';
		joinError = '';
		joinSuccess = false;
		showJoinModal = true;
	}

	function closeJoinModal() {
		if (isJoining) return;
		showJoinModal = false;
		joinCourseCode = '';
		joinError = '';
	}

	async function joinCourse() {
		const code = joinCourseCode.trim();
		if (!code) {
			joinError = $_('Please enter a code');
			return;
		}
		isJoining = true;
		joinError = '';

		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch('/api/v1/student/courses/enroll', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`
				},
				body: JSON.stringify({ course_id: code })
			});

			if (res.status === 409) {
				joinError = $_('Already enrolled in this course');
				return;
			}
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? $_('Invalid code or course not found'));
			}

			const enrolled: EnrolledCourse = await res.json();
			userCourses = [{ ...enrolled }, ...userCourses];
			newlyJoinedId = enrolled.id;
			joinSuccess = true;

			setTimeout(() => {
				showJoinModal = false;
				joinCourseCode = '';
				joinSuccess = false;
				setTimeout(() => {
					newlyJoinedId = '';
				}, 4000);
			}, 1500);
		} catch (e: any) {
			joinError = e?.message ?? $_('Enrollment error');
		} finally {
			isJoining = false;
		}
	}

	// ── DELETE / LEAVE COURSE (DASHBOARD) ──────────────────
	let showDeleteModal = false;
	let courseToDelete: string | null = null;
	let isDeleting = false;
	let deleteError = '';

	function openDeleteModal(courseId: string) {
		courseToDelete = courseId;
		deleteError = '';
		showDeleteModal = true;
	}

	function closeDeleteModal() {
		if (isDeleting) return;
		showDeleteModal = false;
		courseToDelete = null;
		deleteError = '';
	}

	async function unenrollCourse() {
		if (!courseToDelete) return;
		isDeleting = true;
		deleteError = '';

		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`/api/v1/student/courses/${courseToDelete}`, {
				method: 'DELETE',
				headers: { Authorization: `Bearer ${token}` }
			});

			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail ?? $_('Error while deleting course'));
			}

			userCourses = userCourses.filter((c) => c.id !== courseToDelete);

			if (currentCourses.length === 0 && currentCoursePage > 0) {
				currentCoursePage -= 1;
			}

			closeDeleteModal();
			toast.success($_('Course left successfully'));
		} catch (e: any) {
			deleteError = e?.message ?? $_('Deletion error');
		} finally {
			isDeleting = false;
		}
	}

	// ── MOUNT ───────────────────────────────────────────────
	onMount(async () => {
		if (browser) {
			storeChatId.set('');

			if (sessionStorage.selectedModels) {
				sessionStorage.removeItem('selectedModels');
			}
			if (localStorage.getItem('pendingSupportData')) {
				localStorage.removeItem('pendingSupportData');
			}

			const keysToRemove: string[] = [];
			for (let i = 0; i < localStorage.length; i++) {
				const key = localStorage.key(i);
				if (key && key.startsWith('chat-input-')) keysToRemove.push(key);
			}
			keysToRemove.forEach((key) => localStorage.removeItem(key));

			if ($isDemo) {
				isLoadingSupports = false;
				isLoadingCourses = false;
				isLoadingQuizzes = false;
			} else {
				const token = localStorage.getItem('token');
				if (token) {
					try {
						const supports = await getSupportRequests(token);
						if (supports && Array.isArray(supports)) {
							userSupports = supports;
						}
					} catch (error) {
						console.error('Error fetching supports:', error);
						userSupports = [];
					} finally {
						isLoadingSupports = false;
					}

					await fetchCourses();
					await fetchQuizzes();
				} else {
					isLoadingSupports = false;
					isLoadingCourses = false;
					isLoadingQuizzes = false;
				}
			}

			if (!window.openTutorEvents) {
				window.openTutorEvents = new EventTarget();
			}

			window.openTutorEvents.addEventListener('chatCreated', ((event: CustomEvent) => {
				const newChatId = event.detail?.chatId;
				if (newChatId && pendingSupportId) {
					updateSupportWithChatId(pendingSupportId, newChatId);
				}
			}) as EventListener);

			const handleAvatarUpdate = () => {
				fetchCourses();
			};
			window.addEventListener('avatar-updated', handleAvatarUpdate as EventListener);

			chatIdSubscription = storeChatId.subscribe((newChatId) => {
				if (newChatId && newChatId !== 'local' && pendingSupportId) {
					updateSupportWithChatId(pendingSupportId, newChatId);
				}
			});

			urlCheckInterval = setInterval(() => {
				try {
					const pendingSupportData = localStorage.getItem('pendingSupportData');
					if (!pendingSupportData) {
						clearInterval(urlCheckInterval);
						return;
					}
					const supportData = JSON.parse(pendingSupportData);
					const currentTime = Date.now();
					const MAX_SUPPORT_AGE_MS = 30 * 60 * 1000;
					if (currentTime - (supportData.timestamp || 0) >= MAX_SUPPORT_AGE_MS) {
						localStorage.removeItem('pendingSupportData');
						clearInterval(urlCheckInterval);
						return;
					}
					const currentURL = window.location.pathname;
					if (currentURL.startsWith('/student/c/')) {
						const newChatId = currentURL.split('/student/c/')[1].split('/')[0];
						if (newChatId && supportData.id) {
							updateSupportWithChatId(supportData.id, newChatId);
						}
					}
				} catch (error) {
					localStorage.removeItem('pendingSupportData');
					clearInterval(urlCheckInterval);
				}
			}, 1000);
		}
	});

	onDestroy(() => {
		if (browser) {
			if (chatIdSubscription) chatIdSubscription();
			if (urlCheckInterval) clearInterval(urlCheckInterval);
			window.removeEventListener('avatar-updated', (() => fetchCourses()) as EventListener);
		}
	});

	$: if ($page && $page.url && browser) {
		currentPath = $page.url.pathname || '';
		if (currentPath.startsWith('/student/c/')) {
			chatIdFromURL = currentPath.replace('/student/c/', '').split('/')[0];
			if (chatIdFromURL && localStorage.getItem('pendingSupportData')) {
				try {
					const supportData = JSON.parse(localStorage.getItem('pendingSupportData') || '{}');
					const supportId = supportData.id;
					const currentTime = Date.now();
					const MAX_SUPPORT_AGE_MS = 30 * 60 * 1000;
					if (supportId && currentTime - (supportData.timestamp || 0) < MAX_SUPPORT_AGE_MS) {
						updateSupportWithChatId(supportId, chatIdFromURL);
					} else {
						localStorage.removeItem('pendingSupportData');
					}
				} catch (error) {
					localStorage.removeItem('pendingSupportData');
				}
			}
		}
	}

	async function updateSupportWithChatId(supportId: string, chatId: string) {
		if (!supportId || !chatId || !browser || chatId === 'local' || chatId === 'undefined') return;
		let pendingSupportData: string | null;
		try {
			pendingSupportData = localStorage.getItem('pendingSupportData');
			if (!pendingSupportData) return;
			const supportData = JSON.parse(pendingSupportData);
			if (supportData.id !== supportId) return;
			const currentTime = Date.now();
			const MAX_SUPPORT_AGE_MS = 30 * 60 * 1000;
			if (currentTime - (supportData.timestamp || 0) >= MAX_SUPPORT_AGE_MS) {
				localStorage.removeItem('pendingSupportData');
				return;
			}
		} catch (error) {
			localStorage.removeItem('pendingSupportData');
			return;
		}
		try {
			const token = localStorage.getItem('token');
			if (!token) return;
			await updateSupportChatId(token, supportId, chatId);
			localStorage.removeItem('pendingSupportData');
			pendingSupportId = '';
		} catch (error) {
			console.error('Failed to update support with chat ID:', error);
			try {
				const supportData = JSON.parse(pendingSupportData || '{}');
				const attemptCount = (supportData.attempts || 0) + 1;
				if (attemptCount >= 3) {
					localStorage.removeItem('pendingSupportData');
				} else {
					supportData.attempts = attemptCount;
					localStorage.setItem('pendingSupportData', JSON.stringify(supportData));
				}
			} catch {
				localStorage.removeItem('pendingSupportData');
			}
		}
	}

	// ── PAGINATION supports ─────────────────────────────────
	let currentPage = 0;
	const cardsPerPage = 4;
	$: totalPages = Math.ceil(displaySupports.length / cardsPerPage);
	$: currentSupports = displaySupports.slice(
		currentPage * cardsPerPage,
		(currentPage + 1) * cardsPerPage
	);
	let animationDirection = 'right';

	function nextPage() {
		if (currentPage < totalPages - 1) {
			animationDirection = 'right';
			currentPage += 1;
		}
	}
	function previousPage() {
		if (currentPage > 0) {
			animationDirection = 'left';
			currentPage -= 1;
		}
	}

	// ── SUPPORT POPUP ───────────────────────────────────────
	let showSupportPopup = false;
	let dontShowAgain = false;

	if (browser) {
		dontShowAgain = localStorage.getItem('hideSupportPopup') === 'true';
	}

	function toggleSupportPopup() {
		if (dontShowAgain || (browser && localStorage.getItem('hideSupportPopup') === 'true')) {
			goto('/student/support/create');
			return;
		}
		showSupportPopup = !showSupportPopup;
	}

	$: if (browser) {
		if (dontShowAgain) {
			localStorage.setItem('hideSupportPopup', 'true');
		} else {
			localStorage.removeItem('hideSupportPopup');
		}
	}

	function handleCreateSupport() {
		goto('/student/support/create');
		showSupportPopup = false;
	}

	function handleCardClick(support: SupportResponse) {
		goto(`/student/support/${support.id}`);
	}
</script>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- TEMPLATE                                               -->
<!-- ═══════════════════════════════════════════════════════ -->
<div class="flex flex-col gap-8">
	<div class="flex justify-end mb-4">
		<div class="flex gap-3">
			<!-- Enter Quiz Code (style harmonisé avec les autres boutons) -->
			<button
				class="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full transition"
				on:click={() => goto('/student/assignments?openCode=1')}
			>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2.5"
						d="M12 4v16m8-8H4"
					/>
				</svg>
				{$_('Enter Quiz Code')}
			</button>

			<!-- Join a course (style harmonisé avec page My Classrooms) -->
			<button
				class="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full transition"
				on:click={openJoinModal}
			>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2.5"
						d="M12 4v16m8-8H4"
					/>
				</svg>
				{$i18n.t('Join a course')}
			</button>

			<!-- Support (redirects directly to /student/support/create) -->
			<button
				class="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full transition"
				on:click={() => goto('/student/support/create')}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
						clip-rule="evenodd"
					/>
				</svg>
				{$_('Support')}
			</button>
		</div>
	</div>

	<div class="flex flex-col gap-4">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<div class="section-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
						/>
					</svg>
				</div>
				<div>
					<h2 class="section-title">
						{$_('My')} <span class="title-accent">{$_('Courses')}</span>
					</h2>
					<p class="section-sub">{$_('Your joined courses')}</p>
				</div>
			</div>
		</div>

		<div>
			{#if isLoadingCourses}
				<div class="flex justify-center items-center py-8">
					<div
						class="animate-spin w-7 h-7 border-4 border-blue-500 border-t-transparent rounded-full"
					></div>
					<span class="ml-3 text-gray-500 dark:text-gray-400 text-sm"
						>{$_('Loading courses...')}</span
					>
				</div>
			{:else if userCourses.length === 0}
				<div class="empty-section border-0 p-0 bg-transparent dark:bg-transparent">
					<svg
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						width="32"
						height="32"
						class="text-indigo-300"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="1.5"
							d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
						/>
					</svg>
					<p class="text-sm font-medium text-gray-600 dark:text-gray-400">
						{$_('No courses yet')}
					</p>
					<p class="text-xs text-gray-400 dark:text-gray-500">
						{$_('Join a course with a code')}
					</p>
					<button class="btn-join-inline" on:click={openJoinModal}>
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2.5"
								d="M12 4v16m8-8H4"
							/>
						</svg>
						{$_('Join a course')}
					</button>
				</div>
			{:else}
				<div class="relative">
					{#if currentCoursePage > 0}
						<button
							class="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 sm:-translate-x-6 p-2 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-all"
							on:click={prevCoursePage}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
					{/if}
					{#if currentCoursePage < totalCoursePages - 1}
						<button
							class="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 sm:translate-x-6 p-2 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-all"
							on:click={nextCoursePage}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
					{/if}

					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
						{#each currentCourses as course (course.id)}
							<div
								class="course-card-dash"
								class:card-slide-enter-from-right={courseAnimDir === 'right'}
								class:card-slide-enter-from-left={courseAnimDir === 'left'}
								class:new-highlight-dash={course.id === newlyJoinedId}
								in:fly={{ y: 10, duration: 220, easing: cubicOut }}
							>
								{#if course.id === newlyJoinedId}
									<div class="new-badge-dash" in:fly={{ x: 12, duration: 280 }}>
										✨ {$_('New')}
									</div>
								{/if}

								<div class="cc-top-dash">
									<div class="cc-top-left-dash">
										<div
											class="cc-level-tag-dash"
											style="color:{levelColor(course.level)};background:{levelColor(
												course.level
											)}18;border-color:{levelColor(course.level)}33;"
										>
											<span class="level-dot-dash" style="background:{levelColor(course.level)};"
											></span>
											{levelLabel(course.level)}
										</div>
										<span class="cc-lang-dash">{langFlag(course.language)}</span>
									</div>

									<button
										class="btn-delete-dash"
										on:click|stopPropagation={() => openDeleteModal(course.id)}
										title={$_('Leave course')}
										aria-label={$_('Leave course')}
									>
										<svg
											viewBox="0 0 24 24"
											fill="none"
											stroke="currentColor"
											width="14"
											height="14"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
											/>
										</svg>
									</button>
								</div>

								<h3
									class="cc-title-dash cursor-pointer"
									on:click={() => goto(`/student/classrooms/${course.id}`)}
									on:keypress={(e) => e.key === 'Enter' && goto(`/student/classrooms/${course.id}`)}
									tabindex="0"
									role="button"
								>
									{course.title}
								</h3>

								{#if course.category}
									<span class="cc-cat-dash">{course.category}</span>
								{/if}

								<div class="cc-teacher-dash">
									<div class="teacher-avatar-dash">
										{#if course.teacher_profile_image_url && normalizeAvatarPath(course.teacher_profile_image_url)}
											<img
												src={normalizeAvatarPath(course.teacher_profile_image_url)}
												alt={course.teacher_name}
												class="teacher-avatar-img"
											/>
										{:else}
											{course.teacher_name?.charAt(0)?.toUpperCase() ?? 'P'}
										{/if}
									</div>
									<span class="teacher-name-dash">{course.teacher_name ?? $_('Professor')}</span>
								</div>

								<button
									class="btn-start-dash"
									on:click={() => goto(`/student/classrooms/${course.id}`)}
								>
									<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2.5"
											d="M5 3l14 9-14 9V3z"
										/>
									</svg>
									{$_('Launch')}
								</button>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>

	<div class="flex flex-col gap-4">
		<div class="flex items-center gap-3">
			<div class="section-icon">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
					/>
				</svg>
			</div>
			<div>
				<h2 class="section-title">
					{$_('My')} <span class="title-accent">{$_('Supports')}</span>
				</h2>
				<p class="section-sub">{$_('Your personalized learning sessions')}</p>
			</div>
		</div>

		<div>
			{#if isLoadingSupports}
				<div class="flex justify-center items-center py-8">
					<div
						class="animate-spin w-7 h-7 border-4 border-indigo-500 border-t-transparent rounded-full"
					></div>
					<span class="ml-3 text-gray-500 dark:text-gray-400 text-sm"
						>{$_('Loading your supports...')}</span
					>
				</div>
			{:else if displaySupports.length === 0}
				<div
					class="empty-section border-0 p-0 bg-transparent dark:bg-transparent flex flex-col items-center justify-center text-center gap-3"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="32"
						height="32"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
						class="text-indigo-300"
					>
						<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
					</svg>

					<p class="text-sm font-medium text-gray-600 dark:text-gray-400 m-0">
						{$_('No supports found')}
					</p>

					<p class="text-xs text-gray-400 dark:text-gray-500 m-0">
						{$_('Create a support to get personalized learning assistance')}
					</p>

					<button
						class="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-semibold bg-blue-600 text-white hover:bg-blue-700 rounded-full transition shadow-sm mt-2"
						on:click={toggleSupportPopup}
					>
						+ Create a support
					</button>
				</div>
			{:else}
				<div class="relative">
					{#if currentPage > 0}
						<button
							class="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 sm:-translate-x-6 p-2 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-all"
							on:click={previousPage}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
					{/if}
					{#if currentPage < totalPages - 1}
						<button
							class="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 sm:translate-x-6 p-2 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-all"
							on:click={nextPage}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
									clip-rule="evenodd"
								/>
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
								tabindex="0"
								role="button"
								style="animation-delay: {index * 0.05}s"
							>
								<CourseCard
									title={support.title}
									subject={support.subject || 'mathematics'}
									progress={0}
									href="#"
								/>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>

	<div class="flex flex-col gap-4">
		<div class="flex items-center gap-3">
			<div class="section-icon text-purple-600 dark:text-purple-400">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
					/>
				</svg>
			</div>
			<div>
				<h2 class="section-title">
					{$_('MY QUIZZES')}
				</h2>
				<p class="section-sub">{$_('Your completed quizzes and scores')}</p>
			</div>
		</div>

		<div>
			{#if isLoadingQuizzes}
				<div class="flex justify-center items-center py-8">
					<div
						class="animate-spin w-7 h-7 border-4 border-purple-500 border-t-transparent rounded-full"
					></div>
					<span class="ml-3 text-gray-500 dark:text-gray-400 text-sm"
						>{$_('Loading quizzes...')}</span
					>
				</div>
			{:else if userQuizzes.length === 0}
				<div class="empty-section">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="32"
						height="32"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
						class="text-purple-300"
					>
						<path
							d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
						/>
					</svg>
					<p class="text-sm font-medium text-gray-600 dark:text-gray-400">
						{$_('No quizzes submitted yet')}
					</p>
					<p class="text-xs text-gray-400 dark:text-gray-500">
						{$_('Join an assessment with a code provided by your teacher')}
					</p>
					<button class="btn-join-inline" on:click={openJoinQuizModal}>
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="14" height="14">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2.5"
								d="M12 4v16m8-8H4"
							/>
						</svg>
						{$_('Join a Quiz')}
					</button>
				</div>
			{:else}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each userQuizzes as quiz (quiz.quiz_id ?? quiz.id)}
						<!-- ═══ TEACHER VIEW (only if teacher created it) ═══ -->
						{#if quiz.teacher_id !== undefined || quiz.participants_count !== undefined}
							<div
								class="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-2xl p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between h-full"
							>
								<div>
									<div class="flex items-center justify-between gap-2 mb-3">
										<span
											class="text-[10px] font-semibold tracking-wider text-gray-400 dark:text-gray-500 uppercase"
										>
											{new Date(quiz.created_at).toLocaleDateString(undefined, {
												day: 'numeric',
												month: 'short',
												year: 'numeric'
											})}
										</span>
										<span
											class="px-2.5 py-0.5 text-xs font-semibold rounded-full {quiz.status ===
											'published'
												? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400'
												: 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400'}"
										>
											{quiz.status === 'published' ? $_('Published') : $_('Draft')}
										</span>
									</div>

									{#if quiz.status === 'published' && quiz.quiz_code}
										<div
											class="mb-3 flex items-center gap-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/30 px-3 py-2"
										>
											<span
												class="text-[10px] font-semibold uppercase tracking-wider text-indigo-500 dark:text-indigo-400"
												>{$_('Code')}</span
											>
											<code
												class="rounded bg-white dark:bg-slate-900 px-2 py-0.5 font-mono text-sm font-black tracking-widest text-indigo-700 dark:text-indigo-300"
											>
												{quiz.quiz_code}
											</code>
										</div>
									{/if}

									<h3
										class="text-base font-bold text-gray-800 dark:text-gray-100 mb-2 line-clamp-2"
									>
										{quiz.title}
									</h3>
									<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
										{quiz.total_questions}
										{quiz.total_questions > 1 ? $_('questions') : $_('question')}
									</p>
								</div>
								<div
									class="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-700"
								>
									<div>
										<span
											class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500"
											>{$_('Participants')}</span
										>
										<span
											class="ml-2 text-lg font-extrabold text-fuchsia-600 dark:text-fuchsia-400"
										>
											{quiz.participants_count ?? 0}
										</span>
									</div>
									<button
										class="rounded-lg bg-gradient-to-br from-indigo-600 to-blue-600 px-3 py-1.5 text-xs font-bold text-white shadow-md transition hover:from-indigo-700 hover:to-blue-700"
										on:click={() => goto(`/teacher/quizzes/${quiz.id}`)}
									>
										{quiz.status === 'published' ? $_('Analytics') : $_('Publish')}
									</button>
								</div>
							</div>
						{:else}
							<!-- ═══ STUDENT VIEW (Matches Assignments page design) ═══ -->
							{@const isCompleted =
								quiz._displayStatus === 'completed' ||
								(quiz.score !== undefined && quiz.score !== null)}
							{@const isOverdue = quiz._displayStatus === 'overdue' || quiz.status === 'overdue'}
							{@const isPending = !isCompleted && !isOverdue}

							<div
								class="bg-white dark:bg-gray-800 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.06)] overflow-hidden flex flex-col min-h-[260px] pb-3 relative border border-gray-100 dark:border-gray-700 transition-transform hover:-translate-y-1 duration-300"
							>
								<!-- Top colored bar (smaller) -->
								<div
									class="h-2 w-full {isCompleted
										? 'bg-green-500'
										: isOverdue
											? 'bg-red-500'
											: 'bg-gray-400'}"
								></div>

								<div class="p-4 flex flex-col flex-1">
									<!-- Subject & Points -->
									<div class="flex justify-between items-center mb-3">
										<span
											class="bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 text-[10px] font-medium px-2 py-0.5 rounded-md line-clamp-1"
										>
											{quiz.course || 'Quiz'}
										</span>
										<span
											class="text-gray-400 dark:text-gray-500 text-[10px] font-medium whitespace-nowrap ml-2"
										>
											{(quiz.total_questions ?? 0) * 10}
											{$_('points')}
										</span>
									</div>

									<!-- Title -->
									<h3
										class="text-slate-700 dark:text-gray-100 font-semibold text-[13px] mb-2 line-clamp-1"
									>
										{quiz.title}
									</h3>

									{#if isCompleted}
										<!-- Completed state statistics (compact) -->
										<div
											class="bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800 rounded-lg p-3 mt-1 space-y-1.5 flex-1"
										>
											<div
												class="grid grid-cols-2 gap-2 text-[10px] text-slate-600 dark:text-slate-300"
											>
												<div class="flex flex-col">
													<span
														class="text-[8px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black"
														>Score</span
													>
													<span
														class="font-extrabold text-[11px] text-emerald-600 dark:text-emerald-400 mt-0.5"
													>
														{quiz.score}/{quiz.total ?? quiz.total_questions}
													</span>
												</div>
												<div class="flex flex-col">
													<span
														class="text-[8px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black"
														>Time</span
													>
													<span
														class="font-semibold text-[11px] text-slate-700 dark:text-slate-200 mt-0.5"
													>
														{quiz.time_spent || '1'} min
													</span>
												</div>
												<div
													class="flex flex-col col-span-2 border-t border-slate-100 dark:border-slate-800 pt-1.5"
												>
													<span
														class="text-[8px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black"
														>Date</span
													>
													<span
														class="font-semibold text-[10px] text-slate-700 dark:text-slate-200 mt-0.5 truncate"
													>
														{quiz.submitted_at
															? new Date(quiz.submitted_at).toLocaleDateString('en-US', {
																	day: 'numeric',
																	month: 'short',
																	year: 'numeric'
																})
															: '—'}
													</span>
												</div>
												<div class="flex flex-col col-span-2">
													<span
														class="text-[8px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-black"
														>Due</span
													>
													<span
														class="font-semibold text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 truncate"
													>
														{quiz.due || quiz.limit_date || 'None'}
													</span>
												</div>
											</div>
										</div>
									{:else}
										<!-- Pending state -->
										<p
											class="text-gray-500 dark:text-gray-400 text-[11px] leading-relaxed line-clamp-3 mb-3 flex-1"
										>
											{quiz.description || `Assessment quiz - ${quiz.total_questions} questions.`}
										</p>

										<div class="w-full h-px bg-gray-100 dark:bg-gray-700 mt-auto mb-3"></div>

										<div class="flex justify-between items-center mb-2">
											<span class="text-gray-400 dark:text-gray-500 text-[10px]">
												{#if isOverdue}
													Due: {quiz.due || quiz.limit_date} (Late)
												{:else}
													Due: {quiz.due || quiz.limit_date || 'None'}
												{/if}
											</span>
										</div>

										<button
											on:click={() => goto(`/student/assignments?take=${quiz.quiz_code}`)}
											class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg py-2 text-[11px] text-center transition-colors"
										>
											{$_('Start Quiz')}
										</button>
									{/if}
								</div>
							</div>
						{/if}
					{/each}
				</div>
			{/if}
		</div>
	</div>
</div>
{#if showJoinModal}
	<div
		class="modal-overlay"
		role="button"
		tabindex="0"
		on:click={closeJoinModal}
		on:keydown={(e) => e.key === 'Escape' && closeJoinModal()}
		in:fade={{ duration: 200 }}
		out:fade={{ duration: 150 }}
	>
		<div
			class="modal-card"
			role="dialog"
			aria-modal="true"
			aria-label={$_('Join a course')}
			on:click|stopPropagation
			on:keydown|stopPropagation
			in:fly={{ y: 20, duration: 300, easing: cubicOut }}
		>
			<!-- Close button -->
			<button class="modal-close" on:click={closeJoinModal} aria-label={$_('Close')}>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					/>
				</svg>
			</button>

			{#if !joinSuccess}
				<!-- ── DEFAULT STATE ── -->
				<div class="modal-body">
					<div class="modal-logo-wrap">
						<img src="{TUTOR_FRONT_URL}/static/favicon.png" alt="OT AI" class="modal-logo-img" />
					</div>

					<h2 class="modal-title">{$_('Join a course')}</h2>
					<p class="modal-subtitle">
						{$_('Enter the code provided by your teacher')}
					</p>

					<!-- Code input -->
					<div class="input-group">
						<label for="courseCodeInputDash" class="input-label">
							{$_('Course code')}
						</label>
						<input
							id="courseCodeInputDash"
							type="text"
							bind:value={joinCourseCode}
							placeholder={$_('ex: a1b2c3d4-...')}
							class="code-input {joinError ? 'input-error' : ''}"
							disabled={isJoining}
							on:keydown={(e) => e.key === 'Enter' && joinCourse()}
							autocomplete="off"
							spellcheck="false"
						/>
						{#if joinError}
							<p class="input-err-msg" in:fly={{ y: -4, duration: 150 }}>
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="13" height="13">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
									/>
								</svg>
								{joinError}
							</p>
						{/if}
					</div>

					<p class="modal-hint">
						{$_('No code? Ask your teacher or your institution')}
					</p>

					<!-- Join button -->
					<button
						class="btn-join-confirm"
						on:click={joinCourse}
						disabled={isJoining || !joinCourseCode.trim()}
					>
						{#if isJoining}
							<svg class="spin-icon" viewBox="0 0 50 50" width="16" height="16">
								<circle
									cx="25"
									cy="25"
									r="20"
									fill="none"
									stroke="currentColor"
									stroke-width="5"
									stroke-dasharray="80 40"
								/>
							</svg>
							{$_('Enrolling...')}
						{:else}
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2.5"
									d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
								/>
							</svg>
							{$_('Join the course')}
						{/if}
					</button>
				</div>
			{:else}
				<!-- ── SUCCESS STATE ── -->
				<div class="modal-success" in:fly={{ y: 12, duration: 280, easing: cubicOut }}>
					<div class="success-icon-wrap">
						<svg viewBox="0 0 24 24" fill="none" stroke="#22c55e" width="32" height="32">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2.5"
								d="M5 13l4 4L19 7"
							/>
						</svg>
					</div>
					<h2 class="modal-title">{$_('Course joined!')}</h2>
					<p class="modal-subtitle">{$_('You are now enrolled in the course.')}</p>
				</div>
			{/if}
		</div>
	</div>
{/if}

<!-- ═══════════════════════════════════════════════════════ -->
<!-- DELETE COURSE CONFIRMATION MODAL                        -->
<!-- ═══════════════════════════════════════════════════════ -->
{#if showDeleteModal}
	<div
		class="modal-overlay"
		role="button"
		tabindex="0"
		on:click={closeDeleteModal}
		on:keydown={(e) => e.key === 'Escape' && closeDeleteModal()}
		in:fade={{ duration: 200 }}
		out:fade={{ duration: 150 }}
	>
		<div
			class="modal-card modal-delete"
			role="dialog"
			aria-modal="true"
			on:click|stopPropagation
			on:keydown|stopPropagation
			in:fly={{ y: 20, duration: 300, easing: cubicOut }}
		>
			<div class="modal-body">
				<div class="delete-icon-wrap">
					<svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" width="32" height="32">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
						/>
					</svg>
				</div>

				<h2 class="modal-title">{$_('Leave this course?')}</h2>
				<p class="modal-subtitle">
					{$_('Are you sure you want to unenroll? You will lose access to all course resources.')}
				</p>

				{#if deleteError}
					<p class="input-err-msg text-center" in:fly={{ y: -4, duration: 150 }}>
						{deleteError}
					</p>
				{/if}

				<div class="delete-actions">
					<button class="btn-cancel" on:click={closeDeleteModal} disabled={isDeleting}>
						{$_('Cancel')}
					</button>
					<button class="btn-confirm-delete" on:click={unenrollCourse} disabled={isDeleting}>
						{#if isDeleting}
							<svg class="spin-icon" viewBox="0 0 50 50" width="16" height="16">
								<circle
									cx="25"
									cy="25"
									r="20"
									fill="none"
									stroke="currentColor"
									stroke-width="5"
									stroke-dasharray="80 40"
								/>
							</svg>
							{$_('Deleting...')}
						{:else}
							{$_('Yes, leave')}
						{/if}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	/* ── SECTION HEADER ── */
	.section-icon {
		width: 40px;
		height: 40px;
		border-radius: 0.75rem;
		background: linear-gradient(145deg, #3b5bdb, #2563eb);
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		box-shadow: 0 6px 14px -4px rgba(37, 99, 235, 0.35);
		flex-shrink: 0;
	}
	.section-title {
		font-size: 1.1rem;
		font-weight: 800;
		margin: 0 0 0.1rem;
		letter-spacing: -0.02em;
		color: #1e293b;
	}
	:global(.dark) .section-title {
		color: #f1f5f9;
	}
	.title-accent {
		color: #2563eb;
	}
	:global(.dark) .title-accent {
		color: #60a5fa;
	}
	.section-sub {
		font-size: 0.75rem;
		color: #64748b;
		margin: 0;
	}
	:global(.dark) .section-sub {
		color: #94a3b8;
	}

	/* ── SEE ALL ── */
	.see-all-btn {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.8rem;
		font-weight: 600;
		color: #2563eb;
		background: none;
		border: none;
		cursor: pointer;
		padding: 0.4rem 0.8rem;
		border-radius: 0.5rem;
		transition: background 0.2s;
	}
	.see-all-btn:hover {
		background: #eff6ff;
	}
	:global(.dark) .see-all-btn {
		color: #60a5fa;
	}
	:global(.dark) .see-all-btn:hover {
		background: rgba(96, 165, 250, 0.1);
	}

	/* ── EMPTY SECTION ── */
	.empty-section {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.6rem;
		padding: 2.5rem;
		text-align: center;
		background: white;
		border: 1.5px dashed #e2e8f0;
		border-radius: 1.25rem;
	}
	:global(.dark) .empty-section {
		background: #1e293b;
		border-color: #334155;
	}

	.btn-join-inline {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		background: linear-gradient(145deg, #3b5bdb, #2563eb);
		color: white;
		border: none;
		border-radius: 0.75rem;
		padding: 0.55rem 1.1rem;
		font-size: 0.82rem;
		font-weight: 700;
		cursor: pointer;
		transition: all 0.2s;
		margin-top: 0.25rem;
		font-family: inherit;
	}
	.btn-join-inline:hover {
		transform: translateY(-1px);
	}

	/* ── COURSE CARD DASHBOARD ── */
	.course-card-dash {
		background: white;
		border: 1.5px solid #e5e8f4;
		border-radius: 1.25rem;
		padding: 1.25rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
		transition: all 0.25s;
		position: relative;
		overflow: hidden;
	}
	.course-card-dash:hover {
		transform: translateY(-3px);
		box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.1);
		border-color: #bfdbfe;
	}
	:global(.dark) .course-card-dash {
		background: #1e293b;
		border-color: #334155;
	}
	:global(.dark) .course-card-dash:hover {
		border-color: #3b5bdb;
	}

	.new-highlight-dash {
		border-color: #3b5bdb !important;
		box-shadow:
			0 0 0 3px rgba(59, 91, 219, 0.12),
			0 12px 24px -8px rgba(59, 91, 219, 0.2) !important;
	}

	.new-badge-dash {
		position: absolute;
		top: 0.75rem;
		right: 0.75rem;
		background: linear-gradient(135deg, #3b5bdb, #2563eb);
		color: white;
		font-size: 0.65rem;
		font-weight: 800;
		padding: 0.2rem 0.55rem;
		border-radius: 2rem;
	}

	/* TOP ROW */
	.cc-top-dash {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
	}
	.cc-top-left-dash {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
		flex: 1;
		min-width: 0;
	}
	.cc-level-tag-dash {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.7rem;
		font-weight: 700;
		padding: 0.2rem 0.55rem;
		border-radius: 9999px;
		border: 1px solid transparent;
		white-space: nowrap;
	}
	.level-dot-dash {
		width: 5px;
		height: 5px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.cc-lang-dash {
		font-size: 0.9rem;
	}

	/* DELETE BUTTON DASHBOARD */
	.btn-delete-dash {
		background: transparent;
		border: none;
		padding: 0.35rem;
		border-radius: 0.5rem;
		color: #94a3b8;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
		flex-shrink: 0;
	}
	.btn-delete-dash:hover {
		background: #fef2f2;
		color: #ef4444;
		transform: scale(1.1);
	}
	:global(.dark) .btn-delete-dash:hover {
		background: rgba(239, 68, 68, 0.15);
		color: #f87171;
	}

	/* TITLE */
	.cc-title-dash {
		font-size: 0.95rem;
		font-weight: 700;
		color: #0f172a;
		margin: 0;
		line-height: 1.35;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		transition: color 0.2s;
	}
	.cc-title-dash:hover {
		color: #2563eb;
	}
	:global(.dark) .cc-title-dash {
		color: #f1f5f9;
	}
	:global(.dark) .cc-title-dash:hover {
		color: #60a5fa;
	}

	/* CATEGORY */
	.cc-cat-dash {
		display: inline-block;
		background: #f1f5f9;
		color: #475569;
		font-size: 0.7rem;
		font-weight: 600;
		padding: 0.18rem 0.55rem;
		border-radius: 9999px;
		align-self: flex-start;
	}
	:global(.dark) .cc-cat-dash {
		background: #334155;
		color: #94a3b8;
	}

	/* TEACHER */
	.cc-teacher-dash {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-top: auto;
	}
	.teacher-avatar-dash {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: linear-gradient(135deg, #dbe4ff, #bac8ff);
		color: #3b5bdb;
		font-size: 0.7rem;
		font-weight: 800;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		overflow: hidden;
	}
	.teacher-avatar-img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		border-radius: 50%;
	}
	:global(.dark) .teacher-avatar-dash {
		background: rgba(59, 91, 219, 0.2);
		color: #93c5fd;
	}
	.teacher-name-dash {
		font-size: 0.78rem;
		font-weight: 500;
		color: #64748b;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	:global(.dark) .teacher-name-dash {
		color: #94a3b8;
	}

	/* START BTN */
	.btn-start-dash {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.4rem;
		padding: 0.6rem 0.875rem;
		border-radius: 0.75rem;
		border: none;
		background: linear-gradient(145deg, #3b5bdb, #2563eb);
		color: white;
		font-weight: 700;
		font-size: 0.82rem;
		cursor: pointer;
		transition: all 0.2s;
		font-family: inherit;
		box-shadow: 0 6px 14px -4px rgba(37, 99, 235, 0.35);
		width: 100%;
	}
	.btn-start-dash:hover {
		background: linear-gradient(145deg, #2563eb, #1d4ed8);
		transform: translateY(-1px);
		box-shadow: 0 10px 18px -6px rgba(37, 99, 235, 0.45);
	}

	/* ── MODALS ── */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(15, 23, 42, 0.6);
		backdrop-filter: blur(8px);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 10000;
	}
	.modal-card {
		background: white;
		border-radius: 2rem;
		padding: 2.5rem 2.25rem 2.25rem;
		max-width: 420px;
		width: 92%;
		box-shadow:
			0 32px 64px -12px rgba(0, 0, 0, 0.24),
			0 0 0 1px rgba(0, 0, 0, 0.04);
		position: relative;
	}
	:global(.dark) .modal-card {
		background: #1e293b;
		border: 1px solid #334155;
	}
	.modal-delete {
		max-width: 380px;
		padding: 2.5rem 2rem 2rem;
	}

	.modal-close {
		position: absolute;
		top: 1.1rem;
		right: 1.1rem;
		background: #f1f5f9;
		border: none;
		cursor: pointer;
		color: #64748b;
		border-radius: 0.6rem;
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}
	.modal-close:hover {
		background: #e2e8f0;
		color: #1e293b;
	}
	:global(.dark) .modal-close {
		background: #334155;
		color: #94a3b8;
	}
	:global(.dark) .modal-close:hover {
		background: #475569;
		color: #f1f5f9;
	}

	.modal-body {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		text-align: center;
	}
	.modal-logo-wrap {
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 0.25rem;
	}
	.modal-logo-img {
		width: 80px;
		height: 80px;
		object-fit: contain;
	}

	.delete-icon-wrap {
		width: 64px;
		height: 64px;
		border-radius: 50%;
		background: #fef2f2;
		border: 2px solid #fecaca;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 0.5rem;
	}
	:global(.dark) .delete-icon-wrap {
		background: rgba(239, 68, 68, 0.15);
		border-color: rgba(239, 68, 68, 0.3);
	}

	.modal-title {
		font-size: 1.3rem;
		font-weight: 800;
		margin: 0;
		color: #0f172a;
		letter-spacing: -0.3px;
	}
	:global(.dark) .modal-title {
		color: #f8fafc;
	}
	.modal-subtitle {
		font-size: 0.88rem;
		color: #64748b;
		margin: 0;
		line-height: 1.55;
		max-width: 300px;
	}
	:global(.dark) .modal-subtitle {
		color: #94a3b8;
	}

	.input-group {
		width: 100%;
		text-align: left;
	}
	.input-label {
		display: block;
		font-size: 0.8rem;
		font-weight: 600;
		color: #475569;
		margin-bottom: 0.4rem;
	}
	:global(.dark) .input-label {
		color: #94a3b8;
	}

	.code-input {
		width: 100%;
		padding: 0.75rem 1rem;
		border: 1.5px solid #e2e8f0;
		border-radius: 0.875rem;
		background: #f8fafc;
		color: #1e293b;
		font-family: 'Courier New', monospace;
		font-size: 0.95rem;
		outline: none;
		box-sizing: border-box;
		transition: all 0.2s;
	}
	.code-input:focus {
		border-color: #3b5bdb;
		background: white;
		box-shadow: 0 0 0 3px rgba(59, 91, 219, 0.12);
	}
	.code-input.input-error {
		border-color: #ef4444;
		background: #fff5f5;
	}
	.code-input:disabled {
		opacity: 0.65;
		cursor: not-allowed;
	}
	:global(.dark) .code-input {
		background: #0f172a;
		border-color: #334155;
		color: #f1f5f9;
	}
	:global(.dark) .code-input:focus {
		border-color: #3b5bdb;
		background: #0f172a;
	}

	.input-err-msg {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.78rem;
		color: #ef4444;
		margin-top: 0.4rem;
		font-weight: 500;
	}
	.modal-hint {
		font-size: 0.78rem;
		color: #94a3b8;
		margin: 0;
		line-height: 1.5;
	}

	.btn-join-confirm {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.875rem 1.5rem;
		border-radius: 1rem;
		border: none;
		background: linear-gradient(145deg, #3b5bdb, #2563eb);
		color: white;
		font-weight: 700;
		font-size: 0.95rem;
		cursor: pointer;
		transition: all 0.2s;
		font-family: inherit;
		box-shadow: 0 8px 16px -6px rgba(37, 99, 235, 0.4);
	}
	.btn-join-confirm:hover:not(:disabled) {
		background: linear-gradient(145deg, #2563eb, #1d4ed8);
		transform: translateY(-2px);
	}
	.btn-join-confirm:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		transform: none;
	}

	/* DELETE MODAL ACTIONS */
	.delete-actions {
		display: flex;
		gap: 0.75rem;
		width: 100%;
		margin-top: 1rem;
	}

	.btn-cancel {
		flex: 1;
		padding: 0.85rem;
		border-radius: 1rem;
		border: 1.5px solid #e2e8f0;
		background: transparent;
		color: #64748b;
		font-weight: 700;
		font-size: 0.9rem;
		cursor: pointer;
		transition: all 0.2s;
		font-family: inherit;
	}
	.btn-cancel:hover:not(:disabled) {
		background: #f8fafc;
		color: #0f172a;
	}
	:global(.dark) .btn-cancel {
		border-color: #334155;
		color: #94a3b8;
	}
	:global(.dark) .btn-cancel:hover:not(:disabled) {
		background: #334155;
		color: #f8fafc;
	}

	.btn-confirm-delete {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 0.85rem;
		border-radius: 1rem;
		border: none;
		background: #ef4444;
		color: white;
		font-weight: 700;
		font-size: 0.9rem;
		cursor: pointer;
		transition: all 0.2s;
		font-family: inherit;
		box-shadow: 0 8px 16px -6px rgba(239, 68, 68, 0.4);
	}
	.btn-confirm-delete:hover:not(:disabled) {
		background: #dc2626;
		transform: translateY(-2px);
	}
	.btn-confirm-delete:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		transform: none;
	}

	/* SUCCESS MODAL */
	.modal-success {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.875rem;
		text-align: center;
		padding: 0.5rem 0;
	}
	.success-icon-wrap {
		width: 72px;
		height: 72px;
		border-radius: 50%;
		background: #f0fdf4;
		border: 2px solid #bbf7d0;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	:global(.dark) .success-icon-wrap {
		background: #052e16;
		border-color: #166534;
	}

	/* SPIN */
	.spin-icon {
		animation: spin 0.8s linear infinite;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	/* ── CARD ANIMATIONS ── */
	.card-container {
		position: relative;
		overflow: hidden;
	}
	.card-item {
		transform-origin: center center;
		backface-visibility: hidden;
		transition: transform 0.2s ease;
		display: flex;
	}
	.card-item > :global(*) {
		flex: 1;
		height: 100%;
	}
	.card-item:hover {
		transform: translateY(-3px);
	}

	.card-slide-enter-from-right {
		animation: slideInFromRight 0.5s cubic-bezier(0.25, 0.1, 0.25, 1) forwards;
	}
	.card-slide-enter-from-left {
		animation: slideInFromLeft 0.5s cubic-bezier(0.25, 0.1, 0.25, 1) forwards;
	}

	@keyframes slideInFromRight {
		from {
			transform: translateX(30px);
			opacity: 0;
		}
		to {
			transform: translateX(0);
			opacity: 1;
		}
	}
	@keyframes slideInFromLeft {
		from {
			transform: translateX(-30px);
			opacity: 0;
		}
		to {
			transform: translateX(0);
			opacity: 1;
		}
	}
</style>
