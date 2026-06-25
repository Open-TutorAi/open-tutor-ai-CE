<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { monitorLocked } from '$lib/stores';
	import { reportPresence } from '$lib/apis/classrooms';

	const i18n: any = getContext('i18n');

	// True only while *this* component drove the browser into fullscreen, so we never
	// exit a fullscreen the student opened themselves.
	let enteredFullscreen = false;
	// Last presence we reported, to coalesce the blur + visibilitychange double-fire.
	let lastAway: boolean | null = null;

	const token = (): string | undefined =>
		typeof localStorage !== 'undefined' ? localStorage.token : undefined;

	const enterFullscreen = async () => {
		try {
			if (!document.fullscreenElement) {
				await document.documentElement.requestFullscreen();
				enteredFullscreen = true;
			}
		} catch (_) {
			// Fullscreen needs a recent user gesture; if denied, the overlay still covers
			// the page and the gesture fallback retries on the next interaction.
		}
	};

	const exitFullscreen = async () => {
		try {
			if (enteredFullscreen && document.fullscreenElement) {
				await document.exitFullscreen();
			}
		} catch (_) {
			// ignore — leaving fullscreen is best-effort
		}
		enteredFullscreen = false;
	};

	const reportAway = (away: boolean) => {
		if (away === lastAway) return; // dedupe blur/visibility overlap
		lastAway = away;
		const t = token();
		if (t) reportPresence(t, away).catch(() => {});
	};

	// If auto-fullscreen was blocked (no gesture), promote on the student's first touch.
	const onGesture = () => {
		if ($monitorLocked && !document.fullscreenElement) enterFullscreen();
	};
	const onVisibility = () => {
		if ($monitorLocked) reportAway(document.hidden);
	};
	const onBlur = () => {
		if ($monitorLocked) reportAway(true);
	};
	const onFocus = () => {
		if ($monitorLocked) reportAway(false);
	};

	onMount(() => {
		document.addEventListener('visibilitychange', onVisibility);
		window.addEventListener('blur', onBlur);
		window.addEventListener('focus', onFocus);
		document.addEventListener('pointerdown', onGesture);
		document.addEventListener('keydown', onGesture);

		let wasLocked = false;
		const unsub = monitorLocked.subscribe((locked) => {
			if (locked && !wasLocked) {
				wasLocked = true;
				lastAway = false; // assume present at the moment of locking
				enterFullscreen();
				if (document.hidden) reportAway(true); // already on another tab when locked
			} else if (!locked && wasLocked) {
				wasLocked = false;
				lastAway = null;
				exitFullscreen();
			}
		});

		return () => {
			document.removeEventListener('visibilitychange', onVisibility);
			window.removeEventListener('blur', onBlur);
			window.removeEventListener('focus', onFocus);
			document.removeEventListener('pointerdown', onGesture);
			document.removeEventListener('keydown', onGesture);
			unsub();
		};
	});
</script>

{#if $monitorLocked}
	<!-- E6: teacher-initiated screen lock. Full-screen, blocks interaction. -->
	<div
		class="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-gray-900/95 text-white text-center px-6 select-none"
		role="alertdialog"
		aria-modal="true"
	>
		<svg class="h-16 w-16 mb-6 text-white/80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="1.5"
				d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
			/>
		</svg>
		<h1 class="text-2xl font-semibold mb-2">{$i18n.t('Screen paused by your teacher')}</h1>
		<p class="text-white/70 max-w-md">
			{$i18n.t('Please look up — your screen will return when your teacher unlocks it.')}
		</p>
	</div>
{/if}
