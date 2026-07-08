// src/lib/apis/classrooms/index.ts

import { TUTOR_BASE_URL } from '$lib/constants';
import type {
	ClassroomCreate,
	ClassroomDetail,
	ClassroomOut,
	ClassroomUpdate,
	EnrolledClassroomOut,
	StudentOut,
	AddStudentRequest,
	AddStudentResponse,
	RemoveStudentResponse,
	ImportResult,
	InviteCreate,
	InviteOut,
	InviteRedeemResult
} from '$lib/types/classroom';
import { ForbiddenError, NotFoundError } from '../errors';


const BASE_URL = `${TUTOR_BASE_URL}/api/classrooms`;

const request = async <T>(token: string, path: string, options: RequestInit = {}): Promise<T> => {
	const res = await fetch(`${BASE_URL}${path}`, {
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

export const ClassroomsAPI = {
	// --- Classroom CRUD ---

	create: (token: string, data: ClassroomCreate): Promise<ClassroomOut> =>
		request(token, '', { method: 'POST', body: JSON.stringify(data) }),

	list: (token: string): Promise<ClassroomOut[]> => request(token, ''),

	/**
	 * List classrooms the current user is enrolled in as a student,
	 * each flagged with an active_session_id if a session is currently open.
	 * GET /api/classrooms/enrolled
	 */
	listEnrolled: (token: string): Promise<EnrolledClassroomOut[]> => request(token, '/enrolled'),

	getDetail: (token: string, id: string): Promise<ClassroomDetail> => request(token, `/${id}`),

	update: (token: string, id: string, data: ClassroomUpdate): Promise<ClassroomOut> =>
		request(token, `/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

	delete: (token: string, id: string): Promise<{ message: string }> =>
		request(token, `/${id}`, { method: 'DELETE' }),

	// --- Student management ---

	/**
	 * List all students enrolled in a classroom
	 * GET /api/classrooms/{classroom_id}/students
	 */
	listStudents: (token: string, classroomId: string): Promise<StudentOut[]> =>
		request(token, `/${classroomId}/students`),

	/**
	 * Enroll a student in a classroom by email
	 * POST /api/classrooms/{classroom_id}/students
	 */
	addStudent: (token: string, classroomId: string, email: string): Promise<AddStudentResponse> =>
		request(token, `/${classroomId}/students`, {
			method: 'POST',
			body: JSON.stringify({ email } as AddStudentRequest)
		}),

	/**
	 * Unenroll a student from a classroom
	 * DELETE /api/classrooms/{classroom_id}/students/{student_id}
	 */
	removeStudent: (
		token: string,
		classroomId: string,
		studentId: string
	): Promise<RemoveStudentResponse> =>
		request(token, `/${classroomId}/students/${studentId}`, {
			method: 'DELETE'
		}),

	/**
	 * Import students via CSV file upload (columns: email, name, password)
	 * POST /api/classrooms/{classroom_id}/import (multipart/form-data)
	 */
	importStudents: async (token: string, classroomId: string, file: File): Promise<ImportResult> => {
		const form = new FormData();
		form.append('file', file, file.name);
		const res = await fetch(`${BASE_URL}/${classroomId}/import`, {
			method: 'POST',
			headers: { Authorization: `Bearer ${token}` },
			body: form
		});

		if (res.status === 403) throw new ForbiddenError();
		if (res.status === 404) throw new NotFoundError();
		if (!res.ok) throw await res.json().catch(() => ({ detail: res.statusText }));
		return res.json();
	},

	/**
	 * Create a join code for a classroom
	 * POST /api/classrooms/{classroom_id}/invites
	 */
	createInvite: (token: string, classroomId: string, data: InviteCreate = {}): Promise<InviteOut> =>
		request(token, `/${classroomId}/invites`, { method: 'POST', body: JSON.stringify(data) }),

	/**
	 * Redeem a join code, enrolling the current user in its classroom
	 * POST /api/classrooms/invites/{code}/redeem
	 */
	redeemInvite: (token: string, code: string): Promise<InviteRedeemResult> =>
		request(token, `/invites/${code}/redeem`, { method: 'POST' })
};
