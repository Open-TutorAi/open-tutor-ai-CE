# Sequence Diagrams — Teacher Classroom Management

---

## 1. Create a classroom

```mermaid
sequenceDiagram
    actor Teacher
    participant UI as SvelteKit UI
    participant API as FastAPI
    participant DB as Database

    Teacher->>UI: Fill in wizard (name, subject, level…)
    UI->>API: POST /api/classrooms
    API->>API: Validate JWT (teacher role)
    API->>DB: INSERT INTO classrooms
    DB-->>API: Classroom row
    API-->>UI: 201 ClassroomOut
    UI-->>Teacher: Redirect to classroom detail page
```

---

## 2. Enroll a student via join code

```mermaid
sequenceDiagram
    actor Student
    participant UI as SvelteKit UI
    participant API as FastAPI
    participant RL as Rate Limiter
    participant DB as Database

    Student->>UI: Enter join code
    UI->>API: POST /api/classrooms/invites/{code}/redeem
    API->>RL: Check rate limit (10/min per IP)
    RL-->>API: OK
    API->>DB: SELECT invite WHERE code = ?
    DB-->>API: Invite row
    API->>API: Check expiry & max_uses
    API->>DB: SELECT enrollment (already enrolled?)
    alt Not yet enrolled
        API->>DB: INSERT INTO enrollments
        API->>DB: UPDATE invites SET uses = uses + 1
        API-->>UI: { enrolled: true }
    else Already enrolled
        API-->>UI: { enrolled: false }
    end
    UI-->>Student: Confirmation message
```

---

## 3. Import students from CSV

```mermaid
sequenceDiagram
    actor Teacher
    participant UI as SvelteKit UI
    participant API as FastAPI
    participant DB as Database

    Teacher->>UI: Select CSV file (≤ 5 MB, ≤ 2000 rows)
    UI->>API: POST /api/classrooms/{id}/import (multipart)
    API->>API: Check file extension (.csv)
    API->>API: Check file size (≤ 5 MB)
    API->>API: Verify teacher owns classroom
    loop For each CSV row
        API->>DB: SELECT user WHERE email = ?
        alt User not found
            API->>DB: INSERT INTO users (create account)
        end
        API->>DB: SELECT enrollment (already enrolled?)
        alt Not yet enrolled
            API->>DB: INSERT INTO enrollments
        end
    end
    API-->>UI: ImportResult (created, enrolled, skipped)
    UI-->>Teacher: Display import summary
```

---

## 4. Start an attendance session

```mermaid
sequenceDiagram
    actor Teacher
    participant UI as SvelteKit UI
    participant API as FastAPI
    participant DB as Database

    Teacher->>UI: Click "Démarrer une séance", fill in course & objectives
    UI->>API: POST /api/classrooms/{id}/sessions
    API->>API: Verify teacher owns classroom
    API->>DB: INSERT INTO class_sessions (ended_at = NULL)
    API->>DB: SELECT enrollments WHERE classroom_id = ?
    loop For each enrolled student
        API->>DB: INSERT INTO presences (status = ABSENT)
    end
    API-->>UI: 201 SessionOut
    UI-->>Teacher: Show "Session started" confirmation
```

---

## 5. Student joins a live session (self check-in)

```mermaid
sequenceDiagram
    actor Student
    participant UI as SvelteKit UI
    participant API as FastAPI
    participant RL as Rate Limiter
    participant DB as Database

    Student->>UI: Click "Join Session" on Live classroom card
    UI->>API: POST /api/sessions/{session_id}/join
    API->>RL: Check rate limit (20/min per IP)
    RL-->>API: OK
    API->>DB: SELECT session WHERE id = ?
    API->>API: Check session is not ended
    API->>DB: SELECT enrollment (student is enrolled?)
    API->>DB: SELECT presence WHERE session_id & student_id
    alt Status is not LATE
        API->>DB: UPDATE presences SET status = PRESENT
    end
    API-->>UI: 200 PresenceOut
    UI-->>Student: Card shows "You are present ✓"
```

---

## 6. End a session and view attendance

```mermaid
sequenceDiagram
    actor Teacher
    participant UI as SvelteKit UI
    participant API as FastAPI
    participant DB as Database

    Teacher->>UI: Click stop icon on session
    UI->>API: POST /api/sessions/{session_id}/end
    API->>API: Verify teacher owns classroom
    API->>DB: UPDATE class_sessions SET ended_at = NOW()
    API-->>UI: 200 SessionOut (ended_at set)
    UI-->>Teacher: Session shown as ended, trash icon appears

    Teacher->>UI: Click session to view presences
    UI->>API: GET /api/sessions/{session_id}/presences
    API->>DB: SELECT presences JOIN users
    API-->>UI: List of PresenceOut
    UI-->>Teacher: Display attendance list with statuses

    Teacher->>UI: Click student name
    UI->>API: GET /api/classrooms/{id}/students/{student_id}/history
    API->>DB: Compute attendance stats from presences
    API-->>UI: StudentHistory (rate, last 10 sessions)
    UI-->>Teacher: Show student history panel
```

---

## 7. Post an announcement

```mermaid
sequenceDiagram
    actor Teacher
    participant UI as SvelteKit UI
    participant API as FastAPI
    participant DB as Database

    Teacher->>UI: Type message, click "Post"
    UI->>API: POST /api/classrooms/{id}/announcements
    API->>API: Verify teacher owns classroom
    API->>DB: INSERT INTO announcements
    API-->>UI: 201 AnnouncementOut
    UI-->>Teacher: Announcement appears at top of stream

    actor Student
    Student->>UI: Open classroom, click "View announcements"
    UI->>API: GET /api/classrooms/{id}/announcements
    API->>DB: SELECT announcements WHERE classroom_id ORDER BY created_at DESC
    API-->>UI: List of AnnouncementOut
    UI-->>Student: Display announcement feed
```
