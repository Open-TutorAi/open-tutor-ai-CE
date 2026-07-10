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
    "beginner":     "variables, print(), opérations mathématiques simples (+,-,*,/)",
    "intermediate": "boucles for/while, conditions if/elif/else, listes",
    "advanced":     "fonctions def, récursivité, algorithmes de tri",
}

FALLBACK_EXERCISE = json.dumps({
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
})


# ── FIX #5 : Génération streamée token par token ─────────────────────────────

async def generate_exercise_stream(
    level: str,
    course: str = "",
    objectives: str = "",
    prerequisites: str = "",
) -> AsyncGenerator[str, None]:
    """
    Génère un exercice Python via Ollama en streaming réel.
    Yield chaque token au fur et à mesure — pas de blocage 60s.

    Ancienne version : stream=False → attendait la réponse complète
    Nouvelle version : stream=True  → yield token par token
    """
    topics = LEVEL_TOPICS.get(level, LEVEL_TOPICS["beginner"])
    # Construire le contexte pédagogique
    ctx_parts = []
    if course:        ctx_parts.append(f"Cours / Sujet : {course}")
    if objectives:    ctx_parts.append(f"Objectifs d'apprentissage : {objectives}")
    if prerequisites: ctx_parts.append(f"Prérequis : {prerequisites}")
    ctx_str = "\n".join(ctx_parts) if ctx_parts else f"Thèmes généraux niveau {level} : {topics}"

    prompt = (
         f"Tu es professeur Python. Génère UN exercice de programmation Python.\n\n"
         f"CONTEXTE PÉDAGOGIQUE (respecte-le strictement) :\n"
         f"{ctx_str}\n\n"
         f"NIVEAU : {level}\n\n"
         f"CONTRAINTES STRICTES :\n"
         f"- L'exercice DOIT porter exactement sur le contexte fourni ci-dessus\n"
         f"- N'invente pas de thème différent\n"
         f"- La description doit être claire et précise\n"
         f"- Génère exactement 1 cas de test avec expected_output\n\n"
         f"Réponds UNIQUEMENT avec ce JSON valide, rien d'autre :\n"
         f'{{"title":"titre court précis",'
         f'"description":"description claire en 2 phrases basée sur le contexte",'
         f'"test_cases":[{{"expected_output":"valeur attendue"}}],'
         f'"hints":["indice 1 lié au contexte","indice 2 lié au contexte"]}}'
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
                    "stream": True,           # ← FIX
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 400,
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
        # Fallback : on yield le JSON complet en un seul token
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
                    "stream": True,           # ← FIX
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
    async for token in generate_exercise_stream(level, course, objectives, prerequisites):
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