import { type Writable, writable } from 'svelte/store';
import type { Banner } from '$lib/types';
import emojiShortCodes from '$lib/emoji-shortcodes.json';

export const mobile = writable(false);
export const theme = writable('system');

export const showSidebar = writable(false);
export const showSettings = writable(false);
export const showArchivedChats = writable(false);
export const showChangelog = writable(false);
export const isFullscreenAvatar = writable(false);

export const banners: Writable<Banner[]> = writable([]);

export const TTSWorker = writable(null);

export const shortCodesToEmojis = writable(
	Object.entries(emojiShortCodes).reduce((acc, [key, value]) => {
		if (typeof value === 'string') {
			acc[value] = key;
		} else {
			for (const v of value) {
				acc[v] = key;
			}
		}

		return acc;
	}, {})
);
