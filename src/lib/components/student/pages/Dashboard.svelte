<!-- Dashboard.svelte -->
<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { goto } from '$app/navigation';
	import CourseCard from '../components/CourseCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// Sample enrolled courses data with subjects
	const enrolledCourses = [
		{
			id: 'html-css',
			title: 'Basic: HTML and CSS',
			progress: 75,
			subject: 'computer-science',
			href: '#'
		},
		{
			id: 'branding',
			title: 'Branding Design',
			progress: 45,
			subject: 'english',
			href: '#'
		},
		{
			id: 'motion',
			title: 'Motion Design',
			progress: 60,
			subject: 'computer-science',
			href: '#'
		},
		{
			id: 'fractions',
			title: 'Les fractions',
			progress: 30,
			subject: 'mathematics',
			href: '#'
		},
		{
			id: 'biology',
			title: 'Cell Biology',
			progress: 85,
			subject: 'biology',
			href: '#'
		},
		{
			id: 'chemistry',
			title: 'Organic Chemistry',
			progress: 40,
			subject: 'chemistry',
			href: '#'
		},
		{
			id: 'physics',
			title: 'Quantum Physics',
			progress: 55,
			subject: 'physics',
			href: '#'
		},
		{
			id: 'geography',
			title: 'World Geography',
			progress: 65,
			subject: 'geography',
			href: '#'
		}
	];

	// State for pagination
	let currentPage = 0;
	const cardsPerPage = 4;

	// Calculate total pages
	$: totalPages = Math.ceil(enrolledCourses.length / cardsPerPage);

	// Get current page courses
	$: currentCourses = enrolledCourses.slice(
		currentPage * cardsPerPage,
		(currentPage + 1) * cardsPerPage
	);

	// Navigation functions
	function nextPage() {
		if (currentPage < totalPages - 1) {
			currentPage += 1;
		}
	}

	function previousPage() {
		if (currentPage > 0) {
			currentPage -= 1;
		}
	}

	// State to control the join course popup
	let showJoinCoursePopup = false;

	// State to control the support popup
	let showSupportPopup = false;

	// Toggle the popups
	function toggleJoinCoursePopup() {
		showJoinCoursePopup = !showJoinCoursePopup;
		if (showJoinCoursePopup) showSupportPopup = false;
	}

	function toggleSupportPopup() {
		showSupportPopup = !showSupportPopup;
		if (showSupportPopup) showJoinCoursePopup = false;
	}

	// Course code input
	let courseCode = '';

	// Don't show again state
	let dontShowAgain = false;

	// Handle joining a course
	function handleJoinCourse() {
		if (courseCode === '0000') {
			// Redirect to student chat component if code is 0000
			goto('/student/chat');
			showJoinCoursePopup = false;
		} else if (courseCode.trim() !== '') {
			// For other valid codes, you would implement the actual join logic here
			// For now, just close the popup
			showJoinCoursePopup = false;
		}
	}

	// Handle creating support
	function handleCreateSupport() {
		// Navigate to student support page
		goto('/student/support');
		showSupportPopup = false;
	}
</script>

