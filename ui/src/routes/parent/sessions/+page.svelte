<script lang="ts">
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import { onMount, getContext } from 'svelte';
	import SessionsIA from '$lib/components/parent/SessionsIA.svelte';

	let loading = true;
	let error: string | null = null;
	const i18n = getContext('i18n');

	onMount(async () => {
		if (!$user) {
			goto('/auth');
			return;
		}
		if ($user.role !== 'parent') {
			goto(`/${$user.role}`);
			return;
		}
		loading = false;
	});
</script>

{#if loading}
	<div class="flex justify-center items-center min-h-screen">
		<div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
	</div>
{:else}
	<div class="min-h-screen bg-gray-100 dark:bg-gray-900 p-4 md:p-8">
		<div class="max-w-4xl mx-auto">
			<!-- Header -->
			<div class="flex items-center justify-between mb-6">
				<div>
					<button
						on:click={() => goto('/parent')}
						class="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-1 flex items-center gap-1"
					>
						← Retour
					</button>
					<h1 class="text-2xl font-bold text-gray-800 dark:text-white">
						📊 Sessions IA de mon enfant
					</h1>
					<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
						Suivez les sessions d'apprentissage et les performances
					</p>
				</div>
			</div>

			<!-- Composant sessions -->
			<SessionsIA />
		</div>
	</div>
{/if}
