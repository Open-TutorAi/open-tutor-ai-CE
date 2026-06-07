# 📊 Program Completion Tracking — Contribution

## Overview
This contribution adds **dynamic Program Completion tracking** to the student
chat interface. The progress bar in the right sidebar now updates automatically
based on the number of messages exchanged in the chat session.

## Related Issue
Issue: Dynamic Program Completion Tracking

## Pull Request
[PR — feat/program-completion-tracking](https://github.com/slimaneBohouch/open-tutor-ai-CE/tree/feat/program-completion-tracking)

## What was changed
- `src/lib/components/student/pages/Chat.svelte`
  - Added real-time progress calculation
  - Progress polls every 3 seconds automatically
  - Passes `courseCompletion` prop to `RightBar` component

## How it works
- Formula: `min(messages × 5, 100)%`
- Every message sent = 5% progress
- Maximum: 100% completion
- Updates every 3 seconds automatically

## Features
- ✅ Real-time progress tracking
- ✅ No backend changes required
- ✅ Automatic polling every 3 seconds
- ✅ Clean prop passing to RightBar component

## How to test
1. Run: `docker compose up`
2. Open `http://localhost:5173`
3. Log in and open a student chat
4. Send messages
5. ✅ Watch "Program Completion" bar increase in right sidebar

## Author
Slimane Bohouch — [@slimaneBohouch](https://github.com/slimaneBohouch)