<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { user } from '$lib/stores';
	import { getConversations } from '$lib/apis/messages';
	import type { Conversation } from '$lib/apis/messages';
	import ConversationView from './ConversationView.svelte';
	import { formatRelativeTime } from '$lib/utils/time';

	const i18n = getContext('i18n');

	export let totalUnread: number = 0;

	let conversations: Conversation[] = [];
	let filtered: Conversation[] = [];
	let loading = true;
	let error: string | null = null;
	let selectedConversation: Conversation | null = null;
	let searchQuery = '';
	let isSearchFocused = false;

	$: filtered = searchQuery.trim()
		? conversations.filter((c) => {
				const q = searchQuery.toLowerCase();
				return c.teacher_name.toLowerCase().includes(q) || c.student_name.toLowerCase().includes(q);
			})
		: conversations;

	$: totalUnread = conversations.reduce((s, c) => s + c.unread_count, 0);

	const selectConversation = (conv: Conversation) => {
		selectedConversation = conv;
		conversations = conversations.map((c) => (c.id === conv.id ? { ...c, unread_count: 0 } : c));
	};

	onMount(async () => {
		if (!$user) return;
		try {
			conversations = await getConversations(localStorage.token);
		} catch (err: any) {
			error = err || 'Impossible de charger les messages';
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex h-full bg-white dark:bg-gray-850 rounded-xl border border-gray-100 dark:border-gray-800 overflow-hidden">
	<!-- Left panel: conversation list -->
	<div
		class="w-full md:w-80 flex-shrink-0 flex flex-col border-r border-gray-100 dark:border-gray-800 {selectedConversation
			? 'hidden md:flex'
			: 'flex'}"
	>
		<!-- Header -->
		<div class="px-4 pt-4 pb-3 border-b border-gray-100 dark:border-gray-800">
			<div class="flex items-center justify-between mb-3">
				<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-200">Mes messages</h2>
				{#if totalUnread > 0}
					<span class="flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-xs text-white font-bold">
						{totalUnread > 9 ? '9+' : totalUnread}
					</span>
				{/if}
			</div>
			<!-- Search -->
			<div
				class="flex items-center bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-lg px-3 py-2 {isSearchFocused
					? 'ring-2 ring-blue-400/40'
					: ''}"
			>
				<svg class="h-4 w-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<input
					type="text"
					bind:value={searchQuery}
					on:focus={() => (isSearchFocused = true)}
					on:blur={() => (isSearchFocused = false)}
					placeholder="Rechercher un enseignant ou élève…"
					class="bg-transparent border-none outline-none focus:ring-0 px-2 py-1 w-full text-sm text-gray-700 dark:text-gray-100 placeholder-gray-400"
				/>
				{#if searchQuery}
					<button
						class="h-4 w-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 flex-shrink-0"
						on:click={() => (searchQuery = '')}
					>
						<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				{/if}
			</div>
		</div>

		<!-- List body -->
		{#if loading}
			<div class="flex justify-center items-center flex-1 py-12">
				<div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
			</div>
		{:else if error}
			<p class="text-center text-red-500 text-sm p-6">{error}</p>
		{:else if conversations.length === 0}
			<div class="flex flex-col items-center justify-center flex-1 py-16 px-6 text-center">
				<svg class="w-10 h-10 text-indigo-400 dark:text-indigo-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
				</svg>
				<p class="text-sm font-medium text-gray-800 dark:text-white mb-2">Aucune conversation</p>
				<p class="text-sm text-gray-600 dark:text-gray-400">Utilisez "Enseignants" pour en démarrer une.</p>
			</div>
		{:else if filtered.length === 0}
			<div class="flex flex-col items-center justify-center flex-1 py-12 px-6 text-center">
				<p class="text-sm text-gray-500 dark:text-gray-400">
					Aucun résultat pour "<span class="font-medium">{searchQuery}</span>"
				</p>
			</div>
		{:else}
			<ul class="flex-1 overflow-y-auto divide-y divide-gray-50 dark:divide-gray-800">
				{#each filtered as conv (conv.id)}
					{@const isSelected = selectedConversation?.id === conv.id}
					<li>
						<button
							class="w-full text-left px-4 py-3.5 transition-colors {isSelected
								? 'bg-gray-100 dark:bg-gray-900'
								: 'hover:bg-gray-50 dark:hover:bg-gray-900'}"
							on:click={() => selectConversation(conv)}
						>
							<div class="flex items-center gap-3">
								<div class="relative flex-shrink-0">
									<div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-semibold text-sm">
										{conv.teacher_name[0]?.toUpperCase() ?? '?'}
									</div>
									{#if conv.unread_count > 0}
										<span class="absolute top-0 right-0 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] text-white font-bold border-2 border-white dark:border-gray-800">
											{conv.unread_count > 9 ? '9+' : conv.unread_count}
										</span>
									{/if}
								</div>
								<div class="flex-1 min-w-0">
									<div class="flex items-center justify-between gap-1">
										<p class="text-sm truncate {conv.unread_count > 0
											? 'font-bold text-gray-900 dark:text-white'
											: 'font-medium text-gray-700 dark:text-gray-200'}">
											{conv.teacher_name}
										</p>
										<span class="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0 whitespace-nowrap">
											{formatRelativeTime(conv.updated_at)}
										</span>
									</div>
									<p class="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
										À propos de <span class="font-medium text-gray-600 dark:text-gray-300">{conv.student_name}</span>
									</p>
								</div>
							</div>
						</button>
					</li>
				{/each}
			</ul>
		{/if}
	</div>

	<!-- Right panel: conversation view -->
	<div class="flex-1 flex flex-col min-w-0 {selectedConversation ? 'flex' : 'hidden md:flex'}">
		{#if selectedConversation}
			<button
				class="md:hidden flex items-center gap-1.5 px-4 py-2.5 text-blue-600 text-sm font-medium border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900 transition"
				on:click={() => (selectedConversation = null)}
			>
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
				</svg>
				Retour
			</button>
			<div class="flex-1 min-h-0">
				<ConversationView
					conversationId={selectedConversation.id}
					receiverId={selectedConversation.teacher_id}
					studentId={selectedConversation.student_id}
					displayName={selectedConversation.teacher_name}
					studentName={selectedConversation.student_name}
				/>
			</div>
		{:else}
			<div class="flex flex-col items-center justify-center flex-1 text-center px-8">
				<svg class="w-10 h-10 text-indigo-400 dark:text-indigo-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
				</svg>
				<p class="text-sm font-medium text-gray-800 dark:text-white mb-2">Sélectionnez une conversation</p>
				<p class="text-sm text-gray-600 dark:text-gray-400">pour lire et répondre aux messages.</p>
			</div>
		{/if}
	</div>
</div>
