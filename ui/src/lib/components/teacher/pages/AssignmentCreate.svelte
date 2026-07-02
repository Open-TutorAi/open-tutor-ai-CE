<!-- AssignmentCreate.svelte -->
<script lang="ts">
	import { getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { createAssignment } from '$lib/apis/assignments';

	const i18n = getContext('i18n');

	let title = '';
	let description = '';
	let rubric = '';
	let dueDate = '';
	let submitting = false;

	async function handleSubmit() {
		const token = localStorage.getItem('token');
		if (!token) {
			toast.error($i18n.t('Authentication required'));
			return;
		}
		if (!title.trim() || !rubric.trim()) {
			toast.error($i18n.t('Title and rubric are required'));
			return;
		}

		submitting = true;
		try {
			await createAssignment(token, {
				title: title.trim(),
				description: description.trim() || undefined,
				rubric: rubric.trim(),
				due_date: dueDate || undefined
			});
			toast.success($i18n.t('Assignment created'));
			goto('/teacher/assignments');
		} catch (err) {
			toast.error(typeof err === 'string' ? err : $i18n.t('Failed to create assignment'));
		} finally {
			submitting = false;
		}
	}
</script>

<div class="mb-6 max-w-2xl">
	<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1">
		{$i18n.t('Create Assignment')}
	</h2>
	<p class="text-gray-600 dark:text-gray-400 mb-6">
		{$i18n.t(
			'Define the task and a grading rubric — the rubric is what the AI grading assistant will use later.'
		)}
	</p>

	<form
		on:submit|preventDefault={handleSubmit}
		class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 space-y-5"
	>
		<div>
			<label for="title" class="block text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2"
				>{$i18n.t('Title')}</label
			>
			<input
				id="title"
				type="text"
				bind:value={title}
				placeholder={$i18n.t('e.g. Fractions Practice Set')}
				class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors duration-200"
			/>
		</div>

		<div>
			<label
				for="description"
				class="block text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2"
				>{$i18n.t('Description')}</label
			>
			<textarea
				id="description"
				bind:value={description}
				rows="3"
				placeholder={$i18n.t('What should students do for this assignment?')}
				class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white transition-colors duration-200"
			></textarea>
		</div>

		<div>
			<label for="rubric" class="flex items-center gap-2 mb-2">
				<span class="text-sm font-semibold text-gray-800 dark:text-gray-200"
					>{$i18n.t('Grading Rubric')}</span
				>
				<span
					class="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
					>{$i18n.t('Used by AI grading')}</span
				>
			</label>
			<textarea
				id="rubric"
				bind:value={rubric}
				rows="4"
				placeholder={$i18n.t(
					'Criteria the AI grading assistant will use, e.g. correctness, clear working, units included...'
				)}
				class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-white transition-colors duration-200"
			></textarea>
		</div>

		<div>
			<label
				for="due-date"
				class="block text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2"
				>{$i18n.t('Due Date')}</label
			>
			<input
				id="due-date"
				type="date"
				bind:value={dueDate}
				class="w-56 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors duration-200"
			/>
		</div>

		<div class="flex justify-end gap-3 pt-2">
			<button
				type="button"
				on:click={() => goto('/teacher/assignments')}
				class="px-4 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
			>
				{$i18n.t('Cancel')}
			</button>
			<button
				type="submit"
				disabled={submitting}
				class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
			>
				{$i18n.t('Create Assignment')}
			</button>
		</div>
	</form>
</div>
