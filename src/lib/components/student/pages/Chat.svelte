<!-- chat/+page.svelte -->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import Chat from '$lib/components/student/tutor/Chat.svelte';
	import RightBar from '$lib/components/student/elements/RightBar.svelte';
	import { page } from '$app/stores';
	import { isFullscreenAvatar } from '$lib/stores';
	import { updateSupportChatId } from '$lib/apis/supports';

	let chatData = {};
	let isRightBarVisible = false;

	// ── Chat ↔ Support linker ─────────────────────────────────────────
	// When a student starts a chat from a support page, SupportDetails.svelte
	// writes the support id to localStorage["pendingSupportData"] then lets
	// the navigation happen. The original linker lived only in Dashboard.svelte,
	// which only fires if the student visits the dashboard after the chat ID
	// appears — unreliable in the common flow.
	//
	// Open WebUI's tutor Chat.svelte uses window.history.replaceState() to
	// set the new chat URL once a chat is created — that bypasses SvelteKit's
	// router, so $page never updates. The reliable signal Open WebUI does
	// expose is a custom DOM event: it dispatches `chatCreated` on
	// window.openTutorEvents with { chatId, timestamp, success: true } as
	// soon as the chat is persisted (see student/tutor/Chat.svelte ~line 2636).
	// We listen for that event here.
	//
	// The Dashboard linker is kept untouched as a safety net.
	const MAX_PENDING_AGE_MS = 30 * 60 * 1000;
	let chatCreatedHandler: ((e: Event) => void) | null = null;
	let linkedFor = '';

	function isRealChatId(v: unknown): v is string {
		return (
			typeof v === 'string' &&
			v.length > 8 &&
			v !== 'local' &&
			v !== 'undefined'
		);
	}

	async function linkPendingSupport(newChatId: string) {
		if (!browser) return;
		if (!isRealChatId(newChatId)) return;
		if (newChatId === linkedFor) return;

		const raw = localStorage.getItem('pendingSupportData');
		if (!raw) return;

		let pending: { id?: string; timestamp?: number } | null = null;
		try {
			pending = JSON.parse(raw);
		} catch {
			localStorage.removeItem('pendingSupportData');
			return;
		}
		if (!pending?.id) {
			localStorage.removeItem('pendingSupportData');
			return;
		}
		if (Date.now() - (pending.timestamp ?? 0) > MAX_PENDING_AGE_MS) {
			localStorage.removeItem('pendingSupportData');
			return;
		}

		const token = localStorage.getItem('token') ?? '';
		if (!token) return;

		// Mark this chat as handled before the network call so a rapid second
		// event with the same id cannot double-fire.
		linkedFor = newChatId;
		// Clear the pending data unconditionally after the first attempt — if
		// the update fails we still don't want to retry on a different chat
		// id later (which would link the wrong support). The Dashboard
		// fallback, if it ever fires, will also see no pending data and exit.
		localStorage.removeItem('pendingSupportData');

		try {
			await updateSupportChatId(token, pending.id, newChatId);
			console.log(
				`[chat-support link] linked support ${pending.id} → chat ${newChatId}`
			);
		} catch (e) {
			console.error('[chat-support link] update failed:', e);
		}
	}

	function handleChatEvent(event: CustomEvent) {
		// Process chat events and update rightbar if needed
		chatData = {...chatData, ...event.detail};
	}

	function toggleRightBar() {
		isRightBarVisible = !isRightBarVisible;
	}

	onMount(() => {
		if (!browser) return;

		// Open WebUI initialises window.openTutorEvents lazily in its Chat
		// components — make sure it exists before we attach (defensive: if
		// pages/Chat.svelte mounts before tutor/Chat.svelte, the target
		// would otherwise be undefined).
		if (!(window as any).openTutorEvents) {
			(window as any).openTutorEvents = new EventTarget();
		}

		chatCreatedHandler = (e: Event) => {
			const detail = (e as CustomEvent).detail ?? {};
			if (detail.success === false) return; // creation failed — nothing to link
			const id = typeof detail.chatId === 'string' ? detail.chatId : '';
			void linkPendingSupport(id);
		};

		(window as any).openTutorEvents.addEventListener(
			'chatCreated',
			chatCreatedHandler
		);
	});

	onDestroy(() => {
		if (!browser) return;
		if (chatCreatedHandler && (window as any).openTutorEvents) {
			(window as any).openTutorEvents.removeEventListener(
				'chatCreated',
				chatCreatedHandler
			);
		}
	});
</script>

<div class="chat-layout flex h-full overflow-hidden relative bg-white dark:bg-gray-900 {$isFullscreenAvatar ? '' : 'p-2'}">
	<!-- Main Chat component takes most of the space -->
	<div class="chat-container flex-1 h-full overflow-hidden bg-[#F5F7F9] dark:bg-gray-900 {$isFullscreenAvatar ? '' : 'rounded-2xl shadow-sm mr-2'}">
		<Chat chatIdProp={$page.params.id} on:chatEvent={handleChatEvent} />
		
		<!-- Toggle button for mobile - hide in fullscreen -->
		{#if !$isFullscreenAvatar}
			<button
				class="toggle-rightbar hidden max-[1210px]:block fixed right-4 bottom-4 bg-blue-500 hover:bg-blue-600 text-white rounded-full p-2 shadow-lg z-99999"
				on:click={toggleRightBar}
				aria-label={isRightBarVisible ? 'Hide sidebar' : 'Show sidebar'}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
					class="w-4 h-4"
				>
					{#if isRightBarVisible}
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					{:else}
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M15 19l-7-7 7-7"
						/>
					{/if}
				</svg>
			</button>
		{/if}
	</div>
	
	<!-- RightBar with fixed width - hide in fullscreen -->
	{#if !$isFullscreenAvatar}
		<div class="rightbar-container h-full w-80 bg-[#F5F7F9] dark:bg-gray-900 rounded-2xl shadow-sm overflow-y-auto transition-transform duration-300 ease-in-out"
			class:mobile-visible={isRightBarVisible}
		>
			<RightBar {chatData} />
		</div>
	{/if}
</div>

<style>
	.chat-layout {
		/* Ensure this layout container takes full height within parent */
		height: 100%;
		width: 100%;
	}
	
	.chat-container, .rightbar-container {
		/* Ensure proper scroll containment */
		height: 100%;
	}
	
	/* Mobile styles */
	@media (max-width: 1210px) {
		.rightbar-container {
			position: fixed;
			right: -320px; /* Start off-screen */
			top: 0;
			bottom: 0;
			z-index: 9999;
			background: var(--background-color, #ffffff);
			backdrop-filter: blur(8px);
			transition: transform 0.3s ease-in-out;
			border-left: 1px solid rgba(229, 231, 235, 0.1);
		}

		.rightbar-container.mobile-visible {
			transform: translateX(-320px);
		}

		:global(.dark) .rightbar-container {
			--background-color: rgba(31, 41, 55, 0.95);
		}
	}

	/* Desktop styles */
	@media (min-width: 1211px) {
		.rightbar-container {
			position: relative;
			right: 0;
		}
	}

	.toggle-rightbar {
		transition: transform 0.3s ease-in-out;
	}

	.toggle-rightbar:hover {
		transform: scale(1.1);
	}
</style>