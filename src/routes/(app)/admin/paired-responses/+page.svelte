<script lang="ts">
    import PairedResponses from '$lib/components/chat/PairedResponses.svelte';
    import { getContext } from 'svelte';
    import type { Writable } from 'svelte/store';
    import type { i18n as i18nType } from 'i18next';

    const i18n = getContext<Writable<i18nType>>('i18n');
</script>

<div class="flex flex-col gap-4">
    <h1 class="text-2xl font-bold">{$i18n.t('Paired Responses')}</h1>
    <PairedResponses />
</div> 