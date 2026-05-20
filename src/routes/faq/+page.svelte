<script>
  import { enhance } from '$app/forms';
  
  // Données des questions FAQ
  const faqData = [
    {
      category: "Compte",
      questions: [
        {
          q: "Comment créer un compte ?",
          a: "Cliquez sur 'S'inscrire' en haut à droite, remplissez le formulaire avec votre email et mot de passe, puis validez votre compte via le lien reçu par email."
        },
        {
          q: "Puis-je utiliser l'application sans compte ?",
          a: "Non, un compte est nécessaire pour accéder à toutes les fonctionnalités et sauvegarder votre progression."
        },
        {
          q: "Comment modifier mon profil ?",
          a: "Allez dans Paramètres > Mon profil pour modifier vos informations personnelles, votre photo et vos préférences."
        }
      ]
    },
    {
      category: "Navigation",
      questions: [
        {
          q: "Comment utiliser Open TutorAI ?",
          a: "Connectez-vous, choisissez votre rôle (élève, professeur, parent) et commencez à discuter avec l'IA pour obtenir de l'aide personnalisée."
        },
        {
          q: "Comment naviguer entre les différentes sections ?",
          a: "Utilisez le menu de navigation en haut de page ou la barre latérale pour accéder aux différentes fonctionnalités."
        }
      ]
    },
    {
      category: "Support",
      questions: [
        {
          q: "Comment contacter le support ?",
          a: "Utilisez le formulaire ci-dessous ou envoyez un email à support@opentutorai.com. Nous répondons sous 24-48h."
        },
        {
          q: "Quels sont les horaires du support ?",
          a: "Notre équipe est disponible du lundi au vendredi, de 9h à 18h (hors jours fériés)."
        }
      ]
    },
    {
      category: "Technique",
      questions: [
        {
          q: "Quels navigateurs sont compatibles ?",
          a: "Open TutorAI fonctionne sur Chrome, Firefox, Safari et Edge (dernières versions)."
        },
        {
          q: "L'application est-elle disponible sur mobile ?",
          a: "Oui, l'application est responsive et fonctionne sur tous les appareils mobiles. Une application native est en développement."
        }
      ]
    }
  ];

  // État
  let searchQuery = '';
  let selectedCategory = 'Toutes';
  let openIndex = 0; // Première question ouverte par défaut
  let form = { success: null, error: null };
  
  // Filtrer les questions
  $: filteredFAQ = faqData.map(cat => ({
    ...cat,
    questions: cat.questions.filter(q => 
      q.q.toLowerCase().includes(searchQuery.toLowerCase()) ||
      q.a.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(cat => 
    (selectedCategory === 'Toutes' || cat.category === selectedCategory) &&
    cat.questions.length > 0
  );

  // Catégories disponibles
  $: categories = ['Toutes', ...faqData.map(c => c.category)];
</script>

<div class="max-w-4xl mx-auto p-6 space-y-8">
  
  <!-- Header -->
  <div class="text-center space-y-4">
    <h1 class="text-4xl font-bold">❓ Aide & FAQ</h1>
    <p class="text-gray-600">Trouvez rapidement des réponses à vos questions</p>
  </div>

  <!-- Barre de recherche -->
  <div class="relative">
    <input
      type="text"
      bind:value={searchQuery}
      placeholder="🔍 Rechercher une question..."
      class="w-full px-6 py-4 text-lg border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition"
    />
    {#if searchQuery}
      <button
        on:click={() => searchQuery = ''}
        class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
      >
        ✕
      </button>
    {/if}
  </div>

  <!-- Filtres par catégorie -->
  <div class="flex flex-wrap gap-2 justify-center">
    {#each categories as cat}
      <button
        on:click={() => selectedCategory = cat}
        class="px-4 py-2 rounded-full border-2 transition {selectedCategory === cat ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300'}"
      >
        {cat}
      </button>
    {/each}
  </div>

  <!-- 🟢 Questions fréquentes (ZONE SCROLLABLE) -->
  <div class="faq-scroll-area space-y-3">
    {#if filteredFAQ.length === 0}
      <div class="text-center py-12 text-gray-500">
        <p class="text-6xl mb-4">🔍</p>
        <p class="text-xl">Aucune question trouvée</p>
        <p>Essayez avec d'autres mots-clés</p>
      </div>
    {:else}
      {#each filteredFAQ as category}
        <div class="mb-6">
          <h2 class="text-lg font-semibold text-blue-600 mb-3 flex items-center gap-2">
            📁 {category.category}
          </h2>
          
          {#each category.questions as question, index}
            <div class="border-2 border-gray-200 rounded-xl overflow-hidden hover:border-blue-300 transition">
              <button
                on:click={() => openIndex = openIndex === `${category.category}-${index}` ? null : `${category.category}-${index}`}
                class="w-full px-6 py-4 text-left flex justify-between items-center bg-white hover:bg-gray-50 transition"
              >
                <span class="font-medium text-gray-800"> {question.q}</span>
                <span class="text-2xl text-blue-500">
                  {openIndex === `${category.category}-${index}` ? '−' : '+'}
                </span>
              </button>
              
              {#if openIndex === `${category.category}-${index}`}
                <div class="px-6 py-4 bg-blue-50 border-t-2 border-gray-200">
                  <p class="text-gray-700 leading-relaxed">{question.a}</p>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/each}
    {/if}
  </div>

  <!-- Formulaire de contact (reste fixe, hors du scroll) -->
  <div class="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl p-8 border-2 border-blue-200">
    <h2 class="text-2xl font-bold mb-2">💬 Vous avez une autre question ?</h2>
    <p class="text-gray-600 mb-6">Notre équipe est là pour vous aider</p>
    
    <form method="POST" use:enhance class="space-y-4">
      <div>
        <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
          Votre email *
        </label>
        <input
          type="email"
          id="email"
          name="email"
          placeholder="votre@email.com"
          class="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
          required
        />
      </div>

      <div>
        <label for="question" class="block text-sm font-medium text-gray-700 mb-1">
          Votre question *
        </label>
        <textarea
          id="question"
          name="question"
          rows="4"
          placeholder="Décrivez votre problème ou votre question..."
          class="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
          required
        ></textarea>
      </div>

      <button
        type="submit"
        class="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition font-medium text-lg"
      >
        📩 Envoyer ma question
      </button>
    </form>

    {#if form?.success}
      <div class="mt-4 p-4 bg-green-100 text-green-700 rounded-lg">
        ✅ Merci ! Votre question a été envoyée. Nous vous répondrons sous 24-48h.
      </div>
    {/if}
    
    {#if form?.error}
      <div class="mt-4 p-4 bg-red-100 text-red-700 rounded-lg">
        ❌ {form.error}
      </div>
    {/if}
  </div>

  <!-- Liens rapides -->
  <div class="grid md:grid-cols-3 gap-4">
    <a href="/feedback" class="p-6 bg-white border-2 border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-lg transition text-center">
      <div class="text-3xl mb-2">💡</div>
      <h3 class="font-semibold text-gray-800">Donner un feedback</h3>
      <p class="text-sm text-gray-600 mt-1">Aidez-nous à nous améliorer</p>
    </a>
    
    <a href="/" class="p-6 bg-white border-2 border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-lg transition text-center">
      <div class="text-3xl mb-2">🏠</div>
      <h3 class="font-semibold text-gray-800">Page d'accueil</h3>
      <p class="text-sm text-gray-600 mt-1">Retourner à l'accueil</p>
    </a>
    
    <a href="mailto:support@opentutorai.com" class="p-6 bg-white border-2 border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-lg transition text-center">
      <div class="text-3xl mb-2">📧</div>
      <h3 class="font-semibold text-gray-800">Email direct</h3>
      <p class="text-sm text-gray-600 mt-1">support@opentutorai.com</p>
    </a>
  </div>

</div>

<style>
  /* Animation fluide pour les boutons */
  button {
    transition: all 0.3s ease;
  }

  /* 🟢 SCROLLBAR GLOBALE DE LA PAGE */
  
  /* Pour Firefox */
  * {
    scrollbar-width: thin;
    scrollbar-color: #94a3b8 #f1f5f9;
  }

  /* Pour Chrome/Safari/Edge */
  ::-webkit-scrollbar {
    width: 10px;
    height: 10px;
  }
  
  ::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 8px;
  }
  
  ::-webkit-scrollbar-thumb {
    background-color: #94a3b8;
    border-radius: 8px;
    border: 2px solid #f1f5f9;
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background-color: #64748b;
  }

  /* Optionnel : Effet de fondu en haut/bas du scroll */
  .faq-page-container {
    min-height: 100vh;
    padding-bottom: 2rem;
  }
</style>