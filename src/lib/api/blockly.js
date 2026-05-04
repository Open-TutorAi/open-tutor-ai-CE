const API_BASE = '/api/blockly';

function authHeaders() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getBlocklyAssignment(assignmentId) {
  const res = await fetch(`${API_BASE}/assignment/${assignmentId}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Erreur ${res.status}`);
  return res.json();
}

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
  return res;
}

export async function getSubmissionHistory(studentId, assignmentId = null) {
  const url = new URL(`${API_BASE}/history/${studentId}`, window.location.origin);
  if (assignmentId) url.searchParams.set('assignment_id', assignmentId);
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Erreur ${res.status}`);
  return res.json();
}

export async function saveWorkspace(assignmentId, blocksJson) {
  await fetch(`${API_BASE}/workspace/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ assignment_id: assignmentId, blocks_json: blocksJson }),
  });
}

export async function loadWorkspace(assignmentId) {
  const res = await fetch(`${API_BASE}/workspace/${assignmentId}`, {
    headers: authHeaders(),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Erreur ${res.status}`);
  return res.json();
}
