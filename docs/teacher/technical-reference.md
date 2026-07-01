# Teacher Section — Technical Reference

API endpoints and data models for the teacher section. Companion to the plain-language
`teacher-section-user-guide.md` and the `security.md` controls reference.

- All HTTP routes are served under the **`/api/v1`** prefix.
- **Teacher** routes require `require_teacher` (authenticated **and** `role == "teacher"`) and the
  service additionally checks the caller **owns the class**. **Student/self** routes require
  authentication and the service enforces **enrolment** (no IDOR). Realtime events ride the
  existing Socket.IO channel.

## Bounded contexts

| Context       | Directory      | Responsibility                                              |
| ------------- | -------------- | ----------------------------------------------------------- |
| `classrooms`  | `classrooms/`  | Classes, roster, invitations, progress, screen-control (E6) |
| `guardians`   | `guardians/`   | Parent ↔ student guardian links                            |
| `assignments` | `assignments/` | Assignment authoring, submission, grading                   |
| `resources`   | `resources/`   | Class-materials library + assignment templates              |
| `messaging`   | `messaging/`   | 1:1 teacher ↔ student conversations                        |
| `exams`       | `exams/`       | Proctored-exam config, sessions, violations                 |

## Endpoints

### Classrooms, roster & invitations

| Method | Path                                     | Who     | Purpose                                             |
| ------ | ---------------------------------------- | ------- | --------------------------------------------------- |
| GET    | `/classrooms`                            | teacher | List the caller's classes                           |
| POST   | `/classrooms`                            | teacher | Create a class                                      |
| GET    | `/classrooms/{id}`                       | teacher | Get one class                                       |
| DELETE | `/classrooms/{id}`                       | teacher | Delete a class (cascades class-scoped data)         |
| GET    | `/classrooms/{id}/students`              | teacher | Roster                                              |
| POST   | `/classrooms/{id}/students`              | teacher | Enrol an existing student by email                  |
| DELETE | `/classrooms/{id}/students/{student_id}` | teacher | Remove a student                                    |
| GET    | `/classrooms/{id}/invitations`           | teacher | List invitations                                    |
| POST   | `/classrooms/{id}/invitations`           | teacher | Invite by email                                     |
| POST   | `/invitations/accept`                    | invitee | Accept an invite via token                          |
| GET    | `/students`                              | teacher | Deduplicated roster across all the caller's classes |
| GET    | `/my-teachers`                           | student | Teachers the caller may message                     |

### Progress (read-only)

| Method | Path                                              | Who     | Purpose                   |
| ------ | ------------------------------------------------- | ------- | ------------------------- |
| GET    | `/classrooms/{id}/progress`                       | teacher | Per-class activity rollup |
| GET    | `/classrooms/{id}/students/{student_id}/progress` | teacher | Per-student detail        |

### Guardians

| Method | Path                                               | Who     | Purpose                         |
| ------ | -------------------------------------------------- | ------- | ------------------------------- |
| GET    | `/classrooms/{id}/students/{student_id}/guardians` | teacher | List a student's guardian links |
| POST   | `/classrooms/{id}/students/{student_id}/guardians` | teacher | Invite/link a parent            |

### Control — screen monitor (E6, realtime)

| Method | Path                                             | Who     | Purpose                                                         |
| ------ | ------------------------------------------------ | ------- | --------------------------------------------------------------- |
| GET    | `/classrooms/{id}/students/{student_id}/monitor` | teacher | One student's lock state                                        |
| POST   | `/classrooms/{id}/students/{student_id}/monitor` | teacher | Lock/unlock one student                                         |
| POST   | `/classrooms/{id}/monitor`                       | teacher | Lock/unlock the whole class (reports `reached/total`)           |
| GET    | `/classrooms/{id}/presence`                      | teacher | Per-student online/offline + counts (powers "X/Y online now")   |
| GET    | `/classrooms/{id}/monitor/away-log`              | teacher | Tab-away history (newest first)                                 |
| DELETE | `/classrooms/{id}/monitor/away-log`              | teacher | Clear the away log                                              |
| GET    | `/me/monitor`                                    | self    | The caller's own aggregate lock state (re-applied on reconnect) |
| POST   | `/me/monitor/presence`                           | self    | Report leaving/returning while locked                           |

Realtime events: `monitor:set` (lock pushed to a student), `monitor:student-away` (away/return
sent to the locking teacher).

### Assignments

