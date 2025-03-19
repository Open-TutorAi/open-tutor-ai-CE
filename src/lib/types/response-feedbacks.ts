import type { ResponseComparisonFeedback } from '$lib/apis/response-feedbacks';

export interface FeedbackResponse {
    id: string;
    data: ResponseComparisonFeedback;
}

export interface FeedbackDisplay {
    id: string;
    preferredResponseId: string;
    reason: string;
    timestamp: number;
    questionId: string;
    responses: {
        id: string;
        content: string;
        modelName?: string;
    }[];
} 