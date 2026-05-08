import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface Flashcard {
	question: string;
	answer: string;
}

export interface FlashcardSet {
	id: string;
	title: string;
	source_label?: string;
	support_id?: string;
	model_used?: string;
	cards: Flashcard[];
	known_indices: number[];
	card_count: number;
	known_count: number;
	created_at: string;
	updated_at?: string;
}

async function apiFetch<T>(url: string, token: string, options: RequestInit = {}): Promise<T> {
	const res = await fetch(url, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`,
			...(options.headers ?? {})
		}
	});
	if (res.status === 204) return undefined as T;
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
		throw new Error(err.detail ?? 'Request failed');
	}
	return res.json();
}

export const generateFlashcards = (
	token: string,
	messages: { role: string; content: string }[],
	model: string,
	title: string,
	source_label?: string,
	support_id?: string
): Promise<FlashcardSet> =>
	apiFetch(`${TUTOR_API_BASE_URL}/flashcards/generate`, token, {
		method: 'POST',
		body: JSON.stringify({ messages, model, title, source_label, support_id })
	});

export const getFlashcardSets = (token: string): Promise<FlashcardSet[]> =>
	apiFetch(`${TUTOR_API_BASE_URL}/flashcards/sets`, token);

export const getFlashcardSet = (token: string, id: string): Promise<FlashcardSet> =>
	apiFetch(`${TUTOR_API_BASE_URL}/flashcards/sets/${id}`, token);

export const updateProgress = (
	token: string,
	id: string,
	known_indices: number[]
): Promise<FlashcardSet> =>
	apiFetch(`${TUTOR_API_BASE_URL}/flashcards/sets/${id}/progress`, token, {
		method: 'PATCH',
		body: JSON.stringify({ known_indices })
	});

export const deleteFlashcardSet = (token: string, id: string): Promise<void> =>
	apiFetch(`${TUTOR_API_BASE_URL}/flashcards/sets/${id}`, token, { method: 'DELETE' });
