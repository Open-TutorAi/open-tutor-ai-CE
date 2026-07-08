<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { sendVideoFrame } from '$lib/apis/engagement';
	import { videoEngagementScore } from '$lib/stores';

	// Lightweight webcam engagement capture with a small self-preview (not the
	// old full monitor widget). When `active` is true it opens the camera, shows
	// a compact picture-in-picture preview, scores frames on an interval, and
	// publishes the live video engagement score so chat/voice sends attach it.
	export let sessionId: string | null = null;
	export let active = false;
	export let captureMs = 2000;
	export let cameraStatus = 'off'; // bindable, for an optional indicator

	let videoEl: HTMLVideoElement | null = null;
	let canvasEl: HTMLCanvasElement | null = null;
	let stream: MediaStream | null = null;
	let imageCapture: any = null; // ImageCapture grabs frames straight from the track
	let cameraOn = false;
	let captureInterval: number | null = null;
	let mounted = false;

	let liveVideo: number | null = null; // smoothed live webcam score
	// Keep the last good score through brief no-face frames (e.g. while the user
	// turns their head talking during a voice message) so the score isn't wiped.
	let noFaceStreak = 0;
	const NO_FACE_GRACE = 3; // ~6s at the default 2s capture interval

	const smooth = (prev: number | null, v: number) => (prev === null ? v : prev * 0.7 + v * 0.3);

	const pct = (x: number | null) => (x == null ? '—' : `${Math.round(x * 100)}%`);
	const tone = (x: number | null) =>
		x == null ? 'bg-gray-400' : x < 0.4 ? 'bg-red-500' : x < 0.75 ? 'bg-amber-500' : 'bg-green-500';

	async function startCamera() {
		if (cameraOn) return;
		// getUserMedia only exists in a secure context (HTTPS or localhost). Over a
		// plain-http LAN IP the browser hides it entirely → camera can't start.
		if (!navigator.mediaDevices?.getUserMedia) {
			cameraStatus = 'needs https / localhost';
			toast.error('Camera needs HTTPS or localhost (open the app at http://localhost).');
			return;
		}
		try {
			stream = await navigator.mediaDevices.getUserMedia({
				video: { width: 320, height: 240 },
				audio: false
			});
			// Ensure the (conditionally shown) preview has rendered so videoEl is
			// bound and visible before attaching the stream — a display:none video
			// won't decode frames, producing black captures with no face.
			cameraOn = true;
			await tick();
			if (videoEl) {
				videoEl.srcObject = stream;
				await videoEl.play();
			}
			// Prefer grabbing frames straight from the camera track. On Linux +
			// Chromium, drawImage(video) often reads a black frame (hardware video
			// overlay), while ImageCapture.grabFrame() returns the real pixels.
			const track = stream.getVideoTracks()[0];
			imageCapture = null;
			if (track && 'ImageCapture' in window) {
				try {
					imageCapture = new (window as any).ImageCapture(track);
				} catch {
					imageCapture = null;
				}
			}
			cameraStatus = 'starting';
			// Guard against overlapping captures: if a capture (frame grab +
			// network roundtrip) takes longer than captureMs, skip the tick
			// instead of stacking concurrent requests.
			let inFlight = false;
			const tickCapture = () => {
				if (inFlight) return;
				inFlight = true;
				Promise.resolve(capture()).finally(() => {
					inFlight = false;
				});
			};
			captureInterval = window.setInterval(tickCapture, captureMs);
			// Grab a first frame quickly so a video score is available right away.
			window.setTimeout(tickCapture, 700);
		} catch (e) {
			cameraStatus = (e as Error)?.message || 'error';
			toast.error(`Camera error: ${cameraStatus}`);
		}
	}

	function stopCamera() {
		if (captureInterval) {
			clearInterval(captureInterval);
			captureInterval = null;
		}
		if (stream) {
			stream.getTracks().forEach((t) => t.stop());
			stream = null;
		}
		imageCapture = null;
		if (videoEl) {
			try {
				videoEl.pause();
				videoEl.srcObject = null;
			} catch (e) {
				// ignore teardown errors
			}
		}
		cameraOn = false;
		cameraStatus = 'off';
		liveVideo = null;
		noFaceStreak = 0;
		videoEngagementScore.set(null);
	}

	async function capture() {
		if (!cameraOn || !canvasEl) return;
		const ctx = canvasEl.getContext('2d');
		if (!ctx) return;

		let drew = false;
		// Preferred path: grab the frame straight from the camera track. This
		// returns real pixels even when drawImage(video) would read black.
		if (imageCapture) {
			try {
				const bitmap = await imageCapture.grabFrame();
				canvasEl.width = bitmap.width;
				canvasEl.height = bitmap.height;
				ctx.drawImage(bitmap, 0, 0);
				bitmap.close?.();
				drew = true;
			} catch {
				drew = false; // fall back to the video element below
			}
		}
		// Fallback: draw from the <video> element at native resolution.
		if (!drew) {
			if (!videoEl || videoEl.readyState < 2 || !videoEl.videoWidth || !videoEl.videoHeight) {
				cameraStatus = 'starting';
				return;
			}
			canvasEl.width = videoEl.videoWidth;
			canvasEl.height = videoEl.videoHeight;
			ctx.drawImage(videoEl, 0, 0, videoEl.videoWidth, videoEl.videoHeight);
		}

		const base64 = canvasEl.toDataURL('image/jpeg', 0.8).split(',')[1];
		try {
			const data = await sendVideoFrame(localStorage.token, base64, sessionId);
			console.debug(
				'[engagement] video frame sent',
				canvasEl.width + 'x' + canvasEl.height,
				imageCapture ? '(grabFrame)' : '(drawImage)',
				'-> score',
				data?.video_score
			);
			if (data && data.video_score != null) {
				noFaceStreak = 0;
				liveVideo = smooth(liveVideo, data.video_score);
				// Publish so the message input saves it with the next send.
				videoEngagementScore.set(Number(liveVideo.toFixed(3)));
				cameraStatus = 'tracking';
			} else {
				// No face in this frame — keep the last good score for a few frames
				// (the user may just be moving while talking). Only clear once the
				// face has been missing for the whole grace window.
				noFaceStreak += 1;
				if (noFaceStreak >= NO_FACE_GRACE) {
					liveVideo = null;
					videoEngagementScore.set(null);
				}
				cameraStatus = 'no face';
			}
		} catch (e) {
			// Transient network/error — keep the last good score rather than
			// dropping it; just surface the status.
			cameraStatus = 'error';
		}
	}

	// React to the `active` toggle once mounted.
	$: if (mounted) {
		if (active && !cameraOn) startCamera();
		else if (!active && cameraOn) stopCamera();
	}

	onMount(() => {
		mounted = true;
		if (active) startCamera();
	});

	onDestroy(() => stopCamera());
</script>

<!-- Offscreen scratch canvas used only to grab frames. -->
<canvas bind:this={canvasEl} width="320" height="240" class="hidden"></canvas>

<!-- Preview container is always in the DOM (so videoEl is bound before the
	stream is attached); only its visibility is toggled. The video must be
	rendered, not display:none, for the browser to decode frames the canvas reads. -->
<div
	class="fixed bottom-4 right-4 z-[9999] w-44 rounded-xl overflow-hidden bg-gray-900 shadow-2xl border border-gray-700 {active
		? ''
		: 'hidden'}"
>
	<!-- svelte-ignore a11y-media-has-caption -->
	<video bind:this={videoEl} muted playsinline class="w-full aspect-video object-cover"></video>

	<!-- Status + live score overlay. -->
	<div
		class="absolute bottom-0 inset-x-0 flex items-center justify-between px-2 py-1 bg-black/50 text-[11px] text-white"
	>
		<span class="flex items-center gap-1">
			<span class="size-1.5 rounded-full {tone(liveVideo)}"></span>
			{cameraStatus}
		</span>
		<span class="font-semibold">{pct(liveVideo)}</span>
	</div>
</div>
