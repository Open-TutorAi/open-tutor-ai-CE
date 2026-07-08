# User Stories — Teacher Classroom Management

## Actors

| Actor | Description |
|-------|-------------|
| **Teacher** | Authenticated user with role `teacher`. Owns classrooms and manages their lifecycle. |
| **Student** | Authenticated user with role `student`. Can join classrooms and attend sessions. |

---

## Epic 1 — Classroom Management

### US-01 — Create a classroom
**As a** teacher,  
**I want to** create a new classroom by providing a name, subject, level, course, objectives and description,  
**so that** I can organize my students into a dedicated space.

**Acceptance criteria:**
- [ ] The wizard has 6 steps: Subject, Course, Objectives, Level, Details, Review.
- [ ] The classroom name is required (1–200 characters).
- [ ] After confirmation, I am redirected to the classroom detail page.
- [ ] The new classroom appears in my "My Classrooms" list.

---

### US-02 — Edit a classroom
**As a** teacher,  
**I want to** edit the details of a classroom I own,  
**so that** I can correct mistakes or update the course information.

**Acceptance criteria:**
- [ ] Only the owner can edit the classroom.
- [ ] All fields (name, description, subject, level, course, objectives) can be updated.
- [ ] Changes are immediately reflected on the classroom detail page.

---

### US-03 — Delete a classroom
**As a** teacher,  
**I want to** permanently delete a classroom I own,  
**so that** I can remove classes that are no longer active.

**Acceptance criteria:**
- [ ] A confirmation dialog lists the consequences: sessions deleted, students lose access.
- [ ] Only the owner can delete the classroom.
- [ ] After deletion, all associated enrollments, sessions, presences, invites and announcements are removed.
- [ ] Student accounts are not deleted.

---

## Epic 2 — Student Enrollment

### US-04 — Add a student by email
**As a** teacher,  
**I want to** add an existing student to my classroom by entering their email,  
**so that** I can quickly enroll individual students.

**Acceptance criteria:**
- [ ] The student must have an existing account.
- [ ] Adding an already-enrolled student returns an appropriate error.
- [ ] The student appears immediately in the Students list.

---

### US-05 — Import students from a CSV file
**As a** teacher,  
**I want to** import multiple students at once by uploading a CSV file,  
**so that** I can enroll a whole class in one operation.

**Acceptance criteria:**
- [ ] The file must be a `.csv` with columns `email`, `name`, `password` (password optional).
- [ ] File size is limited to 5 MB and 2 000 rows.
- [ ] Students without an account are automatically created.
- [ ] Already-enrolled students are skipped (not duplicated).
- [ ] The import summary shows: created, enrolled, and skipped counts.

---

### US-06 — Share a permanent join code
**As a** teacher,  
**I want to** share the classroom's permanent join code with my students,  
**so that** they can enroll themselves without my manual intervention.

**Acceptance criteria:**
- [ ] Every classroom has exactly one permanent code (`is_primary = true`), generated on first view.
- [ ] The code is displayed on the classroom detail page with a copy button.
- [ ] The code never expires and has no use limit.

---

### US-07 — Create a one-off invite code
**As a** teacher,  
**I want to** generate a temporary invite code with an optional expiry date and maximum number of uses,  
**so that** I can control access more precisely for a specific enrollment window.

**Acceptance criteria:**
- [ ] I can set an expiry date (optional).
- [ ] I can set a maximum number of uses ≥ 1 (optional).
- [ ] Redeeming an expired or exhausted code returns an error.
- [ ] The code is shown immediately after creation.

---

### US-08 — Join a classroom with a code (student)
**As a** student,  
**I want to** join a classroom by entering a join code,  
**so that** I can access the course content and attendance sessions.

**Acceptance criteria:**
- [ ] I can enter a code on my "My Classrooms" page or from the dashboard popup.
- [ ] Redeeming a code I already used returns `enrolled: false` without error.
- [ ] The classroom appears in my "My Classrooms" list after joining.
- [ ] The API is rate-limited to 10 attempts per minute per IP to prevent brute-forcing.

---

### US-09 — Remove a student
**As a** teacher,  
**I want to** unenroll a student from my classroom,  
**so that** I can keep the roster accurate.

**Acceptance criteria:**
- [ ] Only the classroom owner can remove a student.
- [ ] The student's account and their enrollments in other classrooms are unaffected.
- [ ] The student disappears from the Students list immediately.

---

## Epic 3 — Attendance (Sessions)

