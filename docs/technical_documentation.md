# Technical Documentation
## OpenTutorAI — Sprint Features

**Project:** OpenTutorAI Community Edition  
**Module:** Student Tutor Interface  
**Language:** TypeScript / Svelte / Python (FastAPI)  
**Date:** June 2026  

---

## Table of Contents

1. [User Story 1 — Voice Interaction with AI](#us1)
2. [User Story 2 — Integrated Explanatory Video in Chat](#us2)

---

## User Story 1 — Voice Interaction with AI {#us1}

> *"As a student, I want to ask questions verbally and listen to the AI's responses, so that I can have a natural exchange without typing on the keyboard."*

### 1.1 Overview

This feature enables a fully voice-driven interaction loop between the student and the AI tutor. The student speaks a question, it is transcribed in real time, sent to the AI, and the AI's response is read aloud automatically — all within the same chat interface.

### 1.2 Architecture

```
Student speaks
     │
     ▼
[Web Speech API]  ──── SpeechRecognition
     │                  · continuous = true
     │                  · interimResults = true
     │                  · lang = fr-FR | en-US
     ▼
[VoiceRecording.svelte]
  · Real-time waveform visualizer (AudioContext + AnalyserNode)
  · Live transcription display (final + interim text)
  · Duration timer
  · Error handling (mic denied, no network, no device)
     │
     ▼ dispatch('confirm', { text })
[MessageInput.svelte]
  · Receives transcribed text
  · Submits to AI chat pipeline
     │
     ▼
[AI Response]
     │
     ▼
[ResponseMessage.svelte]
  · SpeechSynthesisUtterance
  · Language auto-detection (fr-FR | en-US)
  · "Read Aloud" button (🔊) on each message
  · Speaking state indicator
```

### 1.3 Key Components

| File | Role |
|------|------|
| `ui/src/lib/components/chat/MessageInput/VoiceRecording.svelte` | Core voice recording UI and logic |
| `ui/src/lib/components/chat/MessageInput.svelte` | Hosts the mic button and triggers recording |
| `ui/src/lib/components/chat/Messages/ResponseMessage.svelte` | Handles speech synthesis of AI responses |
| `ui/src/lib/components/chat/AvatarChat.svelte` | Avatar mode with synchronized speech |

### 1.4 Feature 1 — Speech Recognition (Input)

**Technology:** Browser-native Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`)

**Implementation** — `VoiceRecording.svelte`:

```typescript
const API = (window as any).SpeechRecognition || 
            (window as any).webkitSpeechRecognition;

recognizer = new API();

// Language selection based on user settings
const lang =
    ($settings as any)?.quizLanguage === 'en' ? 'en-US' :
    ($settings as any)?.quizLanguage === 'fr' ? 'fr-FR' :
    navigator.language || 'fr-FR';

recognizer.lang           = lang;
recognizer.continuous     = true;   // keeps listening until stopped
recognizer.interimResults = true;   // shows partial results in real time

// Real-time transcription
recognizer.onresult = (event) => {
    for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
            transcription += event.results[i][0].transcript + ' ';
        } else {
            interimText = event.results[i][0].transcript; // shown in gray italic
        }
    }
};
```

**Mic Access & Error Handling:**

```typescript
// Requests microphone permission before starting
testStream = await navigator.mediaDevices.getUserMedia({ audio: true });
```

| Error | User Message |
|-------|-------------|
| `NotAllowedError` | 🚫 Microphone denied — instructions to re-enable |
| `NotFoundError` | 🎤 No microphone detected |
| `network` | ⚠️ Network error (Chrome requires internet for transcription) |
| `no-speech` | Silently ignored — auto-restarts listening |

### 1.5 Feature 2 — Waveform Visualizer

A real-time audio waveform is displayed while the student speaks, using the browser's `AudioContext` and `AnalyserNode`.

```typescript
async function startVisualizer(stream: MediaStream) {
    const ctx     = new AudioContext();
    const src     = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 64;
    src.connect(analyser);

    const buf = new Uint8Array(analyser.frequencyBinCount);
    const draw = () => {
        animFrameId = requestAnimationFrame(draw);
        analyser.getByteTimeDomainData(buf);
        // RMS amplitude → height of each bar
        const rms = Math.min(1, Math.max(0.04, Math.sqrt(sum / buf.length) * 12));
        visualizerData = [...visualizerData.slice(1), rms]; // 30-bar rolling window
    };
}
```

The UI renders **30 animated bars** whose height reflects the actual voice amplitude.

### 1.6 Feature 3 — Speech Synthesis (Output)

**Technology:** Browser-native Web Speech Synthesis API (`SpeechSynthesisUtterance`)

**Implementation** — `ResponseMessage.svelte`:

```typescript
const speak = new SpeechSynthesisUtterance(message.content);

