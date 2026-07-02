<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { TUTOR_API_BASE_URL } from '$lib/constants';
	import { settings } from '$lib/stores';
	const dispatch = createEventDispatcher();
	const i18n: any = getContext('i18n');

	let currentView = 'main';
	let videoSearchQuery = '';
	let videoResults: string[] = [];
	let videoIndex = 0;
	let videoLoading = false;
	let videoError = '';

	$: currentVideoId = videoResults[videoIndex] ?? null;
	let videoActivated = false; // true when user clicks play — only THEN load the iframe
	$: if (videoIndex >= 0) videoActivated = false; // reset on navigation

	// Helper to change view and notify parent about video mode state
	function setView(view: string) {
		currentView = view;
		const isVideoMode = view === 'video-search' || view === 'video-player';
		dispatch('videoMode', isVideoMode);
	}

	const EXPLAIN_OVERRIDE = '⚠️ EXPLANATION REQUEST — Do NOT generate quiz questions for this message. Switch to TUTOR/EXPLANATION mode and respond with a clear educational explanation as requested below:\n\n';

	$: understandActions = [
		{
			label: $i18n.t('Analogy'),
			icon: '🔁',
			prompt: EXPLAIN_OVERRIDE + $i18n.t('Explain this concept using a creative analogy from everyday life to make the abstract ideas more concrete and relatable.')
		},
		{
			label: $i18n.t('Example'),
			icon: '💡',
			prompt: EXPLAIN_OVERRIDE + $i18n.t('Give me a concrete, real-world application of this concept. Show me how it works in a practical scenario I might actually encounter.')
		},
		{
			label: $i18n.t('Visual'),
			icon: '📊',
			prompt: EXPLAIN_OVERRIDE + $i18n.t('Organize the key components of this topic into a clear Markdown table or a structured list to help me visualize the relationships between ideas.')
		}
	];

	$: quizActions = [
		{
			label: $i18n.t('Open Ended'),
			icon: '💬',
			prompt: $i18n.t('Ask me one challenging open-ended question that requires a detailed explanation to test my memory and comprehension of what we just discussed.')
		},
		{
			label: $i18n.t('Multiple Choice'),
			icon: '🧩',
			prompt: $i18n.t('Provide 3 Multiple Choice Questions with distinct options to test if I can identify the correct logic among common misconceptions.')
		},
		{
			label: $i18n.t('Concept Link'),
			icon: '🔗',
			prompt: $i18n.t('Pick two distinct concepts we just discussed and ask me to explain the relationship or connection between them to test my ability to synthesize the information.')
		}
	];

	$: difficultyLevels = [
		{
			label: $i18n.t('Beginner'),
			icon: '🟢',
			color: 'rgba(34, 197, 94, 0.15)',
			border: 'rgba(34, 197, 94, 0.3)',
			text: 'var(--color-green-600, #16a34a)',
			darkText: '#4ade80',
			prompt: $i18n.t('Explain the current topic using very simple language and basic analogies, as if I am 5 years old.')
		},
		{
			label: $i18n.t('Intermediate'),
			icon: '🟡',
			color: 'rgba(234, 179, 8, 0.15)',
			border: 'rgba(234, 179, 8, 0.3)',
			text: 'var(--color-yellow-600, #ca8a04)',
			darkText: '#facc15',
			prompt: $i18n.t('Explain this concept with more depth, using standard technical terms where appropriate but ensuring the core logic remains clear and accessible.')
		},
		{
			label: $i18n.t('Advanced'),
			icon: '🔴',
			color: 'rgba(239, 68, 68, 0.15)',
			border: 'rgba(239, 68, 68, 0.3)',
			text: 'var(--color-red-600, #dc2626)',
			darkText: '#f87171',
			prompt: $i18n.t('Provide a deep-dive, technical explanation of the current topic, including nuances and complex details.')
		}
	];

	function sendAction(prompt: string, autoSend: boolean = false) {
		dispatch('submit', { text: prompt, autoSend });
		setView('main');
	}

	async function launchVideoSearch() {
		if (!videoSearchQuery.trim()) return;
		videoLoading = true;
		videoError = '';
		videoResults = [];
		videoIndex = 0;
		setView('video-player');

		try {
			const res = await fetch(
				`${TUTOR_API_BASE_URL}/youtube/search?q=${encodeURIComponent(videoSearchQuery.trim())}`,
				{ headers: { Authorization: `Bearer ${localStorage.token}` } }
			);
			const data = await res.json();
			if (data.videos && data.videos.length > 0) {
				videoResults = data.videos;
			} else {
				videoError = $i18n.t('Aucune vidéo trouvée. Essayez un autre sujet.');
			}
		} catch (e) {
			videoError = $i18n.t('Erreur de connexion. Vérifiez votre réseau.');
		} finally {
			videoLoading = false;
		}
	}

	function closeVideoPlayer() {
		videoResults = [];
		videoSearchQuery = '';
		videoError = '';
		videoLoading = false;
		setView('main');
	}
	// ── Video search voice mic ──────────────────────────────────────────
	let videoMicListening = false;
	let videoMicRecognizer: any = null;

	function startVideoMic() {
		if (videoMicListening) {
			// Stop
			videoMicRecognizer?.stop();
			videoMicListening = false;
			return;
		}
		const SpeechRecognition =
			(window as any).SpeechRecognition ||
			(window as any).webkitSpeechRecognition;
		if (!SpeechRecognition) {
			alert($i18n.t('Reconnaissance vocale non supportée par ce navigateur.'));
			return;
		}
		const lang =
			($settings as any)?.quizLanguage === 'en' ? 'en-US' :
			($settings as any)?.quizLanguage === 'fr' ? 'fr-FR' :
			navigator.language || 'fr-FR';

		videoMicRecognizer = new SpeechRecognition();
		videoMicRecognizer.lang = lang;
		videoMicRecognizer.interimResults = true;
		videoMicRecognizer.continuous = false;

		let finalTranscript = '';
		videoMicRecognizer.onstart = () => { videoMicListening = true; };
		videoMicRecognizer.onresult = (event: any) => {
			let interim = '';
			for (let i = event.resultIndex; i < event.results.length; i++) {
				if (event.results[i].isFinal) finalTranscript += event.results[i][0].transcript + ' ';
				else interim = event.results[i][0].transcript;
			}
			videoSearchQuery = (finalTranscript + interim).trimStart();
		};
		videoMicRecognizer.onend = () => {
			videoMicListening = false;
			videoSearchQuery = finalTranscript.trim() || videoSearchQuery.trim();
		};
		videoMicRecognizer.onerror = () => { videoMicListening = false; };
		videoMicRecognizer.start();
	}
