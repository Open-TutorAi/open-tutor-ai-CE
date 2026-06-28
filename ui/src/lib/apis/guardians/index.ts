/**
 * Guardian / Parent API service
 *
 * PLACEHOLDER — backend endpoints not yet implemented.
 * Expected routes (to be added to gateway/http/routers/guardians.py):
 *
 *   GET  /api/v1/guardians/student/{student_id}           → Guardian[]
 *   POST /api/v1/guardians/student/{student_id}/invite    → Guardian
 *   POST /api/v1/guardians/{guardian_id}/resend           → { message: string }
 *   GET  /api/v1/guardians/{guardian_id}/contact          → GuardianContact
 */

import { TUTOR_API_BASE_URL } from '$lib/constants';

// ─── Types ───────────────────────────────────────────────────────────────────

export type GuardianRelationship = 'Mother' | 'Father' | 'Guardian' | 'Other';
export type GuardianStatus = 'active' | 'pending';

export interface Guardian {
    id: string;
    student_id: string;
    name: string;
    email: string;
    relationship: GuardianRelationship;
    status: GuardianStatus;
    linked_at: string | null;
}

export interface InviteGuardianRequest {
    email: string;
    relationship: GuardianRelationship;
}

export interface GuardianContact {
    id: string;
    name: string;
    email: string;
    phone?: string;
    relationship: GuardianRelationship;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function apiFetch<T>(
    url: string,
    token: string,
    options: RequestInit = {}
): Promise<T> {
    let error: string | null = null;

    const res = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
            ...(options.headers ?? {})
        }
    })
        .then(async (r) => {
            if (!r.ok) throw await r.json();
            return r.json() as Promise<T>;
        })
        .catch((err) => {
            error = err?.detail ?? String(err);
            return null;
        });

    if (error) throw new Error(error);
    return res as T;
}

// ─── Endpoints ───────────────────────────────────────────────────────────────

/** Fetch all guardians linked to a student. */
export const getStudentGuardians = (token: string, studentId: string): Promise<Guardian[]> =>
    apiFetch<Guardian[]>(`${TUTOR_API_BASE_URL}/guardians/student/${studentId}`, token);

/**
 * Send an invitation to a parent/guardian.
 * Creates a Guardian record with status = 'pending'.
 */
export const inviteGuardian = (
    token: string,
    studentId: string,
    data: InviteGuardianRequest
): Promise<Guardian> =>
    apiFetch<Guardian>(`${TUTOR_API_BASE_URL}/guardians/student/${studentId}/invite`, token, {
        method: 'POST',
        body: JSON.stringify(data)
    });

/** Resend the invitation email for a pending guardian. */
export const resendInvitation = (token: string, guardianId: string): Promise<{ message: string }> =>
    apiFetch<{ message: string }>(`${TUTOR_API_BASE_URL}/guardians/${guardianId}/resend`, token, {
        method: 'POST'
    });

/** Fetch contact details for an active guardian. */
export const getGuardianContact = (token: string, guardianId: string): Promise<GuardianContact> =>
    apiFetch<GuardianContact>(`${TUTOR_API_BASE_URL}/guardians/${guardianId}/contact`, token);
