
# Teacher Classroom Management

## What it does

This feature gives teachers a full workflow for running a classroom inside Open TutorAI CE:

- Create, edit, and delete classrooms.
- Enroll students three ways: add by email, import a CSV file, or share a join code (a permanent class code or a one-off invite code with optional expiry/usage limits).
- Run live attendance: start a session, students check themselves in by "joining" while the session is open, the teacher can end the session to stop check-ins, and can delete a session afterward.
- Post announcements to a classroom "stream" that enrolled students see.
- Visualize the class as a 3D seating chart (rows, U-shape, or island/group layouts) with each student's avatar; clicking a student shows their personal info and attendance percentages.

## Who uses it

- **Teacher**: owns classrooms, manages enrollment, runs sessions, posts announcements, views attendance stats and per-student history.
- **Student**: joins classrooms via invite/join code, sees their enrolled classrooms, joins live sessions to be marked present, reads announcements.

## How it works

### Classroom and enrollment

A classroom belongs to one teacher (`owner_id`). Students are linked to a classroom through an `Enrollment` row. There are three ways to enroll a student:

1. **Add by email** — the teacher enters an existing student's email; if no account exists, the request fails with a "user not found" error.
2. **CSV import** — a file with `email,name,password` columns. Unknown emails get a new account created (random password if none given); known emails are just enrolled. Rows with no email are skipped and reported.
3. **Join code** — every classroom gets one permanent, non-expiring code (`Invite.is_primary = true`) generated on first view of the classroom detail page. Teachers can also generate additional one-off codes with an expiry date and/or a max number of uses. Students redeem any code through one endpoint; redeeming twice is a no-op (`enrolled: false` the second time).

### Live attendance (sessions)

A session (`ClassSession`) belongs to a classroom and has a subject and free-text objectives, set by the teacher when starting it.

- When a session starts, every enrolled student gets a `Presence` row defaulting to **ABSENT**.
- A student becomes **PRESENT** by calling the "join" endpoint while the session is open. Joining does not downgrade an existing `LATE` status.
- The teacher can manually override any student's status (`PRESENT` / `ABSENT` / `LATE`) at any time.
- The teacher ends a session (`ended_at` is set); once ended, students can no longer join it.
- An ended session can be deleted, which also removes its presence records. A session that hasn't been ended yet cannot be deleted (the API returns a 400).
- Attendance stats (average rate, total absences/lates) and per-student history (rate, last 10 sessions) are computed from the presence records.

### Announcements (classroom stream)

A lightweight post stream scoped to one classroom. Only the owning teacher can post or delete; the teacher and any enrolled student can read. Posts are returned most-recent first.

### 3D seating chart

A Three.js scene rendered client-side from the enrolled student list — no extra data is stored for this. The teacher can switch between three desk layouts (rows, U-shape, islands of four) at any time; switching layouts only rebuilds the desks/avatars, not the whole 3D scene. Each avatar uses the student's real profile photo if one is set, otherwise a color-coded initials avatar (same color scheme used everywhere a student avatar appears). Hovering an avatar shows the student's name; clicking it opens the same student-info popup used elsewhere, showing enrollment date, presence %, and absence %.

## Data involved

| Model | Purpose | Key fields |
|---|---|---|
| `Classroom` | A teacher's class | `name`, `subject`, `course`, `objectives`, `level`, `description`, `owner_id` |
| `Enrollment` | Links a student to a classroom | `classroom_id`, `student_id`, `enrolled_at` |
| `Invite` | A join code for a classroom | `code`, `classroom_id`, `created_by`, `expires_at`, `max_uses`, `uses`, `is_primary` |
| `ClassSession` | One attendance-taking session | `classroom_id`, `scheduled_at`, `subject`, `objectives`, `auto_recorded`, `ended_at` |
| `Presence` | A student's status for one session | `session_id`, `student_id`, `status` (`PRESENT`/`ABSENT`/`LATE`), `recorded_at` |
| `Announcement` | A post in a classroom's stream | `classroom_id`, `author_id`, `content`, `created_at` |

`User.profile_image_url` (pre-existing field) is now surfaced on the student list and used for avatars; when unset or equal to the generic `/user.png` placeholder, the UI falls back to a colored-initials avatar instead of showing a photo.

## Endpoints

All routes require a valid JWT (`Authorization: Bearer <token>`).

**Classrooms** (`learning/classrooms`)
- `POST /api/classrooms` — create a classroom (teacher)
- `GET /api/classrooms` — list the caller's own classrooms (teacher)
- `GET /api/classrooms/enrolled` — list classrooms the caller is enrolled in (student), each flagged with `active_session_id` if a session is open
- `GET /api/classrooms/{classroom_id}` — classroom detail, including the persistent `join_code` (owner only)
- `PUT /api/classrooms/{classroom_id}` — update a classroom (owner only)
- `DELETE /api/classrooms/{classroom_id}` — delete a classroom (owner only)
- `GET /api/classrooms/{classroom_id}/students` — list enrolled students (owner only)
- `POST /api/classrooms/{classroom_id}/students` — enroll a student by email (owner only)
- `DELETE /api/classrooms/{classroom_id}/students/{student_id}` — unenroll a student (owner only)
- `POST /api/classrooms/{classroom_id}/import` — enroll students from a CSV file (owner only)
- `POST /api/classrooms/{classroom_id}/invites` — create a join code (owner only)
- `POST /api/classrooms/invites/{code}/redeem` — redeem a join code (any authenticated user)

