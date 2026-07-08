// src/lib/apis/announcements/index.ts

import { TUTOR_BASE_URL } from '$lib/constants';
import type { AnnouncementOut } from '$lib/types/classroom';
import { ForbiddenError, NotFoundError } from '../errors';

const BASE_URL = `${TUTOR_BASE_URL}/api`;


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

export const AnnouncementsAPI = {
	/**
	 * List a classroom's announcement stream (teacher or enrolled student)
	 * GET /api/classrooms/{classroom_id}/announcements
	 */
	list: (token: string, classroomId: string): Promise<AnnouncementOut[]> =>
		request(token, `/classrooms/${classroomId}/announcements`),

	/**
	 * Post an announcement (teacher only)
	 * POST /api/classrooms/{classroom_id}/announcements
	 */
	create: (token: string, classroomId: string, content: string): Promise<AnnouncementOut> =>
		request(token, `/classrooms/${classroomId}/announcements`, {
			method: 'POST',
			body: JSON.stringify({ content })
		}),

	/**
	 * Delete an announcement (teacher only)
	 * DELETE /api/announcements/{announcement_id}
	 */
	delete: (token: string, announcementId: string): Promise<{ status: string }> =>
		request(token, `/announcements/${announcementId}`, { method: 'DELETE' })
};