<div class="flex flex-col gap-6">
	<div class="flex justify-end">
		<div class="flex gap-4">
			<button
				class="flex items-center gap-2 bg-indigo-500 dark:bg-indigo-600 text-white py-3 px-6 rounded-full hover:bg-indigo-600 dark:hover:bg-indigo-700 transition-colors"
				on:click={toggleJoinCoursePopup}
			>
				<span class="text-xl font-bold">+</span>
				<span>{$i18n.t('Course')}</span>
			</button>
			<button
				class="flex items-center gap-2 bg-indigo-500 dark:bg-indigo-600 text-white py-3 px-6 rounded-full hover:bg-indigo-600 dark:hover:bg-indigo-700 transition-colors"
				on:click={toggleSupportPopup}
			>
				<span class="text-xl font-bold">+</span>
				<span>{$i18n.t('Support')}</span>
			</button>
		</div>
	</div>

	<div class="flex flex-col gap-6">
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
			{#each currentCourses as course}
				<CourseCard
					title={course.title}
					progress={course.progress}
					subject={course.subject}
					href={course.href}
				/>
			{/each}
		</div>

		{#if totalPages > 1}
			<div class="flex justify-center gap-4 mt-4">
				<button
					class="p-2 rounded-full bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
					on:click={previousPage}
					disabled={currentPage === 0}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-5 w-5 text-gray-600 dark:text-gray-300"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
					</svg>
				</button>
				<span class="flex items-center text-sm text-gray-600 dark:text-gray-300">
					Page {currentPage + 1} of {totalPages}
				</span>
				<button
					class="p-2 rounded-full bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
					on:click={nextPage}
					disabled={currentPage === totalPages - 1}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-5 w-5 text-gray-600 dark:text-gray-300"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
					</svg>
				</button>
			</div>
		{/if}
	</div>
</div>

<!-- Join Course Popup Modal -->
{#if showJoinCoursePopup}
	<div
		class="fixed inset-0 backdrop-blur-sm bg-white/30 dark:bg-black/30 flex items-center justify-center z-50"
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 w-full max-w-md mx-auto relative"
		>
			<!-- Close Button -->
			<button
				class="absolute top-3 right-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none"
				on:click={toggleJoinCoursePopup}
			>
				<span class="text-2xl font-light">×</span>
			</button>

			<!-- OT Logo -->
			<div class="flex justify-center mb-8">
				<img src="/favicon.png" alt="OT Logo" class="w-26 h-26" />
			</div>

			<!-- Title and Instructions -->
			<h2 class="text-center text-xl font-bold mb-2 text-gray-900 dark:text-white">
				{$i18n.t('Enter the course code provided by your teacher')}
			</h2>
			<p class="text-center text-gray-500 dark:text-gray-400 mb-6">
				{$i18n.t('The code is a 6-8 character alphanumeric string')}
			</p>

			<!-- Course Code Input -->
			<div class="mb-6">
				<input
					type="text"
					bind:value={courseCode}
					placeholder="Enter Course Code"
					class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md text-center focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
					on:keydown={(e) => e.key === 'Enter' && handleJoinCourse()}
				/>
			</div>

			<!-- Help Text -->
			<p class="text-center text-gray-500 dark:text-gray-400 mb-6">
				{$i18n.t('Need a code? Ask your teacher or institution')}
			</p>

			<!-- Join Button -->
			<div class="flex justify-center mb-4">
				<button
					class="bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-700 dark:hover:bg-indigo-800 text-white py-3 px-8 rounded-full font-medium"
					on:click={handleJoinCourse}
				>
					{$i18n.t('Join Course')}
				</button>
			</div>

			<!-- Create Course Link -->
			<div class="text-center">
				<span class="text-gray-500 dark:text-gray-400">or</span>
				<a href="#" class="text-blue-600 dark:text-blue-400 hover:underline"
					>{$i18n.t('create your own course')}</a
				>
			</div>
		</div>
	</div>
{/if}

<!-- Support Popup Modal -->
{#if showSupportPopup}
	<div
		class="fixed inset-0 backdrop-blur-sm bg-white/30 dark:bg-black/30 flex items-center justify-center z-50"
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 w-full max-w-md mx-auto relative"
		>
			<!-- Close Button -->
			<button
				class="absolute top-3 right-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none"
				on:click={toggleSupportPopup}
			>
				<span class="text-2xl font-light">×</span>
			</button>

			<!-- OT Logo -->
			<div class="flex justify-center mb-8">
				<img src="/favicon.png" alt="OT Logo" class="w-26 h-26" />
			</div>

			<!-- Title -->
			<h2 class="text-center text-xl font-bold text-gray-900 dark:text-white">
				{$i18n.t('Create Personalized Tutorials for any Subject or Topic')}
			</h2>

			<!-- Divider -->
			<div class="my-8">
				<hr class="border-gray-200 dark:border-gray-600" />
			</div>

			<!-- Learning Path Section -->
			<h3 class="text-center text-lg font-medium mb-6 text-gray-900 dark:text-white">
				{$i18n.t('Create Tour Learning Path')}
			</h3>

			<!-- Steps -->
			<div class="space-y-4 mb-10 px-4">
				<div class="flex items-center gap-4">
					<div
						class="flex-shrink-0 bg-[#004AAD] text-white rounded-full w-7 h-7 flex items-center justify-center"
					>
						<span class="font-bold">1</span>
					</div>
					<span class="text-gray-800 dark:text-gray-200"
						>{$i18n.t('Choose your topic and difficulty level')}</span
					>
				</div>
				<div class="flex items-center gap-4">
					<div
						class="flex-shrink-0 bg-[#004AAD] text-white rounded-full w-7 h-7 flex items-center justify-center"
					>
						<span class="font-bold">2</span>
					</div>
					<span class="text-gray-800 dark:text-gray-200"
						>{$i18n.t('Set your learning objectives')}</span
					>
				</div>
				<div class="flex items-center gap-4">
					<div
						class="flex-shrink-0 bg-[#004AAD] text-white rounded-full w-7 h-7 flex items-center justify-center"
					>
						<span class="font-bold">3</span>
					</div>
					<span class="text-gray-800 dark:text-gray-200"
						>{$i18n.t('Enjoy AI-powered personalized learning')}</span
					>
				</div>
			</div>

			<!-- Create Support Button -->
			<div class="flex justify-center mb-8">
				<button
					class="bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-700 dark:hover:bg-indigo-800 text-white py-3 px-12 rounded-full font-medium"
					on:click={handleCreateSupport}
				>
					{$i18n.t('Create My support')}
				</button>
			</div>

			<!-- Don't Show Again Checkbox -->
			<div class="flex items-center justify-center gap-2 mt-4">
				<input
					type="checkbox"
					id="dontShow"
					bind:checked={dontShowAgain}
					class="h-4 w-4 text-indigo-600 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded focus:ring-indigo-500"
				/>
				<label for="dontShow" class="text-sm text-gray-500 dark:text-gray-400"
					>{$i18n.t('Don\'t show me again')}</label
				>
			</div>
		</div>
	</div>
{/if}
