<script lang="ts">
	import { getContext } from 'svelte';

	import {
		TUTOR_NAME,
		chatId,
		mobile
	} from '$lib/stores';



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
</script>

<ShareChatModal bind:show={showShareChatModal} chatId={$chatId} />

<nav class="sticky top-0 z-30 w-full px-1.5 py-1.5 -mb-8 flex items-center drag-region">
	<div
		class=" bg-linear-to-b via-50% from-white via-white to-transparent dark:from-gray-900 dark:via-gray-900 dark:to-transparent pointer-events-none absolute inset-0 -bottom-7 z-[-1]"
	></div>

	<div class=" flex max-w-full w-full mx-auto px-1 pt-0.5 bg-transparent">
		<div class="flex items-center w-full max-w-full">
			<div class="flex-1 overflow-hidden max-w-full py-0.5">
				{#if showModelSelector}
					<ModelSelector bind:selectedModels showSetDefault={!shareEnabled} />
				{/if}

				
			</div>

			<div class="">
				{#if shareEnabled || !!chat?.id}
					<div
						class="flex-1 overflow-hidden max-w-full py-0.5"
						style="top: {$mobile ? '35px' : '40px'};"
					>
						<button
							id="avatar-toggle-button"
							class="relative h-10 sm:h-11 w-48 sm:w-56 rounded-full bg-blue-500 text-white cursor-pointer overflow-hidden
									transition-all duration-300 shadow-md hover:shadow-lg active:scale-[0.98]"
							on:click={() => toggleAvatar()}
						>
							<div class="relative flex items-center justify-between h-full">
								<!-- Sliding background -->
								<div
									class="absolute top-1/2 left-0 transform -translate-y-1/2 h-[85%] w-1/2 bg-white dark:bg-gray-100 rounded-full
											transition-all duration-300 ease-out"
									style="transform: translateX({avatarActive ? '4px' : 'calc(100% - 4px)'});"
								/>

								<!-- Avatar Label -->
								<div class="w-1/2 flex items-center justify-center z-10 px-2 gap-2">
									<div 
										class="w-[18px] h-[18px] transition-colors duration-300" 
										style="color: {avatarActive ? '#3B82F6' : 'rgba(255,255,255,0.95)'}"
									>
										<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-full h-full">
											<path fill-rule="evenodd" d="M7.5 6a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM3.751 20.105a8.25 8.25 0 0116.498 0 .75.75 0 01-.437.695A18.683 18.683 0 0112 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 01-.437-.695z" clip-rule="evenodd" />
										</svg>
									</div>
									<span
										class="font-bold text-[13px] tracking-wide transition-colors duration-300 whitespace-nowrap"
										style="color: {avatarActive ? '#3B82F6' : 'rgba(255,255,255,0.95)'}"
									>
										{$i18n.t('AVATAR')}
									</span>
								</div>

								<!-- Chat Label -->
								<div class="w-1/2 flex items-center justify-center z-10 px-2 gap-2">
									<div 
										class="w-[18px] h-[18px] transition-colors duration-300" 
										style="color: {avatarActive ? 'rgba(255,255,255,0.95)' : '#3B82F6'}"
									>
										<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-full h-full">
											<path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
										</svg>
									</div>
									<span
										class="font-bold text-[13px] tracking-wide transition-colors duration-300 whitespace-nowrap"
										style="color: {avatarActive ? 'rgba(255,255,255,0.95)' : '#3B82F6'}"
									>
										{$i18n.t('DISCUSS')}
									</span>
								</div>
							</div>
						</button>
					</div>
				{/if}
			</div>
		</div>
	</div>
</nav>