<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import {
		getLibrary,
		downloadMaterial,
		deleteTemplate,
		type ClassMaterial,
		type AssignmentTemplate
	} from '$lib/apis/resources';
	import { fmtDate, fmtSize } from '$lib/utils/format';
	import TemplateModal from '$lib/components/teacher/elements/TemplateModal.svelte';

	const i18n: any = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';

	let materials: ClassMaterial[] = [];
	let templates: AssignmentTemplate[] = [];
	let loading = true;
	let tab: 'materials' | 'templates' = 'materials';
	let showTemplate = false;

	async function load() {
		loading = true;
		try {
			const lib = await getLibrary(token());
			materials = lib.materials;
			templates = lib.templates;
		} catch (err) {
			/* leave empty */
		} finally {
			loading = false;
		}
	}

	async function download(m: ClassMaterial) {
		try {
			const blob = await downloadMaterial(token(), m.classroom_id, m.id);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = m.filename ?? m.title;
			a.click();
			URL.revokeObjectURL(url);
		} catch (err) {
			/* ignore */
		}
	}

	async function removeTemplate(t: AssignmentTemplate) {
		try {
			await deleteTemplate(token(), t.id);
			templates = templates.filter((x) => x.id !== t.id);
		} catch (err) {
			/* keep */
		}
	}
	function onTemplateSaved(e: CustomEvent<AssignmentTemplate>) {
		templates = [e.detail, ...templates];
		showTemplate = false;
	}

	onMount(load);
</script>

<div class="flex flex-col gap-6">
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold text-gray-800 dark:text-white">{$i18n.t('Resources')}</h1>
			<p class="text-gray-500 dark:text-gray-400 mt-1">
				{$i18n.t('Class materials and reusable assignment templates.')}
			</p>
		</div>
		{#if tab === 'templates'}
			<button
				class="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-90 text-white rounded-full transition shadow-sm"
				on:click={() => (showTemplate = true)}>+ {$i18n.t('New template')}</button
			>
		{/if}
	</div>

	<div class="flex gap-6 border-b border-gray-200 dark:border-gray-700">
		<button
			class="pb-2 -mb-px border-b-2 text-sm {tab === 'materials'
				? 'border-blue-500 text-blue-600 dark:text-blue-400 font-semibold'
				: 'border-transparent text-gray-500'}"
			on:click={() => (tab = 'materials')}>{$i18n.t('Materials')} ({materials.length})</button
		>
		<button
			class="pb-2 -mb-px border-b-2 text-sm {tab === 'templates'
				? 'border-blue-500 text-blue-600 dark:text-blue-400 font-semibold'
				: 'border-transparent text-gray-500'}"
			on:click={() => (tab = 'templates')}>{$i18n.t('Templates')} ({templates.length})</button
		>
	</div>

	{#if loading}
		<div class="flex justify-center py-12">
			<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
		</div>
	{:else if tab === 'materials'}
		{#if materials.length === 0}
			<div
				class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
			>
				{$i18n.t('No materials yet — upload one from a class (Resources tab).')}
			</div>
		{:else}
			<div class="overflow-x-auto rounded-2xl bg-white dark:bg-gray-800 shadow-sm">
				<table class="w-full text-left text-sm">
					<thead
						class="text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700"
					>
						<tr>
							<th class="px-5 py-3 font-medium">{$i18n.t('Name')}</th>
							<th class="px-5 py-3 font-medium">{$i18n.t('Class')}</th>
							<th class="px-5 py-3 font-medium">{$i18n.t('Type')}</th>
							<th class="px-5 py-3 font-medium">{$i18n.t('Size')}</th>
							<th class="px-5 py-3 font-medium">{$i18n.t('Uploaded')}</th>
							<th class="px-5 py-3"></th>
						</tr>
					</thead>
					<tbody>
						{#each materials as m (m.id)}
							<tr class="border-b border-gray-50 dark:border-gray-700/50">
								<td class="px-5 py-3 font-medium text-gray-800 dark:text-white">{m.title}</td>
								<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{m.class_name ?? '—'}</td>
								<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{m.content_type ?? '—'}</td>
								<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{fmtSize(m.size)}</td>
								<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{fmtDate(m.created_at)}</td>
								<td class="px-5 py-3 text-right"
									><button
										class="text-blue-600 dark:text-blue-400 text-xs hover:underline"
										on:click={() => download(m)}>{$i18n.t('Download')}</button
									></td
								>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	{:else if templates.length === 0}
		<div
			class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
		>
			{$i18n.t('No templates yet — create one to reuse across classes.')}
		</div>
	{:else}
		<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
			{#each templates as t (t.id)}
				<div
					class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5 flex items-start justify-between gap-3"
				>
					<div class="min-w-0">
						<div class="font-semibold text-gray-800 dark:text-white">{t.title}</div>
						{#if t.instructions}<div
								class="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2"
							>
								{t.instructions}
							</div>{/if}
						<div class="text-xs text-gray-400 mt-2">
							{$i18n.t('Created')}
							{fmtDate(t.created_at)}
						</div>
					</div>
					<button
						class="text-red-500 hover:text-red-600 text-xs whitespace-nowrap"
						on:click={() => removeTemplate(t)}>{$i18n.t('Delete')}</button
					>
				</div>
			{/each}
		</div>
		<p class="text-xs text-gray-400">
			{$i18n.t('Use a template from a class → Assignments to pre-fill a new assignment.')}
		</p>
	{/if}
</div>

{#if showTemplate}
	<TemplateModal on:close={() => (showTemplate = false)} on:saved={onTemplateSaved} />
{/if}
