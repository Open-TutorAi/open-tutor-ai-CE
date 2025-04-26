<script >
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
<div class="flex flex-col items-center justify-center w-full max-w-md mx-auto space-y-4 p-4">
	<div
		class="w-full bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"
		role="region"
		aria-label="Course progress summary"
	>
		<div class="text">
			<h2 class="text-gray-800 dark:text-white font-medium text-base mb-6">
				{$i18n.t('Program Completion')}
			</h2>

			<div class="flex justify-start items-center mb-3">
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
		class="w-full bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"
		role="region"
		aria-label="Module progress tracker"
	>
		<ul class="flex flex-col space-y-6 list-none m-0 p-0">
			{#each modules as module, index}
				<li class="flex items-center">
					<!-- Status indicator -->
					<div class="relative flex justify-center w-10">
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
							<div class="absolute top-6 w-px h-6 bg-blue-600" aria-hidden="true"></div>
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

	<!-- Engagement Card -->
	<div
		class="w-full bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"
		role="region"
		aria-label="Engagement summary"
	>
		<div class="text-center">
			<h2 class="text-gray-800 dark:text-white font-medium text-base mb-6">
				{$i18n.t('How Engaged Am I?')}
			</h2>

			<!-- Toggle buttons -->
			<div class="flex justify-center gap-8 mb-8">
				<!-- Camera Toggle -->
				<button
					class="flex flex-col items-center gap-2 focus:outline-none group"
					on:click={toggleCamera}
					aria-label="Toggle camera {isCameraEnabled ? 'off' : 'on'}"
				>
					<div
						class="w-14 h-7 rounded-full transition-colors duration-200 ease-in-out relative {isCameraEnabled
							? 'bg-blue-500 dark:bg-blue-500'
							: 'bg-gray-600 dark:bg-gray-300'}"
					>
						<div
							class="absolute left-0.5 top-0.5 w-6 h-6 rounded-full bg-white dark:bg-gray-800 transform transition-transform duration-200 ease-in-out {isCameraEnabled
								? 'translate-x-7'
								: 'translate-x-0'}"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4 m-1 {isCameraEnabled
									? 'text-blue-400 dark:text-blue-500'
									: 'text-gray-400 dark:text-gray-400'}"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M4 5a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-1.586a1 1 0 01-.707-.293l-1.121-1.121A2 2 0 0011.172 3H8.828a2 2 0 00-1.414.586L6.293 4.707A1 1 0 015.586 5H4zm6 9a3 3 0 100-6 3 3 0 000 6z"
									clip-rule="evenodd"
								/>
							</svg>
						</div>
					</div>
					<span class="text-sm text-gray-600 dark:text-gray-400">Camera</span>
				</button>

				<!-- Audio Toggle -->
				<button
					class="flex flex-col items-center gap-2 focus:outline-none group"
					on:click={toggleAudio}
					aria-label="Toggle audio {isAudioEnabled ? 'off' : 'on'}"
				>
					<div
						class="w-14 h-7 rounded-full transition-colors duration-200 ease-in-out relative {isAudioEnabled
							? 'bg-blue-500 dark:bg-blue-500'
							: 'bg-gray-600 dark:bg-gray-300'}"
					>
						<div
							class="absolute left-0.5 top-0.5 w-6 h-6 rounded-full bg-white dark:bg-gray-800 transform transition-transform duration-200 ease-in-out {isAudioEnabled
								? 'translate-x-7'
								: 'translate-x-0'}"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4 m-1 {isAudioEnabled
									? 'text-blue-400 dark:text-blue-500'
									: 'text-gray-400 dark:text-gray-400'}"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z"
									clip-rule="evenodd"
								/>
							</svg>
						</div>
					</div>
					<span class="text-sm text-gray-600 dark:text-gray-400">Audio</span>
				</button>
			</div>

			<!-- Engagement Circle -->
			<div class="relative w-40 h-40 mx-auto">
				<svg class="w-full h-full" viewBox="0 0 100 100">
					<!-- Background circle -->
					<circle
						cx="50"
						cy="50"
						r="45"
						fill="none"
						stroke="#E5E7EB"
						stroke-width="10"
						class="dark:stroke-gray-700"
					/>
					<!-- Progress circle -->
					<circle
						cx="50"
						cy="50"
						r="45"
						fill="none"
						stroke="#3B82F6"
						stroke-width="10"
						stroke-linecap="round"
						transform="rotate(-90 50 50)"
						stroke-dasharray={`${animatedEngagement * 2.83} 283`}
						style="transition: stroke-dasharray 1s ease-out"
						class="dark:stroke-blue-500"
					/>
					<!-- Percentage text -->
					<text
						x="50"
						y="45"
						text-anchor="middle"
						dominant-baseline="middle"
						class="fill-gray-900 dark:fill-white"
						font-size="18"
						font-weight="bold"
					>
						{engagement}%
					</text>
					<text
						x="50"
						y="65"
						text-anchor="middle"
						dominant-baseline="middle"
						class="fill-gray-500 dark:fill-gray-400"
						font-size="10"
					>
						{$i18n.t('Engagement')}
					</text>
				</svg>
			</div>
		</div>
	</div>
</div>