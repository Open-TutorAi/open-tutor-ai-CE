# 👋 Welcome Guidance Card — Contribution

## Overview
This contribution adds a **welcome popup modal** to the OpenTutorAI chat interface.
When a student opens a new chat session, a popup appears with 4 pedagogical tips
to help them interact effectively with the AI tutor.

## Related Issue
Closes #21 — Improve the Chat UI for a Better Tutoring Experience

## Pull Request
[PR #208](https://github.com/Open-TutorAi/open-tutor-ai-CE/pull/208)

## What was changed
- `src/lib/components/chat/Placeholder.svelte` — Main component with popup
- `src/lib/i18n/locales/en-US/translation.json` — English translations
- `src/lib/i18n/locales/fr-FR/translation.json` — French translations
- `src/app.css` — Global styles for portal popup

## Features
- ✅ Popup modal appears on first visit to a new chat
- ✅ 4 numbered pedagogical tips
- ✅ "Don't show me again" checkbox with localStorage persistence
- ✅ "Start Learning" button to close
- ✅ Fully accessible (`aria-modal`, `aria-label`)
- ✅ Dark mode compatible
- ✅ i18n support (EN, FR)
- ✅ Rendered via DOM portal — appears above all UI elements

## How to test
1. Run the app: `docker compose up`
2. Open `http://localhost:5173`
3. Log in and open a new chat
4. ✅ Welcome popup appears with 4 tips
5. Check "Don't show me again" → click "Start Learning"
6. Refresh → popup stays hidden

## Reset the popup (for testing)
Open browser console and run:
```js
localStorage.removeItem('welcomeCardDismissed')
```
Then refresh the page.

## Screenshots
<!-- Add s1.png and s2.png here -->

## Author
Slimane Bohouch — [@slimaneBohouch](https://github.com/slimaneBohouch)