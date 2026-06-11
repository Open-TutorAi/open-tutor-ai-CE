import httpx, json, os

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

LEVEL_TOPICS = {
    "beginner":     "variables, print(), opérations mathématiques simples",
    "intermediate": "boucles for/while, conditions if/elif/else, listes",
    "advanced":     "fonctions def, récursivité, algorithmes de tri",
}

class BlocklyLLMGenerator:

    async def stream_exercise(self, level: str, course: str = "", objectives: str = "", prerequisites: str = ""):
        topics = LEVEL_TOPICS.get(level, LEVEL_TOPICS["beginner"])
        context_part = ""
        if course:       context_part += f"\nCours: {course}"
        if objectives:   context_part += f"\nObjectifs: {objectives}"
        if prerequisites: context_part += f"\nPrérequis: {prerequisites}"

        prompt = f"""Tu es professeur Python. Génère un exercice niveau {level}.
Thèmes: {topics}{context_part}

Réponds UNIQUEMENT avec ce JSON, sans texte avant ou après:
{{"title":"titre","description":"description en 2 phrases","test_cases":[{{"expected_output":"valeur"}}],"hints":["indice1","indice2"]}}"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/generate",
                json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False})
            data = resp.json()
            response_text = data.get("response", "")
            # Envoyer le texte complet en un seul chunk
            yield response_text

    async def stream_feedback(self, code: str, score: float, level: str):
        prompt = f"""Tu es tuteur Python bienveillant. Étudiant niveau {level}, score {score}/100.
Code soumis:
{code}

Donne 3 phrases de feedback encourageant en français."""

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/generate",
                json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False})
            data = resp.json()
            yield data.get("response", "Bon travail ! Continue comme ça.")
