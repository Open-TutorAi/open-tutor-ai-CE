
// src/tests/studentsTab.test.ts
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
		listStudents: vi.fn(),
		addStudent: vi.fn(),
		removeStudent: vi.fn()
	}
}));

vi.mock('$lib/apis/sessions', () => ({
	SessionsAPI: {
		getStudentHistory: vi.fn()
	}
}));

const { ClassroomsAPI } = await import('$lib/apis/classrooms');
const { SessionsAPI } = await import('$lib/apis/sessions');
import StudentsTab from '$lib/components/StudentsTab.svelte';

const mockI18nStore = writable({ t: (key: string) => key });
const renderTab = () => render(StudentsTab, { context: new Map([['i18n', mockI18nStore]]) });

const studentsFixture = [
	{ id: 's1', name: 'Alice', email: 'alice@test.com', enrolled_at: '2026-01-10T00:00:00' },
	{ id: 's2', name: 'Bob', email: 'bob@test.com', enrolled_at: '2026-01-11T00:00:00' }
];

beforeEach(() => {
	vi.clearAllMocks();
	localStorage.setItem('token', 'test-token');
});

afterEach(() => {
	localStorage.clear();
});

describe('StudentsTab', () => {
	it('affiche la liste des étudiants', async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue(studentsFixture);
		renderTab();

		await waitFor(() => expect(screen.getAllByTestId('student-row').length).toBe(2));
		expect(screen.getByText('Alice')).toBeTruthy();
		expect(screen.getByText('alice@test.com')).toBeTruthy();
		expect(screen.getByText('Bob')).toBeTruthy();
		expect(screen.getByText('bob@test.com')).toBeTruthy();
	});

	it('bascule vers la vue plan de classe 3D', async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue(studentsFixture);
		renderTab();

		await waitFor(() => expect(screen.getAllByTestId('student-row').length).toBe(2));

		await fireEvent.click(screen.getByTestId('view-toggle-seating'));

		await waitFor(() => expect(screen.getByTestId('seating-chart')).toBeTruthy());
		expect(screen.queryByTestId('student-row')).toBeNull();
	});

	it('ouvre la fenêtre d’info élève quand on clique sur son avatar dans la liste', async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue(studentsFixture);
		vi.mocked(SessionsAPI.getStudentHistory).mockResolvedValue({
			student_id: 's1',
			rate: 90,
			presences: 9,
			absences: 1,
			lates: 0,
			last_10: []
		});
		renderTab();

		await waitFor(() => expect(screen.getAllByTestId('student-row').length).toBe(2));

		await fireEvent.click(screen.getAllByTestId('student-avatar-button')[0]);

		await waitFor(() => expect(screen.getByTestId('student-info-modal')).toBeTruthy());
		expect(screen.getAllByText('Alice').length).toBeGreaterThan(0);
		expect(screen.getAllByText('alice@test.com').length).toBeGreaterThan(0);
	});

	it('ajoute un étudiant par email', async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue([]);
		vi.mocked(ClassroomsAPI.addStudent).mockResolvedValue({
			student_id: 's3',
			student_name: 'Charlie',
			student_email: 'charlie@test.com'
		});
		renderTab();

		await waitFor(() => expect(screen.getByTestId('students-tab')).toBeTruthy());

		const input = screen.getByPlaceholderText('Student email');
		await fireEvent.input(input, { target: { value: 'charlie@test.com' } });
		await fireEvent.click(screen.getByText('Add Student'));

		await waitFor(() => expect(ClassroomsAPI.addStudent).toHaveBeenCalled());
		const [, , email] = vi.mocked(ClassroomsAPI.addStudent).mock.calls[0];
		expect(email).toBe('charlie@test.com');
		await waitFor(() => expect(screen.getByText('Charlie')).toBeTruthy());
	});

	it("affiche une erreur si l'email est inconnu", async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue([]);
		vi.mocked(ClassroomsAPI.addStudent).mockRejectedValue({
			detail: 'User not found'
		});
		renderTab();

		await waitFor(() => expect(screen.getByTestId('students-tab')).toBeTruthy());

		const input = screen.getByPlaceholderText('Student email');
		await fireEvent.input(input, { target: { value: 'unknown@test.com' } });
		await fireEvent.click(screen.getByText('Add Student'));

		await waitFor(() => expect(screen.getByText('User not found')).toBeTruthy());
	});

	it("affiche une erreur si l'étudiant est déjà inscrit", async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue([]);
		vi.mocked(ClassroomsAPI.addStudent).mockRejectedValue({
			detail: 'Student already enrolled'
		});
		renderTab();

		await waitFor(() => expect(screen.getByTestId('students-tab')).toBeTruthy());

		const input = screen.getByPlaceholderText('Student email');
		await fireEvent.input(input, { target: { value: 'existing@test.com' } });
		await fireEvent.click(screen.getByText('Add Student'));

		await waitFor(() => expect(screen.getByText('Student already enrolled')).toBeTruthy());
	});

	it('retire un étudiant', async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue(studentsFixture);
		vi.mocked(ClassroomsAPI.removeStudent).mockResolvedValue({ status: 'removed' });

		// Mock window.confirm pour accepter la suppression
		const confirmSpy = vi.spyOn(window, 'confirm').mockImplementation(() => true);

		renderTab();

		await waitFor(() => expect(screen.getAllByTestId('student-row').length).toBe(2));

		const removeButtons = screen.getAllByTestId('remove-student-button');
		await fireEvent.click(removeButtons[0]);

		await waitFor(() => expect(ClassroomsAPI.removeStudent).toHaveBeenCalled());
		const [, , studentId] = vi.mocked(ClassroomsAPI.removeStudent).mock.calls[0];
		expect(studentId).toBe('s1');

		// Vérifier que l'étudiant a été retiré de la liste
		await waitFor(() => expect(screen.getAllByTestId('student-row').length).toBe(1));
		expect(screen.queryByText('Alice')).toBeNull();

		confirmSpy.mockRestore();
	});

	it("annule le retrait d'un étudiant si confirm() est false", async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue(studentsFixture);

		// Mock window.confirm pour annuler la suppression
		const confirmSpy = vi.spyOn(window, 'confirm').mockImplementation(() => false);

		renderTab();

		await waitFor(() => expect(screen.getAllByTestId('student-row').length).toBe(2));

		const removeButtons = screen.getAllByTestId('remove-student-button');
		await fireEvent.click(removeButtons[0]);

		// Vérifier que removeStudent n'a pas été appelé
		expect(ClassroomsAPI.removeStudent).not.toHaveBeenCalled();

		// Vérifier que la liste est toujours complète
		expect(screen.getAllByTestId('student-row').length).toBe(2);

		confirmSpy.mockRestore();
	});

	it('affiche un message vide avec le bon texte', async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue([]);
		renderTab();

		await waitFor(() => expect(screen.getByText('No students enrolled yet')).toBeTruthy());
	});

	it('affiche un message de chargement', async () => {
		// Simuler un chargement lent
		vi.mocked(ClassroomsAPI.listStudents).mockImplementation(
			() => new Promise((resolve) => setTimeout(() => resolve([]), 100))
		);
		renderTab();

		// Vérifier que le message de chargement apparaît
		expect(screen.getByText('Loading students...')).toBeTruthy();

		// Attendre que le chargement soit terminé
		await waitFor(() => expect(screen.queryByText('Loading students...')).toBeNull());
	});

	it('gère les erreurs de chargement', async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockRejectedValue({
			detail: 'Failed to load students'
		});
		renderTab();

		await waitFor(() => expect(screen.getByText('Failed to load students')).toBeTruthy());
	});

	it('ajoute un étudiant avec la touche Entrée', async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue([]);
		vi.mocked(ClassroomsAPI.addStudent).mockResolvedValue({
			student_id: 's4',
			student_name: 'David',
			student_email: 'david@test.com'
		});
		renderTab();

		await waitFor(() => expect(screen.getByTestId('students-tab')).toBeTruthy());

		const input = screen.getByPlaceholderText('Student email');
		await fireEvent.input(input, { target: { value: 'david@test.com' } });
		await fireEvent.keyDown(input, { key: 'Enter' });

		await waitFor(() => expect(ClassroomsAPI.addStudent).toHaveBeenCalled());
		const [, , email] = vi.mocked(ClassroomsAPI.addStudent).mock.calls[0];
		expect(email).toBe('david@test.com');
		await waitFor(() => expect(screen.getByText('David')).toBeTruthy());
	});

	it("désactive le bouton Add Student quand l'email est vide", async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue([]);
		renderTab();

		await waitFor(() => expect(screen.getByTestId('students-tab')).toBeTruthy());

		const addButton = screen.getByText('Add Student') as HTMLButtonElement;
		expect(addButton.disabled).toBe(true);

		const input = screen.getByPlaceholderText('Student email');
		await fireEvent.input(input, { target: { value: 'test@test.com' } });
		expect(addButton.disabled).toBe(false);
	});

	it('désactive le bouton Add Student pendant la soumission', async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue([]);
		vi.mocked(ClassroomsAPI.addStudent).mockImplementation(
			() => new Promise((resolve) => setTimeout(resolve, 100))
		);
		renderTab();

		await waitFor(() => expect(screen.getByTestId('students-tab')).toBeTruthy());

		const input = screen.getByPlaceholderText('Student email');
		await fireEvent.input(input, { target: { value: 'test@test.com' } });

		const addButton = screen.getByText('Add Student') as HTMLButtonElement;
		await fireEvent.click(addButton);

		// Le bouton devrait être désactivé pendant la soumission
		expect(addButton.disabled).toBe(true);

		// Attendre que la soumission soit terminée
		await waitFor(() => expect(addButton.disabled).toBe(false));
	});

	it('affiche "Adding..." pendant la soumission', async () => {
		vi.mocked(ClassroomsAPI.listStudents).mockResolvedValue([]);
		vi.mocked(ClassroomsAPI.addStudent).mockImplementation(
			() => new Promise((resolve) => setTimeout(resolve, 100))
		);
		renderTab();

		await waitFor(() => expect(screen.getByTestId('students-tab')).toBeTruthy());

		const input = screen.getByPlaceholderText('Student email');
		await fireEvent.input(input, { target: { value: 'test@test.com' } });

		const addButton = screen.getByText('Add Student');
		await fireEvent.click(addButton);

		// Vérifier que le texte du bouton change
		await waitFor(() => expect(screen.getByText('Adding...')).toBeTruthy());

		// Attendre que la soumission soit terminée
		await waitFor(() => expect(screen.getByText('Add Student')).toBeTruthy());
	});
});
