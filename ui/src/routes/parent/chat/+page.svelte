<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import Chat from '$lib/components/student/tutor/Chat.svelte';
	import RightBar from '$lib/components/student/elements/RightBar.svelte';
	import { isFullscreenAvatar } from '$lib/stores';
	import { linkChatToSupport } from '$lib/apis/parent';

	let chatData = {};

	function handleChatEvent(event: any) {
		chatData = { ...chatData, ...event.detail };
	}

	// Déclaré en dehors de onMount pour pouvoir le supprimer dans onDestroy
	async function handleChatCreated(event: any) {
		const { chatId, success } = event.detail ?? {};
		console.log('[Parent] chatCreated event reçu:', { chatId, success });
		if (!success || !chatId) return;

		const token = localStorage.getItem('token');
		const pendingRaw = localStorage.getItem('pendingSupportData');
		console.log('[Parent] pendingSupportData:', pendingRaw);

		if (token && pendingRaw) {
			try {
				const pending = JSON.parse(pendingRaw);
				if (pending?.id) {
					console.log(`[Parent] Liaison chat ${chatId} → soutien ${pending.id}`);
					await linkChatToSupport(token, pending.id, chatId);
					localStorage.removeItem('pendingSupportData');
				}
			} catch (e) {
				console.error('[Parent] Erreur liaison:', e);
			}
		}

		goto(`/parent/c/${chatId}`, { replaceState: true });
	}

	onMount(() => {
		if (!browser) return;
		const token = localStorage.getItem('token');
		if (!token) { goto('/auth'); return; }

		// Attendre que Chat.svelte initialise openTutorEvents
		const waitForEvents = setInterval(() => {
			if (window.openTutorEvents) {
				clearInterval(waitForEvents);
				console.log('[Parent] openTutorEvents disponible, écoute activée');
				window.openTutorEvents.addEventListener('chatCreated', handleChatCreated);
			}
		}, 50);

		// Timeout 10 secondes
		setTimeout(() => {
			clearInterval(waitForEvents);
			// Si toujours pas disponible, forcer la création
			if (window.openTutorEvents) {
				window.openTutorEvents.addEventListener('chatCreated', handleChatCreated);
			}
		}, 10000);
	});

	onDestroy(() => {
		if (browser && window.openTutorEvents) {
			window.openTutorEvents.removeEventListener('chatCreated', handleChatCreated);
		}
	});
</script>

<div class="flex h-screen overflow-hidden bg-white dark:bg-gray-900 p-2">
	<div class="flex-1 h-full overflow-hidden bg-[#F5F7F9] dark:bg-gray-900 rounded-2xl shadow-sm mr-2">
		<Chat on:chatEvent={handleChatEvent} />
	</div>
	{#if !$isFullscreenAvatar}
		<div class="h-full w-80 bg-[#F5F7F9] dark:bg-gray-900 rounded-2xl shadow-sm overflow-y-auto">
			<RightBar {chatData} />
		</div>
	{/if}
</div>