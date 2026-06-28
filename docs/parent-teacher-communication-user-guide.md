# Parent-Teacher Communication User Guide

This guide explains how parents and teachers use the messaging and announcement features in the parent and teacher dashboards.

## Before users start

An administrator must link:

- each parent account to the correct student account;
- each teacher account to the students they teach.

These links control which teachers a parent can contact and which parent conversations a teacher can see.

## Parent dashboard

Parents open the parent dashboard from `/parent`. The communication tools are available from the sidebar.

### View teachers

Use the `Teachers` section to see the teachers linked to each child. Each row shows the teacher name and the child the teacher is connected to.

To start a message:

1. Open `Teachers`.
2. Choose `Message` beside the teacher.
3. Write the message in the conversation view.
4. Send the message.

The first message creates the conversation automatically.

### Read and send messages

Use the `Messages` section to view conversations with teachers.

- The conversation list shows teacher names, student names, last update time, and unread counts.
- Search filters conversations by teacher or student name.
- Selecting a conversation opens the message thread.
- Pressing `Enter` sends a message; use `Shift+Enter` for a new line.
- Received messages are marked as read when the conversation is opened.

### Attach files

In an existing conversation, use the attachment button beside the message box to upload files. The UI supports common images, videos, PDFs, Office documents, text files, and ZIP files.

Attachments are uploaded before the message is sent. Uploaded attachments appear in the message after sending and can be downloaded from the conversation.

### Check teacher availability

The message header shows the teacher availability status:

- `Available`
- `Busy`
- `Offline`

If office hours are configured and the parent opens a conversation outside those hours, the UI shows a notice that the response may be delayed.

### Read announcements

Use the `Announcements` section to read published teacher announcements.

- Unread announcements show an unread indicator.
- Important and urgent announcements show priority styling.
- Select an announcement to expand it.
- Opening an unread announcement marks it as read.

The parent dashboard also shows unread counts for communication items where available.

## Teacher dashboard

Teachers open the teacher dashboard from `/teacher`. The communication tools are available from the sidebar.

### Read and reply to parent messages

Use `Messages` to manage parent conversations.

- The conversation list shows parent names, student names, last update time, and unread counts.
- Search filters conversations by parent or student name.
- Selecting a conversation opens the message thread.
- Received messages are marked as read when the conversation is opened.
- Replies are sent from the message composer.

Teachers can use the same attachment flow as parents in existing conversations.

### Create announcements

Use `Announcements` to create notices for families.

To create an announcement:

1. Open `Announcements`.
2. Select `New announcement`.
3. Enter a title and content.
4. Choose a priority: `Normal`, `Important`, or `Urgent`.
5. Select `Create`.

New announcements are created as drafts. Drafts are not visible to parents until they are published.

### Edit announcements

Unpublished announcements can be edited from the announcement list. Published announcements cannot be edited directly. To change a published announcement:

1. Unpublish it.
2. Edit the title, content, or priority.
3. Publish it again when ready.

### Publish, unpublish, and delete announcements

Teachers can manage each announcement from the action buttons in the announcement list.

- `Publish` makes a draft visible to parents.
- `Unpublish` hides a published announcement from parents.
- `Delete` removes the announcement after confirmation.

Priority labels help parents identify urgent or important updates, so use `Urgent` only for time-sensitive information.

### Teacher availability

Teacher availability is stored as a status and optional office hours. Parents see this information in message headers. The supported status values are:

- `Available`
- `Busy`
- `Offline`

Office hours use `HH:MM` time values. When office hours are set, parents are warned if they message outside that window.

## Troubleshooting

If a parent cannot see any teachers, confirm that the parent is linked to a student and the student is linked to at least one teacher.

If a teacher cannot see parent messages, confirm that a parent has started a conversation or that the relevant parent-student and teacher-student links exist.

If an attachment upload fails, check the file size limit configured by `MAX_UPLOAD_SIZE_MB` and make sure the file type is supported.

If a parent cannot see an announcement, confirm that the announcement is published.
