---
name: Feature request
about: Suggest an idea for this project
title: ""
labels: ""
assignees: ""
---

# Feature Request

## Important Notes

- **Before submitting a report**: Please check the Issues or Discussions section to see if a similar issue or feature request has already been posted. It's likely we're already tracking it! If you’re unsure, start a discussion post first. This will help us efficiently focus on improving the project.

- **Collaborate respectfully**: We value a constructive attitude, so please be mindful of your communication. If negativity is part of your approach, our capacity to engage may be limited. We’re here to help if you’re open to learning and communicating positively. Remember, Open TutorAI is a volunteer-driven project managed by a single maintainer and supported by contributors who also have full-time jobs. We appreciate your time and ask that you respect ours.

- **Contributing**: If you encounter an issue, we highly encourage you to submit a pull request or fork the project. We actively work to prevent contributor burnout to maintain the quality and continuity of Open TutorAI.

- **Bug reproducibility**: If a bug cannot be reproduced with a `:main` or `:dev` Docker setup, or a pip install with Python 3.11, it may require additional help from the community. In such cases, we will move it to the "issues" Discussions section due to our limited resources. We encourage the community to assist with these issues. Remember, it’s not that the issue doesn’t exist; we need your help!

Note: Please remove the notes above when submitting your post. Thank you for your understanding and support!

---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

## Architecture (required before implementation)

**OpenWebUI-first (UI changes only)**
The `ui/` frontend is based on OpenWebUI. Does OpenWebUI already implement this feature or a similar pattern? If yes, reference the component/page so the implementation stays aligned. If no, explain why a new pattern is needed.

**Domain boundary (backend changes only)**
Which domain owns this feature: `accounts`, `learning`, `ai`, `content`, `governance`, or `system`? Does it follow the repository → service → router pattern, or does it need a new domain?

**API contract**
List the new/changed endpoints (`/api/v1/...`) and the matching UI client (`ui/src/lib/apis/<domain>/index.ts`). Every UI `fetch()` must have a backend route (enforced by the contract test).

**Test plan (TDD)**
Which tests will be written first? Backend: `tests/test_<domain>.py` covering success, auth/ownership, missing resource, and validation. Frontend: Vitest where applicable.

**Documentation impact**
Which docs need updating: `AGENTS.md` (conventions/architecture), `docs/`, README, or the i18n locales (AR/FR/EN)?

**Additional context**
Add any other context or screenshots about the feature request here.