// Auto-detect language from AI response content
speak.lang = detectedLang === 'fr' ? 'fr-FR' : 'en-US';
speak.rate = $settings.audio?.tts?.playbackRate ?? 1;

// Select best matching voice for the language
const voice = voices.find(v => v.lang.startsWith(speak.lang.slice(0, 2)));
if (voice) speak.voice = voice;

speechSynthesis.speak(speak);
```

A 🔊 **"Read Aloud"** button is displayed on every AI message. It toggles between speaking and stopped states with visual feedback.

### 1.7 Multilingual Support (FR / EN)

| Component | FR | EN | Auto-detect |
|-----------|----|----|-------------|
| Speech Recognition | `fr-FR` | `en-US` | Via `$settings.quizLanguage` |
| Speech Synthesis | `fr-FR` voice | `en-US` voice | From response content language |
| Fallback | `navigator.language` | `navigator.language` | Browser locale |

### 1.8 Interaction Flow

```
1. Student clicks 🎤 mic button
2. Permission requested → microphone access granted
3. Waveform visualizer starts (real-time audio bars)
4. SpeechRecognition starts in fr-FR or en-US
5. Words appear live as student speaks (interim + final)
6. Student clicks ✓ to confirm
7. Transcribed text is sent as a chat message
8. AI generates response
9. 🔊 button appears → student clicks to hear the response
10. SpeechSynthesis reads aloud in the matching language
```

---

## User Story 2 — Integrated Explanatory Video in Chat {#us2}

> *"As a student, I want the AI to display a short explanatory video directly inside the chat, so I can visualize a concept without leaving my workspace or searching external links."*

### 2.1 Overview

This feature provides two complementary ways to display a contextual YouTube video inline in the chat interface:
- **Via the Pedagogical Shortcuts bar** — A dedicated 🎥 button allows the student to search for any educational video by topic.
- **Via the AI response** — When the AI includes a special tag `[YOUTUBE: VIDEO_ID]` in its response, a video card is automatically rendered inside the message bubble.

In both cases, **no external links are shown** — the video is embedded directly in the chat.

### 2.2 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   TRIGGER LAYER                     │
│                                                     │
│  [🎥 Vidéo button]        [AI Response with tag]    │
│  PedagogicalShortcuts      ResponseMessage          │
│       │                          │                  │
│       ▼                          ▼                  │
│  Search panel           [YOUTUBE: VIDEO_ID]         │
│  (topic input)          → parsed by regex           │
└─────────────┬───────────────────┬───────────────────┘
              │                   │
              ▼                   ▼
    ┌─────────────────┐   ┌──────────────────────┐
    │  Backend API    │   │   Inline Video Card  │
    │ /youtube/search │   │   (thumbnail shown)  │
    │  (FastAPI)      │   │   Click → modal      │
    │  Scrapes YouTube│   │   iframe player      │
    └────────┬────────┘   └──────────────────────┘
             │
             ▼
    Returns 5 video IDs
             │
             ▼
    ┌──────────────────────────────────────┐
    │         VIDEO PLAYER UI             │
    │  1. Thumbnail shown immediately     │
    │  2. Click ▶ → iframe loads         │
    │  3. youtube-nocookie.com embed      │
    │  4. Controls: play/pause/seek/fs    │
    │  5. Navigate prev/next video        │
    └──────────────────────────────────────┘
```

