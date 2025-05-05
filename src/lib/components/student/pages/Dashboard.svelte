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
			href: '/student/studyguide'
		},
		{
			id: 'branding',
			title: 'Branding Design',
			progress: 45,
			subject: 'english',
			href: '/student/studyguide'
		},
		{
			id: 'motion',
			title: 'Motion Design',
			progress: 60,
			subject: 'computer-science',
			href: '/student/studyguide'
		},
		{
			id: 'fractions',
			title: 'Les fractions',
			progress: 30,
			subject: 'mathematics',
			href: '/student/studyguide'
		},
		{
			id: 'biology',
			title: 'Cell Biology',
			progress: 85,
			subject: 'biology',
			href: '/student/studyguide'
		},
		{
			id: 'chemistry',
			title: 'Organic Chemistry',
			progress: 40,
			subject: 'chemistry',
			href: '/student/studyguide'
		},
		{
			id: 'physics',
			title: 'Quantum Physics',
			progress: 55,
			subject: 'physics',
			href: '/student/studyguide'
		},
		{
			id: 'geography',
			title: 'World Geography',
			progress: 65,
			subject: 'geography',
			href: '/student/studyguide'
		}
	];

	// Sample support tickets/cards
	const supportItems = [
		{
			id: 'math-help',
			title: 'Math Homework Help',
			subject: 'mathematics',
			lastUpdated: '2 hours ago'
		},
		{
			id: 'physics-concepts',
			title: 'Physics Concepts',
			subject: 'physics',
			lastUpdated: '1 day ago'
		},
		{
			id: 'essay-review',
			title: 'Essay Review',
			subject: 'english',
			lastUpdated: '3 days ago'
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
	
	// Handle clicking on a support card - redirect to study guide
	function handleSupportCardClick(supportId: string) {
		// Navigate to study guide with the support ID as a parameter
		goto('/student/studyguide');
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

	<!-- Courses Section -->
	<div class="flex flex-col gap-6">
		<h2 class="text-xl font-bold text-gray-800 dark:text-white">{$i18n.t('My Courses')}</h2>
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
					{$i18n.t('Page')} {currentPage + 1} {$i18n.t('of')} {totalPages}
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
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 px-4">
		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-full max-w-md mx-auto overflow-hidden"
		>
			<!-- Header -->
			<div class="bg-blue-500 dark:bg-blue-600 text-white p-4 flex justify-between items-center">
				<h2 class="text-lg font-bold">{$i18n.t('Join a Course')}</h2>
				<button
					class="text-white hover:text-gray-300 transition-colors"
					on:click={toggleJoinCoursePopup}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-6 w-6"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>

			<!-- Content -->
			<div class="p-6">
				<p class="text-gray-700 dark:text-gray-300 mb-4">
					{$i18n.t('Enter the course code provided by your teacher to join the course.')}
				</p>
				<div class="mb-4">
					<label
						for="course-code"
						class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
					>
						{$i18n.t('Course Code')}
					</label>
					<input
						type="text"
						id="course-code"
						bind:value={courseCode}
						class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-100"
						placeholder={$i18n.t('Enter code')}
					/>
				</div>
				<div class="flex justify-end">
					<button
						class="bg-blue-500 hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700 text-white py-2 px-4 rounded-md transition-colors"
						on:click={handleJoinCourse}
					>
						{$i18n.t('Join')}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- Support Modal -->
{#if showSupportPopup}
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 px-4">
		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-full max-w-md mx-auto overflow-hidden"
		>
			<!-- Header -->
			<div class="bg-[#004AAD] text-white p-4 flex justify-between items-center">
				<h2 class="text-lg font-bold">{$i18n.t('Create Personalized Support')}</h2>
				<button
					class="text-white hover:text-gray-300 transition-colors"
					on:click={toggleSupportPopup}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-6 w-6"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>

			<!-- Content -->
			<div class="p-6 pt-8">
				<p class="text-center text-gray-700 dark:text-gray-300 mb-6">
					{$i18n.t('Get AI-powered learning support tailored to your needs.')}
				</p>

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
	</div>
{/if}
