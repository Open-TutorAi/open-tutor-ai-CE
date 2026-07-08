
<!-- src/lib/components/StartSessionModal.svelte -->
<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { SessionsAPI } from '$lib/apis/sessions';
	import type { SessionOut } from '$lib/types/classroom';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();
	const token = () => localStorage.getItem('token') ?? '';

	export let show = false;
	export let classroomId: string;
	export let defaultSubject = '';

	let subject = defaultSubject;
	let objectives = '';
	let starting = false;
	let error = '';
	let created: SessionOut | null = null;

	$: if (show && !created) {
		subject = defaultSubject;
	}

	const close = () => {
		show = false;
		created = null;
		objectives = '';
		error = '';
	};

	const start = async () => {
		if (!subject.trim() || starting) return;
		starting = true;
		error = '';
		try {
			created = await SessionsAPI.startSession(
				token(),
				classroomId,
				subject.trim(),
				objectives.trim()
			);
			dispatch('started', created);
		} catch (err: any) {
			error = err?.detail || $i18n.t('Failed to start session');
		} finally {
			starting = false;
		}
	};

	const formatDate = (iso: string) =>
		new Intl.DateTimeFormat(navigator.language || 'en-US', {
			dateStyle: 'medium',
			timeStyle: 'short'
		}).format(new Date(iso));
</script>

{#if show}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<div
		data-testid="start-session-modal"
		class="absolute inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
		on:click={close}
	>
		<!-- svelte-ignore a11y-no-static-element-interactions -->
		<div
			role="dialog"
			aria-modal="true"
			class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6"
			on:click|stopPropagation
		>
			{#if created}
				<div data-testid="session-started-summary" class="space-y-3">
					<div class="flex items-center gap-2">
						<div
							class="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5 text-green-600"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M5 13l4 4L19 7"
								/>
							</svg>
						</div>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
							{$i18n.t('Session started')}
						</h2>
					</div>

					<dl class="text-sm space-y-1.5">
						<div class="flex justify-between gap-4">
							<dt class="text-gray-500 dark:text-gray-400">{$i18n.t('Course')}</dt>
							<dd class="font-medium text-gray-900 dark:text-white text-right">
								{created.subject}
							</dd>
						</div>
						<div class="flex justify-between gap-4">
							<dt class="text-gray-500 dark:text-gray-400">{$i18n.t('Started at')}</dt>
							<dd class="font-medium text-gray-900 dark:text-white text-right">
								{formatDate(created.scheduled_at)}
							</dd>
						</div>
						{#if created.objectives}
							<div>
								<dt class="text-gray-500 dark:text-gray-400 mb-0.5">{$i18n.t('Objectives')}</dt>
								<dd class="font-medium text-gray-900 dark:text-white whitespace-pre-wrap">
									{created.objectives}
								</dd>
							</div>
						{/if}
					</dl>

					<button
						type="button"
						on:click={close}
						class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
					>
						{$i18n.t('Close')}
					</button>
				</div>
			{:else}
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
					{$i18n.t('Start a session')}
				</h2>
				<p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
					{$i18n.t('Students will be able to join and check themselves present once started.')}
				</p>

				<div class="space-y-3">
					<div>
						<label
							for="session-subject"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
						>
							{$i18n.t('Course')}
						</label>
						<input
							id="session-subject"
							type="text"
							bind:value={subject}
							disabled={starting}
							placeholder={$i18n.t('e.g. Algebra — Chapter 3')}
							class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<div>
						<label
							for="session-objectives"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
						>
							{$i18n.t('Objectives')}
						</label>
						<textarea
							id="session-objectives"
							bind:value={objectives}
							disabled={starting}
							rows="3"
							placeholder={$i18n.t('What should students learn or do in this session?')}
							class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
						></textarea>
					</div>
				</div>

				{#if error}
					<p class="text-sm text-red-600 dark:text-red-400 mt-3">{error}</p>
				{/if}

				<div class="flex justify-end gap-2 mt-4">
					<button
						type="button"
						on:click={close}
						class="px-4 py-2 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-sm"
					>
						{$i18n.t('Cancel')}
					</button>
					<button
						type="button"
						data-testid="confirm-start-session"
						disabled={!subject.trim() || starting}
						on:click={start}
						class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
					>
						{starting ? $i18n.t('Starting...') : $i18n.t('Start Session')}
					</button>
				</div>
			{/if}
		</div>
	</div>
{/if}
