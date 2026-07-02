<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, getContext, onMount, onDestroy } from 'svelte';
	import { settings } from '$lib/stores';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let recording = false;
	export let className = ' p-2.5 w-full max-w-full';

	type Status = 'idle' | 'testing-mic' | 'starting' | 'listening' | 'error';
	let status: Status = 'idle';
	let errorMsg = '';
	let transcription = '';
	let interimText   = '';
	let durationSeconds = 0;
	let durationTimer: ReturnType<typeof setInterval> | null = null;
	let recognizer: any = null;
	let active = false;
	let hasFailed = false;    // ← prevents infinite restart loop after error
	let startTimeout: ReturnType<typeof setTimeout> | null = null;

	// Visualizer
	let micStream: MediaStream | null = null;
	let animFrameId: number | null = null;
	let visualizerData: number[] = new Array(30).fill(0.05);

	const fmt = (s: number) =>
		`${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

	const startTimer = () => {
		durationTimer = setInterval(() => durationSeconds++, 1000);
	};
	const stopTimer = () => {
		clearInterval(durationTimer!);
		durationSeconds = 0;
	};

	// ── Visualizer (real waveform) ─────────────────────────────────────────
	async function startVisualizer(stream: MediaStream) {
		try {
			const ctx = new AudioContext();
			const src = ctx.createMediaStreamSource(stream);
			const analyser = ctx.createAnalyser();
			analyser.fftSize = 64;
			src.connect(analyser);
			const buf = new Uint8Array(analyser.frequencyBinCount);
			const draw = () => {
				if (!active) return;
				animFrameId = requestAnimationFrame(draw);
				analyser.getByteTimeDomainData(buf);
				let sum = 0;
				for (let i = 0; i < buf.length; i++) {
					const v = (buf[i] - 128) / 128;
					sum += v * v;
				}
				const rms = Math.min(1, Math.max(0.04, Math.sqrt(sum / buf.length) * 12));
				visualizerData = [...visualizerData.slice(1), rms];
			};
			draw();
		} catch (_) {}
	}

	function stopVisualizer() {
		if (animFrameId) { cancelAnimationFrame(animFrameId); animFrameId = null; }
		if (micStream) { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
	}

	// ── Core recording ─────────────────────────────────────────────────────
	async function startRecognition() {
		if (active || hasFailed) return;   // ← guard: no restart after error

		active       = true;
		hasFailed    = false;
		transcription = '';
		interimText  = '';
		errorMsg     = '';
		status       = 'testing-mic';

		// 1) Check SpeechRecognition API
		const API =
			(window as any).SpeechRecognition ||
			(window as any).webkitSpeechRecognition;

		if (!API) {
			showError('Reconnaissance vocale non supportée.\nUtilisez Google Chrome (pas Firefox).');
			return;
		}

		// 2) Test mic access
		let testStream: MediaStream;
		try {
			testStream = await navigator.mediaDevices.getUserMedia({ audio: true });
		} catch (e: any) {
			if (e.name === 'NotAllowedError' || e.name === 'PermissionDeniedError') {
				showError(
					'🚫 Microphone refusé par Chrome.\n' +
					'→ Cliquez sur 🔒 dans la barre d\'adresse\n' +
					'→ Microphone → Autoriser\n' +
					'→ Rechargez (F5)'
				);
			} else if (e.name === 'NotFoundError') {
				showError('🎤 Aucun microphone trouvé.\nBranchez un micro.');
			} else {
				showError(`Erreur micro : ${e.name}\n${e.message}`);
			}
			return;
		}

		// Mic is accessible — keep the stream for visualizer
		micStream = testStream;
		startVisualizer(testStream);
		startTimer();
		status = 'starting';

		// 3) Timeout if SpeechRecognition doesn't start
		startTimeout = setTimeout(() => {
			if (status === 'starting') {
				showError(
					'⚠️ Reconnaissance vocale bloquée.\n' +
					'Chrome nécessite une connexion internet pour transcrire votre voix\n' +
					'(il envoie l\'audio aux serveurs Google).\n\n' +
					'Solutions :\n' +
					'• Vérifiez votre connexion internet\n' +
					'• Ou tapez votre message manuellement ↓'
				);
			}
		}, 5000);

		// 4) Start SpeechRecognition
		recognizer = new API();
		const lang =
			($settings as any)?.quizLanguage === 'en' ? 'en-US' :
			($settings as any)?.quizLanguage === 'fr' ? 'fr-FR' :
			navigator.language || 'fr-FR';

		recognizer.lang           = lang;
		recognizer.continuous     = true;
		recognizer.interimResults = true;

		recognizer.onstart = () => {
			clearTimeout(startTimeout!);
			status = 'listening';
		};

		recognizer.onresult = (event: any) => {
			let interim = '';
			for (let i = event.resultIndex; i < event.results.length; i++) {
				if (event.results[i].isFinal) {
					transcription += event.results[i][0].transcript + ' ';
				} else {
					interim += event.results[i][0].transcript;
				}
			}
			interimText = interim;
		};

		recognizer.onerror = (event: any) => {
			if (event.error === 'no-speech') return; // silence → auto-restart via onend
			clearTimeout(startTimeout!);

			const msgs: Record<string, string> = {
				'not-allowed':
					'🚫 Microphone refusé.\n→ 🔒 → Microphone → Autoriser → F5',
				'network':
					'⚠️ Erreur réseau Google.\n' +
					'Chrome envoie l\'audio aux serveurs Google pour transcrire.\n' +
					'Votre connexion internet bloque cela.\n\n' +
					'→ Vérifiez votre connexion\n' +
					'→ Ou tapez votre message à la place',
				'audio-capture':
					'🎤 Erreur capture audio.\nVérifiez que votre micro est branché.',
				'service-not-allowed':
					'🚫 Service vocal non autorisé.',
				'aborted':
					'Écoute annulée.',
			};
			showError(msgs[event.error] || `Erreur : ${event.error}`);
		};

		recognizer.onend = () => {
			// Auto-restart ONLY if still active and not failed
			if (active && !hasFailed && status === 'listening') {
				try { recognizer.start(); } catch (_) {}
			}
		};

		try {
			recognizer.start();
		} catch (e: any) {
			showError('Impossible de démarrer : ' + e.message);
		}
	}

	function showError(msg: string) {
		hasFailed = true;    // ← prevents reactive from restarting
		active    = false;
		status    = 'error';
		errorMsg  = msg;
		stopTimer();
		stopVisualizer();
		clearTimeout(startTimeout!);
		toast.error(msg.split('\n')[0]);
	}

	function stopAll() {
		active = false;
		clearTimeout(startTimeout!);
		stopTimer();
		stopVisualizer();
		if (recognizer) {
			recognizer.onend    = null;
			recognizer.onresult = null;
			recognizer.onerror  = null;
			try { recognizer.stop(); } catch (_) {}
			recognizer = null;
		}
	}

	function cancel() {
		stopAll();
		status    = 'idle';
		hasFailed = false;
		dispatch('cancel');
		recording = false;
	}

	function confirm() {
		const text = (transcription + interimText).trim();
		stopAll();
		status    = 'idle';
		hasFailed = false;
		// Dispatch BEFORE setting recording=false (prevents race condition)
		dispatch('confirm', { text });
		recording = false;
	}

	// ── Lifecycle ──────────────────────────────────────────────────────────
	// IMPORTANT: guard with hasFailed to avoid infinite restart on error
	$: if (mounted && recording && !active && !hasFailed) startRecognition();
	$: if (mounted && !recording && active) stopAll();

	let mounted = false;
	onMount(() => {
		mounted = true;
		if (recording) startRecognition();
	});
	onDestroy(() => stopAll());
</script>

<!-- ─── UI ──────────────────────────────────────────────────────────────────── -->
<div class="rounded-2xl flex items-center gap-2 {className}
	{status === 'error'
		? 'bg-red-50 dark:bg-red-950/40 border border-red-300 dark:border-red-700'
		: status === 'listening'
			? 'bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-300 dark:border-indigo-700'
			: 'bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700'}
	transition-all duration-300 px-3 py-2">

	<!-- ✕ Cancel -->
	<button type="button"
		class="shrink-0 p-1 rounded-full text-gray-400 hover:text-red-500
			hover:bg-red-50 dark:hover:bg-red-900/30 transition"
		on:click={cancel} title="Annuler">
		<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
			stroke-width="2.5" stroke="currentColor" class="size-4">
			<path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12"/>
		</svg>
	</button>

	<!-- Centre -->
	<div class="flex-1 flex flex-col items-center justify-center overflow-hidden min-w-0 gap-1">

		{#if status === 'error'}
			<div class="text-xs text-red-700 dark:text-red-300 text-center w-full
				whitespace-pre-line leading-snug font-medium">
				{errorMsg}
			</div>

		{:else if transcription || interimText}
			<p class="text-sm text-gray-800 dark:text-gray-100 text-center w-full truncate">
				{transcription}<span class="text-gray-400 italic">{interimText}</span>
			</p>

		{:else}
			<!-- Real waveform bars -->
			<div class="flex items-end justify-center gap-[2px] h-7 w-full">
				{#each visualizerData as level}
					<div class="rounded-full w-[3px] transition-none
						{status === 'listening' ? 'bg-indigo-500 dark:bg-indigo-400'
						: status === 'testing-mic' || status === 'starting'
							? 'bg-yellow-400 dark:bg-yellow-500'
							: 'bg-gray-300 dark:bg-gray-600'}"
						style="height:{Math.max(8, level * 100)}%"
					/>
				{/each}
			</div>

			<span class="text-xs font-medium
				{status === 'listening' ? 'text-indigo-500 dark:text-indigo-400'
				: status === 'testing-mic' || status === 'starting'
					? 'text-yellow-600 dark:text-yellow-400'
				: 'text-gray-400'}">
				{#if status === 'listening'}🎤 Parlez maintenant…
				{:else if status === 'testing-mic'}🔍 Vérification micro…
				{:else if status === 'starting'}⏳ Démarrage…
				{:else}—{/if}
			</span>
		{/if}
	</div>

	<!-- Timer -->
	<span class="shrink-0 text-xs font-mono
		{status === 'listening' ? 'text-indigo-500' : 'text-gray-400'}">
		{fmt(durationSeconds)}
	</span>

	<!-- ✓ Confirm -->
	<button type="button"
		class="shrink-0 p-1.5 rounded-full bg-indigo-500 hover:bg-indigo-600
			text-white transition shadow-sm"
		on:click={confirm} title="Envoyer">
		<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
			stroke-width="2.5" stroke="currentColor" class="size-4">
			<path stroke-linecap="round" stroke-linejoin="round"
				d="m4.5 12.75 6 6 9-13.5"/>
		</svg>
	</button>

</div>
