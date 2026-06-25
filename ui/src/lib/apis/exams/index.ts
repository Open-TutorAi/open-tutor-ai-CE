import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface ExamConfig {
	assignment_id: string;
	time_limit_minutes: number | null;
	max_violations: number | null;
	on_violation: 'warn' | 'flag' | 'auto_submit';
	require_fullscreen: boolean;
}

export interface ExamSession {
	id: string;
	assignment_id: string;
	student_id: string;
	status: 'in_progress' | 'submitted' | 'terminated';
	started_at: string | null;
	submitted_at: string | null;
	violation_count: number;
}

export interface ExamInfo {
	is_exam: boolean;
	config: ExamConfig | null;
	session: ExamSession | null;
}

export interface ExamViolation {
	id: string;
	session_id: string;
	student_id: string;
	type: string;
	created_at: string;
}

export interface ProctorRow {
	student_id: string;
	name: string | null;
	email: string | null;
	status: 'not_started' | 'in_progress' | 'submitted' | 'terminated';
	violation_count: number;
	violations: ExamViolation[];
}

const _send = async (url: string, method: string, token: string, body?: any) => {
	let error = null;
	const res = await fetch(url, {
		method,
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		...(body !== undefined ? { body: JSON.stringify(body) } : {})
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err.detail ?? err;
			return null;
		});
	if (error) throw error;
	return res;
};

// ── teacher: configuration + proctoring ──────────────────────────────────────

export const configureExam = (
	token: string,
	classId: string,
	assignmentId: string,
	cfg: Partial<ExamConfig>
): Promise<ExamConfig> =>
	_send(
		`${TUTOR_API_BASE_URL}/classrooms/${classId}/assignments/${assignmentId}/exam`,
		'POST',
		token,
		cfg
	);

export const unsetExam = (token: string, classId: string, assignmentId: string) =>
	_send(
		`${TUTOR_API_BASE_URL}/classrooms/${classId}/assignments/${assignmentId}/exam`,
		'DELETE',
		token
	);

export const getProctoring = (
	token: string,
	classId: string,
	assignmentId: string
): Promise<ProctorRow[]> =>
	_send(
		`${TUTOR_API_BASE_URL}/classrooms/${classId}/assignments/${assignmentId}/proctoring`,
		'GET',
		token
	);

// ── student / shared: exam lifecycle ─────────────────────────────────────────

export const getExam = (token: string, assignmentId: string): Promise<ExamInfo> =>
	_send(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/exam`, 'GET', token);

export const startExam = (
	token: string,
	assignmentId: string
): Promise<{ config: ExamConfig; session: ExamSession }> =>
	_send(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/exam/start`, 'POST', token);

export const submitExam = (token: string, assignmentId: string): Promise<ExamSession> =>
	_send(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/exam/submit`, 'POST', token);

export const reportViolation = (
	token: string,
	assignmentId: string,
	type: string
): Promise<{ action: string; grace_seconds: number; session: ExamSession }> =>
	_send(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/exam/violation`, 'POST', token, {
		type
	});

export const terminateExam = (
	token: string,
	assignmentId: string,
	reason: string
): Promise<{ session: ExamSession }> =>
	_send(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/exam/terminate`, 'POST', token, {
		reason
	});
