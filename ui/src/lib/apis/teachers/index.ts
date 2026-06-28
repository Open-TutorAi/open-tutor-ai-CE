import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface TeacherAvailability {
	teacher_id: string;
	status: 'available' | 'busy' | 'offline';
	office_hours_start: string | null;
	office_hours_end: string | null;
	updated_at: string | null;
}

export const getTeacherAvailability = async (
	token: string,
	teacherId: string
): Promise<TeacherAvailability> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/teachers/availability/${teacherId}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});
	if (error) throw error;
	return res;
};

export const updateTeacherAvailability = async (
	token: string,
	status: string,
	officeHoursStart?: string | null,
	officeHoursEnd?: string | null
): Promise<TeacherAvailability> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/teachers/availability`, {
		method: 'PUT',
		headers: {
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			status,
			office_hours_start: officeHoursStart ?? null,
			office_hours_end: officeHoursEnd ?? null
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});
	if (error) throw error;
	return res;
};
