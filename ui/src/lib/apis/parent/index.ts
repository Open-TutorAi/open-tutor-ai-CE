import { TUTOR_API_BASE_URL } from '$lib/constants';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ParentSupportCreateRequest {
	student_id: string; title: string; short_description?: string;
	subject?: string; custom_subject?: string; learning_objective?: string;
	learning_type?: string; level?: string; content_language?: string;
	estimated_duration?: string; keywords?: string[]; start_date?: string;
	end_date?: string; parent_message?: string;
}

export interface ParentSupportResponse {
	id: string; user_id: string; title: string; short_description?: string;
	subject?: string; learning_objective?: string; learning_type?: string;
	level?: string; content_language?: string; estimated_duration?: string;
	keywords?: string[]; status: string; created_at: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

async function apiFetch<T>(url: string, token: string, options: RequestInit = {}): Promise<T> {
	const res = await fetch(url, {
		...options,
		headers: { Accept: 'application/json', 'Content-Type': 'application/json', authorization: `Bearer ${token}`, ...(options.headers ?? {}) },
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
		throw new Error(err.detail ?? 'Erreur API');
	}
	return res.json();
}

// ── Soutiens ──────────────────────────────────────────────────────────────────

export const createParentSupport = (token: string, data: ParentSupportCreateRequest) =>
	apiFetch<ParentSupportResponse>(`${TUTOR_API_BASE_URL}/parent/supports/create`, token, { method: 'POST', body: JSON.stringify(data) });

export const listChildSupports = (token: string, studentId: string) =>
	apiFetch<ParentSupportResponse[]>(`${TUTOR_API_BASE_URL}/parent/supports/list/${studentId}`, token);

export const uploadParentSupportFile = async (token: string, supportId: string, studentId: string, file: File) => {
	const form = new FormData();
	form.append('support_id', supportId); form.append('student_id', studentId); form.append('file', file);
	const res = await fetch(`${TUTOR_API_BASE_URL}/parent/supports/upload-file`, { method: 'POST', headers: { authorization: `Bearer ${token}` }, body: form });
	if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? 'Erreur upload');
	return res.json();
};

// ── Dashboard ─────────────────────────────────────────────────────────────────

export const getDashboard = (token: string, studentId: string) =>
	apiFetch<any>(`${TUTOR_API_BASE_URL}/parent/dashboard/${studentId}`, token);

// ── Évaluations ───────────────────────────────────────────────────────────────

export const getEvaluations = (token: string, studentId: string, matiere?: string) =>
	apiFetch<any>(`${TUTOR_API_BASE_URL}/parent/evaluations/${studentId}${matiere ? `?matiere=${matiere}` : ''}`, token);

// ── Sessions IA ───────────────────────────────────────────────────────────────

export const getSessions = (token: string, studentId: string, matiere?: string) =>
	apiFetch<any>(`${TUTOR_API_BASE_URL}/parent/sessions/${studentId}${matiere ? `?matiere=${matiere}` : ''}`, token);

// ── Notifications ─────────────────────────────────────────────────────────────

export const getNotifications = (token: string) =>
	apiFetch<any>(`${TUTOR_API_BASE_URL}/parent/notifications`, token);

export const marquerLue = (token: string, notifId: string) =>
	apiFetch<any>(`${TUTOR_API_BASE_URL}/parent/notifications/${notifId}/lire`, token, { method: 'PATCH', body: '{}' });

export const getChildSupportDetail = (token: string, supportId: string) =>
	apiFetch<any>(`${TUTOR_API_BASE_URL}/parent/supports/detail/${supportId}`, token);

export const linkChatToSupport = (token: string, supportId: string, chatId: string) =>
	apiFetch<any>(`${TUTOR_API_BASE_URL}/parent/supports/link-chat/${supportId}?chat_id=${chatId}`, token, { method: 'PATCH', body: '{}' });