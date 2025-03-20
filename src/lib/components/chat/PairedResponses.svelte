<script lang="ts">
    import { onMount } from 'svelte';
    import { getAllChatsInDB } from '$lib/apis/chats';
    import dayjs from '$lib/dayjs';
    import type { i18n as i18nType } from 'i18next';
    import type { Writable } from 'svelte/store';
    import { getContext } from 'svelte';
    import { toast } from 'svelte-sonner';
    import { createResponseFeedback, getAllResponseFeedbacks } from '$lib/apis/response-feedbacks';

    const i18n = getContext<Writable<i18nType>>('i18n');

    const MAX_PREVIEW_LENGTH = 300;
    let expandedId: string | null = null;
    let selectedPair: PairedMessage | null = null;
    let selectedResponse: Message | null = null;
    let preferredResponseId: string | null = null;
    let comparisonReason = '';
    let currentQuestionId: string | null = null;
    let showComparisonModal = false;

    function toggleResponse(responseId: string) {
        expandedId = expandedId === responseId ? null : responseId;
    }

    function handleEvaluate(pair: PairedMessage) {
        selectedPair = pair;
        currentQuestionId = pair.question.id;
    }

    function handleResponseSelect(responseId: string) {
        preferredResponseId = responseId;
    }

    async function handleComparisonSubmit() {
        if (!preferredResponseId || !comparisonReason) {
            toast.error('Please select a preferred response and provide a reason');
            return;
        }

        if (!currentQuestionId) {
            toast.error('No question selected');
            return;
        }

        const token = localStorage.getItem('token');
        if (!token) {
            toast.error('Authentication required');
            return;
        }

        try {
            const feedback = {
                preferredResponseId,
                reason: comparisonReason,
                timestamp: Date.now(),
                questionId: currentQuestionId,
                question: selectedPair?.question.content || '',
                responses: selectedPair?.responses.map(r => ({
                    id: r.id,
                    content: r.content,
                    modelName: r.modelName
                })) || []
            };

            await createResponseFeedback(token, feedback);
            
            // Remove the submitted pair from the list
            if (selectedPair) {
                const questionId = selectedPair.question.id;
                pairedMessages = pairedMessages.filter(pair => 
                    pair.question.id !== questionId
                );
                console.log('Removed pair:', questionId);
                console.log('Remaining pairs:', pairedMessages.length);
            }
            
            toast.success('Feedback submitted successfully');
            showComparisonModal = false;
            selectedPair = null;
            preferredResponseId = null;
            comparisonReason = '';
        } catch (error) {
            console.error('Error submitting feedback:', error);
            toast.error('Failed to submit feedback');
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
        childrenIds: string[];
        timestamp: number;
        model?: string;
        modelName?: string;
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
    }

    let pairedMessages: PairedMessage[] = [];
    let loading = true;
    let error: string | null = null;

    function findPairedResponses(chat: Chat): PairedMessage[] {
        const pairs: PairedMessage[] = [];
        const messages = chat.chat?.history?.messages || {};

        // Convert messages object to array for easier iteration
        const messageArray = Object.values(messages);

        for (let i = 0; i < messageArray.length; i++) {
            const message = messageArray[i];
            if (message.role === 'user') {
                // Find responses that are children of this message
                const responses = messageArray.filter(
                    (m) => m.role === 'assistant' && message.childrenIds.includes(m.id)
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

    onMount(async () => {
        try {
            console.log('Fetching all chats...');
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('No authentication token found');
            }
            const chats = await getAllChatsInDB(token);
            console.log('Chats received:', chats);

            if (!Array.isArray(chats)) {
                throw new Error('Invalid response format: expected an array of chats');
            }

            const allPairs: PairedMessage[] = [];

            for (const chat of chats) {
                if (!chat || typeof chat !== 'object') {
                    console.warn('Invalid chat object:', chat);
                    continue;
                }

                if (chat.chat?.history?.messages) {
                    const pairs = findPairedResponses(chat);
                    allPairs.push(...pairs);
                }
            }

            console.log('Found pairs:', allPairs);

            // Get all evaluated feedbacks
            const feedbacks = await getAllResponseFeedbacks(token);
            const evaluatedQuestionIds = new Set(
                (feedbacks || []).map((feedback: any) => feedback.data.questionId)
            );

            // Filter out already evaluated pairs
            const unevaluatedPairs = allPairs.filter(pair => 
                !evaluatedQuestionIds.has(pair.question.id)
            );

            // Sort by timestamp, newest first
            pairedMessages = unevaluatedPairs.sort((a, b) => b.timestamp - a.timestamp);
        } catch (err) {
            console.error('Error loading paired responses:', err);
            error = err instanceof Error 
                ? `Failed to load paired responses: ${err.message}`
                : 'Failed to load paired responses';
        } finally {
            loading = false;
        }
    });
</script>

<div class="flex flex-col gap-4">
    {#if loading}
        <div class="flex justify-center items-center h-32">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-white"></div>
        </div>
    {:else if error}
        <div class="text-red-500 dark:text-red-400 p-4 rounded-lg bg-red-50 dark:bg-red-900/20">
            {error}
        </div>
    {:else if pairedMessages.length === 0}
        <div class="text-gray-500 dark:text-gray-400 text-center p-4">
            {$i18n.t('No paired responses found')}
        </div>
    {:else}
        <div class="space-y-6">
            {#each pairedMessages as pair}
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                    <div class="flex justify-between items-start mb-2">
                        <a href="/chat/{pair.chatId}" class="text-sm text-blue-600 dark:text-blue-400 hover:underline">
                            {pair.chatTitle || 'Untitled Chat'}
                        </a>
                        <button
                            on:click={() => handleEvaluate(pair)}
                            class="px-3 py-1 text-sm bg-emerald-600 hover:bg-emerald-700 dark:bg-[#4ADE80] dark:hover:bg-[#22C55E] text-white rounded-lg transition-colors"
                        >
                            {$i18n.t('Compare Responses')}
                        </button>
                    </div>
                    <div class="mb-4">
                        <h3 class="font-medium text-gray-900 dark:text-white mb-2">
                            {$i18n.t('Question')}:
                        </h3>
                        <p class="text-gray-700 dark:text-gray-300">{pair.question.content}</p>
                    </div>

                    <div class="space-y-4">
                        {#each pair.responses as response, index}
                            <div class="border-l-4 border-blue-500 pl-4">
                                <div class="flex items-center gap-2 mb-2">
                                    <span class="text-sm font-medium text-gray-500 dark:text-gray-400">
                                        {$i18n.t('Response')} {index + 1}
                                    </span>
                                    {#if response.modelName}
                                        <span class="text-xs text-gray-400 dark:text-gray-500">
                                            ({response.modelName})
                                        </span>
                                    {/if}
                                </div>
                                <div class="text-gray-700 dark:text-gray-300">
                                    <p class="whitespace-pre-wrap">
                                        {#if expandedId === response.id || response.content.length <= MAX_PREVIEW_LENGTH}
                                            {response.content}
                                        {:else}
                                            {response.content.slice(0, MAX_PREVIEW_LENGTH)}...
                                        {/if}
                                    </p>
                                    {#if response.content.length > MAX_PREVIEW_LENGTH}
                                        <button
                                            class="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                                            on:click={() => toggleResponse(response.id)}
                                        >
                                            {expandedId === response.id ? $i18n.t('Show less') : $i18n.t('Show more')}
                                        </button>
                                    {/if}
                                </div>
                            </div>
                        {/each}
                    </div>

                    <div class="mt-4 text-sm text-gray-500 dark:text-gray-400">
                        {dayjs(pair.timestamp).format('YYYY-MM-DD HH:mm:ss')}
                    </div>
                </div>
            {/each}
        </div>
    {/if}

    {#if selectedPair}
        <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div class="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                <div class="p-4">
                    <div class="flex justify-between items-start mb-4">
                        <h2 class="text-lg font-medium text-gray-900 dark:text-white">
                            {$i18n.t('Compare Responses')}
                        </h2>
                        <button
                            on:click={() => {
                                selectedPair = null;
                                preferredResponseId = null;
                                comparisonReason = '';
                            }}
                            class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    <div class="mb-4">
                        <h3 class="font-medium text-gray-900 dark:text-white mb-2">
                            {$i18n.t('Question')}:
                        </h3>
                        <p class="text-gray-700 dark:text-gray-300">{selectedPair.question.content}</p>
                    </div>

                    <div class="grid grid-cols-2 gap-4 mb-6">
                        {#each selectedPair.responses as response, index}
                            <div class="border rounded-lg p-4 {preferredResponseId === response.id ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20' : 'border-gray-200 dark:border-gray-700'}">
                                <div class="flex items-center justify-between mb-2">
                                    <span class="text-sm font-medium text-gray-500 dark:text-gray-400">
                                        {$i18n.t('Response')} {index + 1}
                                    </span>
                                    {#if response.modelName}
                                        <span class="text-xs text-gray-400 dark:text-gray-500">
                                            ({response.modelName})
                                        </span>
                                    {/if}
                                </div>
                                <p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap mb-4">
                                    {response.content}
                                </p>
                                <button
                                    on:click={() => handleResponseSelect(response.id)}
                                    class="w-full px-3 py-2 text-sm font-medium rounded-lg transition-colors
                                        {preferredResponseId === response.id
                                            ? 'bg-emerald-600 hover:bg-emerald-700 dark:bg-[#4ADE80] dark:hover:bg-[#22C55E] text-white'
                                            : 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300'}"
                                >
                                    {preferredResponseId === response.id ? $i18n.t('Selected') : $i18n.t('Select this response')}
                                </button>
                            </div>
                        {/each}
                    </div>

                    <div class="mb-6">
                        <label for="comparisonReason" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            {$i18n.t('Why do you prefer this response?')}
                        </label>
                        <textarea
                            id="comparisonReason"
                            bind:value={comparisonReason}
                            rows="4"
                            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            placeholder={$i18n.t('Please explain your preference...')}
                        ></textarea>
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
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .container {
        max-width: 1200px;
    }
</style>