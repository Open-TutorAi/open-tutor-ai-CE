<!-- Dashboard.svelte -->
<script lang="ts">
	import { getContext, onMount, onDestroy } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { chatId as storeChatId, isDemo, demoData } from '$lib/stores';
	import CourseCard from '../elements/CourseCard.svelte';
	import { getSupportRequests, type SupportResponse, updateSupportChatId } from '$lib/apis/supports';
	import { page } from '$app/stores';
	import { fade, scale } from 'svelte/transition';
	import { toast } from 'svelte-sonner';

	const i18n = getContext<Writable<i18nType>>('i18n');

	let userSupports: SupportResponse[] = [];
	let isLoading = true;

	$: displaySupports = $isDemo ? $demoData.supports.map(s => ({
		id: s.id, title: s.title, description: s.description,
		status: s.progress < 30 ? 'not-started' : s.progress < 100 ? 'in-progress' : 'completed',
		category: s.category, difficulty: s.difficulty, progress: s.progress
	})) : userSupports;

	let pendingSupportId = '';
	let chatIdSubscription: Function;
	let urlCheckInterval: ReturnType<typeof setInterval>;
	let currentPath = '';
	let chatIdFromURL = '';

	// ── Blockly popup state ──────────────────────────────────────
	let showBlocklyPopup = false;
	let blocklyForm = { course: '', objectives: '', prerequisites: '', level: 'beginner' };
	let blocklyLoading = false;

	function toggleBlocklyPopup() {
		showBlocklyPopup = !showBlocklyPopup;
	}

	async function handleStartBlockly() {
		if (!blocklyForm.course.trim()) {
			toast.error('Veuillez entrer un cours');
			return;
		}
		blocklyLoading = true;
		// Sauvegarder le contexte pour la page Blockly
		if (browser) {
			localStorage.setItem('blocklyContext', JSON.stringify(blocklyForm));
		}
		showBlocklyPopup = false;
		blocklyLoading = false;
		goto('/student/blockly/new');
	}
	// ────────────────────────────────────────────────────────────

	onMount(async () => {
		if (browser) {
			storeChatId.set('');
			if (sessionStorage.selectedModels) sessionStorage.removeItem('selectedModels');
			if (localStorage.getItem('pendingSupportData')) localStorage.removeItem('pendingSupportData');
			const keysToRemove = [];
			for (let i = 0; i < localStorage.length; i++) {
				const key = localStorage.key(i);
				if (key && key.startsWith('chat-input-')) keysToRemove.push(key);
			}
			keysToRemove.forEach(key => localStorage.removeItem(key));

			if ($isDemo) {
				isLoading = false;
			} else {
				const token = localStorage.getItem('token');
				if (token) {
					try {
						const supports = await getSupportRequests(token);
						if (supports && Array.isArray(supports)) userSupports = supports;
					} catch (error) {
						userSupports = [];
					} finally {
						isLoading = false;
					}
				} else {
					isLoading = false;
				}
			}

			if (!window.openTutorEvents) window.openTutorEvents = new EventTarget();
			window.openTutorEvents.addEventListener('chatCreated', ((event: CustomEvent) => {
				const newChatId = event.detail?.chatId;
				if (newChatId && pendingSupportId) updateSupportWithChatId(pendingSupportId, newChatId);
			}) as EventListener);

			chatIdSubscription = storeChatId.subscribe((newChatId) => {
				if (newChatId && newChatId !== 'local' && pendingSupportId)
					updateSupportWithChatId(pendingSupportId, newChatId);
			});

			urlCheckInterval = setInterval(() => {
				try {
					const pendingSupportData = localStorage.getItem('pendingSupportData');
					if (!pendingSupportData) { clearInterval(urlCheckInterval); return; }
					const supportData = JSON.parse(pendingSupportData);
					const currentTime = Date.now();
					if (currentTime - (supportData.timestamp || 0) >= 30 * 60 * 1000) {
						localStorage.removeItem('pendingSupportData');
						clearInterval(urlCheckInterval);
						return;
					}
					const currentURL = window.location.pathname;
					if (currentURL.startsWith('/student/c/')) {
						const newChatId = currentURL.split('/student/c/')[1].split('/')[0];
						if (newChatId && supportData.id) updateSupportWithChatId(supportData.id, newChatId);
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
					if (supportId && currentTime - (supportData.timestamp || 0) < 30 * 60 * 1000) {
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
		let pendingSupportData;
		try {
			pendingSupportData = localStorage.getItem('pendingSupportData');
			if (!pendingSupportData) return;
			const supportData = JSON.parse(pendingSupportData);
			if (supportData.id !== supportId) return;
			if (Date.now() - (supportData.timestamp || 0) >= 30 * 60 * 1000) {
				localStorage.removeItem('pendingSupportData'); return;
			}
		} catch (error) {
			localStorage.removeItem('pendingSupportData'); return;
		}
		try {
			const token = localStorage.getItem('token');
			if (!token) return;
			await updateSupportChatId(token, supportId, chatId);
			localStorage.removeItem('pendingSupportData');
			pendingSupportId = '';
		} catch (error) {
			try {
				const supportData = JSON.parse(pendingSupportData || '{}');
				const attemptCount = (supportData.attempts || 0) + 1;
				if (attemptCount >= 3) {
					localStorage.removeItem('pendingSupportData');
				} else {
					supportData.attempts = attemptCount;
					localStorage.setItem('pendingSupportData', JSON.stringify(supportData));
				}
			} catch { localStorage.removeItem('pendingSupportData'); }
		}
	}

	let currentPage = 0;
	const cardsPerPage = 4;
	$: totalPages = Math.ceil(displaySupports.length / cardsPerPage);
	$: currentSupports = displaySupports.slice(currentPage * cardsPerPage, (currentPage + 1) * cardsPerPage);
	let animationDirection = 'right';
	function nextPage() { if (currentPage < totalPages - 1) { animationDirection = 'right'; currentPage += 1; } }
	function previousPage() { if (currentPage > 0) { animationDirection = 'left'; currentPage -= 1; } }
	function goToPage(pageIndex: number) {
		if (pageIndex !== currentPage) { animationDirection = pageIndex > currentPage ? 'right' : 'left'; currentPage = pageIndex; }
	}

	let showJoinCoursePopup = false;
	let showSupportPopup = false;
	function toggleJoinCoursePopup() { showJoinCoursePopup = !showJoinCoursePopup; if (showJoinCoursePopup) showSupportPopup = false; }
	function toggleSupportPopup() {
		if (dontShowAgain || (browser && localStorage.getItem('hideSupportPopup') === 'true')) { goto('/student/support/create'); return; }
		showSupportPopup = !showSupportPopup;
		if (showSupportPopup) showJoinCoursePopup = false;
	}
	let courseCode = '';
	let dontShowAgain = false;
	if (browser) { const storedFlag = localStorage.getItem('hideSupportPopup') === 'true'; if (storedFlag) dontShowAgain = true; }
	function handleJoinCourse() {
		if (courseCode === '0000') { goto('/student/chat'); showJoinCoursePopup = false; }
		else if (courseCode.trim() !== '') { showJoinCoursePopup = false; }
	}
	$: if (browser) {
		if (dontShowAgain) localStorage.setItem('hideSupportPopup', 'true');
		else localStorage.removeItem('hideSupportPopup');
	}
	function handleCreateSupport() { goto('/student/support/create'); showSupportPopup = false; }
	function handleCardClick(support: SupportResponse, index: number) { goto(`/student/support/${support.id}`); }
</script>

<div class="flex flex-col gap-6">
	<div class="flex justify-end">
		<div class="flex gap-3">
			<!-- 🧩 Bouton Blockly -->
			<button
				class="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full transition shadow-md"
				on:click={toggleBlocklyPopup}
			>
				<span class="text-base">🧩</span>
				Blockly
			</button>

			<!-- Bouton Support existant -->
			<button
				class="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full transition"
				on:click={toggleSupportPopup}
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
				</svg>
				{$i18n.t('Support')}
			</button>
		</div>
	</div>

	<div class="flex flex-col gap-6">
		{#if isLoading}
			<div class="flex justify-center items-center py-12">
				<div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
				<span class="ml-3 text-gray-600 dark:text-gray-300">{$i18n.t('Loading your supports...')}</span>
			</div>
		{:else if displaySupports.length === 0}
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
				<button class="absolute left-0 top-1/2 transform -translate-y-1/2 -translate-x-4 sm:-translate-x-6 p-2 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-all" on:click={previousPage}>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
				</button>
				{/if}
				{#if currentPage < totalPages - 1}
				<button class="absolute right-0 top-1/2 transform -translate-y-1/2 translate-x-4 sm:translate-x-6 p-2 rounded-full bg-white dark:bg-gray-700 shadow-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 z-10 transition-all" on:click={nextPage}>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" /></svg>
				</button>
				{/if}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 card-container">
					{#each currentSupports as support, index (support.id)}
						<div class="cursor-pointer card-item h-full"
							class:card-slide-enter-from-right={animationDirection === 'right'}
							class:card-slide-enter-from-left={animationDirection === 'left'}
							on:click={() => handleCardClick(support, index)}
							on:keypress={(e) => e.key === 'Enter' && handleCardClick(support, index)}
							tabindex="0" role="button" style="animation-delay: {index * 0.05}s">
							<CourseCard title={support.title} subject={support.subject || 'mathematics'} progress={0} href="#" />
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>

<!-- ── Blockly Popup ──────────────────────────────────────────────────── -->
{#if showBlocklyPopup}
<div class="fixed inset-0 backdrop-blur-sm bg-black/40 flex items-center justify-center z-50" role="dialog" aria-modal="true" in:fade>
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 w-11/12 max-w-lg mx-auto relative ring-1 ring-gray-200 dark:ring-gray-700" transition:scale={{ duration: 200 }}>
		<button class="absolute top-3 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-2xl font-light" on:click={toggleBlocklyPopup}>×</button>

		<!-- Header -->
		<div class="flex items-center gap-3 mb-6">
			<div class="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center text-2xl shadow-sm">🧩</div>
			<div>
				<h2 class="text-xl font-bold text-gray-900 dark:text-white">Exercice Blockly</h2>
				<p class="text-sm text-gray-500 dark:text-gray-400">Apprenez à programmer avec des blocs visuels</p>
			</div>
		</div>

		<!-- Formulaire -->
		<div class="space-y-4">
			<!-- Cours -->
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
					📚 Cours / Sujet <span class="text-red-500">*</span>
				</label>
				<input
					type="text"
					bind:value={blocklyForm.course}
					placeholder="Ex: Structures de contrôle, Boucles, Variables..."
					class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
				/>
			</div>

			<!-- Objectifs -->
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
					🎯 Objectifs d'apprentissage
				</label>
				<textarea
					bind:value={blocklyForm.objectives}
					placeholder="Ex: Comprendre les boucles for, savoir afficher des résultats..."
					rows="2"
					class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
				></textarea>
			</div>

			<!-- Prérequis -->
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
					✅ Prérequis (ce que vous savez déjà)
				</label>
				<input
					type="text"
					bind:value={blocklyForm.prerequisites}
					placeholder="Ex: Je connais les variables et print()"
					class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
				/>
			</div>

			<!-- Niveau -->
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">🏆 Niveau de départ</label>
				<div class="grid grid-cols-3 gap-2">
					{#each [['beginner','🌱','Débutant'],['intermediate','🔥','Intermédiaire'],['advanced','⚡','Avancé']] as [val, emoji, label]}
						<button
							class="py-2 px-3 rounded-xl border-2 text-sm font-medium transition-all {blocklyForm.level === val ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300' : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-blue-400'}"
							on:click={() => blocklyForm.level = val}
						>
							{emoji} {label}
						</button>
					{/each}
				</div>
			</div>
		</div>

		<!-- Bouton démarrer -->
		<button
			class="mt-6 w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl shadow-sm transition-colors duration-200 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
			on:click={handleStartBlockly}
			disabled={blocklyLoading || !blocklyForm.course.trim()}
		>
			{#if blocklyLoading}
				<div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
				Préparation...
			{:else}
				🚀 Démarrer l'exercice
			{/if}
		</button>
	</div>
</div>
{/if}

<!-- Support Popup existant -->
{#if showJoinCoursePopup}
<div class="fixed inset-0 backdrop-blur-sm bg-white/30 dark:bg-black/30 flex items-center justify-center z-50" role="dialog" aria-modal="true" in:fade>
	<div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-11/12 sm:w-full max-w-md mx-auto relative overflow-y-auto max-h-[90vh] ring-1 ring-gray-200 dark:ring-gray-700" transition:scale={{ duration: 200 }}>
		<button class="absolute top-3 right-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none" on:click={toggleJoinCoursePopup}><span class="text-2xl font-light">×</span></button>
		<div class="flex justify-center mb-8"><img src="/favicon.png" alt="OT Logo" class="w-26 h-26" /></div>
		<h2 class="text-center text-xl font-bold mb-2 text-gray-900 dark:text-white">{$i18n.t('Enter the course code provided by your teacher')}</h2>
		<p class="text-center text-gray-500 dark:text-gray-400 mb-6">{$i18n.t('The code is a 6-8 character alphanumeric string')}</p>
		<div class="mb-6">
			<input type="text" bind:value={courseCode} placeholder={$i18n.t('Enter Course Code')} class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md text-center focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" on:keydown={(e) => e.key === 'Enter' && handleJoinCourse()} />
		</div>
		<div class="flex justify-center mb-4">
			<button class="bg-indigo-600 hover:bg-indigo-700 text-white py-3 px-8 rounded-full font-medium" on:click={handleJoinCourse}>{$i18n.t('Join Course')}</button>
		</div>
	</div>
</div>
{/if}

{#if showSupportPopup}
<div class="fixed inset-0 backdrop-blur-sm bg-white/30 dark:bg-black/30 flex items-center justify-center z-50" role="dialog" aria-modal="true" in:fade>
	<div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-4 w-11/12 sm:w-full max-w-sm mx-auto relative overflow-y-auto max-h-[90vh] ring-1 ring-gray-200 dark:ring-gray-700" transition:scale={{ duration: 200 }}>
		<button class="absolute top-2 right-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none" on:click={toggleSupportPopup}><span class="text-xl font-light">×</span></button>
		<div class="flex justify-center mb-4"><img src="/favicon.png" alt="OT Logo" class="w-20 h-20" /></div>
		<h2 class="text-center text-lg font-bold text-gray-900 dark:text-white mb-4">{$i18n.t('Create Personalized Tutorials for any Subject or Topic')}</h2>
		<div class="space-y-3 mb-6 px-2">
			{#each [['1','Choose your topic and level'],['2','Set your learning objectives'],['3','Enjoy AI-powered personalized learning']] as [num, text]}
			<div class="flex items-center gap-3">
				<div class="flex-shrink-0 bg-[#004AAD] text-white rounded-full w-6 h-6 flex items-center justify-center"><span class="font-bold text-sm">{num}</span></div>
				<span class="text-sm text-gray-800 dark:text-gray-200">{$i18n.t(text)}</span>
			</div>
			{/each}
		</div>
		<div class="flex justify-center mb-4">
			<button class="bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-8 rounded-full font-medium text-sm" on:click={handleCreateSupport}>{$i18n.t('Create My support')}</button>
		</div>
		<div class="flex items-center justify-center gap-2">
			<input type="checkbox" id="dontShow" bind:checked={dontShowAgain} class="h-3 w-3" />
			<label for="dontShow" class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t("Don't show me again")}</label>
		</div>
	</div>
</div>
{/if}

<style>
	.card-container { position: relative; overflow: hidden; }
	.card-item { transform-origin: center center; backface-visibility: hidden; transition: transform 0.2s ease; display: flex; }
	.card-item > :global(*) { flex: 1; height: 100%; }
	.card-item:hover { transform: translateY(-3px); }
	.card-slide-enter-from-right { animation: slideInFromRight 0.5s cubic-bezier(0.25, 0.1, 0.25, 1) forwards; }
	.card-slide-enter-from-left { animation: slideInFromLeft 0.5s cubic-bezier(0.25, 0.1, 0.25, 1) forwards; }
	@keyframes slideInFromRight { from { transform: translateX(30px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
	@keyframes slideInFromLeft { from { transform: translateX(-30px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
</style>