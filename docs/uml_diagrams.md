# UML Diagrams — OpenTutorAI Sprint Features

---

# USER STORY 1 — Voice Interaction with AI

---

## 1.1 Class Diagram — US1

```mermaid
classDiagram
    class VoiceRecording {
        +boolean recording
        +string className
        -Status status
        -string errorMsg
        -string transcription
        -string interimText
        -number durationSeconds
        -MediaStream micStream
        -number[] visualizerData
        -any recognizer
        -boolean active
        -boolean hasFailed
        +startRecognition() Promise~void~
        +stopAll() void
        +cancel() void
        +confirm() void
        -startVisualizer(stream: MediaStream) Promise~void~
        -stopVisualizer() void
        -startTimer() void
        -stopTimer() void
        -showError(msg: string) void
    }

    class MessageInput {
        -boolean recording
        -string value
        +handleMicClick() void
        +handleVoiceConfirm(text: string) void
        +handleVoiceCancel() void
        +submitMessage() void
    }

    class ResponseMessage {
        -string content
        -boolean speaking
        -number speakingIdx
        -string youtubeVideoId
        +toggleSpeakMessage() Promise~void~
        -detectLanguage(text: string) string
        -speakWithSynthesis(text: string, lang: string) void
    }

    class SpeechRecognizerWrapper {
        <<interface>>
        +string lang
        +boolean continuous
        +boolean interimResults
        +start() void
        +stop() void
        +onstart() void
        +onresult(event) void
        +onerror(event) void
        +onend() void
    }

    class AudioVisualizer {
        <<utility>>
        -AudioContext ctx
        -AnalyserNode analyser
        -Uint8Array buffer
        +connect(stream: MediaStream) void
        +getRMSLevel() number
        +drawFrame() void
    }

    class SpeechSynthesisService {
        <<interface>>
        +speak(utterance: SpeechSynthesisUtterance) void
        +cancel() void
        +getVoices() SpeechSynthesisVoice[]
    }

    class SpeechSynthesisUtterance {
        +string text
        +string lang
        +number rate
        +SpeechSynthesisVoice voice
        +onend() void
    }

    MessageInput "1" --> "1" VoiceRecording : contains
    VoiceRecording "1" --> "1" SpeechRecognizerWrapper : uses
    VoiceRecording "1" --> "1" AudioVisualizer : uses
    ResponseMessage "1" --> "1" SpeechSynthesisService : uses
    SpeechSynthesisService "1" --> "*" SpeechSynthesisUtterance : creates
    MessageInput "1" --> "1" ResponseMessage : triggers AI → response
```

---

## 1.2 Activity Diagram — US1

```mermaid
flowchart TD
    A([Student clicks 🎤 Mic Button]) --> B[Request microphone permission]
    B --> C{Permission granted?}
    C -- No --> D[Show error: Microphone denied\nInstructions to re-enable]
    D --> Z([End])
    C -- Yes --> E[Start audio stream\nStart waveform visualizer]
    E --> F[Start SpeechRecognition\nfr-FR or en-US]
    F --> G{API started\nwithin 5s?}
    G -- No --> H[Show error: Network / Chrome blocked]
    H --> Z
    G -- Yes --> I[Status: LISTENING 🎤\nWaveform animated]
    I --> J[Student speaks]
    J --> K[Interim text displayed in gray italic]
    K --> L{Speech segment\nfinalized?}
    L -- No → continue --> J
    L -- Yes --> M[Append final text to transcription]
    M --> N{Student action?}
    N -- Continue speaking --> J
    N -- Click ✕ Cancel --> O[Stop recording\nDiscard transcription]
    O --> Z
    N -- Click ✓ Confirm --> P[Stop recording\nSend transcribed text to chat]
    P --> Q[AI processes message\nGenerates response]
    Q --> R[Response displayed in chat bubble]
    R --> S{Student clicks\n🔊 Read Aloud?}
    S -- No --> Z
    S -- Yes --> T[Detect response language\nfr-FR or en-US]
    T --> U[Create SpeechSynthesisUtterance\nSelect matching voice]
    U --> V[speechSynthesis.speak]
    V --> W[AI response read aloud]
    W --> Z([End])
```

---

## 1.3 Sequence Diagram — US1

