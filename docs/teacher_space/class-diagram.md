# Class Diagram — Teacher Classroom Management

```mermaid
classDiagram

    class User {
        +String id
        +String name
        +String email
        +String role
        +String profile_image_url
        +String hashed_password
        +DateTime created_at
    }

    class Classroom {
        +String id
        +String name
        +String subject
        +String course
        +String objectives
        +String level
        +String description
        +DateTime created_at
        +String owner_id
    }

    class Enrollment {
        +String id
        +String classroom_id
        +String student_id
        +Date enrolled_at
    }

    class Invite {
        +String id
        +String code
        +String classroom_id
        +String created_by
        +DateTime created_at
        +DateTime expires_at
        +Integer max_uses
        +Integer uses
        +Boolean is_primary
    }

    class ClassSession {
        +String id
        +String classroom_id
        +DateTime scheduled_at
        +String subject
        +String objectives
        +Boolean auto_recorded
        +DateTime ended_at
    }

    class Presence {
        +String id
        +String session_id
        +String student_id
        +PresenceStatus status
        +DateTime recorded_at
    }

    class PresenceStatus {
        <<enumeration>>
        PRESENT
        ABSENT
        LATE
    }

    class Announcement {
        +String id
        +String classroom_id
        +String author_id
        +String content
        +DateTime created_at
    }

    %% Relationships
    User "1" --> "0..*" Classroom        : owns (teacher)
    User "0..*" --> "0..*" Classroom     : enrolled in (student)
    Classroom "1" *-- "0..*" Enrollment  : has
    Enrollment "0..*" --> "1" User       : student
    Classroom "1" *-- "0..*" Invite      : has
    Invite "0..*" --> "1" User           : created_by
    Classroom "1" *-- "0..*" ClassSession: has
    ClassSession "1" *-- "0..*" Presence : records
    Presence "0..*" --> "1" User         : student
    Presence --> PresenceStatus           : status
    Classroom "1" *-- "0..*" Announcement: has
    Announcement "0..*" --> "1" User     : author
```

## Class descriptions

| Class | Role |
|-------|------|
| `User` | User account (teacher or student). The `role` field distinguishes the two. |
| `Classroom` | A classroom owned by a teacher (`owner_id`). |
| `Enrollment` | Join table linking a student to a classroom, with the enrollment date. |
| `Invite` | Invite code that lets a student join a classroom. `is_primary = true` = the classroom's permanent join code. |
| `ClassSession` | An attendance session. `ended_at = null` means the session is still open. |
| `Presence` | Attendance status of a student for a given session (PRESENT / ABSENT / LATE). |
| `Announcement` | A message posted by the teacher in the classroom stream, visible to all enrolled students. |
