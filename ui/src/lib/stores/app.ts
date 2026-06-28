import { writable } from 'svelte/store';

// Electron App
export const isApp = writable(false);
export const appInfo = writable(null);
export const appData = writable(null);
