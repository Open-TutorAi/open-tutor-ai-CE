# Intelligent Flashcards System

## Overview
The Intelligent Flashcards system allows students to automatically generate revision cards from their course notes (text or PDF) using local AI (Ollama). It implements the Leitner spaced repetition algorithm to optimize long-term memorization and offers two interactive revision modes: Quiz (typing answers with fuzzy validation) and Flip (classic 3D flip cards).

## Who uses it
- **Student**: The primary user who generates, manages, and reviews flashcards.

## Data Involved
A new `Flashcard` table was created in the database with the following structure:
- `id` (UUID): Unique identifier.
- `user_id` (UUID): Owner of the card.
- `question` (Text): The question side of the card.
- `answer` (Text): The answer side of the card.
- `tag` (String): Subject/category (e.g., "Philosophy", "Python").
- `box` (Integer): Leitner box level (1 to 5).
- `next_review` (DateTime): Scheduled date for the next review.
- `times_reviewed` (Integer): Total number of times the card was reviewed.
- `times_correct` (Integer): Total number of correct answers.
- `created_at` / `updated_at` (DateTime): Timestamps.

## Endpoints Added
### Generation
- `POST /api/v1/flashcards/generate`: Generates flashcards from plain text.
- `POST /api/v1/flashcards/generate-from-pdf`: Extracts text from an uploaded PDF and generates flashcards.

### Revision & Management
- `GET /api/v1/flashcards/due`: Retrieves cards due for review.
- `GET /api/v1/flashcards/due/{tag}`: Retrieves cards due for review, filtered by tag.
- `POST /api/v1/flashcards/review`: Records a review (correct/incorrect) and updates the Leitner box.
- `GET /api/v1/flashcards/tags`: Lists all tags used by the student.
- `GET /api/v1/flashcards/stats`: Returns mastery statistics.
- `DELETE /api/v1/flashcards/{card_id}`: Deletes a specific card.
- `DELETE /api/v1/flashcards/delete-all`: Deletes all cards for the current user.

## Files Changed or Created
### Backend
- `ai/llm/flashcard_generator.py`: AI generation logic with strict validation to prevent hallucinations.
- `ai/pdf/pdf_extractor.py`: PDF text extraction using `pdfplumber`.
- `data/models/flashcard.py`: SQLAlchemy model for flashcards.
- `data/repositories/flashcard_repository.py`: Database queries and Leitner logic.
- `gateway/http/routers/flashcards.py`: FastAPI routes.

### Frontend
- `ui/src/lib/apis/flashcards/index.ts`: API client functions.
- `ui/src/lib/features/student/components/flashcards/pages/QuizReview.svelte`: Quiz mode component.
- `ui/src/lib/features/student/components/flashcards/pages/FlashcardReview.svelte`: Flip mode component.
- `ui/src/routes/student/flashcards/+page.svelte`: Dashboard with statistics.
- `ui/src/routes/student/flashcards/generate/+page.svelte`: Generation page.
- `ui/src/routes/student/flashcards/review/+page.svelte`: Revision page.
- `ui/src/lib/icons/Flashcards.svelte`: Sidebar icon.
- `ui/src/lib/features/student/components/elements/Sidebar.svelte`: Added navigation link.

## What Changed
- **Added**: Complete AI-powered flashcard generation (text & PDF).
- **Added**: Interactive Quiz mode with Levenshtein fuzzy validation.
- **Added**: Flip mode with 3D CSS animations.
- **Added**: Leitner spaced repetition algorithm (5 mastery levels).
- **Added**: Tag system for subject organization.
- **Added**: Student dashboard with real-time statistics.
- **Fixed**: AI context reset between generations to prevent memory leakage.
- **Fixed**: Strict answer validation to ensure generated content strictly matches the source text.