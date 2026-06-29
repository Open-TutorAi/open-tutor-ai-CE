<script>
	import { user } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import {
	getSupportRequests,
	createSupport,
	deleteSupport,
	updateSupport,
	uploadSupportFile
} from '$lib/apis/supports';

	let loading = true;
	let activePage = 'dashboard';
	let supports = [];
let loadingSupports = false;
let showSupportForm = false;
let search = '';
let selectedStatus = 'all';
let selectedSupport = null;
let editingId = null;
let selectedFile = null;
$: filteredSupports =
	supports.filter((support) => {
		const matchesSearch =
			support.title?.toLowerCase().includes(search.toLowerCase()) ||
			support.subject?.toLowerCase().includes(search.toLowerCase());

		const matchesStatus =
			selectedStatus === 'all' ||
			support.status === selectedStatus;

		return matchesSearch && matchesStatus;
	});

async function removeSupport(id) {
	const ok = confirm('Voulez-vous supprimer cette demande ?');

	if (!ok) return;

	try {
		const token = localStorage.getItem('token') || '';

		await deleteSupport(token, id);

		await loadSupports();
	} catch (e) {
		console.log(e);
		alert('Erreur lors de la suppression');
	}
}

let supportForm = {
	title: '',
	subject: '',
	short_description: ''
};

async function loadSupports() {
	try {
		loadingSupports = true;

		const token = localStorage.getItem('token') || '';

		supports = await getSupportRequests(token);

		if (!supports) {
			supports = [];
		}
	} catch (e) {
		console.log(e);
		supports = [];
	} finally {
		loadingSupports = false;
	}
}
function editSupport(support) {
	editingId = support.id;

	supportForm = {
		title: support.title,
		subject: support.subject,
		short_description: support.short_description
	};

	showSupportForm = true;
}
async function createNewSupport() {
	try {
		const token = localStorage.getItem('token') || '';

		if (editingId) {
	await updateSupport(token, editingId, {
		title: supportForm.title,
		subject: supportForm.subject,
		short_description: supportForm.short_description
	});

	editingId = null;
} else {
	const support = await createSupport(token, {
	title: supportForm.title,
	subject: supportForm.subject,
	short_description: supportForm.short_description
});

if (selectedFile) {
	await uploadSupportFile(
		token,
		support.id,
		selectedFile
	);

	selectedFile = null;
}
}

		supportForm = {
			title: '',
			subject: '',
			short_description: ''
		};

		showSupportForm = false;

		await loadSupports();
	} catch (e) {
		console.log(e);
		alert('Erreur lors de la création.');
	}
}


	onMount(() => {
		if (!$user) {
			goto('/auth');
			return;
		}

		if ($user.role !== 'teacher') {
			goto(`/${$user.role}`);
			return;
		}

		loading = false;
		loadSupports();
	});
</script>

