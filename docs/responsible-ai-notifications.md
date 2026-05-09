# Responsible AI Notification Design

This note defines a safe implementation shape for learner-facing notifications when tutor responses may be uncertain, incomplete, or outside the intended educational role.

## Goals

- Help learners recognize when a response needs additional scrutiny.
- Keep the tutor transparent without interrupting normal learning flow.
- Separate learner guidance from administrative review and audit logging.
- Avoid collecting unnecessary personal data when evaluating a response.

## Notification levels

| Level | Use when | Learner-facing behavior |
| --- | --- | --- |
| `info` | The response is useful but may benefit from source checking or more context. | Show a small inline note such as "Check the provided sources before using this answer." |
| `caution` | The response is uncertain, partially grounded, or based on weak retrieval evidence. | Show a visible banner explaining why review is recommended and offer a follow-up action. |
| `blocked` | The request is outside the tutor role or asks for unsupported high-impact advice. | Provide a short refusal or redirection and suggest contacting a qualified person where appropriate. |

## Trigger categories

Notifications should be driven by explicit signals rather than broad keyword matching alone.

- Low retrieval support: no sources, weak semantic match, or conflicting sources.
- Model uncertainty: low confidence metadata when available, repeated self-correction, or incomplete answer state.
- Role boundary: requests for medical, legal, financial, disciplinary, or other high-impact decisions.
- Academic integrity: requests to complete graded work without learning support.
- Safety or wellbeing: content where the tutor should avoid acting as a counselor, clinician, or emergency responder.
- System limits: unavailable model, failed tool call, missing course context, or stale classroom material.

## UX requirements

- Keep notifications brief and specific to the issue.
- Do not shame the learner or imply misconduct without evidence.
- Provide a next step, such as "ask for an example", "request sources", "contact an instructor", or "try a simpler explanation".
- Use accessible color contrast and include text labels; do not rely on color alone.
- Make notification copy localizable through the existing i18n workflow.
- Preserve chat continuity so the learner can keep studying after the notice.

## Data handling

- Store the minimum event data needed for product improvement and quality review.
- Avoid logging full learner submissions when a category, timestamp, and model identifier are sufficient.
- If full content is retained for review, make that retention explicit in the privacy policy and admin documentation.
- Keep learner-facing notices separate from internal moderation labels so private review metadata is not exposed in the UI.

## Suggested event shape

```json
{
  "message_id": "response-message-id",
  "level": "caution",
  "category": "low_retrieval_support",
  "reason": "No course source passed the configured relevance threshold.",
  "created_at": "2026-05-09T00:00:00Z",
  "model_id": "configured-model-id",
  "visible_to_learner": true
}
```

## Validation checklist

- A normal answer with good sources shows no warning.
- A weakly grounded answer shows a caution notice and an option to ask for sources.
- A role-boundary request is redirected without providing unsupported advice.
- Keyboard and screen-reader users can perceive the notification and any action buttons.
- Notifications are included in exported chat transcripts only when they were visible to the learner.
- Administrators can review aggregate notification rates without exposing unnecessary learner content.