```mermaid
sequenceDiagram
    actor Student
    participant MI as MessageInput.svelte
    participant VR as VoiceRecording.svelte
    participant Nav as navigator.mediaDevices
    participant SR as Web SpeechRecognition API
    participant Chat as Chat Pipeline
    participant AI as AI Server
    participant RM as ResponseMessage.svelte
    participant SS as SpeechSynthesis API

    Student->>MI: Click 🎤 button
    MI->>VR: recording = true
    VR->>Nav: getUserMedia({ audio: true })
    Nav-->>VR: MediaStream (mic access granted)
    VR->>VR: startVisualizer(stream)
    Note over VR: AudioContext + AnalyserNode\nReal-time waveform bars

    VR->>SR: new SpeechRecognition()
    VR->>SR: lang = fr-FR | en-US
    VR->>SR: continuous = true, interimResults = true
    VR->>SR: start()
    SR-->>VR: onstart()
    Note over VR: Status → LISTENING

    loop Student speaks
        SR-->>VR: onresult(interim)
        VR->>VR: interimText = interim transcript
        Note over VR: Gray italic text shown live
    end

    SR-->>VR: onresult(final)
    VR->>VR: transcription += final segment

    Student->>VR: Click ✓ Confirm
    VR->>SR: stop()
    VR->>MI: dispatch('confirm', { text })
    MI->>Chat: submitMessage(transcribedText)
    Chat->>AI: POST /api/chat { message }
    AI-->>Chat: AI response stream
    Chat-->>RM: render message content

    Student->>RM: Click 🔊 Read Aloud
    RM->>RM: detectLanguage(content)
    RM->>SS: new SpeechSynthesisUtterance(content)
    RM->>SS: utterance.lang = fr-FR | en-US
    RM->>SS: speechSynthesis.speak(utterance)
    SS-->>Student: 🔊 AI response read aloud
    SS-->>RM: onend() → speaking = false
```

---
---

# USER STORY 2 — Integrated Explanatory Video in Chat

---

## 2.1 Class Diagram — US2

```mermaid
classDiagram
    class PedagogicalShortcuts {
        -string currentView
        -string videoSearchQuery
        -string[] videoResults
        -number videoIndex
        -boolean videoLoading
        -string videoError
        -boolean videoActivated
        +launchVideoSearch() Promise~void~
        +closeVideoPlayer() void
        +sendAction(prompt: string) void
    }

    class VideoPlayer {
        <<embedded component>>
        -string videoId
        -boolean activated
        -string searchQuery
        +renderThumbnail() void
        +activateIframe() void
        +navigatePrev() void
        +navigateNext() void
    }

    class ResponseMessage {
        -string content
        -string youtubeVideoId
        -boolean modalVisible
        +parseYoutubeTag(content: string) string
        +showModal(videoId: string) void
        +hideModal() void
        +toggleSpeakMessage() void
    }

    class YouTubeModal {
        <<embedded component>>
        -string videoId
        -boolean visible
        +show() void
        +hide() void
        +stopVideo() void
    }

    class YouTubeRouter {
        <<FastAPI Router>>
        +searchVideos(q: string) JSONResponse
        -scrapeYoutube(url: string) string
        -extractVideoIds(html: string) string[]
        -deduplicateIds(ids: string[]) string[]
    }

    class YouTubeScraperService {
        <<utility>>
        -string baseUrl
        -dict headers
        -string filterParam
        +buildSearchUrl(query: string) string
        +fetchPage(url: string) string
        +parseVideoIds(html: string) string[]
    }

    class IframePlayer {
        <<browser component>>
        +string src
        +boolean allowfullscreen
        +string allow
        +load(videoId: string) void
        +unload() void
    }

    PedagogicalShortcuts "1" --> "1" VideoPlayer : renders
    PedagogicalShortcuts "1" --> "1" YouTubeRouter : calls via fetch
    VideoPlayer "1" --> "1" IframePlayer : creates on activation
    ResponseMessage "1" --> "1" YouTubeModal : controls
    YouTubeModal "1" --> "1" IframePlayer : contains
    YouTubeRouter "1" --> "1" YouTubeScraperService : delegates
```

---

## 2.2 Activity Diagram — US2 (Pedagogical Shortcuts path)

```mermaid
flowchart TD
    A([Student clicks 🎥 Vidéo button]) --> B[Show Video Search Panel]
    B --> C[Student types topic\ne.g. 'protocole TCP']
    C --> D{Press Enter\nor click Rechercher?}
    D -- No --> C
    D -- Yes --> E[Call GET /youtube/search?q=topic]
    E --> F[Backend scrapes YouTube\nwith video-only filter]
    F --> G{Videos found?}
    G -- No --> H[Show error message\n+ fallback link to YouTube]
    H --> I{Retry?}
    I -- Yes --> C
    I -- No --> Z([End])
    G -- Yes --> J[Return up to 5 video IDs]
    J --> K[Display video thumbnail\nwith ▶ play overlay]
    K --> L{Student action?}
    L -- Click ‹ › Navigate --> M[Show previous/next thumbnail]
    M --> L
    L -- Click ✕ Close --> Z
    L -- Click ▶ Play --> N[videoActivated = true]
    N --> O[Load iframe\nyoutube-nocookie.com/embed/ID\n?autoplay=1&controls=1&fs=1]
    O --> P[Video plays inline in chat]
    P --> Q{Student action?}
    Q -- Pause/Seek/Fullscreen --> R[YouTube native controls]
    R --> Q
    Q -- Click ✕ Close --> S[Hide panel\nReset state]
    S --> Z([End])
```

---

## 2.3 Activity Diagram — US2 (AI Response path)

