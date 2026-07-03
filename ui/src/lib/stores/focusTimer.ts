import { writable, derived, get } from 'svelte/store';

export type FocusPhase = 'idle' | 'work' | 'break';

export interface FocusState {
	phase: FocusPhase;
	remaining: number;
	totalSeconds: number;
	running: boolean;
	workMinutes: number;
	breakMinutes: number;
	sessionsCompleted: number;
}

export type FocusEvent =
	| { type: 'work_complete'; workMinutes: number }
	| { type: 'break_complete' }
	| null;

const INITIAL: FocusState = {
	phase: 'idle',
	remaining: 25 * 60,
	totalSeconds: 25 * 60,
	running: false,
	workMinutes: 25,
	breakMinutes: 5,
	sessionsCompleted: 0
};

export const focusTimer = writable<FocusState>({ ...INITIAL });
export const focusEvent = writable<FocusEvent>(null);
export const dashboardTab = writable<'performance' | 'productivity'>('performance');

let _interval: ReturnType<typeof setInterval> | null = null;

function _clearInterval() {
	if (_interval !== null) {
		clearInterval(_interval);
		_interval = null;
	}
}

function _tick() {
	const s = get(focusTimer);
	if (!s.running) {
		_clearInterval();
		return;
	}
	const next = s.remaining - 1;
	if (next <= 0) {
		_clearInterval();
		if (s.phase === 'work') {
			focusTimer.update((st) => ({ ...st, running: false, remaining: 0 }));
			focusEvent.set({ type: 'work_complete', workMinutes: s.workMinutes });
		} else {
			focusTimer.update((st) => ({ ...st, running: false, remaining: 0 }));
			focusEvent.set({ type: 'break_complete' });
		}
	} else {
		focusTimer.update((st) => ({ ...st, remaining: next }));
	}
}

function _startInterval() {
	_clearInterval();
	_interval = setInterval(_tick, 1000);
}

export function startFocusTimer() {
	const s = get(focusTimer);
	if (s.running || s.remaining <= 0) return;
	if (s.phase === 'idle') {
		focusTimer.update((st) => ({
			...st,
			phase: 'work',
			remaining: st.workMinutes * 60,
			totalSeconds: st.workMinutes * 60
		}));
	}
	focusTimer.update((st) => ({ ...st, running: true }));
	_startInterval();
}

export function pauseFocusTimer() {
	_clearInterval();
	focusTimer.update((s) => ({ ...s, running: false }));
}

export function resetFocusTimer() {
	_clearInterval();
	focusTimer.update((s) => ({
		...s,
		running: false,
		remaining: s.phase === 'break' ? s.breakMinutes * 60 : s.workMinutes * 60,
		totalSeconds: s.phase === 'break' ? s.breakMinutes * 60 : s.workMinutes * 60
	}));
}

export function beginBreak() {
	_clearInterval();
	const s = get(focusTimer);
	const total = s.breakMinutes * 60;
	focusTimer.update((st) => ({
		...st,
		phase: 'break',
		remaining: total,
		totalSeconds: total,
		running: true,
		sessionsCompleted: st.sessionsCompleted + 1
	}));
	_startInterval();
}

export function beginWork() {
	_clearInterval();
	const s = get(focusTimer);
	const total = s.workMinutes * 60;
	focusTimer.update((st) => ({
		...st,
		phase: 'work',
		remaining: total,
		totalSeconds: total,
		running: false
	}));
}

export function initFocusSettings(workMinutes: number, breakMinutes: number) {
	focusTimer.update((s) => {
		if (s.running) return s;
		const updated = { ...s, workMinutes, breakMinutes };
		if (s.phase === 'idle' || (s.phase === 'work' && s.remaining === s.totalSeconds)) {
			updated.remaining = workMinutes * 60;
			updated.totalSeconds = workMinutes * 60;
		}
		return updated;
	});
}

export function updateFocusSettingsStore(workMinutes: number, breakMinutes: number) {
	focusTimer.update((s) => {
		const updated = { ...s, workMinutes, breakMinutes };
		if (!s.running) {
			if (s.phase === 'work' || s.phase === 'idle') {
				updated.remaining = workMinutes * 60;
				updated.totalSeconds = workMinutes * 60;
			} else {
				updated.remaining = breakMinutes * 60;
				updated.totalSeconds = breakMinutes * 60;
			}
		}
		return updated;
	});
}

export const focusTimeDisplay = derived(focusTimer, ($s) => {
	const m = Math.floor(Math.max($s.remaining, 0) / 60);
	const sc = Math.max($s.remaining, 0) % 60;
	return `${String(m).padStart(2, '0')}:${String(sc).padStart(2, '0')}`;
});

export const isBreakActive = derived(
	focusTimer,
	($s) => $s.phase === 'break' && $s.running
);

export const isFocusVisible = derived(
	focusTimer,
	($s) => $s.phase !== 'idle' && ($s.running || $s.remaining < $s.totalSeconds)
);
