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
    let loading = true;
    let error: string | null = null;
    let expandedFeedbackId: string | null = null;

    function toggleFeedback(feedbackId: string) {
        expandedFeedbackId = expandedFeedbackId === feedbackId ? null : feedbackId;
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
                feedbacks = (response as FeedbackResponse[]).map(feedback => ({
                    id: feedback.id,
                    preferredResponseId: feedback.data.preferredResponseId,
                    reason: feedback.data.reason,
                    timestamp: feedback.data.timestamp,
                    questionId: feedback.data.questionId,
                    responses: feedback.data.responses
                }));
            }
        } catch (err) {
            console.error('Error loading feedbacks:', err);
            error = 'Failed to load feedbacks';
        } finally {
            loading = false;
        }
    });
</script>

<div class="flex flex-col gap-4">
    <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            {$i18n.t('Response Comparison Feedbacks')}
        </h1>
        <div class="text-sm text-gray-500 dark:text-gray-400">
            {$i18n.t('Total feedbacks')}: {feedbacks.length}
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
    {:else if feedbacks.length === 0}
        <div class="text-gray-500 dark:text-gray-400 text-center p-4">
            {$i18n.t('No feedbacks found')}
        </div>
    {:else}
        <div class="space-y-4">
            {#each feedbacks as feedback, index}
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
                                {$i18n.t('Feedback')} #{index + 1}
                            </h3>
                            <p class="text-sm text-gray-500 dark:text-gray-400">
                                {dayjs(feedback.timestamp).format('YYYY-MM-DD HH:mm:ss')}
                            </p>
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
                            <div class="grid grid-cols-2 gap-4">
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