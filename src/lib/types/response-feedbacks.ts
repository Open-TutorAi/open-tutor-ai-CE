import type { ResponseComparisonFeedback } from '$lib/apis/response-feedbacks';

export interface FeedbackResponse {
    id: string;
    user_id: string;
    version: number;
    type: string;
    data: {
        preferredResponseId: string;
        reason: string;
        timestamp: string;
        questionId: string;
        question?: string;
        responses: Array<{
            id: string;
            content: string;
            modelName?: string;
        }>;
    };
    created_at: number;
    updated_at: number;
    meta: any;
    snapshot: any;
}

export interface FeedbackDisplay {
    id: string;
    preferredResponseId: string;
    reason: string;
    timestamp: string;
    questionId: string;
    question?: string;
    responses: Array<{
        id: string;
        content: string;
        modelName?: string;
    }>;
    userId: string;
} 