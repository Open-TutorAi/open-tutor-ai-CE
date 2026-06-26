"""
Générateur LLM — Module Blockly (US-B02, US-B05).
Appelle Ollama (qwen2.5:0.5b) pour :
  - générer des exercices Python adaptés au niveau
  - produire un feedback pédagogique bienveillant
"""
import json
import os
import httpx

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = "qwen2.5:0.5b"

LEVEL_TOPICS = {
    "beginner":     "variables, print(), opérations mathématiques simples (+,-,*,/)",
    "intermediate": "boucles for/while, conditions if/elif/else, listes",
    "advanced":     "fonctions def, récursivité, algorithmes de tri",
}

FALLBACK_EXERCISE = json.dumps(
    {
        "title": "Calcul de somme",
        "description": (
            "Calculez la somme de deux nombres et affichez le résultat. "
            "Utilisez les blocs Variables et Maths."
        ),
        "test_cases": [{"expected_output": "8"}],
        "hints": [
            "Utilisez un bloc 'définir variable' pour chaque nombre",
            "Utilisez le bloc print() pour afficher le résultat",
        ],
    }
)


async def generate_exercise(
    level: str,
    course: str = "",
    objectives: str = "",
    prerequisites: str = "",
) -> str:
    """
    Génère un exercice Python via Ollama.

    Returns:
        str : JSON brut {title, description, test_cases, hints}
              ou FALLBACK_EXERCISE si Ollama indisponible.
    """
    topics = LEVEL_TOPICS.get(level, LEVEL_TOPICS["beginner"])

    ctx = ""
    if course:        ctx += f"\nCours : {course}"
    if objectives:    ctx += f"\nObjectifs : {objectives}"
    if prerequisites: ctx += f"\nPrérequis : {prerequisites}"

    prompt = (
        f"Tu es professeur Python. Génère un exercice niveau {level}.\n"
        f"Thèmes : {topics}{ctx}\n\n"
        f"Réponds UNIQUEMENT avec ce JSON valide, rien d'autre :\n"
        f'{{"title":"titre court",'
        f'"description":"description claire en 2 phrases",'
        f'"test_cases":[{{"expected_output":"valeur attendue"}}],'
        f'"hints":["indice 1","indice 2"]}}'
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": MODEL, "prompt": prompt, "stream": False},
            )
            return resp.json().get("response", FALLBACK_EXERCISE)
    except Exception:
        return FALLBACK_EXERCISE


async def get_feedback(code: str, score: float, level: str) -> str:
    """
    Génère un feedback pédagogique bienveillant via Ollama.

    Returns:
        str : texte du feedback (3-4 phrases en français)
    """
    prompt = (
        f"Tu es tuteur Python bienveillant. "
        f"Étudiant niveau {level}, score {score}/100.\n"
        f"Code soumis :\n{code}\n\n"
        f"Donne un feedback encourageant en français (3-4 phrases).\n"
        f"Commence par féliciter, puis propose une amélioration."
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": MODEL, "prompt": prompt, "stream": False},
            )
            return resp.json().get(
                "response", "Bon travail ! Continue à pratiquer. 🎉"
            )
    except Exception:
        return "Bon travail ! Continue à pratiquer. 🎉"
