<script>
	import { onMount } from 'svelte';
	import { getContext } from 'svelte';
	// Props for the component
	export let courseCompletion = 45;
	export let engagement = 75; // New prop for engagement
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

	<!-- Modules Progress Card -->
	<div
		class="w-full max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"
		role="region"
		aria-label="Module progress tracker"
	>
		<ul class="flex flex-col space-y-8 list-none m-0 p-0">
			{#each modules as module, index}
				<li class="flex items-center">
					<!-- Status indicator -->
					<div class="relative flex justify-center w-16">
						{#if module.status === 'completed'}
							<div
								class="bg-blue-500 dark:bg-blue-600 w-6 h-6 rounded-full flex items-center justify-center z-10"
								aria-hidden="true"
							>
								<!-- Check icon -->
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="12"
									height="12"
									viewBox="0 0 24 24"
									fill="none"
									stroke="white"
									stroke-width="3"
									stroke-linecap="round"
									stroke-linejoin="round"
								>
									<polyline points="20 6 9 17 4 12"></polyline>
								</svg>
							</div>
						{:else if module.status === 'in-progress'}
							<div
								class="w-6 h-6 rounded-full border-2 border-blue-600 flex items-center justify-center z-10"
								aria-hidden="true"
							>
								<div class="bg-blue-500 dark:bg-blue-600 w-2 h-2 rounded-full"></div>
							</div>
						{:else}
							<div
								class="w-6 h-6 rounded-full border border-gray-300 bg-white z-10"
								aria-hidden="true"
							></div>
						{/if}

						<!-- Vertical connector line -->
						{#if index < modules.length - 1}
							<div class="absolute top-6 w-px h-8 bg-blue-600" aria-hidden="true"></div>
						{/if}
					</div>

					<!-- Module name -->
					<span class="text-gray-900 dark:text-white font-medium">
						{module.name}
						<span class="sr-only">
							{#if module.status === 'completed'}
								, completed
							{:else if module.status === 'in-progress'}
								, in progress
							{:else}
								, not started
							{/if}
						</span>
					</span>
				</li>
			{/each}
		</ul>
	</div>

</div>
