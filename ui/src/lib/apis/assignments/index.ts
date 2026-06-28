import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface Assignment {
    id: string;
    classroom_id: string;
    teacher_id: string;
    title: string;
    instructions: string | null;
    attachment_url: string | null;
    due_date: string;
    max_score: number;
    created_at: string;
}

export interface Submission {
    id: string;
    assignment_id: string;
    student_id: string;
    content: string | null;
    attachment_url: string | null;
    submitted_at: string | null;
    score: number | null;
    feedback: string | null;
    graded_at: string | null;
    status: 'submitted' | 'late' | 'returned';
}

export interface StatusRow {
    student_id: string;
    status: 'submitted' | 'late' | 'missed' | 'not_submitted' | 'returned';
    submission: Submission | null;
}

async function apiFetch<T>(url: string, token: string, options: RequestInit = {}): Promise<T> {
    const res = await fetch(url, {
        ...options,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...(options.headers ?? {}) }
    });
    if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err?.detail ?? `HTTP ${res.status}`); }
    if (res.status === 204) return undefined as T;
    return res.json();
}

export const getAssignments = (token: string): Promise<Assignment[]> =>
    apiFetch(`${TUTOR_API_BASE_URL}/assignments`, token);

export const getAssignment = (token: string, id: string): Promise<Assignment> =>
    apiFetch(`${TUTOR_API_BASE_URL}/assignments/${id}`, token);

export const createAssignment = (token: string, data: {
    classroom_id: string; title: string; instructions?: string;
    due_date: string; attachment_url?: string; max_score?: number;
}): Promise<Assignment> =>
    apiFetch(`${TUTOR_API_BASE_URL}/assignments`, token, { method: 'POST', body: JSON.stringify(data) });

export const getSubmissions = (token: string, assignmentId: string): Promise<Submission[]> =>
    apiFetch(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/submissions`, token);

export const gradeSubmission = (token: string, assignmentId: string, submissionId: string, data: { score: number; feedback?: string }): Promise<Submission> =>
    apiFetch(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/submissions/${submissionId}/grade`, token, {
        method: 'POST', body: JSON.stringify(data)
    });

export const getStatusTracker = (token: string, assignmentId: string): Promise<StatusRow[]> =>
    apiFetch(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/status`, token);

export const submitAssignment = (token: string, assignmentId: string, data: { content?: string; attachment_url?: string }): Promise<Submission> =>
    apiFetch(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/submit`, token, {
        method: 'POST', body: JSON.stringify(data)
    });

export const getMySubmission = (token: string, assignmentId: string): Promise<Submission | null> =>
    apiFetch(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/my-submission`, token);

export const updateAssignment = (token: string, id: string, data: {
    title?: string; instructions?: string; due_date?: string;
    attachment_url?: string; max_score?: number;
}): Promise<Assignment> =>
    apiFetch(`${TUTOR_API_BASE_URL}/assignments/${id}`, token, { method: 'PUT', body: JSON.stringify(data) });

export const deleteAssignment = (token: string, id: string): Promise<void> =>
    apiFetch(`${TUTOR_API_BASE_URL}/assignments/${id}`, token, { method: 'DELETE' });

export const cancelSubmission = (token: string, assignmentId: string): Promise<void> =>
    apiFetch(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/my-submission`, token, { method: 'DELETE' });
