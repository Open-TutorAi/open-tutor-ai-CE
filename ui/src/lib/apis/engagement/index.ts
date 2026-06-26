import { TUTOR_API_BASE_URL } from '$lib/constants';

const authHeaders = (token: string) => ({
	'Content-Type': 'application/json',
	...(token ? { Authorization: `Bearer ${token}` } : {})
});

const handle = async (res: Response) => {
	if (!res.ok) throw await res.json().catch(() => ({ detail: res.statusText }));
	return res.json();
};

/** Send a base64 webcam frame and receive the live video engagement score. */
export const sendVideoFrame = async (
	token: string,
	frame: string,
	sessionId: string | null = null
) => {
	const res = await fetch(`${TUTOR_API_BASE_URL}/engagement/video`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({ frame, session_id: sessionId })
	});
	return handle(res);
};

/** Send a base64 voice clip for audio engagement scoring. */
export const sendAudioChunk = async (
	token: string,
	audio: string,
	sessionId: string | null = null,
	durationSeconds: number | null = null,
	message: string | null = null,
	videoScore: number | null = null
) => {
	const res = await fetch(`${TUTOR_API_BASE_URL}/engagement/audio`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({
			audio,
			session_id: sessionId,
			duration_seconds: durationSeconds,
			message,
			video_score: videoScore
		})
	});
	return handle(res);
};

/** Record a text (or transcribed-voice) engagement event. */
export const sendChatEngagement = async (
	token: string,
	message: string,
	opts: {
		sessionId?: string | null;
		isVoice?: boolean;
		audio?: string | null;
		durationSeconds?: number | null;
		videoScore?: number | null;
	} = {}
) => {
	const res = await fetch(`${TUTOR_API_BASE_URL}/engagement/chat`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({
			message,
			session_id: opts.sessionId ?? null,
			is_voice: opts.isVoice ?? false,
			audio: opts.audio ?? null,
			duration_seconds: opts.durationSeconds ?? null,
			video_score: opts.videoScore ?? null
		})
	});
	return handle(res);
};

/** Fetch the weighted overall engagement score for a session. */
export const getSessionScore = async (token: string, sessionId: string) => {
	const res = await fetch(`${TUTOR_API_BASE_URL}/engagement/session/${sessionId}/score`, {
		method: 'GET',
		headers: authHeaders(token)
	});
	return handle(res);
};

/** Fetch recent engagement rows + averages for a session. */
export const getSessionSummary = async (token: string, sessionId: string, limit = 50) => {
	const res = await fetch(
		`${TUTOR_API_BASE_URL}/engagement/session/${sessionId}/summary?limit=${limit}`,
		{
			method: 'GET',
			headers: authHeaders(token)
		}
	);
	return handle(res);
};
