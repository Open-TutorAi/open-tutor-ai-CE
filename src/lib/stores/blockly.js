// src/lib/stores/blockly.js
// Store Svelte pour la gestion de l'état Blockly

import { writable, derived } from 'svelte/store';

// État principal du workspace Blockly
export const blocklyStore = writable({
  pythonCode: '',
  blocksJson: null,
  isModified: false,
  lastSaved: null,
});

// Historique des soumissions (pour le dashboard)
export const submissionHistory = writable([]);

// Résultat de la dernière soumission
export const lastResult = writable(null);

// Store dérivé : indicateur de code prêt à soumettre
export const isReadyToSubmit = derived(
  blocklyStore,
  ($store) => $store.pythonCode && $store.pythonCode.trim().length > 0
);

// Store dérivé : statistiques de progression
export const progressStats = derived(
  submissionHistory,
  ($history) => {
    if ($history.length === 0) return { best: 0, average: 0, attempts: 0 };
    const scores = $history.map(s => s.score).filter(s => s !== null);
    return {
      best: Math.max(...scores),
      average: Math.round(scores.reduce((a, b) => a + b, 0) / scores.length),
      attempts: $history.length,
    };
  }
);

// Actions
export function addSubmission(submission) {
  submissionHistory.update(history => [submission, ...history]);
  lastResult.set(submission);
}

export function clearBlockly() {
  blocklyStore.set({
    pythonCode: '',
    blocksJson: null,
    isModified: false,
    lastSaved: null,
  });
  lastResult.set(null);
}