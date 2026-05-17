<script lang="ts">
    import { getContext } from 'svelte';
    import type { Writable } from 'svelte/store';
    import type { i18n as i18nType } from 'i18next';

    const i18n = getContext<Writable<i18nType>>('i18n');

    export let animParticipation: number = 0;
    export let animTasksExam: number     = 0;
    export let animQuiz: number          = 0;
    export let animGrades: number        = 0;
    export let ringOffset: number        = 0;
    export let ringCirc: number          = 0;
    export let ringR: number             = 52;
</script>

	<!-- ▌1. STATISTICS PANEL ▐ -->
			<div class="rounded-2xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 p-5 flex flex-col gap-4">
				<h3 class="text-base font-bold text-gray-800 dark:text-white">{$i18n.t('Statistics')}</h3>
				<div class="flex flex-col sm:flex-row items-center gap-5">
					<!-- Stat bars -->
					<div class="flex flex-col gap-3 flex-1 w-full">
						<!-- Participation -->
						<div class="flex items-center gap-3">
							<div class="w-9 h-9 rounded-full flex items-center justify-center bg-indigo-100 dark:bg-indigo-900/30 shrink-0">
								<svg class="w-5 h-5 text-indigo-500" fill="currentColor" viewBox="0 0 24 24">
									<path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
								</svg>
							</div>
							<div class="flex-1">
								<div class="flex justify-between mb-1">
									<span class="text-xs font-medium text-gray-600 dark:text-gray-300">{$i18n.t('Participation')}</span>
									<span class="text-xs font-bold text-indigo-500">{Math.round(animParticipation)}%</span>
								</div>
								<div class="h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
									<div class="h-full rounded-full bg-indigo-500" style="width:{animParticipation}%"></div>
								</div>
							</div>
						</div>
						<!-- Tasks & Exam -->
						<div class="flex items-center gap-3">
							<div class="w-9 h-9 rounded-full flex items-center justify-center bg-emerald-100 dark:bg-emerald-900/30 shrink-0">
								<svg class="w-5 h-5 text-emerald-500" fill="currentColor" viewBox="0 0 24 24">
									<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
								</svg>
							</div>
							<div class="flex-1">
								<div class="flex justify-between mb-1">
									<span class="text-xs font-medium text-gray-600 dark:text-gray-300">{$i18n.t('Tasks & Exam')}</span>
									<span class="text-xs font-bold text-emerald-500">{Math.round(animTasksExam)}%</span>
								</div>
								<div class="h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
									<div class="h-full rounded-full bg-emerald-500" style="width:{animTasksExam}%"></div>
								</div>
							</div>
						</div>
						<!-- Quiz -->
						<div class="flex items-center gap-3">
							<div class="w-9 h-9 rounded-full flex items-center justify-center bg-amber-100 dark:bg-amber-900/30 shrink-0">
								<svg class="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
									<path d="M11 7h2v2h-2zm0 4h2v6h-2zm1-9C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
								</svg>
							</div>
							<div class="flex-1">
								<div class="flex justify-between mb-1">
									<span class="text-xs font-medium text-gray-600 dark:text-gray-300">{$i18n.t('Quiz')}</span>
									<span class="text-xs font-bold text-amber-500">{Math.round(animQuiz)}%</span>
								</div>
								<div class="h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
									<div class="h-full rounded-full bg-amber-500" style="width:{animQuiz}%"></div>
								</div>
							</div>
						</div>
					</div>

					<!-- Circular grades ring -->
					<div class="flex flex-col items-center shrink-0">
						<div class="relative w-28 h-28">
							<svg class="w-full h-full -rotate-90" viewBox="0 0 128 128">
								<circle cx="64" cy="64" r={ringR} fill="none" stroke="#e5e7eb" class="dark:stroke-gray-700" stroke-width="10"/>
								<circle cx="64" cy="64" r={ringR} fill="none" stroke="#6366f1" stroke-width="10"
									stroke-linecap="round" stroke-dasharray={ringCirc} stroke-dashoffset={ringOffset}/>
							</svg>
							<div class="absolute inset-0 flex flex-col items-center justify-center">
								<span class="text-xl font-extrabold text-gray-800 dark:text-white">{Math.round(animGrades)}%</span>
								<span class="text-[9px] text-gray-400 dark:text-gray-500 text-center leading-tight px-1">{$i18n.t('Grades Completed')}</span>
							</div>
						</div>
					</div>
				</div>
			</div>