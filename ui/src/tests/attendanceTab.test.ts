
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { writable } from 'svelte/store';
import type { PresenceOut, StudentHistory } from '$lib/types/classroom';

vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

vi.mock('$app/environment', () => ({
	browser: true,
	dev: false
}));

vi.mock('$app/stores', () => ({
	page: writable({ params: { id: 'c1' } })
}));

vi.mock('$lib/apis/classrooms', () => ({
	ClassroomsAPI: {
		create: vi.fn(),
		list: vi.fn(),
		getDetail: vi.fn(),
		delete: vi.fn()
	}
}));

vi.mock('$lib/apis/sessions', () => ({
	SessionsAPI: {
		startSession: vi.fn(),
		endSession: vi.fn(),
		deleteSession: vi.fn(),
		getPresences: vi.fn(),
		updatePresence: vi.fn(),
		getStats: vi.fn(),
		getStudentHistory: vi.fn(),
		getSessions: vi.fn()
	}
}));

vi.mock('$lib/apis/announcements', () => ({
	AnnouncementsAPI: {
		list: vi.fn(),
		create: vi.fn(),
		delete: vi.fn()
	}
}));

const { ClassroomsAPI } = await import('$lib/apis/classrooms');
const { SessionsAPI } = await import('$lib/apis/sessions');
const { AnnouncementsAPI } = await import('$lib/apis/announcements');
const { ForbiddenError } = await import('$lib/apis/errors');
const Page = (await import('../routes/classrooms/[id]/+page.svelte')).default;

const mockI18nStore = writable({ t: (key: string) => key });
const renderPage = () => render(Page, { context: new Map([['i18n', mockI18nStore]]) });

const classroomDetailFixture = {
	id: 'c1',
	name: 'Algebra I',
	subject: 'Math',
	course: 'Algebra',
	objectives: '',
	level: 'Tronc Commun',
	description: '',
	created_at: '2026-01-01T00:00:00',
	owner_id: 'owner-1',
	student_count: 2,
	objectives_list: [],
	recent_activity: [],
	join_code: 'ABC12345'
};

const statsFixture = {
	avg_rate: 87.5,
	sessions_count: 4,
	total_absences: 3,
	total_lates: 2
};

const sessionsFixture = [
	{
		id: 's1',
		classroom_id: 'c1',
		scheduled_at: '2026-01-10T09:00:00',
		subject: 'Algebra',
		auto_recorded: true,
		present_count: 8,
		absent_count: 1,
		late_count: 1
	},
	{
		id: 's2',
		classroom_id: 'c1',
		scheduled_at: '2026-01-17T09:00:00',
		subject: 'Algebra',
		auto_recorded: true,
		present_count: 9,
		absent_count: 0,
		late_count: 1
	}
];

const presencesFixture: PresenceOut[] = [
	{
		id: 'p1',
		student_id: 'student-1',
		student_name: 'Student One',
		status: 'PRESENT',
		recorded_at: '2026-01-10T09:00:00'
	},
	{
		id: 'p2',
		student_id: 'student-2',
		student_name: 'Student Two',
		status: 'ABSENT',
		recorded_at: '2026-01-10T09:00:00'
	}
];

const historyFixture: StudentHistory = {
	student_id: 'student-1',
	rate: 80,
	presences: 8,
	absences: 1,
	lates: 1,
	last_10: [
		'PRESENT',
		'PRESENT',
		'ABSENT',
		'PRESENT',
		'LATE',
		'PRESENT',
		'PRESENT',
		'PRESENT',
		'ABSENT',
		'PRESENT'
	]
};

const setupHappyPath = () => {
	vi.mocked(ClassroomsAPI.getDetail).mockResolvedValue(classroomDetailFixture);
	vi.mocked(SessionsAPI.getStats).mockResolvedValue(statsFixture);
	vi.mocked(SessionsAPI.getSessions).mockResolvedValue(sessionsFixture);
};

beforeEach(() => {
	vi.clearAllMocks();
	localStorage.setItem('token', 'test-token');
});

afterEach(() => {
	localStorage.clear();
});

