<!-- EngagementGauge.svelte -->
<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { tweened } from 'svelte/motion';
	import { cubicOut } from 'svelte/easing';
	import { fade } from 'svelte/transition';

	const i18n = getContext<Writable<i18nType>>('i18n');
	
	// Props
	export let percentage: number = 0;
	export let sessions: number = 0;
	export let avgDuration: string = "0 min";
	
	// Toggle states
	let cameraEnabled = true;
	let micEnabled = false;
	
	// Tooltip states
	let showCameraTooltip = false;
	let showMicTooltip = false;
	
	// Calculate the stroke dash offset for the circular progress
	const circumference = 251.2; // 2 * PI * 40
	const progressTween = tweened(0, {
		duration: 1500,
		easing: cubicOut
	});
	
	$: dashOffset = circumference - (circumference * $progressTween / 100);
	
	// Toggle handlers
	function toggleCamera() {
		cameraEnabled = !cameraEnabled;
	}
	
	function toggleMic() {
		micEnabled = !micEnabled;
	}
	
	onMount(() => {
		// Animate the percentage when component mounts
		progressTween.set(percentage);
	});
</script>

<div class="bg-white dark:bg-gray-800 p-5 rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-300">
	<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6 text-center">{$i18n.t('How Engaged Am I?')}</h2>
	
	<!-- Toggle buttons -->
	<div class="flex justify-center gap-8 mb-8">
		<!-- Camera toggle -->
		<div class="flex flex-col items-center">
			<button 
				class={`w-12 h-6 rounded-full flex items-center px-0.5 transition-colors duration-300 ${cameraEnabled ? 'bg-gray-700' : 'bg-gray-300'}`}
				on:click={toggleCamera}
				aria-label={cameraEnabled ? 'Disable camera' : 'Enable camera'}
			>
				<div 
					class={`w-5 h-5 rounded-full bg-white flex items-center justify-center transform transition-transform duration-300 ${cameraEnabled ? 'translate-x-6' : 'translate-x-0'}`}
				>
					<svg xmlns="http://www.w3.org/2000/svg" class={`h-3 w-3 ${cameraEnabled ? 'text-blue-500' : 'text-gray-400'} transition-colors duration-300`} viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M4 5a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-1.586a1 1 0 01-.707-.293l-1.121-1.121A2 2 0 0011.172 3H8.828a2 2 0 00-1.414.586L6.293 4.707A1 1 0 015.586 5H4zm6 9a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd" />
					</svg>
				</div>
			</button>
			<span class="text-xs text-gray-500 dark:text-gray-400 mt-1">Camera</span>
		</div>

		<!-- Microphone toggle -->
		<div class="flex flex-col items-center">
			<button 
				class={`w-12 h-6 rounded-full flex items-center px-0.5 transition-colors duration-300 ${micEnabled ? 'bg-gray-700' : 'bg-gray-300'}`}
				on:click={toggleMic}
				aria-label={micEnabled ? 'Disable microphone' : 'Enable microphone'}
			>
				<div 
					class={`w-5 h-5 rounded-full bg-white flex items-center justify-center transform transition-transform duration-300 ${micEnabled ? 'translate-x-6' : 'translate-x-0'}`}
				>
					<svg xmlns="http://www.w3.org/2000/svg" class={`h-3 w-3 ${micEnabled ? 'text-blue-500' : 'text-gray-400'} transition-colors duration-300`} viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clip-rule="evenodd" />
					</svg>
				</div>
			</button>
			<span class="text-xs text-gray-500 dark:text-gray-400 mt-1">Microphone</span>
		</div>
	</div>
	
	<!-- Circular progress indicator -->
	<div class="flex justify-center">
		<div class="relative w-40 h-40 engagement-container">
			<svg class="w-full h-full" viewBox="0 0 100 100">
				<!-- Background circle -->
				<circle cx="50" cy="50" r="40" fill="none" stroke="#f1f5f9" stroke-width="12" />
				
				<!-- Progress circle -->
				<circle 
					cx="50" 
					cy="50" 
					r="40" 
					fill="none" 
					stroke="#2563eb" 
					stroke-width="12" 
					stroke-dasharray={circumference} 
					stroke-dashoffset={dashOffset} 
					transform="rotate(-90 50 50)" 
					stroke-linecap="round"
					class="progress-circle"
				/>
			</svg>
			<div class="absolute inset-0 flex flex-col items-center justify-center">
				<div class="text-4xl font-bold text-blue-600 percentage-text">{Math.round($progressTween)}%</div>
				<div class="text-sm text-gray-400 mt-1">{$i18n.t('Engagement')}</div>
			</div>
		</div>
	</div>
</div>

<style>
	.progress-circle {
		transition: stroke-dashoffset 1.5s ease-out;
	}
	
	.percentage-text {
		animation: pulseText 3s infinite;
	}
	
	.engagement-container:hover .progress-circle {
		filter: drop-shadow(0 0 3px rgba(37, 99, 235, 0.5));
	}
	
	@keyframes pulseText {
		0% {
			opacity: 0.9;
			transform: scale(1);
		}
		50% {
			opacity: 1;
			transform: scale(1.05);
		}
		100% {
			opacity: 0.9;
			transform: scale(1);
		}
	}
</style> 