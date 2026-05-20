const BACKEND_URL = 'http://localhost:5500';

export const actions = {
  default: async ({ request }) => {
    const formData = await request.formData();
    const email = formData.get('email');
    const question = formData.get('question');

    try {
      const res = await fetch(`${BACKEND_URL}/api/faq-question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, question })
      });

      if (!res.ok) return { error: 'Erreur serveur' };
      return { success: true };
    } catch (e) {
      return { error: 'Impossible de contacter le backend' };
    }
  }
};