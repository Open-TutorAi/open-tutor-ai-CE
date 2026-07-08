
// src/tests/studentAvatar.test.ts
import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import StudentAvatar from '$lib/components/StudentAvatar.svelte';

describe('StudentAvatar', () => {
	it('shows colored initials when there is no photo', () => {
		render(StudentAvatar, { props: { name: 'Alice Martin' } });

		const avatar = screen.getByTestId('student-avatar');
		expect(avatar.tagName).toBe('DIV');
		expect(avatar.textContent?.trim()).toBe('AM');
	});

	it('shows colored initials when imageUrl is the generic placeholder', () => {
		render(StudentAvatar, { props: { name: 'Bob', imageUrl: '/user.png' } });

		expect(screen.getByTestId('student-avatar').tagName).toBe('DIV');
	});

	it('shows the real photo when a custom imageUrl is provided', () => {
		render(StudentAvatar, { props: { name: 'Alice', imageUrl: 'https://example.com/alice.jpg' } });

		const avatar = screen.getByTestId('student-avatar');
		expect(avatar.tagName).toBe('IMG');
		expect(avatar.getAttribute('src')).toBe('https://example.com/alice.jpg');
	});

	it('falls back to initials if the photo fails to load', async () => {
		render(StudentAvatar, { props: { name: 'Alice', imageUrl: 'https://example.com/broken.jpg' } });

		const img = screen.getByTestId('student-avatar');
		await fireEvent.error(img);

		const avatar = screen.getByTestId('student-avatar');
		expect(avatar.tagName).toBe('DIV');
	});
});
