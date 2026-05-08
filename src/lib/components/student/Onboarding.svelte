<script>
  import { onMount } from 'svelte';
  import introJs from 'intro.js';
  import 'intro.js/introjs.css';

  function startOnboarding() {
    if (!localStorage.getItem('student-onboarding-done')) {
      setTimeout(() => {
        const intro = introJs();

        intro.setOptions({
          steps: [
            {
              element: '#create-support-btn',
              title: 'Créer un support',
              intro: 'Cliquez ici pour créer votre premier support d’apprentissage. Vous serez guidé pour définir votre sujet et vos objectifs.'
            }
          ],
          exitOnOverlayClick: false,
          nextLabel: 'Suivant →',
          prevLabel: '← Précédent',
          doneLabel: 'Terminé'
        });

        intro.onexit(() => {
          localStorage.setItem('student-onboarding-done', 'true');
        });

        intro.start();
      }, 1000);
    }
  }

  onMount(() => {
    startOnboarding();
  });
</script>