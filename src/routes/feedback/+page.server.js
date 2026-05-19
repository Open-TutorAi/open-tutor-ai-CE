// src/routes/feedback/+page.server.js

const BACKEND_URL = 'http://localhost:5500'; // Ton port backend Python

export async function load() {
  try {
    // 1. On appelle l'API Python pour avoir la liste
    const response = await fetch(`${BACKEND_URL}/api/feedback`);
    
    if (!response.ok) {
      return { feedbacks: [] }; // Retourne vide si erreur
    }
    
    const feedbacks = await response.json();
    return { feedbacks };
    
  } catch (error) {
    console.error("Erreur chargement feedbacks:", error);
    return { feedbacks: [] };
  }
}

export const actions = {
  default: async ({ request }) => {
    try {
      const formData = await request.formData();
      const name = formData.get('name');
      const message = formData.get('feedback'); // Change 'feedback' en 'message' si besoin côté serveur

      // 2. On envoie au backend Python
      const response = await fetch(`${BACKEND_URL}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, message })
      });

      if (!response.ok) {
        return { error: 'Erreur serveur', status: 500 };
      }

      return { success: true };

    } catch (error) {
      return { error: 'Impossible de contacter le backend', status: 500 };
    }
  }
};