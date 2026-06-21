# Assignments Feature

The assignments system lets teachers create and grade homework, and students submit answers with file attachments.

---

## Roles

| Role | Access |
|---|---|
| `teacher` / `admin` | Create classrooms, assign homework, enroll students, grade submissions |
| `user` (student) | View assigned homework, submit answers, view returned grades |

---

## Data Models

### Classroom
```
id            UUID  (primary key)
teacher_id    UUID  (FK → users)
name          str   required
subject       str   optional
description   str   optional
is_active     bool  default true
created_at    datetime
```

### Enrollment
```
id            UUID
classroom_id  UUID  (FK → classrooms)
student_id    UUID  (FK → users)
enrolled_at   datetime
```

### Assignment
```
id             UUID
classroom_id   UUID  (FK → classrooms)
title          str   required
instructions   str   optional
due_date       datetime
attachment_url str   optional  — URL of a teacher-uploaded file
max_score      int   default 20
created_at     datetime
```

### Submission
```
id             UUID
assignment_id  UUID  (FK → assignments)
student_id     UUID  (FK → users)
content        str   optional  — text answer
attachment_url str   optional  — URL of a student-uploaded file
score          int   optional
feedback       str   optional
status         enum  submitted | late | returned | missed | not_submitted
submitted_at   datetime
graded_at      datetime
```

---

## API Endpoints

### Classrooms

| Method | Path | Who | Description |
|---|---|---|---|
| `GET` | `/api/v1/classrooms` | teacher / student | List classrooms (teacher: owned; student: enrolled) |
| `POST` | `/api/v1/classrooms` | teacher | Create a classroom |
| `GET` | `/api/v1/classrooms/{id}` | teacher | Get classroom details |
| `POST` | `/api/v1/classrooms/{id}/enroll` | teacher | Enroll a student by ID |
| `GET` | `/api/v1/classrooms/{id}/students` | teacher | List enrolled students with name + email |

**Enroll request body:**
```json
{ "student_id": "<uuid>" }
```

**Students response:**
```json
[
  {
    "student_id": "abc-123",
    "name": "Alice Dupont",
    "email": "alice@school.fr",
    "enrolled_at": "2026-06-21T19:58:03"
  }
]
```

> To find a student's ID from their email: `GET /api/v1/users/lookup?email=alice@school.fr`

---

### Assignments

| Method | Path | Who | Description |
|---|---|---|---|
| `GET` | `/api/v1/assignments` | teacher / student | List assignments |
| `POST` | `/api/v1/assignments` | teacher | Create an assignment |
| `GET` | `/api/v1/assignments/{id}` | any | Get assignment details |
| `POST` | `/api/v1/assignments/{id}/submit` | student | Submit an answer |
| `GET` | `/api/v1/assignments/{id}/my-submission` | student | Get own submission |
| `GET` | `/api/v1/assignments/{id}/submissions` | teacher | List all submissions |
| `POST` | `/api/v1/assignments/{id}/grade/{sub_id}` | teacher | Return a grade |
| `GET` | `/api/v1/assignments/{id}/status-tracker` | teacher | Per-student status overview |

**Create assignment body:**
```json
{
  "classroom_id": "<uuid>",
  "title": "Lab Report",
  "instructions": "Write a report and attach your PDF.",
  "due_date": "2026-12-31T23:59:00",
  "attachment_url": "http://localhost:8080/api/v1/files/<file_id>/content",
  "max_score": 20
}
```

**Submit body:**
```json
{
  "content": "My written answer...",
  "attachment_url": "http://localhost:8080/api/v1/files/<file_id>/content"
}
```
Both `content` and `attachment_url` are optional — at least one is required.

**Grade body:**
```json
{ "score": 17, "feedback": "Good work!" }
```

---

## File Attachments

Files are uploaded separately via `POST /api/v1/files/` (multipart) and return a file ID. The URL is then stored on the assignment or submission.

```
POST /api/v1/files/
Content-Type: multipart/form-data
Authorization: Bearer <token>

→ { "id": "<file_id>", "filename": "report.pdf", ... }
```

The download URL is: `GET /api/v1/files/<file_id>/content`

> **Important:** The files endpoint requires authentication. Use `fetch()` with an `Authorization: Bearer` header to download — a plain `<a href>` will return 401.

```typescript
const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
const blob = await res.blob();
const a = document.createElement('a');
a.href = URL.createObjectURL(blob);
a.download = 'filename.pdf';
a.click();
```

---

## Frontend Routes

| Path | Role | Description |
|---|---|---|
| `/teacher/classrooms` | teacher | List and create classrooms |
| `/teacher/classrooms/[id]` | teacher | Classroom detail — enrolled students, enroll by email |
| `/teacher/assignments` | teacher | List and create assignments |
| `/teacher/assignments/[id]` | teacher | Submissions list, grade modal, status tracker |
| `/student/assignments` | student | Assignments list (tabs: To Do / Submitted / Late / Missed) |
| `/student/assignments/[id]` | student | Submit answer + attach file, view returned grade |

---

## Submission Status Flow

```
not_submitted
     │
     ▼  (student submits before due date)
 submitted
     │
     ▼  (teacher grades)
  returned

not_submitted
     │
     ▼  (student submits after due date)
    late
     │
     ▼  (teacher grades)
  returned

not_submitted
     │
     ▼  (due date passes, no submission)
   missed
```

---

## Source Files

```
Backend
├── data/models/classroom.py          — ORM models: Classroom, Enrollment, Assignment, Submission
├── learning/classrooms/repository.py — Data access for classrooms and enrollments
├── learning/classrooms/service.py    — Business logic: create, enroll, list
├── learning/assignments/repository.py— Data access for assignments and submissions
├── learning/assignments/service.py   — Business logic: submit (detects late), grade, status tracker
└── gateway/http/routers/
    ├── classrooms.py                 — REST endpoints for classrooms
    └── assignments.py                — REST endpoints for assignments

Frontend
├── ui/src/lib/apis/classrooms/index.ts          — API client
├── ui/src/lib/apis/assignments/index.ts         — API client
├── ui/src/routes/teacher/classrooms/            — Teacher classroom pages
├── ui/src/routes/teacher/assignments/           — Teacher assignment pages
└── ui/src/routes/student/assignments/           — Student assignment pages
```
