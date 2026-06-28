# Parent-Teacher Communication Technical Reference

This document describes the backend contract for parent-teacher messaging, classroom announcements, and teacher availability. All endpoints are registered below `/api/v1` and require the normal bearer-token authentication unless noted otherwise.

## Access model

- Parent and teacher messaging is scoped to a student.
- A parent can message a teacher only when the parent is linked to the student.
- A teacher conversation is created for a `(parent_id, teacher_id, student_id)` combination.
- Teachers can create and manage only their own announcements.
- Published announcements are visible to authenticated users through the parent-facing list.
- Only teachers can update their own availability.
- Admin-only linking endpoints create the parent-student and teacher-student relationships used by the messaging feature.

## Messaging endpoints

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| `GET` | `/api/v1/messages/conversations` | parent, teacher | List conversations for the current user. |
| `GET` | `/api/v1/messages/conversations/{conversation_id}` | participant | List messages in a conversation and mark unread received messages as read. |
| `POST` | `/api/v1/messages/send` | parent, teacher | Send a message. Creates the conversation if it does not already exist. |
| `PATCH` | `/api/v1/messages/{message_id}/read` | participant | Mark a message as read. |
| `GET` | `/api/v1/messages/teachers/{student_id}` | parent | List teachers linked to one child. |
| `GET` | `/api/v1/messages/my-children-teachers` | parent | List all linked child and teacher pairs for the current parent. |
| `POST` | `/api/v1/messages/conversations/{conversation_id}/attachments` | participant | Upload an attachment for a conversation. |
| `GET` | `/api/v1/messages/attachments/{attachment_id}/download` | participant | Download an attachment. |
| `POST` | `/api/v1/messages/admin/link-parent-student` | admin | Link a parent to a student. |
| `POST` | `/api/v1/messages/admin/link-teacher-student` | admin | Link a teacher to a student. |

### Send message request

```json
{
  "receiver_id": "teacher-or-parent-user-id",
  "student_id": "student-user-id",
  "content": "Could we schedule a check-in this week?",
  "attachment_ids": ["uploaded-attachment-id"]
}
```

### Send message response

```json
{
  "message_id": "message-id",
  "status": "sent",
  "message": {
    "id": "message-id",
    "conversation_id": "conversation-id",
    "sender_id": "sender-user-id",
    "content": "Could we schedule a check-in this week?",
    "is_read": false,
    "attachments": [],
    "created_at": "2026-06-28T12:00:00"
  }
}
```

### Conversation response shape

```json
{
  "id": "conversation-id",
  "parent_id": "parent-user-id",
  "teacher_id": "teacher-user-id",
  "student_id": "student-user-id",
  "parent_name": "Parent Name",
  "teacher_name": "Teacher Name",
  "student_name": "Student Name",
  "unread_count": 2,
  "created_at": "2026-06-28T12:00:00",
  "updated_at": "2026-06-28T12:15:00"
}
```

### Attachment handling

Attachments are uploaded with `multipart/form-data` using a `file` field. The upload endpoint validates file size using `MAX_UPLOAD_SIZE_MB` and allows common image, video, document, spreadsheet, presentation, text, PDF, and ZIP MIME types. Uploaded attachment records can be linked to a later message by passing their IDs in `attachment_ids`.

The attachment response shape is:

```json
{
  "id": "attachment-id",
  "message_id": null,
  "conversation_id": "conversation-id",
  "original_filename": "progress-report.pdf",
  "mime_type": "application/pdf",
  "file_size": 12345,
  "uploaded_at": "2026-06-28T12:00:00"
}
```

## Announcement endpoints

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| `GET` | `/api/v1/announcements/mine` | teacher | List announcements created by the current teacher. |
| `POST` | `/api/v1/announcements` | teacher | Create a draft announcement. |
| `PATCH` | `/api/v1/announcements/{announcement_id}` | owner teacher | Update an unpublished announcement. |
| `POST` | `/api/v1/announcements/{announcement_id}/publish` | owner teacher | Publish an announcement. |
| `POST` | `/api/v1/announcements/{announcement_id}/unpublish` | owner teacher | Unpublish an announcement. |
| `DELETE` | `/api/v1/announcements/{announcement_id}` | owner teacher | Delete an announcement. |
| `GET` | `/api/v1/announcements` | authenticated | List published announcements with read state for the current user. |
| `POST` | `/api/v1/announcements/{announcement_id}/read` | authenticated | Mark an announcement as read. |
| `GET` | `/api/v1/announcements/unread-count` | authenticated | Return the current user's unread announcement count. |

### Create announcement request

```json
{
  "title": "Field trip reminder",
  "content": "Please return permission slips by Friday.",
  "priority": "important",
  "target_type": "all"
}
```

`priority` must be `normal`, `important`, or `urgent`. `target_type` defaults to `all`; the model also supports `class` and `selected` for future targeting.

### Announcement response shape

