<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { gradeSubmission, type SubmissionRow } from '$lib/apis/assignments';

	const dispatch = createEventDispatcher();
	const i18n: any = getContext('i18n');
	export let classId: string;
	export let assignmentId: string;
	export let row: SubmissionRow;
	const token = () => localStorage.getItem('token') ?? '';

	let grade: string = row.submission?.grade != null ? String(row.submission.grade) : '';
	let feedback: string = row.submission?.feedback ?? '';
	let busy = false;
	let message = '';

	function close() {
		dispatch('close');
	}

	async function save() {
		message = '';
		busy = true;
		try {
			const updated = await gradeSubmission(
				token(),
				classId,
				assignmentId,
				row.student_id,
				grade === '' ? null : Number(grade),
				feedback.trim()
			);
			dispatch('graded', updated);
		} catch (err: any) {
			message = typeof err === 'string' ? err : $i18n.t('Could not save the grade');
		} finally {
			busy = false;
		}
	}
</script>

<div
	class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
	on:click|self={close}
	role="presentation"
>
	<div class="w-full max-w-md rounded-2xl bg-white dark:bg-gray-800 shadow-xl p-6">
		<div class="flex items-center justify-between mb-1">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-white">
				{$i18n.t('Grade')} — {row.name ?? row.email ?? '—'}
			</h2>
			<button class="text-gray-400 hover:text-gray-600" on:click={close} aria-label="Close"
				>✕</button
			>
		</div>

		{#if row.submission?.content}
			<div
				class="mt-3 rounded-lg bg-gray-50 dark:bg-gray-700/40 p-3 text-sm text-gray-700 dark:text-gray-200 whitespace-pre-wrap max-h-48 overflow-y-auto"
			>
				{row.submission.content}
			</div>
		{:else}
			<p class="mt-3 text-sm text-gray-400">{$i18n.t('No submission content.')}</p>
		{/if}

		<div class="mt-4 flex flex-col gap-4">
			<div>
				<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1">{$i18n.t('Grade')}</label
				>
				<input
					type="number"
					min="0"
					max="100"
					class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300"
					bind:value={grade}
					placeholder="0 – 100"
				/>
			</div>
			<div>
				<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
					>{$i18n.t('Feedback')}</label
				>
				<textarea
					rows="3"
					class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300"
					bind:value={feedback}
					placeholder={$i18n.t('Optional feedback for the student')}
				></textarea>
			</div>
		</div>

		{#if message}<p class="text-sm mt-3 text-red-500">{message}</p>{/if}

		<div class="flex justify-end gap-2 mt-5">
			<button
				class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
				on:click={close}>{$i18n.t('Cancel')}</button
			>
			<button
				class="px-4 py-2 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm hover:opacity-90 disabled:opacity-50"
				on:click={save}
				disabled={busy}>{$i18n.t('Save grade')}</button
			>
		</div>
	</div>
</div>