describe('Classroom Detail page', () => {
	it('shows classroom name, level badge, and Edit button in the header', async () => {
		setupHappyPath();
		renderPage();

		await waitFor(() => expect(screen.getByText('Algebra I')).toBeTruthy());
		expect(screen.getByText('Tronc Commun')).toBeTruthy();
		expect(screen.getByRole('button', { name: /^Edit$/i })).toBeTruthy();
	});

	it('shows the persistent class join code with a copy button', async () => {
		setupHappyPath();
		const writeText = vi.fn();
		Object.assign(navigator, { clipboard: { writeText } });
		renderPage();

		await waitFor(() => expect(screen.getByTestId('join-code-banner')).toBeTruthy());
		expect(screen.getByText('ABC12345')).toBeTruthy();

		await fireEvent.click(screen.getByTestId('copy-join-code-button'));
		expect(writeText).toHaveBeenCalledWith('ABC12345');
	});

	it('shows the session subject and objectives in the session list', async () => {
		setupHappyPath();
		vi.mocked(SessionsAPI.getSessions).mockResolvedValue([
			{
				id: 's1',
				classroom_id: 'c1',
				scheduled_at: '2026-01-10T09:00:00',
				subject: 'Algebra',
				objectives: 'Solve quadratic equations',
				auto_recorded: true,
				present_count: 8,
				absent_count: 1,
				late_count: 1
			}
		]);
		renderPage();

		await waitFor(() => expect(screen.getAllByTestId('session-item').length).toBe(1));
		expect(screen.getByText('Algebra')).toBeTruthy();
		expect(screen.getByText(/Solve quadratic equations/)).toBeTruthy();
	});

	it('renders all 7 tabs', async () => {
		setupHappyPath();
		renderPage();

		await waitFor(() => expect(screen.getByText('Algebra I')).toBeTruthy());
		for (const label of [
			'Overview',
			'Students',
			'Resources',
			'Présences',
			'Devoirs',
			'Rapports',
			'Paramètres'
		]) {
			expect(screen.getByRole('tab', { name: label })).toBeTruthy();
		}
	});

	it('shows the announcements feed on the Overview tab and lets the teacher post', async () => {
		setupHappyPath();
		vi.mocked(AnnouncementsAPI.list).mockResolvedValue([]);
		vi.mocked(AnnouncementsAPI.create).mockResolvedValue({
			id: 'a1',
			classroom_id: 'c1',
			author_id: 'owner-1',
			author_name: 'Teacher',
			content: 'Quiz on Friday',
			created_at: '2026-01-01T00:00:00'
		});
		renderPage();

		await waitFor(() => expect(screen.getByText('Algebra I')).toBeTruthy());
		await fireEvent.click(screen.getByRole('tab', { name: 'Overview' }));

		await waitFor(() => expect(screen.getByTestId('announcements-feed')).toBeTruthy());

		const textarea = screen.getByPlaceholderText('Share an announcement with your class...');
		await fireEvent.input(textarea, { target: { value: 'Quiz on Friday' } });
		await fireEvent.click(screen.getByTestId('post-announcement-button'));

		await waitFor(() =>
			expect(AnnouncementsAPI.create).toHaveBeenCalledWith('test-token', 'c1', 'Quiz on Friday')
		);
		await waitFor(() => expect(screen.getByText('Quiz on Friday')).toBeTruthy());
	});

	it('shows 4 KPI cards on the Présences tab', async () => {
		setupHappyPath();
		renderPage();

		await waitFor(() => expect(screen.getAllByTestId('kpi-card').length).toBe(4));
		expect(screen.getByTestId('kpi-avg-rate').textContent).toContain('87.5');
		expect(screen.getByTestId('kpi-sessions').textContent).toContain('4');
		expect(screen.getByTestId('kpi-absences').textContent).toContain('3');
		expect(screen.getByTestId('kpi-lates').textContent).toContain('2');
	});

	it('renders session list items with date, time, and attendance summary', async () => {
		setupHappyPath();
		renderPage();

		await waitFor(() => expect(screen.getAllByTestId('session-item').length).toBe(2));
		const items = screen.getAllByTestId('session-item');
		expect(items[0].textContent).toContain('2026');
		expect(items[0].textContent).toContain('8');
	});

	it('loads the session detail panel with student list when a session is clicked', async () => {
		setupHappyPath();
		vi.mocked(SessionsAPI.getPresences).mockResolvedValue(presencesFixture);
		renderPage();

		const items = await waitFor(() => screen.getAllByTestId('session-item'));
		await fireEvent.click(items[0]);

		await waitFor(() => expect(screen.getByTestId('session-detail')).toBeTruthy());
		expect(screen.getByText('Student One')).toBeTruthy();
		expect(screen.getAllByTestId('presence-status-badge').length).toBe(2);
	});

	it('"Démarrer une séance" opens a form, then calls SessionsAPI.startSession() with course and objectives', async () => {
		setupHappyPath();
		vi.mocked(SessionsAPI.startSession).mockResolvedValue({
			id: 's3',
			classroom_id: 'c1',
			scheduled_at: '2026-02-01T09:00:00',
			subject: 'Algebra II',
			objectives: 'Review chapter 3',
			auto_recorded: true
		});
		vi.mocked(SessionsAPI.getPresences).mockResolvedValue([]);
		renderPage();
		await waitFor(() => expect(screen.getAllByTestId('session-item').length).toBe(2));

		await fireEvent.click(screen.getByRole('button', { name: /Démarrer une séance/i }));
		await waitFor(() => expect(screen.getByTestId('start-session-modal')).toBeTruthy());

		const subjectInput = screen.getByLabelText('Course');
		await fireEvent.input(subjectInput, { target: { value: 'Algebra II' } });
		const objectivesInput = screen.getByLabelText('Objectives');
		await fireEvent.input(objectivesInput, { target: { value: 'Review chapter 3' } });

		await fireEvent.click(screen.getByTestId('confirm-start-session'));

		await waitFor(() =>
			expect(SessionsAPI.startSession).toHaveBeenCalledWith(
				'test-token',
				'c1',
				'Algebra II',
				'Review chapter 3'
			)
		);
		await waitFor(() => expect(screen.getByTestId('session-started-summary')).toBeTruthy());
		expect(screen.getByText('Review chapter 3')).toBeTruthy();
	});

	it('"Terminer" on an open session calls SessionsAPI.endSession() and refreshes the list', async () => {
		setupHappyPath();
		vi.mocked(SessionsAPI.endSession).mockResolvedValue({
			id: 's1',
			classroom_id: 'c1',
			scheduled_at: '2026-01-10T09:00:00',
			subject: 'Algebra',
			auto_recorded: true,
			ended_at: '2026-01-10T10:00:00'
		});
		renderPage();
		await waitFor(() => expect(screen.getAllByTestId('session-item').length).toBe(2));

		const endButtons = screen.getAllByTestId('end-session-button');
		await fireEvent.click(endButtons[0]);

		await waitFor(() => expect(SessionsAPI.endSession).toHaveBeenCalledWith('test-token', 's1'));
		await waitFor(() => expect(SessionsAPI.getSessions).toHaveBeenCalledTimes(2));
	});

	it('shows "Supprimer" only on ended sessions and deletes after confirmation', async () => {
		setupHappyPath();
		vi.mocked(SessionsAPI.getSessions).mockResolvedValue([
			{ ...sessionsFixture[0], ended_at: '2026-01-10T10:00:00' },
			sessionsFixture[1]
		]);
		vi.mocked(SessionsAPI.deleteSession).mockResolvedValue({ status: 'deleted' });
		const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
		renderPage();

		await waitFor(() => expect(screen.getAllByTestId('session-item').length).toBe(2));
		expect(screen.getAllByTestId('delete-session-button').length).toBe(1);
		expect(screen.getAllByTestId('end-session-button').length).toBe(1);

		await fireEvent.click(screen.getByTestId('delete-session-button'));

		expect(confirmSpy).toHaveBeenCalled();
		await waitFor(() => expect(SessionsAPI.deleteSession).toHaveBeenCalledWith('test-token', 's1'));
		await waitFor(() => expect(SessionsAPI.getSessions).toHaveBeenCalledTimes(2));

		confirmSpy.mockRestore();
	});

	it('does not delete a session if the confirmation is cancelled', async () => {
		setupHappyPath();
		vi.mocked(SessionsAPI.getSessions).mockResolvedValue([
			{ ...sessionsFixture[0], ended_at: '2026-01-10T10:00:00' },
			sessionsFixture[1]
		]);
		const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
		renderPage();

		await waitFor(() => expect(screen.getAllByTestId('delete-session-button').length).toBe(1));
		await fireEvent.click(screen.getByTestId('delete-session-button'));

		expect(confirmSpy).toHaveBeenCalled();
		expect(SessionsAPI.deleteSession).not.toHaveBeenCalled();

		confirmSpy.mockRestore();
	});

	it('shows the student history panel with rate, counts, and 10 session circles', async () => {
		setupHappyPath();
		vi.mocked(SessionsAPI.getPresences).mockResolvedValue(presencesFixture);
		vi.mocked(SessionsAPI.getStudentHistory).mockResolvedValue(historyFixture);
		renderPage();

		const items = await waitFor(() => screen.getAllByTestId('session-item'));
		await fireEvent.click(items[0]);
		await waitFor(() => screen.getByTestId('session-detail'));

		await fireEvent.click(screen.getByText('Student One'));

		await waitFor(() => expect(screen.getByTestId('student-history-panel')).toBeTruthy());
		expect(screen.getByText(/80/)).toBeTruthy();
		expect(screen.getAllByTestId('history-circle').length).toBe(10);
	});

	it('renders the attendance donut chart', async () => {
		setupHappyPath();
		vi.mocked(SessionsAPI.getPresences).mockResolvedValue(presencesFixture);
		vi.mocked(SessionsAPI.getStudentHistory).mockResolvedValue(historyFixture);
		renderPage();

		const items = await waitFor(() => screen.getAllByTestId('session-item'));
		await fireEvent.click(items[0]);
		await waitFor(() => screen.getByTestId('session-detail'));
		await fireEvent.click(screen.getByText('Student One'));

		await waitFor(() => expect(screen.getByTestId('donut')).toBeTruthy());
	});

	it('shows "Accès non autorisé" and hides all content on a 403', async () => {
		vi.mocked(ClassroomsAPI.getDetail).mockRejectedValue(new ForbiddenError());
		renderPage();

		await waitFor(() => expect(screen.getByText('Accès non autorisé')).toBeTruthy());
		expect(screen.queryByRole('tab', { name: 'Présences' })).toBeNull();
		expect(screen.queryByTestId('kpi-card')).toBeNull();
	});
});
