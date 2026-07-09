// Small shared formatting helpers used across the teacher/student UI.
// Previously each component re-implemented these inline (and drifted).

const DASH = '—';

/** Localised date only (no time). `—` for null/empty. */
export const fmtDate = (ts?: string | null): string =>
	ts ? new Date(ts).toLocaleDateString() : DASH;

/** Localised date + time. `—` for null/empty, empty string for an unparseable value. */
export const fmtDateTime = (ts?: string | null): string => {
	if (!ts) return DASH;
	const d = new Date(ts);
	return isNaN(d.getTime()) ? '' : d.toLocaleString();
};

/** Human-readable byte size (B / KB / MB). `—` for null. */
export const fmtSize = (bytes: number | null): string => {
	if (bytes == null) return DASH;
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

/** Trigger a browser download for a blob under the given filename. */
export const downloadBlob = (blob: Blob, filename: string): void => {
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename;
	a.click();
	URL.revokeObjectURL(url);
};
