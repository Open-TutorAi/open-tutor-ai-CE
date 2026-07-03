import { TUTOR_API_BASE_URL } from '$lib/constants';

export type FocusSettings = {
	work_minutes: number;
	break_minutes: number;
	long_break_minutes: number;
	long_break_interval: number;
};

export async function postFocusSession(
	token: string,
	duration_minutes: number,
	session_type: 'work' | 'break' = 'work'
): Promise<{ id: string; status: string }> {
	const res = await fetch(`${TUTOR_API_BASE_URL}/focus/session`, {
		method: 'POST',
		headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
		body: JSON.stringify({ duration_minutes, session_type })
	});
	if (!res.ok) throw new Error('Failed to record focus session');
	return res.json();
}

export async function getFocusSettings(token: string): Promise<FocusSettings> {
	const res = await fetch(`${TUTOR_API_BASE_URL}/focus/settings`, {
		method: 'GET',
		headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
	});
	if (!res.ok) throw new Error('Failed to fetch focus settings');
	return res.json();
}

export async function updateFocusSettings(
	token: string,
	settings: FocusSettings
): Promise<FocusSettings> {
	const res = await fetch(`${TUTOR_API_BASE_URL}/focus/settings`, {
		method: 'PUT',
		headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
		body: JSON.stringify(settings)
	});
	if (!res.ok) throw new Error('Failed to update focus settings');
	return res.json();
}
