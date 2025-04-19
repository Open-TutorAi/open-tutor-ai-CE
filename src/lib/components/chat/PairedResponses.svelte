<script lang="ts">
	import { onMount } from 'svelte';
	import { getAllChatsInDB } from '$lib/apis/chats';
	import dayjs from '$lib/dayjs';
	import type { i18n as i18nType } from 'i18next';
	import type { Writable } from 'svelte/store';
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { createResponseFeedback, getAllResponseFeedbacks } from '$lib/apis/response-feedbacks';
	import { getAllFeedbacks, type Feedback } from '$lib/apis/feedbacks';
	import { user } from '$lib/stores';

	const i18n = getContext<Writable<i18nType>>('i18n');

	const MAX_PREVIEW_LENGTH = 300;
	let expandedId: string | null = null;
	let selectedPair: PairedMessage | null = null;
	let selectedResponse: Message | null = null;
	let preferredResponseId: string | null = null;
	let comparisonReason = '';
	let currentQuestionId: string | null = null;
	let showComparisonModal = false;
	let searchQuery = '';
	let filter: 'all' | 'todo' | 'done' = 'all';

	let uploadedFiles: File[] = [];
	let fileUploadError: string | null = null;	

	function handleFileUpload(event: Event) {
		const input = event.target as HTMLInputElement;
		if (!input.files || input.files.length === 0) return;
		
		fileUploadError = null;
		
		// Process each file
		Array.from(input.files).forEach(file => {
			// Check file size (max 50MB)
			if (file.size > 50 * 1024 * 1024) {
			fileUploadError = `${file.name} exceeds the maximum size of 50MB`;
			return;
			}
			
			// Check file type
			const validTypes = ['.pdf', '.docx', '.pptx', '.mp4', 'application/pdf', 
								'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
								'application/vnd.openxmlformats-officedocument.presentationml.presentation',
								'video/mp4'];
			
			const isValidType = validTypes.some(type => 
			file.type.includes(type) || file.name.toLowerCase().endsWith(type.toLowerCase())
			);
			
			if (!isValidType) {
			fileUploadError = `${file.name} is not a supported file type`;
			return;
			}
			
			// Add file to uploaded files
			uploadedFiles = [...uploadedFiles, file];
		});
		
		// Clear the input to allow selecting the same file again
		input.value = '';
		
		if (fileUploadError) {
			toast.error(fileUploadError);
		} else if (uploadedFiles.length > 0) {
			toast.success($i18n.t('Files uploaded successfully'));
		}
		}

		function removeFile(index: number) {
		uploadedFiles = uploadedFiles.filter((_, idx) => idx !== index);
		}

		function formatFileSize(bytes: number): string {
		if (bytes < 1024) return bytes + ' B';
		else if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
		else if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
		return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
		}

	function toggleResponse(responseId: string) {
		expandedId = expandedId === responseId ? null : responseId;
	}

	async function handleEvaluate(pair: PairedMessage) {
		try {
			const token = localStorage.getItem('token');
			if (!token) {
				toast.error($i18n.t('Authentication required'));
				return;
			}

			// Fetch latest feedbacks
			const [responseFeedbacksData, studentFeedbacks] = await Promise.all([
				getAllResponseFeedbacks(token),
				getAllFeedbacks(token)
			]);

			// Find and attach admin feedback
			const adminFeedback = responseFeedbacksData?.find(fb => fb.data?.questionId === pair.question.id);
			if (adminFeedback) {
				pair.adminFeedback = {
					preferredResponseId: adminFeedback.data.preferredResponseId,
					reason: adminFeedback.data.reason,
					timestamp: adminFeedback.data.timestamp
				};
			}

			// Attach student feedbacks
			if (studentFeedbacks && Array.isArray(studentFeedbacks)) {
				const feedbacksByMessageId = new Map();
				studentFeedbacks.forEach((feedback: Feedback) => {
					if (feedback.type === 'rating' && feedback.data?.rating) {
						const messageId = feedback.meta?.message_id;
						if (messageId) {
							if (!feedbacksByMessageId.has(messageId)) {
								feedbacksByMessageId.set(messageId, []);
							}
							feedbacksByMessageId.get(messageId)?.push({
								rating: feedback.data.rating,
								reason: feedback.data.reason || '',
								comment: feedback.data.comment || '',
								timestamp: feedback.created_at
							});
						}
					}
				});

				pair.responses.forEach(response => {
					response.studentFeedback = feedbacksByMessageId.get(response.id) || [];
				});
			}

			selectedPair = pair;
			currentQuestionId = pair.question.id;
		} catch (error) {
			console.error('Error loading feedbacks:', error);
			toast.error($i18n.t('Failed to load feedbacks'));
		}
	}

	function handleResponseSelect(responseId: string) {
		preferredResponseId = responseId;
	}

	async function handleComparisonSubmit() {
		if (!preferredResponseId || !comparisonReason) {
			toast.error($i18n.t('Please select a preferred response and provide a reason'));
			return;
		}

		if (!currentQuestionId) {
			toast.error($i18n.t('No question selected'));
			return;
		}

		const token = localStorage.getItem('token');
		if (!token) {
			toast.error($i18n.t('Authentication required'));
			return;
		}

		try {
			const feedback = {
				preferredResponseId,
				reason: comparisonReason,
				timestamp: Date.now(),
				questionId: currentQuestionId,
				question: selectedPair?.question.content || '',
				responses:
					selectedPair?.responses.map((r) => ({
						id: r.id,
						content: r.content,
						modelName: r.modelName
					})) || []
			};

			await createResponseFeedback(token, feedback);

			// Update evaluatedQuestionIds
			if (selectedPair) {
				evaluatedQuestionIds.add(selectedPair.question.id);
				evaluatedQuestionIds = evaluatedQuestionIds; // Trigger reactivity
				evaluatedPairs = evaluatedQuestionIds.size;
			}

			toast.success($i18n.t('Feedback submitted successfully'));
			showComparisonModal = false;
			selectedPair = null;
			preferredResponseId = null;
			comparisonReason = '';
		} catch (error) {
			console.error('Error submitting feedback:', error);
			toast.error($i18n.t('Failed to submit feedback'));
		}
	}

	function getTruncatedContent(content: string, responseId: string): string {
		if (isExpanded(responseId) || content.length <= MAX_PREVIEW_LENGTH) {
			return content;
		}
		return content.slice(0, MAX_PREVIEW_LENGTH) + '...';
	}

	function isExpanded(responseId: string): boolean {
		return expandedId === responseId;
	}

	interface Message {
		id: string;
		role: string;
		content: string;
		childrenIds?: string[];  // Made optional with ?
		timestamp: number;
		model?: string;
		modelName?: string;
		studentFeedback?: {
			rating: number;
			reason: string;
			comment: string;
			timestamp: number;
		}[];
	}

	interface Chat {
		id: string;
		title: string;
		chat: {
			history: {
				messages: Record<string, Message>;
				currentId: string;
			};
		};
	}

	interface PairedMessage {
		chatId: string;
		chatTitle: string;
		question: Message;
		responses: Message[];
		timestamp: number;
		studentFeedbacks?: {
			responseId: string;
			rating: number;
			reason: string;
			comment: string;
			timestamp: number;
		}[];
		adminFeedback?: {
			preferredResponseId: string;
			reason: string;
			timestamp: number;
		};
	}

	let pairedMessages: PairedMessage[] = [];
	let loading = true;
	let error: string | null = null;
	let totalPairs = 0;
	let evaluatedPairs = 0;
	let evaluatedQuestionIds = new Set<string>();
	let responseFeedbacks: any[] = [];

	function findPairedResponses(chat: Chat): PairedMessage[] {
		const pairs: PairedMessage[] = [];
		const messages = chat.chat?.history?.messages || {};

		// Convert messages object to array for easier iteration
		const messageArray = Object.values(messages);

		for (let i = 0; i < messageArray.length; i++) {
			const message = messageArray[i];
			if (message.role === 'user') {
				// Ensure childrenIds exists and is an array
				const childrenIds = message.childrenIds || [];
				
				// Find responses that are children of this message
				const responses = messageArray.filter(
					(m) => m.role === 'assistant' && childrenIds.includes(m.id)
				);

				// Only include if there are exactly two responses
				if (responses.length === 2) {
					pairs.push({
						chatId: chat.id,
						chatTitle: chat.title,
						question: message,
						responses,
						timestamp: message.timestamp
					});
				}
			}
		}

		return pairs;
	}

	$: filteredMessages = pairedMessages.filter((pair) => {
		const matchesSearch =
			!searchQuery ||
			pair.question.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
			pair.chatTitle.toLowerCase().includes(searchQuery.toLowerCase());

		const isEvaluatedPair = evaluatedQuestionIds.has(pair.question.id);
		const matchesFilter =
			filter === 'all' ||
			(filter === 'todo' && !isEvaluatedPair) ||
			(filter === 'done' && isEvaluatedPair);

		return matchesSearch && matchesFilter;
	});

	function isEvaluated(pair: PairedMessage): boolean {
		return evaluatedQuestionIds.has(pair.question.id);
	}

	onMount(async () => {
		try {
			console.log('Starting to fetch data...');
			const token = localStorage.getItem('token');
			if (!token) {
				throw new Error($i18n.t('No authentication token found'));
			}

			// Fetch chats
			console.log('Fetching chats...');
			const chats = await getAllChatsInDB(token);
			if (!chats || !Array.isArray(chats)) {
				throw new Error('Invalid chats data received');
			}
			console.log('Chats received:', chats);

			// Fetch feedbacks
			console.log('Fetching feedbacks...');
			const [responseFeedbacksData, studentFeedbacks] = await Promise.all([
				getAllResponseFeedbacks(token),
				getAllFeedbacks(token)
			]);
			responseFeedbacks = responseFeedbacksData || [];
			console.log('Response feedbacks:', responseFeedbacks);
			console.log('Student feedbacks:', studentFeedbacks);

			// Process student feedbacks
			const feedbacksByMessageId = new Map<
				string,
				Array<{
					rating: number;
					reason: string;
					comment: string;
					timestamp: number;
				}>
			>();

			if (studentFeedbacks && Array.isArray(studentFeedbacks)) {
				studentFeedbacks.forEach((feedback: Feedback) => {
					if (feedback.type === 'rating' && feedback.data?.rating) {
						const messageId = feedback.meta?.message_id;
						if (messageId) {
							if (!feedbacksByMessageId.has(messageId)) {
								feedbacksByMessageId.set(messageId, []);
							}
							feedbacksByMessageId.get(messageId)?.push({
								rating: feedback.data.rating,
								reason: feedback.data.reason || '',
								comment: feedback.data.comment || '',
								timestamp: feedback.created_at
							});
						}
					}
				});
			}

			// Process chats and find pairs
			const allPairs: PairedMessage[] = [];
			console.log('Processing chats to find pairs...');

			for (const chat of chats) {
				if (!chat || typeof chat !== 'object') {
					console.warn('Invalid chat object:', chat);
					continue;
				}

				if (chat.chat?.history?.messages) {
					const pairs = findPairedResponses(chat);
					if (pairs && pairs.length > 0) {
						console.log(`Found ${pairs.length} pairs in chat ${chat.id}`);
						// Attach student feedbacks to responses
						pairs.forEach((pair) => {
							pair.responses.forEach((response) => {
								response.studentFeedback = feedbacksByMessageId.get(response.id) || [];
							});
						});
						allPairs.push(...pairs);
					}
				}
			}

			console.log('Total pairs found:', allPairs.length);

			// Get evaluated question IDs
			evaluatedQuestionIds = new Set<string>();
			if (responseFeedbacks && Array.isArray(responseFeedbacks)) {
				responseFeedbacks.forEach((feedback: any) => {
					if (feedback.data?.questionId) {
						evaluatedQuestionIds.add(feedback.data.questionId);
					}
				});
			}
			console.log('Evaluated question IDs:', Array.from(evaluatedQuestionIds));

			// Update statistics
			totalPairs = allPairs.length;
			evaluatedPairs = evaluatedQuestionIds.size;

			// Store all pairs and let the reactive statement handle filtering
			pairedMessages = allPairs.sort((a, b) => b.timestamp - a.timestamp);

			console.log('Loaded all pairs:', pairedMessages.length);
			console.log('First pair sample:', pairedMessages[0]);

			// After processing all pairs, attach admin feedbacks
			allPairs.forEach(pair => {
				const adminFeedback = responseFeedbacks.find(fb => fb.data?.questionId === pair.question.id);
				if (adminFeedback) {
					pair.adminFeedback = {
						preferredResponseId: adminFeedback.data.preferredResponseId,
						reason: adminFeedback.data.reason,
						timestamp: adminFeedback.data.timestamp
					};
				}
			});

		} catch (err) {
			console.error('Error loading paired responses:', err);
			error =
				err instanceof Error
					? `Failed to load paired responses: ${err.message}`
					: 'Failed to load paired responses';
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex flex-col gap-6">
	{#if loading}
		<div class="flex justify-center items-center min-h-[200px]">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-white"></div>
		</div>
	{:else if error}
		<div class="text-red-500 dark:text-red-400 p-4 rounded-lg bg-red-50 dark:bg-red-900/20">
			{error}
		</div>
	{:else}
		<!-- Stats Cards -->
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 sm:p-6 mb-6">
			<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
				<div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 transform transition-transform hover:scale-[1.02]">
					<div class="flex items-center justify-between">
						<div>
							<div class="text-sm text-green-600 dark:text-green-400">{$i18n.t('Total')}</div>
							<div class="text-2xl font-bold text-green-700 dark:text-green-300">{totalPairs}</div>
						</div>
						<svg class="h-8 w-8 text-green-500 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
						</svg>
					</div>
				</div>
				<div class="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 transform transition-transform hover:scale-[1.02]">
					<div class="flex items-center justify-between">
						<div>
							<div class="text-sm text-orange-600 dark:text-orange-400">{$i18n.t('To Do')}</div>
							<div class="text-2xl font-bold text-orange-700 dark:text-orange-300">{totalPairs - evaluatedPairs}</div>
						</div>
						<svg class="h-8 w-8 text-orange-500 dark:text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
						</svg>
					</div>
				</div>
				<div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 transform transition-transform hover:scale-[1.02]">
					<div class="flex items-center justify-between">
						<div>
							<div class="text-sm text-blue-600 dark:text-blue-400">{$i18n.t('Done')}</div>
							<div class="text-2xl font-bold text-blue-700 dark:text-blue-300">{evaluatedPairs}</div>
						</div>
						<svg class="h-8 w-8 text-blue-500 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
					</div>
				</div>
			</div>
			<div class="mt-6">
				<div class="flex items-center justify-between mb-2">
					<div class="text-sm font-medium text-gray-600 dark:text-gray-400">{$i18n.t('Progress')}</div>
					<div class="text-sm font-medium text-gray-600 dark:text-gray-400">
						{Math.round((evaluatedPairs / totalPairs) * 100)}%
					</div>
				</div>
				<div class="bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
					<div
						class="bg-green-500 dark:bg-green-400 h-2.5 rounded-full transition-all duration-500"
						style="width: {Math.round((evaluatedPairs / totalPairs) * 100)}%"
					></div>
				</div>
			</div>
		</div>

		<!-- Search and Filters -->
		<div class="flex flex-col sm:flex-row gap-4 mb-6">
			<div class="flex-1 order-2 sm:order-1">
				<div class="relative">
					<input
						type="text"
						bind:value={searchQuery}
						placeholder={$i18n.t('Search questions or chat titles...')}
						class="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
					/>
					<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
						<svg
							class="h-5 w-5 text-gray-400"
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
				</div>
			</div>
			<div class="order-1 sm:order-2">
				<div class="inline-flex rounded-lg border border-gray-300 dark:border-gray-600 overflow-hidden bg-white dark:bg-gray-800 shadow-sm">
					<button
						class="px-4 py-2 text-sm font-medium transition-colors {filter === 'all'
							? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
							: 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}"
						on:click={() => (filter = 'all')}
					>
						{$i18n.t('All')}
					</button>
					<button
						class="px-4 py-2 text-sm font-medium border-l border-gray-300 dark:border-gray-600 transition-colors {filter === 'todo'
							? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
							: 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}"
						on:click={() => (filter = 'todo')}
					>
						{$i18n.t('To Do')}
					</button>
					<button
						class="px-4 py-2 text-sm font-medium border-l border-gray-300 dark:border-gray-600 transition-colors {filter === 'done'
							? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
							: 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}"
						on:click={() => (filter = 'done')}
					>
						{$i18n.t('Done')}
					</button>
				</div>
			</div>
		</div>

		<!-- Paired Messages List -->
		{#if filteredMessages.length === 0}
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center">
				<div class="text-gray-400 dark:text-gray-500 mb-4">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-16 w-16 mx-auto"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
						/>
					</svg>
				</div>
				<h3 class="text-xl font-medium text-gray-900 dark:text-white mb-2">No pairs found</h3>
				<p class="text-gray-600 dark:text-gray-400">
					{#if filter === 'todo'}
						{$i18n.t('All pairs have been evaluated. Great job!')}
					{:else if filter === 'done'}
						{$i18n.t('No evaluated pairs yet.')}
					{:else}
						{$i18n.t('No pairs match your search criteria.')}
					{/if}
				</p>
			</div>
		{:else}
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
				{#each filteredMessages as pair}
					<div
						class="bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-all cursor-pointer {!isEvaluated(pair) ? 'hover:bg-gray-50 dark:hover:bg-gray-700/50' : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'} border border-gray-200 dark:border-gray-700"
						on:click={() => handleEvaluate(pair)}
						on:keydown={(e) => e.key === 'Enter' && handleEvaluate(pair)}
						role="button"
						tabindex="0"
					>
						<div class="p-4">
							<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
								<div class="flex flex-wrap items-center gap-2 sm:gap-4">
									<div class="text-sm font-medium text-gray-500 dark:text-gray-400">
										#{pair.chatId.slice(0, 8)}
									</div>
									<div class="text-sm text-gray-400 dark:text-gray-500">
										{dayjs(pair.timestamp * 1000).format('YYYY-MM-DD')}
									</div>
									<div class="text-sm font-medium text-blue-600 dark:text-blue-400 truncate max-w-[200px]">
										{pair.chatTitle || 'Untitled Chat'}
									</div>
								</div>
								<div>
									{#if !isEvaluated(pair)}
										<span
											class="inline-flex items-center px-3 py-1 text-sm font-medium bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400 rounded-lg group-hover:bg-orange-200 dark:group-hover:bg-orange-900/40 transition-colors"
										>
											<svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
											</svg>
											{$i18n.t('To Do')}
										</span>
									{:else}
										<span
											class="inline-flex items-center px-3 py-1 text-sm font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400 rounded-lg"
										>
											<svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
											</svg>
											{$i18n.t('Done')}
										</span>
									{/if}
								</div>
							</div>
							<p class="text-gray-900 dark:text-white text-sm sm:text-base mb-4 line-clamp-2">
								{pair.question.content}
							</p>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/if}

	{#if selectedPair}
		<div class="fixed inset-0 bg-gray-900/20 backdrop-blur-sm flex items-center justify-center p-4 z-50">
			<div
				class="bg-white/95 dark:bg-gray-800/95 backdrop-blur-md rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-xl border border-gray-200/50 dark:border-gray-700/50"
			>
				<div class="p-6">
					<div class="flex justify-between items-start mb-6">
						<h2 class="text-xl font-bold text-gray-900 dark:text-white">
							{isEvaluated(selectedPair) ? $i18n.t('View Responses') : $i18n.t('Compare Responses')}
						</h2>
						<button
							on:click={() => {
								selectedPair = null;
								preferredResponseId = null;
								comparisonReason = '';
							}}
							class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-6 w-6"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M6 18L18 6M6 6l12 12"
								/>
							</svg>
						</button>
					</div>

					<div class="mb-6">
						<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
							{$i18n.t('Question')}:
						</h3>
						<p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
							{selectedPair.question.content}
						</p>
					</div>

					{#if selectedPair.adminFeedback}
						<div class="mb-6 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-4">
							<div class="flex items-center justify-between mb-2">
								<h3 class="text-lg font-medium text-emerald-700 dark:text-emerald-400">
									{$i18n.t('Teacher Feedback')}
								</h3>
								<span class="text-sm text-emerald-600 dark:text-emerald-300">
									{dayjs(selectedPair.adminFeedback.timestamp).format('YYYY-MM-DD HH:mm')}
								</span>
							</div>
							<div class="mb-2">
								<span class="text-sm font-medium text-emerald-600 dark:text-emerald-400">
									{$i18n.t('Preferred Response')}:
								</span>
								<span class="text-sm text-emerald-700 dark:text-emerald-300 ml-2">
									{selectedPair.responses.find(r => r.id === selectedPair.adminFeedback?.preferredResponseId)?.modelName || 'Response ' + (selectedPair.responses.findIndex(r => r.id === selectedPair.adminFeedback?.preferredResponseId) + 1)}
								</span>
							</div>
							<p class="text-emerald-700 dark:text-emerald-300 whitespace-pre-wrap">
								{selectedPair.adminFeedback.reason}
							</p>
						</div>
					{/if}

					<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
						{#each selectedPair.responses as response, index}
							<div
								class="border rounded-lg p-6 {preferredResponseId === response.id
									? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
									: 'border-gray-200 dark:border-gray-700'}"
							>
								<div class="flex items-center justify-between mb-4">
									<div class="flex items-center gap-2">
										<span class="text-lg font-medium text-gray-500 dark:text-gray-400">
											{$i18n.t('Response')}
											{index + 1}
										</span>
										{#if response.modelName}
											<span class="text-sm text-gray-400 dark:text-gray-500">
												({response.modelName})
											</span>
										{/if}
									</div>
									{#if preferredResponseId === response.id}
										<span class="text-emerald-600 dark:text-emerald-400">
											<svg
												xmlns="http://www.w3.org/2000/svg"
												class="h-6 w-6"
												fill="none"
												viewBox="0 0 24 24"
												stroke="currentColor"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M5 13l4 4L19 7"
												/>
											</svg>
										</span>
									{/if}
								</div>
								<p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap mb-6">
									{response.content}
								</p>

								{#if response.studentFeedback && response.studentFeedback.length > 0}
									<div class="border-t border-gray-200 dark:border-gray-700 pt-4 mb-6">
										<div class="flex items-center justify-between mb-4">
											<h4 class="text-lg font-medium text-gray-900 dark:text-white">
												{$i18n.t('Student Feedback')}
											</h4>
											<div class="flex items-center gap-2">
												<span class="text-sm text-gray-500">
													{$i18n.t('Average Rating')}:
												</span>
												<span class="text-lg font-medium">
													{(
														response.studentFeedback.reduce((acc, f) => acc + f.rating, 0) /
														response.studentFeedback.length
													).toFixed(1)}
												</span>
											</div>
										</div>
										<div class="space-y-3 max-h-48 overflow-y-auto">
											{#each response.studentFeedback as feedback}
												<div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
													<div class="flex items-center justify-between mb-2">
														<div class="flex items-center gap-2">
															<span class="font-medium">
																{$i18n.t('Rating')}: {feedback.rating}
															</span>
															<div class="flex">
																{#each Array(Math.max(0, Math.min(5, Math.floor(feedback.rating)))) as _, i}
																	<svg
																		class="h-4 w-4 text-yellow-400"
																		fill="currentColor"
																		viewBox="0 0 20 20"
																	>
																		<path
																			d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
																		/>
																	</svg>
																{/each}
															</div>
														</div>
														<span class="text-sm text-gray-500">
															{dayjs(feedback.timestamp * 1000).fromNow()}
														</span>
													</div>
													{#if feedback.reason}
														<p class="text-gray-600 dark:text-gray-300 text-sm mb-2">
															{feedback.reason}
														</p>
													{/if}
													{#if feedback.comment}
														<p class="text-gray-600 dark:text-gray-300 text-sm">
															{feedback.comment}
														</p>
													{/if}
												</div>
											{/each}
										</div>
									</div>
								{/if}

								{#if !isEvaluated(selectedPair)}
									<button
										on:click={() => handleResponseSelect(response.id)}
										class="w-full px-4 py-2 text-sm font-medium rounded-lg transition-colors
											{preferredResponseId === response.id
											? 'bg-emerald-600 hover:bg-emerald-700 dark:bg-[#4ADE80] dark:hover:bg-[#22C55E] text-white'
											: 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300'}"
									>
										{preferredResponseId === response.id
											? $i18n.t('Selected')
											: $i18n.t('Select this response')}
									</button>
								{/if}
							</div>
						{/each}
					</div>

					{#if !isEvaluated(selectedPair)}
						<div class="mb-6">
							<label
								for="comparisonReason"
								class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
							>
								{$i18n.t('Why do you prefer this response? (Pedagogical perspective)')}
							</label>
							<textarea
								id="comparisonReason"
								bind:value={comparisonReason}
								rows="4"
								class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
								placeholder={$i18n.t(
									'Please explain your preference from a pedagogical perspective...'
								)}
							></textarea>
							<div class="mb-6 mt-6">
								<div class="flex items-center mb-2">
								  <svg class="h-5 w-5 text-gray-600 dark:text-gray-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
								  </svg>
								  <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
									{$i18n.t('Attach teaching materials')}
								  </label>
								</div>
								
								<p class="text-sm text-gray-500 dark:text-gray-400 mb-3">
								  {$i18n.t('Upload lesson plans, presentations, worksheets, or instructional videos')}
								</p>
								
								<div 
								  class="border border-dashed border-blue-300 dark:border-blue-700 rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-colors"
								  on:click={() => document.getElementById('fileInput').click()}
								  on:keydown={(e) => e.key === 'Enter' && document.getElementById('fileInput').click()}
								  role="button"
								  tabindex="0"
								>
								  <input 
									type="file" 
									id="fileInput" 
									class="hidden" 
									accept=".pdf,.docx,.pptx,.mp4" 
									on:change={handleFileUpload} 
									multiple
								  />
								  
								  <div class="h-12 w-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-4">
									<svg class="h-6 w-6 text-blue-500 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
									</svg>
								  </div>
								  
								  <p class="text-blue-500 dark:text-blue-400 text-sm font-medium mb-1">
									{$i18n.t('Click to upload or drag and drop files')}
								  </p>
								  
								  <p class="text-xs text-gray-500 dark:text-gray-400">
									PDF, DOCX, PPTX, MP4 (max 50MB)
								  </p>
								</div>
							  
								{#if uploadedFiles && uploadedFiles.length > 0}
								  <div class="mt-4 space-y-2">
									{#each uploadedFiles as file, idx}
									  <div class="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
										<div class="flex items-center">
										  <div class="bg-blue-100 dark:bg-blue-900/20 rounded-md p-2 mr-3">
											{#if file.type.includes('pdf') || file.name.endsWith('.pdf')}
											  <svg class="h-5 w-5 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
											  </svg>
											{:else if file.type.includes('word') || file.name.endsWith('.docx')}
											  <svg class="h-5 w-5 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
											  </svg>
											{:else if file.type.includes('presentation') || file.name.endsWith('.pptx')}
											  <svg class="h-5 w-5 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
											  </svg>
											{:else if file.type.includes('video') || file.name.endsWith('.mp4')}
											  <svg class="h-5 w-5 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
											  </svg>
											{:else}
											  <svg class="h-5 w-5 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
											  </svg>
											{/if}
										  </div>
										  <div>
											<p class="text-sm font-medium text-gray-700 dark:text-gray-300 truncate max-w-[200px]">
											  {file.name}
											</p>
											<p class="text-xs text-gray-500 dark:text-gray-400">
											  {formatFileSize(file.size)}
											</p>
										  </div>
										</div>
										<button 
										  on:click|stopPropagation={() => removeFile(idx)}
										  class="text-gray-400 hover:text-red-500 transition-colors"
										>
										  <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
										  </svg>
										</button>
									  </div>
									{/each}
								  </div>
								{/if}
							  </div>
						</div>

						

						<div class="flex justify-end gap-4">
							<button
								on:click={() => {
									selectedPair = null;
									preferredResponseId = null;
									comparisonReason = '';
								}}
								class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
							>
								{$i18n.t('Cancel')}
							</button>
							<button
								on:click={handleComparisonSubmit}
								class="px-4 py-2 text-sm font-medium bg-emerald-600 hover:bg-emerald-700 dark:bg-[#4ADE80] dark:hover:bg-[#22C55E] text-white rounded-lg transition-colors"
							>
								{$i18n.t('Submit Feedback')}
							</button>
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	/* Add smooth transitions */
	.transition-all {
		transition-property: all;
		transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
		transition-duration: 150ms;
	}

	/* Improve focus styles for accessibility */
	button:focus-visible,
	[role="button"]:focus-visible {
		outline: 2px solid #60a5fa;
		outline-offset: 2px;
	}

	/* Add hover effects for interactive elements */
	@media (hover: hover) {
		.hover\:scale-\[1\.02\]:hover {
			transform: scale(1.02);
		}
	}

	/* Responsive padding adjustments */
	@media (max-width: 640px) {
		.p-4 {
			padding: 1rem;
		}
	}
</style>
