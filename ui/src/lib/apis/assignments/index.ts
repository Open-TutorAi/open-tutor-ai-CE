import { TUTOR_API_BASE_URL } from '$lib/constants';

// Types
export interface AssignmentCreateRequest {
	title: string;
	description?: string;
	rubric: string;
	due_date?: string;
}

export interface AssignmentResponse {
	id: string;
	user_id: string;
	title: string;
	description?: string;
	rubric: string;
	due_date?: string;
	created_at: string;
	updated_at?: string;
}

export interface SubmissionResponse {
	id: string;
	assignment_id: string;
	user_id: string;
	filename: string;
	file_size?: number;
	extracted_text?: string;
	ai_score?: number;
	ai_feedback?: string;
	teacher_score?: number;
	teacher_feedback?: string;
	status: string;
	created_at: string;
	updated_at?: string;
}

export interface FinalizeGradeRequest {
	score: number;
	feedback: string;
}

async function handle(res: Response) {
	if (!res.ok) throw (await res.json()).detail;
	return res.json();
}

/**
 * Create a new assignment (teacher only)
 */
export const createAssignment = async (
	token: string,
	data: AssignmentCreateRequest
): Promise<AssignmentResponse> => {
	const res = await fetch(`${TUTOR_API_BASE_URL}/assignments`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(data)
	}).then(handle);

	return res;
};

/**
 * List assignments visible to the current user (own assignments for a
 * teacher, all assignments for a student — there is no classroom/roster yet)
 */
export const getAssignments = async (token: string): Promise<AssignmentResponse[]> => {
	const res = await fetch(`${TUTOR_API_BASE_URL}/assignments`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	}).then(handle);

	return res;
};

/**
 * Get a single assignment by ID
 */
export const getAssignmentById = async (
	token: string,
	assignmentId: string
): Promise<AssignmentResponse> => {
	const res = await fetch(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	}).then(handle);

	return res;
};

/**
 * Submit a student's work for an assignment (multipart file upload)
 */
export const submitAssignmentWork = async (
	token: string,
	assignmentId: string,
	file: File
): Promise<SubmissionResponse> => {
	const formData = new FormData();
	formData.append('file', file);

	const res = await fetch(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/submissions`, {
		method: 'POST',
		headers: {
			authorization: `Bearer ${token}`
		},
		body: formData
	}).then(handle);

	return res;
};

/**
 * List all submissions for an assignment (teacher only, must own the assignment)
 */
export const getSubmissions = async (
	token: string,
	assignmentId: string
): Promise<SubmissionResponse[]> => {
	const res = await fetch(`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/submissions`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	}).then(handle);

	return res;
};

/**
 * Get a single submission (the owning student or the owning teacher only)
 */
export const getSubmissionById = async (
	token: string,
	assignmentId: string,
	submissionId: string
): Promise<SubmissionResponse> => {
	const res = await fetch(
		`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/submissions/${submissionId}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				authorization: `Bearer ${token}`
			}
		}
	).then(handle);

	return res;
};

/**
 * Request an AI-generated draft score and feedback for a submission (teacher only)
 */
export const requestAiGrade = async (
	token: string,
	assignmentId: string,
	submissionId: string
): Promise<SubmissionResponse> => {
	const res = await fetch(
		`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/submissions/${submissionId}/ai-grade`,
		{
			method: 'POST',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				authorization: `Bearer ${token}`
			}
		}
	).then(handle);

	return res;
};

/**
 * Finalize a submission's grade with the teacher's own score and feedback
 */
export const finalizeGrade = async (
	token: string,
	assignmentId: string,
	submissionId: string,
	data: FinalizeGradeRequest
): Promise<SubmissionResponse> => {
	const res = await fetch(
		`${TUTOR_API_BASE_URL}/assignments/${assignmentId}/submissions/${submissionId}/finalize`,
		{
			method: 'PUT',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				authorization: `Bearer ${token}`
			},
			body: JSON.stringify(data)
		}
	).then(handle);

	return res;
};
