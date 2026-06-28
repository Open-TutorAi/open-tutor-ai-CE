# Parent-Teacher Messaging, Announcements, and Availability

## Summary

This branch adds the first pass of parent-teacher communication features across the backend API, domain services, tests, and Svelte dashboards.

It introduces:

- Parent-teacher conversations scoped to linked students.
- Message send/read flows with conversation lists.
- Attachment upload, validation, message linking, and download support.
- Teacher-created classroom announcements with publish, unpublish, edit, delete, read tracking, and unread counts.
- Teacher availability status and office hours.
- Parent and teacher dashboard UI updates for messaging, announcements, and availability.
- English and French i18n strings for the new dashboard surfaces.

## Backend Changes

- Added SQLAlchemy models for announcements, announcement reads, conversations, messages, message attachments, parent-student links, teacher-student links, and teacher availability.
- Registered new API routers under `/api/v1`:
  - `/messages`
  - `/announcements`
  - `/teachers`
- Added domain services and repositories for:
  - `learning/messages`
  - `learning/announcements`
  - `learning/teachers`
- Added dependency providers for the new services.
- Updated auth signup handling so user roles can support parent and teacher dashboard flows.
- Added upload configuration support in the backend Docker setup.

## Frontend Changes

- Added API clients for:
  - Messages and attachments.
  - Announcements.
  - Teacher availability.
- Added reusable dashboard sidebar component.
- Added parent dashboard components:
  - Announcements list.
  - Messages inbox.
  - Conversation view.
  - Teachers list.
- Added teacher dashboard components:
  - Announcements management.
  - Parent messages.
- Updated parent and teacher routes to use the new communication features.
- Added shared time formatting helper.
- Added English and French translations for the new UI labels and states.

## Tests Added

- `tests/test_announcements.py`
  - Teacher announcement creation, listing, publishing, unpublishing, editing, deleting, read tracking, and parent visibility.
- `tests/test_availability.py`
  - Teacher availability defaults, updates, office hours, validation, parent read access, and upsert behavior.
- `tests/test_message_attachments.py`
  - Attachment uploads, MIME type validation, participant authorization, sending attachments with messages, and fetching messages with attachments.

## Notes Before Opening PR

Current branch: `feat/parent-teacher-messaging`

The branch is currently aligned with `main` by commit history, but the feature work is still in the local working tree. Stage and commit the changes before pushing:

```bash
git status
git add .
git commit -m "feat: add parent-teacher messaging"
git push -u origin feat/parent-teacher-messaging
```

Then open a pull request from:

```text
feat/parent-teacher-messaging -> main
```

## Verification

Recommended targeted checks:

```bash
pytest tests/test_announcements.py tests/test_availability.py tests/test_message_attachments.py
```

Recommended frontend checks:

```bash
cd ui
npm run check
npm run lint
```

