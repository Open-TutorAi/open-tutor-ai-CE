import { writable } from 'svelte/store';

// Demo Mode
export const isDemo = writable(false);
export const originalUserData = writable<any>(null);
export const demoData = writable<DemoData>({
	dashboard: {
		progress: 0,
		coursesCompleted: 0,
		currentStreak: 0,
		weeklyGoal: { completed: 0, target: 5 },
		totalLearningHours: 0,
		achievements: 0
	},
	chats: [],
	supports: [],
	assignments: [],
	courses: []
});

// Demo Mode Types
export type DemoData = {
	dashboard: DemoDashboard;
	chats: DemoChat[];
	supports: DemoSupport[];
	assignments: DemoAssignment[];
	courses: DemoCourse[];
};

export type DemoDashboard = {
	progress: number;
	coursesCompleted: number;
	currentStreak: number;
	weeklyGoal: { completed: number; target: number };
	totalLearningHours: number;
	achievements: number;
};

export type DemoChat = {
	id: string;
	title: string;
	models: string[];
	timestamp: number;
	messages: DemoMessage[];
	supportId?: string; // Link to support
};

export type DemoMessage = {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	timestamp: number;
	done?: boolean;
	parentId?: string;
	childrenIds?: string[];
};

export type DemoSupport = {
	id: string;
	title: string;
	description: string;
	progress: number;
	lessons: number;
	category: string;
	difficulty: string;
	chatId?: string; // Link to chat conversation
};

export type DemoAssignment = {
	id: string;
	title: string;
	description: string;
	due: string;
	status: 'pending' | 'in-progress' | 'completed' | 'overdue';
	points: number;
	course: string;
};

export type DemoCourse = {
	id: string;
	name: string;
	teacher: string;
	progress: number;
	students: number;
	thumbnail: string;
};
