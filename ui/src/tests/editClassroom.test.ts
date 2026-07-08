import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { writable } from 'svelte/store';

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
		getDetail: vi.fn(),
		update: vi.fn()
	}
}));

const { goto } = await import('$app/navigation');
const { ClassroomsAPI } = await import('$lib/apis/classrooms');
const { ForbiddenError } = await import('$lib/apis/errors');
const Page = (await import('../routes/classrooms/[id]/edit/+page.svelte')).default;

const mockI18nStore = writable({ t: (key: string) => key });
const renderPage = () => render(Page, { context: new Map([['i18n', mockI18nStore]]) });

const classroomFixture = {
	id: 'c1',
	name: 'Algebra I',
	subject: 'Mathematics',
	course: 'Algebra',
	objectives: 'Learn algebra',
	level: 'Tronc Commun',
	description: 'Intro to algebra',
	created_at: '2026-01-01T00:00:00',
	owner_id: 'owner-1',
	student_count: 2,
	objectives_list: ['Learn algebra'],
	recent_activity: []
};

beforeEach(() => {
	vi.clearAllMocks();
	localStorage.setItem('token', 'test-token');
});

afterEach(() => {
	localStorage.clear();
});

describe('Edit Classroom page', () => {
	it("pre-fills the form with the classroom's current data", async () => {
		vi.mocked(ClassroomsAPI.getDetail).mockResolvedValue(classroomFixture);
		renderPage();

		await waitFor(() =>
			expect((screen.getByLabelText(/Classroom Name/i) as HTMLInputElement).value).toBe('Algebra I')
		);
		expect((screen.getByLabelText(/Short Description/i) as HTMLTextAreaElement).value).toBe(
			'Intro to algebra'
		);
	});

	it('calls ClassroomsAPI.update() with the edited fields on save', async () => {
		vi.mocked(ClassroomsAPI.getDetail).mockResolvedValue(classroomFixture);
		vi.mocked(ClassroomsAPI.update).mockResolvedValue({ ...classroomFixture, name: 'Algebra II' });
		renderPage();

		const nameInput = await waitFor(() => screen.getByLabelText(/Classroom Name/i));
		await fireEvent.input(nameInput, { target: { value: 'Algebra II' } });
		await fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));

		await waitFor(() => expect(ClassroomsAPI.update).toHaveBeenCalled());
		const [, classroomId, payload] = vi.mocked(ClassroomsAPI.update).mock.calls[0];
		expect(classroomId).toBe('c1');
		expect(payload).toMatchObject({ name: 'Algebra II' });
	});

	it('navigates back to the classroom detail page after a successful save', async () => {
		vi.mocked(ClassroomsAPI.getDetail).mockResolvedValue(classroomFixture);
		vi.mocked(ClassroomsAPI.update).mockResolvedValue(classroomFixture);
		renderPage();

		await waitFor(() => screen.getByLabelText(/Classroom Name/i));
		await fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));

		await waitFor(() => expect(goto).toHaveBeenCalledWith('/classrooms/c1'));
	});

	it('disables "Save Changes" when the name is cleared', async () => {
		vi.mocked(ClassroomsAPI.getDetail).mockResolvedValue(classroomFixture);
		renderPage();

		const nameInput = await waitFor(() => screen.getByLabelText(/Classroom Name/i));
		await fireEvent.input(nameInput, { target: { value: '' } });

		const saveButton = screen.getByRole('button', { name: /Save Changes/i }) as HTMLButtonElement;
		expect(saveButton.disabled).toBe(true);
	});

	it('shows "Accès non autorisé" on a 403 response', async () => {
		vi.mocked(ClassroomsAPI.getDetail).mockRejectedValue(new ForbiddenError());
		renderPage();

		await waitFor(() => expect(screen.getByText('Accès non autorisé')).toBeTruthy());
		expect(screen.queryByTestId('edit-classroom-form')).toBeNull();
	});

	it('shows an inline error if the update request fails', async () => {
		vi.mocked(ClassroomsAPI.getDetail).mockResolvedValue(classroomFixture);
		vi.mocked(ClassroomsAPI.update).mockRejectedValue({ detail: 'Something went wrong' });
		renderPage();

		await waitFor(() => screen.getByLabelText(/Classroom Name/i));
		await fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));

		await waitFor(() => expect(screen.getByText('Something went wrong')).toBeTruthy());
	});
});
