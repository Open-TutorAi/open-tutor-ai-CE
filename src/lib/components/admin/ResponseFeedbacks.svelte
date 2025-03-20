<script lang="ts">
    import { onMount } from 'svelte';
    import dayjs from '$lib/dayjs';
    import type { i18n as i18nType } from 'i18next';
    import type { Writable } from 'svelte/store';
    import { getContext } from 'svelte';
    import { toast } from 'svelte-sonner';
    import { getAllResponseFeedbacks } from '$lib/apis/response-feedbacks';
    import type { FeedbackResponse, FeedbackDisplay } from '$lib/types/response-feedbacks';

    const i18n = getContext<Writable<i18nType>>('i18n');

    let feedbacks: FeedbackDisplay[] = [];
    let filteredFeedbacks: FeedbackDisplay[] = [];
    let loading = true;
    let error: string | null = null;
    let expandedFeedbackId: string | null = null;
    
    // Date filtering
    let startDate: string = '';
    let endDate: string = '';
    
    // Selected feedbacks for export
    let selectedFeedbacks: Set<string> = new Set();
    let selectAll: boolean = false;

    function toggleFeedback(feedbackId: string) {
        expandedFeedbackId = expandedFeedbackId === feedbackId ? null : feedbackId;
    }
    
    function toggleFeedbackSelection(feedbackId: string) {
        if (selectedFeedbacks.has(feedbackId)) {
            selectedFeedbacks.delete(feedbackId);
        } else {
            selectedFeedbacks.add(feedbackId);
        }
        // Force reactivity by creating a new Set
        selectedFeedbacks = new Set(selectedFeedbacks);
        updateSelectAllStatus();
    }
    
    function toggleSelectAll() {
        selectAll = !selectAll;
        
        if (selectAll) {
            // Select all visible feedbacks
            filteredFeedbacks.forEach(feedback => {
                selectedFeedbacks.add(feedback.questionId);
            });
        } else {
            // Deselect all feedbacks
            selectedFeedbacks.clear();
        }
        
        // Force reactivity by creating a new Set
        selectedFeedbacks = new Set(selectedFeedbacks);
    }
    
    function updateSelectAllStatus() {
        selectAll = filteredFeedbacks.length > 0 && 
            filteredFeedbacks.every(feedback => selectedFeedbacks.has(feedback.questionId));
    }
    
    function applyDateFilter() {
        if (!startDate && !endDate) {
            filteredFeedbacks = [...feedbacks];
            return;
        }
        
        const start = startDate ? dayjs(startDate).startOf('day') : dayjs(0);
        const end = endDate ? dayjs(endDate).endOf('day') : dayjs();
        
        filteredFeedbacks = feedbacks.filter(feedback => {
            const feedbackDate = dayjs(feedback.timestamp);
            return feedbackDate.isAfter(start) && feedbackDate.isBefore(end);
        });
        
        // Update selection status after filtering
        selectedFeedbacks = new Set(
            [...selectedFeedbacks].filter(id => 
                filteredFeedbacks.some(feedback => feedback.questionId === id)
            )
        );
        updateSelectAllStatus();
    }
    
    function resetFilters() {
        startDate = '';
        endDate = '';
        filteredFeedbacks = [...feedbacks];
        selectedFeedbacks.clear();
        selectAll = false;
    }

    onMount(async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                error = 'Authentication required';
                return;
            }

            const response = await getAllResponseFeedbacks(token);
            if (response) {
                console.log('API Response:', response);
                feedbacks = (response as FeedbackResponse[]).map(feedback => {
                    console.log('Processing feedback:', feedback);
                    return {
                        id: feedback.id,
                        preferredResponseId: feedback.data.preferredResponseId,
                        reason: feedback.data.reason,
                        timestamp: feedback.data.timestamp,
                        questionId: feedback.data.questionId,
                        question: feedback.data.question,
                        responses: feedback.data.responses,
                        userId: feedback.user_id
                    };
                });
                filteredFeedbacks = [...feedbacks];
            }
        } catch (err) {
            console.error('Error loading feedbacks:', err);
            error = 'Failed to load feedbacks';
        } finally {
            loading = false;
        }
    });

    const exportRLHFData = () => {
        try {
            // Only export selected feedbacks
            const rlhfData = filteredFeedbacks
                .filter(feedback => selectedFeedbacks.has(feedback.questionId))
                .map((feedback) => {
                    const responses = feedback.responses.map((response) => ({
                        text: response.content,
                        model: response.modelName || 'unknown',
                        id: response.id
                    }));

                    const chosenResponse = responses.find((r) => r.id === feedback.preferredResponseId);
                    const rejectedResponse = responses.find((r) => r.id !== feedback.preferredResponseId);

                    return {
                        prompt: {
                            Id: feedback.questionId,
                            text: feedback.question || feedback.questionId
                        },
                        responses,
                        chosen: chosenResponse?.id,
                        rejected: rejectedResponse?.id,
                        reason: feedback.reason,
                        metadata: {
                            timestamp: new Date(feedback.timestamp).getTime()
                        }
                    };
                });

            const blob = new Blob([JSON.stringify(rlhfData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `rlhf_data_${dayjs().format('YYYY-MM-DD_HH-mm')}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            const count = rlhfData.length;
            toast.success(`${count} ${count === 1 ? $i18n.t('feedback') : $i18n.t('feedbacks')} ${$i18n.t('exported successfully')}`);
        } catch (e) {
            toast.error($i18n.t('Failed to export data'));
        }
    };
</script>

<div class="flex flex-col gap-4">
    <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            {$i18n.t('Response Comparison Feedbacks')}
        </h1>
        <div class="text-sm text-gray-500 dark:text-gray-400">
            {$i18n.t('Selected')}: {selectedFeedbacks.size} / {filteredFeedbacks.length}
        </div>
        <button
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed"
            on:click={exportRLHFData}
            disabled={selectedFeedbacks.size === 0}
        >
            {$i18n.t('Export Selected')}
        </button>
    </div>

    <!-- Date filter controls -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
            {$i18n.t('Filter by Date')}
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {$i18n.t('Start Date')}
                </label>
                <input 
                    type="date" 
                    bind:value={startDate}
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm dark:bg-gray-700 dark:text-white"
                />
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {$i18n.t('End Date')}
                </label>
                <input 
                    type="date" 
                    bind:value={endDate}
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm dark:bg-gray-700 dark:text-white"
                />
            </div>
            <div class="flex items-end gap-2">
                <button
                    class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    on:click={applyDateFilter}
                >
                    {$i18n.t('Apply Filter')}
                </button>
                <button
                    class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                    on:click={resetFilters}
                >
                    {$i18n.t('Reset')}
                </button>
            </div>
        </div>
    </div>

    {#if loading}
        <div class="flex justify-center items-center h-32">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-white"></div>
        </div>
    {:else if error}
        <div class="text-red-500 dark:text-red-400 p-4 rounded-lg bg-red-50 dark:bg-red-900/20">
            {error}
        </div>
    {:else if filteredFeedbacks.length === 0}
        <div class="text-gray-500 dark:text-gray-400 text-center p-4">
            {$i18n.t('No feedbacks found')}
        </div>
    {:else}
        <!-- Select all control -->
        <div class="flex items-center mb-2 pl-2">
            <input 
                type="checkbox" 
                id="select-all"
                checked={selectAll}
                on:change={toggleSelectAll}
                class="h-4 w-4 text-blue-600 dark:text-blue-500 rounded"
            />
            <label for="select-all" class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                {$i18n.t('Select All')} ({filteredFeedbacks.length})
            </label>
        </div>
        
        <div class="space-y-4">
            {#each filteredFeedbacks as feedback, index}
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                    <div class="flex justify-between items-start mb-4">
                        <div class="flex items-center">
                            <input 
                                type="checkbox"
                                id={`feedback-${feedback.questionId}`}
                                checked={selectedFeedbacks.has(feedback.questionId)}
                                on:change={() => toggleFeedbackSelection(feedback.questionId)}
                                class="h-4 w-4 text-blue-600 dark:text-blue-500 rounded mr-3"
                            />
                            <div>
                                <h3 class="text-base text-black-500 dark:text-gray-400">
                                    {$i18n.t('Feedback')} # {feedback.questionId}
                                </h3>
                                <p class="text-sm text-gray-500 dark:text-gray-400">
                                    {dayjs(feedback.timestamp).format('YYYY-MM-DD HH:mm:ss')}
                                </p>
                            </div>
                        </div>
                        <button
                            on:click={() => toggleFeedback(feedback.questionId)}
                            class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                        >
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                class="h-6 w-6 transform transition-transform {expandedFeedbackId === feedback.questionId ? 'rotate-180' : ''}"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                            </svg>
                        </button>
                    </div>

                    {#if expandedFeedbackId === feedback.questionId}
                        <div class="space-y-4">
                            <div>
                                <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
                                    {$i18n.t('Question')}:
                                </h4>
                                <p class="text-gray-700 dark:text-gray-300">
                                    {feedback.question || feedback.questionId}
                                </p>
                            </div>

                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {#each feedback.responses as response}
                                    <div class="border rounded-lg p-4 {response.id === feedback.preferredResponseId ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20' : 'border-gray-200 dark:border-gray-700'}">
                                        <div class="flex items-center justify-between mb-2">
                                            <span class="text-sm font-medium text-gray-500 dark:text-gray-400">
                                                {$i18n.t('Response')}
                                            </span>
                                            {#if response.modelName}
                                                <span class="text-xs text-gray-400 dark:text-gray-500">
                                                    ({response.modelName})
                                                </span>
                                            {/if}
                                        </div>
                                        <p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                                            {response.content}
                                        </p>
                                        {#if response.id === feedback.preferredResponseId}
                                            <div class="mt-2 text-sm text-emerald-600 dark:text-emerald-400">
                                                {$i18n.t('Preferred Response')}
                                            </div>
                                        {/if}
                                    </div>
                                {/each}
                            </div>

                            <div>
                                <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
                                    {$i18n.t('Reason for preference')}:
                                </h4>
                                <p class="text-gray-700 dark:text-gray-300">
                                    {feedback.reason}
                                </p>
                            </div>
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}
</div>