
<!-- src/lib/components/StudentInfoModal.svelte -->
<script lang="ts">
	import { getContext } from 'svelte';
	import { SessionsAPI } from '$lib/apis/sessions';
	import type { StudentOut, StudentHistory } from '$lib/types/classroom';
	import StudentAvatar from './StudentAvatar.svelte';
	import StudentHistoryPanel from './attendance/StudentHistoryPanel.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	const i18n = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';

	export let show = false;
	export let student: StudentOut | null = null;
	export let classroomId: string;

	let history: StudentHistory | null = null;
	let loading = false;
	let error = '';

	$: if (show && student) {
		loadHistory(student.id);
	}

	const loadHistory = async (studentId: string) => {
		loading = true;
		error = '';
		history = null;
		try {
			history = await SessionsAPI.getStudentHistory(token(), classroomId, studentId);
		} catch (err: any) {
			error = err?.detail || $i18n.t('Failed to load student history');
		} finally {
			loading = false;
		}
	};

	const close = () => {
		show = false;
	};
</script>

{#if show && student}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<div
		data-testid="student-info-modal"
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
			<div class="flex items-start justify-between mb-1">
				<div class="flex items-center gap-3">
					<StudentAvatar name={student.name} imageUrl={student.profile_image_url} size="lg" />
					<div>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">{student.name}</h2>
						<p class="text-sm text-gray-500 dark:text-gray-400">{student.email}</p>
					</div>
				</div>
				<button
					type="button"
					on:click={close}
					aria-label={$i18n.t('Close')}
					class="p-1.5 rounded-full text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
				>
					<XMark className="w-4 h-4" />
				</button>
			</div>

			<p class="text-xs text-gray-400 dark:text-gray-500 mb-4">
				{$i18n.t('Enrolled on')}
				{new Date(student.enrolled_at).toLocaleDateString()}
			</p>

			{#if loading}
				<div
					class="h-24 rounded-lg bg-gray-100 dark:bg-gray-700 animate-pulse"
					aria-hidden="true"
				></div>
			{:else if error}
				<p class="text-sm text-red-600 dark:text-red-400">{error}</p>
			{:else if history}
				<StudentHistoryPanel {history} />
			{/if}
		</div>
	</div>
{/if}
