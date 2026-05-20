import { TUTOR_API_BASE_URL } from '$lib/constants';

export interface TopSubject {
    name: string;
    count: number;
}

export interface LatestActivity {
    id: string;
    title: string;
    subject: string;
    status: string;
    updatedAt: string | null;
}

export interface DashboardStatsResponse {
    totalSupports: number;
    activeSupports: number;
    completedSupports: number;
    completionRate: number;
    topSubjects: TopSubject[];
    latestActivity: LatestActivity | null;
    lastUpdated: string;
}

/**
 * Fetch student dashboard statistics from the backend
 * @param token - Authentication token
 * @returns Promise with DashboardStatsResponse or null
 */
export const getDashboardStats = async (
    token: string,
    startDate?: string,
    endDate?: string
): Promise<DashboardStatsResponse | null> => {
    let error = null;

    let url = `${TUTOR_API_BASE_URL}/dashboard/stats`;
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    if (params.toString()) {
        url += `?${params.toString()}`;
    }

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
        .catch((err) => {
            error = err.detail || err;
            console.error('Error fetching dashboard stats:', err);
            return null;
        });

    if (error) {
        throw error;
    }

    return res;
};
