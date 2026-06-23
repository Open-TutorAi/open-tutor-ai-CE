import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface ErrorCard {
    id: string;
    support_id: string;
    user_id: string;
    concept: string;
    error_description: string;
    simple_explanation: string;
    correct_example: string;
    created_at: string | null;
}

/**
 * Analyse le dernier échange (user → assistant) du chat de support.
 * Retourne toutes les fiches d'erreur détectées (0, 1 ou plusieurs).
 */
export const analyzeExchangeForErrorCard = async (
    token: string,
    supportId: string,
    userMessage: string,
    assistantMessage: string,
    model: string
): Promise<ErrorCard[]> => {
    let error: string | null = null;

    const res = await fetch(
        `${TUTOR_API_BASE_URL}/supports/${supportId}/error-cards/analyze`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Accept: 'application/json',
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({
                user_message: userMessage,
                assistant_message: assistantMessage,
                model
            })
        }
    )
        .then(async (r) => {
            if (!r.ok) {
                error = await r.text();
                return null;
            }
            return r.json();
        })
        .catch((err) => {
            error = err?.message ?? String(err);
            return null;
        });

    if (error) {
        console.error('[error-cards] analyze failed:', error);
        return [];
    }
    return (res?.cards as ErrorCard[]) ?? [];
};

/**
 * Liste toutes les fiches d'erreur d'un support pour l'utilisateur courant.
 */
export const listErrorCards = async (
    token: string,
    supportId: string
): Promise<ErrorCard[]> => {
    let error: string | null = null;

    const res = await fetch(
        `${TUTOR_API_BASE_URL}/supports/${supportId}/error-cards`,
        {
            method: 'GET',
            headers: {
                Accept: 'application/json',
                Authorization: `Bearer ${token}`
            }
        }
    )
        .then(async (r) => {
            if (!r.ok) {
                error = await r.text();
                return null;
            }
            return r.json();
        })
        .catch((err) => {
            error = err?.message ?? String(err);
            return null;
        });

    if (error) {
        console.error('[error-cards] list failed:', error);
        return [];
    }
    return (res as ErrorCard[]) ?? [];
};

/**
 * Supprime une fiche d'erreur (doit appartenir à l'utilisateur courant).
 */
export const deleteErrorCard = async (
    token: string,
    supportId: string,
    cardId: string
): Promise<boolean> => {
    const res = await fetch(
        `${TUTOR_API_BASE_URL}/supports/${supportId}/error-cards/${cardId}`,
        {
            method: 'DELETE',
            headers: {
                Accept: 'application/json',
                Authorization: `Bearer ${token}`
            }
        }
    ).catch((err) => {
        console.error('[error-cards] delete failed:', err);
        return null;
    });

    return !!res && res.ok;
};
