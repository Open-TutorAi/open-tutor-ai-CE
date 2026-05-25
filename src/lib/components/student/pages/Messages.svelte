<script lang="ts">
	import { getContext, tick } from 'svelte';
	import { goto } from '$app/navigation';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { user } from '$lib/stores';

	const i18n = getContext<Writable<i18nType>>('i18n');
	
	let channels = [
		{ id: 1, name: 'Général - Cours Java', subtitle: "N'oubliez pas le TP de demain.", unread: 3, members: 45, code: 'JAV-101' },
		{ id: 2, name: 'Projet Final - Web', subtitle: 'Le cahier des charges est en ligne.', unread: 0, members: 12, code: 'WEB-302' },
		{ id: 3, name: 'Algorithmique Avancée', subtitle: "Quelqu'un a compris le tri fusion ?", unread: 12, members: 30, code: 'ALG-201' },
		{ id: 4, name: 'Base de Données SQL', subtitle: 'La jointure externe est complexe.', unread: 0, members: 22, code: 'BDD-105' },
		{ id: 5, name: 'Intelligence Artificielle', subtitle: 'Nouveau papier sur les LLMs.', unread: 1, members: 15, code: 'IA-404' }
	];

	let activeChannelId = 4;
	let newMessage = '';
	let messagesContainer: HTMLElement;

	// Mock messages per channel
	let allMessages: Record<number, any[]> = {
		4: [
			{ id: 1, sender: 'Prof. Aicha Dakir', avatarColor: 'bg-green-500 text-white', role: 'ENSEIGNANT', time: '10:30', content: "Bonjour à tous, j'ai mis à jour le support de cours sur l'héritage en Java." },
			{ id: 2, sender: 'Abdelhadi Ait Boubker', avatarColor: 'bg-yellow-500 text-white', role: '', time: '10:45', content: "Merci Monsieur ! Est-ce que l'examen couvrira aussi les interfaces ?" },
			{ id: 3, sender: 'Abdelaziz Boukdous', avatarColor: 'bg-orange-500 text-white', role: '', time: '11:02', content: "J'ai une question sur le polymorphisme, je ne comprends pas bien la liaison dynamique." },
			{ id: 4, sender: 'Prof. Aicha Dakir', avatarColor: 'bg-green-500 text-white', role: 'ENSEIGNANT', time: '11:15', content: "Très bonne question Abdelhadi. Nous y reviendrons en détail lors de la séance de demain à 14h." },
			{ id: 5, sender: 'Hafid Qastali', avatarColor: 'bg-white border border-gray-200 text-gray-400 dark:border-gray-600 dark:text-gray-400', role: '', time: 'Lundi', content: "Je suis bloqué sur la requête avec le FULL OUTER JOIN, une idée ?", isSvg: true }
		],
		1: [
			{ id: 1, sender: 'Prof. Aicha Dakir', avatarColor: 'bg-green-500 text-white', role: 'ENSEIGNANT', time: '09:00', content: "Bienvenue dans le cours de Java. Le premier TP est disponible." }
		],
		2: [],
		3: [],
		5: []
	};

	$: activeChannel = channels.find(c => c.id === activeChannelId) || channels[0];
	$: currentMessages = allMessages[activeChannelId] || [];

	function selectChannel(id: number) {
		activeChannelId = id;
		// Mark as read
		channels = channels.map(c => c.id === id ? { ...c, unread: 0 } : c);
		scrollToBottom();
	}

	async function sendMessage() {
		if (!newMessage.trim()) return;
		
		const msg = {
			id: Date.now(),
			sender: $user?.name || 'Karim',
			avatarColor: 'bg-[#0ea5e9] text-white',
			role: 'ÉTUDIANT',
			time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
			content: newMessage.trim(),
			isSvg: false
		};

		if (!allMessages[activeChannelId]) {
			allMessages[activeChannelId] = [];
		}
		
		allMessages[activeChannelId] = [...allMessages[activeChannelId], msg];
		newMessage = '';

		scrollToBottom();
	}

	async function scrollToBottom() {
		await tick();
		if (messagesContainer) {
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}
</script>

<div class="h-[calc(100vh-8rem)] flex gap-4 md:gap-6 font-sans text-slate-800 dark:text-gray-100 overflow-hidden">
	
	<!-- LEFT SIDEBAR: Channels Card -->
	<div class="w-[300px] lg:w-[340px] bg-white dark:bg-[#27272a] rounded-[2rem] flex flex-col hidden md:flex shrink-0 shadow-sm border border-gray-100 dark:border-gray-800 overflow-hidden">
		<!-- Header -->
		<div class="p-6 pb-4 flex justify-between items-center">
			<h2 class="text-xl font-bold text-slate-800 dark:text-white tracking-tight">Discussions</h2>
			<button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
			</button>
		</div>

		<!-- Search -->
		<div class="px-6 pb-4">
			<div class="relative">
				<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
					<svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
				</div>
				<input type="text" placeholder="Rechercher un canal..." class="block w-full pl-10 pr-3 py-2.5 border border-gray-200 dark:border-[#3f3f46] rounded-xl leading-5 bg-gray-50 dark:bg-[#3f3f46] text-slate-800 dark:text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-[#0ea5e9] focus:border-[#0ea5e9] sm:text-sm transition duration-150 ease-in-out shadow-sm" />
			</div>
		</div>

		<!-- Channels List -->
		<div class="flex-1 overflow-y-auto px-4">
			<div class="py-2">
				<h3 class="px-2 text-[11px] font-bold text-gray-500 dark:text-gray-400 tracking-wider uppercase mb-3">Canaux de cours</h3>
				<ul class="space-y-1.5">
					{#each channels as channel}
						<li>
							<button on:click={() => selectChannel(channel.id)} class="w-full flex items-start text-left px-3 py-3 rounded-2xl transition-colors duration-150 {channel.id === activeChannelId ? 'bg-gray-100 dark:bg-[#3f3f46]' : 'hover:bg-gray-50 dark:hover:bg-[#3f3f46]/50'}">
								<div class="flex-shrink-0 mt-0.5">
									<div class="w-8 h-8 rounded-xl flex items-center justify-center {channel.id === activeChannelId ? 'bg-white dark:bg-gray-500 text-gray-800 dark:text-white shadow-sm' : 'bg-gray-100 dark:bg-[#3f3f46] text-gray-500 dark:text-gray-400'} font-medium text-sm">
										#
									</div>
								</div>
								<div class="ml-3 flex-1 overflow-hidden">
									<div class="flex items-center justify-between mb-0.5">
										<span class="text-sm font-bold truncate {channel.id === activeChannelId ? 'text-slate-800 dark:text-white' : 'text-slate-600 dark:text-gray-300'}">{channel.name}</span>
										{#if channel.unread > 0}
											<span class="inline-flex items-center justify-center px-1.5 py-0.5 ml-2 text-[10px] font-bold leading-none text-white bg-red-500 rounded-full">{channel.unread}</span>
										{/if}
									</div>
									<p class="text-[12px] text-gray-500 dark:text-gray-400 truncate">{channel.subtitle}</p>
								</div>
							</button>
						</li>
					{/each}
				</ul>
			</div>
		</div>

		<!-- Preferences -->
		<div class="p-4 mt-auto">
			<button on:click={() => goto('/student/settings')} class="w-full flex items-center px-4 py-3 rounded-2xl bg-gray-50 dark:bg-[#3f3f46] hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors border border-gray-100 dark:border-gray-700 shadow-sm">
				<div class="bg-[#0ea5e9] p-2 rounded-xl mr-3 text-white shadow-sm">
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
				</div>
				<div class="text-left">
					<div class="text-sm font-bold text-slate-700 dark:text-gray-100">Préférences</div>
					<div class="text-[11px] text-gray-500 dark:text-gray-400">Gérer les notifications</div>
				</div>
			</button>
		</div>
	</div>

	<!-- MIDDLE: Chat Area Card -->
	<div class="flex-1 bg-white dark:bg-[#27272a] rounded-[2rem] flex flex-col min-w-0 shadow-sm border border-gray-100 dark:border-gray-800 overflow-hidden relative">
		
		<!-- Chat Header -->
		<div class="px-8 py-6 border-b border-gray-100 dark:border-[#3f3f46] flex items-center justify-between">
			<div class="flex items-center">
				<span class="text-gray-400 dark:text-gray-500 text-2xl font-light mr-3">#</span>
				<div>
					<h2 class="text-xl font-bold text-slate-800 dark:text-white">{activeChannel.name}.</h2>
					<p class="text-[12px] text-gray-500 dark:text-gray-400 font-medium mt-0.5">{activeChannel.members} membres actifs - {activeChannel.code}</p>
				</div>
			</div>
			<div class="flex items-center space-x-3">
				<button class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
				</button>
				<button class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
				</button>
				<button class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
				</button>
			</div>
		</div>

		<!-- Messages Scroll Area -->
		<div bind:this={messagesContainer} class="flex-1 overflow-y-auto p-8 space-y-8 scroll-smooth">
			
			<!-- Conversation Start Badge -->
			<div class="flex justify-center mb-10 mt-2 relative">
				<div class="bg-[#9333EA] text-white text-[11px] font-bold tracking-widest px-12 py-8 rounded-[1.5rem] w-full text-center shadow-sm uppercase">
					DÉBUT DE LA CONVERSATION DANS #{activeChannel.name}
				</div>
			</div>

			<!-- Messages List -->
			{#if currentMessages.length === 0}
				<div class="text-center text-gray-400 dark:text-gray-500 py-10">
					Aucun message pour le moment.
				</div>
			{/if}

			{#each currentMessages as msg}
				<div class="flex items-start max-w-3xl">
					<div class="flex-shrink-0 mr-4">
						<div class="w-10 h-10 rounded-full {msg.avatarColor} flex items-center justify-center font-bold text-lg shadow-sm overflow-hidden">
							{#if msg.isSvg}
								<svg class="w-6 h-6 text-gray-300" fill="currentColor" viewBox="0 0 24 24"><path d="M24 20.993V24H0v-2.996A14.977 14.977 0 0112.004 15c4.904 0 9.26 2.354 11.996 5.993zM16.002 8.999a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
							{:else}
								{msg.sender.charAt(0)}
							{/if}
						</div>
					</div>
					<div class="flex-1 min-w-0">
						<div class="flex items-baseline mb-2">
							<span class="font-bold text-slate-800 dark:text-white mr-2 text-[15px]">{msg.sender}</span>
							{#if msg.role}
								<span class="bg-[#0084FF] text-white text-[9px] font-bold px-2 py-0.5 rounded-full mr-2 tracking-wide">{msg.role}</span>
							{/if}
							<span class="text-xs text-gray-400 font-medium">{msg.time}</span>
						</div>
						<div class="bg-gray-100 dark:bg-[#3f3f46] rounded-2xl rounded-tl-sm px-5 py-4 text-[14px] text-slate-700 dark:text-gray-200 shadow-sm inline-block max-w-full">
							{msg.content}
						</div>
					</div>
				</div>
			{/each}
		</div>

		<!-- Input Area -->
		<div class="p-6 pt-2">
			<div class="bg-white dark:bg-[#27272a] border border-[#0ea5e9] rounded-[1.5rem] shadow-sm overflow-hidden focus-within:ring-2 focus-within:ring-[#0ea5e9]/50 transition-all">
				<textarea 
					bind:value={newMessage}
					on:keydown={handleKeydown}
					rows="1" 
					class="w-full bg-transparent border-0 resize-none px-5 py-4 focus:ring-0 text-[15px] text-slate-800 dark:text-gray-100 placeholder-gray-400" 
					placeholder="Envoyer un message dans #{activeChannel.name}."></textarea>
				
				<div class="flex items-center justify-between px-4 py-3 bg-transparent border-t border-gray-100 dark:border-transparent">
					<div class="flex items-center space-x-2">
						<button class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>
						</button>
						<button class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
						</button>
						<div class="w-px h-5 bg-gray-200 dark:bg-[#3f3f46] mx-1"></div>
						<button class="p-1.5 text-gray-500 font-serif font-bold hover:text-gray-700 dark:hover:text-gray-200 transition-colors">B</button>
						<button class="p-1.5 text-gray-500 font-serif italic hover:text-gray-700 dark:hover:text-gray-200 transition-colors">I</button>
					</div>
					<div class="flex items-center space-x-4">
						<span class="text-[12px] text-gray-400 font-medium hidden sm:inline-block">Entrée pour envoyer</span>
						<button on:click={sendMessage} class="bg-[#0ea5e9] hover:bg-blue-500 text-white px-6 py-2.5 rounded-[1rem] text-[14px] font-bold shadow-sm flex items-center transition-colors">
							Envoyer
							<svg class="w-4 h-4 ml-1.5 -mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path></svg>
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
