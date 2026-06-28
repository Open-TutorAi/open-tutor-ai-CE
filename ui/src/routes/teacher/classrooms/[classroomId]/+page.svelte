<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getClassroom, getClassroomStudents, enrollStudent, unenrollStudent, type Classroom } from '$lib/apis/classrooms';
	import { TUTOR_API_BASE_URL } from '$lib/constants';

	const i18n = getContext('i18n');

	$: classroomId = $page.params.classroomId;

	let classroom: Classroom | null = null;
	let students: { student_id: string; name: string; email: string | null; enrolled_at: string }[] = [];
	let loading = true;
	let searchQuery = '';

	let showEnrollModal = false;
	let enrollEmail = '';
	let foundStudent: { id: string; name: string; email: string } | null = null;
	let lookupError = '';
	let looking = false;
	let enrolling = false;

	onMount(async () => {
		try {
			[classroom, students] = await Promise.all([
				getClassroom(localStorage.token, classroomId),
				getClassroomStudents(localStorage.token, classroomId),
			]);
		} catch {
			toast.error('Classroom not found');
			goto('/teacher/classrooms');
		} finally { loading = false; }
	});

	function openEnrollModal() {
		enrollEmail = '';
		foundStudent = null;
		lookupError = '';
		showEnrollModal = true;
	}

	async function handleLookup() {
		if (!enrollEmail.trim()) return;
		looking = true;
		foundStudent = null;
		lookupError = '';
		try {
			const res = await fetch(
				`${TUTOR_API_BASE_URL}/users/lookup?email=${encodeURIComponent(enrollEmail.trim())}`,
				{ headers: { Authorization: `Bearer ${localStorage.token}` } }
			);
			if (!res.ok) { const d = await res.json(); lookupError = d?.detail ?? 'Not found'; return; }
			foundStudent = await res.json();
		} catch { lookupError = 'Search failed'; }
		finally { looking = false; }
	}

	async function handleEnroll() {
		if (!foundStudent) return;
		enrolling = true;
		try {
			const e = await enrollStudent(localStorage.token, classroomId, foundStudent.id);
			students = [...students, {
				student_id: e.student_id,
				name: foundStudent.name,
				email: foundStudent.email,
				enrolled_at: e.enrolled_at ?? new Date().toISOString()
			}];
			showEnrollModal = false;
			toast.success(`${foundStudent.name} enrolled`);
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to enroll student');
		} finally { enrolling = false; }
	}

	$: filtered = students.filter(s =>
		!searchQuery ||
		s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
		(s.email ?? '').toLowerCase().includes(searchQuery.toLowerCase())
	);

	function fmtDate(d: string) {
		return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
	}

	function avatarInitials(name: string) {
		return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) || '??';
	}
	async function handleUnenroll(student: { student_id: string; name: string }) {
		if (!confirm(`Remove ${student.name} from this classroom?`)) return;
		try {
			await unenrollStudent(localStorage.token, classroomId, student.student_id);
			students = students.filter(s => s.student_id !== student.student_id);
			toast.success(`${student.name} removed`);
		} catch (e: any) {
			toast.error(e?.message ?? 'Failed to remove student');
		}
	}

	function avatarColor(id: string) {
		const colors = ['bg-indigo-100 text-indigo-700','bg-emerald-100 text-emerald-700','bg-rose-100 text-rose-700','bg-amber-100 text-amber-700'];
		return colors[id.charCodeAt(0) % colors.length];
	}
</script>

