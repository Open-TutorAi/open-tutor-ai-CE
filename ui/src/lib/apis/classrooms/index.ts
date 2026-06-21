import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface Classroom {
    id: string;
    teacher_id: string;
    name: string;
    description: string | null;
    subject: string | null;
    is_active: boolean;
    created_at: string;
}

async function apiFetch<T>(url: string, token: string, options: RequestInit = {}): Promise<T> {
    const res = await fetch(url, {
        ...options,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...(options.headers ?? {}) }
    });
    if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err?.detail ?? `HTTP ${res.status}`); }
    return res.json();
}

export const getClassrooms = (token: string): Promise<Classroom[]> =>
    apiFetch(`${TUTOR_API_BASE_URL}/classrooms`, token);

export const createClassroom = (token: string, data: { name: string; description?: string; subject?: string }): Promise<Classroom> =>
    apiFetch(`${TUTOR_API_BASE_URL}/classrooms`, token, { method: 'POST', body: JSON.stringify(data) });

export const getClassroom = (token: string, id: string): Promise<Classroom> =>
    apiFetch(`${TUTOR_API_BASE_URL}/classrooms/${id}`, token);

export const enrollStudent = (token: string, classroomId: string, studentId: string): Promise<any> =>
    apiFetch(`${TUTOR_API_BASE_URL}/classrooms/${classroomId}/enroll`, token, {
        method: 'POST', body: JSON.stringify({ student_id: studentId })
    });

export const getClassroomStudents = (token: string, classroomId: string): Promise<{ student_id: string; name: string; email: string | null; enrolled_at: string }[]> =>
    apiFetch(`${TUTOR_API_BASE_URL}/classrooms/${classroomId}/students`, token);

export const unenrollStudent = (token: string, classroomId: string, studentId: string): Promise<void> =>
    apiFetch(`${TUTOR_API_BASE_URL}/classrooms/${classroomId}/students/${studentId}`, token, { method: 'DELETE' });
