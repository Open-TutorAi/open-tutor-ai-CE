// Public surface of the chat feature.
// Import these from `$lib/features/chat` rather than reaching into ./components/*.
// (Avatar components live here for now and will move to $lib/features/avatar.)

export { default as Chat } from './components/Chat.svelte';
export { default as Messages } from './components/Messages.svelte';
export { default as MessageInput } from './components/MessageInput.svelte';
export { default as ChatControls } from './components/ChatControls.svelte';
export { default as ModelSelector } from './components/ModelSelector.svelte';
export { default as Navbar } from './components/Navbar.svelte';
export { default as Placeholder } from './components/Placeholder.svelte';
export { default as Suggestions } from './components/Suggestions.svelte';
export { default as PairedResponses } from './components/PairedResponses.svelte';
export { default as FullscreenButton } from './components/FullscreenButton.svelte';
export { default as Tags } from './components/Tags.svelte';
export { default as ShareChatModal } from './components/ShareChatModal.svelte';
export { default as TagChatModal } from './components/TagChatModal.svelte';
export { default as SettingsModal } from './components/SettingsModal.svelte';
export { default as ShortcutsModal } from './components/ShortcutsModal.svelte';
