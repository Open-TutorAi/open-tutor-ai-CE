<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getClassrooms, type Classroom } from '$lib/apis/classrooms';
	import { getAssignments, type Assignment } from '$lib/apis/assignments';

	const i18n = getContext('i18n');

	let classrooms: Classroom[] = [];
	let assignments: Assignment[] = [];
	let loading = true;

	onMount(async () => {
		try {
			[classrooms, assignments] = await Promise.all([
				getClassrooms(localStorage.token).catch(() => []),
				getAssignments(localStorage.token).catch(() => []),
			]);
		} finally { loading = false; }
	});

	function assignmentCount(classroomId: string) {
		return assignments.filter(a => a.classroom_id === classroomId).length;
	}

	function pendingCount(classroomId: string) {
		return assignments.filter(a => a.classroom_id === classroomId && new Date(a.due_date) > new Date()).length;
	}

	const GRAD = [
		'from-indigo-500 to-violet-600',
		'from-emerald-500 to-teal-600',
		'from-rose-500 to-pink-600',
		'from-amber-500 to-orange-600',
	];
	function grad(i: number) { return GRAD[i % GRAD.length]; }
	function initials(name: string) { return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2); }
</script>

<div class="space-y-6">

	<!-- Header -->
	<div>
		<h1 class="text-2xl font-bold text-gray-800 dark:text-white">My Classrooms</h1>
		<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Your enrolled classes</p>
	</div>

	{#if loading}
		<div class="flex justify-center py-20">
			<div class="h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
		</div>

	{:else if classrooms.length === 0}
		<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-16 text-center">
			<div class="text-5xl mb-4">🏫</div>
			<p class="text-gray-600 dark:text-gray-300 font-semibold text-lg">Not enrolled in any class yet</p>
			<p class="text-sm text-gray-400 mt-2">Ask your teacher to enroll you using your email address.</p>
		</div>

	{:else}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each classrooms as classroom, i}
				<button on:click={() => goto('/student/assignments')}
					class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 text-left hover:shadow-md hover:border-indigo-200 dark:hover:border-indigo-700 transition-all duration-200 group">

					<!-- Top -->
					<div class="flex items-start justify-between mb-4">
						<div class="h-11 w-11 rounded-xl bg-gradient-to-br {grad(i)} flex items-center justify-center text-white font-bold text-sm shrink-0">
							{initials(classroom.name)}
						</div>
						{#if classroom.subject}
							<span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
								{classroom.subject}
							</span>
						{/if}
					</div>

					<!-- Name -->
					<h3 class="font-semibold text-gray-800 dark:text-white text-sm leading-snug group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors mb-1">
						{classroom.name}
					</h3>
					{#if classroom.description}
						<p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mb-3">{classroom.description}</p>
					{/if}

					<!-- Stats -->
					<div class="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-700 mt-3">
						<div class="flex items-center gap-3">
							<span class="text-xs text-gray-500">
								<span class="font-semibold text-gray-800 dark:text-white">{assignmentCount(classroom.id)}</span> assignments
							</span>
							{#if pendingCount(classroom.id) > 0}
								<span class="px-2 py-0.5 bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 text-xs font-semibold rounded-full">
									{pendingCount(classroom.id)} pending
								</span>
							{/if}
						</div>
						<svg class="h-4 w-4 text-gray-300 group-hover:text-indigo-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
						</svg>
					</div>
				</button>
			{/each}
		</div>
	{/if}
</div>
