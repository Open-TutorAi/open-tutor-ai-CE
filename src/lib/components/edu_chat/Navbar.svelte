<script lang="ts">
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';

	import {
		TUTOR_NAME,
		chatId,
		mobile,
		settings,
		showArchivedChats,
		showControls,
		showSidebar,
		temporaryChatEnabled,
		user
	} from '$lib/stores';

	import { slide } from 'svelte/transition';
	import { page } from '$app/stores';

	import ShareChatModal from '../chat/ShareChatModal.svelte';
	import ModelSelector from '../chat/ModelSelector.svelte';



	const i18n = getContext('i18n');

	export let initNewChat: Function;
	export let title: string = $TUTOR_NAME;
	export let shareEnabled: boolean = false;
	export let avatarActive: boolean = false;
	export let toggleAvatar: Function;

	export let chat;
	export let selectedModels;
	export let showModelSelector = true;

	let showShareChatModal = false;
	let showDownloadChatModal = false;
</script>

<ShareChatModal bind:show={showShareChatModal} chatId={$chatId} />

<nav class="sticky top-0  w-full px-1.5 py-1.5 -mb-8 flex items-center drag-region">

	<div class=" flex max-w-full w-full mx-auto px-1 pt-0.5 bg-transparent">
		<div class="flex items-center w-full max-w-full">
			<div
				class="flex-1 overflow-hidden max-w-full py-0.5
			{$showSidebar ? 'ml-1' : ''}
			"
			>
				{#if showModelSelector}
					<ModelSelector bind:selectedModels showSetDefault={!shareEnabled} />
				{/if}
			</div>

			<!-- Center section with avatar toggle - Responsive for all devices -->
			{#if shareEnabled || !!chat?.id}
			<div class="absolute left-1/2 transform -translate-x-1/2 flex justify-center items-center  mt-10" 
				style="top: {$mobile ? '35px' : '40px'};">
				<button
				id="avatar-toggle-button"
				class="relative h-8 sm:h-10 w-36 sm:w-44 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white cursor-pointer overflow-hidden 
						transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-105 border border-blue-300/30 pr-2"
				on:click={() => {
					toggleAvatar();
				}}
				>
				<!-- Container for the toggle with improved design -->
				<div class="relative flex items-center h-full">
					<!-- Sliding white background with smoother animation -->
					<div 
					class="absolute h-5/6 w-1/2 bg-white dark:bg-gray-100 rounded-full 
							transition-transform duration-300 ease-in-out shadow-md"
					style="transform: translateX({avatarActive ? '0%' : '100%'}); left: 4px;"
					></div>
					
					<!-- Left side label - Avatar with icon -->
					<div class="w-1/2 h-full flex items-center justify-center z-10 space-x-1 px-1">

					<span class="font-medium text-xs sm:text-sm transition-colors duration-300"
							style="color: {avatarActive ? '#3B82F6' : 'white'}">
						{$i18n.t('Avatar')}
					</span>
					</div>
					
					<!-- Right side label - Chat with icon -->
					<div class="w-1/2 h-full flex items-center justify-center z-10 space-x-1 px-1">

					<span class="font-medium text-xs sm:text-sm transition-colors duration-300 pl-2"
							style="color: {avatarActive ? 'white' : '#3B82F6'}">
						{$i18n.t('Discuss')}
					</span>
					</div>
				</div>
				
				<!-- Subtle pulse animation on hover -->
				<div class="absolute inset-0 bg-white opacity-0 rounded-full hover:opacity-10 transition-opacity duration-300"></div>
				</button>
			</div>
			{/if}
		</div>
	</div>
</nav>
