export async function simulateAIResponse(
	prompt: string,
	onChunk: (chunk: string) => void,
	onComplete: () => void
): Promise<void> {
	const response = generateMockResponse(prompt);
	const words = response.split(' ');
	
	for (let i = 0; i < words.length; i++) {
		const word = i === 0 ? words[i] : ' ' + words[i];
		onChunk(word);
		
		await sleep(50 + Math.random() * 100);
	}
	
	onComplete();
}

function sleep(ms: number): Promise<void> {
	return new Promise(resolve => setTimeout(resolve, ms));
}

function generateMockResponse(prompt: string): string {
	const lowerPrompt = prompt.toLowerCase();
	
	if (lowerPrompt.includes('hello') || lowerPrompt.includes('hi') || lowerPrompt.includes('hey')) {
		return "Hello! I'm your AI tutor in demo mode. I'm here to help you learn! What would you like to explore today?";
	}
	
	if (lowerPrompt.includes('photosynthesis')) {
		return "Photosynthesis is the process by which plants convert light energy into chemical energy. Plants use sunlight, water, and carbon dioxide to produce glucose and oxygen. The formula is: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂. This process occurs in the chloroplasts, specifically in structures called thylakoids where chlorophyll captures light energy. Would you like to learn more about any specific aspect?";
	}
	
	if (lowerPrompt.includes('math') || lowerPrompt.includes('algebra') || lowerPrompt.includes('equation')) {
		return "Let me help you with that math problem! When solving equations, remember to maintain balance - whatever you do to one side, do to the other. Start by isolating the variable term, then solve for the variable. Would you like to work through a specific example together?";
	}
	
	if (lowerPrompt.includes('history') || lowerPrompt.includes('war') || lowerPrompt.includes('historical')) {
		return "History helps us understand how past events shape our present. When studying historical events, it's important to consider multiple perspectives, examine primary sources, and understand the context of the time period. What specific historical topic interests you?";
	}
	
	if (lowerPrompt.includes('science') || lowerPrompt.includes('experiment')) {
		return "Science is all about observation, hypothesis, and experimentation! The scientific method involves: 1) Making observations, 2) Forming a question, 3) Creating a hypothesis, 4) Conducting experiments, 5) Analyzing data, and 6) Drawing conclusions. This systematic approach helps us understand the natural world. What would you like to investigate?";
	}
	
	if (lowerPrompt.includes('write') || lowerPrompt.includes('essay') || lowerPrompt.includes('writing')) {
		return "Great writing starts with clear thinking! Here are some tips: 1) Start with a strong thesis statement, 2) Organize your ideas with an outline, 3) Support your points with evidence, 4) Use transitions to connect ideas, and 5) Revise and edit your work. Remember, writing is a process - don't expect perfection on the first draft. What are you working on writing?";
	}
	
	if (lowerPrompt.includes('help') || lowerPrompt.includes('explain')) {
		return "I'm here to help you understand! Learning is most effective when we break complex topics into smaller, manageable pieces. Could you tell me more specifically what you'd like help with? The more details you provide, the better I can tailor my explanation to your needs.";
	}
	
	if (lowerPrompt.includes('thank')) {
		return "You're very welcome! I'm glad I could help. Remember, learning is a journey, and every question you ask is a step forward. Feel free to ask me anything else you'd like to explore!";
	}
	
	return `That's an interesting question! In demo mode, I provide simulated responses to help you explore the interface. In the full version, I would give you a comprehensive, personalized answer based on your learning history and goals. I can help with subjects like math, science, history, literature, and more. What would you like to learn about?`;
}

export function generateMockAvatarResponse(prompt: string): {
	response: string;
	animation?: {
		facial_expression?: number;
		head_movement?: number;
		hand_gesture?: number;
		eye_movement?: number;
		body_posture?: number;
	};
	glbAnimation?: string;
	glbAnimationCategory?: string;
} {
	const response = generateMockResponse(prompt);
	const lowerPrompt = prompt.toLowerCase();
	
	let animation = {
		facial_expression: 1,
		head_movement: 1,
		hand_gesture: 1,
		eye_movement: 5,
		body_posture: 0
	};
	
	let glbAnimation = 'talking_neutral';
	let glbAnimationCategory = 'expression';
	
	if (lowerPrompt.includes('hello') || lowerPrompt.includes('hi')) {
		animation.facial_expression = 1;
		animation.hand_gesture = 3;
		glbAnimation = 'talking_happy';
	} else if (lowerPrompt.includes('thank')) {
		animation.facial_expression = 1;
		animation.head_movement = 1;
		glbAnimation = 'talking_happy';
	} else if (lowerPrompt.includes('help')) {
		animation.facial_expression = 3;
		animation.head_movement = 3;
		glbAnimation = 'talking_thoughtful';
	}
	
	return {
		response,
		animation,
		glbAnimation,
		glbAnimationCategory
	};
}

