<!-- student/supports/+page.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getSupportRequests } from '$lib/apis/supports';
	import type { Writable } from 'svelte/store';
	import { browser } from '$app/environment';
	import SupportCard from '$lib/components/student/elements/SupportCard.svelte';

	// Get i18n from context with proper typing
	interface I18n {
		t: (key: string) => string;
	}
	const i18n = getContext<Writable<I18n>>('i18n');

	// Support data
	let supports: any[] = [];
	let loading = true;
	let error: string | null = null;

	// Load supports
	onMount(async () => {
		if (!browser) return;

		try {
			await loadSupports();
		} catch (err: any) {
			console.error('Error loading supports:', err);
			error = err?.message || $i18n.t('Failed to load supports');
		} finally {
			loading = false;
		}
	});

	// Load supports without status filter
	async function loadSupports() {
		const token = localStorage.getItem('token');
		if (!token) {
			error = $i18n.t('Authentication required');
			return;
		}

		loading = true;

		try {
			supports = await getSupportRequests(token);
			console.log('Loaded supports:', supports);
			error = null;
		} catch (err: any) {
			console.error('Error loading supports:', err);
			error = err?.message || $i18n.t('Failed to load supports');
			supports = [];
		} finally {
			loading = false;
		}
	}
</script>

<div class="bg-gray-50 dark:bg-gray-900 min-h-screen px-4 py-8">
	<div class="max-w-6xl mx-auto">
		<!-- Header with create button -->
		<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
			<div>
				<h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
					{$i18n.t('My Support')}
				</h1>
				<p class="text-gray-600 dark:text-gray-400 mb-4 sm:mb-0">
					{$i18n.t('Manage your learning supports')}
				</p>
			</div>

			<button
				on:click={() => goto('/student/support/create')}
				class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors shadow-sm"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5 mr-2"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
						clip-rule="evenodd"
					/>
				</svg>
				{$i18n.t('Create New Support')}
			</button>
		</div>

		<!-- Search or filter header - simplified with just the "All" option -->
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 mb-6 flex items-center justify-between">
			<div class="flex items-center">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5 text-gray-500 dark:text-gray-400"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
					/>
				</svg>
				<span class="ml-2 text-gray-700 dark:text-gray-300 font-medium">
					{$i18n.t('All Support')}
				</span>
			</div>
			
			<button
				on:click={loadSupports}
				class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm flex items-center"
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
						d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
					/>
				</svg>
				{$i18n.t('Refresh')}
			</button>
		</div>

		{#if loading}
			<!-- Loading skeleton -->
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
				<div class="animate-pulse space-y-4">
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
				</div>
			</div>
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
				<div class="animate-pulse space-y-4">
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
				</div>
			</div>
		{:else if error}
			<!-- Error state -->
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
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
						{$i18n.t('Error Loading Supports')}
					</h3>
					<p class="text-gray-600 dark:text-gray-400">{error}</p>

					<button
						on:click={loadSupports}
						class="mt-6 inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-5 w-5 mr-2"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
								clip-rule="evenodd"
							/>
						</svg>
						{$i18n.t('Try Again')}
					</button>
				</div>
			</div>
		{:else if supports.length === 0}
			<!-- Empty state -->
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center">
				<div
					class="w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mx-auto mb-4"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-8 w-8 text-blue-500"
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
				<h3 class="text-xl font-medium text-gray-900 dark:text-white mb-2">
					{$i18n.t('No Supports Found')}
				</h3>
				<p class="text-gray-600 dark:text-gray-400 mb-6">
					{$i18n.t("You haven't created any supports yet")}
				</p>

				<button
					on:click={() => goto('/student/support/create')}
					class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-5 w-5 mr-2"
						viewBox="0 0 20 20"
						fill="currentColor"
					>
						<path
							fill-rule="evenodd"
							d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
							clip-rule="evenodd"
						/>
					</svg>
					{$i18n.t('Create Your First Support')}
				</button>
			</div>
		{:else}
			<!-- Support list -->
			<div class="space-y-4">
				{#each supports as support (support.id)}
					<SupportCard {support} i18n={$i18n} />
				{/each}
			</div>
		{/if}
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