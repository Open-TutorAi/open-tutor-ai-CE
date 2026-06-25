<script lang="ts">
	import { onMount, createEventDispatcher, getContext } from 'svelte';
	import { createAssignment, type AssignmentSummary } from '$lib/apis/assignments';
	import {
		getTemplates,
		createAssignmentFromTemplate,
		type AssignmentTemplate
	} from '$lib/apis/resources';
	import { uploadFile } from '$lib/apis/files';
	import { configureExam } from '$lib/apis/exams';

	const dispatch = createEventDispatcher();
	const i18n: any = getContext('i18n');
	export let classId: string;
	const token = () => localStorage.getItem('token') ?? '';

	let title = '';
	let instructions = '';
	let dueDate = '';
	let attachment: File | null = null;
	let busy = false;
	let message = '';

	// E10 exam mode — policy is fixed to auto-submit after a capped number of warnings.
	let isExam = false;
	let maxViolations = 3; // 1..3
	let timeLimit = 0; // minutes; 0 = no limit
	let requireFullscreen = true;

	function onPickFile(e: Event) {
		const input = e.target as HTMLInputElement;
		attachment = input.files && input.files.length ? input.files[0] : null;
	}

	let templates: AssignmentTemplate[] = [];
	let templateId = ''; // '' → build manually; otherwise use the server-side template

	$: usingTemplate = templateId !== '';
	$: valid = usingTemplate || !!title.trim();
	$: selectCls =
		'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300';

	// Preview the chosen template's content in the (disabled) fields.
	$: if (usingTemplate) {
		const t = templates.find((x) => x.id === templateId);
		if (t) {
			title = t.title;
			instructions = t.instructions ?? '';
		}
	}

	function close() {
		dispatch('close');
	}

	async function submit() {
		message = '';
		if (!valid) {
			message = $i18n.t('Title is required');
			return;
		}
		busy = true;
		// <input type="date"> gives YYYY-MM-DD; send an ISO datetime (end of day).
		const due = dueDate ? `${dueDate}T23:59:59` : undefined;
		try {
			let attachment_id: string | undefined;
			if (!usingTemplate && attachment) {
				const file = await uploadFile(token(), attachment);
				attachment_id = file.id;
			}
			const created: AssignmentSummary = usingTemplate
				? await createAssignmentFromTemplate(token(), classId, templateId, due)
				: await createAssignment(token(), classId, {
						title: title.trim(),
						instructions: instructions.trim() || undefined,
						attachment_id,
						due_date: due
					});
			// If marked as an exam, attach proctoring config to the new assignment.
			if (isExam && created?.id) {
				await configureExam(token(), classId, created.id, {
					on_violation: 'auto_submit',
					max_violations: Math.min(3, Math.max(1, maxViolations || 3)),
					time_limit_minutes: timeLimit > 0 ? timeLimit : undefined,
					require_fullscreen: requireFullscreen
				});
			}
			dispatch('created', created);
		} catch (err: any) {
			message = typeof err === 'string' ? err : $i18n.t('Could not create the assignment');
		} finally {
			busy = false;
		}
	}

	onMount(async () => {
		try {
			templates = await getTemplates(token());
		} catch (err) {
			/* templates are optional */
		}
	});
</script>

<div
	class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
	on:click|self={close}
	role="presentation"
>
	<div class="w-full max-w-lg rounded-2xl bg-white dark:bg-gray-800 shadow-xl p-6">
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-white">
				{$i18n.t('New assignment')}
			</h2>
			<button class="text-gray-400 hover:text-gray-600" on:click={close} aria-label="Close"
				>✕</button
			>
		</div>

		<div class="flex flex-col gap-4">
			{#if templates.length > 0}
				<div>
					<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
						>{$i18n.t('Start from a template')}</label
					>
					<select class={selectCls} bind:value={templateId}>
						<option value="" class="bg-white dark:bg-gray-800 text-gray-800 dark:text-white"
							>{$i18n.t('None — build manually')}</option
						>
						{#each templates as t (t.id)}
							<option value={t.id} class="bg-white dark:bg-gray-800 text-gray-800 dark:text-white"
								>{t.title}</option
							>
						{/each}
					</select>
				</div>
			{/if}
			<div>
				<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
					>{$i18n.t('Title')} *</label
				>
				<input
					class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:opacity-60"
					bind:value={title}
					disabled={usingTemplate}
					placeholder={$i18n.t('e.g. Fractions worksheet')}
				/>
			</div>
			<div>
				<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
					>{$i18n.t('Instructions')}</label
				>
				<textarea
					rows="4"
					class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:opacity-60"
					bind:value={instructions}
					disabled={usingTemplate}
					placeholder={$i18n.t('What should students do?')}
				></textarea>
			</div>
			<div>
				<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
					>{$i18n.t('Due date')}</label
				>
				<input
					type="date"
					class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300"
					bind:value={dueDate}
				/>
			</div>
			<div>
				<label class="block text-sm text-gray-600 dark:text-gray-300 mb-1"
					>{$i18n.t('Attachment (optional)')}</label
				>
				<input
					type="file"
					class="w-full text-sm text-gray-600 dark:text-gray-300 file:mr-3 file:rounded-full file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-60"
					on:change={onPickFile}
					disabled={usingTemplate}
				/>
				{#if usingTemplate}<p class="text-xs text-gray-400 mt-1">
						{$i18n.t('Templates carry their own attachment.')}
					</p>{/if}
			</div>
		</div>

		<!-- E10: proctored exam -->
		<div class="mt-4 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
			<label
				class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200 cursor-pointer"
			>
				<input type="checkbox" bind:checked={isExam} class="rounded" />
				🔒 {$i18n.t('Make this a proctored exam')}
			</label>
			{#if isExam}
				<p class="text-xs text-gray-400 mt-1">
					{$i18n.t(
						'Students take it full screen. Leaving the page or exiting full screen is recorded; the exam is submitted automatically after the warning limit.'
					)}
				</p>
				<div class="grid sm:grid-cols-2 gap-3 mt-3">
					<div>
						<label class="block text-xs text-gray-500 dark:text-gray-400 mb-1"
							>{$i18n.t('Warnings before auto-submit (max 3)')}</label
						>
						<input type="number" min="1" max="3" bind:value={maxViolations} class={selectCls} />
					</div>
					<div>
						<label class="block text-xs text-gray-500 dark:text-gray-400 mb-1"
							>{$i18n.t('Time limit (minutes, 0 = none)')}</label
						>
						<input type="number" min="0" bind:value={timeLimit} class={selectCls} />
					</div>
					<label
						class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200 sm:col-span-2"
					>
						<input type="checkbox" bind:checked={requireFullscreen} class="rounded" />
						{$i18n.t('Require full screen')}
					</label>
				</div>
			{/if}
		</div>

		{#if message}<p class="text-sm mt-3 text-red-500">{message}</p>{/if}

		<div class="flex justify-end gap-2 mt-5">
			<button
				class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
				on:click={close}>{$i18n.t('Cancel')}</button
			>
			<button
				class="px-4 py-2 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm hover:opacity-90 disabled:opacity-50"
				on:click={submit}
				disabled={busy || !valid}>{$i18n.t('Create')}</button
			>
		</div>
	</div>
</div>
