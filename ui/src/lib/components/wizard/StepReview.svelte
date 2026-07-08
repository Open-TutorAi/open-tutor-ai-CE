<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	export let formData: Record<string, string>;
	export let submitting = false;
	export let fieldErrors: { field: string; msg: string }[] = [];
	export let onSubmit: () => void = () => {};

	const ROWS: [string, string][] = [
		['Classroom Name', 'name'],
		['Short Description', 'description'],
		['Subject', 'subject'],
		['Course', 'course'],
		['Objectives', 'objectives'],
		['Level', 'level'],
		['Estimated Duration', 'duration'],
		['Language', 'language']
	];
</script>

<div data-testid="wizard-step-review" class="space-y-4">
	{#if fieldErrors.length > 0}
		<div
			data-testid="wizard-errors"
			class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-sm text-red-700 dark:text-red-300 space-y-1"
		>
			{#each fieldErrors as err}
				<div>{$i18n.t(err.field)}: {err.msg}</div>
			{/each}
		</div>
	{/if}

	<table class="w-full text-sm">
		<tbody>
			{#each ROWS as [label, key]}
				<tr class="border-b border-gray-100 dark:border-gray-700">
					<td class="py-2 pr-4 font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
						{$i18n.t(label)}
					</td>
					<td class="py-2 text-gray-900 dark:text-white">{formData[key] || '—'}</td>
				</tr>
			{/each}
		</tbody>
	</table>

	<button
		type="button"
		disabled={submitting}
		on:click={onSubmit}
		class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
	>
		{submitting ? $i18n.t('Creating...') : $i18n.t('Create Classroom')}
	</button>
</div>
