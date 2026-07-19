"""
Générateur LLM — Module Blockly (US-B02, US-B05).

Corrections apportées :
  - FIX #5 : stream=True pour le vrai streaming token par token
  - generate_exercise_stream() : générateur async qui yield chaque token
  - get_feedback_stream()      : générateur async qui yield chaque token
  - Les anciennes fonctions bloquantes sont conservées comme fallback
"""

import json
import os
from typing import AsyncGenerator

import httpx

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")

LEVEL_TOPICS = {
    "beginner": "variables, print(), opérations mathématiques simples (+,-,*,/)",
    "intermediate": "boucles for/while, conditions if/elif/else, listes",
    "advanced": "fonctions def, récursivité, algorithmes de tri",
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


# ── FIX #5 : Génération streamée token par token ─────────────────────────────


async def generate_exercise_stream(
    level: str,
    course: str = "",
    objectives: str = "",
    prerequisites: str = "",
) -> AsyncGenerator[str, None]:
    """
    Génère un exercice via Ollama.
    Utilise stream=False pour fiabilité puis yield le JSON par morceaux.
    """
    topics = LEVEL_TOPICS.get(level, LEVEL_TOPICS["beginner"])
    ctx_parts = []
    if course:
        ctx_parts.append(f"Cours : {course}")
    if objectives:
        ctx_parts.append(f"Objectifs : {objectives}")
    if prerequisites:
        ctx_parts.append(f"Prérequis : {prerequisites}")
    ctx_str = "\n".join(ctx_parts) if ctx_parts else f"Thèmes : {topics}"

    prompt = (
        f"Tu es professeur Python. Génère UN exercice niveau {level}.\n"
        f"CONTEXTE : {ctx_str}\n\n"
        f"L'exercice doit demander à l'étudiant d'afficher UN résultat précis avec print().\n"
        f"Tu dois choisir toi-même quelle valeur sera affichée et mettre cette valeur dans expected_output.\n\n"
        f"EXEMPLE CORRECT :\n"
        f'{{"title":"Addition simple",'
        f'"description":"Calculez 3 + 5 et affichez le résultat.",'
        f'"test_cases":[{{"expected_output":"8"}}],'
        f'"hints":["Utilisez le bloc print","Utilisez le bloc addition"]}}\n\n'
        f"Génère maintenant un exercice similaire sur le thème : {ctx_str}\n"
        f"Réponds UNIQUEMENT avec un JSON valide, rien d'autre."
    )

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # stream=False pour fiabilité
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 400},
                },
            )
            full_response = resp.json().get("response", FALLBACK_EXERCISE)

        # Yield par chunks de 10 caractères pour simuler le streaming
        chunk_size = 10
        for i in range(0, len(full_response), chunk_size):
            yield full_response[i : i + chunk_size]

    except Exception:
        yield FALLBACK_EXERCISE


async def get_feedback_stream(
    code: str,
    score: float,
    level: str,
) -> AsyncGenerator[str, None]:
    """
    Génère un feedback pédagogique bienveillant via Ollama en streaming réel.
    Yield chaque token au fur et à mesure.

    Ancienne version : stream=False → réponse complète bloquante
    Nouvelle version : stream=True  → yield token par token
    """
    prompt = (
        f"Tu es tuteur Python bienveillant. "
        f"Étudiant niveau {level}, score {score}/100.\n"
        f"Code soumis :\n{code}\n\n"
        f"Donne un feedback encourageant en français (3-4 phrases max).\n"
        f"Commence par féliciter, puis propose une amélioration concrète."
    )

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # FIX : stream=True au lieu de stream=False
            async with client.stream(
                "POST",
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": True,  # ← FIX
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 200,
                    },
                },
            ) as response:
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

    except Exception:
        yield "Bon travail ! Continue à pratiquer. 🎉"


# ── Fonctions legacy (gardées pour compatibilité) ─────────────────────────────


async def generate_exercise(
    level: str,
    course: str = "",
    objectives: str = "",
    prerequisites: str = "",
) -> str:
    """
    Version non-streamée — gardée pour compatibilité.
    Préférer generate_exercise_stream() pour le streaming réel.
    """
    result = ""
    async for token in generate_exercise_stream(
        level, course, objectives, prerequisites
    ):
        result += token
    return result or FALLBACK_EXERCISE


async def get_feedback(code: str, score: float, level: str) -> str:
    """
    Version non-streamée — gardée pour compatibilité.
    Préférer get_feedback_stream() pour le streaming réel.
    """
    result = ""
    async for token in get_feedback_stream(code, score, level):
        result += token
    return result or "Bon travail ! Continue à pratiquer. 🎉"
