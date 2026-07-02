import { describe, it, expect, vi, beforeEach } from 'vitest';

// Written before ui/src/lib/apis/assignments/index.ts exists (TDD red step).
vi.mock('$lib/constants', () => ({
	TUTOR_API_BASE_URL: 'http://localhost:8080/api/v1'
}));

import {
	createAssignment,
	getAssignments,
	getAssignmentById,
	submitAssignmentWork,
	getSubmissions,
	getSubmissionById,
	getMySubmission,
	requestAiGrade,
	finalizeGrade
} from '$lib/apis/assignments';

const TOKEN = 'test-token';
const BASE = 'http://localhost:8080/api/v1/assignments';

function mockFetchOnce(body: unknown, ok = true) {
	global.fetch = vi.fn().mockResolvedValue({
		ok,
		json: async () => body
	});
}

describe('assignments API client', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('createAssignment posts to /assignments with the auth header and body', async () => {
		mockFetchOnce({ id: 'a1', title: 'Fractions' });

		const result = await createAssignment(TOKEN, {
			title: 'Fractions',
			rubric: 'Correctness + working shown.'
		});

		expect(fetch).toHaveBeenCalledWith(
			BASE,
			expect.objectContaining({
				method: 'POST',
				headers: expect.objectContaining({ authorization: `Bearer ${TOKEN}` }),
				body: JSON.stringify({ title: 'Fractions', rubric: 'Correctness + working shown.' })
			})
		);
		expect(result).toEqual({ id: 'a1', title: 'Fractions' });
	});

	it('getAssignments issues a GET to /assignments', async () => {
		mockFetchOnce([{ id: 'a1' }]);

		const result = await getAssignments(TOKEN);

		expect(fetch).toHaveBeenCalledWith(
			BASE,
			expect.objectContaining({
				method: 'GET',
				headers: expect.objectContaining({ authorization: `Bearer ${TOKEN}` })
			})
		);
		expect(result).toEqual([{ id: 'a1' }]);
	});

	it('getAssignmentById issues a GET to /assignments/{id}', async () => {
		mockFetchOnce({ id: 'a1' });

		await getAssignmentById(TOKEN, 'a1');

		expect(fetch).toHaveBeenCalledWith(`${BASE}/a1`, expect.objectContaining({ method: 'GET' }));
	});

	it('submitAssignmentWork posts multipart form data without a Content-Type header', async () => {
		mockFetchOnce({ id: 's1', filename: 'answers.pdf' });
		const file = new File(['content'], 'answers.pdf', { type: 'application/pdf' });

		const result = await submitAssignmentWork(TOKEN, 'a1', file);

		expect(fetch).toHaveBeenCalledTimes(1);
		const [url, init] = vi.mocked(fetch).mock.calls[0];
		expect(url).toBe(`${BASE}/a1/submissions`);
		expect(init.method).toBe('POST');
		expect(init.headers).toEqual({ authorization: `Bearer ${TOKEN}` });
		expect(init.body).toBeInstanceOf(FormData);
		expect(result).toEqual({ id: 's1', filename: 'answers.pdf' });
	});

	it('getSubmissions issues a GET to /assignments/{id}/submissions', async () => {
		mockFetchOnce([{ id: 's1' }]);

		await getSubmissions(TOKEN, 'a1');

		expect(fetch).toHaveBeenCalledWith(
			`${BASE}/a1/submissions`,
			expect.objectContaining({ method: 'GET' })
		);
	});

	it('getSubmissionById issues a GET to /assignments/{id}/submissions/{id}', async () => {
		mockFetchOnce({ id: 's1' });

		await getSubmissionById(TOKEN, 'a1', 's1');

		expect(fetch).toHaveBeenCalledWith(
			`${BASE}/a1/submissions/s1`,
			expect.objectContaining({ method: 'GET' })
		);
	});

	it('getMySubmission issues a GET to /assignments/{id}/submissions/mine', async () => {
		mockFetchOnce({ id: 's1', status: 'submitted' });

		const result = await getMySubmission(TOKEN, 'a1');

		expect(fetch).toHaveBeenCalledWith(
			`${BASE}/a1/submissions/mine`,
			expect.objectContaining({ method: 'GET' })
		);
		expect(result).toEqual({ id: 's1', status: 'submitted' });
	});

	it('getMySubmission resolves to null when the student has not submitted yet', async () => {
		mockFetchOnce(null);

		const result = await getMySubmission(TOKEN, 'a1');

		expect(result).toBeNull();
	});

	it('requestAiGrade posts the chosen model id to the ai-grade action', async () => {
		mockFetchOnce({ id: 's1', ai_score: 78, ai_feedback: 'Good work.' });

		const result = await requestAiGrade(TOKEN, 'a1', 's1', 'gpt-4o-mini');

		expect(fetch).toHaveBeenCalledWith(
			`${BASE}/a1/submissions/s1/ai-grade`,
			expect.objectContaining({
				method: 'POST',
				headers: expect.objectContaining({ authorization: `Bearer ${TOKEN}` }),
				body: JSON.stringify({ model: 'gpt-4o-mini' })
			})
		);
		expect(result).toEqual({ id: 's1', ai_score: 78, ai_feedback: 'Good work.' });
	});

	it('finalizeGrade puts score and feedback to the finalize action', async () => {
		mockFetchOnce({ id: 's1', status: 'finalized' });

		const result = await finalizeGrade(TOKEN, 'a1', 's1', { score: 90, feedback: 'Great job.' });

		expect(fetch).toHaveBeenCalledWith(
			`${BASE}/a1/submissions/s1/finalize`,
			expect.objectContaining({
				method: 'PUT',
				body: JSON.stringify({ score: 90, feedback: 'Great job.' })
			})
		);
		expect(result).toEqual({ id: 's1', status: 'finalized' });
	});

	it('throws the response detail when the request fails', async () => {
		mockFetchOnce({ detail: 'Only teachers can perform this action' }, false);

		await expect(createAssignment(TOKEN, { title: 'X', rubric: 'r' })).rejects.toEqual(
			'Only teachers can perform this action'
		);
	});
});