```mermaid
flowchart TD
    A([Student sends message to AI]) --> B[AI Server processes request]
    B --> C{AI decides to\nsuggest a video?}
    C -- No --> D[Normal text response]
    D --> Z([End])
    C -- Yes --> E["AI includes tag in response:\n[YOUTUBE: VIDEO_ID]"]
    E --> F[Response streamed to ResponseMessage]
    F --> G["Regex parses [YOUTUBE: VIDEO_ID] tag"]
    G --> H[youtubeVideoId extracted\nTag removed from displayed text]
    H --> I[Render text content normally]
    I --> J[Render YouTube Video Card below message]
    J --> K[Show thumbnail with\n▶ Cliquez pour lancer overlay]
    K --> L{Student clicks thumbnail?}
    L -- No --> Z
    L -- Yes --> M[Open fullscreen modal\nbg-black/90 backdrop]
    M --> N["Load iframe\nyoutube-nocookie.com/embed/ID\n?autoplay=1&controls=1&fs=1"]
    N --> O[Video plays in fullscreen modal]
    O --> P{Student action?}
    P -- Click outside modal --> Q[Hide modal\nReset iframe src to stop video]
    P -- Click ✕ Close --> Q
    P -- Use player controls --> R[Play / Pause / Seek / Fullscreen]
    R --> P
    Q --> Z([End])
```

---

## 2.4 Sequence Diagram — US2 (Pedagogical Shortcuts path)

```mermaid
sequenceDiagram
    actor Student
    participant PS as PedagogicalShortcuts.svelte
    participant FE as Frontend (Fetch API)
    participant YR as YouTubeRouter (FastAPI)
    participant YT as YouTube.com
    participant VP as VideoPlayer (iframe)

    Student->>PS: Click 🎥 Vidéo button
    PS->>PS: currentView = 'video-search'
    Note over PS: Search panel appears

    Student->>PS: Type topic + click Rechercher
    PS->>PS: videoLoading = true
    PS->>FE: fetch('/youtube/search?q=topic')
    FE->>YR: GET /youtube/search?q=topic
    YR->>YT: GET youtube.com/results?search_query=topic&sp=EgIQAQ
    YT-->>YR: HTML page with search results
    YR->>YR: Extract videoIds via regex
    YR->>YR: Deduplicate → max 5 IDs
    YR-->>FE: { "videos": ["id1","id2",...] }
    FE-->>PS: videoResults = ["id1","id2",...]
    PS->>PS: videoLoading = false
    PS->>PS: currentView = 'video-player'

    Note over PS: Thumbnail shown\n(img.youtube.com/vi/id1/hqdefault.jpg)

    Student->>PS: Click ▶ on thumbnail
    PS->>PS: videoActivated = true
    PS->>VP: render iframe
    VP->>YT: Load youtube-nocookie.com/embed/id1?autoplay=1&controls=1&fs=1
    YT-->>VP: Video stream
    Note over VP: Video plays inline in chat

    opt Navigate to next video
        Student->>PS: Click › arrow
        PS->>PS: videoIndex++
        PS->>PS: videoActivated = false
        Note over PS: New thumbnail shown
    end

    Student->>PS: Click ✕ Close
    PS->>PS: closeVideoPlayer()
    Note over PS: Reset all state\nReturn to main shortcuts
```

---

## 2.5 Sequence Diagram — US2 (AI Response path)

```mermaid
sequenceDiagram
    actor Student
    participant MI as MessageInput.svelte
    participant AI as AI Server
    participant RM as ResponseMessage.svelte
    participant Modal as YouTube Modal (DOM)
    participant VP as IframePlayer

    Student->>MI: Type/speak message
    MI->>AI: POST /api/chat { message }

    AI->>AI: Process → decide to add video
    AI-->>RM: Stream response with [YOUTUBE: abc123xyz]

    RM->>RM: Parse content with regex
    Note over RM: /\[YOUTUBE:\s*([a-zA-Z0-9_-]{8,15})\]/gi
    RM->>RM: youtubeVideoId = "abc123xyz"
    RM->>RM: Remove tag from displayed text

    RM->>RM: Render text content
    RM->>RM: Render YouTube Video Card
    Note over RM: Thumbnail shown\n+ play overlay

    Student->>RM: Click thumbnail ▶
    RM->>Modal: getElementById('yt-modal-abc123xyz')\n.classList.remove('hidden')
    Modal->>Modal: Show fullscreen overlay\n(fixed, z-9999, bg-black/90)
    Modal->>VP: Render iframe
    VP->>VP: Load youtube-nocookie.com/embed/abc123xyz\n?autoplay=1&controls=1&fs=1
    Note over VP: Video plays in fullscreen modal

    alt Student clicks outside modal
        Student->>Modal: click (self)
        Modal->>VP: iframe.src = iframe.src (stops video)
        Modal->>Modal: classList.add('hidden')
    else Student clicks ✕ Close button
        Student->>Modal: click ✕
        Modal->>Modal: classList.add('hidden')
    end
```
