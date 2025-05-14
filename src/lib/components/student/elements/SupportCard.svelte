<!-- src/lib/components/student/elements/SupportCard.svelte -->
<script lang="ts">
	import { goto } from '$app/navigation';
	
	export let support: any;
	export let i18n: any;

	// Format date for display
	function formatDate(dateString: string): string {
		if (!dateString) return '';
		try {
			const date = new Date(dateString);
			return new Intl.DateTimeFormat(navigator.language || 'en-US', {
				year: 'numeric',
				month: 'short',
				day: 'numeric'
			}).format(date);
		} catch (error) {
			console.error('Error formatting date:', error);
			return dateString;
		}
	}
</script>

<!-- svelte-ignore a11y-no-static-element-interactions -->
<!-- svelte-ignore a11y-no-noninteractive-tabindex -->
<div
	class="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow border border-gray-100 dark:border-gray-700 cursor-pointer"
	on:click={() => goto(`/student/support/${support.id}`)}
	on:keypress={(e) => e.key === 'Enter' && goto(`/student/support/${support.id}`)}
	tabindex="0"
>
	<div class="px-6 py-5">
		<div class="sm:flex sm:items-start sm:justify-between">
			<div class="mb-4 sm:mb-0">
				<div class="flex items-center mb-2">
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white mr-3">
						{support.title}
					</h3>
				</div>

				<p class="text-gray-600 dark:text-gray-400 text-sm line-clamp-2">
					{support.short_description || i18n.t('No description provided')}
				</p>
			</div>

			<div class="flex items-center sm:flex-col sm:items-end text-sm">
				<div
					class="flex items-center text-gray-500 dark:text-gray-400 mr-4 sm:mr-0 sm:mb-2"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-4 w-4 mr-1"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
						/>
					</svg>
					{formatDate(support.created_at)}
				</div>

				<div class="flex items-center text-blue-600 dark:text-blue-400 font-medium">
					<span>{i18n.t('View Details')}</span>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-4 w-4 ml-1"
						viewBox="0 0 20 20"
						fill="currentColor"
					>
						<path
							fill-rule="evenodd"
							d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
			</div>
		</div>

		<div
			class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 flex flex-wrap items-center gap-3"
		>
			{#if support.subject}
				<div
					class="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-3.5 w-3.5 mr-1"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
						/>
					</svg>
					{i18n.t(support.subject)}
				</div>
			{/if}

			{#if support.level}
				<div
					class="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-3.5 w-3.5 mr-1"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
						/>
					</svg>
					{i18n.t(support.level.charAt(0).toUpperCase() + support.level.slice(1))}
				</div>
			{/if}

			{#if support.learning_type}
				<div
					class="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-3.5 w-3.5 mr-1"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
						/>
					</svg>
					{i18n.t(support.learning_type)}
				</div>
			{/if}

			{#if support.chat_id}
				<div
					class="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-3.5 w-3.5 mr-1"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
						/>
					</svg>
					{i18n.t('Chat Available')}
				</div>
			{:else}
				<div
					class="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-3.5 w-3.5 mr-1"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
						/>
					</svg>
					{i18n.t('No Chat')}
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	/* For text truncation */
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style> 