<div class="space-y-5 max-w-4xl mx-auto">

	<!-- Back -->
	<button on:click={() => goto('/teacher/classrooms')}
		class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 transition font-medium">
		<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
		Back to Classrooms
	</button>

	{#if loading}
		<div class="flex justify-center py-20">
			<div class="h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
		</div>
	{:else if classroom}

	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
		<div class="flex items-start justify-between gap-4">
			<div>
				<p class="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-1">Classroom</p>
				<h1 class="text-xl font-bold text-gray-800 dark:text-white">{classroom.name}</h1>
				{#if classroom.subject}
					<span class="inline-block mt-2 px-2.5 py-0.5 bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 text-xs font-semibold rounded-full">{classroom.subject}</span>
				{/if}
				{#if classroom.description}
					<p class="mt-2 text-sm text-gray-500 dark:text-gray-400">{classroom.description}</p>
				{/if}
			</div>
			<div class="text-right shrink-0">
				<p class="text-2xl font-bold text-indigo-600">{students.length}</p>
				<p class="text-xs text-gray-500">Students</p>
			</div>
		</div>
	</div>

	<!-- Students section -->
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm overflow-hidden">
		<div class="border-b border-gray-100 dark:border-gray-700 px-5 py-4 flex items-center justify-between">
			<h2 class="font-bold text-gray-800 dark:text-white">Enrolled Students</h2>
			<div class="flex items-center gap-3">
				<div class="flex items-center gap-2 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-1.5">
					<svg class="h-3.5 w-3.5 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
					</svg>
					<input type="text" placeholder="Search by name…" bind:value={searchQuery}
						class="bg-transparent text-xs outline-none text-gray-700 dark:text-gray-200 placeholder-gray-400 w-32"/>
				</div>
				<button on:click={openEnrollModal}
					class="flex items-center gap-1.5 px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl transition">
					<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
					Enroll Student
				</button>
			</div>
		</div>

		{#if filtered.length === 0}
			<div class="py-16 text-center text-gray-400">
				<div class="text-3xl mb-3">👨‍🎓</div>
				<p class="font-medium text-gray-600 dark:text-gray-300">
					{searchQuery ? 'No matching students' : 'No students enrolled yet'}
				</p>
				{#if !searchQuery}
					<button on:click={openEnrollModal} class="mt-2 text-sm text-indigo-600 hover:underline">Add your first student</button>
				{/if}
			</div>
		{:else}
			<div class="divide-y divide-gray-100 dark:divide-gray-700">
				{#each filtered as s}
					<div class="flex items-center gap-4 px-5 py-4">
						<div class="h-9 w-9 rounded-full {avatarColor(s.student_id)} flex items-center justify-center text-xs font-bold shrink-0">
							{avatarInitials(s.name)}
						</div>
						<div class="flex-1 min-w-0">
							<p class="text-sm font-semibold text-gray-800 dark:text-white truncate">{s.name}</p>
							{#if s.email}
								<p class="text-xs text-gray-400 truncate">{s.email}</p>
							{/if}
							<p class="text-xs text-gray-400">Enrolled {fmtDate(s.enrolled_at)}</p>
						</div>
						<button on:click={() => handleUnenroll(s)}
							class="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition" title="Remove student">
							<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7a4 4 0 11-8 0 4 4 0 018 0zM9 14a6 6 0 00-6 6v1h12v-1a6 6 0 00-6-6zM21 12h-6"/></svg>
						</button>
					</div>
				{/each}
			</div>
		{/if}
	</div>
	{/if}
</div>

<!-- Enroll modal -->
{#if showEnrollModal}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
	on:click|self={() => (showEnrollModal = false)} role="dialog" aria-modal="true">
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-sm p-6">
		<div class="flex items-center justify-between mb-4">
			<h3 class="font-bold text-gray-800 dark:text-white">Enroll a Student</h3>
			<button on:click={() => (showEnrollModal = false)} class="text-gray-400 hover:text-gray-600">
				<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
			</button>
		</div>

		<div class="space-y-4">
			<!-- Email search -->
			<div>
				<label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Student Email <span class="text-red-500">*</span></label>
				<div class="flex gap-2">
					<input bind:value={enrollEmail} placeholder="student@school.fr" type="email"
						on:keydown={(e) => e.key === 'Enter' && handleLookup()}
						class="flex-1 border border-gray-200 dark:border-gray-700 rounded-xl px-3 py-2.5 text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"/>
					<button type="button" on:click={handleLookup} disabled={looking || !enrollEmail.trim()}
						class="px-3 py-2.5 bg-indigo-100 hover:bg-indigo-200 disabled:opacity-50 text-indigo-700 text-sm font-semibold rounded-xl transition">
						{#if looking}
							<span class="h-4 w-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin inline-block"></span>
						{:else}
							Search
						{/if}
					</button>
				</div>
				{#if lookupError}
					<p class="mt-1.5 text-xs text-red-500">{lookupError}</p>
				{/if}
			</div>

			<!-- Found student preview -->
			{#if foundStudent}
				<div class="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
					<div class="h-9 w-9 rounded-full bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 flex items-center justify-center text-sm font-bold shrink-0">
						{foundStudent.name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)}
					</div>
					<div class="min-w-0">
						<p class="text-sm font-semibold text-gray-800 dark:text-white">{foundStudent.name}</p>
						<p class="text-xs text-gray-500 dark:text-gray-400 truncate">{foundStudent.email}</p>
					</div>
					<svg class="h-5 w-5 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
					</svg>
				</div>
			{/if}

			<div class="flex gap-3">
				<button type="button" on:click={() => (showEnrollModal = false)}
					class="flex-1 py-2.5 text-sm font-medium text-gray-600 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
					Cancel
				</button>
				<button type="button" on:click={handleEnroll} disabled={enrolling || !foundStudent}
					class="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold rounded-xl transition flex items-center justify-center gap-2">
					{#if enrolling}
						<span class="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
						Enrolling…
					{:else}
						Enroll
					{/if}
				</button>
			</div>
		</div>
	</div>
</div>
{/if}
