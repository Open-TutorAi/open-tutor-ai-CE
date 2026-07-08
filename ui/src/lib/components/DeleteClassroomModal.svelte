<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { ClassroomsAPI } from '$lib/apis/classrooms';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let show = false;
	export let classroomId: string;
	export let classroomName: string;

	let deleting = false;
	let error: string | null = null;

	const CONSEQUENCES = [
		'All sessions and attendance records for this classroom will be permanently deleted.',
		'Enrolled students will lose access to this classroom immediately.',
		"Student accounts and their other classrooms won't be affected.",
		'This action cannot be undone.'
	];

	const cancel = () => {
		show = false;
		error = null;
	};

	const confirmDelete = async () => {
		deleting = true;
		error = null;
		try {
			const token = localStorage.getItem('token') ?? '';
			await ClassroomsAPI.delete(token, classroomId);
			show = false;
			dispatch('deleted', classroomId);
			goto('/classrooms');
		} catch (err: any) {
			error = err?.detail || err?.message || $i18n.t('Failed to delete classroom');
		} finally {
			deleting = false;
		}
	};
</script>

{#if show}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<div
		data-testid="delete-classroom-modal"
		class="absolute inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
		on:click={cancel}
	>
		<!-- svelte-ignore a11y-no-static-element-interactions -->
		<div
			role="dialog"
			aria-modal="true"
			class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6"
			on:click|stopPropagation
		>
			<div class="flex items-start gap-3 mb-4">
				<div
					class="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-6 w-6 text-red-600"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
						/>
					</svg>
				</div>
				<div>
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
						{$i18n.t('Delete Classroom')}
					</h2>
					<p class="text-sm text-gray-600 dark:text-gray-400">
						{$i18n.t('Are you sure you want to delete')} "{classroomName}"?
					</p>
				</div>
			</div>

			<ul class="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 space-y-1 mb-4">
				{#each CONSEQUENCES as item}
					<li>{$i18n.t(item)}</li>
				{/each}
			</ul>

			{#if error}
				<p class="text-sm text-red-600 mb-4">{error}</p>
			{/if}

			<div class="flex justify-end gap-2">
				<button
					type="button"
					on:click={cancel}
					class="px-4 py-2 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
				>
					{$i18n.t('Cancel')}
				</button>
				<button
					type="button"
					disabled={deleting}
					on:click={confirmDelete}
					class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
				>
					{deleting ? $i18n.t('Deleting...') : $i18n.t('Delete Classroom')}
				</button>
			</div>
		</div>
	</div>
{/if}
