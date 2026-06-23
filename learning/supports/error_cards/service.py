"""Service for generating and managing error cards from student/tutor exchanges."""
import json
import logging
import re
from typing import List, Optional

import httpx
from sqlalchemy.orm import Session

from ai.providers.service import ProvidersService
from common.exceptions import NotFoundError, ValidationError
from data.models.error_card import ErrorCard
from learning.supports.error_cards.repository import ErrorCardRepository
from learning.supports.repository import SupportRepository

log = logging.getLogger(__name__)


ANALYZER_SYSTEM_PROMPT = """Tu es un analyseur pédagogique expert.
On va te donner un échange entre un élève et un tuteur IA.

Ta tâche : identifier TOUTES les erreurs de compréhension, confusions conceptuelles,
ou mauvaises applications de notions présentes dans le MESSAGE DE L'ÉLÈVE.

Réponds TOUJOURS avec ce format JSON strict :
{
  "errors": [
    {
      "concept": "nom court du concept (max 80 caractères)",
      "error_description": "description de l'erreur détectée (1-2 phrases)",
      "simple_explanation": "explication pédagogique du concept correct (2-4 phrases)",
      "correct_example": "exemple concret et correct (code, chiffres ou texte)"
    }
  ]
}

Si l'élève ne montre AUCUNE erreur (question de curiosité, demande de clarification,
remerciement, salutation, ou compréhension correcte), réponds :
{ "errors": [] }

RÈGLES STRICTES :
- Réponds UNIQUEMENT avec du JSON valide, sans markdown, sans ```json, sans texte avant/après.
- Le tableau "errors" peut contenir 0, 1 ou plusieurs entrées selon le nombre d'erreurs détectées.
- Pas d'entrée pour les salutations, questions hors-sujet ou messages sans erreur.
- Sois pédagogique : chaque explication doit aider l'élève à corriger sa compréhension."""


class ErrorCardsService:
    """Analyzes student/tutor exchanges and generates structured error cards."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = ErrorCardRepository(session)
        self.supports_repo = SupportRepository(session, __import__(
            "data.models", fromlist=["Support"]
        ).Support)
        self.providers = ProvidersService(session)

    # ---------- Public API ----------

    async def analyze_exchange(
        self,
        support_id: str,
        user_id: str,
        user_message: str,
        assistant_message: str,
        model: str,
    ) -> List[ErrorCard]:
        """Analyze one exchange. Create and return ALL detected error cards.
        Returns an empty list if no error is detected or LLM is unavailable.
        """
        # 1. Verify the support exists and belongs to this user
        support = self.supports_repo.get_by_id(support_id)
        if not support:
            raise NotFoundError("Support", support_id)
        if support.user_id != user_id:
            raise NotFoundError("Support", support_id)

        if not user_message or not assistant_message:
            raise ValidationError("user_message and assistant_message are required")

        # 2. Resolve provider for the chosen model
        try:
            base_url, api_key, path = await self.providers.resolve_provider(model)
        except Exception as exc:
            log.warning("Cannot resolve provider for model '%s': %s", model, exc)
            return []

        # 3. Build the LLM payload (OpenAI-compatible chat completions)
        llm_body = {
            "model": model,
            "messages": [
                {"role": "system", "content": ANALYZER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"--- MESSAGE DE L'ÉLÈVE ---\n{user_message}\n\n"
                        f"--- RÉPONSE DU TUTEUR ---\n{assistant_message}\n\n"
                        "Analyse maintenant et réponds en JSON."
                    ),
                },
            ],
            "stream": False,
            "temperature": 0.2,
        }

        # 4. Call the LLM
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=llm_body, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            log.warning("LLM analysis call failed for support %s: %s", support_id, exc)
            return []

        # 5. Extract the textual content
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            log.warning("Malformed LLM response: %s", data)
            return []

        # 6. Parse the JSON
        parsed = self._extract_json(content)
        if not parsed:
            return []

        raw_errors = parsed.get("errors", [])
        if not isinstance(raw_errors, list) or not raw_errors:
            return []

        # 7. Persist one card per detected error
        required = ["concept", "error_description", "simple_explanation", "correct_example"]
        created: List[ErrorCard] = []
        for entry in raw_errors:
            if not isinstance(entry, dict):
                continue
            if not all(entry.get(f) for f in required):
                log.info("Incomplete error entry, skipped: %s", entry)
                continue
            card = self.repo.create(
                support_id=support_id,
                user_id=user_id,
                concept=str(entry["concept"])[:200],
                error_description=str(entry["error_description"]),
                simple_explanation=str(entry["simple_explanation"]),
                correct_example=str(entry["correct_example"]),
                source_user_message=user_message[:2000],
                source_assistant_message=assistant_message[:2000],
            )
            log.info(
                "Error card created for support %s (user %s): %s",
                support_id, user_id, card.concept,
            )
            created.append(card)

        return created

    def list_cards(self, support_id: str, user_id: str) -> List[ErrorCard]:
        """List all error cards for a support, scoped to the user."""
        return self.repo.list_by_support(support_id, user_id)

    def delete_card(self, card_id: str, user_id: str) -> bool:
        """Delete a card if it belongs to the user. Returns True on success."""
        return self.repo.delete_for_user(card_id, user_id)

    # ---------- Helpers ----------

    @staticmethod
    def _extract_json(text: str) -> Optional[dict]:
        """Tolerant JSON extraction: handles raw JSON, markdown fences, and prose."""
        if not text:
            return None
        text = text.strip()

        # Remove markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract the first {...} block
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return None
