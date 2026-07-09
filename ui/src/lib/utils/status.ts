// Shared status → badge-style + label maps for the teacher/student UI.
// These were duplicated verbatim across five components; keeping them here means
// a colour/label tweak lands everywhere at once.

// ── Learner activity (progress / roster / directory) ────────────────────────
export const activityStatusStyle: Record<string, string> = {
	active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
	idle: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
	not_started: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
};

export const activityStatusLabel: Record<string, string> = {
	active: 'active',
	idle: 'idle',
	not_started: 'not started'
};

// ── Assignment / submission status ──────────────────────────────────────────
export const submissionStatusStyle: Record<string, string> = {
	graded: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
	submitted: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
	auto_submitted: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
	late: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
	missing: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
	pending: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
};

export const submissionStatusLabel: Record<string, string> = {
	graded: 'Graded',
	submitted: 'Submitted',
	auto_submitted: 'Auto-submitted',
	late: 'Submitted late',
	missing: 'Missing',
	pending: 'To do'
};
