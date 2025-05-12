import { TUTOR_API_BASE_URL } from '$lib/constants';

// Types
export interface SupportFile {
    id: string;
    filename: string;
    file_type?: string;
    file_size?: number;
}

export interface SupportCreateRequest {
    title: string;
    short_description?: string;
    subject: string;
    custom_subject?: string;
    course_id?: string;
    learning_objective?: string;
    learning_type?: string;
    level?: string;
    content_language?: string;
    estimated_duration?: string;
    access_type?: string;
    keywords?: string[];
    start_date?: string;
    end_date?: string;
    avatar_id?: string;
}

export interface SupportResponse {
    id: string;
    user_id: string;
    title: string;
    short_description?: string;
    subject: string;
    custom_subject?: string;
    course_id?: string;
    learning_objective?: string;
    learning_type?: string;
    level?: string;
    content_language?: string;
    estimated_duration?: string;
    access_type?: string;
    keywords?: string[];
    start_date?: string;
    end_date?: string;
    avatar_id?: string;
    status: string;
    chat_id?: string;
    created_at: string;
    updated_at?: string;
}

/**
 * Create a new support request in the database
 * @param token - Authentication token
 * @param data - Support request data
 * @returns A promise that resolves to the created support
 */
export const createSupport = async (token: string, data: SupportCreateRequest) => {
    let error = null;

    // Log for debugging
    console.log(`Creating support request with token: ${token.substring(0, 5)}...`);
    console.log('Support data:', JSON.stringify(data));

    const res = await fetch(`${TUTOR_API_BASE_URL}/supports/create`, {
        method: 'POST',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            authorization: `Bearer ${token}`
        },
        body: JSON.stringify(data)
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

/**
 * Upload a file for a support request
 * @param token - Authentication token
 * @param supportId - ID of the support request
 * @param file - File to upload
 * @returns A promise that resolves to the uploaded file info
 */
export const uploadSupportFile = async (token: string, supportId: string, file: File) => {
    let error = null;

    const formData = new FormData();
    formData.append('support_id', supportId);
    formData.append('file', file);

    const res = await fetch(`${TUTOR_API_BASE_URL}/supports/upload-file`, {
        method: 'POST',
        headers: {
            authorization: `Bearer ${token}`
        },
        body: formData
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

/**
 * Get a list of support requests for the current user
 * @param token - Authentication token
 * @param status - Optional status filter
 * @returns A promise that resolves to an array of support requests
 */
export const getSupportRequests = async (token: string, status?: string) => {
    let error = null;

    const url = status 
        ? `${TUTOR_API_BASE_URL}/supports/list?status=${status}` 
        : `${TUTOR_API_BASE_URL}/supports/list`;
        
    const res = await fetch(url, {
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

/**
 * Get a specific support request by ID
 * @param token - Authentication token
 * @param supportId - ID of the support request to retrieve
 * @returns A promise that resolves to the support request
 */
export const getSupportById = async (token: string, supportId: string) => {
    let error = null;

    const res = await fetch(`${TUTOR_API_BASE_URL}/supports/${supportId}`, {
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

export const updateSupportChatId = async (token: string, supportId: string, chatId: string) => {
    try {
        // Input validation
        if (!supportId || !chatId || supportId.trim() === '' || chatId.trim() === '') {
            console.error('Invalid parameters for updateSupportChatId', { supportId, chatId });
            throw new Error('Invalid supportId or chatId');
        }
        
        console.log(`Updating support ${supportId} with chat ID ${chatId}`);
        
        // Make sure supportId and chatId are properly formatted
        const encodedSupportId = encodeURIComponent(supportId.trim());
        const encodedChatId = encodeURIComponent(chatId.trim());
        
        // Construct the API URL with query parameter
        const url = `${TUTOR_API_BASE_URL}/supports/${encodedSupportId}/update-chat?chat_id=${encodedChatId}`;
        console.log('Making API request to:', url);
        
        const res = await fetch(url, {
            method: 'PATCH',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            credentials: 'include'
        });

        console.log('API response status:', res.status);
        
        if (!res.ok) {
            let errorData;
            try {
                errorData = await res.json();
            } catch (e) {
                errorData = { detail: `Failed API request with status ${res.status}` };
            }
            console.error('Support update error:', errorData, 'Status:', res.status);
            throw errorData.detail || `Failed to update support chat ID (${res.status})`;
        }

        let data;
        try {
            data = await res.json();
        } catch (e) {
            console.warn('Could not parse response as JSON, assuming success');
            data = { status: 'success', message: 'Update processed' };
        }
        
        console.log('Support chat ID update successful:', data);
        return data;
    } catch (error) {
        console.error('Error in updateSupportChatId:', error);
        throw error;
    }
}; 