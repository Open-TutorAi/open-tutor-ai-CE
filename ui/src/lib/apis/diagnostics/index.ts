import { TUTOR_API_BASE_URL } from '$lib/constants';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface DiagnosticQuestion {
	id: number;
	question: string;
	choices: string[];
	correct_answer?: string;
	explanation?: string;
}

export interface DiagnosticAnswer {
	question_id: number;
	answer: string;
}

export interface DiagnosticResult {
	id: string;
	support_id: string;
	user_id: string;
	questions: DiagnosticQuestion[] | null;
	answers: DiagnosticAnswer[] | null;
	score: number | null;
	determined_level: string | null;
	status: 'pending' | 'completed';
	created_at: string;
	updated_at?: string;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const generateDiagnostic = async (
	token: string,
	supportId: string,
	modelId: string
): Promise<DiagnosticResult> => {
	let error = null;

	const res = await fetch(`${TUTOR_API_BASE_URL}/diagnostics/generate`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ support_id: supportId, model_id: modelId })
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});

	if (error) throw error;
	return res;
};

export const submitDiagnostic = async (
	token: string,
	diagnosticId: string,
	answers: DiagnosticAnswer[]
): Promise<DiagnosticResult> => {
	let error = null;

	const res = await fetch(`${TUTOR_API_BASE_URL}/diagnostics/${diagnosticId}/submit`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ answers })
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});

	if (error) throw error;
	return res;
};

export const getDiagnosticById = async (
	token: string,
	diagnosticId: string
): Promise<DiagnosticResult> => {
	let error = null;

	const res = await fetch(`${TUTOR_API_BASE_URL}/diagnostics/${diagnosticId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});

	if (error) throw error;
	return res;
};

export const getDiagnosticBySupport = async (
	token: string,
	supportId: string
): Promise<DiagnosticResult | null> => {
	let error = null;

	const res = await fetch(`${TUTOR_API_BASE_URL}/diagnostics/by-support/${supportId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});

	if (error) throw error;
	return res;
};
