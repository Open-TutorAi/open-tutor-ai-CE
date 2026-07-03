import { TUTOR_API_BASE_URL } from '$lib/constants';

export type SubjectStat = {
	subject: string;
	percentage: number;
	total_count: number;
};

export type PerformanceData = {
	completion_rate: number;
	tutorials_completed: number;
	total_tutorials: number;
	total_points: number;
};

export type CalendarData = {
	year: number;
	month: number;
	active_days: number[];
	week_start?: string;
};

export type DailyHours = {
	day: string;
	hours: number;
};

export type ProductivityData = {
	streak: number;
	total_sessions: number;
	weekly_hours: number;
	daily_hours: DailyHours[];
};

export async function getDashboardStatistics(
	token: string,
	opts?: { year?: number; month?: number; startDate?: string }
): Promise<SubjectStat[]> {
	const params = new URLSearchParams();
	if (opts?.year) params.set('year', String(opts.year));
	if (opts?.month) params.set('month', String(opts.month));
	if (opts?.startDate) params.set('start_date', opts.startDate);
	const search = params.size ? '?' + params.toString() : '';
	const res = await fetch(`${TUTOR_API_BASE_URL}/dashboard/statistics` + search, {
		method: 'GET',
		headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
	});
	if (!res.ok) throw new Error('Failed to fetch statistics');
	return res.json();
}

export async function getDashboardPerformance(
	token: string,
	opts?: { year?: number; month?: number; startDate?: string }
): Promise<PerformanceData> {
	const params = new URLSearchParams();
	if (opts?.year) params.set('year', String(opts.year));
	if (opts?.month) params.set('month', String(opts.month));
	if (opts?.startDate) params.set('start_date', opts.startDate);
	const search = params.size ? '?' + params.toString() : '';
	const res = await fetch(`${TUTOR_API_BASE_URL}/dashboard/performance` + search, {
		method: 'GET',
		headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
	});
	if (!res.ok) throw new Error('Failed to fetch performance');
	return res.json();
}

export async function getDashboardCalendar(
	token: string,
	year?: number,
	month?: number,
	startDate?: string
): Promise<CalendarData> {
	const params = new URLSearchParams();
	if (year) params.set('year', String(year));
	if (month) params.set('month', String(month));
	if (startDate) params.set('start_date', startDate);
	const search = params.size ? '?' + params.toString() : '';
	const res = await fetch(`${TUTOR_API_BASE_URL}/dashboard/calendar` + search, {
		method: 'GET',
		headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
	});
	if (!res.ok) throw new Error('Failed to fetch calendar');
	return res.json();
}

export async function getDashboardProductivity(token: string): Promise<ProductivityData> {
	const res = await fetch(`${TUTOR_API_BASE_URL}/dashboard/productivity`, {
		method: 'GET',
		headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
	});
	if (!res.ok) throw new Error('Failed to fetch productivity');
	return res.json();
}
