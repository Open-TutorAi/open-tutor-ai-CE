<!-- StudentResources.svelte — class materials shared with the student (E8-S3) -->
<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { getMyTeachers } from '$lib/apis/classrooms';
	import { getClassMaterials, downloadMaterial, type ClassMaterial } from '$lib/apis/resources';

	const i18n: any = getContext('i18n');
	const token = () => localStorage.getItem('token') ?? '';

	let materials: (ClassMaterial & { class_name: string })[] = [];
	let loading = true;
	let classFilter = 'all';
	let query = '';

	$: classes = Array.from(new Map(materials.map((m) => [m.classroom_id, m.class_name])).entries());
	$: filtered = materials.filter(
		(m) =>
			(classFilter === 'all' || m.classroom_id === classFilter) &&
			m.title.toLowerCase().includes(query.toLowerCase())
	);

	function fmtSize(bytes: number | null): string {
		if (bytes == null) return '—';
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}
	function fmtDate(ts?: string | null): string {
		return ts ? new Date(ts).toLocaleDateString() : '—';
	}

	async function load() {
		loading = true;
		try {
			// The student's enrolled classes come from their teachers' class lists.
			const teachers = await getMyTeachers(token());
			const classMap = new Map<string, string>();
			for (const t of teachers) for (const c of t.classes) classMap.set(c.id, c.name);

			const lists = await Promise.all(
				[...classMap.entries()].map(async ([id, name]) => {
					try {
						const items = await getClassMaterials(token(), id);
						return items.map((m) => ({ ...m, class_name: name }));
					} catch {
						return [];
					}
				})
			);
			materials = lists.flat();
		} catch (err) {
			materials = [];
		} finally {
			loading = false;
		}
	}

	async function download(m: ClassMaterial) {
		try {
			const blob = await downloadMaterial(token(), m.classroom_id, m.id);
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

	onMount(load);
</script>

<div class="flex flex-col gap-6">
	<div>
		<h1 class="text-2xl font-bold text-gray-800 dark:text-white">{$i18n.t('Resources')}</h1>
		<p class="text-gray-500 dark:text-gray-400 mt-1">
			{$i18n.t('Materials your teachers shared with your classes.')}
		</p>
	</div>

	{#if !loading && materials.length > 0}
		<div class="flex flex-col sm:flex-row gap-3 sm:items-center">
			<select
				class="rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 py-2 text-sm text-gray-800 dark:text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
				bind:value={classFilter}
			>
				<option value="all" class="bg-white dark:bg-gray-800 text-gray-800 dark:text-white"
					>{$i18n.t('All classes')}</option
				>
				{#each classes as [id, name] (id)}
					<option value={id} class="bg-white dark:bg-gray-800 text-gray-800 dark:text-white"
						>{name}</option
					>
				{/each}
			</select>
			<div class="relative max-w-xs flex-1">
				<input
					class="w-full rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 py-2 text-sm text-gray-800 dark:text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
					placeholder={$i18n.t('Search materials…')}
					bind:value={query}
				/>
			</div>
		</div>
	{/if}

	{#if loading}
		<div class="flex justify-center py-12">
			<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
		</div>
	{:else if materials.length === 0}
		<div
			class="rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/60 dark:bg-gray-800/40 p-10 text-center text-gray-500 dark:text-gray-400"
		>
			{$i18n.t('No materials yet — they’ll appear here when a teacher shares them.')}
		</div>
	{:else}
		<div class="overflow-x-auto rounded-2xl bg-white dark:bg-gray-800 shadow-sm">
			<table class="w-full text-left text-sm">
				<thead
					class="text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700"
				>
					<tr>
						<th class="px-5 py-3 font-medium">{$i18n.t('Name')}</th>
						<th class="px-5 py-3 font-medium">{$i18n.t('Class')}</th>
						<th class="px-5 py-3 font-medium">{$i18n.t('Type')}</th>
						<th class="px-5 py-3 font-medium">{$i18n.t('Size')}</th>
						<th class="px-5 py-3 font-medium">{$i18n.t('Shared')}</th>
						<th class="px-5 py-3"></th>
					</tr>
				</thead>
				<tbody>
					{#each filtered as m (m.id)}
						<tr class="border-b border-gray-50 dark:border-gray-700/50">
							<td class="px-5 py-3 font-medium text-gray-800 dark:text-white">{m.title}</td>
							<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{m.class_name}</td>
							<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{m.content_type ?? '—'}</td>
							<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{fmtSize(m.size)}</td>
							<td class="px-5 py-3 text-gray-600 dark:text-gray-300">{fmtDate(m.created_at)}</td>
							<td class="px-5 py-3 text-right"
								><button
									class="text-blue-600 dark:text-blue-400 text-xs hover:underline"
									on:click={() => download(m)}>{$i18n.t('Download')}</button
								></td
							>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