</script>

<div class="shortcut-col">
	{#if currentView === 'main'}
		<div class="shortcut-row">
			<button type="button" on:click={() => (setView('difficulty'))} class="nav-button menu-theme">
				<span>🎚️</span> {$i18n.t('Difficulty')} <span class="chevron">›</span>
			</button>

			<button type="button" on:click={() => (setView('understand'))} class="nav-button menu-theme">
				<span>🔍</span> {$i18n.t('Understand')} <span class="chevron">›</span>
			</button>

			<button type="button" on:click={() => sendAction(EXPLAIN_OVERRIDE + $i18n.t('Synthesize our conversation into 3-5 high-impact bullet points that capture the "must-know" essentials of this topic.'))} class="nav-button">
				<span>📝</span> {$i18n.t('Summarize')}
			</button>

			<button type="button" on:click={() => sendAction(EXPLAIN_OVERRIDE + $i18n.t('Based on what we just covered, what is the most logical next concept I should learn? Briefly introduce it and show me how it connects to this.'))} class="nav-button">
				<span>⏭️</span> {$i18n.t('Next Step')}
			</button>

			<button type="button" on:click={() => (setView('quiz'))} class="nav-button menu-theme">
				<span>🧠</span> {$i18n.t('Quiz')} <span class="chevron">›</span>
			</button>

			<button type="button" on:click={() => (setView('video-search'))} class="nav-button video-theme">
				<span>🎥</span> {$i18n.t('Vidéo')} <span class="chevron">›</span>
			</button>
		</div>

	{:else if currentView === 'difficulty'}
		<div class="shortcut-row">
			<button type="button" on:click={() => (setView('main'))} class="nav-button back-button">
				<span>⬅️</span> {$i18n.t('Back')}
			</button>
			{#each difficultyLevels as level}
				<button
					type="button"
					on:click={() => sendAction(level.prompt)}
					class="nav-button difficulty-btn pulse-animation"
					style="background: {level.color}; border-color: {level.border}; --light-text: {level.text}; --dark-text: {level.darkText};"
				>
					<span>{level.icon}</span> {level.label}
				</button>
			{/each}
		</div>

	{:else if currentView === 'understand'}
		<div class="shortcut-row">
			<button type="button" on:click={() => (setView('main'))} class="nav-button back-button">
				<span>⬅️</span> {$i18n.t('Back')}
			</button>
			{#each understandActions as action}
				<button type="button" on:click={() => sendAction(action.prompt, false)} class="nav-button pulse-animation">
					<span>{action.icon}</span> {action.label}
				</button>
			{/each}
		</div>

	{:else if currentView === 'quiz'}
		<div class="shortcut-row">
			<button type="button" on:click={() => (setView('main'))} class="nav-button back-button">
				<span>⬅️</span> {$i18n.t('Back')}
			</button>
			{#each quizActions as action}
				<button type="button" on:click={() => sendAction(action.prompt, false)} class="nav-button pulse-animation">
					<span>{action.icon}</span> {action.label}
				</button>
			{/each}
		</div>

	{:else if currentView === 'video-search'}
		<!-- Inline video search panel — no AI involved -->
		<div class="video-search-panel pulse-animation">
			<div class="video-search-header">
				<span>🎥</span>
				<span class="video-search-title">{$i18n.t('Rechercher une vidéo explicative')}</span>
				<button type="button" class="close-btn" on:click={() => (setView('main'))}>✕</button>
			</div>
			<div class="video-search-body">
				<input
					type="text"
					class="video-search-input"
					placeholder={$i18n.t('Ex: algorithmes et pseudocode, protocole TCP...')}
					bind:value={videoSearchQuery}
					on:keydown={(e) => { if (e.key === 'Enter') launchVideoSearch(); }}
					autofocus
				/>
				<!-- Mic button: fills videoSearchQuery with voice -->
				<button
					type="button"
					class="video-mic-btn"
					class:listening={videoMicListening}
					on:click={startVideoMic}
					title={videoMicListening ? $i18n.t('Arrêter l\'écoute') : $i18n.t('Dicter le sujet')}
				>
					{#if videoMicListening}
						<!-- Animated stop/wave icon while listening -->
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="mic-icon">
							<rect x="6" y="6" width="12" height="12" rx="2"/>
						</svg>
					{:else}
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="mic-icon">
							<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
							<path d="M19 10v2a7 7 0 0 1-14 0v-2H3v2a9 9 0 0 0 8 8.94V22H9v2h6v-2h-2v-1.06A9 9 0 0 0 21 12v-2h-2z"/>
						</svg>
					{/if}
				</button>
				<button type="button" class="video-search-btn" on:click={launchVideoSearch}>
					▶ {$i18n.t('Rechercher')}
				</button>
			</div>
		</div>

	{:else if currentView === 'video-player'}
		<!-- Embedded YouTube player with real video IDs from backend -->
		<div class="video-player-panel">
			<div class="video-player-header">
				<span>🎥</span>
				<span class="video-search-title">{videoSearchQuery}</span>
				{#if videoResults.length > 1}
					<span class="video-nav-info">{videoIndex + 1}/{videoResults.length}</span>
					<button type="button" class="nav-arrow" disabled={videoIndex === 0} on:click={() => videoIndex--}>‹</button>
					<button type="button" class="nav-arrow" disabled={videoIndex >= videoResults.length - 1} on:click={() => videoIndex++}>›</button>
				{/if}
				<button type="button" class="close-btn" on:click={closeVideoPlayer}>✕</button>
			</div>
			<div class="video-player-body">
				{#if videoLoading}
					<div class="video-loading">
						<div class="spinner"></div>
						<span>{$i18n.t('Recherche de vidéos...')}</span>
					</div>
				{:else if videoError}
					<div class="video-error">
						<span>😕 {videoError}</span>
						<a href={"https://www.youtube.com/results?search_query=" + encodeURIComponent(videoSearchQuery)} target="_blank" rel="noopener noreferrer" class="video-link">
							{$i18n.t('Rechercher sur YouTube')} ↗
						</a>
					</div>
				{:else if currentVideoId}
					<!-- Lecteur YouTube intégré : miniature d'abord, iframe (youtube-nocookie.com) après clic -->
					<div class="video-16-9">
						{#if videoActivated}
							<!-- youtube-nocookie.com : domaine officiel d'intégration sans blocage -->
							<iframe
								src={"https://www.youtube-nocookie.com/embed/" + currentVideoId + "?rel=0&modestbranding=1&autoplay=1&controls=1&fs=1"}
								title={videoSearchQuery}
								frameborder="0"
								allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
								allowfullscreen
							></iframe>
						{:else}
							<!-- Miniature avec bouton play — l'iframe ne charge qu'au clic -->
							<button
								type="button"
								class="yt-thumb-btn"
								on:click={() => { videoActivated = true; }}
								title="Lancer la vidéo"
							>
								<img
									src={"https://img.youtube.com/vi/" + currentVideoId + "/hqdefault.jpg"}
									alt="{videoSearchQuery} thumbnail"
									class="yt-thumb-img"
									on:error={(e) => { e.currentTarget.src = "https://img.youtube.com/vi/" + currentVideoId + "/default.jpg"; }}
								/>
								<div class="yt-play-overlay">
									<div class="yt-play-btn">
										<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" class="yt-play-icon">
											<path d="M8 5v14l11-7z"/>
										</svg>
									</div>
									<span class="yt-play-label">{$i18n.t('Cliquez pour lancer')}</span>
								</div>
							</button>
						{/if}
					</div>
					<p class="video-hint">
						{$i18n.t('Vidéo non disponible ?')}
						{#if videoIndex < videoResults.length - 1}
							<button type="button" class="inline-btn" on:click={() => { videoIndex++; }}>{$i18n.t('Vidéo suivante')}</button> |
						{/if}
						<a href={"https://www.youtube.com/watch?v=" + currentVideoId} target="_blank" rel="noopener noreferrer" class="video-link">
							{$i18n.t('Ouvrir dans YouTube')} ↗
						</a>
					</p>
				{/if}
			</div>
		</div>
	{/if}
</div>


<style>
    .shortcut-col {
        display: flex;
        flex-direction: column;
        width: 100%;
        gap: 8px;
        margin-bottom: 8px;
        margin-top: 5px;
    }

    .shortcut-row {
        display: flex;
        flex-wrap: nowrap;
        overflow-x: auto;
        gap: 12px;
        width: 100%;
        padding-bottom: 4px;
        align-items: center;
    }

    .no-scrollbar::-webkit-scrollbar { display: none; }
    .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

    .nav-button {
        flex: 0 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 8px 14px;
        background: rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 12px;
        font-size: 14px;
        color: #374151;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        white-space: nowrap;
        cursor: pointer;
    }

    :global(.dark) .nav-button {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ececec;
    }

    .nav-button:hover {
        filter: brightness(1.2);
        background: rgba(0, 0, 0, 0.08);
        transform: translateY(-1px);
    }

    :global(.dark) .nav-button:hover {
        background: rgba(255, 255, 255, 0.15);
    }

    .difficulty-btn { color: var(--light-text); }
    :global(.dark) .difficulty-btn { color: var(--dark-text); }

    .chevron { opacity: 0.5; font-size: 16px; margin-left: 2px; }

    .menu-theme {
        background: rgba(59, 130, 246, 0.1);
        border-color: rgba(59, 130, 246, 0.2);
        color: #2563eb;
    }
    :global(.dark) .menu-theme {
        background: rgba(59, 130, 246, 0.15);
        border-color: rgba(59, 130, 246, 0.3);
        color: #60a5fa;
    }

    .video-theme {
        background: rgba(239, 68, 68, 0.08);
        border-color: rgba(239, 68, 68, 0.25);
        color: #dc2626;
    }
    :global(.dark) .video-theme {
        background: rgba(239, 68, 68, 0.12);
        border-color: rgba(239, 68, 68, 0.3);
        color: #f87171;
    }

    .back-button {
        background: transparent;
        border: 1px dashed rgba(0, 0, 0, 0.2);
        color: #6b7280;
    }
    :global(.dark) .back-button {
        border: 1px dashed rgba(255, 255, 255, 0.2);
        color: #9ca3af;
    }

    .pulse-animation { animation: pulse-border 1.5s ease-out 1; }
    @keyframes pulse-border {
        0%   { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.2); }
        70%  { box-shadow: 0 0 0 8px rgba(255, 255, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
    }

    /* ── Video Search Panel ── */
    .video-search-panel {
        width: 100%;
        border-radius: 16px;
        border: 1px solid rgba(239, 68, 68, 0.3);
        background: rgba(239, 68, 68, 0.05);
        overflow: hidden;
    }
    :global(.dark) .video-search-panel {
        background: rgba(239, 68, 68, 0.08);
        border-color: rgba(239, 68, 68, 0.25);
    }

    .video-search-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        background: linear-gradient(90deg, #dc2626, #ef4444);
        color: white;
        font-size: 13px;
        font-weight: 600;
    }
    .video-search-title {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .close-btn {
        background: rgba(255,255,255,0.2);
        border: none;
        color: white;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        cursor: pointer;
        font-size: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.2s;
    }
    .close-btn:hover { background: rgba(255,255,255,0.35); }

    .video-search-body {
        display: flex;
        gap: 8px;
        padding: 10px 12px;
        align-items: center;
    }
    .video-search-input {
        flex: 1;
        padding: 8px 12px;
        border-radius: 10px;
        border: 1px solid rgba(0,0,0,0.15);
        background: white;
        color: #111;
        font-size: 13px;
        outline: none;
        transition: border-color 0.2s;
    }
    :global(.dark) .video-search-input {
        background: rgba(255,255,255,0.08);
        border-color: rgba(255,255,255,0.15);
        color: #eee;
    }
    .video-search-input:focus {
        border-color: #ef4444;
    }
    .video-search-btn {
        padding: 8px 16px;
        background: #dc2626;
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        white-space: nowrap;
        transition: background 0.2s, transform 0.1s;
    }
    .video-search-btn:hover { background: #b91c1c; transform: scale(1.03); }

    .video-mic-btn {
        flex-shrink: 0;
        width: 36px; height: 36px;
        border: 1.5px solid rgba(239,68,68,0.4);
        border-radius: 50%;
        background: transparent;
        color: #ef4444;
        cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        transition: background 0.2s, border-color 0.2s, transform 0.15s;
    }
    .video-mic-btn:hover { background: rgba(239,68,68,0.1); transform: scale(1.08); }
    .video-mic-btn.listening {
        background: #ef4444;
        border-color: #ef4444;
        color: white;
        animation: mic-pulse 1s ease-in-out infinite;
    }
    @keyframes mic-pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.5); }
        50%       { box-shadow: 0 0 0 8px rgba(239,68,68,0); }
    }
    .mic-icon { width: 16px; height: 16px; }

    /* ── Video Player Panel ── */
    .video-player-panel {
        width: 100%;
        border-radius: 16px;
        border: 1px solid rgba(239, 68, 68, 0.3);
        overflow: hidden;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    .video-player-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        background: linear-gradient(90deg, #dc2626, #ef4444);
        color: white;
        font-size: 13px;
        font-weight: 600;
    }
    .video-player-body {
        background: #000;
    }
    .video-16-9 {
        position: relative;
        width: 100%;
        padding-top: 56.25%;
        background: #000;
    }
    .video-16-9 iframe {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        border: none;
    }
    .video-hint {
        text-align: center;
        font-size: 11px;
        color: #9ca3af;
        padding: 6px 12px;
        margin: 0;
        background: #111;
    }
    .video-link {
        color: #f87171;
        text-decoration: underline;
        cursor: pointer;
    }

    /* ── YouTube Lite Embed ── */
    .video-16-9 .yt-thumb-btn {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        padding: 0; border: none;
        cursor: pointer;
        background: #000;
        overflow: hidden;
    }
    .yt-thumb-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
        transition: transform 0.3s ease, filter 0.3s ease;
    }
    .yt-thumb-btn:hover .yt-thumb-img {
        transform: scale(1.03);
        filter: brightness(0.75);
    }
    .yt-play-overlay {
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        pointer-events: none;
    }
    .yt-play-btn {
        width: 60px; height: 60px;
        background: rgba(220, 38, 38, 0.9);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        transition: transform 0.2s, background 0.2s;
    }
    .yt-thumb-btn:hover .yt-play-btn {
        background: #dc2626;
        transform: scale(1.1);
    }
    .yt-play-icon { width: 28px; height: 28px; margin-left: 3px; }
    .yt-play-label {
        color: white;
        font-size: 12px;
        font-weight: 600;
        text-shadow: 0 1px 4px rgba(0,0,0,0.8);
        background: rgba(0,0,0,0.4);
        padding: 3px 10px;
        border-radius: 20px;
    }
</style>