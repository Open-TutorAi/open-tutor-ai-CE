
<script lang="ts">
	import { getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { ClassroomsAPI } from '$lib/apis/classrooms';
	import type { ClassroomCreate } from '$lib/types/classroom';
	import StepSubject from '$lib/components/wizard/StepSubject.svelte';
	import StepCourse from '$lib/components/wizard/StepCourse.svelte';
	import StepObjectives from '$lib/components/wizard/StepObjectives.svelte';
	import StepLevel from '$lib/components/wizard/StepLevel.svelte';
	import StepDetails from '$lib/components/wizard/StepDetails.svelte';
	import StepReview from '$lib/components/wizard/StepReview.svelte';

	const i18n = getContext('i18n');

	const STEP_LABELS = ['Subject', 'Course', 'Objectives', 'Level', 'Details', 'Review'];
	const TOTAL_STEPS = STEP_LABELS.length;

	let currentStep = 1;

	let formData = {
		name: '',
		description: '',
		subject: '',
		course: '',
		objectives: '',
		level: '',
		duration: '',
		language: ''
	};

	let submitting = false;
	let fieldErrors: { field: string; msg: string }[] = [];

	$: canProceed =
		currentStep === 1
			? formData.name.trim().length > 0 && formData.description.trim().length > 0
			: true;

	const next = () => {
		if (!canProceed || currentStep >= TOTAL_STEPS) return;
		currentStep += 1;
	};

	const back = () => {
		if (currentStep > 1) currentStep -= 1;
	};

	const cancel = () => {
		goto('/classrooms');
	};

	const parseFieldErrors = (err: any): { field: string; msg: string }[] => {
		if (Array.isArray(err?.detail)) {
			return err.detail.map((d: any) => ({
				field: Array.isArray(d.loc) ? String(d.loc[d.loc.length - 1]) : 'error',
				msg: d.msg || $i18n.t('Invalid value')
			}));
		}
		return [
			{
				field: 'error',
				msg: err?.detail || err?.message || $i18n.t('Failed to create classroom')
			}
		];
	};

	const submit = async () => {
		const token = localStorage.getItem('token') ?? '';
		const payload: ClassroomCreate = {
			name: formData.name,
			description: formData.description,
			subject: formData.subject,
			course: formData.course,
			objectives: formData.objectives,
			level: formData.level
		};

		submitting = true;
		fieldErrors = [];
		try {
			const created = await ClassroomsAPI.create(token, payload);
			goto(`/classrooms/${created.id}`);
		} catch (err) {
			fieldErrors = parseFieldErrors(err);
		} finally {
			submitting = false;
		}
	};
</script>

<div class="max-w-3xl mx-auto">
	<button
		type="button"
		on:click={() => goto('/classrooms')}
		class="inline-flex items-center text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 mb-4"
	>
		&larr; {$i18n.t('My Classrooms')}
	</button>

	<h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
		{$i18n.t('Create Classroom')}
	</h1>

	<div class="flex items-center mb-8" data-testid="wizard-progress">
		{#each STEP_LABELS as label, index}
			{@const stepNumber = index + 1}
			<div class="flex items-center flex-1">
				<div class="flex flex-col items-center">
					<div
						class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium border-2 {currentStep >=
						stepNumber
							? 'bg-blue-600 border-blue-600 text-white'
							: 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-500'}"
					>
						{#if currentStep > stepNumber}
							&#10003;
						{:else}
							{stepNumber}
						{/if}
					</div>
					<span class="text-xs mt-1 text-gray-600 dark:text-gray-400">{$i18n.t(label)}</span>
				</div>
				{#if stepNumber < TOTAL_STEPS}
					<div
						class="flex-1 h-0.5 mx-2 {currentStep > stepNumber
							? 'bg-blue-600'
							: 'bg-gray-300 dark:bg-gray-600'}"
					></div>
				{/if}
			</div>
		{/each}
	</div>

	<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
		{#if currentStep === 1}
			<StepSubject
				bind:name={formData.name}
				bind:description={formData.description}
				bind:subject={formData.subject}
			/>
		{:else if currentStep === 2}
			<StepCourse bind:course={formData.course} />
		{:else if currentStep === 3}
			<StepObjectives bind:objectives={formData.objectives} />
		{:else if currentStep === 4}
			<StepLevel bind:level={formData.level} />
		{:else if currentStep === 5}
			<StepDetails bind:duration={formData.duration} bind:language={formData.language} />
		{:else}
			<StepReview {formData} {submitting} {fieldErrors} onSubmit={submit} />
		{/if}

		<div class="flex justify-between mt-8 pt-4 border-t border-gray-100 dark:border-gray-700">
			{#if currentStep === 1}
				<button
					type="button"
					on:click={cancel}
					class="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
				>
					{$i18n.t('Cancel')}
				</button>
			{:else}
				<button
					type="button"
					on:click={back}
					class="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
				>
					{$i18n.t('Back')}
				</button>
			{/if}

			{#if currentStep < TOTAL_STEPS}
				<button
					type="button"
					disabled={!canProceed}
					on:click={next}
					class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{$i18n.t('Next')}
				</button>
			{/if}
		</div>
	</div>
</div>
