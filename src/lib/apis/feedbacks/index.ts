import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface Feedback {
    id: string;
    user_id: string;
    type: string;
    data: {
        rating: number;
        reason?: string;
        comment?: string;
        model_id?: string;
    };
    meta: {
        message_id: string;
        chat_id: string;
        model_id: string;
    };
    created_at: number;
    updated_at: number;
}

export const getAllFeedbacks = async (token: string): Promise<Feedback[]> => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/evaluations/feedbacks/all`, {
        method: 'GET',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            authorization: `Bearer ${token}`
        }
    })
        .then(async (res) => {
            if (!res.ok) throw await res.json();
            return res.json();
        })
        .catch((err) => {
            error = err.detail;
            console.log(err);
            return null;
        });

    if (error) {
        throw error;
    }

    return res;
}; 