import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface ClassMaterial {
	id: string;
	classroom_id: string;
	file_id: string;
	title: string;
	description?: string | null;
	uploaded_by: string;
	created_at?: string | null;
	filename: string | null;
	content_type: string | null;
	size: number | null;
	class_name?: string | null;
}

export interface AssignmentTemplate {
	id: string;
	owner_teacher_id: string;
	title: string;
	instructions?: string | null;
	attachment_id?: string | null;
	created_at?: string | null;
}

export interface Library {
	materials: ClassMaterial[];
	templates: AssignmentTemplate[];
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

// ── class materials ───────────────────────────────────────────────────────────

export const getClassMaterials = (token: string, id: string): Promise<ClassMaterial[]> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/resources`, 'GET', token);

export const uploadMaterial = async (
	token: string,
	id: string,
	file: File,
	title: string,
	description = ''
): Promise<ClassMaterial> => {
	const form = new FormData();
	form.append('file', file);
	form.append('title', title);
	form.append('description', description);
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/classrooms/${id}/resources`, {
		method: 'POST',
		headers: { Accept: 'application/json', authorization: `Bearer ${token}` },
		body: form
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

export const deleteMaterial = (token: string, id: string, rid: string) =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/resources/${rid}`, 'DELETE', token);

// Download endpoint — returned as a Blob (auth header required, so not a plain href).
export const downloadMaterial = async (token: string, id: string, rid: string): Promise<Blob> => {
	const res = await fetch(`${TUTOR_API_BASE_URL}/classrooms/${id}/resources/${rid}/content`, {
		method: 'GET',
		headers: { authorization: `Bearer ${token}` }
	});
	if (!res.ok) throw await res.json().catch(() => 'Download failed');
	return res.blob();
};

// ── flat library + templates ──────────────────────────────────────────────────

export const getLibrary = (token: string): Promise<Library> =>
	_send(`${TUTOR_API_BASE_URL}/resources`, 'GET', token);

export const getTemplates = (token: string): Promise<AssignmentTemplate[]> =>
	_send(`${TUTOR_API_BASE_URL}/assignment-templates`, 'GET', token);

export const saveTemplate = (
	token: string,
	title: string,
	instructions = '',
	attachmentId?: string
): Promise<AssignmentTemplate> =>
	_send(`${TUTOR_API_BASE_URL}/assignment-templates`, 'POST', token, {
		title,
		instructions,
		attachment_id: attachmentId
	});

export const deleteTemplate = (token: string, tid: string) =>
	_send(`${TUTOR_API_BASE_URL}/assignment-templates/${tid}`, 'DELETE', token);

// ── create assignment from a template (E7) ────────────────────────────────────

export const createAssignmentFromTemplate = (
	token: string,
	id: string,
	templateId: string,
	dueDate?: string
) =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/assignments/from-template`, 'POST', token, {
		template_id: templateId,
		due_date: dueDate
	});
