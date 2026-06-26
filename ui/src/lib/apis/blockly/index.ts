const BASE = '/api/blockly';

// ── Types ────────────────────────────────────────────────────────────────────

export interface ExecutionResult {
  stdout:            string | null;
  stderr:            string | null;
  error:             string | null;
  timed_out:         boolean;
  execution_time_ms: number | null;
}

export interface SSEEvent {
  type:           'score' | 'feedback' | 'chunk' | 'done';
  value?:         number;    // pour type='score'
  content?:       string;    // pour type='chunk' | 'feedback'
  assignment_id?: string;    // pour type='done'
}

export interface BlocklyContext {
  course:        string;
  objectives:    string;
  prerequisites: string;
  level:         'beginner' | 'intermediate' | 'advanced';
}

// ── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Parse les événements SSE depuis un ReadableStream.
 * Générateur async — usage : for await (const ev of parseSSE(response)) { ... }
 */
export async function* parseSSE(response: Response): AsyncGenerator<SSEEvent> {
  const reader  = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    for (const line of decoder.decode(value, { stream: true }).split('\n')) {
      if (!line.startsWith('data: ')) continue;
      try {
        yield JSON.parse(line.slice(6)) as SSEEvent;
      } catch {}
    }
  }
}

/**
 * Normalise les clés JSON retournées par Ollama.
 * Ollama peut retourner "title" ou "titre" selon le contexte.
 */
export function normalizeExercise(raw: Record<string, unknown>) {
  return {
    title:       String(raw.title || raw.titre || 'Exercice Python'),
    description: String(raw.description || ''),
    test_cases:  Array.isArray(raw.test_cases)   ? raw.test_cases   :
                 Array.isArray(raw.testing_cases) ? raw.testing_cases : [],
    hints:       Array.isArray(raw.hints)   ? raw.hints   :
                 Array.isArray(raw.indices) ? raw.indices : [],
  };
}

// ── US-B04 : Exécution ────────────────────────────────────────────────────────

/**
 * Exécute du code Python dans le sandbox isolé.
 */
export async function executeCode(pythonCode: string): Promise<ExecutionResult> {
  const res = await fetch(`${BASE}/execute`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ python_code: pythonCode }),
  });
  if (!res.ok) throw new Error(`Erreur exécution HTTP ${res.status}`);
  return res.json();
}

// ── US-B05 : Soumission ───────────────────────────────────────────────────────

/**
 * Soumet une solution.
 * Retourne un générateur SSE : score, feedback, done.
 */
export async function submitSolution(
  pythonCode: string,
  level: string,
): Promise<Response> {
  const res = await fetch(`${BASE}/submit`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ python_code: pythonCode, level }),
  });
  if (!res.ok) throw new Error(`Erreur soumission HTTP ${res.status}`);
  return res;
}

// ── US-B02 : Génération exercice ─────────────────────────────────────────────

/**
 * Génère un exercice via l'IA Ollama.
 * Retourne un générateur SSE : chunk(s), done.
 */
export async function generateExercise(ctx: BlocklyContext): Promise<Response> {
  const res = await fetch(`${BASE}/generate/stream`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({
      level:         ctx.level,
      course:        ctx.course,
      objectives:    ctx.objectives,
      prerequisites: ctx.prerequisites,
    }),
  });
  if (!res.ok) throw new Error(`Erreur génération HTTP ${res.status}`);
  return res;
}

// ── US-B07 : Workspace ────────────────────────────────────────────────────────

/**
 * Sauvegarde le workspace XML Blockly.
 */
export async function saveWorkspace(
  assignmentId: string,
  workspaceXml: string,
): Promise<{ status: string; id: string }> {
  const res = await fetch(`${BASE}/workspace/save`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({
      assignment_id: assignmentId,
      workspace_xml: workspaceXml,
    }),
  });
  if (!res.ok) throw new Error(`Erreur sauvegarde HTTP ${res.status}`);
  return res.json();
}

/**
 * Charge un workspace sauvegardé.
 * Retourne null si aucun workspace n'est trouvé.
 */
export async function loadWorkspace(
  assignmentId: string,
): Promise<string | null> {
  const res = await fetch(`${BASE}/workspace/${assignmentId}`);
  if (!res.ok) return null;
  const data = await res.json();
  return data.workspace_xml ?? null;
}
