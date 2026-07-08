<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { fade } from 'svelte/transition';
	import type { PresenceOut } from '$lib/types/classroom';
	import PresenceStatusBadge from '$lib/components/attendance/PresenceStatusBadge.svelte';
	import StudentAvatar from '$lib/components/StudentAvatar.svelte';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let presences: PresenceOut[] = [];
</script>

<div data-testid="session-detail">
	<table class="w-full text-sm">
		<thead>
			<tr class="text-left text-gray-500 dark:text-gray-400">
				<th class="py-2">{$i18n.t('Student')}</th>
				<th class="py-2">{$i18n.t('Status')}</th>
			</tr>
		</thead>
		<tbody>
			{#each presences as presence (presence.id)}
				<!-- svelte-ignore a11y-click-events-have-key-events -->
				<!-- svelte-ignore a11y-no-static-element-interactions -->
				<tr
					in:fade={{ duration: 150 }}
					class="border-t border-gray-100 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
					on:click={() => dispatch('selectStudent', presence.student_id)}
				>
					<td class="py-2 text-gray-900 dark:text-white">
						<div class="flex items-center gap-2">
							<StudentAvatar name={presence.student_name} size="sm" />
							{presence.student_name}
						</div>
					</td>
					<td class="py-2"><PresenceStatusBadge status={presence.status} /></td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
