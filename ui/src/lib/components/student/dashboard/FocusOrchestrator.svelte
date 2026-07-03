<!-- Composant invisible monté dans le layout — gère les effets de bord du timer Focus -->
<script lang="ts">
	import { onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { focusEvent, beginBreak, beginWork, dashboardTab } from '$lib/stores/focusTimer';
	import { postFocusSession } from '$lib/apis/focus';
	import { isDemo } from '$lib/stores';

	let handlingEvent = false;

	const unsubscribe = focusEvent.subscribe((event) => {
		if (!event || !browser || handlingEvent) return;
		handlingEvent = true;

		void (async () => {
			try {
				if (event.type === 'work_complete') {
					const token = localStorage.getItem('token');
					if (token && !$isDemo) {
						try {
							await postFocusSession(token, event.workMinutes, 'work');
						} catch {}
					}
					toast.success('Session de travail terminée ! Pause méritée. 🎉', { duration: 4000 });
					beginBreak();
					dashboardTab.set('productivity');
					if (window.location.pathname !== '/student/dashboard') {
						await goto('/student/dashboard');
					}
				} else if (event.type === 'break_complete') {
					toast.info('Pause terminée ! Prêt pour une nouvelle session ? 💪', { duration: 4000 });
					beginWork();
					dashboardTab.set('productivity');
					if (window.location.pathname !== '/student/dashboard') {
						await goto('/student/dashboard');
					}
				}
			} finally {
				focusEvent.set(null);
				handlingEvent = false;
			}
		})();
	});

	onDestroy(unsubscribe);
</script>