{#if loading}
<div class="flex justify-center items-center min-h-screen">
	<div
		class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"
	></div>
</div>

{:else}

<div class="flex min-h-screen bg-[#f5f6fb]">

	<!-- SIDEBAR -->
	<aside class="w-[230px] bg-white border-r border-gray-200 flex flex-col">

		<div class="p-6">
			<img src="/favicon.png" alt="OpenTutorAI" class="h-12 w-auto" />

			<p class="text-[11px] text-gray-400 uppercase mt-8 font-semibold">
				Portail des enseignants
			</p>
		</div>

		<nav class="flex-1 px-3 space-y-2">

			<button
				on:click={() => activePage = 'dashboard'}
				class="w-full rounded-xl px-4 py-3 flex items-center gap-3
				{activePage === 'dashboard'
					? 'bg-blue-600 text-white'
					: 'text-gray-700 hover:bg-gray-100'}"
			>
				📊 Tableau de bord
			</button>

			<button
				on:click={() => activePage = 'mes-cours'}
				class="w-full rounded-xl px-4 py-3 flex items-center gap-3
				{activePage === 'mes-cours'
					? 'bg-blue-600 text-white'
					: 'text-gray-700 hover:bg-gray-100'}"
			>
				🧑‍🏫 Mes cours
			</button>

			<button
				on:click={() => activePage = 'soutien'}
				class="w-full rounded-xl px-4 py-3 flex items-center gap-3
				{activePage === 'soutien'
					? 'bg-blue-600 text-white'
					: 'text-gray-700 hover:bg-gray-100'}"
			>
				📚 Soutien
			</button>

			<button
				on:click={() => activePage = 'devoirs'}
				class="w-full rounded-xl px-4 py-3 flex items-center gap-3
				{activePage === 'devoirs'
					? 'bg-blue-600 text-white'
					: 'text-gray-700 hover:bg-gray-100'}"
			>
				📝 Devoirs à corriger
			</button>

			<button
				on:click={() => activePage = 'planification'}
				class="w-full rounded-xl px-4 py-3 flex items-center gap-3
				{activePage === 'planification'
					? 'bg-blue-600 text-white'
					: 'text-gray-700 hover:bg-gray-100'}"
			>
				📅 Planification
			</button>

			<button
				on:click={() => activePage = 'rapports'}
				class="w-full rounded-xl px-4 py-3 flex items-center gap-3
				{activePage === 'rapports'
					? 'bg-blue-600 text-white'
					: 'text-gray-700 hover:bg-gray-100'}"
			>
				📈 Rapports
			</button>

			<button
				on:click={() => activePage = 'parametres'}
				class="w-full rounded-xl px-4 py-3 flex items-center gap-3
				{activePage === 'parametres'
					? 'bg-blue-600 text-white'
					: 'text-gray-700 hover:bg-gray-100'}"
			>
				⚙️ Paramètres
			</button>

		</nav>

		<div class="p-5 text-xs text-gray-400">
			© 2025 OpenTutorAI
		</div>
	</aside>

	<!-- MAIN -->
	<div class="flex-1 flex flex-col">

		<header
			class="bg-white h-20 border-b border-gray-200 flex items-center justify-between px-8"
		>
			<div>
				<h1 class="font-bold text-xl">
					Bonjour {$user?.name || 'Prof'} 👋
				</h1>

				<p class="text-sm text-gray-400">
					Préparez le cours d'aujourd'hui !
				</p>
			</div>

			<div class="flex items-center gap-5">

				<input
					type="text"
					placeholder="Recherché..."
					class="bg-gray-100 rounded-full px-5 py-3 w-72 outline-none"
				/>

				<button
					on:click={() => activePage = 'soutien'}
					class="bg-blue-700 text-white rounded-xl px-6 py-3 font-semibold shadow"
				>
					+ Soutien
				</button>

				<button class="text-gray-500 text-xl">
					🔔
				</button>

				<div
					class="w-10 h-10 rounded-full bg-purple-200 flex items-center justify-center"
				>
					👩
				</div>

			</div>
		</header>

		<!-- CONTENU -->
		<main class="flex-1 p-8">

			{#if activePage === 'dashboard'}
				<div class="bg-white rounded-3xl h-full shadow-sm p-12">
					<h1 class="text-4xl font-bold">
						📊 Tableau de bord
					</h1>

					<p class="text-gray-500 mt-4">
						Bienvenue dans votre espace enseignant.
					</p>
				</div>
			{/if}

			{#if activePage === 'mes-cours'}
				<div class="bg-white rounded-3xl h-full shadow-sm p-12">
					<h1 class="text-4xl font-bold">
						🧑‍🏫 Mes cours
					</h1>

					<p class="text-gray-500 mt-4">
						L'espace des cours sera ajouté ici.
					</p>
				</div>
			{/if}
			{#if activePage === 'soutien'}
<div class="bg-white rounded-3xl h-full shadow-sm p-12">

	<h1 class="text-4xl font-bold mb-8">
		📚 Soutien
	</h1>

	<div class="grid grid-cols-3 gap-6 mb-10">

		<div class="bg-blue-100 p-6 rounded-2xl">
			<h2 class="font-bold text-xl">Mes demandes</h2>
			<p class="text-4xl mt-4">{supports.length}</p>
		</div>

		<div class="bg-green-100 p-6 rounded-2xl">
			<h2 class="font-bold text-xl">En cours</h2>
			<p class="text-4xl mt-4">
				{supports.filter((s) => s.status === 'pending').length}
			</p>
		</div>

		<div class="bg-orange-100 p-6 rounded-2xl">
			<h2 class="font-bold text-xl">Terminés</h2>
			<p class="text-4xl mt-4">
				{supports.filter((s) => s.status === 'completed').length}
			</p>
		</div>

	</div>

	<button
		class="bg-blue-600 text-white px-6 py-3 rounded-xl mb-8"
		on:click={() => showSupportForm = !showSupportForm}
	>
		+ Nouvelle demande de soutien
	</button>

	{#if showSupportForm}
	<div class="border rounded-2xl p-6 mb-8 bg-gray-50">

		<h2 class="text-2xl font-bold mb-5">
			Nouvelle demande
		</h2>

		<input
			bind:value={supportForm.title}
			placeholder="Titre"
			class="w-full border p-3 rounded-xl mb-4"
		/>

		<input
			bind:value={supportForm.subject}
			placeholder="Sujet"
			class="w-full border p-3 rounded-xl mb-4"
		/>

		<textarea
			bind:value={supportForm.short_description}
			placeholder="Description"
			class="w-full border p-3 rounded-xl mb-4"
		></textarea>
		<input
	type="file"
	class="w-full border p-3 rounded-xl mb-4"
	on:change={(e) => {
		selectedFile = e.target.files[0];
	}}
/>

		<button
			class="bg-green-600 text-white px-5 py-3 rounded-xl"
			on:click={createNewSupport}
		>
			Créer
		</button>

	</div>
	{/if}

	<div class="border rounded-2xl p-8 max-h-[500px] overflow-y-auto">

		<h2 class="text-2xl font-bold mb-6">
			Liste des demandes
		</h2>
<div class="flex gap-4 mb-6">

	<input
		bind:value={search}
		placeholder="Rechercher..."
		class="border rounded-xl p-3 flex-1"
	/>

	<select
		bind:value={selectedStatus}
		class="border rounded-xl p-3"
	>
		<option value="all">Tous</option>
		<option value="pending">En cours</option>
		<option value="completed">Terminés</option>
	</select>

</div>
		{#if loadingSupports}
			<p>Chargement...</p>

		{:else if supports.length === 0}

			<p class="text-gray-500">
				Aucune demande pour le moment.
			</p>

		{:else}

			{#each filteredSupports as support}

				<div
	class="border rounded-xl p-5 mb-4 cursor-pointer hover:bg-gray-50"
	on:click={() => selectedSupport = support}
>

					<h3 class="font-bold text-lg">
						{support.title}
					</h3>

					<p class="text-gray-500">
						{support.subject}
					</p>

					<p class="mt-2">
						{support.short_description}
					</p>

					<p class="text-sm text-blue-600 mt-3">
						Statut : {support.status}
					</p>
					<p class="text-sm text-gray-500 mt-1">
	📅 Créé le :
	{new Date(support.created_at).toLocaleString('fr-FR')}
</p>
					<div class="mt-4 flex gap-3">

	<button
		class="bg-yellow-500 text-white px-4 py-2 rounded-lg"
		on:click|stopPropagation={() => editSupport(support)}
	>
		✏️ Modifier
	</button>

	<button
		class="bg-red-600 text-white px-4 py-2 rounded-lg"
		on:click|stopPropagation={() => removeSupport(support.id)}
	>
		🗑 Supprimer
	</button>

</div>
					<div class="mt-4 flex gap-3">



</div>

				</div>

			{/each}

		{/if}

	</div>

</div>
{/if}
{#if selectedSupport}
<div
	class="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
	on:click={() => selectedSupport = null}
>

	<div
		class="bg-white rounded-3xl p-8 w-[600px]"
		on:click|stopPropagation
	>

		<h2 class="text-3xl font-bold mb-5">
			{selectedSupport.title}
		</h2>

		<p class="text-gray-500 mb-4">
			Sujet : {selectedSupport.subject}
		</p>

		<p class="mb-6">
			{selectedSupport.short_description}
		</p>

		<p class="text-blue-600">
			Statut : {selectedSupport.status}
		</p>
<p class="text-gray-500 mt-3">
	📅 Créé le :
	{new Date(selectedSupport.created_at).toLocaleString('fr-FR')}
</p>
		<button
			class="mt-8 bg-gray-200 px-5 py-3 rounded-xl"
			on:click={() => selectedSupport = null}
		>
			Fermer
		</button>

	</div>

</div>
{/if}

			{#if activePage === 'devoirs'}
				<div class="bg-white rounded-3xl h-full shadow-sm p-12">
					<h1 class="text-4xl font-bold">
						📝 Devoirs à corriger
					</h1>

					<p class="text-gray-500 mt-4">
						L'espace des devoirs sera ajouté ici.
					</p>
				</div>
			{/if}

			{#if activePage === 'planification'}
				<div class="bg-white rounded-3xl h-full shadow-sm p-12">
					<h1 class="text-4xl font-bold">
						📅 Planification
					</h1>

					<p class="text-gray-500 mt-4">
						L'espace de planification sera ajouté ici.
					</p>
				</div>
			{/if}

			{#if activePage === 'rapports'}
				<div class="bg-white rounded-3xl h-full shadow-sm p-12">
					<h1 class="text-4xl font-bold">
						📈 Rapports
					</h1>

					<p class="text-gray-500 mt-4">
						L'espace des rapports sera ajouté ici.
					</p>
				</div>
			{/if}

			{#if activePage === 'parametres'}
				<div class="bg-white rounded-3xl h-full shadow-sm p-12">
					<h1 class="text-4xl font-bold">
						⚙️ Paramètres
					</h1>

					<p class="text-gray-500 mt-4">
						L'espace des paramètres sera ajouté ici.
					</p>
				</div>
			{/if}

		</main>

	</div>

	<!-- RIGHT MENU -->
	<div
		class="fixed right-8 top-1/3 bg-white rounded-3xl shadow-lg p-2 flex flex-col gap-2"
	>
		<button
			class="w-20 h-20 rounded-2xl text-gray-400 hover:bg-gray-100 text-xs"
		>
			❔<br />AIDE
		</button>

		<button
			class="w-20 h-20 rounded-2xl text-gray-400 hover:bg-gray-100 text-xs"
		>
			📖<br />GUIDE
		</button>

		<button
			class="w-20 h-20 rounded-2xl text-gray-400 hover:bg-gray-100 text-xs"
		>
			👍<br />RETOUR
		</button>
	</div>

</div>

{/if}