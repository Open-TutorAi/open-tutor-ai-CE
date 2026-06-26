<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import Chat from '$lib/components/student/tutor/Chat.svelte';
	import RightBar from '$lib/components/student/elements/RightBar.svelte';
	import { isFullscreenAvatar } from '$lib/stores';
	import { TUTOR_API_BASE_URL } from '$lib/constants';

	let chatData = {};
	let courseCompletion = 0;
	let supportId = '';
	let progressInterval: ReturnType<typeof setInterval>;
	let interceptInterval: ReturnType<typeof setInterval>;

	$: chatId = $page.params.id;
	// Recharger la progression quand chatId change
	$: if (chatId && browser) {
		const t = localStorage.getItem('token');
		if (t) fetchSupportId(t);
	}

	function handleChatEvent(event: any) {
		chatData = { ...chatData, ...event.detail };
		// Mettre à jour la progression après chaque message IA
		const t = localStorage.getItem('token');
		if (t && supportId) updateProgress(t);
	}

	// Trouver le support_id lié à ce chat_id
	async function fetchSupportId(token: string) {
		try {
			// Utiliser l'ID étudiant depuis localStorage
			const studentId = localStorage.getItem('parent_student_id') 
				?? 'e7081ab6-fce1-4111-ae63-74c0e6ae46b6';
			
			const res = await fetch(`${TUTOR_API_BASE_URL}/parent/supports/list/${studentId}`, {
				headers: { authorization: `Bearer ${token}` }
			});
			if (!res.ok) return;
			const supports = await res.json();
			const support = supports.find((s: any) => s.chat_id === chatId);
			if (support) {
				supportId = support.id;
				// Charger la progression immédiatement
				await updateProgress(token);
			}
		} catch (e) { 
			console.error('Support lookup failed:', e); 
		}
	}

	// Calculer et mettre à jour la progression
	async function updateProgress(token: string) {
		if (!supportId) return;
		try {
			const res = await fetch(`${TUTOR_API_BASE_URL}/parent/support-progress/${supportId}`, {
				headers: { authorization: `Bearer ${token}` }
			});
			if (!res.ok) return;
			const data = await res.json();
			courseCompletion = data.progress ?? 0;
		} catch (e) { 
			console.error('Progress fetch failed:', e); 
		}
	}

	onMount(async () => {
		if (!browser) return;
		const token = localStorage.getItem('token');
		if (!token) { goto('/auth'); return; }

		// Trouver le support et charger la progression
		await fetchSupportId(token);

		// Rafraîchir la progression toutes les 15 secondes (après chaque réponse IA)
		progressInterval = setInterval(() => updateProgress(token), 15000);

		// Intercepter /student/c/... → /parent/c/...
		interceptInterval = setInterval(() => {
			const path = window.location.pathname;
			if (path.startsWith('/student/c/')) {
				const id = path.replace('/student/c/', '');
				if (id) {
					clearInterval(interceptInterval);
					goto(`/parent/c/${id}`, { replaceState: true });
				}
			}
		}, 100);

		setTimeout(() => clearInterval(interceptInterval), 30000);
	});

	onDestroy(() => {
		if (progressInterval) clearInterval(progressInterval);
		if (interceptInterval) clearInterval(interceptInterval);
	});
</script>

<div class="flex h-screen overflow-hidden bg-white dark:bg-gray-900 p-2">
	<div class="flex-1 h-full overflow-hidden bg-[#F5F7F9] dark:bg-gray-900 rounded-2xl shadow-sm mr-2">
		<Chat chatIdProp={chatId} on:chatEvent={handleChatEvent} />
	</div>
	{#if !$isFullscreenAvatar}
		<div class="h-full w-80 bg-[#F5F7F9] dark:bg-gray-900 rounded-2xl shadow-sm overflow-y-auto">
			<RightBar {chatData} {courseCompletion} />
		</div>
	{/if}
</div>