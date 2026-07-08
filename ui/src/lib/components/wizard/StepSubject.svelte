<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	export let name = '';
	export let description = '';
	export let subject = '';

	const SUBJECTS = [
		'Mathematics',
		'Science',
		'History',
		'Computer Science',
		'English',
		'Geography',
		'Chemistry',
		'Biology',
		'Physics'
	];
</script>

<div data-testid="wizard-step-subject" class="space-y-4">
	<div
		class="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-lg p-4 text-sm text-blue-800 dark:text-blue-200"
	>
		{$i18n.t('A clear classroom name helps students identify your course easily.')}
	</div>

	<div>
		<label
			for="classroom-name"
			class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
		>
			{$i18n.t('Classroom Name')}
		</label>
		<input
			id="classroom-name"
			type="text"
			bind:value={name}
			placeholder={$i18n.t('e.g. Algebra I')}
			class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
		/>
	</div>

	<div>
		<label
			for="classroom-description"
			class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
		>
			{$i18n.t('Short Description')}
		</label>
		<textarea
			id="classroom-description"
			bind:value={description}
			rows="3"
			placeholder={$i18n.t('What is this classroom about?')}
			class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
		></textarea>
	</div>

	<div>
		<label
			for="classroom-subject"
			class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
		>
			{$i18n.t('Subject')}
		</label>
		<select
			id="classroom-subject"
			bind:value={subject}
			class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
		>
			<option value="">{$i18n.t('Select a subject')}</option>
			{#each SUBJECTS as s}
				<option value={s}>{$i18n.t(s)}</option>
			{/each}
		</select>
	</div>
</div>
