import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

vi.mock('$lib/constants', () => ({
	TUTOR_BASE_URL: 'http://localhost:8080'
}));

const { ClassroomsAPI } = await import('$lib/apis/classrooms');
const { SessionsAPI } = await import('$lib/apis/sessions');
const { ForbiddenError, NotFoundError } = await import('$lib/apis/errors');

const BASE = 'http://localhost:8080';
const TOKEN = 'test-token';

const server = setupServer();

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('ClassroomsAPI', () => {
	it('create() posts to /api/classrooms and returns the created classroom', async () => {
		server.use(
			http.post(`${BASE}/api/classrooms`, async ({ request }) => {
				const body = await request.json();
				expect(body).toEqual({ name: 'Algebra I' });
				return HttpResponse.json(
					{
						id: 'c1',
						name: 'Algebra I',
						created_at: '2026-01-01T00:00:00',
						owner_id: 'owner-1',
						student_count: 0
					},
					{ status: 201 }
				);
			})
		);

		const result = await ClassroomsAPI.create(TOKEN, { name: 'Algebra I' });

		expect(result.id).toBe('c1');
		expect(result.student_count).toBe(0);
	});

	it('list() gets /api/classrooms and returns the classroom array', async () => {
		server.use(
			http.get(`${BASE}/api/classrooms`, () =>
				HttpResponse.json([
					{
						id: 'c1',
						name: 'Algebra I',
						created_at: '2026-01-01T00:00:00',
						owner_id: 'owner-1',
						student_count: 2
					}
				])
			)
		);

		const result = await ClassroomsAPI.list(TOKEN);

		expect(result).toHaveLength(1);
		expect(result[0].name).toBe('Algebra I');
	});

	it('getDetail() gets /api/classrooms/:id and returns classroom detail', async () => {
		server.use(
			http.get(`${BASE}/api/classrooms/c1`, () =>
				HttpResponse.json({
					id: 'c1',
					name: 'Algebra I',
					created_at: '2026-01-01T00:00:00',
					owner_id: 'owner-1',
					student_count: 2,
					objectives_list: ['Learn algebra'],
					recent_activity: []
				})
			)
		);

		const result = await ClassroomsAPI.getDetail(TOKEN, 'c1');

		expect(result.objectives_list).toEqual(['Learn algebra']);
	});

	it('getDetail() throws ForbiddenError on a 403 response', async () => {
		server.use(
			http.get(`${BASE}/api/classrooms/c1`, () =>
				HttpResponse.json({ detail: 'Access denied' }, { status: 403 })
			)
		);

		await expect(ClassroomsAPI.getDetail(TOKEN, 'c1')).rejects.toBeInstanceOf(ForbiddenError);
	});

	it('delete() deletes /api/classrooms/:id and returns a message', async () => {
		server.use(
			http.delete(`${BASE}/api/classrooms/c1`, () =>
				HttpResponse.json({ message: 'Classroom deleted' })
			)
		);

		const result = await ClassroomsAPI.delete(TOKEN, 'c1');

		expect(result.message).toBe('Classroom deleted');
	});

	it('delete() throws NotFoundError on a 404 response', async () => {
		server.use(
			http.delete(`${BASE}/api/classrooms/missing`, () =>
				HttpResponse.json({ detail: 'Classroom not found' }, { status: 404 })
			)
		);

		await expect(ClassroomsAPI.delete(TOKEN, 'missing')).rejects.toBeInstanceOf(NotFoundError);
	});
});

describe('SessionsAPI', () => {
	it('startSession() posts to /api/classrooms/:id/sessions and returns the session', async () => {
		server.use(
			http.post(`${BASE}/api/classrooms/c1/sessions`, async ({ request }) => {
				const body = (await request.json()) as { subject: string };
				expect(body.subject).toBe('Algebra');
				return HttpResponse.json(
					{
						id: 's1',
						classroom_id: 'c1',
						scheduled_at: '2026-01-01T10:00:00',
						subject: 'Algebra',
						auto_recorded: true
					},
					{ status: 201 }
				);
			})
		);

		const result = await SessionsAPI.startSession(TOKEN, 'c1', 'Algebra');

		expect(result.id).toBe('s1');
		expect(result.auto_recorded).toBe(true);
	});

	it('getPresences() gets /api/sessions/:id/presences and returns the presence list', async () => {
		server.use(
			http.get(`${BASE}/api/sessions/s1/presences`, () =>
				HttpResponse.json([
					{
						id: 'p1',
						student_id: 'student-1',
						student_name: 'Student One',
						status: 'PRESENT',
						recorded_at: '2026-01-01T10:00:00'
					}
				])
			)
		);

		const result = await SessionsAPI.getPresences(TOKEN, 's1');

		expect(result).toHaveLength(1);
		expect(result[0].status).toBe('PRESENT');
	});

	it('updatePresence() patches /api/presences/:id and returns the updated presence', async () => {
		server.use(
			http.patch(`${BASE}/api/presences/p1`, async ({ request }) => {
				const body = await request.json();
				expect(body).toEqual({ status: 'LATE' });
				return HttpResponse.json({
					id: 'p1',
					student_id: 'student-1',
					student_name: 'Student One',
					status: 'LATE',
					recorded_at: '2026-01-01T10:00:00'
				});
			})
		);

		const result = await SessionsAPI.updatePresence(TOKEN, 'p1', 'LATE');

		expect(result.status).toBe('LATE');
	});

	it('getStats() gets /api/classrooms/:id/attendance-stats and returns stats', async () => {
		server.use(
			http.get(`${BASE}/api/classrooms/c1/attendance-stats`, () =>
				HttpResponse.json({
					avg_rate: 90,
					sessions_count: 3,
					total_absences: 3,
					total_lates: 3
				})
			)
		);

		const result = await SessionsAPI.getStats(TOKEN, 'c1');

		expect(result.avg_rate).toBe(90);
		expect(result.sessions_count).toBe(3);
	});

	it('getStudentHistory() gets /api/classrooms/:id/students/:sid/history and returns history', async () => {
		server.use(
			http.get(`${BASE}/api/classrooms/c1/students/student-1/history`, () =>
				HttpResponse.json({
					student_id: 'student-1',
					rate: 80,
					presences: 8,
					absences: 1,
					lates: 1,
					last_10: ['PRESENT', 'PRESENT', 'LATE']
				})
			)
		);

		const result = await SessionsAPI.getStudentHistory(TOKEN, 'c1', 'student-1');

		expect(result.student_id).toBe('student-1');
		expect(result.last_10).toEqual(['PRESENT', 'PRESENT', 'LATE']);
	});

	it('getStats() throws NotFoundError on a 404 response', async () => {
		server.use(
			http.get(`${BASE}/api/classrooms/missing/attendance-stats`, () =>
				HttpResponse.json({ detail: 'Classroom not found' }, { status: 404 })
			)
		);

		await expect(SessionsAPI.getStats(TOKEN, 'missing')).rejects.toBeInstanceOf(NotFoundError);
	});
});
