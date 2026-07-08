import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/svelte';
import { tick } from 'svelte';
import { writable } from 'svelte/store';

vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

vi.mock('$app/environment', () => ({
	browser: true,
	dev: false
}));

vi.mock('$lib/apis/classrooms', () => ({
	ClassroomsAPI: {
		list: vi.fn(),
		create: vi.fn(),
		getDetail: vi.fn(),
		delete: vi.fn()
	}
}));

vi.mock('$lib/stores', async () => {
	const { writable } = await vi.importActual<typeof import('svelte/store')>('svelte/store');
	return {
		user: writable({
			id: 'teacher-1',
			email: 'teacher1@t.com',
			name: 'Teacher One',
			role: 'teacher',
			profile_image_url: ''
		})
	};
});

const { goto } = await import('$app/navigation');
const { ClassroomsAPI } = await import('$lib/apis/classrooms');
const Page = (await import('../routes/classrooms/+page.svelte')).default;

// Mocking the entire 'svelte' module (e.g. to stub getContext) breaks Svelte's
// internal onMount/lifecycle wiring, so context is injected the supported way:
// via testing-library's `context` render option, which Svelte propagates to children.
const mockI18nStore = writable({ t: (key: string) => key });
const renderPage = () => render(Page, { context: new Map([['i18n', mockI18nStore]]) });

const classroomsFixture = [
	{
		id: 'c1',
		name: 'Algebra I',
		subject: 'Math',
		course: 'Algebra',
		objectives: '',
		level: 'Beginner',
		description: '',
		created_at: '2026-01-15T00:00:00',
		owner_id: 'teacher-1',
		student_count: 12
	},
	{
		id: 'c2',
		name: 'Biology Basics',
		subject: 'Science',
		course: 'Biology',
		objectives: '',
		level: 'Advanced',
		description: '',
		created_at: '2026-02-20T00:00:00',
		owner_id: 'teacher-1',
		student_count: 5
	}
];

beforeEach(() => {
	vi.clearAllMocks();
	localStorage.setItem('token', 'test-token');
});

afterEach(() => {
	localStorage.clear();
});

describe('My Classrooms dashboard', () => {
	it('renders a loading skeleton while fetching', async () => {
		let resolveList: (value: typeof classroomsFixture) => void = () => {};
		vi.mocked(ClassroomsAPI.list).mockImplementation(
			() =>
				new Promise((resolve) => {
					resolveList = resolve;
				})
		);

		renderPage();
		await tick();

		expect(screen.getByTestId('classrooms-skeleton')).toBeTruthy();

		resolveList([]);
		await waitFor(() => expect(screen.queryByTestId('classrooms-skeleton')).toBeNull());
	});

	it('renders one ClassroomCard per classroom returned by the API', async () => {
		vi.mocked(ClassroomsAPI.list).mockResolvedValue(classroomsFixture);

		renderPage();

		await waitFor(() =>
			expect(screen.getAllByTestId('classroom-card').length).toBe(classroomsFixture.length)
		);
	});

	it('shows name, level+subject badge, student count, and creation date on each card', async () => {
		vi.mocked(ClassroomsAPI.list).mockResolvedValue(classroomsFixture);

		renderPage();

		const cards = await waitFor(() => screen.getAllByTestId('classroom-card'));
		const card = within(cards[0]);

		expect(card.getByText('Algebra I')).toBeTruthy();
		expect(card.getByTestId('classroom-badge').textContent).toContain('Beginner');
		expect(card.getByTestId('classroom-badge').textContent).toContain('Math');
		expect(card.getByTestId('student-count').textContent).toContain('12');
		expect(card.getByTestId('classroom-date').textContent).toContain('2026');
	});

	it('shows a "+ Create Classroom" CTA in the empty state when the list is empty', async () => {
		vi.mocked(ClassroomsAPI.list).mockResolvedValue([]);

		renderPage();

		const emptyState = await screen.findByTestId('classrooms-empty');
		expect(within(emptyState).getByRole('button', { name: /Create Classroom/i })).toBeTruthy();
	});

	it('filters cards by name from the search input without calling the API again', async () => {
		vi.mocked(ClassroomsAPI.list).mockResolvedValue(classroomsFixture);

		renderPage();
		await waitFor(() => expect(screen.getAllByTestId('classroom-card').length).toBe(2));

		const search = screen.getByTestId('classroom-search');
		await fireEvent.input(search, { target: { value: 'Bio' } });
		await tick();

		expect(screen.getAllByTestId('classroom-card').length).toBe(1);
		expect(screen.getByText('Biology Basics')).toBeTruthy();
		expect(screen.queryByText('Algebra I')).toBeNull();
		expect(ClassroomsAPI.list).toHaveBeenCalledTimes(1);
	});

	it('navigates to /classrooms/new when "+ Create Classroom" is clicked', async () => {
		vi.mocked(ClassroomsAPI.list).mockResolvedValue(classroomsFixture);

		renderPage();
		await waitFor(() => expect(screen.getAllByTestId('classroom-card').length).toBe(2));

		await fireEvent.click(screen.getByRole('button', { name: /Create Classroom/i }));

		expect(goto).toHaveBeenCalledWith('/classrooms/new');
	});
});
