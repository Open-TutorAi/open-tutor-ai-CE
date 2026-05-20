<script lang="ts">
    import { getContext, createEventDispatcher } from 'svelte';
    import type { Writable } from 'svelte/store';
    import type { i18n as i18nType } from 'i18next';

    const i18n = getContext<Writable<i18nType>>('i18n');
    const dispatch = createEventDispatcher();

    export let calCells: (number | null)[] = [];
    export let calMonth: number            = 0;
    export let calYear: number             = 0;
    export let calSelectedDays: number[]   = [];
    export let calEventDays: number[]      = [];
    export let isToday: (d: number) => boolean  = () => false;
    export let isSunSat: (d: number) => boolean = () => false;
    export let calPrev: () => void              = () => {};
    export let calNext: () => void              = () => {};

    const DOW  = ['SUN','MON','TUE','WED','THU','FRI','SAT'];
    const MONS = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];

    function selectDay(day: number) {
        dispatch('selectDay', day);
    }
</script>

<div class="sm:col-span-2 lg:col-span-1 rounded-2xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 p-5 flex flex-col gap-3">
    <div class="flex items-center justify-between">
        <button on:click={calPrev}
            class="w-7 h-7 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-500 dark:text-gray-400"
            aria-label={$i18n.t('Previous month')}>
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/>
            </svg>
        </button>
        <h3 class="text-sm font-bold text-gray-800 dark:text-white">{$i18n.t(MONS[calMonth])} {calYear}</h3>
        <button on:click={calNext}
            class="w-7 h-7 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-500 dark:text-gray-400"
            aria-label={$i18n.t('Next month')}>
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
            </svg>
        </button>
    </div>

    <div class="grid grid-cols-7 text-center">
        {#each DOW as d, i}
            <span class="text-[10px] font-semibold uppercase {i === 0 || i === 6 ? 'text-red-400' : 'text-gray-400 dark:text-gray-500'}">{$i18n.t(d)}</span>
        {/each}
    </div>

    <div class="grid grid-cols-7 gap-y-1 text-center">
        {#each calCells as day}
            {#if day === null}
                <span></span>
            {:else}
                <button
                    on:click={() => selectDay(day)}
                    class="relative mx-auto w-7 h-7 flex items-center justify-center rounded-full text-xs font-medium transition-all duration-150
                        {isToday(day)
                            ? 'bg-indigo-500 text-white shadow-md hover:bg-indigo-600'
                            : calSelectedDays.includes(day)
                            ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-300'
                            : isSunSat(day)
                            ? 'text-red-500 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}"
                    aria-pressed={calSelectedDays.includes(day)}
                    aria-label="{day} {MONS[calMonth]} {calYear}"
                >
                    {day}
                    {#if calEventDays.includes(day) && !isToday(day)}
                        <span class="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-indigo-400"></span>
                    {/if}
                </button>
            {/if}
        {/each}
    </div>
</div>
            <!-- Remplacez calSelected = day par selectDay(day) -->