```json
{
  "id": "announcement-id",
  "teacher_id": "teacher-user-id",
  "title": "Field trip reminder",
  "content": "Please return permission slips by Friday.",
  "priority": "important",
  "is_published": false,
  "target_type": "all",
  "is_read": false,
  "created_at": "2026-06-28T12:00:00",
  "updated_at": "2026-06-28T12:00:00"
}
```

Published announcements can be unpublished or deleted. Published announcements cannot be edited; unpublish first before changing title, content, priority, or target type.

## Teacher availability endpoints

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| `GET` | `/api/v1/teachers/availability/{teacher_id}` | authenticated | Read a teacher availability record. |
| `PUT` | `/api/v1/teachers/availability` | teacher | Update the current teacher availability. |

### Update availability request

```json
{
  "status": "available",
  "office_hours_start": "08:30",
  "office_hours_end": "16:30"
}
```

`status` must be `available`, `busy`, or `offline`. Office hour fields are optional `HH:MM` strings.

### Availability response shape

```json
{
  "teacher_id": "teacher-user-id",
  "status": "available",
  "office_hours_start": "08:30",
  "office_hours_end": "16:30",
  "updated_at": "2026-06-28T12:00:00"
}
```

If no availability record exists for a teacher, the API returns a default response with `status` set to `available`, null office hours, and null `updated_at`.

## Data models

### `parent_students`

Links a parent user to a student user.

| Field | Notes |
| --- | --- |
| `id` | UUID string primary key. |
| `parent_id` | Foreign key to `users.id`; indexed. |
| `student_id` | Foreign key to `users.id`; indexed. |
| `created_at` | UTC creation timestamp. |

### `teacher_students`

Links a teacher user to a student user.

| Field | Notes |
| --- | --- |
| `id` | UUID string primary key. |
| `teacher_id` | Foreign key to `users.id`; indexed. |
| `student_id` | Foreign key to `users.id`; indexed. |
| `created_at` | UTC creation timestamp. |

### `parent_teacher_conversations`

Represents one thread between a parent and teacher about one student.

| Field | Notes |
| --- | --- |
| `id` | UUID string primary key. |
| `parent_id` | Foreign key to `users.id`; indexed. |
| `teacher_id` | Foreign key to `users.id`; indexed. |
| `student_id` | Foreign key to `users.id`; indexed. |
| `created_at` | UTC creation timestamp. |
| `updated_at` | UTC update timestamp. |

### `parent_teacher_messages`

Stores individual messages inside parent-teacher conversations.

| Field | Notes |
| --- | --- |
| `id` | UUID string primary key. |
| `conversation_id` | Foreign key to `parent_teacher_conversations.id`; indexed. |
| `sender_id` | Foreign key to `users.id`; indexed. |
| `content` | Message body text. |
| `is_read` | Boolean read state. |
| `created_at` | UTC creation timestamp. |
| `updated_at` | UTC update timestamp. |

### `message_attachments`

Stores uploaded files associated with a conversation and optionally a message.

| Field | Notes |
| --- | --- |
| `id` | UUID string primary key. |
| `message_id` | Nullable foreign key to `parent_teacher_messages.id`; indexed. |
| `conversation_id` | Nullable foreign key to `parent_teacher_conversations.id`; indexed. |
| `uploader_id` | Foreign key to `users.id`; indexed. |
| `original_filename` | User-facing filename. |
| `filename` | UUID-based stored filename. |
| `mime_type` | Validated MIME type. |
| `file_size` | File size in bytes. |
| `file_path` | Absolute disk path. |
| `uploaded_at` | UTC upload timestamp. |

### `announcements`

Stores teacher-created announcements.

| Field | Notes |
| --- | --- |
| `id` | UUID string primary key. |
| `teacher_id` | Foreign key to `users.id`; indexed. |
| `title` | Required title, up to 255 characters. |
| `content` | Required announcement body. |
| `priority` | `normal`, `important`, or `urgent`. |
| `is_published` | Boolean publication state. |
| `target_type` | `all`, `class`, or `selected`. |
| `created_at` | UTC creation timestamp. |
| `updated_at` | UTC update timestamp. |

### `announcement_reads`

Tracks announcement read state per user.

| Field | Notes |
| --- | --- |
| `id` | UUID string primary key. |
| `announcement_id` | Foreign key to `announcements.id`; indexed. |
| `user_id` | Foreign key to `users.id`; indexed. |
| `read_at` | UTC read timestamp. |

### `teacher_availability`

Stores one availability record per teacher.

| Field | Notes |
| --- | --- |
| `id` | UUID string primary key. |
| `teacher_id` | Unique foreign key to `users.id`; indexed. |
| `status` | `available`, `busy`, or `offline`. |
| `office_hours_start` | Nullable `HH:MM` string. |
| `office_hours_end` | Nullable `HH:MM` string. |
| `updated_at` | UTC update timestamp. |
