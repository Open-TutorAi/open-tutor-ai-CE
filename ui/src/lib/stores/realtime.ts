import { type Writable, writable } from 'svelte/store';
import type { Socket } from 'socket.io-client';

export const socket: Writable<null | Socket> = writable(null);
export const activeUserIds: Writable<null | string[]> = writable(null);
export const USAGE_POOL: Writable<null | string[]> = writable(null);

export const isLastActiveTab = writable(true);
export const playingNotificationSound = writable(false);