| Method | Path                                                 | Who     | Purpose                                    |
| ------ | ---------------------------------------------------- | ------- | ------------------------------------------ |
| GET    | `/classrooms/{id}/assignments`                       | teacher | List a class's assignments                 |
| POST   | `/classrooms/{id}/assignments`                       | teacher | Create                                     |
| GET    | `/classrooms/{id}/assignments/{assignment_id}`       | teacher | Detail + submissions                       |
| DELETE | `/classrooms/{id}/assignments/{assignment_id}`       | teacher | Delete                                     |
| POST   | `/classrooms/{id}/assignments/{assignment_id}/grade` | teacher | Grade & return a submission                |
| GET    | `/assignments`                                       | student | The caller's assignment feed (with status) |
| GET    | `/assignments/{assignment_id}/submission`            | student | The caller's submission                    |
| POST   | `/assignments/{assignment_id}/submit`                | student | Submit text and/or attachment              |
| GET    | `/assignments/{assignment_id}/attachment`            | student | Download the teacher's attachment          |

### Resources & templates

| Method     | Path                                         | Who             | Purpose                                               |
| ---------- | -------------------------------------------- | --------------- | ----------------------------------------------------- |
| POST       | `/classrooms/{id}/resources`                 | teacher         | Upload a class material (MIME-allowlisted + size cap) |
| GET        | `/classrooms/{id}/resources`                 | teacher/student | List class materials                                  |
| GET        | `/classrooms/{id}/resources/{rid}/content`   | teacher/student | Download a material                                   |
| DELETE     | `/classrooms/{id}/resources/{rid}`           | teacher         | Delete a material                                     |
| GET        | `/resources`                                 | teacher         | The caller's library across classes                   |
| GET / POST | `/assignment-templates`                      | teacher         | List / save reusable templates                        |
| DELETE     | `/assignment-templates/{tid}`                | teacher         | Delete a template                                     |
| POST       | `/classrooms/{id}/assignments/from-template` | teacher         | Create an assignment from a template                  |

### Proctored exams

| Method | Path                                                      | Who     | Purpose                                      |
| ------ | --------------------------------------------------------- | ------- | -------------------------------------------- |
| POST   | `/classrooms/{id}/assignments/{assignment_id}/exam`       | teacher | Configure an assignment as an exam           |
| DELETE | `/classrooms/{id}/assignments/{assignment_id}/exam`       | teacher | Remove exam config                           |
| GET    | `/classrooms/{id}/assignments/{assignment_id}/proctoring` | teacher | Live proctoring view                         |
| GET    | `/assignments/{assignment_id}/exam`                       | student | Exam config for the taker                    |
| POST   | `/assignments/{assignment_id}/exam/start`                 | student | Start/resume the session                     |
| POST   | `/assignments/{assignment_id}/exam/violation`             | student | Report a violation (drives `exam:violation`) |
| POST   | `/assignments/{assignment_id}/exam/submit`                | student | Submit                                       |
| POST   | `/assignments/{assignment_id}/exam/terminate`             | student | Terminate (timeout/auto-submit)              |

### Messaging

| Method | Path                                        | Who         | Purpose                                       |
| ------ | ------------------------------------------- | ----------- | --------------------------------------------- |
| GET    | `/conversations`                            | self        | List the caller's conversations (with unread) |
| POST   | `/conversations`                            | self        | Start a conversation                          |
| GET    | `/conversations/{conversation_id}/messages` | participant | Messages in a conversation                    |
| POST   | `/conversations/{conversation_id}/messages` | participant | Send a message                                |

Realtime event: `message:new` (delivered to the recipient; drives the unread badge).

## Data models

| Model                     | Table                       | Notes                                                  |
| ------------------------- | --------------------------- | ------------------------------------------------------ |
| `Classroom`               | `classrooms`                | Aggregate root; owned by a teacher                     |
| `Enrollment`              | `enrollments`               | Student ↔ class membership                            |
| `Invitation`              | `invitations`               | Pending/accepted/expired invite (token-based)          |
| `GuardianLink`            | `guardian_links`            | Parent ↔ student bond (`pending` → `active`)          |
| `Assignment`              | `assignments`               | Belongs to a class                                     |
| `Submission`              | `submissions`               | One per student per assignment; carries grade/feedback |
| `ClassResource`           | `class_resources`           | Uploaded class material (reuses `content/files`)       |
| `AssignmentTemplate`      | `assignment_templates`      | Reusable assignment blueprint                          |
| `MonitorState`            | `monitor_states`            | Persisted per-student lock (the source of truth)       |
| `MonitorAwayEvent`        | `monitor_away_events`       | Append-only tab-away history                           |
| `Conversation`            | `conversations`             | 1:1 thread                                             |
| `ConversationParticipant` | `conversation_participants` | Per-user `last_read_at` (unread tracking)              |
| `Message`                 | `messages`                  | A message (optional attachment)                        |
| `ExamConfig`              | `exam_configs`              | 1:1 with an assignment; time limit + violation policy  |
| `ExamSession`             | `exam_sessions`             | One per student; resume-only                           |
| `ExamViolation`           | `exam_violations`           | Append-only proctoring log                             |

Cross-context reads (never duplicated): user/role data from `accounts`, learning activity from
`learning.supports` + `self_regulation`, files from `content/files`.
