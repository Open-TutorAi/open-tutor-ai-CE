"""Flashcard generation service using LLM providers."""

import json
import logging
import re
import time
from typing import List
from config import settings

log = logging.getLogger(__name__)


class FlashcardGenerator:
    STOP_WORDS = {
        'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'à', 'en', 'et',
        'ou', 'mais', 'donc', 'or', 'ni', 'car', 'que', 'qui', 'quoi', 'dont',
        'ce', 'cet', 'cette', 'ces', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes',
        'son', 'sa', 'ses', 'notre', 'votre', 'leur', 'leurs', 'je', 'tu',
        'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'est', 'sont', 'été',
        'avoir', 'être', 'faire', 'dire', 'aller', 'voir', 'savoir', 'pouvoir',
        'vouloir', 'dans', 'sur', 'sous', 'avec', 'sans', 'pour', 'par'
    }
    
    def __init__(self, model_name: str = None):
        self.ollama_url = getattr(
            settings, 
            'OLLAMA_BASE_URL', 
            getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434')
        )
        self.model = model_name or "qwen2.5:7b"
        log.info(f"🎯 FlashcardGenerator: modèle={self.model}")

    def _preprocess_text(self, text: str, max_chars: int = 2000) -> str:
        """Pré-traite le texte"""
        if not text:
            return ""
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        meaningful = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        processed = ' '.join(meaningful)
        
        if len(processed) > max_chars:
            processed = processed[:max_chars]
            last_space = processed.rfind(' ')
            if last_space > max_chars - 100:
                processed = processed[:last_space]
        
        return processed.strip()

    def _validate_answer_in_text(self, answer: str, text: str) -> bool:
        """Vérifie que la réponse est bien dans le texte original"""
        if not answer or not text:
            return False
        
        answer_norm = answer.lower().strip()
        text_norm = text.lower()
        
        answer_words = answer_norm.split()
        matches = sum(1 for word in answer_words if word in text_norm)
        
        return matches / len(answer_words) >= 0.7 if answer_words else False

    async def _reset_context(self):
        """🧹 VIDE COMPLÈTEMENT le contexte d'Ollama"""
        try:
            import httpx
            log.info("🧹 Reset du contexte Ollama...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Appel avec context=[] force le reset
                await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": ".",
                        "stream": False,
                        "context": [],  # ⚡ CRITIQUE : Vide le contexte
                        "options": {"num_predict": 1}
                    }
                )
            log.info("✅ Contexte Ollama vidé")
        except Exception as e:
            log.warning(f"⚠️ Reset échoué (non critique): {e}")

    async def generate_from_content(self, content: str, num_cards: int = 5) -> List[dict]:
        log.info("=" * 60)
        log.info("🚀 generate_from_content")
        log.info(f"Texte reçu: {len(content)} caractères")
        
        # 🧹 RESET DU CONTEXTE AVANT CHAQUE GÉNÉRATION
        await self._reset_context()
        
        processed = self._preprocess_text(content)
        log.info(f"Texte traité: {len(processed)} caractères")
        
        if len(processed) < 100:
            log.warning("⚠️ Texte trop court, fallback")
            return self._create_fallback_cards(content, num_cards)
        
        # Générer un ID unique pour cette session
        session_id = f"SESSION_{int(time.time())}_{num_cards}"
        
        # Prompt ULTRA STRICT avec marqueur de session
        prompt = f"""[NOUVELLE_SESSION: {session_id}]
IGNORE TOUTE CONVERSATION PRÉCÉDENTE.
TA SEULE SOURCE D'INFORMATION EST LE TEXTE CI-DESSOUS.

Tu es un générateur de quiz. Ta tâche est CRITIQUE :

CONTRAINTE ABSOLUE : Tu ne dois utiliser QUE les informations EXPLICITEMENT présentes dans le texte ci-dessous.
INTERDIT : Inventer, deviner, ou ajouter des informations externes.

TEXTE SOURCE (ta SEULE source d'information) :
---
{processed}
---

Génère EXACTEMENT {num_cards} questions de quiz.

RÈGLES STRICTES :
1. Chaque question DOIT porter sur un fait EXPLICITE du texte
2. La réponse DOIT être un mot ou expression du texte (1-4 mots)
3. Si tu ne trouves pas assez de faits, génère moins de questions
4. INTERDIT de mentionner des concepts externes

FORMAT DE RÉPONSE (JSON uniquement) :
[
  {{"question": "Question basée UNIQUEMENT sur le texte ?", "answer": "mot/expression du texte"}},
  {{"question": "Autre question du texte ?", "answer": "autre mot du texte"}}
]

RÉPONDS UNIQUEMENT AVEC LE JSON :"""

        try:
            import httpx
            
            log.info(f"📡 Appel Ollama ({self.model}) - Session: {session_id}")
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "context": [],  # ⚡ CRITIQUE : Force le reset du contexte
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.8,
                            "num_predict": 800,
                            "num_ctx": 2048  # Limite le contexte à 2048 tokens
                        }
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                text = result.get("response", "").strip()
                
                log.info(f"✅ Réponse reçue ({len(text)} chars)")
                log.info(f"Début: {text[:300]}")
                
                # Nettoyage
                text = text.replace("```json", "").replace("```", "").strip()
                match = re.search(r'\[[\s\S]*\]', text)
                
                if match:
                    cards = json.loads(match.group())
                    log.info(f"📦 JSON parsé: {len(cards)} cartes")
                    
                    # VALIDATION STRICTE
                    valid_cards = []
                    for card in cards:
                        q = card.get("question", "").strip()
                        a = self._clean_answer(card.get("answer", ""))
                        
                        if q and a and len(a) <= 50 and len(q) > 10:
                            if self._validate_answer_in_text(a, content):
                                valid_cards.append({"question": q, "answer": a})
                                log.info(f"✅ Carte validée: Q={q[:50]}... R={a}")
                            else:
                                log.warning(f"❌ Carte REJETÉE: Q={q[:50]}... R={a}")
                    
                    if len(valid_cards) >= 2:
                        log.info(f"✅ {len(valid_cards)} cartes valides")
                        log.info("=" * 60)
                        return valid_cards[:num_cards]
                    else:
                        log.warning(f"⚠️ Seulement {len(valid_cards)} valides, fallback")
                else:
                    log.error("❌ Pas de JSON trouvé")
                
        except Exception as e:
            log.error(f"❌ Erreur IA: {e}", exc_info=True)
        
        log.info("🔄 Fallback intelligent")
        result = self._create_fallback_cards(content, num_cards)
        log.info("=" * 60)
        return result
    
    def _clean_answer(self, answer: str) -> str:
        if not answer:
            return ""
        cleaned = answer.lower().strip()
        cleaned = re.sub(r'[.,!?;:\'"()\-\/\\]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'^(le|la|les|un|une|des|de|du|à|en|pour|sur|avec|sans)\s+', '', cleaned)
        words = cleaned.split()
        return " ".join(words[:4])
    
    def _create_fallback_cards(self, content: str, num_cards: int) -> List[dict]:
        """Fallback intelligent"""
        log.info(f"🔧 FALLBACK: {len(content)} caractères")
        
        content = re.sub(r'\s+', ' ', content).strip()
        sentences = re.split(r'(?<=[.!?])\s+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return [{"question": "Erreur", "answer": "texte trop court"}]
        
        cards = []
        used = set()
        
        # 1. Définitions "X est Y"
        for sentence in sentences:
            if len(cards) >= num_cards:
                break
            match = re.search(
                r'([A-ZÀ-Ý][a-zà-ÿ\s]{3,30})\s+(?:est|sont|représente)\s+(.+?)(?:\.|$)',
                sentence
            )
            if match:
                concept = match.group(1).strip()
                definition = match.group(2).strip()
                if concept.lower() not in used and len(concept) > 3:
                    cards.append({
                        "question": f"Qu'est-ce que '{concept}' ?",
                        "answer": self._clean_answer(definition[:60])
                    })
                    used.add(concept.lower())
        
        # 2. Étymologies
        for sentence in sentences:
            if len(cards) >= num_cards:
                break
            match = re.search(
                r'([A-ZÀ-Ý][a-zà-ÿ]{3,20})\s*\([^:]+:\s*([^)]+)\)',
                sentence
            )
            if match:
                concept = match.group(1).strip()
                meaning = match.group(2).strip()
                if concept.lower() not in used:
                    cards.append({
                        "question": f"Que signifie '{concept}' ?",
                        "answer": self._clean_answer(meaning[:50])
                    })
                    used.add(concept.lower())
        
        # 3. Concepts importants
        for sentence in sentences:
            if len(cards) >= num_cards:
                break
            words = re.findall(r'\b[A-ZÀ-Ý][a-zà-ÿ]{5,}\b', sentence)
            for word in words:
                if len(cards) >= num_cards:
                    break
                if word.lower() not in self.STOP_WORDS and word.lower() not in used:
                    cards.append({
                        "question": f"Quel est le rôle de '{word}' ?",
                        "answer": self._clean_answer(sentence[:60])
                    })
                    used.add(word.lower())
        
        # 4. Phrases à trous
        if len(cards) < num_cards:
            for sentence in sentences:
                if len(cards) >= num_cards:
                    break
                words = sentence.split()
                important = [w for w in words if len(w) > 6 and w.lower() not in self.STOP_WORDS]
                if important:
                    hidden = important[0]
                    masked = sentence.replace(hidden, "_____", 1)
                    if len(masked) < 100:
                        cards.append({
                            "question": f"Complétez : {masked}",
                            "answer": self._clean_answer(hidden)
                        })
        
        log.info(f"✅ FALLBACK: {len(cards)} cartes")
        for i, c in enumerate(cards):
            log.info(f"  {i+1}. Q: {c['question'][:50]}... R: {c['answer']}")
        
        return cards[:num_cards]
