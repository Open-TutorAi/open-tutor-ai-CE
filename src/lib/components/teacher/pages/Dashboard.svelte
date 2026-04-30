<script lang="ts">
<<<<<<< HEAD
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	import { browser } from '$app/environment';
	import { user } from '$lib/stores';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	function copyToClipboard(text: string) {
		if (browser) {
			navigator.clipboard.writeText(text);
			toast.success('Code copied to clipboard!');
		}
	}

	// --- 1. i18n Initialization ---
	const i18n = getContext<Writable<i18nType>>('i18n');

	// --- 2. Dark Mode Logic ---
	let isDarkMode = false;

	onMount(() => {
		if (browser) {
			isDarkMode =
				localStorage.theme === 'dark' ||
				(!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
			applyTheme();
		}
	});

	function toggleDarkMode() {
		isDarkMode = !isDarkMode;
		applyTheme();
	}

	function applyTheme() {
		if (isDarkMode) {
			document.documentElement.classList.add('dark');
			localStorage.theme = 'dark';
		} else {
			document.documentElement.classList.remove('dark');
			localStorage.theme = 'light';
		}
	}

	// --- 3. Navigation & Stats ---
	function handleCreateCourse() {
		goto('/teacher/classrooms');
	}

	let stats = [
		{ label: 'Total courses', value: '4', trend: '+1 this month' },
		{ label: 'Enrolled students', value: '120', trend: '+12% vs last week' }
	];

	// --- 4. Data (Reactive) ---
	let courses = [
		{ id: 1, title: 'STUDY PROJECT', code: 'PER-402', students: 34, time: '2 hours' },
		{ id: 2, title: 'DevOps Technologies', code: 'D-Ops-101', students: 42, time: 'yesterday' },
		{ id: 3, title: 'Advanced Full stack', code: 'Ful-220', students: 28, time: '3 days' },
		{ id: 4, title: 'NoSQL databases', code: 'BaSE-305', students: 16, time: '1 week' }
	];

	let openMenuId: number | null = null;

	// --- 5. Logic Functions ---
	function toggleMenu(id: number) {
		openMenuId = openMenuId === id ? null : id;
	}

	function deleteCourse(id: number) {
		if (confirm($i18n.t('Are you sure you want to delete this course?'))) {
			courses = courses.filter((c) => c.id !== id);
			openMenuId = null;
			toast.success($i18n.t('Course deleted successfully!'));
		}
	}

	function renameCourse(id: number) {
		const course = courses.find((c) => c.id === id);
		const newTitle = prompt($i18n.t('Modify course title:'), course?.title);

		if (newTitle && newTitle.trim() !== '') {
			courses = courses.map((c) => (c.id === id ? { ...c, title: newTitle.toUpperCase() } : c));
			toast.success($i18n.t('Course renamed!'));
		}
		openMenuId = null;
=======
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	const i18n = getContext('i18n');

	// Mock data for UI testing
	let courses = [
		{ id: 1, title: 'PROJET D\'ETUDE', modified: '2 heures', code: 'PER-402', students: 34 },
		{ id: 2, title: 'Technologies DevOps', modified: 'hier', code: 'D-Ops-101', students: 42 },
		{ id: 3, title: 'Full stack avancé', modified: '3 jours', code: 'Ful-220', students: 28 },
		{ id: 4, title: 'bases de données NoSQL', modified: '1 semaine', code: 'BaSE-305', students: 16 }
	];

	function copyToClipboard(text: string) {
		navigator.clipboard.writeText(text);
		// You can add a toast here
>>>>>>> 4f8e763b8ec48fe19c4ef0f70a0b4f2c1b7b4f11
	}
</script>

<svelte:window on:click={() => (openMenuId = null)} />

<div
	class="min-h-screen bg-[#f8fafc] dark:bg-[#030712] p-8 font-sans transition-colors duration-500"
>
	<div class="flex flex-wrap justify-between items-center mb-10 gap-4">
		<div>
			<h1
				class="text-3xl font-bold text-[#1E293B] dark:text-slate-50 transition-colors tracking-tight"
			>
				{$i18n.t('Hello')}, Prof. {$user?.name || 'Youssef ES-SAADY'}
			</h1>
			<p class="text-slate-500 dark:text-slate-400 mt-1 text-lg transition-colors">
				{$i18n.t("Here's what's happening in your classes today")}
			</p>
		</div>

		<button
			on:click={handleCreateCourse}
			class="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-3.5 rounded-full font-bold flex items-center gap-2 shadow-lg shadow-indigo-500/20 transition-all active:scale-95"
		>
			<span class="text-2xl leading-none">+</span>
			{$i18n.t('Create a new course')}
		</button>
	</div>

	<div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
		{#each stats as stat}
			<div
				class="bg-white dark:bg-[#111827] p-8 rounded-[32px] border border-slate-100 dark:border-slate-800 shadow-sm flex flex-col items-center justify-center text-center transition-all hover:shadow-md"
			>
				<span
					class="text-slate-400 dark:text-slate-500 font-black uppercase tracking-[0.2em] text-[10px] mb-4"
				>
					{$i18n.t(stat.label)}
				</span>
				<div class="flex items-baseline gap-3">
					<span class="text-5xl font-black text-[#1E293B] dark:text-white transition-colors"
						>{stat.value}</span
					>
					<span
						class="text-green-500 font-bold text-sm flex items-center gap-1 bg-green-50 dark:bg-green-500/10 px-2 py-1 rounded-lg"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-4 w-4"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="3"
								d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
							/>
						</svg>
						{$i18n.t(stat.trend)}
					</span>
				</div>
			</div>
		{/each}
	</div>

	<div class="flex justify-between items-center mb-6">
		<h2
			class="text-xl font-extrabold text-[#1E293B] dark:text-slate-100 flex items-center gap-2 transition-colors tracking-tight"
		>
			<span class="text-indigo-500 dark:text-indigo-400">🕒</span>
			{$i18n.t('Recent Courses')}
		</h2>
		<button
			class="text-sm font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-200 transition-colors"
		>
			{$i18n.t('View all')}
		</button>
	</div>

	<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
		{#each courses as course (course.id)}
			<div
				class="bg-white dark:bg-[#111827] p-6 rounded-[28px] border border-slate-100 dark:border-slate-800 shadow-sm relative group transition-all hover:border-indigo-500/50"
			>
				<div class="flex justify-between items-start">
					<div>
						<h3
							class="font-bold text-slate-800 dark:text-slate-100 uppercase transition-colors tracking-tight text-sm"
						>
							{$i18n.t(course.title)}
						</h3>
						<p class="text-[11px] text-slate-400 dark:text-slate-500 transition-colors mt-1">
							{$i18n.t('Modified')}
							{$i18n.t(course.time)}
							{$i18n.t('ago')}
						</p>
					</div>

					<div class="relative">
						<button
							on:click|stopPropagation={() => toggleMenu(course.id)}
							class="p-1 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-full text-slate-300 dark:text-slate-600 hover:text-slate-600 dark:hover:text-slate-300 transition-colors font-bold text-xl"
						>
							⋮
						</button>

						{#if openMenuId === course.id}
							<div
								class="absolute right-0 mt-2 w-52 bg-white dark:bg-[#1e293b] border border-slate-100 dark:border-slate-800 shadow-xl rounded-2xl z-50 overflow-hidden py-1 text-left ring-1 ring-black/5 dark:ring-white/5"
							>
								<button
									on:click={() => renameCourse(course.id)}
									class="w-full text-left px-4 py-2.5 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/80 flex items-center gap-3 transition-colors"
								>
									✏️ <span class="font-medium">{$i18n.t('Modify title')}</span>
								</button>

								<div class="border-t border-slate-50 dark:border-slate-800 my-1"></div>

								<button
									on:click={() => deleteCourse(course.id)}
									class="w-full text-left px-4 py-2.5 text-sm text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-3 transition-colors"
								>
									🗑️ <span class="font-medium">{$i18n.t('Delete course')}</span>
								</button>
							</div>
						{/if}
					</div>
				</div>

				<div class="mt-6 flex justify-between items-center">
					<div
						class="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs transition-colors"
					>
						<span class="text-sm">👥</span>
						<span class="font-bold">{course.students} {$i18n.t('Students')}</span>
					</div>

					<button
						on:click={() => goto('/teacher/reports')}
						class="px-7 py-2.5 bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-200 rounded-full text-xs font-black hover:bg-indigo-600 dark:hover:bg-indigo-600 hover:text-white transition-all active:scale-95 shadow-sm"
					>
						{$i18n.t('Manage')}
					</button>
				</div>
			</div>
		{/each}
	</div>
</div>
