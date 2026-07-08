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

vi.mock('$lib/apis/classrooms', () => ({
	ClassroomsAPI: {
		create: vi.fn(),
		list: vi.fn(),
		getDetail: vi.fn(),
		delete: vi.fn()
	}
}));

const { goto } = await import('$app/navigation');
const { ClassroomsAPI } = await import('$lib/apis/classrooms');
const Page = (await import('../routes/classrooms/new/+page.svelte')).default;

const mockI18nStore = writable({ t: (key: string) => key });
const renderWizard = () => render(Page, { context: new Map([['i18n', mockI18nStore]]) });

const nextButton = () => screen.getByRole('button', { name: /^Next$/i });

const fillStep1 = async (name = 'Algebra I', description = 'Intro to algebra') => {
	await fireEvent.input(screen.getByLabelText(/Classroom Name/i), { target: { value: name } });
	await fireEvent.input(screen.getByLabelText(/Short Description/i), {
		target: { value: description }
	});
};

const goToReview = async () => {
	for (let i = 0; i < 5; i++) {
		await fireEvent.click(nextButton());
	}
};

beforeEach(() => {
	vi.clearAllMocks();
	localStorage.setItem('token', 'test-token');
});

afterEach(() => {
	localStorage.clear();
});

describe('Create Classroom wizard', () => {
	it('renders "Classroom Name" and "Short Description" inputs on step 1', () => {
		renderWizard();

		expect(screen.getByLabelText(/Classroom Name/i)).toBeTruthy();
		expect(screen.getByLabelText(/Short Description/i)).toBeTruthy();
	});

	it('disables "Next" when required fields are empty', async () => {
		renderWizard();

		expect((nextButton() as HTMLButtonElement).disabled).toBe(true);

		await fillStep1();

		expect((nextButton() as HTMLButtonElement).disabled).toBe(false);
	});

	it('can navigate all 6 steps when each step is valid', async () => {
		renderWizard();
		await fillStep1();

		await fireEvent.click(nextButton());
		expect(screen.getByTestId('wizard-step-course')).toBeTruthy();

		await fireEvent.click(nextButton());
		expect(screen.getByTestId('wizard-step-objectives')).toBeTruthy();

		await fireEvent.click(nextButton());
		expect(screen.getByTestId('wizard-step-level')).toBeTruthy();

		await fireEvent.click(nextButton());
		expect(screen.getByTestId('wizard-step-details')).toBeTruthy();

		await fireEvent.click(nextButton());
		expect(screen.getByTestId('wizard-step-review')).toBeTruthy();
	});

	it('shows a summary and "Create Classroom" button on step 6 (Review)', async () => {
		renderWizard();
		await fillStep1('Algebra I', 'Intro to algebra');
		await goToReview();

		expect(screen.getByTestId('wizard-step-review')).toBeTruthy();
		expect(screen.getByText('Algebra I')).toBeTruthy();
		expect(screen.getByRole('button', { name: /Create Classroom/i })).toBeTruthy();
	});

	it('calls ClassroomsAPI.create() with the correct payload on submit', async () => {
		vi.mocked(ClassroomsAPI.create).mockResolvedValue({
			id: 'new-id',
			name: 'Algebra I',
			created_at: '2026-01-01T00:00:00',
			owner_id: 'owner-1',
			student_count: 0
		});

		renderWizard();
		await fillStep1('Algebra I', 'Intro to algebra');
		await goToReview();

		await fireEvent.click(screen.getByRole('button', { name: /Create Classroom/i }));

		await waitFor(() => expect(ClassroomsAPI.create).toHaveBeenCalled());
		const [, payload] = vi.mocked(ClassroomsAPI.create).mock.calls[0];
		expect(payload).toMatchObject({ name: 'Algebra I', description: 'Intro to algebra' });
	});

	it('shows inline field validation errors on a 422 response', async () => {
		vi.mocked(ClassroomsAPI.create).mockRejectedValue({
			detail: [{ loc: ['body', 'name'], msg: 'field required' }]
		});

		renderWizard();
		await fillStep1();
		await goToReview();

		await fireEvent.click(screen.getByRole('button', { name: /Create Classroom/i }));

		await waitFor(() => expect(screen.getByText(/field required/i)).toBeTruthy());
	});

	it('navigates to /classrooms/{new_id} on success', async () => {
		vi.mocked(ClassroomsAPI.create).mockResolvedValue({
			id: 'new-id',
			name: 'Algebra I',
			created_at: '2026-01-01T00:00:00',
			owner_id: 'owner-1',
			student_count: 0
		});

		renderWizard();
		await fillStep1();
		await goToReview();

		await fireEvent.click(screen.getByRole('button', { name: /Create Classroom/i }));

		await waitFor(() => expect(goto).toHaveBeenCalledWith('/classrooms/new-id'));
	});
});