### 2.3 Key Components

| File | Role |
|------|------|
| `ui/src/lib/components/chat/Shortcuts/PedagogicalShortcuts.svelte` | Video search UI + embedded player |
| `ui/src/lib/components/chat/Messages/ResponseMessage.svelte` | AI message video card + fullscreen modal |
| `gateway/http/routers/youtube.py` | Backend: YouTube scraper API |
| `ui/vite.config.ts` | CORS / COOP headers configuration |

### 2.4 Feature 1 — Backend: YouTube Search API

**Technology:** FastAPI (Python) — server-side YouTube scraping

**Endpoint:** `GET /youtube/search?q={query}`

**File:** `gateway/http/routers/youtube.py`

```python
@router.get("/youtube/search")
async def search_youtube_videos(q: str = Query(..., min_length=1, max_length=200)):
    """Search YouTube and return up to 5 real video IDs for a given query."""
    url = (
        f"https://www.youtube.com/results"
        f"?search_query={requests.utils.quote(q)}"
        f"&sp=EgIQAQ%3D%3D"   # filter: videos only (no playlists/channels)
    )
    resp = requests.get(url, headers=HEADERS, timeout=8)

    # Extract video IDs from page source using regex
    ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)

    # Deduplicate, return first 5
    unique_ids = list(dict.fromkeys(ids))[:5]
    return JSONResponse({"videos": unique_ids, "query": q})
```

**Response format:**
```json
{
  "videos": ["dQw4w9WgXcQ", "abc123def45", "..."],
  "query": "protocole TCP réseau"
}
```

**Error handling:**

| Scenario | HTTP Code | Response |
|----------|-----------|----------|
| No videos found | `404` | `{"error": "No videos found", "videos": []}` |
| YouTube timeout | `504` | `{"error": "YouTube request timed out", "videos": []}` |
| Any other error | `500` | `{"error": "<message>", "videos": []}` |

### 2.5 Feature 2 — Pedagogical Shortcuts Video Player

**File:** `PedagogicalShortcuts.svelte`

**User flow:**
1. Student clicks 🎥 **Vidéo** button in the shortcuts bar
2. A search panel appears inline
3. Student types a topic (e.g. "algorithmes de tri") and presses Search
4. Frontend calls `/youtube/search?q=...`
5. Results are displayed as a **lazy-loaded player** (thumbnail first, iframe on click)
6. Student can navigate between up to 5 videos with ‹ › arrows

**Key implementation:**

```typescript
// State
let videoResults: string[] = [];     // array of video IDs
let videoIndex   = 0;                // current video index
let videoActivated = false;          // true only after user clicks ▶

// Search call
const res = await fetch(
    `${TUTOR_API_BASE_URL}/youtube/search?q=${encodeURIComponent(query)}`,
    { headers: { Authorization: `Bearer ${localStorage.token}` } }
);
const data = await res.json();
videoResults = data.videos;          // array of up to 5 IDs
```

**Lazy-loading pattern** (performance optimization):
```svelte
{#if videoActivated}
    <!-- iframe only loads AFTER user clicks play -->
    <iframe src="https://www.youtube-nocookie.com/embed/{currentVideoId}
                 ?rel=0&autoplay=1&controls=1&fs=1" ...></iframe>
{:else}
    <!-- Show thumbnail first — zero iframe cost -->
    <button on:click={() => videoActivated = true}>
        <img src="https://img.youtube.com/vi/{currentVideoId}/hqdefault.jpg" />
        <div class="play-overlay">▶ Cliquez pour lancer</div>
    </button>
{/if}
```

