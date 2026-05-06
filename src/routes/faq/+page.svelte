<script>
	import { onMount } from "svelte";

	let lang = "fr";

	let translations = {
		fr: {
			title: "❓ Aide / FAQ",
			faqs: [
				{
					q: "Comment utiliser Open TutorAI ?",
					a: "Connectez-vous, choisissez votre rôle et commencez à discuter avec l’IA."
				},
				{
					q: "Puis-je utiliser l’application sans compte ?",
					a: "Non, vous devez vous connecter pour accéder aux fonctionnalités."
				},
				{
					q: "Comment contacter le support ?",
					a: "Utilisez cette page FAQ ou contactez l’administrateur."
				}
			]
		},
		en: {
			title: "❓ Help / FAQ",
			faqs: [
				{
					q: "How to use Open TutorAI?",
					a: "Log in, choose your role, and start chatting with the AI."
				},
				{
					q: "Can I use the app without an account?",
					a: "No, you need to log in to access features."
				},
				{
					q: "How to contact support?",
					a: "Use this FAQ page or contact the administrator."
				}
			]
		}
	};

	let activeIndex = null;

	function toggle(index) {
		activeIndex = activeIndex === index ? null : index;
	}
</script>

<div class="max-w-3xl mx-auto px-4 py-8">

	<!-- HEADER -->
	<div class="flex justify-between items-center mb-6">
		<h1 class="text-3xl font-bold">
			{translations[lang].title}
		</h1>

		<!-- LANGUAGE SWITCH -->
		<select bind:value={lang} class="border rounded px-2 py-1">
			<option value="fr">FR</option>
			<option value="en">EN</option>
		</select>
	</div>

	<!-- FAQ LIST -->
	<div class="space-y-4">
		{#each translations[lang].faqs as faq, index}
			<div class="bg-white dark:bg-gray-900 border rounded-2xl shadow hover:shadow-lg transition">

				<button
					class="w-full text-left p-4 flex justify-between items-center font-medium"
					on:click={() => toggle(index)}
				>
					<span class="flex items-center gap-2">
						📌 {faq.q}
					</span>

					<span class="text-xl">
						{activeIndex === index ? "−" : "+"}
					</span>
				</button>

				{#if activeIndex === index}
					<div class="px-4 pb-4 text-gray-600 dark:text-gray-300 border-t animate-fade">
						💡 {faq.a}
					</div>
				{/if}

			</div>
		{/each}
	</div>

</div>

<style>
	@keyframes fade {
		from { opacity: 0; transform: translateY(-5px); }
		to { opacity: 1; transform: translateY(0); }
	}

	.animate-fade {
		animation: fade 0.3s ease;
	}
</style>