import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface ResponseComparisonFeedback {
    preferredResponseId: string;
    reason: string;
    timestamp: number;
    questionId: string;
    question: string;
    responses: {
        id: string;
        content: string;
        modelName?: string;
    }[];
}

export const getAllResponseFeedbacks = async (token: string = '') => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/evaluations/response-feedbacks/all`, {
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
        .then((json) => {
            return json;
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

export const createResponseFeedback = async (token: string, feedback: ResponseComparisonFeedback) => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/evaluations/response-feedback`, {
        method: 'POST',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
            type: 'response_comparison',
            data: feedback
        })
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

export const getResponseFeedbackById = async (token: string, feedbackId: string) => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/evaluations/response-feedback/${feedbackId}`, {
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
        .then((json) => {
            return json;
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