### 2.6 Feature 3 — AI-Triggered Video Card in Message Bubble

When the AI's response contains the special tag `[YOUTUBE: VIDEO_ID]`, the message component automatically renders a rich video card directly inside the message bubble.

**Tag format (used in AI prompt/response):**
```
[YOUTUBE: dQw4w9WgXcQ]
```

**Parsing** — `ResponseMessage.svelte`:
```typescript
let youtubeVideoId: string | null = null;

// Extract and strip the tag from displayed content
processed = processed.replace(
    /\[YOUTUBE:\s*([a-zA-Z0-9_-]{8,15})\]/gi,
    (match, videoId) => {
        youtubeVideoId = videoId.trim();
        return ''; // remove from visible text
    }
);
```

**Rendered card:**
- Header bar with YouTube logo and "Explanatory Video — Micro-Learning (1–3 min)"
- Thumbnail with animated play button overlay
- Click → **fullscreen modal** with `youtube-nocookie.com` iframe
- Click outside modal or ✕ → closes and stops video

### 2.7 Iframe Embedding — Technical Solution

YouTube blocks `<iframe>` embedding on localhost and unauthorized origins using its standard domain. This was resolved by using **YouTube's Privacy-Enhanced Mode**:

| Domain | Embedding | Restrictions |
|--------|-----------|-------------|
| `www.youtube.com/embed/` | ❌ Blocked on localhost | X-Frame-Options |
| `www.youtube-nocookie.com/embed/` | ✅ Works everywhere | No cookies, no block |

**Final iframe URL format:**
```
https://www.youtube-nocookie.com/embed/{VIDEO_ID}
    ?rel=0              // no related videos
    &modestbranding=1   // minimal YouTube branding
    &autoplay=1         // auto-start on load
    &controls=1         // show player controls (play/pause/seek)
    &fs=1               // enable fullscreen button
```

**CORS/COOP headers** — `vite.config.ts`:
```typescript
res.setHeader('Cross-Origin-Opener-Policy', 'unsafe-none');
// Allows YouTube iframes and new tab links to work correctly
```

### 2.8 Player Controls Summary

| Control | Implementation |
|---------|---------------|
| ▶ Play | `autoplay=1` on iframe load + YouTube native controls |
| ⏸ Pause | YouTube native controls (`controls=1`) |
| ⏩ Progress bar | YouTube native controls (`controls=1`) |
| ⛶ Fullscreen | `fs=1` + `allowfullscreen` + `allow="fullscreen"` on iframe |
| ‹ › Navigate videos | Custom prev/next buttons — `videoIndex--` / `videoIndex++` |
| ✕ Close modal | Hides modal + resets iframe `src` to stop playback |

### 2.9 No-Link Policy — Compliance

The application **never displays a raw YouTube URL** as a clickable link in normal operation. The video is always rendered as an embedded player. A fallback link ("Open on YouTube ↗") is only shown in error cases (e.g., video not found, network error).

---

## Summary Table

| Feature | Technology | File |
|---------|------------|------|
| Voice recognition | Web Speech API | `VoiceRecording.svelte` |
| Waveform visualizer | AudioContext + AnalyserNode | `VoiceRecording.svelte` |
| Speech synthesis | SpeechSynthesis API | `ResponseMessage.svelte` |
| Multilingual support | `quizLanguage` setting | `VoiceRecording.svelte`, `ResponseMessage.svelte` |
| YouTube search API | FastAPI + requests (Python) | `youtube.py` |
| Video search UI | Svelte reactive state | `PedagogicalShortcuts.svelte` |
| AI video card | Regex tag parsing + iframe | `ResponseMessage.svelte` |
| Lazy-load player | Thumbnail → iframe on click | `PedagogicalShortcuts.svelte` |
| Fullscreen modal | CSS + DOM toggle | `ResponseMessage.svelte` |
| Embed fix (nocookie) | `youtube-nocookie.com` | Both Svelte components |
