<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';

	const i18n = getContext('i18n');

	$: username = $user?.name?.split(' ')[0] ?? 'Teacher';

	let loading = true;
	let error = null;

	onMount(async () => {
		try {
			if (!$user) {
				goto('/auth');
				return;
			}
			if ($user.role !== 'teacher') {
				await goto(`/${$user.role}`);
				return;
			}
			loading = false;
		} catch (err) {
			error = err.message || 'An error occurred';
			loading = false;
		}
	});
</script>

{#if loading}
	<div class="flex justify-center items-center min-h-screen">
		<div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
	</div>
{:else if error}
	<div class="flex justify-center items-center min-h-screen p-6">
		<p class="text-red-600">{error}</p>
	</div>
{:else}
<div class="space-y-6">

	<!-- Welcome -->
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
		<h1 class="text-2xl font-bold text-gray-800 dark:text-white mb-1">
			{$i18n.t('Hello')} {username} 👋
		</h1>
		<p class="text-sm text-gray-500 dark:text-gray-400">
			{$i18n.t("Here's an overview of your teaching activity.")}
		</p>
	</div>

	<!-- Quick actions -->
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

		<button
			on:click={() => goto('/teacher/classrooms')}
			class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 text-left hover:shadow-md transition group"
		>
			<div class="h-10 w-10 rounded-xl bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center mb-3 group-hover:bg-indigo-200 transition">
				<svg class="h-5 w-5 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
				</svg>
			</div>
			<p class="font-semibold text-gray-800 dark:text-white">{$i18n.t('My Classrooms')}</p>
			<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{$i18n.t('Manage your classes and students')}</p>
		</button>

		<button
			on:click={() => goto('/teacher/assignments')}
			class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 text-left hover:shadow-md transition group"
		>
			<div class="h-10 w-10 rounded-xl bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center mb-3 group-hover:bg-amber-200 transition">
				<svg class="h-5 w-5 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
				</svg>
			</div>
			<p class="font-semibold text-gray-800 dark:text-white">{$i18n.t('Assignments')}</p>
			<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{$i18n.t('Create and track assignments')}</p>
		</button>

		<button
			on:click={() => goto('/teacher/messages')}
			class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 text-left hover:shadow-md transition group"
		>
			<div class="h-10 w-10 rounded-xl bg-green-100 dark:bg-green-900/40 flex items-center justify-center mb-3 group-hover:bg-green-200 transition">
				<svg class="h-5 w-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
				</svg>
			</div>
			<p class="font-semibold text-gray-800 dark:text-white">{$i18n.t('Messages')}</p>
			<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{$i18n.t('Communicate with students and parents')}</p>
		</button>

	</div>

</div>
{/if}
