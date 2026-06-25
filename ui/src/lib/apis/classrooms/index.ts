import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface Classroom {
	id: string;
	teacher_id: string;
	name: string;
	short_description?: string | null;
	subject?: string | null;
	custom_subject?: string | null;
	course?: string | null;
	learning_objective?: string | null;
	competencies?: string | null;
	learning_type?: string | null;
	level?: string | null;
	content_language?: string | null;
	estimated_duration?: string | null;
	keywords?: string[] | null;
	student_count: number;
	created_at?: string | null;
	updated_at?: string | null;
}

export interface ClassroomCreateRequest {
	name: string;
	short_description: string;
	subject: string;
	custom_subject?: string;
	course: string;
	learning_objective: string;
	competencies: string;
	learning_type: string;
	level: string;
	content_language: string;
	estimated_duration: string;
	keywords: string[];
	// Optional teacher settings (schedule + capacity).
	capacity?: number | null;
	term_start?: string | null;
	term_end?: string | null;
	meeting_days?: string[] | null;
}

export interface RosterEntry {
	student_id: string;
	name: string | null;
	email: string | null;
	status: string;
	enrolled_at?: string | null;
}

export interface Invitation {
	id: string;
	classroom_id: string;
	email: string;
	invitee_role: string;
	token: string;
	status: string;
	created_at?: string | null;
	expires_at?: string | null;
}

export interface InviteResult {
	invitation: Invitation;
	join_url: string;
	email_sent: boolean;
}

const jsonHeaders = (token: string) => ({
	Accept: 'application/json',
	'Content-Type': 'application/json',
	authorization: `Bearer ${token}`
});

export const getClassrooms = async (token: string): Promise<Classroom[]> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/classrooms`, {
		method: 'GET',
		headers: jsonHeaders(token)
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

export const createClassroom = async (
	token: string,
	data: ClassroomCreateRequest
): Promise<Classroom> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/classrooms`, {
		method: 'POST',
		headers: jsonHeaders(token),
		body: JSON.stringify(data)
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

export const getClassroom = async (token: string, id: string): Promise<Classroom> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/classrooms/${id}`, {
		method: 'GET',
		headers: jsonHeaders(token)
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

export const deleteClassroom = async (token: string, id: string) => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/classrooms/${id}`, {
		method: 'DELETE',
		headers: jsonHeaders(token)
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

export const getRoster = (token: string, id: string): Promise<RosterEntry[]> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/students`, 'GET', token);

export const enrolStudent = (token: string, id: string, email: string): Promise<RosterEntry> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/students`, 'POST', token, { email });

export const removeStudent = (token: string, id: string, studentId: string) =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/students/${studentId}`, 'DELETE', token);

export const getInvitations = (token: string, id: string): Promise<Invitation[]> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/invitations`, 'GET', token);

export const createInvitation = (
	token: string,
	id: string,
	email: string,
	inviteeRole: 'student' | 'parent' = 'student'
): Promise<InviteResult> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/invitations`, 'POST', token, {
		email,
		invitee_role: inviteeRole
	});

export const acceptInvitation = (token: string, inviteToken: string) =>
	_send(`${TUTOR_API_BASE_URL}/invitations/accept`, 'POST', token, { token: inviteToken });

export interface ClassProgressRow {
	student_id: string;
	name: string | null;
	email: string | null;
	supports_total: number;
	last_active: string | null;
	status: 'active' | 'idle' | 'not_started';
}

export interface SupportItem {
	id: string;
	title: string;
	subject?: string | null;
	level?: string | null;
	status: string;
	updated_at?: string | null;
}

export interface StudentProgress {
	student_id: string;
	name: string | null;
	email: string | null;
	activity: { last_active: string | null; status: string };
	supports: { total: number; by_status: Record<string, number>; items: SupportItem[] };
	engagement: { feedback_positive: number; feedback_negative: number; feedback_total: number };
}

export const getClassProgress = (token: string, id: string): Promise<ClassProgressRow[]> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/progress`, 'GET', token);

export interface DirectoryStudent {
	student_id: string;
	name: string | null;
	email: string | null;
	classes: { id: string; name: string }[];
	supports_total: number;
	last_active: string | null;
	status: 'active' | 'idle' | 'not_started';
	guardians: number;
}

