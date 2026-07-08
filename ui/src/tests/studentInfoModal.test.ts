// src/tests/studentInfoModal.test.ts
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import { writable } from 'svelte/store';

vi.mock('$lib/apis/sessions', () => ({
	SessionsAPI: {
		getStudentHistory: vi.fn()
	}
}));

const { SessionsAPI } = await import('$lib/apis/sessions');
import StudentInfoModal from '$lib/components/StudentInfoModal.svelte';

const mockI18nStore = writable({ t: (key: string) => key });

const studentFixture = {
	id: 's1',
	name: 'Alice Martin',
	email: 'alice@test.com',
	enrolled_at: '2026-01-10T00:00:00'
};

const renderModal = (
	props: Partial<{ show: boolean; student: typeof studentFixture | null; classroomId: string }> = {}
) =>
	render(StudentInfoModal, {
		props: { show: true, student: studentFixture, classroomId: 'c1', ...props },
		context: new Map([['i18n', mockI18nStore]])
	});

beforeEach(() => {
	vi.clearAllMocks();
	localStorage.setItem('token', 'test-token');
});

afterEach(() => {
	localStorage.clear();
});

describe('StudentInfoModal', () => {
	it('shows the student personal info', async () => {
		vi.mocked(SessionsAPI.getStudentHistory).mockResolvedValue({
			student_id: 's1',
			rate: 75,
			presences: 6,
			absences: 2,
			lates: 0,
			last_10: []
		});
		renderModal();

		await waitFor(() => expect(screen.getByTestId('student-info-modal')).toBeTruthy());
		expect(screen.getByText('Alice Martin')).toBeTruthy();
		expect(screen.getByText('alice@test.com')).toBeTruthy();
	});

	it('shows both the presence and absence percentages', async () => {
		vi.mocked(SessionsAPI.getStudentHistory).mockResolvedValue({
			student_id: 's1',
			rate: 75,
			presences: 6,
			absences: 2,
			lates: 0,
			last_10: []
		});
		renderModal();

		await waitFor(() => expect(screen.getByTestId('presence-rate')).toBeTruthy());
		expect(screen.getByTestId('presence-rate').textContent).toContain('75.0%');
		// 2 absences out of 8 total sessions = 25%
		expect(screen.getByTestId('absence-rate').textContent).toContain('25.0%');
	});

	it('fetches history scoped to the given classroom and student', async () => {
		vi.mocked(SessionsAPI.getStudentHistory).mockResolvedValue({
			student_id: 's1',
			rate: 100,
			presences: 5,
			absences: 0,
			lates: 0,
			last_10: []
		});
		renderModal({ classroomId: 'c42' });

		await waitFor(() =>
			expect(SessionsAPI.getStudentHistory).toHaveBeenCalledWith('test-token', 'c42', 's1')
		);
	});

	it('renders nothing when show is false', () => {
		renderModal({ show: false });
		expect(screen.queryByTestId('student-info-modal')).toBeNull();
	});

	it('shows an inline error if loading history fails', async () => {
		vi.mocked(SessionsAPI.getStudentHistory).mockRejectedValue({ detail: 'Network error' });
		renderModal();

		await waitFor(() => expect(screen.getByText('Network error')).toBeTruthy());
	});
});
