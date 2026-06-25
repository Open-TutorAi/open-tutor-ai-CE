import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface Assignment {
	id: string;
	classroom_id: string;
	created_by: string;
	title: string;
	instructions?: string | null;
	attachment_id?: string | null;
	attachment_name?: string | null;
	due_date?: string | null;
	created_at?: string | null;
}

export interface AssignmentSummary extends Assignment {
	student_count: number;
	submitted_count: number;
	graded_count: number;
}

export interface Submission {
	id: string;
	assignment_id: string;
	student_id: string;
	content?: string | null;
	attachment_id?: string | null;
	attachment_name?: string | null;
	submitted_at?: string | null;
	is_late: boolean;
	grade?: number | null;
	feedback?: string | null;
	graded_at?: string | null;
	status: string;
}

export type SubmissionStatus = 'pending' | 'submitted' | 'late' | 'missing' | 'graded';

export interface SubmissionRow {
	student_id: string;
	name: string | null;
	email: string | null;
	status: SubmissionStatus;
	submission: Submission | null;
}

export interface AssignmentOverview extends AssignmentSummary {
	submissions: SubmissionRow[];
}

export interface StudentAssignment extends Assignment {
	class_name: string | null;
	status: SubmissionStatus;
	submission: Submission | null;
}

export interface AssignmentCreateRequest {
	title: string;
	instructions?: string;
	attachment_id?: string;
	due_date?: string;
}

const jsonHeaders = (token: string) => ({
	Accept: 'application/json',
	'Content-Type': 'application/json',
	authorization: `Bearer ${token}`
});

const _send = async (url: string, method: string, token: string, body?: any) => {
	let error = null;
	const res = await fetch(url, {
		method,
		headers: jsonHeaders(token),
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

// ── teacher: authoring / grading ──────────────────────────────────────────────

export const getAssignments = (token: string, id: string): Promise<AssignmentSummary[]> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/assignments`, 'GET', token);

export const createAssignment = (
	token: string,
	id: string,
	data: AssignmentCreateRequest
): Promise<AssignmentSummary> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/assignments`, 'POST', token, data);

export const getAssignment = (
	token: string,
	id: string,
	assignmentId: string
): Promise<AssignmentOverview> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/assignments/${assignmentId}`, 'GET', token);

export const deleteAssignment = (token: string, id: string, assignmentId: string) =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/assignments/${assignmentId}`, 'DELETE', token);

export const gradeSubmission = (
	token: string,
	id: string,
	assignmentId: string,
	studentId: string,
	grade: number | null,
	feedback: string
): Promise<Submission> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/assignments/${assignmentId}/grade`, 'POST', token, {
		student_id: studentId,
		grade,
		feedback
	});

// ── student: feed / submission ────────────────────────────────────────────────

export const getMyAssignments = (token: string): Promise<StudentAssignment[]> =>
	_send(`${TUTOR_API_BASE_URL}/assignments`, 'GET', token);

export const getMySubmission = (token: string, assignmentId: string): Promise<Submission | null> =>
	_send(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/submission`, 'GET', token);

export const submitAssignment = (
	token: string,
	assignmentId: string,
	content: string,
	attachmentId?: string
): Promise<Submission> =>
	_send(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/submit`, 'POST', token, {
		content,
		attachment_id: attachmentId
	});

// ── attachment downloads (authed blobs; scoped by class membership) ──────────

const _downloadBlob = async (url: string, token: string): Promise<Blob> => {
	const res = await fetch(url, { method: 'GET', headers: { authorization: `Bearer ${token}` } });
	if (!res.ok) throw await res.json().catch(() => 'Download failed');
	return res.blob();
};

export const downloadAssignmentAttachment = (token: string, assignmentId: string): Promise<Blob> =>
	_downloadBlob(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/attachment`, token);

export const downloadMySubmissionAttachment = (
	token: string,
	assignmentId: string
): Promise<Blob> =>
	_downloadBlob(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/submission/attachment`, token);

export const downloadSubmissionAttachment = (
	token: string,
	classId: string,
	assignmentId: string,
	studentId: string
): Promise<Blob> =>
	_downloadBlob(
		`${TUTOR_API_BASE_URL}/classrooms/${classId}/assignments/${assignmentId}/students/${studentId}/submission/attachment`,
		token
	);
