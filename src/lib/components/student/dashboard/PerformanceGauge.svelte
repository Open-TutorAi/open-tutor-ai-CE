<script lang="ts">
    import { getContext } from 'svelte';
    import type { Writable } from 'svelte/store';
    import type { i18n as i18nType } from 'i18next';

    const i18n = getContext<Writable<i18nType>>('i18n');

    export let animPoints: number   = 0;
    export let animNeedle: number   = 0;
    export let gFillPath: string    = '';
    export let gBgPath: string      = '';
    export let gNeedleTip: { x: number; y: number } = { x: 0, y: 0 };
    export let gFillLarge: number   = 0;
    export let gcx: number          = 100;
    export let gcy: number          = 90;
    export let gR: number           = 70;
    export let zoneArc: (from: number, to: number, r: number) => string = () => '';
</script>

<!-- ▌2. PERFORMANCE GAUGE ▐ -->
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 p-5 flex flex-col gap-2">
				<h3 class="text-base font-bold text-gray-800 dark:text-white">{$i18n.t('Performance')}</h3>
				<div class="flex items-center gap-2 mb-1">
					<span class="w-3 h-3 rounded-sm bg-indigo-500 inline-block"></span>
					<span class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Point Progress')}</span>
				</div>
				<div class="flex flex-col items-center flex-1 justify-center">
					<svg viewBox="0 0 200 105" class="w-full max-w-[200px]" aria-label={$i18n.t('Performance gauge')}>
						<defs>
							<linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
								<stop offset="0%"   stop-color="#ef4444"/>
								<stop offset="50%"  stop-color="#f59e0b"/>
								<stop offset="100%" stop-color="#10b981"/>
							</linearGradient>
						</defs>
						<path d={zoneArc(180,120,gR)} fill="none" stroke="#ef4444" stroke-width="13" opacity="0.15"/>
						<path d={zoneArc(120, 60,gR)} fill="none" stroke="#f59e0b" stroke-width="13" opacity="0.15"/>
						<path d={zoneArc( 60,  0,gR)} fill="none" stroke="#10b981" stroke-width="13" opacity="0.15"/>
						<path d={gBgPath}   fill="none" stroke="#e5e7eb" class="dark:stroke-gray-700" stroke-width="13" stroke-linecap="round" opacity="0.5"/>
						<path d={gFillPath} fill="none" stroke="url(#gaugeGrad)" stroke-width="13" stroke-linecap="round"/>
						<line x1={gcx} y1={gcy} x2={gNeedleTip.x} y2={gNeedleTip.y}
							stroke="#374151" class="dark:stroke-gray-200" stroke-width="2.5" stroke-linecap="round"/>
						<circle cx={gcx} cy={gcy} r="5"   fill="#374151" class="dark:fill-gray-200"/>
						<circle cx={gcx} cy={gcy} r="2.5" fill="white"   class="dark:fill-gray-800"/>
						<text x="20"  y="103" font-size="7" fill="#ef4444" text-anchor="middle" font-family="sans-serif">Low</text>
						<text x="100" y="16"  font-size="7" fill="#f59e0b" text-anchor="middle" font-family="sans-serif">Mid</text>
						<text x="180" y="103" font-size="7" fill="#10b981" text-anchor="middle" font-family="sans-serif">High</text>
					</svg>
					<div class="text-center mt-2">
						<p class="text-xs text-gray-400 dark:text-gray-500">{$i18n.t('Your Point')}</p>
						<p class="text-2xl font-extrabold text-gray-800 dark:text-white tracking-tight">
							{Math.round(animPoints).toLocaleString()}
						</p>
					</div>
				</div>
			</div>
