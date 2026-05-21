import { writable } from 'svelte/store';

export const blocklyStore = writable({
  pythonCode: '',
  blocksJson: null,
});
