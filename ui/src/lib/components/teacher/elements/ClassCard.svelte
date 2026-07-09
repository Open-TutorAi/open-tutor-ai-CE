<script lang="ts">
	import { getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import type { Classroom } from '$lib/apis/classrooms';

	const i18n: any = getContext('i18n');
	export let klass: Classroom;
</script>

<button
	class="text-left rounded-2xl bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition p-5 flex flex-col gap-3 w-full"
	on:click={() => goto(`/teacher/classes/${klass.id}`)}
>
	<div class="flex items-start justify-between">
		<div
			class="h-11 w-11 rounded-xl grid place-items-center bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300"
		>
			<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"
				><path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="1.8"
					d="M12 14l9-5-9-5-9 5 9 5z"
				/><path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="1.8"
					d="M12 14l6.16-3.42A12 12 0 0112 21a12 12 0 01-6.16-10.42L12 14z"
				/></svg
			>
		</div>
		<span class="text-gray-300 dark:text-gray-600">›</span>
	</div>
	<div>
		<div class="font-semibold text-gray-800 dark:text-white">{klass.name}</div>
		{#if klass.subject}
			<div class="text-sm text-gray-500 dark:text-gray-400">{klass.subject}</div>
		{/if}
	</div>
	<div class="text-sm text-gray-500 dark:text-gray-400">
		{klass.student_count}
		{klass.student_count === 1 ? $i18n.t('student') : $i18n.t('students')}
	</div>
</button>
