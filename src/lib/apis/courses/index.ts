// src/lib/apis/courses/index.ts — FULL REPLACEMENT

import { TUTOR_API_BASE_URL } from '$lib/constants';

// ── Types ──────────────────────────────────────────────────────────────────

export interface CourseFile {
	id: string;
	name: string;
	size_kb: number;
	type: string;
}

export interface SectionDetail {
	id: string;
	title: string;
	status: 'not-started' | 'in-progress' | 'completed';
}

export interface ChapterDetail {
	id: string;
	title: string;
	sections: SectionDetail[];
}

export interface CourseDetailResponse {
	id: string;
	title: string;
	language: string;
	category: string | null;
	level: string;
	teacher_name: string;
	objectives: string;
	welcome_message?: string;
	files: CourseFile[];
	chapters: ChapterDetail[];
	enrolled_at: string;
	status: string;
	progress_percentage: number;
	chat_id: string | null;
}

export interface SectionProgressResponse {
	chapter_id: string;
	section_id: string;
	status: string;
	completed_at: string | null;
}

export interface ProgressSummaryResponse {
	total_sections: number;
	completed_sections: number;
	progress_percentage: number;
	sections: SectionProgressResponse[];
	chat_id: string | null;
}

// ── Helpers ────────────────────────────────────────────────────────────────

async function apiFetch<T>(
	url: string,
	token: string,
	options: RequestInit = {}
): Promise<T> {
	const res = await fetch(url, {
		...options,
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`,
			...(options.headers ?? {})
		}
	});

	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
		throw err.detail ?? err;
	}

	// 204 No Content
	if (res.status === 204) return undefined as unknown as T;
	return res.json();
}

// ── API calls ──────────────────────────────────────────────────────────────

/**
 * Get full course details including chapters with per-section progress status.
 */
export const getCourseById = async (
	token: string,
	courseId: string
): Promise<CourseDetailResponse> => {
	return apiFetch<CourseDetailResponse>(
		`${TUTOR_API_BASE_URL}/student/courses/${courseId}`,
		token
	);
};

/**
 * Get progress summary for a course.
 */
export const getCourseProgress = async (
	token: string,
	courseId: string
): Promise<ProgressSummaryResponse> => {
	return apiFetch<ProgressSummaryResponse>(
		`${TUTOR_API_BASE_URL}/student/courses/${courseId}/progress`,
		token
	);
};

/**
 * Mark a section as completed (or update its status).
 */
export const updateSectionProgress = async (
	token: string,
	courseId: string,
	chapterId: string,
	sectionId: string,
	status: 'not-started' | 'in-progress' | 'completed' = 'completed'
): Promise<ProgressSummaryResponse> => {
	return apiFetch<ProgressSummaryResponse>(
		`${TUTOR_API_BASE_URL}/student/courses/${courseId}/progress`,
		token,
		{
			method: 'PUT',
			body: JSON.stringify({ chapter_id: chapterId, section_id: sectionId, status })
		}
	);
};

/**
 * Save the AI chat session ID so the student can resume later.
 */
export const saveCourseChatId = async (
	token: string,
	courseId: string,
	chatId: string
): Promise<void> => {
	return apiFetch<void>(
		`${TUTOR_API_BASE_URL}/student/courses/${courseId}/chat`,
		token,
		{
			method: 'PUT',
			body: JSON.stringify({ chat_id: chatId })
		}
	);
};