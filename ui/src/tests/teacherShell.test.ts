// src/tests/teacherShell.test.ts
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import { writable } from 'svelte/store';

vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

vi.mock('$app/environment', () => ({
	browser: true,
	dev: false
}));

vi.mock('$app/stores', () => ({
	page: writable({ url: { pathname: '/teacher' }, params: {} })
}));

vi.mock('$lib/stores', () => ({
	user: writable({
		id: 'teacher-1',
		name: 'Jane Teacher',
		role: 'teacher',
		profile_image_url: '/user.png'
	}),
	theme: writable('light'),
	isDemo: writable(false),
	demoData: writable({}),
	originalUserData: writable(null)
}));

const { goto } = await import('$app/navigation');
const mockI18nStore = writable({ t: (key: string) => key });

import TeacherShell from '$lib/components/teacher/TeacherShell.svelte';

beforeEach(() => {
	vi.clearAllMocks();
});

afterEach(() => {
	localStorage.clear();
});

describe('TeacherShell', () => {
	it('renders the navbar with the teacher greeting and does not redirect', async () => {
		render(TeacherShell, { context: new Map([['i18n', mockI18nStore]]) });

		await waitFor(() => expect(screen.getByText(/Jane/)).toBeTruthy());
		expect(goto).not.toHaveBeenCalled();
	});

	it('shows the teacher-specific subtitle, not the student one', async () => {
		render(TeacherShell, { context: new Map([['i18n', mockI18nStore]]) });

		await waitFor(() =>
			expect(screen.getByText('Manage your classrooms and track student progress')).toBeTruthy()
		);
		expect(screen.queryByText("Let's learn something new today!")).toBeNull();
	});
});
