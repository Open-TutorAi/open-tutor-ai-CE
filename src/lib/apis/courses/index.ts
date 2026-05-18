import { TUTOR_API_BASE_URL } from '$lib/constants';

// Types
export interface CourseFile {
	id: string;
	name: string;
	size_kb: number;
	type: string;
}

export interface Section {
	id: string;
	title: string;
	status: 'not-started' | 'in-progress' | 'completed';
}

export interface Chapter {
	id: string;
	title: string;
	sections: Section[];
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
	chapters: Chapter[];
	enrolled_at: string;
	status: string;
}

/**
 * Fetch course details including chapters, sections, and files
 * @param token - Authentication token
 * @param courseId - ID of the course
 * @returns A promise that resolves to the course details
 */
export const getCourseById = async (token: string, courseId: string): Promise<CourseDetailResponse | null> => {
	let error = null;

	const res = await fetch(`${TUTOR_API_BASE_URL}/student/courses/${courseId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail || err;
			console.log('Error fetching course:', err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
