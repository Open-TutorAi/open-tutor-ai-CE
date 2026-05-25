# Pull Request: Course Progress Tracking & Chat Integration System

## PR Title
**Implement Course Progress Tracking with LLM Chat Session Persistence & Progress Signal Detection**

---

## Overview

This PR implements a **complete course progress tracking system** that integrates the AI tutor chat experience with course management. Students can now:
- ✅ Resume their AI chat sessions within a course (chat session persistence)
- ✅ Have their progress automatically tracked as they interact with the AI
- ✅ See course section status updated based on AI signals in responses
- ✅ Access course details and file resources alongside the chat interface

The system bridges the gap between **Support tickets** (standalone tutor sessions) and **Course-integrated tutoring** (guided learning paths).

---

## Problem Statement

### Current Issues
1. **Chat Session Loss**: When students access a course, they start a new chat session each time. No ability to resume previous conversations.
2. **Progress Tracking Gap**: The AI tutoring experience existed in isolation from course management. Progress was not being tracked.
3. **Feature Fragmentation**: 
   - Support feature worked independently
   - Course feature had no tutoring integration
   - Progress tracking logic was absent
4. **Data Continuity**: No mechanism to link chat sessions to course enrollments or track learning progress within a course context.

### Why This Matters
- Students lose context when switching between support and courses
- Teachers can't see how students progress through course material
- The tutor experience isn't leveraged to track learning objectives completion
- Course feature incomplete without student-AI interaction capability

---

## Solution Architecture

### Core Components

#### 1. **Frontend: Course Learning Route** (`src/routes/student/classrooms/[id]/learn/+page.svelte`)
- **Purpose**: Entry point for course-based learning
- **Flow**:
  1. Fetch course details and chapter structure
  2. Check if student has an existing chat session for this course
  3. Support two scenarios:
     - **Resume existing chat**: Pass chatId to Chat component
     - **New chat**: Let Chat component create new session and save chat_id to course

```javascript
// Resolves chat ID using this priority:
1. localStorage.resumeCourseChat (temp session storage)
2. courseDetail.chat_id (backend saved)
3. Empty string (create new chat)
```

#### 2. **Frontend: Course Layout Integration** (`src/routes/student/+layout.svelte`)
- Active course context management via localStorage
- Sidebar and navbar awareness of current course
- Session cleanup when leaving course

#### 3. **Frontend: Chat Component Enhancement** (`src/lib/components/student/tutor/Chat.svelte`)
- New props: `chatIdProp` (resume chat), `courseIdProp` (course context)
- **Chat creation event**: When new chat is created, dispatch `chatCreated` event with `chatId`
- **Progress tracking**: Parse AI responses for `<COURSE_PROGRESS>` signals
- **Course progress tracking prompt**: Inject course structure into system prompt
- **Signal processing**: Extract and apply progress updates from AI responses

#### 4. **Frontend: Chat Data Presentation** (`src/lib/components/student/pages/Chat.svelte`)
- Two-pane layout:
  - **Left pane**: Chat interface (flexible, takes most space)
  - **Right pane**: Course context (RightBar component showing course details, resources)
- Mobile responsive:
  - Desktop (1211px+): Side-by-side layout
  - Mobile (max-width: 1210px): Drawer with toggle button

#### 5. **Course Progress Tracker Utility** (`src/lib/utils/courseProgressTracker.ts`)

**Key Functions**:

##### `resolveCourseIdForChat(args)`
Resolves which course a chat session belongs to using multiple fallback strategies:
```
1. courseIdProp (from component prop)
2. URL pattern: /student/classrooms/<courseId>/learn
3. localStorage key: course-chat-<chatId>
4. activeCourseData from localStorage
```

##### `extractCourseProgressSignalsFromContent(content)`
- Parses `<COURSE_PROGRESS>...</COURSE_PROGRESS>` blocks from AI responses
- Validates signals (chapter_id, section_id, status required)
- Returns cleaned content + extracted signals
- **Fresh regex per call** to avoid /g flag state issues

Signal format (AI outputs this in responses):
```xml
<COURSE_PROGRESS>
{
  "chapter_id": "ch1",
  "section_id": "sec1-1",
  "status": "completed",
  "confidence": 0.95,
  "reason": "Student demonstrated understanding of concepts"
}
</COURSE_PROGRESS>
```

