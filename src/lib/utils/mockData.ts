import type { DemoData } from '$lib/stores';

export function generateDemoData(): DemoData {
	const chats = generateDemoChats();
	const supports = generateDemoSupports(chats);
	
	return {
		dashboard: generateDemoDashboard(supports),
		chats,
		supports,
		assignments: generateDemoAssignments(),
		courses: generateDemoCourses()
	};
}

function generateDemoDashboard(supports: any[]) {
	// Calculate average progress from all supports
	const avgProgress = supports.length > 0
		? Math.round(supports.reduce((sum, s) => sum + s.progress, 0) / supports.length)
		: 0;
	
	return {
		progress: avgProgress,
		coursesCompleted: 3,
		currentStreak: 12,
		weeklyGoal: { completed: 8, target: 10 },
		totalLearningHours: 127,
		achievements: 15
	};
}

function generateDemoChats() {
	const now = Date.now();
	return [
		{
			id: 'demo-chat-1',
			title: 'Understanding Photosynthesis',
			models: ['gpt-4'],
			timestamp: now - 3600000 * 2,
			supportId: 'demo-support-1', // Link to Biology support
			messages: [
				{
					id: 'msg-1',
					role: 'user',
					content: 'Can you explain photosynthesis in simple terms?',
					timestamp: now - 3600000 * 2
				},
				{
					id: 'msg-2',
					role: 'assistant',
					content:
						"Photosynthesis is how plants make their own food! Think of it like this: plants are like tiny solar-powered factories. They use sunlight as energy, take in carbon dioxide from the air through tiny holes in their leaves, and absorb water through their roots.\n\nThen, they combine all these ingredients to create glucose (a type of sugar) that gives them energy to grow. As a bonus, they release oxygen into the air, which is what we breathe!\n\nThe simple equation is:\nSunlight + Water + Carbon Dioxide → Glucose + Oxygen\n\nIt's like plants are doing us a favor by cleaning the air and giving us oxygen while they make their food!",
					timestamp: now - 3600000 * 2 + 5000
				},
				{
					id: 'msg-3',
					role: 'user',
					content: 'What is chlorophyll and why are plants green?',
					timestamp: now - 3600000 * 2 + 10000
				},
				{
					id: 'msg-4',
					role: 'assistant',
					content:
						"Great question! Chlorophyll is the special green pigment in plants that makes photosynthesis possible. It's like the solar panel of the plant.\n\nHere's why plants look green:\n- Chlorophyll absorbs red and blue light from the sun\n- But it reflects green light\n- Since green light bounces off the leaves instead of being absorbed, that's the color we see!\n\nChlorophyll is found in tiny structures called chloroplasts inside plant cells. These chloroplasts are like little power plants, working hard to convert sunlight into energy.",
					timestamp: now - 3600000 * 2 + 15000
				}
			]
		},
		{
			id: 'demo-chat-2',
			title: 'Algebra Fundamentals',
			models: ['gpt-4'],
			timestamp: now - 86400000,
			supportId: 'demo-support-2', // Link to Algebra support
			messages: [
				{
					id: 'msg-1',
					role: 'user',
					content: 'I need help understanding how to solve equations with variables on both sides.',
					timestamp: now - 86400000
				},
				{
					id: 'msg-2',
					role: 'assistant',
					content:
						"I'd be happy to help you with that! Solving equations with variables on both sides involves getting all the variable terms on one side and all the constant terms on the other side.\n\nLet's work through an example:\n3x + 5 = 2x + 12\n\nStep 1: Get all x terms on one side\nSubtract 2x from both sides:\n3x - 2x + 5 = 2x - 2x + 12\nx + 5 = 12\n\nStep 2: Get the constant alone\nSubtract 5 from both sides:\nx + 5 - 5 = 12 - 5\nx = 7\n\nThe key principle is: whatever you do to one side, you must do to the other side to keep the equation balanced!\n\nWould you like to try a problem yourself?",
					timestamp: now - 86400000 + 5000
				}
			]
		},
		{
			id: 'demo-chat-3',
			title: 'Creative Writing - Character Development',
			models: ['gpt-4'],
			timestamp: now - 172800000,
			supportId: 'demo-support-3', // Link to Creative Writing support
			messages: [
				{
					id: 'msg-1',
					role: 'user',
					content: 'How do I create compelling characters for my story?',
					timestamp: now - 172800000
				},
				{
					id: 'msg-2',
					role: 'assistant',
					content:
						"Creating compelling characters is one of the most exciting parts of writing! Here are key elements to focus on:\n\n**1. Give them depth and flaws**\n   - Perfect characters are boring\n   - Flaws make characters relatable and human\n   - Internal conflicts create interesting character arcs\n\n**2. Create a detailed backstory**\n   - Where did they come from?\n   - What experiences shaped who they are?\n   - What are their fears and dreams?\n\n**3. Make their motivations clear**\n   - What do they want more than anything?\n   - What's stopping them from getting it?\n   - How far will they go to achieve their goals?\n\n**4. Show, don't tell**\n   - Reveal character through actions, not descriptions\n   - Let dialogue reflect their personality\n   - Use body language and reactions\n\n**5. Give them a unique voice**\n   - How do they speak?\n   - What phrases do they use?\n   - How do they see the world differently?\n\nRemember: Your characters should feel like real people with complex emotions and contradictions. They should surprise you sometimes!",
					timestamp: now - 172800000 + 8000
				}
			]
		}
	];
}

