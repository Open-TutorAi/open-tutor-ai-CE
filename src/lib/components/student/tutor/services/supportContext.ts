import { v4 as uuidv4 } from 'uuid';
import { getSupportById } from '$lib/apis/supports';
import { TUTOR_API_BASE_URL } from '$lib/constants';

import type { SupportDetails, SupportFile, ChatHistory } from './types';

export async function generateSupportSystemPrompt(
	supportId: string,
	additionalPrompt?: string
): Promise<string | null> {
	try {
		console.log(`Fetching support details for ID: ${supportId}`);
		const token = localStorage.getItem('token');

		if (!token) {
			console.error('No token found, cannot fetch support details');
			return null;
		}

		// Fetch support details from API
		const supportDetails: SupportDetails = await getSupportById(token, supportId);
		if (!supportDetails) {
			console.error('Failed to fetch support details');
			return null;
		}

		let systemPrompt = buildBasePrompt();
		systemPrompt += buildSubjectContext(supportDetails);
		systemPrompt += buildLearningDirectives(supportDetails);
		systemPrompt += buildTopicDetails(supportDetails);
		systemPrompt += buildLevelGuidance(supportDetails);
		systemPrompt += buildLanguagePreference(supportDetails);
		systemPrompt += buildKeywords(supportDetails);
		systemPrompt += buildFileContext(supportDetails);
		systemPrompt += buildDurationGuidance(supportDetails);
		systemPrompt += buildGeneralInstruction(supportDetails);
		systemPrompt += buildFinalReminder(supportDetails);

		// Add any additional prompt data
		if (additionalPrompt) {
			systemPrompt += additionalPrompt;
		}

		console.log('Generated system prompt:', systemPrompt);
		return systemPrompt;
	} catch (error) {
		console.error('Error generating support system prompt:', error);
		return null;
	}
}

/**
 * Builds the base educational tutor prompt
 */
function buildBasePrompt(): string {
	return `You are a highly experienced educator, instructional designer, and tutor. You specialize in creating clear, engaging, and progressive step-by-step lessons for any topic and any academic level. You combine best practices in pedagogy (e.g., scaffolding, active recall, formative feedback) with adaptive teaching strategies. Your role is to guide me through a structured learning path, You guide the learner one concept at a time, combining effective teaching strategies, personalized communication style, and the most suitable reasoning method, in a way that is tailored to my needs, level, and learning goals.`;
}

/**
 * Builds subject context section
 */
function buildSubjectContext(supportDetails: SupportDetails): string {
	let prompt = `You are an educational tutor specializing in ${supportDetails.subject || 'various subjects'}`;

	if (supportDetails.custom_subject) {
		prompt += `, particularly in ${supportDetails.custom_subject}`;
	}

	prompt += `.\n\n`;
	return prompt;
}

/**
 * Builds learning directives section
 */
function buildLearningDirectives(supportDetails: SupportDetails): string {
	let prompt = `IMPORTANT INSTRUCTIONS: This is a learning session about ${supportDetails.title}. In your FIRST response, introduce yourself as a tutor for this specific topic and briefly mention what you'll be covering based on the learning objective. Even if the user's first message is generic (like "hello"), you should respond by acknowledging the course topic and learning goals described below.\n\n`;

	prompt += `CRITICAL INSTRUCTION: DO NOT ask the student about their educational level, background, prior knowledge, or learning objectives. This information has ALREADY been provided below and you must use it directly without asking the student to repeat it. Your first message should immediately begin teaching based on these details without asking any preliminary questions about the student's goals or background.\n\n`;

	prompt += `Begin your first message by saying: "I'm your tutor for ${supportDetails.title}. We'll be working on ${supportDetails.learning_objective || 'this topic'} today." Then immediately start providing relevant content. Do not ask what they want to learn or what their background is.\n\n`;

	return prompt;
}

/**
 * Builds topic details section
 */
