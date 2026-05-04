// src/lib/api/blockly.js
// Fonctions d'appel API pour le module Blockly

const API_BASE = '/api/blockly';

/**
 * Récupère les détails d'un exercice Blockly
 * @param {string} assignmentId
 * @returns {Promise<BlocklyAssignment>}
 */
export async function getBlocklyAssignment(assignmentId) {
  const res = await fetch(`${API_BASE}/assignment/${assignmentId}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Erreur ${res.status}: ${await res.text()}`);
  return res.json();
}

/**
 * Teste le code Python sans soumission formelle
 * @param {{ python_code, assignment_id, blocks_json }} payload
 * @returns {Promise<TestResult>}
 */
export async function testBlocklyCode(payload) {
  const res = await fetch(`${API_BASE}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Erreur ${res.status}`);
  }
  return res.json();
}

/**
 * Soumet un exercice Blockly pour évaluation officielle (retourne un stream SSE)
 * Usage : voir composant BlocklyEditor.svelte — utilise fetch + ReadableStream
 * @param {{ assignment_id, python_code, blocks_json }} payload
 * @returns {Promise<Response>} - Response streaming SSE
 */
export async function submitBlocklyCode(payload) {
  const res = await fetch(`${API_BASE}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Erreur ${res.status}`);
  }
  return res; // retourner la Response brute pour streamer
}

/**
 * Récupère l'historique des soumissions Blockly d'un étudiant
 * @param {string} studentId
 * @param {string} [assignmentId] - filtre optionnel
 * @returns {Promise<BlocklySubmission[]>}
 */
export async function getSubmissionHistory(studentId, assignmentId = null) {
  const url = new URL(`${API_BASE}/history/${studentId}`, window.location.origin);
  if (assignmentId) url.searchParams.set('assignment_id', assignmentId);
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Erreur ${res.status}`);
  return res.json();
}

/**
 * Sauvegarde le workspace Blockly en backend (auto-save)
 * @param {string} assignmentId
 * @param {string} blocksJson - XML du workspace
 */
export async function saveWorkspace(assignmentId, blocksJson) {
  await fetch(`${API_BASE}/workspace/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ assignment_id: assignmentId, blocks_json: blocksJson }),
  });
  // Silencieux - pas d'erreur critique si ça échoue
}

/**
 * Charge le dernier workspace sauvegardé en backend
 * @param {string} assignmentId
 * @returns {Promise<{blocks_json: string}|null>}
 */
export async function loadWorkspace(assignmentId) {
  const res = await fetch(`${API_BASE}/workspace/${assignmentId}`, {
    headers: authHeaders(),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Erreur ${res.status}`);
  return res.json();
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function authHeaders() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}
