<script lang="ts">
	import { onMount, onDestroy, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import {
		getClassroom,
		getRoster,
		getInvitations,
		getClassProgress,
		removeStudent,
		deleteClassroom,
		getMonitor,
		setMonitor,
		setClassMonitor,
		getClassPresence,
		getAwayLog,
		clearAwayLog,
		type Classroom,
		type RosterEntry,
		type Invitation,
		type ClassProgressRow,
		type AwayEvent,
		type StudentPresence
	} from '$lib/apis/classrooms';
	import { getAssignments, type AssignmentSummary } from '$lib/apis/assignments';
	import {
		getClassMaterials,
		downloadMaterial,
		deleteMaterial,
		type ClassMaterial
	} from '$lib/apis/resources';
	import {
		activityStatusStyle as statusStyle,
		activityStatusLabel as statusLabel
	} from '$lib/utils/status';
	import { fmtDate, fmtSize, fmtDateTime as fmtTime } from '$lib/utils/format';
	import { monitorAway } from '$lib/stores';
	import AddStudentModal from '$lib/components/teacher/elements/AddStudentModal.svelte';
	import InviteModal from '$lib/components/teacher/elements/InviteModal.svelte';
	import CreateAssignmentModal from '$lib/components/teacher/elements/CreateAssignmentModal.svelte';
	import UploadMaterialModal from '$lib/components/teacher/elements/UploadMaterialModal.svelte';

	const i18n: any = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';
	const classId = $page.params.id;

	let klass: Classroom | null = null;
	let roster: RosterEntry[] = [];
	let invitations: Invitation[] = [];
	let progress: ClassProgressRow[] = [];
	let assignments: AssignmentSummary[] = [];
	let materials: ClassMaterial[] = [];
	let monitorMap: Record<string, boolean> = {};
	let monitorLoaded = false;
	let monitorBusy = false;
	let monitorError = '';
	// Last lock action verb ('' | 'Unlocked' | 'Locked'); the "X/Y online now" note is
	// derived reactively from it + live presence counts, so opening the dropdown (which
	// refreshes presence) keeps the note's count in sync.
	let lockVerb = '';
	let presence: StudentPresence[] = [];
	let presenceOnline = 0;
	let presenceTotal = 0;
	let showPresence = false;

	let tab: 'Roster' | 'Progress' | 'Assignments' | 'Resources' | 'Invitations' | 'Control' =
		'Roster';
	let loading = true;
	let showAdd = false;
	let showInvite = false;
	let showCreateAssignment = false;
	let showUpload = false;
	let showDelete = false;
	let deleting = false;

	const tabs = [
		'Roster',
		'Progress',
		'Assignments',
		'Resources',
		'Invitations',
		'Control'
	] as const;

	async function load() {
		try {
			[klass, roster, invitations, progress, assignments, materials] = await Promise.all([
				getClassroom(token(), classId),
				getRoster(token(), classId),
				getInvitations(token(), classId),
				getClassProgress(token(), classId),
				getAssignments(token(), classId),
				getClassMaterials(token(), classId)
			]);
		} catch (err) {
			klass = null;
		} finally {
			loading = false;
		}
	}

	async function onRemove(studentId: string) {
		try {
			await removeStudent(token(), classId, studentId);
			roster = roster.filter((s) => s.student_id !== studentId);
		} catch (err) {
			/* keep row */
		}
	}
	function onEnrolled(e: CustomEvent<RosterEntry>) {
		roster = [...roster, e.detail];
		showAdd = false;
	}
	async function onDeleteClass() {
		deleting = true;
		try {
			await deleteClassroom(token(), classId);
			goto('/teacher/classes');
		} catch (err) {
			deleting = false;
			showDelete = false;
		}
	}
	async function refreshInvites() {
		invitations = await getInvitations(token(), classId);
	}
	async function onAssignmentCreated(e: CustomEvent<AssignmentSummary>) {
		assignments = [e.detail, ...assignments];
		showCreateAssignment = false;
	}
	function onMaterialUploaded(e: CustomEvent<ClassMaterial>) {
		materials = [e.detail, ...materials];
		showUpload = false;
	}
	async function downloadM(m: ClassMaterial) {
		try {
			const blob = await downloadMaterial(token(), classId, m.id);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = m.filename ?? m.title;
			a.click();
			URL.revokeObjectURL(url);
		} catch (err) {
			/* ignore */
		}
	}
	async function removeMaterial(m: ClassMaterial) {
		try {
			await deleteMaterial(token(), classId, m.id);
			materials = materials.filter((x) => x.id !== m.id);
		} catch (err) {
			/* keep */
		}
	}

	// ── E6 monitor control ──────────────────────────────────────────────────
	async function loadMonitors() {
		const entries = await Promise.all(
			roster.map(async (s) => {
				try {
					const m = await getMonitor(token(), classId, s.student_id);
					return [s.student_id, m.enabled] as const;
				} catch {
					return [s.student_id, true] as const;
				}
			})
		);
		monitorMap = Object.fromEntries(entries);
		monitorLoaded = true;
	}
	// Lazy-load monitor state the first time the Control tab is opened.
	$: if (tab === 'Control' && !monitorLoaded && roster.length) loadMonitors();

	// Durable tab-away history (server-authoritative). Loaded when the Control tab
	// opens and reloaded whenever a live away/return event lands for this class, so
	// the teacher sees history they missed plus new events.
	let awayLog: AwayEvent[] = [];
	let awaySig = '__init__';
	async function loadAwayLog() {
		try {
			awayLog = await getAwayLog(token(), classId);
		} catch {
			/* keep last-loaded on transient failure */
		}
	}
	let clearingActivity = false;
	async function clearActivity() {
		clearingActivity = true;
		try {
			await clearAwayLog(token(), classId);
			awayLog = [];
		} catch {
			/* ignore */
		} finally {
			clearingActivity = false;
		}
	}
	$: if (tab === 'Control') {
		const sig = Object.entries($monitorAway)
			.filter(([, v]) => v.classroom_id === classId)
			.map(([k, v]) => `${k}:${v.at}:${v.away}`)
			.join('|');
		if (sig !== awaySig) {
			awaySig = sig;
			loadAwayLog();
		}
	}

	// Clear stale tab-away state when a student's lock changes: unlocking drops it
	// entirely; a fresh lock resets to "present" until the student reports otherwise
	// (they only emit on a transition, so a present student would never overwrite a
	// leftover `away:true` from a previous lock session).
	function resetAway(sid: string, enabled: boolean) {
		monitorAway.update((m) => {
			const next = { ...m };
			if (enabled) delete next[sid];
			else next[sid] = { away: false, classroom_id: classId, at: Date.now() };
			return next;
		});
	}

	// Live presence for the "X/Y online now" indicator + its dropdown. Refreshed on a
	// timer while the Control tab is open (plus after every lock action), so the teacher
	// sees who goes online/offline without reloading the page.
	let presenceLoaded = false;
	// Resolve a student's display name from the already-loaded roster (the presence
	// endpoint returns ids only, to stay cheap on a short poll interval).
	const nameFor = (sid: string): string => {
		const s = roster.find((r) => r.student_id === sid);
		return s?.name ?? s?.email ?? '—';
	};
	async function refreshPresence() {
		try {
			const p = await getClassPresence(token(), classId);
			presence = p.students;
			presenceOnline = p.online;
			presenceTotal = p.total;
			presenceLoaded = true;
		} catch {
			/* keep last-known on transient failure */
		}
	}
	// Always-on "X/Y online now"; after a lock action a transient "Unlocked · " / "Locked · "
	// verb is prefixed. Derived, so the count tracks live presence updates.
	$: presenceLabel = `${presenceOnline}/${presenceTotal} ${$i18n.t('online now')}`;
	$: monitorNote = lockVerb ? `${$i18n.t(lockVerb)} · ${presenceLabel}` : presenceLabel;

	// ── live presence polling ────────────────────────────────────────────────
	const PRESENCE_POLL_MS = 3000;
	let presenceTimer: ReturnType<typeof setInterval> | null = null;
	function startPresencePolling() {
		if (presenceTimer) return;
		// Seed from the roster (all offline) so the indicator/dropdown show sensible
		// totals before the first network response lands.
		if (!presenceLoaded) {
			presence = roster.map((s) => ({ student_id: s.student_id, online: false }));
			presenceTotal = roster.length;
		}
		refreshPresence();
		presenceTimer = setInterval(refreshPresence, PRESENCE_POLL_MS);
	}
	function stopPresencePolling() {
		if (presenceTimer) {
			clearInterval(presenceTimer);
			presenceTimer = null;
		}
	}
	// Poll only while the Control tab is visible; stop on leave / unmount to avoid waste.
	$: if (tab === 'Control' && roster.length) startPresencePolling();
	$: if (tab !== 'Control') stopPresencePolling();
	onDestroy(stopPresencePolling);

	async function togglePresence() {
		showPresence = !showPresence;
		if (showPresence) await refreshPresence();
	}

	async function toggleMonitor(sid: string, enabled: boolean) {
		monitorMap = { ...monitorMap, [sid]: enabled }; // optimistic
		resetAway(sid, enabled);
		try {
			const res = await setMonitor(token(), classId, sid, enabled);
			monitorMap = { ...monitorMap, [sid]: res.enabled };
			// A single-student lock surfaces the same class-wide "X/Y online now" note.
			monitorError = '';
			lockVerb = enabled ? 'Unlocked' : 'Locked';
			await refreshPresence();
		} catch {
			monitorMap = { ...monitorMap, [sid]: !enabled }; // revert
		}
	}
	async function setAll(enabled: boolean) {
		monitorBusy = true;
		monitorError = '';
		// Reset before the round-trip so a fast student away-report (arriving after the
		// server fans out monitor:set) isn't clobbered by a late reset.
		monitorMap = Object.fromEntries(roster.map((s) => [s.student_id, enabled])); // optimistic
		roster.forEach((s) => resetAway(s.student_id, enabled));
		try {
			await setClassMonitor(token(), classId, enabled);
			lockVerb = enabled ? 'Unlocked' : 'Locked';
			await refreshPresence();
		} catch {
			lockVerb = '';
			monitorError = $i18n.t('Could not update the class');
		} finally {
			monitorBusy = false;
		}
	}

	onMount(load);
</script>

<div class="flex flex-col gap-6">
	<button
		class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 self-start"
		on:click={() => goto('/teacher/classes')}
	>
		‹ {$i18n.t('Classes')}
	</button>

	{#if loading}
		<div class="flex justify-center py-12">
			<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
		</div>
	{:else if !klass}
		<div class="rounded-2xl bg-red-50 dark:bg-red-900/20 p-4 text-red-600">
			{$i18n.t('Could not load this class')}
		</div>
	{:else}
		<div class="flex items-start justify-between gap-4">
			<div>
				<h1 class="text-2xl font-bold text-gray-800 dark:text-white">{klass.name}</h1>
				<p class="text-gray-500 dark:text-gray-400 mt-1">
					{klass.subject ?? ''}{klass.level ? ` · ${klass.level}` : ''} · {klass.student_count}
					{$i18n.t('students')}
				</p>
			</div>
			<div class="flex gap-2">
				<button
					class="px-3 py-2 rounded-full bg-blue-600 text-white text-sm hover:bg-blue-700"
					on:click={() => (showAdd = true)}>+ {$i18n.t('Add student')}</button
				>
				<button
					class="px-3 py-2 rounded-full border border-blue-400 text-blue-500 text-sm hover:bg-blue-50 dark:hover:bg-blue-900/20"
					on:click={() => (showInvite = true)}>✉ {$i18n.t('Invite')}</button
				>
				<button
					class="px-3 py-2 rounded-full border border-red-300 text-red-500 text-sm hover:bg-red-50 dark:hover:bg-red-900/20"
					on:click={() => (showDelete = true)}
					title={$i18n.t('Delete class')}
					aria-label={$i18n.t('Delete class')}>🗑</button
				>
			</div>
		</div>

		<div class="flex gap-6 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
			{#each tabs as t}
				<button
					class="pb-2 -mb-px border-b-2 text-sm whitespace-nowrap {tab === t
						? 'border-blue-500 text-blue-600 dark:text-blue-400 font-semibold'
						: 'border-transparent text-gray-500'}"
					on:click={() => (tab = t)}
				>
					{$i18n.t(t)}{#if t === 'Roster'}
						({roster.length}){:else if t === 'Invitations'}
						({invitations.length}){:else if t === 'Assignments'}
						({assignments.length}){:else if t === 'Resources'}
						({materials.length}){/if}
				</button>
			{/each}
		</div>

		{#if tab === 'Roster'}
			{#if roster.length === 0}
				<div
					class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
				>
					{$i18n.t('No students yet — add or invite one.')}
				</div>
			{:else}
				<div class="overflow-x-auto rounded-2xl bg-white dark:bg-gray-800 shadow-sm">
					<table class="w-full text-left text-sm">
						<thead
							class="text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700"
						>
							<tr
								><th class="px-5 py-3 font-medium">{$i18n.t('Name')}</th><th
									class="px-5 py-3 font-medium">{$i18n.t('Email')}</th
								><th class="px-5 py-3"></th></tr
							>
						</thead>
						<tbody>
							{#each roster as s (s.student_id)}
								<tr class="border-b border-gray-50 dark:border-gray-700/50">
									<td class="px-5 py-3 text-gray-800 dark:text-white">{s.name ?? '—'}</td>
									<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{s.email ?? '—'}</td>
									<td class="px-5 py-3 text-right"
										><button
											class="text-red-500 hover:text-red-600 text-xs"
											on:click={() => onRemove(s.student_id)}>{$i18n.t('Remove')}</button
										></td
									>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		{:else if tab === 'Invitations'}
			{#if invitations.length === 0}
				<div
					class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
				>
					{$i18n.t('No invitations yet.')}
				</div>
			{:else}
				<div class="overflow-x-auto rounded-2xl bg-white dark:bg-gray-800 shadow-sm">
					<table class="w-full text-left text-sm">
						<thead
							class="text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700"
						>
							<tr
								><th class="px-5 py-3 font-medium">{$i18n.t('Email')}</th><th
									class="px-5 py-3 font-medium">{$i18n.t('Role')}</th
								><th class="px-5 py-3 font-medium">{$i18n.t('Status')}</th></tr
							>
						</thead>
						<tbody>
							{#each invitations as inv (inv.id)}
								<tr class="border-b border-gray-50 dark:border-gray-700/50">
									<td class="px-5 py-3 text-gray-800 dark:text-white">{inv.email}</td>
									<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{inv.invitee_role}</td>
									<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{inv.status}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		{:else if tab === 'Progress'}
			{#if progress.length === 0}
				<div
					class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
				>
					{$i18n.t('No students yet — add or invite one.')}
				</div>
			{:else}
				<div class="overflow-x-auto rounded-2xl bg-white dark:bg-gray-800 shadow-sm">
					<table class="w-full text-left text-sm">
						<thead
							class="text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700"
						>
							<tr
								><th class="px-5 py-3 font-medium">{$i18n.t('Name')}</th><th
									class="px-5 py-3 font-medium">{$i18n.t('Status')}</th
								><th class="px-5 py-3 font-medium">{$i18n.t('Supports')}</th><th class="px-5 py-3"
								></th></tr
							>
						</thead>
						<tbody>
							{#each progress as p (p.student_id)}
								<tr class="border-b border-gray-50 dark:border-gray-700/50">
									<td class="px-5 py-3 text-gray-800 dark:text-white">{p.name ?? '—'}</td>
									<td class="px-5 py-3"
										><span class={`text-xs px-2 py-0.5 rounded-full ${statusStyle[p.status]}`}
											>{$i18n.t(statusLabel[p.status])}</span
										></td
									>
									<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{p.supports_total}</td>
									<td class="px-5 py-3 text-right"
										><button
											class="text-blue-600 dark:text-blue-400 text-xs hover:underline"
											on:click={() => goto(`/teacher/classes/${classId}/students/${p.student_id}`)}
											>{$i18n.t('View')}</button
										></td
									>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		{:else if tab === 'Assignments'}
			<div class="flex justify-end">
				<button
					class="px-3 py-2 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm hover:opacity-90"
					on:click={() => (showCreateAssignment = true)}>+ {$i18n.t('New assignment')}</button
				>
			</div>
			{#if assignments.length === 0}
				<div
					class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
				>
					{$i18n.t('No assignments yet — create one.')}
				</div>
			{:else}
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
					{#each assignments as a (a.id)}
						<button
							class="text-left rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5 hover:shadow-md transition"
							on:click={() => goto(`/teacher/classes/${classId}/assignments/${a.id}`)}
						>
							<div class="flex items-start justify-between gap-2">
								<h3 class="font-semibold text-gray-800 dark:text-white">{a.title}</h3>
								<span class="text-xs text-gray-400 whitespace-nowrap"
									>{$i18n.t('Due')} {fmtDate(a.due_date)}</span
								>
							</div>
							{#if a.instructions}<p
									class="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2"
								>
									{a.instructions}
								</p>{/if}
							<div class="flex gap-4 mt-3 text-xs text-gray-500 dark:text-gray-400">
								<span>📥 {a.submitted_count}/{a.student_count} {$i18n.t('submitted')}</span>
								<span>✅ {a.graded_count} {$i18n.t('graded')}</span>
							</div>
						</button>
					{/each}
				</div>
			{/if}
		{:else if tab === 'Resources'}
			<div class="flex justify-end">
				<button
					class="px-3 py-2 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm hover:opacity-90"
					on:click={() => (showUpload = true)}>+ {$i18n.t('Upload material')}</button
				>
			</div>
			{#if materials.length === 0}
				<div
					class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
				>
					{$i18n.t('No materials yet — upload one.')}
				</div>
			{:else}
				<div class="overflow-x-auto rounded-2xl bg-white dark:bg-gray-800 shadow-sm">
					<table class="w-full text-left text-sm">
						<thead
							class="text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700"
						>
							<tr
								><th class="px-5 py-3 font-medium">{$i18n.t('Name')}</th><th
									class="px-5 py-3 font-medium">{$i18n.t('Type')}</th
								><th class="px-5 py-3 font-medium">{$i18n.t('Size')}</th><th class="px-5 py-3"
								></th></tr
							>
						</thead>
						<tbody>
							{#each materials as m (m.id)}
								<tr class="border-b border-gray-50 dark:border-gray-700/50">
									<td class="px-5 py-3 text-gray-800 dark:text-white">{m.title}</td>
									<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{m.content_type ?? '—'}</td
									>
									<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{fmtSize(m.size)}</td>
									<td class="px-5 py-3 text-right">
										<button
											class="text-blue-600 dark:text-blue-400 text-xs hover:underline mr-3"
											on:click={() => downloadM(m)}>{$i18n.t('Download')}</button
										>
										<button
											class="text-red-500 hover:text-red-600 text-xs"
											on:click={() => removeMaterial(m)}>{$i18n.t('Remove')}</button
										>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		{:else if tab === 'Control'}
			<div
				class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
			>
				<div>
					<div class="font-semibold text-gray-800 dark:text-white">{$i18n.t('Screen control')}</div>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						{$i18n.t(
							'Blank or restore a student’s TutorAI screen. Online students update instantly; others apply on reconnect.'
						)}
					</p>
					{#if monitorError}
						<p class="text-xs text-red-600 dark:text-red-400 mt-1">{monitorError}</p>
					{:else if monitorNote}
						<div class="relative mt-1 inline-block">
							<button
								type="button"
								class="text-xs text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
								on:click={togglePresence}
								aria-expanded={showPresence}
							>
								{monitorNote}
								<span class="text-[0.6rem]">{showPresence ? '▲' : '▼'}</span>
							</button>
							{#if showPresence}
								<div
									class="absolute z-20 mt-1 w-64 max-h-72 overflow-y-auto rounded-xl border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg p-2"
								>
									{#if presence.length === 0}
										<p class="text-xs text-gray-400 dark:text-gray-500 px-2 py-1.5">
											{$i18n.t('No students yet — add or invite one.')}
										</p>
									{:else}
										<ul class="flex flex-col">
											{#each presence as p (p.student_id)}
												<li class="flex items-center gap-2 px-2 py-1.5 text-sm">
													<span
														class="h-2.5 w-2.5 rounded-full shrink-0 {p.online
															? 'bg-green-500'
															: 'bg-red-500'}"
														title={p.online ? $i18n.t('Online') : $i18n.t('Offline')}
													></span>
													<span class="text-gray-800 dark:text-gray-100 truncate"
														>{nameFor(p.student_id)}</span
													>
												</li>
											{/each}
										</ul>
									{/if}
								</div>
							{/if}
						</div>
					{/if}
				</div>
				<div class="flex gap-2 shrink-0">
					<button
						class="px-3 py-2 rounded-full bg-red-500 text-white text-sm hover:bg-red-600 disabled:opacity-50"
						on:click={() => setAll(false)}
						disabled={monitorBusy || roster.length === 0}>🔒 {$i18n.t('Lock all')}</button
					>
					<button
						class="px-3 py-2 rounded-full bg-green-600 text-white text-sm hover:bg-green-700 disabled:opacity-50"
						on:click={() => setAll(true)}
						disabled={monitorBusy || roster.length === 0}>🔓 {$i18n.t('Unlock all')}</button
					>
				</div>
			</div>
			{#if roster.length === 0}
				<div
					class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
				>
					{$i18n.t('No students yet — add or invite one.')}
				</div>
			{:else}
				<div class="overflow-x-auto rounded-2xl bg-white dark:bg-gray-800 shadow-sm">
					<table class="w-full text-left text-sm">
						<thead
							class="text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700"
						>
							<tr
								><th class="px-5 py-3 font-medium">{$i18n.t('Name')}</th><th
									class="px-5 py-3 font-medium">{$i18n.t('Screen')}</th
								><th class="px-5 py-3"></th></tr
							>
						</thead>
						<tbody>
							{#each roster as s (s.student_id)}
								<tr class="border-b border-gray-50 dark:border-gray-700/50">
									<td class="px-5 py-3 text-gray-800 dark:text-white">{s.name ?? s.email ?? '—'}</td
									>
									<td class="px-5 py-3">
										{#if monitorMap[s.student_id] === false}
											<span
												class="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
												>🔒 {$i18n.t('Locked')}</span
											>
											{#if $monitorAway[s.student_id]?.away && $monitorAway[s.student_id]?.classroom_id === classId}
												<span
													class="ml-1.5 text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
													title={$i18n.t('Student navigated away from the locked screen')}
													>👀 {$i18n.t('Away')}</span
												>
											{/if}
										{:else}
											<span
												class="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
												>🔓 {$i18n.t('Active')}</span
											>
										{/if}
									</td>
									<td class="px-5 py-3 text-right">
										{#if monitorMap[s.student_id] === false}
											<button
												class="text-green-600 dark:text-green-400 text-xs hover:underline"
												on:click={() => toggleMonitor(s.student_id, true)}
												>{$i18n.t('Unlock')}</button
											>
										{:else}
											<button
												class="text-red-500 hover:text-red-600 text-xs"
												on:click={() => toggleMonitor(s.student_id, false)}
												>{$i18n.t('Lock')}</button
											>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}

			<!-- E6: durable tab-away history (survives the teacher not watching live). -->
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm p-5">
				<div class="flex items-start justify-between gap-2">
					<h3 class="text-sm font-semibold text-gray-800 dark:text-white mb-1">
						{$i18n.t('Screen activity')}
					</h3>
					{#if awayLog.length > 0}
						<button
							class="text-xs text-gray-500 dark:text-gray-400 hover:text-red-600 hover:underline disabled:opacity-50"
							on:click={clearActivity}
							disabled={clearingActivity}
						>
							{clearingActivity ? $i18n.t('Clearing…') : $i18n.t('Clear')}
						</button>
					{/if}
				</div>
				<p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
					{$i18n.t('When locked students leave or return to the TutorAI screen.')}
				</p>
				{#if awayLog.length === 0}
					<p class="text-sm text-gray-400 dark:text-gray-500">{$i18n.t('No activity yet.')}</p>
				{:else}
					<ul class="flex flex-col gap-1.5 max-h-72 overflow-y-auto">
						{#each awayLog as ev (ev.id)}
							<li class="flex items-center gap-2 text-sm">
								{#if ev.away}
									<span class="text-amber-600 dark:text-amber-400">👀</span>
									<span class="text-gray-800 dark:text-gray-100"
										>{ev.student_name ?? ev.student_email ?? $i18n.t('A student')}</span
									>
									<span class="text-gray-500 dark:text-gray-400">{$i18n.t('left the screen')}</span>
								{:else}
									<span class="text-green-600 dark:text-green-400">↩️</span>
									<span class="text-gray-800 dark:text-gray-100"
										>{ev.student_name ?? ev.student_email ?? $i18n.t('A student')}</span
									>
									<span class="text-gray-500 dark:text-gray-400"
										>{$i18n.t('returned to the screen')}</span
									>
								{/if}
								<span class="ml-auto text-xs text-gray-400 dark:text-gray-500"
									>{fmtTime(ev.created_at)}</span
								>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		{/if}
	{/if}
</div>

{#if showAdd}
	<AddStudentModal
		{classId}
		on:close={() => (showAdd = false)}
		on:enrolled={onEnrolled}
		on:invited={refreshInvites}
	/>
{/if}
{#if showInvite}
	<InviteModal {classId} on:close={() => (showInvite = false)} on:invited={refreshInvites} />
{/if}
{#if showCreateAssignment}
	<CreateAssignmentModal
		{classId}
		on:close={() => (showCreateAssignment = false)}
		on:created={onAssignmentCreated}
	/>
{/if}
{#if showUpload}
	<UploadMaterialModal
		{classId}
		on:close={() => (showUpload = false)}
		on:uploaded={onMaterialUploaded}
	/>
{/if}
{#if showDelete}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
		on:click|self={() => (showDelete = false)}
		role="presentation"
	>
		<div class="w-full max-w-md rounded-2xl bg-white dark:bg-gray-800 shadow-xl p-6">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-white">
				{$i18n.t('Delete this class?')}
			</h2>
			<p class="text-sm text-gray-600 dark:text-gray-300 mt-2">
				{$i18n.t('This permanently deletes')} <span class="font-semibold">{klass?.name ?? ''}</span>
				{$i18n.t(
					'along with its roster, invitations, assignments, submissions and resources. This cannot be undone.'
				)}
			</p>
			<div class="flex justify-end gap-2 mt-5">
				<button
					class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
					on:click={() => (showDelete = false)}
					disabled={deleting}>{$i18n.t('Cancel')}</button
				>
				<button
					class="px-4 py-2 rounded-full bg-red-600 text-white text-sm hover:bg-red-700 disabled:opacity-50"
					on:click={onDeleteClass}
					disabled={deleting}>{deleting ? $i18n.t('Deleting…') : $i18n.t('Delete class')}</button
				>
			</div>
		</div>
	</div>
{/if}
