<script>
  const faqs = [
    {
      question: "Comment créer un compte étudiant ?",
      answer: "Cliquez sur 'Sign Up', choisissez 'Student', puis remplissez vos informations."
    },
    {
      question: "Comment se connecter à la plateforme ?",
      answer: "Utilisez votre email et votre mot de passe depuis la page de connexion."
    },
    {
      question: "Où trouver mon tableau de bord ?",
      answer: "Après connexion, vous êtes automatiquement redirigé vers votre dashboard."
    },
    {
      question: "Pourquoi mon tableau de bord est vide ?",
      answer: "C’est normal au début. Vous devez créer votre premier support."
    },
    {
      question: "Comment créer un support d’apprentissage ?",
      answer: "Cliquez sur '+ Support' puis ajoutez un titre et une description."
    },
    {
      question: "Comment choisir une matière ?",
      answer: "Pendant la création du support, sélectionnez la matière correspondante."
    },
    {
      question: "Quels fichiers puis-je importer ?",
      answer: "Vous pouvez importer des fichiers PDF, Word ou PowerPoint."
    },
    {
      question: "Puis-je continuer sans fichier ?",
      answer: "Oui, cliquez simplement sur 'Continue'."
    },
    {
      question: "Comment utiliser l’assistant IA ?",
      answer: "Décrivez ce que vous souhaitez apprendre puis continuez."
    },
    {
      question: "Comment suivre ma progression ?",
      answer: "Votre progression est visible depuis votre dashboard."
    }
  ];
</script>

<div class="max-w-4xl mx-auto p-6">

  <h1 class="text-3xl font-bold mb-8">
    Questions fréquentes
  </h1>

  <div class="space-y-4">

    {#each faqs as faq}

      <div class="border rounded-xl p-5">

        <h2 class="font-semibold text-lg mb-2">
          {faq.question}
        </h2>

        <p class="opacity-80">
          {faq.answer}
        </p>

      </div>

    {/each}

  </div>

</div>