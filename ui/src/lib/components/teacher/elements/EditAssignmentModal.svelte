<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { updateAssignment, type AssignmentSummary, type Assignment } from '$lib/apis/assignments';
	import { uploadFile } from '$lib/apis/files';

	const i18n: any = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';
	const dispatch = createEventDispatcher();

	export let classId: string;
	export let assignment: Assignment; // the plain (non-exam) assignment being edited

	let title = assignment.title ?? '';
	let instructions = assignment.instructions ?? '';
	// `due_date` is an ISO datetime; <input type="date"> wants YYYY-MM-DD.
	let dueDate = assignment.due_date ? assignment.due_date.slice(0, 10) : '';
	let newFile: File | null = null;
	let removeAttachment = false;
	let busy = false;
	let error = '';

	// The current attachment stays unless the teacher replaces or removes it.
	$: hasExisting = !!assignment.attachment_id && !removeAttachment && !newFile;

	function onPickFile(e: Event) {
		const input = e.target as HTMLInputElement;
		newFile = input.files && input.files.length ? input.files[0] : null;
		if (newFile) removeAttachment = false;
	}

	function close() {
		dispatch('close');
	}

	async function save() {
		if (!title.trim()) {
			error = $i18n.t('Title is required');
			return;
		}
		busy = true;
		error = '';
		try {
			let attachment_id: string | undefined;
			if (newFile) {
				attachment_id = (await uploadFile(token(), newFile)).id;
			} else if (!removeAttachment && assignment.attachment_id) {
				attachment_id = assignment.attachment_id; // keep the current file
			}
			const due = dueDate ? `${dueDate}T23:59:59` : undefined;
			const updated: AssignmentSummary = await updateAssignment(token(), classId, assignment.id, {
				title: title.trim(),
				instructions: instructions.trim() || undefined,
				attachment_id,
				due_date: due
			});
			dispatch('updated', updated);
		} catch (err: any) {
			error = typeof err === 'string' ? err : $i18n.t('Could not save the assignment');
		} finally {
			busy = false;
		}
	}

	const inputCls =
		'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300';
</script>

<div
	class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
	on:click|self={close}
	role="presentation"
>
	<div class="w-full max-w-lg rounded-2xl bg-white dark:bg-gray-800 shadow-xl p-6">
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-white">
				{$i18n.t('Edit assignment')}
			</h2>
			<button class="text-gray-400 hover:text-gray-600" on:click={close} aria-label="Close"
				>✕</button
			>
		</div>

		<div class="flex flex-col gap-4">
			<div>
				<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
					>{$i18n.t('Title')} *</label
				>
				<input class={inputCls} bind:value={title} placeholder={$i18n.t('Assignment title')} />
			</div>
			<div>
				<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
					>{$i18n.t('Instructions')}</label
				>
				<textarea rows="4" class={inputCls} bind:value={instructions}></textarea>
			</div>
			<div>
				<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
					>{$i18n.t('Due date')}</label
				>
				<input type="date" class={inputCls} bind:value={dueDate} />
			</div>
			<div>
				<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
					>{$i18n.t('Attachment')}</label
				>
				{#if hasExisting}
					<div class="flex items-center gap-3 mb-2 text-sm">
						<span class="text-gray-600 dark:text-gray-300"
							>📎 {assignment.attachment_name ?? $i18n.t('Attachment')}</span
						>
						<button class="text-red-500 hover:underline" on:click={() => (removeAttachment = true)}
							>{$i18n.t('Remove')}</button
						>
					</div>
				{:else if removeAttachment}
					<p class="text-xs text-gray-400 mb-2">{$i18n.t('Attachment will be removed.')}</p>
				{/if}
				<input
					type="file"
					class="w-full text-sm text-gray-600 dark:text-gray-300 file:mr-3 file:rounded-full file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-blue-700 hover:file:bg-blue-100"
					on:change={onPickFile}
				/>
				<p class="text-xs text-gray-400 mt-1">
					{$i18n.t('Choosing a file replaces the current attachment.')}
				</p>
			</div>
		</div>

		{#if error}<p class="text-sm text-red-500 mt-3">{error}</p>{/if}

		<div class="flex justify-end gap-2 mt-6">
			<button
				class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
				on:click={close}>{$i18n.t('Cancel')}</button
			>
			<button
				class="px-5 py-2 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-semibold hover:opacity-90 disabled:opacity-50"
				on:click={save}
				disabled={busy}>{busy ? $i18n.t('Saving…') : $i18n.t('Save changes')}</button
			>
		</div>
	</div>
</div>