**Sessions / attendance** (`learning/attendance`, `learning/sessions`)
- `POST /api/classrooms/{classroom_id}/sessions` — start a session (owner only)
- `GET /api/classrooms/{classroom_id}/sessions` — list a classroom's sessions with present/absent/late counts (owner only)
- `POST /api/sessions/{session_id}/end` — close a session (owner only)
- `DELETE /api/sessions/{session_id}` — delete an ended session (owner only; 400 if still open)
- `POST /api/sessions/{session_id}/join` — student self-check-in (enrolled student only; 400 if the session has ended)
- `GET /api/sessions/{session_id}/presences` — list presences for a session (owner, or the student themself)
- `PATCH /api/presences/{presence_id}` — manually set a presence status (owner only)
- `GET /api/classrooms/{classroom_id}/attendance-stats` — classroom-wide stats (owner only)
- `GET /api/classrooms/{classroom_id}/students/{student_id}/history` — one student's attendance history (owner, or the student themself)

**Announcements** (`learning/announcements`)
- `POST /api/classrooms/{classroom_id}/announcements` — post an announcement (owner only)
- `GET /api/classrooms/{classroom_id}/announcements` — list announcements (owner or enrolled student)
- `DELETE /api/announcements/{announcement_id}` — delete an announcement (owner only)

## Files changed or created

**Backend**
- `data/models/classroom.py`, `enrollment.py`, `invite.py`, `session.py`, `presence.py`, `announcement.py`
- `learning/classrooms/repository.py`, `service.py`, `schemas.py`
- `learning/attendance/repository.py`, `service.py`
- `learning/sessions/schemas.py`
- `learning/announcements/repository.py`, `service.py`, `schemas.py`
- `gateway/http/routers/classrooms.py`, `sessions.py`, `announcements.py`
- `gateway/http/app.py` (router registration), `gateway/http/routers/auth.py` (teacher role on signup)
- `alembic/versions/` — four migrations (initial domain tables, `ended_at`, `is_primary` + announcements table, `objectives`)
- `tests/test_classrooms.py`, `test_classrooms_integration.py`, `test_classrooms_import_invites.py`, `test_attendance.py`, `test_announcements.py`
- `tests/fixtures/sample_students.csv`

**Frontend**
- `ui/src/lib/apis/classrooms/index.ts`, `sessions/index.ts`, `announcements/index.ts`, `errors.ts`
- `ui/src/lib/types/classroom.ts`
- `ui/src/lib/components/StudentsTab.svelte`, `StudentAvatar.svelte`, `StudentInfoModal.svelte`, `ClassroomSeatingChart.svelte`, `ClassroomCard.svelte`, `CreateStudentModal.svelte`, `DeleteClassroomModal.svelte`, `AnnouncementsFeed.svelte`, `StartSessionModal.svelte`
- `ui/src/lib/components/attendance/` — `AttendanceDonut.svelte`, `AttendanceKPICards.svelte`, `PresenceStatusBadge.svelte`, `SessionDetail.svelte`, `SessionList.svelte`, `StudentHistoryPanel.svelte`
- `ui/src/lib/components/teacher/TeacherShell.svelte` (shared sidebar/navbar shell for teacher pages)
- `ui/src/lib/components/wizard/` — the multi-step "create classroom" wizard
- `ui/src/lib/components/icons/StopCircle.svelte`
- `ui/src/lib/components/student/elements/Sidebar.svelte`, `Navbar.svelte` (extended to support the teacher role)
- `ui/src/lib/components/student/pages/Classrooms.svelte`, `Dashboard.svelte` (student-side enrolled-classrooms view and join-course flow)
- `ui/src/routes/classrooms/` — `+layout.svelte`, `+page.svelte`, `[id]/+page.svelte`, `[id]/edit/+page.svelte`, `new/+page.svelte`
- `ui/src/routes/teacher/+layout.svelte`, `+page.svelte`
- `ui/src/tests/` — test files for each component above

## What changed

- **Added**: the entire classroom management domain (classrooms, enrollment, invites, attendance/sessions, announcements, 3D seating chart, student-facing "My Classrooms" page) — none of this existed before.
- **Changed**: `Sidebar.svelte` and `Navbar.svelte` were generalized to work for both the `student` and `teacher` roles instead of being student-only; the student `Dashboard.svelte` "Join Course" popup was wired to the real join-code redemption endpoint instead of a hardcoded stub.
- **Fixed**: a CSV import crash on rows with an empty email (`EmailStr` rejected `""` but not `None`); a class of bugs where repository writes used `session.flush()` instead of `session.commit()`, which silently rolled back outside of the test fixtures' shared session.
