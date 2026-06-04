<script lang="ts">
	import { goto } from '$app/navigation';

	export let name: string;
	export let subject: string;
	export let students: number;
	export let href: string;

	const isMath3A = name === 'Math 3A';

	// Couleur de pastille selon la matière
	const subjectColors: Record<string, string> = {
		Mathematics: 'bg-blue-500',
		Physics: 'bg-cyan-500',
		'Computer Science': 'bg-indigo-500',
		English: 'bg-purple-500'
	};
	const badgeColor = subjectColors[subject] || 'bg-gray-500';

	// Icône associée à la matière
	const subjectIcon: Record<string, string> = {
		Mathematics: '📐',
		Physics: '⚛️',
		'Computer Science': '💻',
		English: '📖'
	};
	const icon = subjectIcon[subject] || '📚';

	// Mapping matière -> image d'en-tête
	const headerImageMap: Record<string, string> = {
		Mathematics: '/assets/images/math.png',
		Physics: '/assets/images/physics.png',
		'Computer Science': '/assets/images/cs.png',
		English: '/assets/images/english.png'
	};
	const headerImage = headerImageMap[subject];
</script>

<button
	class="group relative w-full rounded-2xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 shadow-sm hover:shadow-xl transition-all duration-300 ease-out text-left overflow-hidden"
	on:click={() => goto(href)}
>
	<!-- Image d'en-tête (si elle existe) -->
	{#if headerImage}
		<div class="h-28 w-full overflow-hidden">
			<img src={headerImage} alt={`${subject} header`} class="w-full h-full object-cover" />
		</div>
	{/if}

	<!-- Dégradé de fond au survol -->
	<div class="absolute inset-0 bg-gradient-to-br from-indigo-50/0 to-indigo-50/0 group-hover:from-indigo-50/30 group-hover:to-indigo-100/20 transition-all duration-500 pointer-events-none"></div>

	<!-- Pastille de matière en haut à droite -->
	<div class="absolute top-4 right-4 flex items-center gap-1 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 px-2 py-1 rounded-full">
		<span>{icon}</span>
		<span>{subject}</span>
	</div>

	<!-- Contenu principal (avec padding) -->
	<div class="relative z-10 p-6">
		<h3 class="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">{name}</h3>
		
		<div class="mt-4 flex items-center gap-2 text-gray-600 dark:text-gray-300">
			<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
			</svg>
			<span class="text-lg font-medium">{students} students</span>
		</div>

		<!-- Actions -->
		<div class="mt-6">
			<span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/30 group-hover:bg-indigo-100 dark:group-hover:bg-indigo-900/50 transition-colors">
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
				View Course Details
			</span>
		</div>
	</div>
</button>