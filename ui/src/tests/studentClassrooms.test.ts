// src/tests/studentClassrooms.test.ts
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { writable } from 'svelte/store';

vi.mock('$app/environment', () => ({
	browser: true,
	dev: false
}));

vi.mock('$lib/apis/classrooms', () => ({
	ClassroomsAPI: {
		listEnrolled: vi.fn(),
		redeemInvite: vi.fn()
	}
}));

vi.mock('$lib/apis/sessions', () => ({
	SessionsAPI: {
		joinSession: vi.fn()
	}
}));

const { ClassroomsAPI } = await import('$lib/apis/classrooms');
const { SessionsAPI } = await import('$lib/apis/sessions');
import Classrooms from '$lib/components/student/pages/Classrooms.svelte';

const mockI18nStore = writable({ t: (key: string) => key });
const renderPage = () => render(Classrooms, { context: new Map([['i18n', mockI18nStore]]) });

const classroomsFixture = [
	{
		id: 'c1',
		name: 'Algebra I',
		subject: 'Mathematics',
		created_at: '2026-01-01T00:00:00',
		owner_id: 'owner-1',
		student_count: 5,
		active_session_id: 's1'
	},
	{
		id: 'c2',
		name: 'World History',
		subject: 'History',
		created_at: '2026-01-01T00:00:00',
		owner_id: 'owner-1',
		student_count: 8,
		active_session_id: null
	}
];

beforeEach(() => {
	vi.clearAllMocks();
	localStorage.setItem('token', 'test-token');
});

afterEach(() => {
	localStorage.clear();
});

describe('Student Classrooms page', () => {
	it('lists enrolled classrooms after loading', async () => {
		vi.mocked(ClassroomsAPI.listEnrolled).mockResolvedValue(classroomsFixture);
		renderPage();

		await waitFor(() => expect(screen.getAllByTestId('enrolled-classroom-card').length).toBe(2));
		expect(screen.getByText('Algebra I')).toBeTruthy();
		expect(screen.getByText('World History')).toBeTruthy();
	});

	it('shows a "Live" badge and Join Session button only for classrooms with an active session', async () => {
		vi.mocked(ClassroomsAPI.listEnrolled).mockResolvedValue(classroomsFixture);
		renderPage();

		await waitFor(() => expect(screen.getAllByTestId('enrolled-classroom-card').length).toBe(2));
		expect(screen.getAllByTestId('live-badge').length).toBe(1);
		expect(screen.getAllByTestId('join-session-button').length).toBe(1);
	});

	it('calls SessionsAPI.joinSession() with the active session id when "Join Session" is clicked', async () => {
		vi.mocked(ClassroomsAPI.listEnrolled).mockResolvedValue(classroomsFixture);
		vi.mocked(SessionsAPI.joinSession).mockResolvedValue({
			id: 'p1',
			student_id: 'student-1',
			student_name: 'Student One',
			status: 'PRESENT',
			recorded_at: '2026-01-01T00:00:00'
		});
		renderPage();

		await waitFor(() => screen.getByTestId('join-session-button'));
		await fireEvent.click(screen.getByTestId('join-session-button'));

		await waitFor(() => expect(SessionsAPI.joinSession).toHaveBeenCalledWith('test-token', 's1'));
		await waitFor(() => expect(screen.getByTestId('joined-indicator')).toBeTruthy());
	});

	it('shows an error toast and leaves the button clickable if joining fails', async () => {
		vi.mocked(ClassroomsAPI.listEnrolled).mockResolvedValue(classroomsFixture);
		vi.mocked(SessionsAPI.joinSession).mockRejectedValue({ detail: 'Session has ended' });
		renderPage();

		await waitFor(() => screen.getByTestId('join-session-button'));
		await fireEvent.click(screen.getByTestId('join-session-button'));

		await waitFor(() => expect(SessionsAPI.joinSession).toHaveBeenCalled());
		expect(screen.queryByTestId('joined-indicator')).toBeNull();
		expect(screen.getByTestId('join-session-button')).toBeTruthy();
	});

	it('redeems an invite code and refreshes the classroom list', async () => {
		vi.mocked(ClassroomsAPI.listEnrolled).mockResolvedValue(classroomsFixture);
		vi.mocked(ClassroomsAPI.redeemInvite).mockResolvedValue({
			student_id: 'student-1',
			enrolled: true
		});
		renderPage();

		await waitFor(() => screen.getByTestId('redeem-code-button'));
		await fireEvent.input(screen.getByPlaceholderText('Enter course code'), {
			target: { value: 'ABC123' }
		});
		await fireEvent.click(screen.getByTestId('redeem-code-button'));

		await waitFor(() =>
			expect(ClassroomsAPI.redeemInvite).toHaveBeenCalledWith('test-token', 'ABC123')
		);
		await waitFor(() => expect(ClassroomsAPI.listEnrolled).toHaveBeenCalledTimes(2));
	});

	it('shows an error toast if the invite code is invalid', async () => {
		vi.mocked(ClassroomsAPI.listEnrolled).mockResolvedValue(classroomsFixture);
		vi.mocked(ClassroomsAPI.redeemInvite).mockRejectedValue({ detail: 'Invite not found' });
		renderPage();

		await waitFor(() => screen.getByTestId('redeem-code-button'));
		await fireEvent.input(screen.getByPlaceholderText('Enter course code'), {
			target: { value: 'BADCODE' }
		});
		await fireEvent.click(screen.getByTestId('redeem-code-button'));

		await waitFor(() => expect(ClassroomsAPI.redeemInvite).toHaveBeenCalled());
		expect(ClassroomsAPI.listEnrolled).toHaveBeenCalledTimes(1);
	});

	it('shows an empty state when the student has no enrolled classrooms', async () => {
		vi.mocked(ClassroomsAPI.listEnrolled).mockResolvedValue([]);
		renderPage();

		await waitFor(() =>
			expect(screen.getByText(/not enrolled in any classroom yet/i)).toBeTruthy()
		);
	});

	it('shows an inline error if loading classrooms fails', async () => {
		vi.mocked(ClassroomsAPI.listEnrolled).mockRejectedValue({ detail: 'Network error' });
		renderPage();

		await waitFor(() => expect(screen.getByText('Network error')).toBeTruthy());
	});
});