function generateDemoSupports(chats: any[]) {
	return [
		{
			id: 'demo-support-1',
			title: 'Introduction to Biology',
			description:
				'Explore the fundamentals of life sciences, from cells to ecosystems. Learn about genetics, evolution, and the diversity of living organisms.',
			progress: 78,
			lessons: 20,
			category: 'Science',
			difficulty: 'Beginner',
			chatId: 'demo-chat-1' // Has existing conversation
		},
		{
			id: 'demo-support-2',
			title: 'Algebra Mastery',
			description:
				'Master algebraic concepts including equations, inequalities, functions, and polynomials. Build a strong foundation for advanced mathematics.',
			progress: 45,
			lessons: 15,
			category: 'Mathematics',
			difficulty: 'Intermediate',
			chatId: 'demo-chat-2' // Has existing conversation
		},
		{
			id: 'demo-support-3',
			title: 'Creative Writing Workshop',
			description:
				'Develop your storytelling skills through guided exercises in narrative structure, character development, and descriptive writing.',
			progress: 23,
			lessons: 12,
			category: 'Language Arts',
			difficulty: 'Beginner',
			chatId: 'demo-chat-3' // Has existing conversation
		}
	];
}

function generateDemoAssignments() {
	const today = new Date();
	const tomorrow = new Date(today);
	tomorrow.setDate(tomorrow.getDate() + 1);
	const nextWeek = new Date(today);
	nextWeek.setDate(nextWeek.getDate() + 7);
	const lastWeek = new Date(today);
	lastWeek.setDate(lastWeek.getDate() - 7);

	return [
		{
			id: 'demo-assign-1',
			title: 'Essay: Climate Change Impact',
			description:
				'Write a 500-word essay discussing the impact of climate change on coastal ecosystems.',
			due: tomorrow.toISOString().split('T')[0],
			status: 'pending' as const,
			points: 100,
			course: 'Environmental Science'
		},
		{
			id: 'demo-assign-2',
			title: 'Math Quiz: Chapter 3',
			description: 'Complete the online quiz covering linear equations and graphing.',
			due: nextWeek.toISOString().split('T')[0],
			status: 'pending' as const,
			points: 50,
			course: 'Algebra II'
		},
		{
			id: 'demo-assign-3',
			title: 'Biology Lab Report',
			description: 'Submit your observations and analysis from the photosynthesis experiment.',
			due: lastWeek.toISOString().split('T')[0],
			status: 'completed' as const,
			points: 75,
			course: 'Biology 101'
		},
		{
			id: 'demo-assign-4',
			title: 'History Timeline Project',
			description: 'Create a visual timeline of major events in World War II.',
			due: today.toISOString().split('T')[0],
			status: 'in-progress' as const,
			points: 150,
			course: 'World History'
		},
		{
			id: 'demo-assign-5',
			title: 'Literature Review: Shakespeare',
			description: 'Write a critical analysis of themes in Romeo and Juliet.',
			due: nextWeek.toISOString().split('T')[0],
			status: 'pending' as const,
			points: 100,
			course: 'English Literature'
		},
		{
			id: 'demo-assign-6',
			title: 'Chemistry Problem Set',
			description: 'Solve problems 1-20 on stoichiometry and chemical reactions.',
			due: (new Date(today.getTime() - 2 * 86400000)).toISOString().split('T')[0],
			status: 'overdue' as const,
			points: 60,
			course: 'Chemistry'
		}
	];
}

function generateDemoCourses() {
	return [
		{
			id: 'demo-course-1',
			name: 'Biology 101',
			teacher: 'Dr. Sarah Mitchell',
			progress: 72,
			students: 28,
			thumbnail: '/images/background.jpeg'
		},
		{
			id: 'demo-course-2',
			name: 'Algebra II',
			teacher: 'Mr. James Rodriguez',
			progress: 58,
			students: 32,
			thumbnail: '/images/background.jpeg'
		},
		{
			id: 'demo-course-3',
			name: 'World History',
			teacher: 'Ms. Emily Chen',
			progress: 85,
			students: 25,
			thumbnail: '/images/background.jpeg'
		}
	];
}

