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

	import ShareChatModal from '../../chat/ShareChatModal.svelte';
	import ModelSelector from '../../chat/ModelSelector.svelte';
	import Tooltip from '../../common/Tooltip.svelte';
	import Menu from '$lib/components/layout/Navbar/Menu.svelte';
	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import MenuLines from '../../icons/MenuLines.svelte';
	import AdjustmentsHorizontal from '../../icons/AdjustmentsHorizontal.svelte';
	import ChatBubbleOval from '../../icons/ChatBubbleOval.svelte';
	import User from '../../icons/User.svelte';

	import PencilSquare from '../../icons/PencilSquare.svelte';

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

<nav class="sticky top-0 z-30 w-full px-1.5 py-1.5 -mb-8 flex items-center drag-region">
	<div
		class=" bg-linear-to-b via-50% from-white via-white to-transparent dark:from-gray-900 dark:via-gray-900 dark:to-transparent pointer-events-none absolute inset-0 -bottom-7 z-[-1]"
	></div>

	<div class=" flex max-w-full w-full mx-auto px-1 pt-0.5 bg-transparent">
		<div class="flex items-center w-full max-w-full">
			<div
				class="{$showSidebar
					? 'md:hidden'
					: ''} mr-1 self-start flex flex-none items-center text-gray-600 dark:text-gray-400"
			>
				<button
					id="sidebar-toggle-button"
					class="cursor-pointer px-2 py-2 flex rounded-xl hover:bg-gray-50 dark:hover:bg-gray-850 transition"
					on:click={() => {
						showSidebar.set(!$showSidebar);
					}}
					aria-label="Toggle Sidebar"
				>
					<div class=" m-auto self-center">
						<MenuLines />
					</div>
				</button>
			</div>

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
				<div
					class="absolute left-1/2 transform -translate-x-1/2 z-20"
					style="top: {$mobile ? '35px' : '40px'};"
				>
					<button
						id="avatar-toggle-button"
						class="relative h-10 sm:h-12 w-40 sm:w-48 rounded-full bg-blue-500 text-white cursor-pointer overflow-hidden
           transition-all duration-300 shadow-md hover:shadow-lg"
						on:click={() => toggleAvatar()}
					>
						<div class="relative flex items-center justify-between h-full px-1">
							<!-- Sliding background (50% width of the button) -->
							<div
								class="absolute top-1/2 left-0 transform -translate-y-1/2 h-[80%] w-1/2 bg-white dark:bg-gray-200 rounded-full
               transition-transform duration-300 ease-in-out"
								style="transform: translateX({avatarActive ? '0%' : '100%'});"
							></div>

							<!-- Avatar Label -->
							<div class="w-1/2 flex items-center justify-center z-10">
								<span
									class="font-semibold uppercase text-[11px] sm:text-sm tracking-wide transition-colors duration-300 whitespace-nowrap"
									style="color: {avatarActive ? '#3B82F6' : 'white'}"
								>
									{$i18n.t('Avatar')}
								</span>
							</div>

							<!-- Chat Label -->
							<div class="w-1/2 flex items-center justify-center z-10">
								<span
									class="font-semibold uppercase text-[11px] sm:text-sm tracking-wide transition-colors duration-300 whitespace-nowrap"
									style="color: {avatarActive ? 'white' : '#3B82F6'}"
								>
									{$i18n.t('Discussion')}
								</span>
							</div>
						</div>
					</button>
				</div>
			{/if}
		</div>
	</div>
</nav>
