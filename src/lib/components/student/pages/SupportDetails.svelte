<!-- student/support/[id]/+page.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getSupportById, deleteSupport } from '$lib/apis/supports';
	import type { Writable } from 'svelte/store';
	import { browser } from '$app/environment';
	import ConfirmDialog from '$lib/components/student/elements/ConfirmDialog.svelte';

	// Get i18n from context with proper typing
	interface I18n {
		t: (key: string) => string;
	}
	const i18n = getContext<Writable<I18n>>('i18n');

	// Support data
	let support: any = null;
	let loading = true;
	let error: string | null = null;

	// Confirmation dialog
	let showDeleteConfirm = false;

	// Extract support ID from URL
	$: supportId = $page.params.id;

	// Load support data
	onMount(async () => {
		if (!browser) return;

		try {
			const token = localStorage.getItem('token');
			if (!token) {
				error = $i18n.t('Authentication required');
				loading = false;
				return;
			}

			if (!supportId) {
				error = $i18n.t('Support ID is required');
				loading = false;
				return;
			}

			console.log(`Loading support with ID: ${supportId}`);
			support = await getSupportById(token, supportId);
			console.log('Support data loaded:', support);
		} catch (err: any) {
			console.error('Error loading support:', err);
			error = err?.message || $i18n.t('Failed to load support details');
		} finally {
			loading = false;
		}
	});

	// Format date for display
	function formatDate(dateString: string): string {
		if (!dateString) return $i18n.t('Not specified');
		try {
			const date = new Date(dateString);
			return new Intl.DateTimeFormat(navigator.language || 'en-US', {
				year: 'numeric',
				month: 'short',
				day: 'numeric',
				hour: '2-digit',
				minute: '2-digit'
			}).format(date);
		} catch (error) {
			console.error('Error formatting date:', error);
			return dateString;
		}
	}

	// Handle delete
	async function handleDelete() {
		if (!browser || !supportId) return;

		try {
			const token = localStorage.getItem('token');
			if (!token) {
				toast.error($i18n.t('Authentication required'));
				return;
			}

			const result = await deleteSupport(token, supportId);
			console.log('Delete result:', result);

			toast.success($i18n.t('Support deleted successfully'));

			// Redirect to support list
			goto('/student/supports');
		} catch (err: any) {
			console.error('Error deleting support:', err);
			toast.error(err?.message || $i18n.t('Failed to delete support'));
		}
	}

	// Handle starting a chat for this support
	function handleStartChat(event: MouseEvent) {
		if (!support || !support.id) return;
		
		// Save support data to localStorage for chat linking
		const supportData = {
			id: support.id,
			timestamp: Date.now(),
			attempts: 0
		};
		
		localStorage.setItem('pendingSupportData', JSON.stringify(supportData));
		console.log('Saved support ID to localStorage:', support.id);
		
		// Let the navigation happen normally - the href will take us to the chat page
	}
</script>

