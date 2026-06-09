<script lang="ts">
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { TUTOR_VERSION, TUTOR_BUILD_HASH } from '$lib/constants';
	import { config } from '$lib/stores';
	import { exportConfig, importConfig } from '$lib/apis/configs';
	import { downloadDatabase } from '$lib/apis/utils';

	const i18n = getContext<Writable<i18nType>>('i18n');

	let exporting = false;
	let importing = false;

	const exportConfigHandler = async () => {
		exporting = true;
		try {
			const data = await exportConfig(localStorage.token);
			const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
			saveAs(blob, `opentutorai-config-${Date.now()}.json`);
			toast.success($i18n.t('Config exported.'));
		} catch (e) {
			toast.error(`${e}`);
		} finally {
			exporting = false;
		}
	};

	const importConfigHandler = async (e: Event) => {
		const target = e.target as HTMLInputElement;
		const file = target?.files?.[0];
		if (!file) return;
		importing = true;
		const reader = new FileReader();
		reader.onload = async (ev) => {
			try {
				const data = JSON.parse(ev.target?.result as string);
				await importConfig(localStorage.token, data);
				toast.success($i18n.t('Config imported successfully.'));
			} catch (err) {
				toast.error(`${err}`);
			} finally {
				importing = false;
				target.value = '';
			}
		};
		reader.readAsText(file);
	};

	const downloadDBHandler = async () => {
		try {
			await downloadDatabase(localStorage.token);
			toast.success($i18n.t('Database downloaded.'));
		} catch (e) {
			toast.error(`${e}`);
		}
	};
</script>

<div class="flex flex-col gap-5 text-sm">
	<!-- Version info -->
	<div class="flex flex-col gap-1.5">
		<div class="font-medium">{$i18n.t('Version')}</div>
		<div class="flex gap-4 text-xs text-gray-500 dark:text-gray-400">
			<span>{$i18n.t('Open TutorAI')} <strong class="text-gray-700 dark:text-gray-200">{TUTOR_VERSION}</strong></span>
			{#if TUTOR_BUILD_HASH}
				<span>{$i18n.t('Build')} <code class="text-gray-600 dark:text-gray-300">{TUTOR_BUILD_HASH.slice(0, 8)}</code></span>
			{/if}
		</div>
	</div>

	<hr class="border-gray-100 dark:border-gray-800" />

	<!-- Config export / import -->
	<div class="flex flex-col gap-2">
		<div class="font-medium">{$i18n.t('Configuration')}</div>
		<div class="flex gap-2">
			<button
				type="button"
				class="flex-1 py-2 text-xs rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-850 transition disabled:opacity-50"
				on:click={exportConfigHandler}
				disabled={exporting}
			>
				{exporting ? $i18n.t('Exporting...') : $i18n.t('Export Config')}
			</button>

			<label
				class="flex-1 py-2 text-xs rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-850 transition text-center cursor-pointer {importing ? 'opacity-50 pointer-events-none' : ''}"
			>
				{importing ? $i18n.t('Importing...') : $i18n.t('Import Config')}
				<input type="file" accept=".json" class="hidden" on:change={importConfigHandler} />
			</label>
		</div>
	</div>

	<hr class="border-gray-100 dark:border-gray-800" />

	<!-- Database -->
	<div class="flex flex-col gap-2">
		<div class="font-medium">{$i18n.t('Database')}</div>
		<button
			type="button"
			class="w-full py-2 text-xs rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-850 transition"
			on:click={downloadDBHandler}
		>
			{$i18n.t('Download Database')}
		</button>
	</div>
</div>
