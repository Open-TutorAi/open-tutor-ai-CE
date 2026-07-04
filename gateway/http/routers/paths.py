"""Learning paths generation routes - using requests."""

import json
import re
from json_repair import repair_json
import logging
from typing import Any, Dict

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user

log = logging.getLogger(__name__)

router = APIRouter(prefix="/paths", tags=["paths"])

OLLAMA_BASE_URL = "http://127.0.0.1:11434"


@router.post("/generate")
async def generate_learning_path(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Generate a personalized learning path using Ollama AI."""
    subject = body.get("subject", "")
    level = body.get("level", "Débutant")
    objective = body.get("objective", "Comprendre les bases")

    if not subject:
        raise HTTPException(status_code=400, detail="Subject is required")

    # Build the prompt for the AI
    prompt = f"""Tu es un expert pédagogique. Crée un cours complet et détaillé.

**Sujet** : {subject}
**Niveau** : {level}  
**Objectif** : {objective}

Crée 3 chapitres progressifs avec du contenu RICHE et DÉTAILLÉ (explications claires, exemples concrets, cas pratiques).

Format JSON strict :
{{
    "title": "Titre du cours",
    "description": "Description en 2-3 phrases",
    "chapters": [
        {{
            "id": 1,
            "title": "Titre chapitre 1",
            "introduction": "2-3 phrases d'intro",
            "content": "Contenu détaillé avec explications, exemples, cas pratiques (plusieurs paragraphes)",
            "summary": "Résumé en 2-3 phrases",
            "quiz": [
                {{"question": "Question ?", "options": ["A", "B", "C", "D"], "correct": 0}}
            ]
        }}
    ]
}}

Règles :
- Contenu pédagogique de qualité (explications claires, exemples concrets)
- 3-5 questions de quiz pertinentes par chapitre
- Réponds UNIQUEMENT avec le JSON, rien d'autre"""


    # Call Ollama directly using requests
    try:
        log.info(f"Calling Ollama at {OLLAMA_BASE_URL}/api/generate")
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            },
            timeout=600
        )
        
        log.info(f"Ollama response status: {response.status_code}")
        
        if response.status_code != 200:
            log.error(f"Ollama error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail=f"Ollama error: {response.status_code}")
        
        data = response.json()
        content = data.get("response", "")
        
        log.info(f"Ollama raw response length: {len(content)}")
        
                # Clean up the response using Regex to find the JSON block
                # Clean up the response using Regex to find the JSON block
        try:
            # Find the first { and the last }
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                json_str = content
		            # Log pour debug
            log.info(f"JSON brut reçu (premiers 2000 chars): {json_str[:2000]}")
            log.info(f"JSON brut (derniers 500 chars): {json_str[-500:]}")
                        # Utiliser json_repair pour réparer le JSON cassé
            repaired = repair_json(json_str, return_objects=True)
            
            if repaired is None:
                raise ValueError("Impossible de réparer le JSON")
            
            # Si c'est un tableau, extraire le premier élément
            if isinstance(repaired, list) and len(repaired) > 0:
                path_data = repaired[0]
            else:
                path_data = repaired
            
            # Vérifier que la structure est correcte
            if not isinstance(path_data, dict):
                raise ValueError("Le parcours doit être un objet JSON")
            
            if 'title' not in path_data or 'chapters' not in path_data:
                raise ValueError("Structure JSON invalide: title et chapters requis")

            log.info("Successfully parsed learning path JSON")
            return {"success": True, "path": path_data}
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse JSON: {e}")
	                # Sauvegarder la réponse complète pour analyse
            with open('/tmp/ai_raw_response.txt', 'w', encoding='utf-8') as f:
                f.write(json_str)
            log.error(f"Réponse complète sauvegardée dans /tmp/ai_raw_response.txt")
            log.error(f"Raw response (first 1000 chars): {content[:1000]}")
            log.error(f"Raw response (last 500 chars): {content[-500:]}")
            raise HTTPException(status_code=500, detail="AI response was not valid JSON")
            
    except requests.exceptions.RequestException as e:
        log.error(f"Failed to connect to Ollama: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to Ollama: {str(e)}")
    except Exception as e:
        log.error(f"Error generating learning path: {e}")
        raise HTTPException(status_code=500, detail=str(e))
