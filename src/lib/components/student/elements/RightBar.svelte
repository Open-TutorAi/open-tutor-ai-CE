<script>
	import { onMount } from 'svelte';
	import { getContext } from 'svelte';
	// Props for the component
	export let courseCompletion = 0; // TODO  calcul this indicator Dynamiquely
	export let engagement = 0; // New prop for engagement
	export let modules = [
		{ id: 1, name: 'Introduction', status: 'completed' },
		{ id: 2, name: 'HDFS', status: 'completed' },
		{ id: 3, name: 'MapReduce', status: 'in-progress' },
		{ id: 4, name: 'YARN', status: 'not-started' },
		{ id: 5, name: 'Hive & Pig', status: 'not-started' }
	];

	// Toggle states
	let isCameraEnabled = false;
	let isAudioEnabled = false;
	// Animation for progress bars
	let animatedProgress = 0;
	let animatedEngagement = 0;
	const i18n = getContext('i18n');

	onMount(() => {
		setTimeout(() => {
			animatedProgress = courseCompletion;
			animatedEngagement = engagement;
		}, 200);
	});

	// Calculate number of completed modules for accessibility
	$: completedModules = modules.filter((module) => module.status === 'completed').length;
	// Handle toggle changes
	function toggleCamera() {
		isCameraEnabled = !isCameraEnabled;
	}
	function toggleAudio() {
		isAudioEnabled = !isAudioEnabled;
	}
</script>

<!-- Progress Summary Card -->
<div class="flex flex-col items-center justify-center w-full h-full mx-auto p-4">
	<div
		class="w-full max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6"
		role="region"
		aria-label="Course progress summary"
	>
		<div class="text">
			<h2 class="text-gray-800 dark:text-white font-medium text-xl mb-4 text-center">
				{$i18n.t('Program Completion')}
			</h2>

			<div class="flex justify-center items-center mb-3">
				<span class="text-gray-900 dark:text-white text-2xl font-bold" aria-live="polite">
					{courseCompletion}%
				</span>
			</div>

			<div
				class="bg-blue-100 dark:bg-gray-700 h-3 w-full rounded-full overflow-hidden"
				role="progressbar"
				aria-valuenow={courseCompletion}
				aria-valuemin="0"
				aria-valuemax="100"
			>
				<div
					class="bg-green-500 dark:bg-blue-500 h-full rounded-full transition-all duration-1000 ease-out"
					style="width: {animatedProgress}%"
				></div>
			</div>
		</div>
	</div>


</div>
