<!-- StudyGuide.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import ProgramCompletion from '../components/ProgramCompletion.svelte';
	import LearningPath from '../components/LearningPath.svelte';
	import EngagementGauge from '../components/EngagementGauge.svelte';
	import { fade, fly } from 'svelte/transition';
	import { quartOut } from 'svelte/easing';
	import MessageInput from '$lib/components/chat/MessageInput.svelte';
	import Messages from '$lib/components/chat/Messages.svelte';
	import AvatarChat from '$lib/components/chat/AvatarChat.svelte';
	import ModelSelector from '$lib/components/chat/ModelSelector.svelte';
	import { v4 as uuidv4 } from 'uuid';
	import { generateChatCompletion } from '$lib/apis/ollama';
	import { settings, models } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import { getModels } from '$lib/apis';

	const i18n = getContext<Writable<i18nType>>('i18n');

	interface Message {
		id: string;
		role: 'user' | 'assistant' | 'system';
		content: string;
		timestamp: number;
		parentId?: string;
		childrenIds?: string[];
		loading?: boolean;
	}

	interface ChatHistory {
		messages: Record<string, Message>;
		currentId: string | null;
	}

	interface OllamaResponse {
		model: string;
		created_at: string;
		message: {
			role: string;
			content: string;
		};
		done: boolean;
	}

	// Define an interface for the model
	interface Model {
		id: string;
		name: string;
		[key: string]: any;
	}

	// Sample current study topic
	const currentTopic = {
		title: 'Introduction to Hadoop',
		description: 'Hadoop is an open-source framework that allows for the distributed processing of large data sets across clusters of computers using simple programming models.',
		progress: 45
	};

	// Sample learning path/roadmap
	const learningPath = [
		{ id: 'intro', title: 'Introduction', completed: true },
		{ id: 'hdfs', title: 'HDFS', completed: true },
		{ id: 'mapreduce', title: 'MapReduce', completed: false, current: true },
		{ id: 'yarn', title: 'YARN', completed: false },
		{ id: 'hive', title: 'Hive & Pig', completed: false }
	];

	// Engagement metrics
	const engagement = {
		percentage: 75,
		sessions: 12,
		avgDuration: '25 min'
	};

	// Function to navigate to a specific topic
	function goToTopic(topicId: string) {
		console.log(`Navigating to topic: ${topicId}`);
		// Implementation would go here
	}
	
	// Chat state
	let history: ChatHistory = {
		messages: {},
		currentId: null
	};
	let selectedModels = [''];
	let atSelectedModel = undefined;
	let files = [];
	let prompt = '';
	let selectedToolIds = [];
	let imageGenerationEnabled = false;
	let webSearchEnabled = false;
	let codeInterpreterEnabled = false;
	let autoScroll = true;
	let processing = false;
	
	// Avatar state
	let avatarActive = true;
	let avatarSpeaking = false;
	let currentAvatarMessage = '';
	let processingRequest = false;  // New flag to track if a request is in progress
	
	// Avatar animation configuration
	const avatarType: string = "mentor"; // You can modify this or make it dynamic
	const gender: string = "female"; // "male" or "female" based on avatar
	const prefix: string = gender === "male" ? "M_" : "F_";
	
	const avatarPersonality = `You are The Mentor: encouraging, warm, supportive, and insightful. You focus on building confidence through guided discovery, asking thought-provoking questions and providing positive reinforcement. Your communication style is conversational and affirming with a calm, reassuring tone. You use relatable examples and analogies to help explain concepts.

IMPORTANT: Always keep responses very short (5-15 words). NEVER use emojis. You are a real human mentor, not an AI or a language model - you are a 3D avatar with The Mentor's personality and expertise. Always respond as if you are The Mentor in all interactions.`;

	const animationInstructions = `
IMPORTANT: Format ALL responses as valid JSON with these fields:
- "response": Your text answer to the user's question (REQUIRED, between 5-15 words only, NO emojis)
- "animation": Animation codes for basic expressions (OPTIONAL)
- "glbAnimation": Name or array of animation names from the library (OPTIONAL)
- "glbAnimationCategory": Category for the animation (OPTIONAL, defaults to "expression")

Your response MUST be a valid JSON object without any markdown formatting. The JSON object should be the entire response.

CRITICAL RULES:
- Keep responses between 5-15 words only
- NEVER use emojis or special characters
- Use short, direct sentences
- Avoid lengthy explanations

The animation fields should match exactly the content and emotion of your response. Always include animations to make your avatar more expressive and engaging.

Available animation options are:

1. SIMPLE ANIMATION CODES (use in "animation" object):
   - facial_expression: 
     0=neutral, 1=smile, 2=frown, 3=raised_eyebrows, 4=surprise, 5=wink, 6=sad, 7=angry
   - head_movement: 
     0=no_move, 1=nod_small, 2=shake, 3=tilt, 4=look_down, 5=look_up, 6=turn_left, 7=turn_right
   - hand_gesture: 
     0=no_move, 1=open_hand, 2=pointing, 3=wave, 4=open_palm, 5=thumbs_up, 6=fist, 7=peace_sign, 8=finger_snap
   - eye_movement: 
     0=no_move, 1=look_up, 2=look_down, 3=look_left, 4=look_right, 5=blink, 6=wide_open, 7=squint
   - body_posture: 
     0=neutral, 1=forward_lean, 2=lean_back, 3=shoulders_up, 4=rest_arms, 5=hands_on_hips, 6=sit, 7=stand

2. GLB ANIMATIONS (use in "glbAnimation" field with appropriate category):

   For female avatar, use these animations:
   - "talking_neutral", "talking_happy", "talking_excited", "talking_thoughtful", "talking_concerned"
   - "expression_smile", "expression_sad", "expression_surprise", "expression_thinking", "expression_angry"
   - "idle_normal", "idle_shift_weight", "idle_look_around", "idle_stretch", "idle_impatient"

Example JSON response:
{
  "response": "Hello! I'm here to help with any questions.",
  "animation": {
    "facial_expression": 1,
    "head_movement": 1,
    "hand_gesture": 3,
    "eye_movement": 5
  },
  "glbAnimation": "talking_happy",
  "glbAnimationCategory": "expression"
}

DO NOT wrap the JSON in code blocks, markdown, or any other formatting. The entire response must be a single valid JSON object.`;
	
	// Toggle avatar mode function
	const toggleAvatar = () => {
		avatarActive = !avatarActive;
	};
	
	// Track whether components have mounted for animation
	let mounted = false;
	
	let currentController: AbortController | null = null;
	
	// Function to handle direct API calls when server authentication fails
	const generateDirectCompletion = async (prompt: string, systemMessage: string = '') => {
		try {
			// Try to make a direct request to Ollama API
			// This is a fallback method when the server authentication fails
			const response = await fetch('http://localhost:11434/api/chat', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					model: 'mistral',
					messages: [
						...(systemMessage ? [{ role: 'system', content: systemMessage }] : []),
						{ role: 'user', content: prompt }
					],
					stream: false
				})
			});
			
			if (!response.ok) {
				throw new Error(`Failed to get response: ${response.status}`);
			}
			
			const data = await response.json();
			return data.message?.content || 'No response received';
		} catch (err) {
			console.error('Direct API call failed:', err);
			throw err;
		}
	};

	// Replace the existing loadModels function with this one
	const loadModels = async () => {
		try {
			// Try to load models directly from Ollama API first
			try {
				const response = await fetch('http://localhost:11434/api/tags');
				if (response.ok) {
					const data = await response.json();
					if (data.models && data.models.length > 0) {
						// Convert Ollama models to the format expected by the app
						const availableModels = data.models.map((model: any) => ({
							id: model.name,
							name: model.name,
							model: model.name,
							info: {
								meta: {
									description: `${model.name} (${model.size || 'unknown size'})`,
									capabilities: {
										chat: true
									}
								}
							}
						}));
						
						await models.set(availableModels);
						
						// Set default model
						if (selectedModels[0] === '') {
							// Prefer mistral if available
							const defaultModel = availableModels.find((m: Model) => 
								m.id.toLowerCase().includes('mistral')
							);
							
							if (defaultModel) {
								selectedModels = [defaultModel.id];
							} else if (availableModels.length > 0) {
								selectedModels = [availableModels[0].id];
							}
						}
						
						return; // Successfully loaded models directly
					}
				}
			} catch (directError) {
				console.warn('Could not connect directly to Ollama:', directError);
			}
			
			// If direct connection failed, fall back to API
			const availableModels = await getModels(localStorage.token);
			if (availableModels && availableModels.length > 0) {
				await models.set(availableModels);
				if (selectedModels[0] === '') {
					// Set default model if available
					const defaultModel = availableModels.find((m: Model) => m.id === 'mistral');
					if (defaultModel) {
						selectedModels = [defaultModel.id];
					} else if (availableModels.length > 0) {
						selectedModels = [availableModels[0].id];
					}
				}
			} else {
				// If no models are returned, use a fallback
				selectedModels = ['mistral'];
				toast.warning('No models available. Using fallback model.');
			}
		} catch (error) {
			console.error('Error loading models:', error);
			// Set a fallback model if API call fails
			selectedModels = ['mistral'];
			toast.error('Failed to load models. Using default fallback.');
		}
	};
	
	// Add a custom implementation of the scrollToBottom function
	const scrollToBottom = () => {
		// Use setTimeout to ensure DOM is fully rendered
		setTimeout(() => {
			const element = document.getElementById('messages-container');
			if (element) {
				element.scrollTop = element.scrollHeight;
			}
		}, 100);
	};

	// Add this method to the sendDirectMessage function after updating the messages
	const sendDirectMessage = async (messageContent: string, systemPrompt: string = '') => {
		if ((!prompt.trim() && !messageContent.trim()) || processing || processingRequest) return;
		
		processingRequest = true;  // Set the processing flag
		const messageId = uuidv4();
		const userMessageId = uuidv4();
		
		// Clear the current avatar message to prevent reading old messages
		currentAvatarMessage = '';
		avatarSpeaking = false;
		
		// Add user message
		history.messages[userMessageId] = {
			id: userMessageId,
			role: 'user',
			content: messageContent,
			timestamp: Date.now(),
			childrenIds: [messageId]
		};
		
		// Add assistant message placeholder
		history.messages[messageId] = {
			id: messageId,
			role: 'assistant',
			content: '',
			timestamp: Date.now(),
			parentId: userMessageId,
			loading: true
		};
		
		history.currentId = messageId;
		processing = true;
		
		// Scroll to bottom after updating messages
		scrollToBottom();
		
		try {
			// Use direct streaming if available
			try {
				const response = await fetch('http://localhost:11434/api/chat', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({
						model: selectedModels[0] || 'mistral',
						messages: [
							...(systemPrompt ? [{ role: 'system', content: systemPrompt }] : []),
							{ role: 'user', content: messageContent }
						],
						stream: false // Changed to false to get complete response at once for proper JSON parsing
					})
				});
				
				if (!response.ok) {
					throw new Error(`Failed to get response: ${response.status}`);
				}
				
				const data = await response.json();
				const content = data.message?.content || 'No response received';
				
				console.log("Received response from Ollama:", content);
				
				// Check if it's valid JSON
				try {
					const jsonTest = JSON.parse(content);
					console.log("Response is valid JSON:", jsonTest);
				} catch (e) {
					console.warn("Response is not valid JSON:", e);
				}
				
				// Process and update the message
				if (history.messages[messageId]) {
					history.messages[messageId].content = content;
					history.messages[messageId].loading = false;
				}
				
				// Scroll to show new content
				scrollToBottom();
				
				// If we're in avatar mode, set the message after the response is received
				if (avatarActive) {
					// First ensure the avatar isn't speaking
					avatarSpeaking = false;
					
					// Set the message after a small delay
					setTimeout(() => {
						currentAvatarMessage = content;
						console.log("Updated currentAvatarMessage:", currentAvatarMessage);
						
						// Then trigger speaking
						setTimeout(() => {
							avatarSpeaking = true;
							console.log("Avatar should now be speaking:", currentAvatarMessage);
						}, 100);
					}, 50);
				}
			} catch (streamError) {
				console.warn('Direct request failed:', streamError);
				toast.error('Failed to connect to Ollama. Is it running locally?');
				
				if (history.messages[messageId]) {
					delete history.messages[messageId];
				}
				if (history.messages[userMessageId]) {
					history.messages[userMessageId].childrenIds = [];
				}
			}
		} catch (error) {
			console.error('Direct message failed:', error);
			toast.error('Failed to connect to Ollama. Is it running locally?');
			
			if (history.messages[messageId]) {
				delete history.messages[messageId];
			}
			if (history.messages[userMessageId]) {
				history.messages[userMessageId].childrenIds = [];
			}
		} finally {
			processing = false;
			processingRequest = false;  // Reset the processing flag
		}
	};
	
	// Update submitPrompt to use direct messaging
	const submitPrompt = async () => {
		if (!prompt.trim() || processing) return;
		
		const currentPrompt = prompt;
		prompt = '';
		
		const systemMessage = avatarActive 
			? `${avatarPersonality}\n\n${animationInstructions}` 
			: 'You are a helpful AI tutor. Provide clear, accurate, and educational responses.';
		
		await sendDirectMessage(currentPrompt, systemMessage);
	};
	
	// Rest of the code can be removed as we're replacing them with the direct implementation
	const sendAvatarMessage = async () => {
		// This is no longer needed as we've consolidated the logic in sendDirectMessage
	};
	
	const sendChatMessage = async () => {
		// This is no longer needed as we've consolidated the logic in sendDirectMessage
	};
	
	// Update the other functions to use the direct API
	const continueResponse = async (messageId: string) => {
		const message = history.messages[messageId];
		if (!message) return;
		
		const systemMessage = avatarActive 
			? `${avatarPersonality}\n\n${animationInstructions}` 
			: 'You are a helpful AI tutor. Provide clear, accurate, and educational responses.';
		
		await sendDirectMessage("Please continue from where you left off.", systemMessage);
	};

	const regenerateResponse = async (messageId: string) => {
		const message = history.messages[messageId];
		if (!message || !message.parentId) return;
		
		const parentMessage = history.messages[message.parentId];
		if (!parentMessage) return;
		
		const systemMessage = avatarActive 
			? `${avatarPersonality}\n\n${animationInstructions}` 
			: 'You are a helpful AI tutor. Provide clear, accurate, and educational responses.';
		
		await sendDirectMessage(parentMessage.content, systemMessage);
	};

	const showMessage = () => {};
	const mergeResponses = () => {};
	
	const submitMessage = async (message: string) => {
		const systemMessage = avatarActive 
			? `${avatarPersonality}\n\n${animationInstructions}` 
			: 'You are a helpful AI tutor. Provide clear, accurate, and educational responses.';
			
		await sendDirectMessage(message, systemMessage);
	};
	
	const addMessages = (newMessages: Message[]) => {
		newMessages.forEach(message => {
			history.messages[message.id] = message;
		});
	};

	const chatActionHandler = () => {};
	const stopResponse = () => {
		processing = false;
		avatarSpeaking = false;
	};
	
	onMount(async () => {
		mounted = true;
		await loadModels();
		
		// Check browser support for speech synthesis
		if ('speechSynthesis' in window) {
			console.log("Speech synthesis is supported in this browser");
		} else {
			console.warn("Speech synthesis is NOT supported in this browser");
			toast.warning("Your browser doesn't support text-to-speech features");
		}
	});