function buildTopicDetails(supportDetails: SupportDetails): string {
	let prompt = `TOPIC: ${supportDetails.title}\n`;

	if (supportDetails.short_description) {
		prompt += `DESCRIPTION: ${supportDetails.short_description}\n`;
	}

	if (supportDetails.learning_objective) {
		prompt += `\nLEARNING OBJECTIVE: ${supportDetails.learning_objective}\n`;
	}

	if (supportDetails.learning_type) {
		prompt += `LEARNING TYPE: ${supportDetails.learning_type}\n`;

		// Add specific guidance based on learning type
		switch (supportDetails.learning_type) {
			case 'exam':
				prompt += `Focus on exam preparation, practice questions, and assessment strategies.\n`;
				break;
			case 'course':
				prompt += `Focus on comprehensive understanding of course material and concepts.\n`;
				break;
			case 'skill':
				prompt += `Focus on practical skill-building and application of knowledge.\n`;
				break;
		}
	}

	return prompt;
}

/**
 * Builds education level guidance section
 */
function buildLevelGuidance(supportDetails: SupportDetails): string {
	if (!supportDetails.level) return '';

	let prompt = `EDUCATION LEVEL: ${supportDetails.level}\n`;

	// Level-specific language guidance
	const levelGuidance: Record<string, string> = {
		primary: `Use simple language and explanations appropriate for young learners.\n`,
		middle: `Use moderately complex explanations with clear examples.\n`,
		high: `Use more detailed explanations and challenging concepts appropriate for high school students.\n`,
		university: `Use advanced concepts and academic language appropriate for university-level education.\n`
	};

	if (levelGuidance[supportDetails.level]) {
		prompt += levelGuidance[supportDetails.level];
	}

	prompt += `NOTE: The student is at the ${supportDetails.level} education level. Do not ask them about their level.\n`;

	return prompt;
}

/**
 * Builds language preference section
 */
function buildLanguagePreference(supportDetails: SupportDetails): string {
	if (!supportDetails.content_language) return '';

	return `PREFERRED LANGUAGE: ${supportDetails.content_language}\nPlease respond in ${supportDetails.content_language} unless the student asks otherwise.\n`;
}

/**
 * Builds keywords section
 */
function buildKeywords(supportDetails: SupportDetails): string {
	if (!supportDetails.keywords || supportDetails.keywords.length === 0) return '';

	return `\nKEY CONCEPTS: ${supportDetails.keywords.join(', ')}\n`;
}

/**
 * Builds file context section
 */
function buildFileContext(supportDetails: SupportDetails): string {
	if (!supportDetails.files || supportDetails.files.length === 0) return '';

	let prompt = `\nCOURSE MATERIALS: The student has uploaded ${supportDetails.files.length} file(s) as course materials:\n`;

	// List the files
	for (const file of supportDetails.files) {
		prompt += `- ${file.filename} (${file.file_type || 'unknown type'})\n`;
	}

	prompt += `\nWhen answering questions, you should reference and use the content from these materials whenever relevant. The content will be made available through the chat interface. If the student asks about content from these materials, prioritize information from them in your answers.\n`;

	// Note about text-based files
	try {
		for (const file of supportDetails.files) {
			if (
				file.file_type &&
				(file.file_type.includes('text') ||
					file.file_type.includes('pdf') ||
					file.file_type.includes('document'))
			) {
				prompt += `\nNote: Content from ${file.filename} will be made available for reference.\n`;
			}
		}
	} catch (fileError) {
		console.error('Error processing file content:', fileError);
	}

	return prompt;
}

/**
 * Builds duration guidance section
 */
function buildDurationGuidance(supportDetails: SupportDetails): string {
	if (!supportDetails.estimated_duration) return '';

	return `\nESTIMATED DURATION: This learning session is planned for ${supportDetails.estimated_duration}. Please pace your teaching accordingly.\n`;
}

/**
 * Builds general instruction section
 */
