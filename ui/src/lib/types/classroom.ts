// src/lib/types/classroom.ts


export type PresenceStatus = 'PRESENT' | 'ABSENT' | 'LATE';

export interface ClassroomCreate {
	name: string;
	subject?: string;
	course?: string;
	objectives?: string;
	level?: string;
	description?: string;
}

export interface ClassroomUpdate {
	name?: string;
	subject?: string;
	course?: string;
	objectives?: string;
	level?: string;
	description?: string;
}

export interface ClassroomOut {
	id: string;
	name: string;
	subject?: string;
	course?: string;
	objectives?: string;
	level?: string;
	description?: string;
	created_at: string;
	owner_id: string;
	student_count: number;
}

export interface ActivityItem {
	type: string;
	title: string;
	date: string;
}

export interface ClassroomDetail extends ClassroomOut {
	objectives_list: string[];
	recent_activity: ActivityItem[];
	join_code?: string | null;
}

export interface EnrolledClassroomOut extends ClassroomOut {
	active_session_id?: string | null;
}

export interface SessionOut {
	id: string;
	classroom_id: string;
	scheduled_at: string;
	subject?: string;
	objectives?: string | null;
	auto_recorded: boolean;
	ended_at?: string | null;
}

export interface SessionSummary extends SessionOut {
	present_count: number;
	absent_count: number;
	late_count: number;
}

export interface PresenceOut {
	id: string;
	student_id: string;
	student_name: string;
	status: PresenceStatus;
	recorded_at: string;
}

export interface AttendanceStats {
	avg_rate: number;
	sessions_count: number;
	total_absences: number;
	total_lates: number;
}

export interface StudentHistory {
	student_id: string;
	rate: number;
	presences: number;
	absences: number;
	lates: number;
	last_10: PresenceStatus[];
}

// --- Student management types ---

export interface StudentOut {
	id: string;
	name: string;
	email: string;
	enrolled_at: string;
	profile_image_url?: string | null;
}

export interface AddStudentRequest {
	email: string;
}

export interface AddStudentResponse {
	student_id: string;
	student_name: string;
	student_email: string;
}

export interface RemoveStudentResponse {
	status: string;
}

export interface ImportRowReport {
	row_number: number;
	email?: string;
	name?: string;
	created: boolean;
	enrolled: boolean;
	error?: string;
}

export interface ImportResult {
	created: number;
	enrolled: number;
	skipped: number;
	rows: ImportRowReport[];
}

export interface InviteCreate {
	expires_at?: string;
	max_uses?: number;
}

export interface InviteOut {
	id: string;
	code: string;
	classroom_id: string;
	created_by: string;
	created_at: string;
	expires_at?: string;
	max_uses?: number;
	uses: number;
}

export interface InviteRedeemResult {
	student_id: string;
	enrolled: boolean;
}

// --- Announcements (classroom stream) ---

export interface AnnouncementOut {
	id: string;
	classroom_id: string;
	author_id: string;
	author_name?: string;
	content: string;
	created_at: string;
}

export interface AnnouncementCreate {
	content: string;
}
