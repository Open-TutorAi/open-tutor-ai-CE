// src/lib/utils/activityTracker.ts

/**
 * Activity Tracker for Engagement Monitoring
 * Roadmap v1.1.0 — Personalization & UX
 * 
 * Tracks: page views, clicks, session duration, drop-offs
 * Sends data to backend /api/v1/engagement/track
 */

export class ActivityTracker {
	private sessionStartTime: number | null = null;
	private token: string | null = null;

	constructor() {
		if (typeof window === 'undefined') {
			throw new Error('ActivityTracker must be instantiated in browser only');
		}
		
		this.updateToken();
		this.trackPageView();
		this.startSessionTracking();
		this.trackClicks();
	}

	private trackPageView() {
		this.sendActivity('page_view', 0, { url: window.location.pathname });
	}

	private startSessionTracking() {
		this.sessionStartTime = Date.now();
		this.sendActivity('session_start', 0);

		window.addEventListener('beforeunload', () => {
			if (this.sessionStartTime) {
				const duration = Math.floor((Date.now() - this.sessionStartTime) / 1000);
				this.sendActivity('session_end', duration);
			}
		});

		document.addEventListener('visibilitychange', () => {
			if (document.visibilityState === 'hidden' && this.sessionStartTime) {
				const duration = Math.floor((Date.now() - this.sessionStartTime) / 1000);
				if (duration > 10) {
					this.sendActivity('session_end', duration);
					this.sessionStartTime = Date.now();
				}
			}
		});
	}

	private trackClicks() {
		document.addEventListener('click', (e) => {
			const target = e.target as HTMLElement;
			if (target.tagName === 'BUTTON' || target.tagName === 'A' || target.tagName === 'INPUT') {
				this.sendActivity('click', 0, {
					element: target.tagName,
					id: target.id || null,
					className: target.className || null,
					text: target.textContent?.substring(0, 50) || null
				});
			}
		});
	}

	public trackDropOff(reason: string = 'manual_leave') {
		this.sendActivity('drop_off', 0, { reason });
	}

	public trackFeedback() {
		this.sendActivity('feedback', 0, { type: 'user_feedback' });
	}

	public trackCustom(activityType: string, duration: number = 0, metadata: any = null) {
		this.sendActivity(activityType, duration, metadata);
	}

	// ============================================================
	// FONCTION CORRIGÉE : Envoi en query string (pas body JSON)
	// ============================================================
	private async sendActivity(type: string, duration: number = 0, metadata: any = null) {
		this.updateToken();
		
		if (!this.token) {
			console.debug('[ActivityTracker] No token, skipping track');
			return;
		}

		// Construire l'URL avec les paramètres en query string
		const params = new URLSearchParams();
		params.append('activity_type', type);
		if (duration > 0) {
			params.append('duration', duration.toString());
		}
		if (metadata) {
			params.append('metadata', JSON.stringify(metadata));
		}

		const url = `/api/v1/engagement/track?${params.toString()}`;

		try {
			await fetch(url, {
				method: 'POST',
				headers: {
					'Authorization': `Bearer ${this.token}`
				}
				// PAS de body, PAS de Content-Type: application/json
				// Les paramètres sont dans l'URL (query string)
			});
		} catch (e) {
			console.debug('[ActivityTracker] Failed to track:', e);
		}
	}

	private updateToken() {
		try {
			const userData = localStorage.getItem('user');
			if (userData) {
				const parsed = JSON.parse(userData);
				this.token = parsed.token || null;
			}
			if (!this.token) {
				this.token = localStorage.getItem('token') || null;
			}
		} catch (e) {
			this.token = localStorage.getItem('token') || null;
		}
	}
}