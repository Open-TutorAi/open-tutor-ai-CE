# Student User Guide — Voice Interaction & Integrated Video

This guide explains how to use the two new features available in the **student learning space**.

---

## 🎤 Feature 1 — Voice Interaction with the AI

### How to activate the microphone

1. Open the **student chat** at `/student/chat`
2. Look for the **microphone icon 🎤** in the bottom chat bar (right side)
3. Click the 🎤 button
4. Your browser will ask for **microphone permission** — click **"Allow"**
5. The button turns **red and pulses** → the AI is now listening
6. **Speak clearly** — your words appear as grey italic text in real time
7. Click **✓ (confirm)** to send your message to the AI
8. Click **✕ (cancel)** to discard the recording without sending

### Switching language (FR / EN)

- Click the **FR 🇫🇷 / EN 🇬🇧 toggle button** in the chat bar
- The AI will respond in the selected language for all subsequent messages
- Voice recognition also switches to match: `fr-FR` or `en-US`

### Listening to AI responses

1. After the AI replies, look for the **🔊 button** next to the AI message
2. Click 🔊 to have the response **read aloud**
3. The voice matches the selected language (French or English)
4. Click 🔊 again to **stop** playback

### What happens if microphone permission is denied?

- An error message appears explaining that the microphone is blocked
- To re-enable: click the **lock icon 🔒** in your browser's address bar → set Microphone to **"Allow"** → refresh the page

### What happens if voice recognition doesn't start?

- This can happen if the browser blocks access after inactivity
- Click the mic button again, or refresh the page
- Make sure you are using **Google Chrome** or **Microsoft Edge** (Firefox has limited support)

---

## 🎥 Feature 2 — Integrated Explanatory Video in Chat

### How to search for a video

1. In the student chat, click the **shortcut bar** above the input field
2. Click the **🎥 (Video)** button
3. A **search panel** appears above the input
4. Type the topic you want (e.g. `TCP protocol`, `sorting algorithms`)
5. Press **Enter** or click **▶ Search**
6. The AI fetches up to **5 relevant YouTube videos**

### How to use the mic to search (voice search)

1. Inside the video search panel, click the **🎤 mic button** (next to the search field)
2. The mic icon turns **red and pulses** → speak your topic
3. Your speech fills the search field automatically
4. Click **▶ Search** to launch the search

### How to navigate between video results

- Use the **‹ (previous)** and **› (next)** arrows to browse thumbnails
- The counter shows your position (e.g. `2/5`)
- Each thumbnail shows a **▶ play overlay** — click it to load the video

### How to play a video

1. Click the **▶ thumbnail** to activate the inline player
2. The video loads directly in the chat (no new tab or external link)
3. Use the **native YouTube controls**: play, pause, seek, fullscreen
4. The main chat input is **locked** while the video panel is open (shown by a red banner)

### How to close the video panel

- Click the **✕** button in the top-right corner of the video panel
- The chat input returns to normal
- All video state is reset

### What if no videos are found?

- A message appears: *"No video found. Try a different topic."*
- Try using a shorter or more general search term
- Check your internet connection

---

## ⚠️ Browser Compatibility

| Feature | Chrome | Edge | Firefox | Safari |
|---|---|---|---|---|
| 🎤 Voice input (SpeechRecognition) | ✅ | ✅ | ⚠️ Partial | ❌ |
| 🔊 Text-to-speech (SpeechSynthesis) | ✅ | ✅ | ✅ | ✅ |
| 🎥 Embedded video (YouTube iframe) | ✅ | ✅ | ✅ | ✅ |

> **Recommendation**: Use **Google Chrome** for the best experience with voice features.
