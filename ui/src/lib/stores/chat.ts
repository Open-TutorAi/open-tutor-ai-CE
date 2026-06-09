import { writable } from 'svelte/store';

export const chatId = writable('');
export const chatTitle = writable('');

export const channels = writable([]);
export const chats = writable([]);
export const pinnedChats = writable([]);
export const tags = writable([]);

export const showControls = writable(false);
export const showOverview = writable(false);
export const showArtifacts = writable(false);
export const showCallOverlay = writable(false);

export const temporaryChatEnabled = writable(false);
export const scrollPaginationEnabled = writable(false);
export const currentChatPage = writable(1);
