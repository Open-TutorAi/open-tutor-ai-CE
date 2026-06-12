<script lang="ts">
	import { getContext, onMount, tick } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { toast } from 'svelte-sonner';
	import Modal from '../../common/Modal.svelte';

	import { derived } from 'svelte/store';
	const i18n: any = getContext('i18n');
	const _ = derived(i18n, ($i18n: any) => (key: string, options?: any) => $i18n.t(key, options));

	export let show = false;
	export let studentId = '';
	export let studentName = '';

	let courses: any[] = [];
	let isLoading = false;
	let isSaving = false;

	// Track which course IDs are checked (to be hidden)
	let hiddenCourseIds: string[] = [];

	$: if (show && studentId) {
		fetchStudentCourses();
	}

	async function fetchStudentCourses() {
		isLoading = true;
		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch(`/api/v1/teacher/students/${studentId}/courses`, {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				courses = await res.json();
				// Populate hidden courses
				hiddenCourseIds = courses.filter((c: any) => c.is_hidden).map((c: any) => c.course_id);
			} else {
				const err = await res.json();
				toast.error(err.detail || 'Failed to fetch student courses.');
			}
		} catch (e) {
			console.error('Error fetching student courses:', e);
			toast.error('An error occurred while fetching courses.');
		} finally {
			isLoading = false;
		}
	}

	function toggleCourseVisibility(courseId: string) {
		if (hiddenCourseIds.includes(courseId)) {
			hiddenCourseIds = hiddenCourseIds.filter((id) => id !== courseId);
		} else {
			hiddenCourseIds = [...hiddenCourseIds, courseId];
		}
	}

	async function handleSave() {
		isSaving = true;
		try {
			const token = localStorage.getItem('token') ?? '';
			const res = await fetch('/api/v1/teacher/students/hide-courses', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`
				},
				body: JSON.stringify({
					student_id: studentId,
					hidden_course_ids: hiddenCourseIds
				})
			});

			if (res.ok) {
				toast.success('Course visibility updated successfully!');
				show = false;
			} else {
				const err = await res.json();
				toast.error(err.detail || 'Failed to save visibility changes.');
			}
		} catch (e) {
			console.error('Error saving visibility changes:', e);
			toast.error('An error occurred while saving.');
		} finally {
			isSaving = false;
		}
	}
</script>

<Modal
	bind:show
	size="md"
	className="bg-white dark:bg-[#111827] rounded-[28px] overflow-hidden border border-slate-100 dark:border-slate-800 shadow-2xl"
>
	<div class="p-6 space-y-6">
		<!-- Header -->
		<div class="flex justify-between items-start">
			<div>
				<h2
					class="text-xl font-extrabold text-slate-800 dark:text-slate-50 flex items-center gap-2"
				>
					<span class="text-blue-500 text-2xl">👁️‍🗨️</span>
					{$i18n.t('Manage Lesson Visibility')}
				</h2>
				<p class="text-slate-500 dark:text-slate-400 text-sm mt-1">
					{$i18n.t('Select which courses should be hidden from')}
					<span class="font-bold text-blue-600 dark:text-indigo-400">{studentName}</span>.
				</p>
			</div>
			<button
				class="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
				on:click={() => (show = false)}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
						clip-rule="evenodd"
					/>
				</svg>
			</button>
		</div>

		<!-- Body list -->
		{#if isLoading}
			<div class="flex flex-col items-center justify-center py-12 space-y-4">
				<div
					class="animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"
				></div>
				<span class="text-xs font-bold text-slate-400 dark:text-slate-500"
					>{$i18n.t('Loading enrolled courses...')}</span
				>
			</div>
		{:else if courses.length === 0}
			<div class="flex flex-col items-center justify-center py-10 text-center space-y-3">
				<span class="text-3xl">📭</span>
				<div class="text-sm font-extrabold text-slate-700 dark:text-slate-300">
					{$i18n.t('No Enrolled Courses')}
				</div>
				<p class="text-xs text-slate-400 dark:text-slate-500 max-w-xs">
					{$i18n.t('This student is not currently enrolled in any of your courses.')}
				</p>
			</div>
		{:else}
			<div class="max-h-60 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800 pr-1">
				{#each courses as course}
					{@const isHidden = hiddenCourseIds.includes(course.course_id)}
					<div
						class="flex items-center justify-between py-3.5 px-3 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer"
						on:click={() => toggleCourseVisibility(course.course_id)}
					>
						<div class="flex items-center gap-3">
							<div
								class="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-extrabold transition-all duration-300
								{isHidden
									? 'bg-red-50 dark:bg-red-500/10 text-red-500 border border-red-200 dark:border-red-500/20'
									: 'bg-green-50 dark:bg-green-500/10 text-green-500 border border-green-200 dark:border-green-500/20'}"
							>
								{isHidden ? '🚫' : '👁️'}
							</div>
							<span class="text-sm font-bold text-slate-700 dark:text-slate-200 line-clamp-1">
								{course.title}
							</span>
						</div>

						<div class="flex items-center gap-3" on:click|stopPropagation>
							<span
								class="text-[10px] font-black uppercase tracking-wider
								{isHidden ? 'text-red-500 dark:text-red-400' : 'text-slate-400 dark:text-slate-500'}"
							>
								{isHidden ? $i18n.t('Hidden') : $i18n.t('Visible')}
							</span>

							<!-- Premium Custom Toggle Checkbox -->
							<label class="relative inline-flex items-center cursor-pointer">
								<input
									type="checkbox"
									class="sr-only peer"
									checked={isHidden}
									on:change={() => toggleCourseVisibility(course.course_id)}
								/>
								<div
									class="w-10 h-6 bg-slate-200 dark:bg-slate-700 rounded-full peer peer-focus:ring-2 peer-focus:ring-blue-500/20
									peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-slate-300
									after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:after:border-gray-600
									peer-checked:bg-red-500 dark:peer-checked:bg-red-600 transition-colors"
								></div>
							</label>
						</div>
					</div>
				{/each}
			</div>
		{/if}

		<!-- Action Footer -->
		<div class="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
			<button
				type="button"
				class="px-5 py-2.5 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 font-bold text-sm rounded-xl transition-all"
				on:click={() => (show = false)}
				disabled={isSaving}
			>
				{$i18n.t('Cancel')}
			</button>
			<button
				type="button"
				class="px-5 py-2.5 bg-blue-600 dark:bg-indigo-600 hover:bg-blue-700 dark:hover:bg-indigo-700 text-white font-bold text-sm rounded-xl shadow-lg shadow-blue-500/25 dark:shadow-indigo-500/25 flex items-center gap-2 transition-all"
				on:click={handleSave}
				disabled={isLoading || isSaving}
			>
				{#if isSaving}
					<div
						class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"
					></div>
					{$i18n.t('Saving...')}
				{:else}
					{$i18n.t('Save Changes')}
				{/if}
			</button>
		</div>
	</div>
</Modal>
