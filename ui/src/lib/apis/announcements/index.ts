import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface Announcement {
	id: string;
	teacher_id: string;
	title: string;
	content: string;
	priority: 'normal' | 'important' | 'urgent';
	is_published: boolean;
	target_type: string;
	is_read: boolean;
	created_at: string;
	updated_at: string;
}

// ── Teacher ───────────────────────────────────────────────────────────────────

export const getMyAnnouncements = async (token: string): Promise<Announcement[]> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/announcements/mine`, {
		headers: { authorization: `Bearer ${token}` }
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => { error = err.detail; return null; });
	if (error) throw error;
	return res;
};

export const createAnnouncement = async (
	token: string,
	title: string,
	content: string,
	priority: string = 'normal',
	targetType: string = 'all'
): Promise<Announcement> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/announcements`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json', authorization: `Bearer ${token}` },
		body: JSON.stringify({ title, content, priority, target_type: targetType })
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => { error = err.detail; return null; });
	if (error) throw error;
	return res;
};

export const updateAnnouncement = async (
	token: string,
	id: string,
	fields: Partial<{ title: string; content: string; priority: string; target_type: string }>
): Promise<Announcement> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/announcements/${id}`, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json', authorization: `Bearer ${token}` },
		body: JSON.stringify(fields)
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => { error = err.detail; return null; });
	if (error) throw error;
	return res;
};

export const publishAnnouncement = async (
	token: string,
	id: string
): Promise<Announcement> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/announcements/${id}/publish`, {
		method: 'POST',
		headers: { authorization: `Bearer ${token}` }
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => { error = err.detail; return null; });
	if (error) throw error;
	return res;
};

export const unpublishAnnouncement = async (
	token: string,
	id: string
): Promise<Announcement> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/announcements/${id}/unpublish`, {
		method: 'POST',
		headers: { authorization: `Bearer ${token}` }
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => { error = err.detail; return null; });
	if (error) throw error;
	return res;
};

export const deleteAnnouncement = async (
	token: string,
	id: string
): Promise<{ deleted: boolean }> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/announcements/${id}`, {
		method: 'DELETE',
		headers: { authorization: `Bearer ${token}` }
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => { error = err.detail; return null; });
	if (error) throw error;
	return res;
};

// ── Parent ────────────────────────────────────────────────────────────────────

export const getPublishedAnnouncements = async (
	token: string
): Promise<Announcement[]> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/announcements`, {
		headers: { authorization: `Bearer ${token}` }
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => { error = err.detail; return null; });
	if (error) throw error;
	return res;
};

export const markAnnouncementRead = async (
	token: string,
	id: string
): Promise<Announcement> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/announcements/${id}/read`, {
		method: 'POST',
		headers: { authorization: `Bearer ${token}` }
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => { error = err.detail; return null; });
	if (error) throw error;
	return res;
};

export const getUnreadCount = async (token: string): Promise<number> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/announcements/unread-count`, {
		headers: { authorization: `Bearer ${token}` }
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => { error = err.detail; return null; });
	if (error) throw error;
	return res?.unread_count ?? 0;
};