### US-10 — Start a live attendance session
**As a** teacher,  
**I want to** start a session by providing a course name and objectives,  
**so that** students can check themselves in as present.

**Acceptance criteria:**
- [ ] When a session starts, every enrolled student is automatically marked ABSENT.
- [ ] Only one session per classroom can be open at a time.
- [ ] A confirmation shows the course, start time, and objectives.

---

### US-11 — Student self check-in (mark present)
**As a** student,  
**I want to** join a live session from my "My Classrooms" page,  
**so that** I am automatically marked as PRESENT.

**Acceptance criteria:**
- [ ] The classroom card shows a green "Live" badge when a session is open.
- [ ] Clicking "Join Session" marks me PRESENT.
- [ ] If the session has already ended, the button is not shown.
- [ ] Joining does not downgrade an existing LATE status.
- [ ] The API is rate-limited to 20 attempts per minute per IP.

---

### US-12 — View and adjust attendance
**As a** teacher,  
**I want to** see each student's presence status for a session and change it manually,  
**so that** I can correct errors (e.g. student forgot to check in).

**Acceptance criteria:**
- [ ] Clicking a session in the list shows all students with their status (PRESENT / ABSENT / LATE).
- [ ] I can change any student's status at any time.
- [ ] Status changes are saved immediately.

---

### US-13 — View a student's attendance history
**As a** teacher,  
**I want to** see the attendance history of a specific student,  
**so that** I can identify students who are frequently absent.

**Acceptance criteria:**
- [ ] Clicking a student's name opens a history panel.
- [ ] The panel shows: presence rate (%), absence rate (%), total presences / absences / lates.
- [ ] The last 10 sessions are displayed as a visual status list.

---

### US-14 — End a session
**As a** teacher,  
**I want to** close a live session,  
**so that** students can no longer check themselves in.

**Acceptance criteria:**
- [ ] Clicking the stop icon ends the session (`ended_at` is set).
- [ ] Once ended, the "Join Session" button disappears for students.
- [ ] A trash icon replaces the stop icon for ended sessions.

---

### US-15 — Delete a session
**As a** teacher,  
**I want to** permanently delete an ended session and its attendance records,  
**so that** I can remove test sessions or incorrect data.

**Acceptance criteria:**
- [ ] Only ended sessions can be deleted (active sessions return a 400 error).
- [ ] A confirmation is required before deletion.
- [ ] All associated presence records are also deleted.

---

## Epic 4 — Announcements

### US-16 — Post an announcement
**As a** teacher,  
**I want to** post a message to my classroom's announcement stream,  
**so that** all enrolled students are informed of news or updates.

**Acceptance criteria:**
- [ ] Only the classroom owner can post announcements.
- [ ] The announcement appears at the top of the stream (most recent first).
- [ ] Content is limited to 5 000 characters.

---

### US-17 — Read announcements (student)
**As a** student,  
**I want to** read the announcements posted in my classrooms,  
**so that** I stay informed about course news.

**Acceptance criteria:**
- [ ] Announcements are visible to all enrolled students.
- [ ] They are displayed most-recent first.

---

### US-18 — Delete an announcement
**As a** teacher,  
**I want to** delete an announcement I posted,  
**so that** I can remove outdated or incorrect information.

**Acceptance criteria:**
- [ ] Only the classroom owner can delete announcements.
- [ ] The announcement disappears immediately from the stream for all users.

---

## Epic 5 — 3D Seating Chart

### US-19 — View the classroom as a 3D seating chart
**As a** teacher,  
**I want to** see my students placed on a 3D seating chart,  
**so that** I have a visual overview of the class layout.

**Acceptance criteria:**
- [ ] The chart is accessible from the Students tab via the "Classroom view" toggle.
- [ ] Each student is represented by an avatar (real photo if set, colored initials otherwise).
- [ ] I can drag to rotate and scroll to zoom.
- [ ] Hovering an avatar shows the student's name.
- [ ] Clicking an avatar opens the student info card (enrollment date, presence %, absence %).

---

### US-20 — Switch seating layout
**As a** teacher,  
**I want to** switch between different desk arrangements (rows, U-shape, islands),  
**so that** the chart reflects the actual physical layout of my classroom.

**Acceptance criteria:**
- [ ] Three layouts are available: Rows, U-shape, Islands (groups of 4).
- [ ] Switching layout only rebuilds the scene, it does not reload the page.
- [ ] The selected layout button is visually highlighted.
