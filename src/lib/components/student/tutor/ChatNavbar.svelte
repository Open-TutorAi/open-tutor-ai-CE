<script lang="ts">
    import { getContext } from 'svelte';
    import { toast } from 'svelte-sonner';
    import { onMount } from 'svelte';
    import { selectedLanguage } from '$lib/common/languageStore';

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

   const languages = [
    { code: 'fr', name: 'Français', flag: '🇫🇷' },
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'es', name: 'Español', flag: '🇪🇸' },
    { code: 'ar', name: 'العربية', flag: '🇸🇦' }  // Drapeau de l'Arabie Saoudite (le plus couramment utilisé pour l'arabe)
];
    function handleLanguageChange(event: Event) {
        const val = (event.target as HTMLSelectElement).value;
        selectedLanguage.set(val);
        localStorage.setItem('preferredLanguage', val);
        // Recharger la page pour appliquer la nouvelle langue
        window.location.reload();
    }

    onMount(() => {
        const saved = localStorage.getItem('preferredLanguage');
        if (saved) selectedLanguage.set(saved);
    });
</script>

<ShareChatModal bind:show={showShareChatModal} chatId={$chatId} />

<nav class="sticky top-0 z-30 w-full px-1.5 py-1.5 -mb-8 flex items-center drag-region">
    <div
        class="bg-linear-to-b via-50% from-white via-white to-transparent dark:from-gray-900 dark:via-gray-900 dark:to-transparent pointer-events-none absolute inset-0 -bottom-7 z-[-1]"
    ></div>

    <div class="flex max-w-full w-full mx-auto px-1 pt-0.5 bg-transparent">
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
                    <div class="m-auto self-center">
                        <MenuLines />
                    </div>
                </button>
            </div>

            <div
                class="flex-1 overflow-hidden max-w-full py-0.5
                {$showSidebar ? 'ml-1' : ''}"
            >
                {#if showModelSelector}
                    <ModelSelector bind:selectedModels showSetDefault={!shareEnabled} />
                {/if}
            </div>

            <!-- Language selector -->
            <div class="flex items-center mx-2">
                <select
                    bind:value={$selectedLanguage}
                    on:change={handleLanguageChange}
                    class="px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 
                           bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm
                           hover:border-gray-400 dark:hover:border-gray-500 transition-colors
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    {#each languages as lang}
                        <option value={lang.code}>
                            {lang.flag} {lang.name}
                        </option>
                    {/each}
                </select>
            </div>

            <!-- Bouton Toggle Avatar/Discuss - Design amélioré -->
            {#if shareEnabled || !!chat?.id}
                <div class="flex items-center justify-center mx-4">
                    <button
                        id="avatar-toggle-button"
                        class="relative h-10 w-56 rounded-full cursor-pointer overflow-hidden
                               transition-all duration-500 ease-out
                               shadow-lg hover:shadow-xl active:scale-95
                               focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2
                               dark:focus:ring-offset-gray-900"
                        on:click={() => toggleAvatar()}
                    >
                        <!-- Gradient Background -->
                        <div class="absolute inset-0 bg-gradient-to-r from-blue-500 to-blue-600"></div>
                        
                        <!-- Animated Background Highlight -->
                        <div
                            class="absolute inset-0 bg-gradient-to-r from-blue-400 to-blue-500
                                   transition-opacity duration-300 opacity-0 hover:opacity-100"
                        ></div>

                        <!-- Sliding Indicator -->
                        <div
                            class="absolute top-1 left-1 bottom-1 w-[calc(50%-4px)]
                                   bg-white/90 dark:bg-white/95 backdrop-blur-sm rounded-full
                                   shadow-md transition-all duration-500 ease-[cubic-bezier(0.68,-0.55,0.265,1.55)]"
                            style="transform: translateX({avatarActive ? '0' : 'calc(100% + 6px)'});"
                        ></div>

                        <!-- Avatar Option -->
                        <div class="absolute inset-0 flex items-center justify-start pl-4 pr-2">
                            <div class="flex items-center gap-2 z-10 w-1/2">
                                <div 
                                    class="w-5 h-5 transition-all duration-300"
                                    style="color: {avatarActive ? '#3B82F6' : 'white'}"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-full h-full">
                                        <path fill-rule="evenodd" d="M7.5 6a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM3.751 20.105a8.25 8.25 0 0116.498 0 .75.75 0 01-.437.695A18.683 18.683 0 0112 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 01-.437-.695z" clip-rule="evenodd" />
                                    </svg>
                                </div>
                                <span
                                    class="font-semibold text-sm tracking-wide transition-all duration-300 whitespace-nowrap"
                                    style="color: {avatarActive ? '#3B82F6' : 'white'}"
                                >
                                    {$i18n.t('AVATAR')}
                                </span>
                            </div>
                        </div>

                        <!-- Discuss Option -->
                        <div class="absolute inset-0 flex items-center justify-end pr-4 pl-2">
                            <div class="flex items-center gap-2 z-10 w-1/2 justify-end">
                                <span
                                    class="font-semibold text-sm tracking-wide transition-all duration-300 whitespace-nowrap"
                                    style="color: {avatarActive ? 'white' : '#2563EB'}"
                                >
                                    {$i18n.t('DISCUSS')}
                                </span>
                                <div 
                                    class="w-5 h-5 transition-all duration-300"
                                    style="color: {avatarActive ? 'white' : '#2563EB'}"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-full h-full">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                                    </svg>
                                </div>
                            </div>
                        </div>
                    </button>
                </div>
            {/if}
        </div>
    </div>
</nav>

<style>
    /* Améliorations supplémentaires pour le bouton */
    #avatar-toggle-button {
        transition: transform 0.2s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    }
    
    /* Support pour les écrans tactiles */
    @media (hover: hover) {
        #avatar-toggle-button:hover {
            transform: translateY(-1px);
        }
    }
    
    /* Animation de ripple au clic */
    #avatar-toggle-button:active {
        transform: scale(0.96);
    }
</style>