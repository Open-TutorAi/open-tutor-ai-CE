<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getAssignments, getMySubmission, type Assignment, type Submission } from '$lib/apis/assignments';

	const i18n = getContext('i18n');

	type Tab = 'todo' | 'submitted' | 'graded';
	let activeTab: Tab = 'todo';
	let assignments: Assignment[] = [];
	let submissions: Map<string, Submission> = new Map();
	let loading = true;

	onMount(async () => {
		try {
			assignments = await getAssignments(localStorage.token).catch(() => []);
			const subs = await Promise.all(
				assignments.map(a => getMySubmission(localStorage.token, a.id).catch(() => null))
			);
			subs.forEach((s, i) => { if (s) submissions.set(assignments[i].id, s); });
			submissions = new Map(submissions);
		} finally { loading = false; }
	});

	function isPastDue(a: Assignment) { return new Date(a.due_date) < new Date(); }
	function getSub(a: Assignment): Submission | undefined { return submissions.get(a.id); }

	function daysUntil(d: string): string {
		const diff = Math.ceil((new Date(d).getTime() - Date.now()) / 86400000);
		if (diff < 0) return 'Overdue';
		if (diff === 0) return 'Due today';
		if (diff === 1) return 'Due tomorrow';
		return `Due in ${diff} days`;
	}

	function fmtDate(d: string) {
		return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
	}

	$: todo      = assignments.filter(a => !getSub(a));
	$: submitted = assignments.filter(a => { const s = getSub(a); return s && s.status !== 'returned'; });
	$: graded    = assignments.filter(a => getSub(a)?.status === 'returned');

	$: tabData = activeTab === 'todo' ? todo : activeTab === 'submitted' ? submitted : graded;
</script>

<div class="space-y-6">

	<!-- Header -->
	<div>
		<h1 class="text-2xl font-bold text-gray-800 dark:text-white">My Assignments</h1>
		<p class="text-sm text-gray-500 dark:text-gray-400">Track your work and deadlines</p>
	</div>

	<!-- Stats -->
	<div class="grid grid-cols-3 gap-4">
		<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 border-l-4 border-amber-400">
			<p class="text-2xl font-bold text-amber-500">{todo.length}</p>
			<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">To Do</p>
		</div>
		<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 border-l-4 border-indigo-400">
			<p class="text-2xl font-bold text-indigo-600">{submitted.length}</p>
			<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Submitted</p>
		</div>
		<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 border-l-4 border-green-400">
			<p class="text-2xl font-bold text-green-600">{graded.length}</p>
			<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Graded</p>
		</div>
	</div>

	<!-- Tabs + cards -->
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm overflow-hidden">
		<div class="border-b border-gray-100 dark:border-gray-700 flex">
			{#each [['todo','To Do'],['submitted','Submitted'],['graded','Graded']] as [id, label]}
				<button on:click={() => activeTab = id}
					class="px-5 py-4 text-sm font-medium border-b-2 transition
					{activeTab === id ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-200'}">
					{label}
				</button>
			{/each}
		</div>

		{#if loading}
			<div class="flex justify-center py-12">
				<div class="h-6 w-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
			</div>
		{:else if tabData.length === 0}
			<div class="py-16 text-center text-gray-400">
				<div class="text-4xl mb-3">
					{#if activeTab === 'todo'}✅{:else if activeTab === 'submitted'}📬{:else}🏆{/if}
				</div>
				<p class="font-medium text-gray-600 dark:text-gray-300">
					{activeTab === 'todo' ? 'All caught up!' : activeTab === 'submitted' ? 'No pending submissions' : 'No graded work yet'}
				</p>
			</div>
		{:else}
			<div class="p-4 space-y-3">
				{#each tabData as a}
					{@const sub = getSub(a)}
					{@const overdue = isPastDue(a) && !sub}
					<button on:click={() => goto(`/student/assignments/${a.id}`)}
						class="w-full flex items-center justify-between p-4 border rounded-xl transition text-left
						{overdue ? 'border-red-100 bg-red-50 dark:bg-red-900/10 dark:border-red-900/30 hover:shadow-sm' : 'border-gray-100 dark:border-gray-700 hover:shadow-sm dark:hover:bg-gray-700/20'}">
						<div class="flex items-center gap-3">
							<div class="h-10 w-10 rounded-xl flex items-center justify-center text-xl shrink-0
								{overdue ? 'bg-red-100 dark:bg-red-900/30' : 'bg-indigo-100 dark:bg-indigo-900/30'}">
								{overdue ? '⚠️' : activeTab === 'graded' ? '🏆' : '📝'}
							</div>
							<div class="min-w-0 text-left">
								<p class="font-semibold text-gray-800 dark:text-white">{a.title}</p>
								<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
									Due <span class="{overdue ? 'text-red-600 font-medium' : 'text-amber-600 font-medium'}">{fmtDate(a.due_date)}</span>
									{#if sub?.score != null} · <span class="text-green-600 font-semibold">{sub.score}/{a.max_score}</span>{/if}
								</p>
							</div>
						</div>
						<div class="flex items-center gap-2 shrink-0 ml-3">
							{#if overdue}
								<span class="px-2 py-1 bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 text-xs font-semibold rounded-full">Overdue</span>
							{:else if sub?.status === 'returned'}
								<span class="px-2 py-1 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs font-semibold rounded-full">Graded</span>
							{:else if sub}
								<span class="px-2 py-1 bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400 text-xs font-semibold rounded-full">Submitted</span>
							{:else}
								<span class="px-2 py-1 bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 text-xs font-semibold rounded-full">{daysUntil(a.due_date)}</span>
							{/if}
							<svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
						</div>
					</button>
				{/each}
			</div>
		{/if}
	</div>
</div>