export const getStudentsDirectory = (token: string): Promise<DirectoryStudent[]> =>
	_send(`${TUTOR_API_BASE_URL}/students`, 'GET', token);

export interface MyTeacher {
	teacher_id: string;
	name: string | null;
	email: string | null;
	classes: { id: string; name: string }[];
}

export const getMyTeachers = (token: string): Promise<MyTeacher[]> =>
	_send(`${TUTOR_API_BASE_URL}/my-teachers`, 'GET', token);

export interface MonitorState {
	student_id: string;
	enabled: boolean;
}

export interface MonitorSetResult extends MonitorState {
	state: 'on' | 'off';
	delivered: boolean;
}

export interface ClassMonitorResult {
	state: 'on' | 'off';
	enabled: boolean;
	reached: number;
	total: number;
}

export const getMonitor = (token: string, id: string, studentId: string): Promise<MonitorState> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/students/${studentId}/monitor`, 'GET', token);

// The calling user's own aggregate screen-lock state — read on (re)connect to re-apply
// a lock set while offline (the durable counterpart of the live `monitor:set` event).
export const getMyMonitor = (token: string): Promise<{ enabled: boolean }> =>
	_send(`${TUTOR_API_BASE_URL}/me/monitor`, 'GET', token);

// Tab-away telemetry: a locked student reports leaving (`away:true`) or returning
// (`away:false`) to the screen; the server notifies the locking teacher(s) live.
export const reportPresence = (
	token: string,
	away: boolean
): Promise<{ away: boolean; notified: number }> =>
	_send(`${TUTOR_API_BASE_URL}/me/monitor/presence`, 'POST', token, { away });

export interface AwayEvent {
	id: string;
	classroom_id: string;
	student_id: string;
	away: boolean;
	created_at: string;
	student_name: string | null;
	student_email: string | null;
}

// Durable tab-away history for a class (newest first) — reviewable even if the
// teacher wasn't watching the Control tab when events happened live.
export const getAwayLog = (token: string, id: string): Promise<AwayEvent[]> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/monitor/away-log`, 'GET', token);

export const clearAwayLog = (token: string, id: string): Promise<{ removed: number }> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/monitor/away-log`, 'DELETE', token);

export const setMonitor = (
	token: string,
	id: string,
	studentId: string,
	enabled: boolean
): Promise<MonitorSetResult> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/students/${studentId}/monitor`, 'POST', token, {
		enabled
	});

export const setClassMonitor = (
	token: string,
	id: string,
	enabled: boolean
): Promise<ClassMonitorResult> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/monitor`, 'POST', token, { enabled });

// Ids + live online status only; names are resolved client-side from the loaded
// roster, so this stays cheap enough to poll frequently.
export interface StudentPresence {
	student_id: string;
	online: boolean;
}

export interface ClassPresence {
	students: StudentPresence[];
	online: number;
	total: number;
}

// Live online/offline status for the class roster — powers the "X/Y online now"
// indicator and its dropdown in the Control tab.
export const getClassPresence = (token: string, id: string): Promise<ClassPresence> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/presence`, 'GET', token);

export const getStudentProgress = (
	token: string,
	id: string,
	studentId: string
): Promise<StudentProgress> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/students/${studentId}/progress`, 'GET', token);

export interface GuardianLink {
	id: string;
	student_user_id: string;
	parent_user_id: string | null;
	invited_email: string | null;
	status: 'pending' | 'active';
	created_at?: string | null;
}

export interface GuardianInviteResult {
	guardian: GuardianLink;
	status: 'active' | 'pending';
	join_url?: string;
	email_sent?: boolean;
}

export const getGuardians = (
	token: string,
	id: string,
	studentId: string
): Promise<GuardianLink[]> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/students/${studentId}/guardians`, 'GET', token);

export const inviteGuardian = (
	token: string,
	id: string,
	studentId: string,
	email: string
): Promise<GuardianInviteResult> =>
	_send(`${TUTOR_API_BASE_URL}/classrooms/${id}/students/${studentId}/guardians`, 'POST', token, {
		email
	});
