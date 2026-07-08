<!-- src/lib/components/CreateStudentModal.svelte -->
<script lang="ts">
	import { getContext, createEventDispatcher } from 'svelte';
	import { ClassroomsAPI } from '$lib/apis/classrooms';
	import { userSignUp } from '$lib/apis/auths';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let show = false;
	export let classroomId: string;

	let name = '';
	let email = '';
	let password = '';
	let loading = false;
	let error: string | null = null;

	const reset = () => {
		name = '';
		email = '';
		password = '';
		error = null;
		loading = false;
	};

	const handleSubmit = async () => {
		if (!name.trim() || !email.trim() || !password.trim()) {
			error = $i18n.t('All fields are required');
			return;
		}

		loading = true;
		error = null;

		try {
			const token = localStorage.getItem('token') ?? '';

			// 1. Créer le compte étudiant
			await userSignUp(name.trim(), email.trim(), password.trim(), '', 'user');

			// 2. Ajouter l'étudiant à la classe
			await ClassroomsAPI.addStudent(token, classroomId, email.trim());

			reset();
			show = false;
			dispatch('studentAdded');
		} catch (err: any) {
			error = err?.message || $i18n.t('Failed to create student');
		} finally {
			loading = false;
		}
	};

	const handleCancel = () => {
		reset();
		show = false;
	};
</script>

{#if show}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<div
		data-testid="create-student-modal"
		class="absolute inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
		on:click={handleCancel}
	>
		<!-- svelte-ignore a11y-no-static-element-interactions -->
		<div
			role="dialog"
			aria-modal="true"
			class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6"
			on:click|stopPropagation
		>
			<h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
				{$i18n.t('Create New Student')}
			</h2>
			<p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
				{$i18n.t('Create a student account and add them to this classroom')}
			</p>

			{#if error}
				<div
					class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-700 dark:text-red-300 mb-4"
				>
					{error}
				</div>
			{/if}

			<form on:submit|preventDefault={handleSubmit}>
				<div class="space-y-4">
					<div>
						<label
							for="student-name"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
						>
							{$i18n.t('Full Name')} *
						</label>
						<input
							id="student-name"
							type="text"
							bind:value={name}
							placeholder={$i18n.t('e.g. John Doe')}
							class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							disabled={loading}
							required
						/>
					</div>

					<div>
						<label
							for="student-email"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
						>
							{$i18n.t('Email Address')} *
						</label>
						<input
							id="student-email"
							type="email"
							bind:value={email}
							placeholder={$i18n.t('e.g. student@example.com')}
							class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							disabled={loading}
							required
						/>
					</div>

					<div>
						<label
							for="student-password"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
						>
							{$i18n.t('Password')} *
						</label>
						<input
							id="student-password"
							type="password"
							bind:value={password}
							placeholder={$i18n.t('Minimum 8 characters')}
							class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							disabled={loading}
							minlength="8"
							required
						/>
						<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
							{$i18n.t('Minimum 8 characters')}
						</p>
					</div>
				</div>

				<div class="flex justify-end gap-2 mt-6 pt-4 border-t border-gray-100 dark:border-gray-700">
					<button
						type="button"
						on:click={handleCancel}
						class="px-4 py-2 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
						disabled={loading}
					>
						{$i18n.t('Cancel')}
					</button>
					<button
						type="submit"
						disabled={loading || !name.trim() || !email.trim() || !password.trim()}
						class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{loading ? $i18n.t('Creating...') : $i18n.t('Create & Add')}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
