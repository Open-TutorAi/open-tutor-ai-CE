
// src/tests/announcementsFeed.test.ts
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { writable } from 'svelte/store';

vi.mock('$lib/apis/announcements', () => ({
	AnnouncementsAPI: {
		list: vi.fn(),
		create: vi.fn(),
		delete: vi.fn()
	}
}));

const { AnnouncementsAPI } = await import('$lib/apis/announcements');
import AnnouncementsFeed from '$lib/components/AnnouncementsFeed.svelte';

const mockI18nStore = writable({ t: (key: string) => key });
const renderFeed = (props: { classroomId: string; canPost?: boolean }) =>
	render(AnnouncementsFeed, { props, context: new Map([['i18n', mockI18nStore]]) });

const announcementsFixture = [
	{
		id: 'a1',
		classroom_id: 'c1',
		author_id: 'teacher-1',
		author_name: 'Teacher One',
		content: 'Welcome to the class!',
		created_at: new Date().toISOString()
	}
];

beforeEach(() => {
	vi.clearAllMocks();
	localStorage.setItem('token', 'test-token');
});

afterEach(() => {
	localStorage.clear();
});

describe('AnnouncementsFeed', () => {
	it('lists announcements after loading', async () => {
		vi.mocked(AnnouncementsAPI.list).mockResolvedValue(announcementsFixture);
		renderFeed({ classroomId: 'c1' });

		await waitFor(() => expect(screen.getAllByTestId('announcement-item').length).toBe(1));
		expect(screen.getByText('Welcome to the class!')).toBeTruthy();
		expect(screen.getByText('Teacher One')).toBeTruthy();
	});

	it('shows an empty state when there are no announcements', async () => {
		vi.mocked(AnnouncementsAPI.list).mockResolvedValue([]);
		renderFeed({ classroomId: 'c1' });

		await waitFor(() => expect(screen.getByText('No announcements yet.')).toBeTruthy());
	});

	it('hides the composer and delete button when canPost is false', async () => {
		vi.mocked(AnnouncementsAPI.list).mockResolvedValue(announcementsFixture);
		renderFeed({ classroomId: 'c1', canPost: false });

		await waitFor(() => expect(screen.getAllByTestId('announcement-item').length).toBe(1));
		expect(screen.queryByTestId('post-announcement-button')).toBeNull();
		expect(screen.queryByTestId('delete-announcement-button')).toBeNull();
	});

	it('posts a new announcement and prepends it to the list when canPost is true', async () => {
		vi.mocked(AnnouncementsAPI.list).mockResolvedValue([]);
		vi.mocked(AnnouncementsAPI.create).mockResolvedValue({
			id: 'a2',
			classroom_id: 'c1',
			author_id: 'teacher-1',
			author_name: 'Teacher One',
			content: 'New post',
			created_at: new Date().toISOString()
		});
		renderFeed({ classroomId: 'c1', canPost: true });

		await waitFor(() => screen.getByTestId('post-announcement-button'));
		const textarea = screen.getByPlaceholderText('Share an announcement with your class...');
		await fireEvent.input(textarea, { target: { value: 'New post' } });
		await fireEvent.click(screen.getByTestId('post-announcement-button'));

		await waitFor(() =>
			expect(AnnouncementsAPI.create).toHaveBeenCalledWith('test-token', 'c1', 'New post')
		);
		await waitFor(() => expect(screen.getByText('New post')).toBeTruthy());
	});

	it('deletes an announcement when canPost is true', async () => {
		vi.mocked(AnnouncementsAPI.list).mockResolvedValue(announcementsFixture);
		vi.mocked(AnnouncementsAPI.delete).mockResolvedValue({ status: 'deleted' });
		renderFeed({ classroomId: 'c1', canPost: true });

		await waitFor(() => expect(screen.getAllByTestId('announcement-item').length).toBe(1));
		await fireEvent.click(screen.getByTestId('delete-announcement-button'));

		await waitFor(() => expect(AnnouncementsAPI.delete).toHaveBeenCalledWith('test-token', 'a1'));
		await waitFor(() => expect(screen.queryByTestId('announcement-item')).toBeNull());
	});

	it('shows an inline error if loading fails', async () => {
		vi.mocked(AnnouncementsAPI.list).mockRejectedValue({ detail: 'Network error' });
		renderFeed({ classroomId: 'c1' });

		await waitFor(() => expect(screen.getByText('Network error')).toBeTruthy());
	});
});
