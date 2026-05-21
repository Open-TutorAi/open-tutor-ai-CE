const BASE = '/api/blockly';

export async function testBlocklyCode(payload: {
  python_code: string;
  assignment_id: string;
  blocks_json?: string | null;
}) {
  const res = await fetch(`${BASE}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Erreur ${res.status}`);
  return res.json();
}

export async function submitBlocklyCode(payload: {
  assignment_id: string;
  python_code: string;
  blocks_json?: string | null;
}) {
  const res = await fetch(`${BASE}/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('token')}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Erreur ${res.status}`);
  return res;
}
