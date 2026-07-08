import { TUTOR_BASE_URL } from '$lib/constants';
import type {
	AttendanceStats,
	PresenceOut,
	PresenceStatus,
	SessionOut,
	SessionSummary,
	StudentHistory
} from '$lib/types/classroom';
import { ForbiddenError, NotFoundError } from '../errors';


const request = async <T>(token: string, url: string, options: RequestInit = {}): Promise<T> => {
	const res = await fetch(url, {
		...options,
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`,
			...(options.headers ?? {})
		}
	});

	if (res.status === 403) throw new ForbiddenError();
	if (res.status === 404) throw new NotFoundError();
	if (!res.ok) throw await res.json().catch(() => ({ detail: res.statusText }));

	return res.json();
};

export const SessionsAPI = {
	startSession: (
		token: string,
		classroomId: string,
		subject: string,
		objectives?: string
	): Promise<SessionOut> =>
		request(token, `${TUTOR_BASE_URL}/api/classrooms/${classroomId}/sessions`, {
			method: 'POST',
			body: JSON.stringify({
				scheduled_at: new Date().toISOString(),
				subject,
				objectives: objectives || undefined
			})
		}),

	getPresences: (token: string, sessionId: string): Promise<PresenceOut[]> =>
		request(token, `${TUTOR_BASE_URL}/api/sessions/${sessionId}/presences`),

	updatePresence: (
		token: string,
		presenceId: string,
		status: PresenceStatus
	): Promise<PresenceOut> =>
		request(token, `${TUTOR_BASE_URL}/api/presences/${presenceId}`, {
			method: 'PATCH',
			body: JSON.stringify({ status })
		}),

	getStats: (token: string, classroomId: string): Promise<AttendanceStats> =>
		request(token, `${TUTOR_BASE_URL}/api/classrooms/${classroomId}/attendance-stats`),

	getStudentHistory: (
		token: string,
		classroomId: string,
		studentId: string
	): Promise<StudentHistory> =>
		request(token, `${TUTOR_BASE_URL}/api/classrooms/${classroomId}/students/${studentId}/history`),

	getSessions: (token: string, classroomId: string): Promise<SessionSummary[]> =>
		request(token, `${TUTOR_BASE_URL}/api/classrooms/${classroomId}/sessions`),

	/**
	 * Teacher-only: close a session so students can no longer join it.
	 * POST /api/sessions/{session_id}/end
	 */
	endSession: (token: string, sessionId: string): Promise<SessionOut> =>
		request(token, `${TUTOR_BASE_URL}/api/sessions/${sessionId}/end`, { method: 'POST' }),

	/**
	 * Student-only: enter an open session, marking the caller present.
	 * POST /api/sessions/{session_id}/join
	 */
	joinSession: (token: string, sessionId: string): Promise<PresenceOut> =>
		request(token, `${TUTOR_BASE_URL}/api/sessions/${sessionId}/join`, { method: 'POST' }),

	/**
	 * Teacher-only: permanently delete an ended session and its presence records.
	 * DELETE /api/sessions/{session_id}
	 */
	deleteSession: (token: string, sessionId: string): Promise<{ status: string }> =>
		request(token, `${TUTOR_BASE_URL}/api/sessions/${sessionId}`, { method: 'DELETE' })
};
