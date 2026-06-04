<script lang="ts">
	import ClassCard from '$lib/components/teacher/elements/ClassCard.svelte';
	import CreateClassModal from '$lib/components/teacher/elements/CreateClassModal.svelte';

	const classes = [
		{ id: '1', name: 'Math 3A', subject: 'Mathematics', students: 24 },
		{ id: '2', name: 'Physics 2B', subject: 'Physics', students: 18 },
		{ id: '3', name: 'CS 1S', subject: 'Computer Science', students: 30 },
		{ id: '4', name: 'English 4C', subject: 'English', students: 22 }
	];

	let showCreateModal = false;

	function handleCreateClass() {
		showCreateModal = true;
	}
</script>

<div class="flex flex-col gap-6">
	<div class="flex justify-between items-center">
		<h1 class="text-2xl font-bold">My Classes</h1>
		
		<button
			class="bg-indigo-500 hover:bg-indigo-600 text-white py-2 px-4 rounded-lg"
			on:click={handleCreateClass}
		>
			+ Create New Class
		</button>
	</div>

	{#if classes.length === 0}
		<div class="text-center py-12 text-gray-500">Aucune classe pour le moment.</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
			{#each classes as cls}
				<ClassCard
					name={cls.name}
					subject={cls.subject}
					students={cls.students}
					href={`/teacher/classroom/${cls.id}`}
				/>
			{/each}
		</div>
	{/if}
</div>

<!-- Modale de création -->
<CreateClassModal show={showCreateModal} onClose={() => showCreateModal = false} />