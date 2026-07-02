import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface QuestionCreate {
	question_text: string;
	question_type: string; // 'qcm', 'short_answer', 'essay'
	options?: string[];
	correct_answer?: string;
	explanation?: string;
	points: number;
	difficulty: string; // 'easy', 'medium', 'hard'
	tags: string[];
}

export interface ResourceCreate {
	title: string;
	description?: string;
	resource_type: string;
	classroom_id?: number;
	course_id?: number;
	subject?: string;
	level?: string;
	tags: string[];
	external_url?: string;
	content_json?: Record<string, any>;
}

export interface ResourceResponse {
	id: number;
	title: string;
	resource_type: string;
	subject?: string;
	level?: string;
	created_at: string;
	is_indexed: boolean;
}

export interface QuestionSearchResponse {
	total: number;
	questions: Array<{
		id: number;
		text: string;
		type: string;
		difficulty: string;
		points: number;
		votes: number;
		subject?: string;
	}>;
}

/**
 * Create a new question bank
 */
export const createQuestionBank = async (
	token: string,
	resource: ResourceCreate,
	questions: QuestionCreate[]
): Promise<ResourceResponse> => {
	let error = null;

	const res = await fetch(`${TUTOR_API_BASE_URL}/teacher/content/questions`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ resource, questions })
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail || 'An error occurred';
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Search question bank with semantic RAG
 */
export const searchQuestionBank = async (
	token: string,
	query?: string,
	subject?: string,
	level?: string,
	difficulty?: string
): Promise<QuestionSearchResponse> => {
	let error = null;

	// Build query string
	const params = new URLSearchParams();
	if (query) params.append('q', query);
	if (subject) params.append('subject', subject);
	if (level) params.append('level', level);
	if (difficulty) params.append('difficulty', difficulty);

	const queryString = params.toString();
	const url = `${TUTOR_API_BASE_URL}/teacher/content/questions/search${queryString ? '?' + queryString : ''}`;

	const res = await fetch(url, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail || 'An error occurred';
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export interface RevisionSheetRequest {
	classroom_id: number;
	frequent_errors: string;
	model_id?: string;
}

export interface RevisionSheetResponse {
	resource_id: number;
	content: string;
}

/**
 * Generate a revision sheet based on frequent errors
 */
export const generateRevisionSheet = async (
	token: string,
	request: RevisionSheetRequest
): Promise<RevisionSheetResponse> => {
	let error = null;

	const res = await fetch(
		`${TUTOR_API_BASE_URL}/teacher/content/revision-sheet?classroom_id=${request.classroom_id}`,
		{
			method: 'POST',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				authorization: `Bearer ${token}`
			},
			body: JSON.stringify({
				frequent_errors: request.frequent_errors,
				model_id: request.model_id || ''
			})
		}
	)
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail || 'An error occurred';
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export interface TranscriptSummaryRequest {
	classroom_id: number;
	transcription: string;
	title?: string;
	subject?: string;
	model_id?: string;
}

export interface TranscriptSummaryResponse {
	id: number;
	title: string;
	transcription: string;
	summary: string;
}

/**
 * Generate a summary from a transcript
 */
export const generateTranscriptSummary = async (
	token: string,
	request: TranscriptSummaryRequest
): Promise<TranscriptSummaryResponse> => {
	let error = null;

	const res = await fetch(
		`${TUTOR_API_BASE_URL}/teacher/content/transcript-summary?classroom_id=${request.classroom_id}`,
		{
			method: 'POST',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				authorization: `Bearer ${token}`
			},
			body: JSON.stringify({
				title: request.title,
				subject: request.subject,
				transcription: request.transcription,
				model_id: request.model_id || ''
			})
		}
	)
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail || 'An error occurred';
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Extract text from an uploaded document (PDF/TXT)
 */
export const extractDocumentText = async (token: string, file: File): Promise<{ text: string }> => {
	const data = new FormData();
	data.append('file', file);

	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/teacher/content/extract-text`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		},
		body: data
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail || 'An error occurred';
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Generate a curriculum (yearly planner) from a syllabus document
 */
export const generateCurriculum = async (
	token: string,
	file: File,
	model_id: string = ''
): Promise<any> => {
	const data = new FormData();
	data.append('file', file);
	data.append('model_id', model_id);

	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/teacher/content/curriculum/generate`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		},
		body: data
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail || 'An error occurred during curriculum generation';
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Generate a pedagogical scenario (lesson plan) from a week's theme and objectives
 */
export const generateScenario = async (
	token: string,
	payload: {
		theme: string;
		objectives: string[];
		estimated_hours: number;
		model_id: string;
	}
): Promise<{ scenario: string }> => {
	let error = null;
	const res = await fetch(`${TUTOR_API_BASE_URL}/teacher/content/curriculum/scenario/generate`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(payload)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail || 'An error occurred during scenario generation';
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
