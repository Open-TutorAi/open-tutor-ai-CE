# Avatar Feature Migration Guide

This document outlines the changes needed to migrate the 3D avatar features from the `avatar-talk/open-webui` experimental project to the main `open-tutor-ai-CE` project.

## 1. File Structure Changes (Done)

### Static Assets (Done)
- New avatar images in `/static/images/`:
  - `The Scholar.png`
  - `The Mentor.png`
  - `The Coach.png`
  - `The Innovator.png`
  - `background.jpeg` - Background image for avatar selection

## 2. New UI Components

### Avatar Selection (Done)
- `src/lib/components/chat/AvatarSelection.svelte` - Component for selecting avatar personalities
  - Provides UI for choosing between Scholar, Mentor, Coach, and Innovator avatars
  - Handles avatar selection state management
  - Integrates with settings store for persistence

### Avatar Rendering (Done)
- `src/lib/components/chat/AvatarRenderer.svelte` - Component for 3D rendering avatars
- `src/lib/components/chat/AvatarOverlay.svelte` - Controls for avatar interaction

### Avatar Chat Interface (Done)
- `src/lib/components/chat/AvatarChat.svelte` - Main chat interface with avatar integration
  - Extends the existing Chat component with avatar capabilities
  - Handles animation states and avatar responses

## 3. Store Changes

### Settings Store Updates
- Add avatar-related fields to the settings store:
  - `avatarEnabled` - Toggle for avatar mode
  - `selectedAvatarId` - Track the currently selected avatar

### Chat Store Updates
- Add support for avatar animation states and message processing

## 4. Route Updates (Done)
- `/avatar-talk` - Route for avatar-specific chat interface
- Consider updating the chat type selection to include avatar options

## 5. Implementation Notes

1. The avatar feature relies on 3D model rendering in the browser, ensure Three.js or similar library is properly integrated
2. Avatar animations are controlled via a structured JSON format with specific animation codes
3. Avatar selection preferences are stored in localStorage for persistence between sessions

## 6. Required Dependencies

- Three.js for 3D rendering (should be added to package.json if not already present)

## 7. Remaining Migration Steps

1. Update the stores to include avatar-related state
2. Add the avatar selection option to the main chat interface
3. Test the integration to ensure all avatar features work correctly 