<!-- Assignments.svelte -->
<script lang="ts">
	import { getContext } from 'svelte';
	import { isDemo, demoData } from '$lib/stores';
	import { toast } from 'svelte-sonner';

	const i18n = getContext('i18n');
	
	$: assignments = $isDemo ? $demoData.assignments : [];
	
	function getStatusColor(status: string) {
		switch (status) {
			case 'completed': return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-200';
			case 'in-progress': return 'text-blue-600 bg-blue-100 dark:bg-blue-900 dark:text-blue-200';
			case 'pending': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-200';
			case 'overdue': return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-200';
			default: return 'text-gray-600 bg-gray-100';
		}
	}
	
	function getStatusLabel(status: string) {
		return $i18n.t(status.charAt(0).toUpperCase() + status.slice(1).replace('-', ' '));
	}
	
	function handleSubmit(assignment: any) {
		if ($isDemo) {
			toast.info($i18n.t('Submissions are disabled in demo mode'));
		} else {
			// Real submission logic would go here
			toast.info($i18n.t('Submission functionality coming soon'));
		}
	}
</script>

<div class="mb-6">
	<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-4">{$i18n.t('Assignments Page')}</h2>
	
	{#if $isDemo && assignments.length > 0}
		<div class="grid gap-4 mt-6">
			{#each assignments as assignment (assignment.id)}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
					<div class="flex justify-between items-start mb-3">
						<div class="flex-1">
							<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
								{assignment.title}
							</h3>
							<p class="text-sm text-gray-600 dark:text-gray-400 mb-2">
								{assignment.description}
							</p>
							<div class="flex items-center gap-3 text-sm">
								<span class="text-gray-500 dark:text-gray-400">
									<strong>{$i18n.t('Course')}:</strong> {assignment.course}
								</span>
								<span class="text-gray-500 dark:text-gray-400">
									<strong>{$i18n.t('Due')}:</strong> {assignment.due}
								</span>
								<span class="text-gray-500 dark:text-gray-400">
									<strong>{$i18n.t('Points')}:</strong> {assignment.points}
								</span>
							</div>
						</div>
						<div class="flex flex-col items-end gap-2">
							<span class="px-3 py-1 rounded-full text-xs font-medium {getStatusColor(assignment.status)}">
								{getStatusLabel(assignment.status)}
							</span>
							{#if assignment.status !== 'completed'}
								<button
									on:click={() => handleSubmit(assignment)}
									class="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
								>
									{$i18n.t('Submit')}
								</button>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center mt-6">
			<p class="text-gray-600 dark:text-gray-400">{$i18n.t('No assignments available')}</p>
			{#if !$isDemo}
				<p class="text-sm text-gray-500 dark:text-gray-500 mt-2">{$i18n.t('Enable demo mode to see sample assignments')}</p>
			{/if}
		</div>
	{/if}
</div>