</script>

<div class="flex flex-col lg:flex-row gap-0 lg:gap-4 w-full h-full {avatarActive ? 'avatar-active' : ''}">
	<!-- Main content area with chat -->
	{#if mounted}
		<div class="flex-1 w-full h-full min-h-[600px] mb-6 sm:mb-0" transition:fly={{ x: -20, duration: 500, delay: 100, easing: quartOut }}>
			<div class="bg-gradient-to-br from-gray-50 to-gray-200 dark:from-gray-800 dark:to-gray-900 p-2 sm:p-3 md:p-5 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 h-full flex flex-col border border-gray-200 dark:border-gray-700">
				<!-- Avatar/Chat Toggle Button -->
				<div class="flex flex-wrap justify-between items-center mb-3 gap-2">
					<div class="w-full sm:w-auto">
						<ModelSelector bind:selectedModels={selectedModels} />
					</div>
					<button
						id="avatar-toggle-button"
						class="relative h-10 w-48 mx-auto sm:mx-0 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 cursor-pointer overflow-hidden 
							   transition-all duration-300 shadow-sm hover:shadow-md border border-blue-100 dark:border-blue-800/50 px-1 py-[2px]"
						on:click={toggleAvatar}
					>
						<!-- Container for the toggle with a different approach -->
						<div class="relative flex items-center h-full">
							<!-- Sliding background pill -->
							<div 
								class="absolute h-[90%] w-[48%] bg-blue-500 dark:bg-blue-600 rounded-full shadow-sm
									   transition-transform duration-300 ease-in-out my-auto top-0 bottom-0"
								style="transform: translateX({avatarActive ? '2%' : '104%'});"
							></div>
							
							<!-- Left side label - Avatar with icon -->
							<div class="w-1/2 h-full flex items-center justify-center z-10 gap-1.5">
								<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4 flex-shrink-0" style="color: {avatarActive ? 'white' : 'currentColor'}">
									<path fill-rule="evenodd" d="M7.5 6a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM3.751 20.105a8.25 8.25 0 0116.498 0 .75.75 0 01-.437.695A18.683 18.683 0 0112 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 01-.437-.695z" clip-rule="evenodd" />
								</svg>
								<span class="font-medium text-sm whitespace-nowrap transition-colors duration-300"
									  style="color: {avatarActive ? 'white' : 'currentColor'}">
									Avatar
								</span>
							</div>
							
							<!-- Right side label - Discuss -->
							<div class="w-1/2 h-full flex items-center justify-center z-10 gap-1.5">
								<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4 flex-shrink-0" style="color: {avatarActive ? 'currentColor' : 'white'}">
									<path fill-rule="evenodd" d="M4.848 2.771A49.144 49.144 0 0112 2.25c2.43 0 4.817.178 7.152.52 1.978.292 3.348 2.024 3.348 3.97v6.02c0 1.946-1.37 3.678-3.348 3.97a48.901 48.901 0 01-3.476.383.39.39 0 00-.297.17l-2.755 4.133a.75.75 0 01-1.248 0l-2.755-4.133a.39.39 0 00-.297-.17 48.9 48.9 0 01-3.476-.384c-1.978-.29-3.348-2.024-3.348-3.97V6.741c0-1.946 1.37-3.68 3.348-3.97z" clip-rule="evenodd" />
								</svg>
								<span class="font-medium text-sm whitespace-nowrap transition-colors duration-300"
									  style="color: {avatarActive ? 'currentColor' : 'white'}">
									Discuss
								</span>
							</div>
						</div>
					</button>
				</div>
				
				<!-- Chat interface -->
				<div class="flex-1 flex flex-col relative bg-gradient-to-br from-gray-50 to-gray-200 dark:from-gray-800 dark:to-gray-900 rounded-xl overflow-hidden">
					{#if avatarActive}
						<!-- Reduce height of avatar container to leave space for input -->
						<div class="flex-1 flex-grow overflow-hidden bg-transparent relative rounded-xl fixed-container avatar-container">
							<AvatarChat
								className="h-full w-full"
								{history}
								currentMessage={currentAvatarMessage}
								speaking={avatarSpeaking}
								useClassroom={true}
								on:speechend={() => {
									avatarSpeaking = false;
									console.log("Avatar speech ended");
								}}
								on:speechstart={() => {
									console.log("Avatar speech started");
								}}
							/>
						</div>
						
						<!-- Move input outside the avatar container -->
						<div class="chat-input-container absolute bottom-0 left-0 right-0 z-50 px-1 sm:px-4 pb-2 sm:pb-4">
							<div class="max-w-3xl mx-auto">
								<div class="flex items-center w-full bg-gray-800/90 backdrop-blur-sm rounded-full shadow-md hover:shadow-lg py-2 px-4 transition-all duration-200">
									<input 
										type="text" 
										bind:value={prompt}
										placeholder="ask something"
										disabled={processingRequest}
										class="flex-1 bg-transparent border-none outline-none text-gray-300 placeholder-gray-500 py-1 px-2 text-sm sm:text-base"
									/>
									<div class="flex items-center gap-2 flex-shrink-0">
										<button class="text-gray-400 hover:text-gray-300 p-1 transition-colors duration-200">
											<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5">
												<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
											</svg>
										</button>
										{#if processingRequest}
											<div class="p-1">
												<div class="animate-spin h-5 w-5 border-2 border-blue-500 rounded-full border-t-transparent"></div>
											</div>
										{:else}
											<button 
												class="text-blue-500 hover:text-blue-400 p-1 transition-colors duration-200"
												on:click={submitPrompt}
												disabled={!prompt.trim() || processingRequest || !selectedModels[0]}
											>
												<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5">
													<path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
												</svg>
											</button>
										{/if}
									</div>
								</div>
							</div>
						</div>
					{:else}
						<!-- Text chat mode with integrated input -->
						<div class="flex flex-col h-full relative">
							<!-- Messages container with padding at bottom to make room for input -->
							<div class="flex-1 overflow-auto pb-16" id="messages-container">
								<Messages
									{history}
									{selectedModels}
									{prompt}
									chatId="study-guide"
									className="h-full flex"
									sendPrompt={submitPrompt}
									showMessage={showMessage}
									submitMessage={submitMessage}
									continueResponse={continueResponse}
									regenerateResponse={regenerateResponse}
									mergeResponses={mergeResponses}
									addMessages={addMessages}
									chatActionHandler={chatActionHandler}
									{autoScroll}
									bottomPadding={true}
								/>
							</div>
							
							<!-- Fixed positioned input at the bottom of chat area -->
							<div class="absolute bottom-0 left-0 right-0 px-1 sm:px-4 pb-2 sm:pb-4 bg-gradient-to-t from-gray-900 to-transparent pt-5">
								<div class="max-w-3xl mx-auto">
									<div class="flex items-center w-full bg-gray-800/90 backdrop-blur-sm rounded-full shadow-md hover:shadow-lg py-2 px-4 transition-all duration-200">
										<input 
											type="text" 
											bind:value={prompt}
											placeholder="ask something"
											disabled={processingRequest}
											class="flex-1 bg-transparent border-none outline-none text-gray-300 placeholder-gray-500 py-1 px-2 text-sm sm:text-base"
										/>
										<div class="flex items-center gap-2 flex-shrink-0">
											<button class="text-gray-400 hover:text-gray-300 p-1 transition-colors duration-200">
												<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5">
													<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
												</svg>
											</button>
											{#if processingRequest}
												<div class="p-1">
													<div class="animate-spin h-5 w-5 border-2 border-blue-500 rounded-full border-t-transparent"></div>
												</div>
											{:else}
												<button 
													class="text-blue-500 hover:text-blue-400 p-1 transition-colors duration-200"
													on:click={submitPrompt}
													disabled={!prompt.trim() || processingRequest || !selectedModels[0]}
												>
													<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5">
														<path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
													</svg>
												</button>
											{/if}
										</div>
									</div>
								</div>
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
	
	<!-- Right sidebar with widgets -->
	<div class="w-full lg:w-72 lg:max-w-72 flex-shrink-0 space-y-2 lg:space-y-4 overflow-y-auto pr-1 lg:pr-3 mt-1 lg:mt-0">
		{#if mounted}
			<!-- Program Completion Component -->
			<div transition:fly={{ x: 20, y: -10, duration: 400, delay: 200, easing: quartOut }} class="w-full">
				<ProgramCompletion progress={currentTopic.progress} />
			</div>
			
			<!-- Learning Path Component -->
			<div transition:fly={{ x: 20, duration: 400, delay: 300, easing: quartOut }} class="w-full learning-path-container">
				<LearningPath steps={learningPath} onStepClick={goToTopic} />
			</div>
			
			<!-- Engagement Gauge Component -->
			<div transition:fly={{ x: 20, y: 10, duration: 400, delay: 400, easing: quartOut }} class="w-full mb-2 lg:mb-4">
				<EngagementGauge 
					percentage={engagement.percentage}
					sessions={engagement.sessions}
					avgDuration={engagement.avgDuration}
				/>
			</div>
		{/if}
	</div>
</div>

<style>
	:global(.dark) {
		--tw-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.4), 0 1px 2px -1px rgb(0 0 0 / 0.4);
		--tw-shadow-colored: 0 1px 3px 0 var(--tw-shadow-color), 0 1px 2px -1px var(--tw-shadow-color);
	}
	
	.fixed-container {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 70px; /* Add space at the bottom for the input */
		overflow: hidden;
		min-height: 350px; /* Increased minimum height */
		max-height: 80vh; /* Increased maximum height */
	}
	
	/* Chat input container styling */
	.chat-input-container {
		position: absolute;
		bottom: 10px;
		left: 0;
		right: 0;
		z-index: 50;
	}
	
	/* Ensure avatar is visible on small screens but not too large */
	.avatar-container {
		display: block !important;
		height: 100%;
		min-height: 450px; /* Increased minimum height */
		max-height: 80vh; /* Increased maximum height */
	}
	
	/* Media queries for responsive avatar display */
	@media (max-width: 768px) {
		.avatar-container {
			min-height: 400px; /* Increased for larger mobile screens */
		}
		
		.fixed-container {
			bottom: 60px;
			min-height: 350px; /* Increased for larger mobile screens */
		}
	}
	
	@media (max-width: 640px) {
		.avatar-container {
			min-height: 350px; /* Increased for medium mobile screens */
		}
		
		.fixed-container {
			bottom: 55px;
			min-height: 300px; /* Increased for medium mobile screens */
		}
	}
	
	@media (max-width: 480px) {
		.avatar-container {
			min-height: 300px; /* Increased for small mobile screens */
		}
		
		.fixed-container {
			bottom: 55px;
			min-height: 250px; /* Increased for small mobile screens */
		}
		
		.chat-input-container {
			bottom: 5px;
		}
		
		/* Add more space to ensure the avatar container is fully visible */
		:global(.avatar-active) .flex-1 {
			min-height: 450px !important; /* Increased for better viewing on mobile */
			max-height: 500px !important;
		}
	}
	
	/* Adjustments for mobile layout */
	@media (max-width: 768px) {
		/* Ensure the right sidebar is properly displayed on small screens */
		.w-full.lg\:w-72 {
			margin-top: 0;
		}
	}
	
	/* Add responsive styles for input containers */
	@media (max-width: 480px) {
		input[type="text"] {
			min-width: 0;
			width: 100%;
			font-size: 14px;
			padding-left: 8px;
			height: 32px;
			margin-right: 4px;
		}
		
		/* Ensure the input container doesn't overflow on small screens */
		.flex.items-center.w-full {
			padding-left: 8px;
			padding-right: 8px;
		}
		
		.flex.items-center.gap-1 {
			gap: 2px;
		}
		
		/* Make buttons slightly smaller on mobile */
		button svg {
			width: 20px;
			height: 20px;
		}
	}
	
	/* Even more aggressive styling for extra small screens */
	@media (max-width: 360px) {
		input[type="text"] {
			font-size: 13px;
			padding-left: 6px;
			height: 28px;
		}
		
		.flex.items-center.w-full {
			padding-left: 6px;
			padding-right: 6px;
		}
		
		button svg {
			width: 18px;
			height: 18px;
		}
		
		.fixed-container {
			bottom: 50px;
			min-height: 150px;
		}
		
		.avatar-container {
			min-height: 170px;
		}
		
		:global(.avatar-active) .flex-1 {
			min-height: 250px !important;
		}
	}
</style> 