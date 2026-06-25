import { TUTOR_API_BASE_URL } from '$lib/constants';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Metriques {
	engagement: number;
	comprehension: number;
	autonomie: number;
}

export interface SessionSummary {
	id: string;
	matiere: string;
	duree_minutes: number;
	quality_score: number;
	alerte_difficulte: boolean;
	themes: string[];
	questions: string[];
	resume?: string;
	metriques?: Metriques;
	statut: string;
}

export interface SessionStats {
	total: number;
	avec_alerte: number;
	score_moyen: number;
}

export interface SessionListResponse {
	sessions: SessionSummary[];
	stats: SessionStats;
}

export interface SessionDetail extends SessionSummary {}

export interface TranscriptResponse {
	session_id: string;
	transcript_text: string;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const getIASessions = async (
	token: string,
	childId: string,
	subject?: string
): Promise<SessionListResponse | null> => {
	const params = new URLSearchParams({ child_id: childId });
	if (subject) params.append('subject', subject);

	const res = await fetch(`${TUTOR_API_BASE_URL}/ia-sessions/?${params}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) return null;
	return res.json();
};

export const getIASessionDetail = async (
	token: string,
	sessionId: string,
	childId: string
): Promise<SessionDetail | null> => {
	const params = new URLSearchParams({ child_id: childId });
	const res = await fetch(`${TUTOR_API_BASE_URL}/ia-sessions/${sessionId}/detail?${params}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) return null;
	return res.json();
};

export const getIASessionTranscript = async (
	token: string,
	sessionId: string,
	childId: string
): Promise<TranscriptResponse | null> => {
	const params = new URLSearchParams({ child_id: childId });
	const res = await fetch(`${TUTOR_API_BASE_URL}/ia-sessions/${sessionId}/transcript?${params}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) return null;
	return res.json();
};
