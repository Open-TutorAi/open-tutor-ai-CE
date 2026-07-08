
// src/tests/classroomSeatingChart.test.ts
import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import { writable } from 'svelte/store';

vi.mock('$app/environment', () => ({
	browser: true,
	dev: false
}));

import ClassroomSeatingChart from '$lib/components/ClassroomSeatingChart.svelte';

const mockI18nStore = writable({ t: (key: string) => key });

const studentsFixture = [
	{ id: 's1', name: 'Alice', email: 'alice@test.com', enrolled_at: '2026-01-10T00:00:00' },
	{ id: 's2', name: 'Bob', email: 'bob@test.com', enrolled_at: '2026-01-11T00:00:00' }
];

describe('ClassroomSeatingChart', () => {
	it('shows an empty state when there are no students', () => {
		render(ClassroomSeatingChart, {
			props: { students: [] },
			context: new Map([['i18n', mockI18nStore]])
		});

		expect(screen.getByText('No students enrolled yet')).toBeTruthy();
	});

	it('falls back gracefully when WebGL is unavailable (e.g. this test environment)', async () => {
		render(ClassroomSeatingChart, {
			props: { students: studentsFixture },
			context: new Map([['i18n', mockI18nStore]])
		});

		// jsdom has no real WebGL context, so the component must catch the
		// WebGLRenderer construction error rather than crashing the page.
		await waitFor(() =>
			expect(screen.getByText('3D view is not available in this browser')).toBeTruthy()
		);
	});

	it('offers the three layout choices (rows, U, islands)', () => {
		render(ClassroomSeatingChart, {
			props: { students: studentsFixture },
			context: new Map([['i18n', mockI18nStore]])
		});

		expect(screen.getByTestId('layout-rows')).toBeTruthy();
		expect(screen.getByTestId('layout-u')).toBeTruthy();
		expect(screen.getByTestId('layout-islands')).toBeTruthy();
		expect(screen.getByText('Disposition en rangées')).toBeTruthy();
		expect(screen.getByText('Disposition en U')).toBeTruthy();
		expect(screen.getByText('Disposition en îlots (groupes)')).toBeTruthy();
	});
});
