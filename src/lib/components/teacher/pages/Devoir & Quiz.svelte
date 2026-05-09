<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount, getContext } from 'svelte';
	import { browser } from '$app/environment';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// --- 1. Dark Mode Logic ---
	let isDarkMode: boolean = false;
	onMount(() => {
		if (browser) {
			isDarkMode =
				localStorage.theme === 'dark' ||
				(!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
			applyTheme();
		}
	});

	function applyTheme() {
		if (isDarkMode) {
			document.documentElement.classList.add('dark');
			localStorage.theme = 'dark';
		} else {
			document.documentElement.classList.remove('dark');
			localStorage.theme = 'light';
		}
	}

	// --- 2. Quiz State (Corrected Types) ---
	let quizTitle: string = 'Quiz hebdomadaire : Protocoles Réseaux';
	let dueDate: string = '2026-02-17';
	let aiPrompt: string = 'Réseaux informatiques et couches OSI';

	let questions = [
		{
			id: 1,
			type: 'MULTIPLE CHOICE',
			text: "Quel protocole est utilisé pour l'envoi de courriers électroniques ?",
			points: 2,
			options: ['HTTP', 'SMTP', 'FTP', 'POP3'],
			correctAnswer: 'SMTP'
		},
		{
			id: 2,
			type: 'TRUE / FALSE',
			text: "L'adresse IP 192.168.1.1 est une adresse privée.",
			points: 1,
			correctAnswer: 'Vrai'
		}
	];

	// Ensure the placeholder data is translated when the language changes
	let currentLang = '';
	$: if ($i18n && $i18n.language !== currentLang) {
		currentLang = $i18n.language;
		quizTitle = $i18n.t('Weekly Quiz: Network Protocols');
		aiPrompt = $i18n.t('Computer Networks and OSI Layers');

		if (questions.length > 0) {
			questions[0].text = $i18n.t('Which protocol is used for sending emails?');
		}
		if (questions.length > 1) {
			questions[1].text = $i18n.t('The IP address 192.168.1.1 is a private address.');
			questions[1].correctAnswer = $i18n.t('True');
		}
		questions = questions; // Trigger Svelte reactivity
	}

	// Settings
	let limitTime: boolean = true;
	let timeMinutes: number = 45;
	let shuffleQuestions: boolean = true;
	let showCorrections: boolean = false;

	const handlePublish = () => {
		alert($i18n.t('Quiz published successfully!'));
		goto('/teacher/classrooms');
	};
</script>

<div
	class="flex h-screen bg-[#F8FAFC] dark:bg-[#030712] overflow-hidden font-sans transition-colors duration-500"
>
	<div class="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
		<div class="flex justify-between items-center mb-8">
			<div>
				<h1 class="text-3xl font-bold text-slate-800 dark:text-slate-50 tracking-tight">
					{$i18n.t('Quiz Creation')}
				</h1>
				<p class="text-sm text-slate-400 dark:text-slate-500 mt-1 font-medium">
					{$i18n.t('Design your assessments with AI assistance.')}
				</p>
			</div>
			<div class="flex gap-4">
				<button
					class="px-6 py-2.5 bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-full text-sm font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all"
					>{$i18n.t('Cancel')}</button
				>
				<button
					on:click={handlePublish}
					class="px-8 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-full text-sm font-bold flex items-center gap-2 shadow-lg shadow-indigo-500/20 hover:scale-[1.02] active:scale-95 transition-all"
				>
					<span>💾</span>
					{$i18n.t('Publish quiz')}
				</button>
			</div>
		</div>

		<div
			class="bg-white dark:bg-[#111827] p-8 rounded-[32px] border border-slate-100 dark:border-slate-800 shadow-sm grid grid-cols-2 gap-8 transition-all"
		>
			<div class="space-y-4">
				<label class="flex items-center justify-between cursor-pointer group">
					<span
						class="text-xs font-bold text-slate-600 dark:text-slate-400 group-hover:text-indigo-500 transition-colors"
						>{$i18n.t('Time limit')}</span
					>
					<input
						type="checkbox"
						bind:checked={limitTime}
						class="w-5 h-5 rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-800 text-indigo-600 focus:ring-indigo-500/20"
					/>
				</label>

				<label class="flex items-center justify-between cursor-pointer group">
					<span
						class="text-xs font-bold text-slate-600 dark:text-slate-400 group-hover:text-indigo-500 transition-colors"
						>{$i18n.t('Shuffle questions')}</span
					>
					<input
						type="checkbox"
						bind:checked={shuffleQuestions}
						class="w-5 h-5 rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-800 text-indigo-600 focus:ring-indigo-500/20"
					/>
				</label>

				<label class="flex items-center justify-between cursor-pointer group">
					<span
						class="text-xs font-bold text-slate-600 dark:text-slate-400 group-hover:text-indigo-500 transition-colors"
						>{$i18n.t('Show corrections')}</span
					>
					<input
						type="checkbox"
						bind:checked={showCorrections}
						class="w-5 h-5 rounded-lg border-slate-200 dark:border-slate-700 dark:bg-slate-800 text-indigo-600 focus:ring-indigo-500/20"
					/>
				</label>
			</div>

			<div class="flex items-center justify-center">
				{#if limitTime}
					<div
						class="w-full flex items-center gap-3 p-4 bg-slate-50 dark:bg-[#030712] rounded-2xl border border-slate-100 dark:border-slate-800"
					>
						<input
							type="number"
							bind:value={timeMinutes}
							class="w-20 p-2 bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-xl text-sm font-black text-indigo-600 text-center outline-none focus:ring-2 focus:ring-indigo-500/20"
						/>
						<span class="text-[10px] text-slate-400 font-black uppercase tracking-widest"
							>{$i18n.t('minutes for the quiz')}</span
						>
					</div>
				{:else}
					<p class="text-[10px] text-slate-400 italic text-center">
						{$i18n.t('No time limit set')}
					</p>
				{/if}
			</div>
		</div>

		<div
			class="bg-gradient-to-br from-blue-50/50 to-indigo-50/50 dark:from-indigo-500/5 dark:to-blue-500/5 p-1 rounded-[32px] border-2 border-indigo-100 dark:border-indigo-500/20 border-dashed"
		>
			<div class="p-6">
				<div class="flex items-center gap-4 mb-6">
					<div
						class="w-12 h-12 bg-indigo-600 text-white rounded-2xl flex items-center justify-center text-2xl shadow-lg shadow-indigo-500/20"
					>
						✨
					</div>
					<div class="flex-1">
						<h3 class="font-bold text-slate-800 dark:text-slate-100 text-base">
							{$i18n.t('AI Generation Assistant')}
						</h3>
						<p class="text-xs text-slate-400 dark:text-slate-500 font-medium">
							{$i18n.t('Instantly generate questions from a topic.')}
						</p>
					</div>
				</div>
				<div class="flex gap-3">
					<input
						bind:value={aiPrompt}
						type="text"
						placeholder={$i18n.t('Ex: OSPF routing protocols...')}
						class="flex-1 px-6 py-4 bg-white dark:bg-[#111827] border border-slate-100 dark:border-slate-800 rounded-2xl text-sm dark:text-slate-200 outline-none shadow-sm"
					/>
					<button
						class="px-8 py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl text-sm font-black uppercase tracking-widest transition-all active:scale-95 shadow-lg shadow-indigo-500/20"
						>{$i18n.t('Generate')}</button
					>
				</div>
			</div>
		</div>

		<div class="flex gap-4">
			{#each ['+ MCQ', '+ True / False', '+ Short Answer'] as type}
				<button
					class="px-6 py-3 bg-white dark:bg-[#111827] border border-slate-100 dark:border-slate-800 rounded-full text-[11px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-400 hover:bg-indigo-600 hover:text-white transition-all shadow-sm"
				>
					{$i18n.t(type)}
				</button>
			{/each}
		</div>

		<div class="space-y-6 pb-10">
			{#each questions as q}
				<div
					class="bg-white dark:bg-[#111827] rounded-[32px] border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden group transition-all hover:border-indigo-500/30"
				>
					<div
						class="p-5 bg-slate-50/50 dark:bg-[#030712]/30 flex justify-between items-center border-b border-slate-50 dark:border-slate-800"
					>
						<div class="flex gap-4 items-center">
							<span
								class="bg-indigo-100 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 text-[10px] font-black px-3 py-1.5 rounded-full uppercase tracking-widest"
								>{$i18n.t(q.type)}</span
							>
							<span class="text-xs font-bold text-slate-400">{$i18n.t('Question')} {q.id}</span>
						</div>
						<button class="text-slate-300 hover:text-red-500 transition-colors">🗑️</button>
					</div>

					<div class="p-8 space-y-6">
						<textarea
							bind:value={q.text}
							class="w-full p-5 bg-slate-50 dark:bg-[#030712] border border-slate-100 dark:border-slate-800 rounded-[20px] text-sm dark:text-slate-200 outline-none resize-none min-h-[100px] focus:ring-2 focus:ring-indigo-500/10"
						></textarea>

						{#if q.type === 'TRUE / FALSE'}
							<div class="grid grid-cols-2 gap-4">
								<button
									class="py-4 border-2 border-green-100 dark:border-green-500/20 bg-green-50/30 dark:bg-green-500/5 text-green-600 dark:text-green-400 rounded-[18px] font-black text-xs uppercase tracking-widest"
									>{$i18n.t('True')}</button
								>
								<button
									class="py-4 border border-slate-100 dark:border-slate-800 text-slate-400 rounded-[18px] font-black text-xs uppercase tracking-widest"
									>{$i18n.t('False')}</button
								>
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	</div>
</div>

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 6px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: #e2e8f0;
		border-radius: 20px;
	}
	:global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb {
		background: #1e293b;
	}

	:global(input[type='date']::-webkit-calendar-picker-indicator) {
		filter: invert(0.5);
	}
	:global(.dark input[type='date']::-webkit-calendar-picker-indicator) {
		filter: invert(1);
	}
</style>
