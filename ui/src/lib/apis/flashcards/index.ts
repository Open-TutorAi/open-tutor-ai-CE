import { TUTOR_API_BASE_URL } from '$lib/constants';

export async function generateFlashcards(token: string, content: string, numCards: number = 5, lessonId: string | null = null, tag: string | null = null) {
  const response = await fetch(`${TUTOR_API_BASE_URL}/flashcards/generate`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ 
      content, 
      num_cards: numCards, 
      lesson_id: lessonId,
      tag
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate flashcards');
  }
  
  return await response.json();
}

export async function generateFromPDF(
  token: string, 
  file: File, 
  numCards: number = 5, 
  tag: string | null = null
) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('num_cards', numCards.toString());
  if (tag) formData.append('tag', tag);
  
  const response = await fetch(`${TUTOR_API_BASE_URL}/flashcards/generate-from-pdf`, {
    method: 'POST',
    headers: {
      'authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
    throw new Error(error.detail || 'Failed to generate from PDF');
  }
  
  return await response.json();
}

export async function getDueCards(token: string, limit: number = 20) {
  const response = await fetch(
    `${TUTOR_API_BASE_URL}/flashcards/due?limit=${limit}`,
    { 
      headers: {
        'Accept': 'application/json',
        'authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch due cards');
  }
  
  return await response.json();
}

export async function getDueCardsByTag(token: string, tag: string, limit: number = 20) {
  const response = await fetch(
    `${TUTOR_API_BASE_URL}/flashcards/due/${encodeURIComponent(tag)}?limit=${limit}`,
    { 
      headers: {
        'Accept': 'application/json',
        'authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch cards');
  }
  
  return await response.json();
}

export async function getTags(token: string) {
  const response = await fetch(
    `${TUTOR_API_BASE_URL}/flashcards/tags`,
    { 
      headers: {
        'authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch tags');
  }
  
  return await response.json();
}

export async function reviewCard(token: string, cardId: string, correct: boolean) {
  const response = await fetch(`${TUTOR_API_BASE_URL}/flashcards/review`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ card_id: cardId, correct })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to review card');
  }
  
  return await response.json();
}

export async function getStats(token: string) {
  const response = await fetch(
    `${TUTOR_API_BASE_URL}/flashcards/stats`,
    { 
      headers: {
        'Accept': 'application/json',
        'authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch stats');
  }
  
  return await response.json();
}

export async function deleteFlashcard(token: string, cardId: string) {
  const response = await fetch(
    `${TUTOR_API_BASE_URL}/flashcards/${cardId}`,
    { 
      method: 'DELETE',
      headers: {
        'authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete flashcard');
  }
  
  return await response.json();
}