function buildGeneralInstruction(supportDetails: SupportDetails): string {
	return `\nYour goal is to help the student achieve their learning objective by providing clear explanations, examples, analogies, and guided practice appropriate for their level. Adjust your teaching style, complexity, and examples based on their interactions. Be engaging, supportive, and patient throughout the learning process.\n\n`;
}

/**
 * Builds final reminder section
 */
function buildFinalReminder(supportDetails: SupportDetails): string {
	return `FINAL REMINDER: DO NOT ask the student about information they've already provided such as their educational level, background, or learning goals. Instead, directly begin helping them with their learning objective. Always keep your responses relevant to the topic (${supportDetails.title}) and learning objectives described above. Your role is to provide structured guidance on this specific subject matter. If the student says only "hello" or provides a very brief message, jump straight into teaching the topic - don't waste time with preliminary questions.`;
}

/**
 * Processes pending support data and adds context to chat history
 */
export async function processPendingSupportData(
	history: ChatHistory
): Promise<{
	history: ChatHistory;
	chatFiles: any[];
	supportId: string | null;
}> {
	const chatFiles: any[] = [];
	let supportId: string | null = null;

	const pendingSupportData = localStorage.getItem('pendingSupportData');
	if (!pendingSupportData) {
		return { history, chatFiles, supportId };
	}

	try {
		const supportData = JSON.parse(pendingSupportData);
		if (!supportData?.id) {
			return { history, chatFiles, supportId };
		}

		supportId = supportData.id;
		console.log('Found pending support data:', supportData);

		// Generate system prompt from support data
		const systemPrompt = await generateSupportSystemPrompt(supportData.id);
		if (systemPrompt) {
			// Create a system message with the support context
			const systemMessageId = uuidv4();
			history.messages[systemMessageId] = {
				id: systemMessageId,
				parentId: null,
				childrenIds: [],
				role: 'system',
				content: systemPrompt,
				done: true,
				timestamp: Date.now()
			};

			console.log('Added system prompt to chat history');
		}

		// Fetch support details to get associated files
		try {
			const token = localStorage.getItem('token');
			if (token) {
				const supportDetails: SupportDetails = await getSupportById(token, supportData.id);

				// Process support files
				if (supportDetails?.files && supportDetails.files.length > 0) {
					console.log('Support has associated files:', supportDetails.files);

					// Add files to chat
					for (const file of supportDetails.files) {
						chatFiles.push({
							id: file.id,
							name: file.filename,
							type: file.file_type || 'application/octet-stream',
							size: file.file_size || 0,
							url: `${TUTOR_API_BASE_URL}/files/${file.id}`,
							from_support: true
						});
					}

					console.log('Added support files to chat:', chatFiles);
				}
			}
		} catch (fileError) {
			console.error('Error fetching support files:', fileError);
		}
	} catch (error) {
		console.error('Error processing pendingSupportData:', error);
	}

	return { history, chatFiles, supportId };
}

/**
 * Gets support title for chat naming
 */
export async function getSupportTitle(supportId: string): Promise<string | null> {
	try {
		const token = localStorage.getItem('token');
		if (!token) return null;

		const supportDetails: SupportDetails = await getSupportById(token, supportId);
		return supportDetails?.title || null;
	} catch (error) {
		console.error('Error getting support title:', error);
		return null;
	}
}

/**
 * Clears pending support data from localStorage
 */
export function clearPendingSupportData(): void {
	localStorage.removeItem('pendingSupportData');
	console.log('Cleared pending support data');
}

/**
 * Checks if there is pending support data
 */
export function hasPendingSupportData(): boolean {
	return localStorage.getItem('pendingSupportData') !== null;
}

/**
 * Gets the pending support ID if available
 */
export function getPendingSupportId(): string | null {
	try {
		const pendingData = localStorage.getItem('pendingSupportData');
		if (!pendingData) return null;

		const supportData = JSON.parse(pendingData);
		return supportData?.id || null;
	} catch {
		return null;
	}
}
