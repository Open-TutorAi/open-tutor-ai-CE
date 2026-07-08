<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import { ClassroomsAPI } from '$lib/apis/classrooms';
	import { ForbiddenError } from '$lib/apis/errors';
	import type { ClassroomUpdate } from '$lib/types/classroom';

	const i18n = getContext('i18n');

	$: classroomId = $page.params.id;

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

	const LEVELS = [
		'1ère Année Collège',
		'2ème Année Collège',
		'3ème Année Collège',
		'Tronc Commun',
		'1ère Année Bac',
		'2ème Année Bac'
	];

	let loading = true;
	let notFound = false;
	let forbidden = false;
	let saving = false;
	let error: string | null = null;

	let formData: ClassroomUpdate = {
		name: '',
		subject: '',
		course: '',
		objectives: '',
		level: '',
		description: ''
	};

	const token = () => localStorage.getItem('token') ?? '';

	const load = async () => {
		loading = true;
		try {
			const classroom = await ClassroomsAPI.getDetail(token(), classroomId);
			formData = {
				name: classroom.name,
				subject: classroom.subject ?? '',
				course: classroom.course ?? '',
				objectives: classroom.objectives ?? '',
				level: classroom.level ?? '',
				description: classroom.description ?? ''
			};
		} catch (err) {
			if (err instanceof ForbiddenError) {
				forbidden = true;
			} else {
				notFound = true;
			}
		} finally {
			loading = false;
		}
	};

	onMount(() => {
		if (!browser) return;
		load();
	});

	$: canSave = (formData.name ?? '').trim().length > 0;

	const cancel = () => goto(`/classrooms/${classroomId}`);

	const save = async () => {
		if (!canSave) return;
		saving = true;
		error = null;
		try {
			await ClassroomsAPI.update(token(), classroomId, formData);
			goto(`/classrooms/${classroomId}`);
		} catch (err: any) {
			error = err?.detail || err?.message || $i18n.t('Failed to update classroom');
		} finally {
			saving = false;
		}
	};
</script>

{#if forbidden}
	<div class="flex items-center justify-center py-24">
		<p class="text-lg font-medium text-red-600">{$i18n.t('Accès non autorisé')}</p>
	</div>
{:else if loading}
	<div class="flex items-center justify-center py-24">
		<div class="animate-pulse text-gray-500 dark:text-gray-400">{$i18n.t('Loading...')}</div>
	</div>
{:else if notFound}
	<div class="flex items-center justify-center py-24">
		<p class="text-lg font-medium text-gray-600 dark:text-gray-400">
			{$i18n.t('Classroom not found')}
		</p>
	</div>
{:else}
	<div class="max-w-2xl mx-auto">
		<button
			type="button"
			on:click={cancel}
			class="inline-flex items-center text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 mb-4"
		>
			&larr; {$i18n.t('Back to Classroom')}
		</button>

		<h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
			{$i18n.t('Edit Classroom')}
		</h1>

		<div
			data-testid="edit-classroom-form"
			class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 space-y-4"
		>
			{#if error}
				<div
					class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-700 dark:text-red-300"
				>
					{error}
				</div>
			{/if}

			<div>
				<label
					for="edit-name"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
				>
					{$i18n.t('Classroom Name')}
				</label>
				<input
					id="edit-name"
					type="text"
					bind:value={formData.name}
					class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
				/>
			</div>

			<div>
				<label
					for="edit-description"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
				>
					{$i18n.t('Short Description')}
				</label>
				<textarea
					id="edit-description"
					bind:value={formData.description}
					rows="3"
					class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
				></textarea>
			</div>

			<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
				<div>
					<label
						for="edit-subject"
						class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
					>
						{$i18n.t('Subject')}
					</label>
					<select
						id="edit-subject"
						bind:value={formData.subject}
						class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						<option value="">{$i18n.t('Select a subject')}</option>
						{#each SUBJECTS as s}
							<option value={s}>{$i18n.t(s)}</option>
						{/each}
					</select>
				</div>

				<div>
					<label
						for="edit-level"
						class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
					>
						{$i18n.t('Level')}
					</label>
					<select
						id="edit-level"
						bind:value={formData.level}
						class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						<option value="">{$i18n.t('Select a level')}</option>
						{#each LEVELS as lvl}
							<option value={lvl}>{lvl}</option>
						{/each}
					</select>
				</div>
			</div>

			<div>
				<label
					for="edit-course"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
				>
					{$i18n.t('Course Name')}
				</label>
				<input
					id="edit-course"
					type="text"
					bind:value={formData.course}
					class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
				/>
			</div>

			<div>
				<label
					for="edit-objectives"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
				>
					{$i18n.t('Learning Objectives')}
				</label>
				<textarea
					id="edit-objectives"
					bind:value={formData.objectives}
					rows="4"
					class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
				></textarea>
			</div>

			<div class="flex justify-end gap-2 pt-4 border-t border-gray-100 dark:border-gray-700">
				<button
					type="button"
					on:click={cancel}
					class="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
				>
					{$i18n.t('Cancel')}
				</button>
				<button
					type="button"
					disabled={!canSave || saving}
					on:click={save}
					class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{saving ? $i18n.t('Saving...') : $i18n.t('Save Changes')}
				</button>
			</div>
		</div>
	</div>
{/if}
