<script lang="ts">
	import { onMount } from 'svelte';
	import Dashboard from '$lib/components/student/pages/Dashboard.svelte';
	import Onboarding from '$lib/components/student/Onboarding.svelte';

	let showOnboarding = false;

	onMount(() => {
		const onboardingDone = localStorage.getItem('onboardingDone');
		if (!onboardingDone) {
			showOnboarding = true;
		}
	});

	function finishOnboarding() {
		showOnboarding = false;
	}
</script>

{#if showOnboarding}
	<Onboarding onComplete={finishOnboarding} />
{/if}

<Dashboard />