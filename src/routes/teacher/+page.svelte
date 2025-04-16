<script lang="ts">
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
  import { onMount, getContext } from 'svelte';
  import type { i18n as i18nType } from 'i18next';
  import type { Writable } from 'svelte/store';


	let loading = true;
	let error: string | null = null;
  const i18n = getContext<Writable<i18nType>>('i18n');


	onMount(async () => {
		try {
			loading = true;

			if (!$user) {
				console.log('No user found, redirecting to auth page');
				goto('/auth');
				return;
			}

			console.log('Current user role:', $user.role);

			// Allow access to teachers
			if ($user.role !== 'teacher') {
				console.log('User is not a teacher, redirecting to home');
				await goto(`/${$user.role}`);
				return;
			}

			// User has the correct role, continue loading the page
			loading = false;
		} catch (err) {
			console.error('Error in teacher page:', err);
			error = err instanceof Error ? err.message : 'An error occurred';
			loading = false;
		}
	});
</script>

{#if loading}
	<div class="flex justify-center items-center min-h-screen">
		<div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
	</div>
{:else if error}
	<div
		class="flex flex-col items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900 p-6"
	>
		<div class="w-full max-w-4xl bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
			<h1 class="text-3xl font-bold text-center mb-4 text-red-600">{$i18n.t('Error Loading Teacher Page')}</h1>
			<p class="text-gray-700 dark:text-gray-300 text-center mb-6">{error}</p>
			<div class="flex justify-center">
				<button
					class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
					on:click={() => goto('/auth')}
				>
					{$i18n.t('Return to Login')}
				</button>
			</div>
		</div>
	</div>
{:else}
	<div
		class="flex flex-col items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900 p-6"
	>
		<div class="w-full max-w-4xl bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
			<h1 class="text-3xl font-bold text-center mb-8 text-gray-800 dark:text-white">
				{$i18n.t('Teacher Page')}
			</h1>

			<div class="space-y-6">
				<div class="bg-green-50 dark:bg-green-900/20 p-6 rounded-lg">
					<h2 class="text-xl font-semibold mb-4 text-green-700 dark:text-green-300">
						{$i18n.t('Welcome to Your Teaching Dashboard')}
					</h2>
					<p class="text-gray-700 dark:text-gray-300">
						{$i18n.t('This is your personalized teaching space. Here you can manage your courses, create assignments, and monitor student progress.')}
					</p>
					{#if $user}
						<div class="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
							<h3 class="font-medium text-green-700 dark:text-green-300">{$i18n.t('Your Account Info:')}</h3>
							<p class="text-gray-700 dark:text-gray-300">{$i18n.t('Full Name')}: {$user.name}</p>
							<p class="text-gray-700 dark:text-gray-300">{$i18n.t('Email')}: {$user.email}</p>
							<p class="text-gray-700 dark:text-gray-300">{$i18n.t('Role')}: {$user.role}</p>

							<button
								class="text-xs text-center w-full mt-4 text-gray-400 underline"
								on:click={() => {
									localStorage.removeItem('token');
									location.href = '/auth';
								}}
							>
								{$i18n.t('Sign Out')}
							</button>
						</div>
					{/if}
				</div>

				<!-- Quick Links Section -->
				<div class="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-lg">
					<h2 class="text-xl font-semibold mb-4 text-blue-700 dark:text-blue-300">
						{$i18n.t('Quick Links')}
					</h2>
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<a
							href="/teacher/paired-responses"
							class="flex items-center p-4 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow"
						>
							<div class="flex-1">
								<h3 class="font-medium text-gray-800 dark:text-gray-200">
									{$i18n.t('Paired Responses')}
								</h3>
								<p class="text-sm text-gray-600 dark:text-gray-400">
									{$i18n.t('Review and compare student responses')}
								</p>
							</div>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-6 w-6 text-blue-500"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 5l7 7-7 7"
								/>
							</svg>
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}