<div class="bg-gray-50 dark:bg-gray-900 min-h-screen px-4 py-8">
	<div class="max-w-4xl mx-auto">
		<!-- Header with back button -->
		<div class="mb-6">
			<button
				on:click={() => goto('/student/supports')}
				class="inline-flex items-center text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white mb-4"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5 mr-2"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
						clip-rule="evenodd"
					/>
				</svg>
				{$i18n.t('Back to Supports')}
			</button>

			<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
				{$i18n.t('Support Details')}
			</h1>
		</div>

		{#if loading}
			<!-- Loading skeleton -->
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 animate-pulse">
				<div class="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
				<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-6"></div>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
					<div>
						<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-2"></div>
						<div class="h-16 bg-gray-200 dark:bg-gray-700 rounded w-full mb-4"></div>
					</div>
					<div>
						<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-2"></div>
						<div class="h-16 bg-gray-200 dark:bg-gray-700 rounded w-full mb-4"></div>
					</div>
				</div>
			</div>
		{:else if error}
			<!-- Error state -->
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
				<div class="text-center py-8">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-12 w-12 text-red-500 mx-auto mb-4"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
					<h3 class="text-xl font-medium text-gray-900 dark:text-white mb-2">
						{$i18n.t('Error Loading Support')}
					</h3>
					<p class="text-gray-600 dark:text-gray-400">{error}</p>

					<button
						on:click={() => goto('/student/supports')}
						class="mt-6 inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
					>
						{$i18n.t('Return to Support List')}
					</button>
				</div>
			</div>
		{:else if support}
			<!-- Support detail card -->
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden mb-6">
				<!-- Title and actions header -->
				<div
					class="bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
				>
					<div>
						<h2 class="text-xl font-bold text-white">{support.title}</h2>
						<p class="text-blue-100 text-sm mt-1">
							{$i18n.t('ID')}: {support.id}
						</p>
					</div>

					<!-- Status badge and action buttons -->
					<div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">

						<!-- Support Status, Commented For now -->
						<!-- <span
							class={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
								support.status === 'pending'
									? 'bg-yellow-100 text-yellow-800'
									: support.status === 'active'
										? 'bg-green-100 text-green-800'
										: 'bg-gray-100 text-gray-800'
							}`}
						>
							{support.status.charAt(0).toUpperCase() + support.status.slice(1)}
						</span> -->

						<div class="flex items-center gap-2">
							<button
								on:click={() => goto(`/student/support/${support.id}/edit`)}
								class="inline-flex items-center px-3 py-1.5 bg-white text-gray-700 border border-gray-300 rounded hover:bg-gray-50 text-sm font-medium"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-4 w-4 mr-1"
									viewBox="0 0 20 20"
									fill="currentColor"
								>
									<path
										d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
									/>
								</svg>
								{$i18n.t('Edit')}
							</button>

							<button
								on:click={() => (showDeleteConfirm = true)}
								class="inline-flex items-center px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700 text-sm font-medium"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-4 w-4 mr-1"
									viewBox="0 0 20 20"
									fill="currentColor"
								>
									<path
										fill-rule="evenodd"
										d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
										clip-rule="evenodd"
									/>
								</svg>
								{$i18n.t('Delete')}
							</button>
						</div>
					</div>
				</div>

				<!-- Support content -->
				<div class="p-6">
					<!-- Basic information section -->
					<div class="mb-8">
						<h3
							class="text-lg font-semibold text-gray-800 dark:text-white mb-4 pb-2 border-b border-gray-200 dark:border-gray-700"
						>
							{$i18n.t('Basic Information')}
						</h3>

						<div class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
							<!-- Subject -->
							<div>
								<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
									{$i18n.t('Subject')}
								</h4>
								<p class="text-gray-800 dark:text-gray-200">
									{support.subject}
									{#if support.custom_subject}
										- {support.custom_subject}
									{/if}
								</p>
							</div>

							<!-- Course ID (if any) -->
							{#if support.course_id}
								<div>
									<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
										{$i18n.t('Course')}
									</h4>
									<p class="text-gray-800 dark:text-gray-200">{support.course_id}</p>
								</div>
							{/if}

							<!-- Learning Level -->
							{#if support.level}
								<div>
									<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
										{$i18n.t('Learning Level')}
									</h4>
									<div
										class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100"
									>
										{support.level.charAt(0).toUpperCase() + support.level.slice(1)}
									</div>
								</div>
							{/if}

							<!-- Learning Type -->
							{#if support.learning_type}
								<div>
									<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
										{$i18n.t('Learning Type')}
									</h4>
									<div
										class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-100"
									>
										{support.learning_type}
									</div>
								</div>
							{/if}

							<!-- Learning Language -->
							<div>
								<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
									{$i18n.t('Language')}
								</h4>
								<p class="text-gray-800 dark:text-gray-200">
									{support.content_language || 'English'}
								</p>
							</div>

							<!-- Duration -->
							{#if support.estimated_duration}
								<div>
									<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
										{$i18n.t('Estimated Duration')}
									</h4>
									<p class="text-gray-800 dark:text-gray-200">{support.estimated_duration}</p>
								</div>
							{/if}

							<!-- Access Type -->
							<div>
								<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
									{$i18n.t('Access Type')}
								</h4>
								<p class="text-gray-800 dark:text-gray-200">{support.access_type || 'Private'}</p>
							</div>

							<!-- Created/Updated dates -->
							<div class="col-span-1 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
								<div>
									<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
										{$i18n.t('Created')}
									</h4>
									<p class="text-gray-800 dark:text-gray-200">{formatDate(support.created_at)}</p>
								</div>
								{#if support.updated_at}
									<div>
										<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
											{$i18n.t('Last Updated')}
										</h4>
										<p class="text-gray-800 dark:text-gray-200">{formatDate(support.updated_at)}</p>
									</div>
								{/if}
							</div>
						</div>
					</div>

					<!-- Description and Learning Objectives -->
					<div class="mb-8">

						{#if support.short_description}
						<h3
							class="text-lg font-semibold text-gray-800 dark:text-white mb-4 pb-2 border-b border-gray-200 dark:border-gray-700"
						>
							{$i18n.t('Description & Objectives')}
						</h3>

						
							<div class="mb-6">
								<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
									{$i18n.t('Description')}
								</h4>
								<div
									class="bg-gray-50 dark:bg-gray-750 p-4 rounded-lg border border-gray-100 dark:border-gray-700"
								>
									<p class="text-gray-800 dark:text-gray-200">{support.short_description}</p>
								</div>
							</div>
						{/if}

						{#if support.learning_objective}
							<div>
								<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
									{$i18n.t('Learning Objectives')}
								</h4>
								<div
									class="bg-gray-50 dark:bg-gray-750 p-4 rounded-lg border border-gray-100 dark:border-gray-700"
								>
									<p class="text-gray-800 dark:text-gray-200">{support.learning_objective}</p>
								</div>
							</div>
						{/if}
					</div>

					<!-- Additional Information -->
					{#if (support.keywords && support.keywords.length > 0) || support.start_date || support.end_date}
						<div class="mb-8">
							<h3
								class="text-lg font-semibold text-gray-800 dark:text-white mb-4 pb-2 border-b border-gray-200 dark:border-gray-700"
							>
								{$i18n.t('Additional Information')}
							</h3>

							<div class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
								<!-- Keywords -->
								{#if support.keywords && support.keywords.length > 0}
									<div class="col-span-1 md:col-span-2">
										<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
											{$i18n.t('Keywords')}
										</h4>
										<div class="flex flex-wrap gap-2">
											{#each support.keywords as keyword}
												<span
													class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100"
												>
													{keyword}
												</span>
											{/each}
										</div>
									</div>
								{/if}

								<!-- Availability dates -->
								{#if support.start_date || support.end_date}
									<div class="col-span-1 md:col-span-2">
										<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
											{$i18n.t('Availability')}
										</h4>
										<div class="flex flex-wrap gap-4">
											{#if support.start_date}
												<div class="flex items-center">
													<svg
														xmlns="http://www.w3.org/2000/svg"
														class="h-5 w-5 text-gray-400 mr-2"
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
													<span class="text-gray-700 dark:text-gray-300">
														{$i18n.t('From')}: {formatDate(support.start_date)}
													</span>
												</div>
											{/if}

											{#if support.end_date}
												<div class="flex items-center">
													<svg
														xmlns="http://www.w3.org/2000/svg"
														class="h-5 w-5 text-gray-400 mr-2"
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
													<span class="text-gray-700 dark:text-gray-300">
														{$i18n.t('To')}: {formatDate(support.end_date)}
													</span>
												</div>
											{/if}
										</div>
									</div>
								{/if}
							</div>
						</div>
					{/if}

					<!-- Chat Section -->
					<div class="mb-8">
						<h3
							class="text-lg font-semibold text-gray-800 dark:text-white mb-4 pb-2 border-b border-gray-200 dark:border-gray-700"
						>
							{$i18n.t('Support Chat')}
						</h3>

						<div class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
							<!-- Chat ID -->
							{#if support.chat_id}
								<div>
									<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
										{$i18n.t('Associated Chat')}
									</h4>
									<div class="flex items-center">
										<span class="text-gray-700 dark:text-gray-300 mr-3 text-sm"
											>{support.chat_id}</span
										>
										<a
											href={`/student/c/${support.chat_id}`}
											class="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm bg-blue-100 dark:bg-blue-900 px-3 py-1 rounded-full"
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												class="h-4 w-4 mr-1"
												viewBox="0 0 20 20"
												fill="currentColor"
											>
												<path
													d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"
												/>
												<path
													d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"
												/>
											</svg>
											{$i18n.t('Continue Chat')}
										</a>
									</div>
								</div>
							{:else}
								<div>
									<h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
										{$i18n.t('No Associated Chat')}
									</h4>
									<div class="flex items-center">
										<a
											href="/student/chat"
											on:click={handleStartChat}
											class="inline-flex items-center text-white bg-green-600 hover:bg-green-700 px-3 py-1 rounded-full text-sm"
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												class="h-4 w-4 mr-1"
												viewBox="0 0 20 20"
												fill="currentColor"
											>
												<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clip-rule="evenodd" />
											</svg>
											{$i18n.t('Start a Chat')}
										</a>
									</div>
								</div>
							{/if}
						</div>
					</div>

					<!-- Actions footer -->
					<div
						class="flex justify-end space-x-4 border-t border-gray-200 dark:border-gray-700 pt-6 mt-6"
					>
						<button
							on:click={() => goto('/student/supports')}
							class="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
						>
							{$i18n.t('Back to List')}
						</button>

						<button
							on:click={() => goto(`/student/support/${support.id}/edit`)}
							class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
						>
							{$i18n.t('Edit Support')}
						</button>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<!-- Delete confirmation dialog -->
{#if showDeleteConfirm}
	<ConfirmDialog
		title={$i18n.t('Delete Support')}
		message={$i18n.t(
			'Are you sure you want to delete this support? This action cannot be undone.'
		)}
		confirmText={$i18n.t('Delete')}
		cancelText={$i18n.t('Cancel')}
		confirmButtonClass="bg-red-600 hover:bg-red-700"
		on:confirm={handleDelete}
		on:cancel={() => (showDeleteConfirm = false)}
	/>
{/if}