##### `buildCourseProgressTrackingPrompt(token, courseId)`
- Fetches course structure from backend
- Builds detailed course outline with chapter/section titles
- Returns system prompt injection with:
  - Current course structure
  - Student's current progress per section
  - Instructions for AI to emit `<COURSE_PROGRESS>` signals
  - Heuristic detection rules (fallback if AI doesn't explicitly signal)

##### `applyCourseProgressSignalsFromContent(args)`
- Main orchestrator function called from Chat.svelte
- Extracts explicit signals + applies heuristic detection
- Calls backend to persist progress updates
- Returns detailed report of applied/skipped signals

##### `detectHeuristicSignals(content, planIndex)`
Fallback detection when AI doesn't explicitly emit signals:
```
Patterns detected:
- "complete[d]", "finish[ed]", "master[ed]" → completed
- "understand", "grasp", "learn" → in-progress
- "need to learn", "not sure" → not-started
- Case-insensitive regex matching
- Confidence scores assigned to each detection
```

---

#### 6. **Backend: Course API Routes** (`backend/open_tutorai/routers/student_courses.py`)

**New Endpoints**:

##### `GET /student/courses/<course_id>/progress`
Returns full progress summary:
```json
{
  "total_sections": 8,
  "completed_sections": 3,
  "progress_percentage": 37.5,
  "sections": [
    {
      "chapter_id": "ch1",
      "section_id": "sec1-1",
      "status": "completed",
      "completed_at": "2026-05-20T10:30:00Z"
    }
  ],
  "chat_id": "chat-uuid"
}
```

##### `PUT /student/courses/<course_id>/progress`
Updates section progress status:
```json
Request body:
{
  "chapter_id": "ch1",
  "section_id": "sec1-1",
  "status": "completed"  // 'not-started' | 'in-progress' | 'completed'
}
```
Returns updated progress summary.

##### `PUT /student/courses/<course_id>/chat`
Saves the chat session ID to the course enrollment:
```json
Request body:
{
  "chat_id": "chat-session-uuid"
}
```

**Helper Functions**:
- `_calculate_progress()`: Queries CourseProgress table, calculates percentage
- `_get_section_statuses()`: Returns dict of section_id → current status
- `_build_enrolled_response()`: Constructs course response with progress included

---

#### 7. **Backend: Database Schema** (`backend/open_tutorai/models/database.py`)

**New Tables**:

##### `CourseEnrollment`
```python
id (PK)
user_id (FK → user)
course_id (FK → course)
enrolled_at (DateTime)
status: 'active' | 'archived' | 'completed'
chat_id: Optional[str]  # ← Link to Chat.id for session resumption
```

##### `CourseProgress`
```python
id (PK)
enrollment_id (FK → enrollment)
chapter_id: str
section_id: str
status: 'not-started' | 'in-progress' | 'completed'
completed_at: Optional[DateTime]
updated_at: DateTime
reason: Optional[str]  # Why status was updated
```

---

#### 8. **Database Migrations** (`backend/open_tutorai/models/migrations.py`)

Handles schema additions:
1. `migrate_course_columns()`: Adds custom_category, meta_data, model_used, chat_id to Course
2. `migrate_enrollment_table()`: Adds status, chat_id to CourseEnrollment
3. `migrate_progress_table()`: Adds completed_at, updated_at to CourseProgress

---

## Data Flow Diagrams

### Flow 1: Resuming an Existing Course Chat
```
Student clicks "Resume Learning" on course
    ↓
+page.svelte fetches course details
    ↓
Checks: resumeRaw → courseDetail.chat_id → fallback empty
    ↓
Passes chatIdProp to Chat component
    ↓
Chat.svelte detects existing chat_id → loads history
    ↓
User sees previous conversation with context
```

### Flow 2: Starting a New Course Chat
```
Student enters course for first time
    ↓
+page.svelte finds no existing chat_id
    ↓
Passes empty chatIdProp to Chat.svelte
    ↓
Chat component creates new chat session
    ↓
On first message processed:
  → 'chatCreated' event fires with newChatId
  → +page.svelte listens and calls saveCourseChatId()
  → Backend saves chat_id to course.chat_id
    ↓
Future visits auto-resume this chat session
```

### Flow 3: Progress Tracking During Chat
```
Student sends message to AI
    ↓
AI generates response + optional <COURSE_PROGRESS> signal
    ↓
Chat.svelte receives response
    ↓
applyCourseProgressSignalsFromContent() called:
  1. Extract explicit <COURSE_PROGRESS> blocks
  2. Apply heuristic detection fallback
  3. Call backend PUT /progress endpoint
  4. Update UI with new section statuses
    ↓
Teacher sees updated progress in course dashboard
```

---

## API Contract Examples

### Example 1: Get Course Details with Progress
```bash
GET /student/courses/course-123
Authorization: Bearer token

Response:
{
  "id": "course-123",
  "title": "Introduction to Web Development",
  "chapters": [
    {
      "id": "ch1",
      "title": "HTML Basics",
      "sections": [
        {
          "id": "sec1-1",
          "title": "HTML Structure",
          "status": "completed"
        },
        {
          "id": "sec1-2",
          "title": "HTML Forms",
          "status": "in-progress"
        }
      ]
    }
  ],
  "progress_percentage": 37.5,
  "chat_id": "chat-abc123-xyz",
  "enrolled_at": "2026-05-15T08:00:00Z"
}
```

### Example 2: AI Response with Progress Signal
```
[Assistant]:
Great! You've demonstrated understanding of HTML structure basics.
The concept of semantic HTML is crucial for accessibility.

<COURSE_PROGRESS>
{
  "chapter_id": "ch1",
  "section_id": "sec1-1",
  "status": "completed",
  "confidence": 0.9,
  "reason": "Student correctly explained semantic HTML elements and their purposes"
}
</COURSE_PROGRESS>

Now, let's move to forms...
```

After AI response is processed, the section status in the course detail is updated.

---

## Files Modified / Created

### Frontend
| File | Type | Purpose |
|------|------|---------|
| `src/routes/student/classrooms/[id]/learn/+page.svelte` | NEW | Course learning entry point with chat resumption logic |
| `src/lib/components/student/pages/Chat.svelte` | MODIFIED | Added RightBar with course context, mobile drawer toggle |
| `src/lib/components/student/tutor/Chat.svelte` | MODIFIED | Added courseIdProp, progress tracking, signal extraction |
| `src/lib/utils/courseProgressTracker.ts` | NEW | Core progress tracking utility (5 main functions) |
| `src/lib/apis/courses/index.ts` | MODIFIED | New endpoints: progress tracking, chat resumption |
| `src/routes/student/+layout.svelte` | MODIFIED | Course context management, active page tracking |

### Backend
| File | Type | Purpose |
|------|------|---------|
| `backend/open_tutorai/routers/student_courses.py` | MODIFIED | New routes: PUT /progress, PUT /chat, GET /progress |
| `backend/open_tutorai/models/database.py` | MODIFIED | Added CourseEnrollment, CourseProgress tables |
| `backend/open_tutorai/models/migrations.py` | MODIFIED | Schema migrations for progress tracking |

---

## Technical Details

### Progress Signal Format
AI is instructed to emit progress in this format within response:
```xml
<COURSE_PROGRESS>
{
  "chapter_id": "string (required)",
  "section_id": "string (required)",
  "status": "completed|in-progress|not-started (required)",
  "confidence": "0.0-1.0 (optional)",
  "reason": "string explaining why (optional)"
}
</COURSE_PROGRESS>
```

**Regex Pattern** (fresh instance per call):
```typescript
/<COURSE_PROGRESS>\s*([\s\S]*?)\s*<\/COURSE_PROGRESS>/i
```

### Heuristic Fallback Detection
If AI doesn't emit explicit signals, the system analyzes response text for patterns:
- Keywords: "complete", "finish", "master", "understand", "learn", "need help", etc.
- Match against course plan using fuzzy string matching
- Assign confidence scores (0.0-1.0)
- Only apply signals with confidence > 0.7

### Course Context in System Prompt
When creating chat in course context, system prompt includes:
```
Current Course: [Title]
Current Progress: X% (Y/Z sections completed)

Course Structure:
- Chapter 1: [Title]
  - Section 1.1: [Title] [Status]
  - Section 1.2: [Title] [Status]
  ...

Student Instructions:
When you determine the student has mastered a section concept,
emit progress signals to track their learning...
```

---

## Testing Checklist

### Frontend Tests
- [ ] Resume existing course chat on page reload
- [ ] Create new chat in course (chat_id gets saved)
- [ ] Desktop layout: chat + rightbar side-by-side
- [ ] Mobile layout: toggle button shows/hides rightbar
- [ ] Progress signals extracted and UI updates
- [ ] Heuristic fallback works when AI doesn't emit explicit signals
- [ ] Navigation between courses maintains correct active course context
- [ ] localStorage cleanup on course exit

### Backend Tests
- [ ] `GET /student/courses/<id>/progress` returns correct calculation
- [ ] `PUT /student/courses/<id>/progress` updates section status
- [ ] `PUT /student/courses/<id>/chat` saves chat_id to enrollment
- [ ] Progress percentage calculation (completed_sections / total_sections)
- [ ] Query filters work correctly (enrollment_id, course_id, status)
- [ ] 404 handling for non-existent courses
- [ ] Permission checks (student can only access their courses)

### Integration Tests
- [ ] Full flow: Create course → enroll → chat → progress tracked → resume chat
- [ ] Multiple sections → progress aggregates correctly
- [ ] Support feature still works independently (not broken by changes)
- [ ] Chat history loads correctly on resumption
- [ ] Progress persists across browser sessions

---

## Breaking Changes

**None**. This feature is fully additive:
- Existing Support tickets functionality unchanged
- Existing Chat experience in `/c/` route unchanged
- New course learning route (`/student/classrooms/[id]/learn`) is new
- New database tables/columns added with migrations
- API endpoints are new, no existing endpoints modified

---

## Backward Compatibility

- Students without course enrollments: No impact
- Existing courses without chapters: Works (empty plan, 0% progress)
- Courses with no chat history: Starts fresh conversation
- Old Support tickets: Continue to work as before

---

## Performance Considerations

1. **Progress Calculation**: Aggregates from CourseProgress table
   - Index on (enrollment_id, status) for fast filtering
   - Counts only when needed (on GET /progress endpoint)

2. **Signal Processing**: Done on Chat.svelte (client-side)
   - No blocking operations
   - Regex fresh per call (no /g state issues)
   - Async backend call doesn't block UI

3. **Course Data Caching**: localStorage used for active course
   - Reduces API calls on navigation
   - Cleared on session exit

---

## Future Enhancements

1. **AI Prompt Refinement**: Fine-tune system prompt to get more consistent progress signals
2. **Confidence Scoring**: Weight progress updates by AI confidence score
3. **Batch Progress Updates**: Allow multiple signals in single response
4. **Teacher Dashboard**: Visualize student progress across all enrolled students
5. **Progress Analytics**: Track time spent per section, learning velocity
6. **Mobile App**: Adapt course learning to mobile-first experience
7. **Offline Support**: Cache course structure for offline access
8. **Progress Rollback**: Allow students to reset section progress

---

## Deployment Notes

1. **Database**: Run migrations before deploying backend
2. **Environment**: No new environment variables required
3. **Backwards Compatibility**: Can deploy frontend and backend independently (no tight coupling)
4. **Rollback**: Course progress data persists; feature can be disabled by not visiting `/learn` routes

---

## Code Review Guidance

### Key Areas to Review
1. **courseProgressTracker.ts**: 
   - Signal extraction logic (regex safety)
   - Heuristic detection accuracy
   - localStorage usage (SSR safety)

2. **Chat.svelte modifications**:
   - courseIdProp integration with existing props
   - Event listener cleanup (onDestroy)
   - Progress signal processing (error handling)

3. **Backend routes**:
   - Permission checks (student can't access others' progress)
   - Query performance (indexes, N+1 prevention)
   - Error responses (proper HTTP status codes)

4. **Database schema**:
   - Relationships (FK constraints)
   - Nullable fields justified
   - Migration safety (idempotent operations)

---

## Documentation

- **User Guide**: How to use course learning feature (separate doc)
- **API Documentation**: Swagger/OpenAPI specs for new endpoints (separate doc)
- **Developer Guide**: How to extend progress tracking (in README)

---

## Summary of Changes

| Category | Count | Details |
|----------|-------|---------|
| **New Files** | 2 | +page.svelte (learn route), courseProgressTracker.ts |
| **Modified Files** | 6 | Frontend 5, Backend 1 |
| **New DB Tables** | 2 | CourseEnrollment, CourseProgress |
| **New API Endpoints** | 3 | GET/PUT progress, PUT chat |
| **LOC Added** | ~2500 | Frontend: ~1200, Backend: ~1300 |
| **Tests Required** | 15+ | See Testing Checklist |

---

## Related Issues / PRs

- Previous: Course Management Foundation (created Course, CoursePlan tables)
- Related: Support Feature (standalone tutor) - still independent
- Depends on: AI model with proper prompt injection support

---

## Approval Checklist

- [ ] Code review passed
- [ ] All tests passing
- [ ] Database migrations verified
- [ ] Performance acceptable (< 200ms for progress queries)
- [ ] Documentation updated
- [ ] QA sign-off
- [ ] Product owner approval

---

**Created**: May 20, 2026
**PR Type**: Feature
**Complexity**: High
**Risk Level**: Medium (new tables, but fully additive)
**Estimated Testing Time**: 4-6 hours
