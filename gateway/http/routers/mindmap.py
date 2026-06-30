"""Mindmap router — /api/v1/mindmap/*."""
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user
from learning.sessions.service import ChatsService
from ai.providers.service import ProvidersService, build_llm_body
from ai.providers.proxy import proxy_json
from fastapi.responses import StreamingResponse
import io

log = logging.getLogger(__name__)

router = APIRouter(prefix="/mindmap", tags=["mindmap"])


# ── Schemas ──────────────────────────────────────────────

class MindMapNode(BaseModel):
    id: str
    label: str
    type: str
    color: Optional[str] = "#6366f1"

class MindMapEdge(BaseModel):
    from_: str
    to: str

class VerifyRequest(BaseModel):
    chat_id: str
    nodes: List[MindMapNode]
    edges: List[MindMapEdge]


# ── Helper : extract chat messages ───────────────────────

def _extract_messages(chat: Any) -> List[Dict]:
    """Extract user/assistant messages from a Chat ORM object."""
    try:
        data = chat.chat or {}
        history = data.get("history", {})
        messages_map = history.get("messages", {})
        result = []
        for msg in messages_map.values():
            if msg.get("role") in ("user", "assistant"):
                result.append({
                    "role": msg["role"],
                    "content": msg.get("content", "")
                })
        return result
    except Exception:
        return []


def _build_conversation_text(messages: List[Dict]) -> str:
    """Build a readable conversation text from messages."""
    lines = []
    for m in messages:
        role = "Apprenant" if m["role"] == "user" else "Tuteur IA"
        lines.append(f"{role}: {m['content'][:300]}")
    return "\n".join(lines[-20:])  # last 20 messages


# ── GET /api/v1/mindmap/context/{chat_id} ────────────────

@router.get("/context/{chat_id}")
async def get_mindmap_context(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyse l'historique du chat et retourne :
    - Le titre du cours détecté
    - Les concepts clés abordés
    """
    svc = ChatsService(db)
    try:
        chat = svc.get(chat_id, current_user.id)
    except Exception:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = _extract_messages(chat)
    if not messages:
        return {
            "title": chat.title or "Ma session",
            "concepts": [],
            "chat_id": chat_id
        }

    conversation = _build_conversation_text(messages)
    chat_title = chat.title or "Session d'apprentissage"

    # Prompt pour extraire titre + concepts
    extraction_prompt = f"""Tu es un assistant pédagogique. 
Analyse cette conversation entre un apprenant et un tuteur IA.

CONVERSATION :
{conversation}

Réponds UNIQUEMENT en JSON valide avec ce format exact :
{{
  "title": "titre court du cours (max 5 mots)",
  "concepts": ["concept1", "concept2", "concept3", "concept4", "concept5"]
}}

Extrait entre 3 et 7 concepts clés abordés dans la conversation.
Ne mets rien d'autre que le JSON."""

    try:
        providers_svc = ProvidersService(db)
        # Get first available model
        models = await providers_svc.get_merged_models()
        if not models:
            raise HTTPException(status_code=503, detail="No LLM model available")

        model_id = models[0]["id"]
        base_url, api_key, path = await providers_svc.resolve_provider(model_id)

        body = {
            "model": model_id,
            "stream": False,
            "messages": [
                {"role": "user", "content": extraction_prompt}
            ],
            "temperature": 0.3
        }

        llm_body = build_llm_body(body)
        response = await proxy_json(base_url, api_key, "POST", path, body=llm_body)

        # Parse LLM response
        content = response.get("choices", [{}])[0].get(
            "message", {}
        ).get("content", "")

        # Extract JSON from response
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])
            return {
                "title": parsed.get("title", chat_title),
                "concepts": parsed.get("concepts", []),
                "chat_id": chat_id
            }

    except Exception as e:
        log.warning(f"LLM extraction failed: {e}")

    # Fallback sans LLM
    return {
        "title": chat_title,
        "concepts": [],
        "chat_id": chat_id
    }


# ── POST /api/v1/mindmap/verify ──────────────────────────

@router.post("/verify")
async def verify_mindmap(
    body: VerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Vérifie si la carte mentale couvre bien les concepts
    de la session de chat.
    """
    svc = ChatsService(db)
    try:
        chat = svc.get(body.chat_id, current_user.id)
    except Exception:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = _extract_messages(chat)
    conversation = _build_conversation_text(messages)

    # Concepts dans la carte de l'apprenant
    student_concepts = [
        n.label for n in body.nodes
        if n.type != "central"
    ]

    if not student_concepts:
        return {
            "status": "improve",
            "score": 0,
            "feedback": "Ta carte est vide ! Ajoute des concepts.",
            "missing_concepts": [],
            "covered_concepts": []
        }

    verification_prompt = f"""Tu es un agent pédagogique expert.

CONVERSATION DE LA SESSION :
{conversation}

CARTE MENTALE CRÉÉE PAR L'APPRENANT :
Concepts représentés : {", ".join(student_concepts)}

Évalue si la carte mentale couvre bien les concepts importants de la session.
Réponds UNIQUEMENT en JSON valide :
{{
  "score": 85,
  "covered_concepts": ["concept couvert 1", "concept couvert 2"],
  "missing_concepts": ["concept manquant 1", "concept manquant 2"],
  "feedback": "Message encourageant pour l'apprenant"
}}

Score de 0 à 100. Si score >= 70 la carte est bonne."""

    try:
        providers_svc = ProvidersService(db)
        models = await providers_svc.get_merged_models()
        if not models:
            raise HTTPException(status_code=503, detail="No LLM model available")

        model_id = models[0]["id"]
        base_url, api_key, path = await providers_svc.resolve_provider(model_id)

        body_llm = {
            "model": model_id,
            "stream": False,
            "messages": [
                {"role": "user", "content": verification_prompt}
            ],
            "temperature": 0.3
        }

        llm_body = build_llm_body(body_llm)
        response = await proxy_json(base_url, api_key, "POST", path, body=llm_body)

        content = response.get("choices", [{}])[0].get(
            "message", {}
        ).get("content", "")

        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])
            score = parsed.get("score", 0)
            return {
                "status": "success" if score >= 70 else "improve",
                "score": score,
                "feedback": parsed.get("feedback", ""),
                "covered_concepts": parsed.get("covered_concepts", []),
                "missing_concepts": parsed.get("missing_concepts", [])
            }

    except Exception as e:
        log.warning(f"LLM verification failed: {e}")

    # Fallback
    return {
        "status": "success" if len(student_concepts) >= 4 else "improve",
        "score": len(student_concepts) * 15,
        "feedback": "Bonne carte mentale !" if len(student_concepts) >= 4
                    else "Essaie d'ajouter plus de concepts.",
        "covered_concepts": student_concepts,
        "missing_concepts": []
    }
    from fastapi.responses import StreamingResponse
import io

class ExportRequest(BaseModel):
    nodes: List[MindMapNode]
    edges: List[MindMapEdge]
    title: str = "Carte Mentale"

@router.post("/export/pdf")
async def export_mindmap_pdf(
    body: ExportRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Génère un PDF de la carte mentale.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Titre
        story.append(Paragraph(f"<b>{body.title}</b>", styles['Title']))
        story.append(Spacer(1, 20))

        # Concepts
        story.append(Paragraph("<b>Concepts :</b>", styles['Heading2']))
        story.append(Spacer(1, 10))

        for node in body.nodes:
            if node.type != "central":
                story.append(Paragraph(f"• {node.label}", styles['Normal']))
                story.append(Spacer(1, 5))

        doc.build(story)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=mindmap.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ExportRequest(BaseModel):
    nodes: List[MindMapNode]
    edges: List[MindMapEdge]
    title: str = "Carte Mentale"

@router.post("/export/pdf")
async def export_mindmap_pdf(
    body: ExportRequest,
    current_user: User = Depends(get_current_user),
):
    """Génère un PDF de la carte mentale."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Titre principal
        story.append(Paragraph(f"<b>{body.title}</b>", styles['Title']))
        story.append(Spacer(1, 20))

        # Sous-titre
        story.append(Paragraph(
            "Carte mentale générée depuis votre session d'apprentissage",
            styles['Normal']
        ))
        story.append(Spacer(1, 20))

        # Nœud central
        central = next((n for n in body.nodes if n.type == "central"), None)
        if central:
            story.append(Paragraph(
                f"<b>Sujet principal :</b> {central.label}",
                styles['Heading2']
            ))
            story.append(Spacer(1, 15))

        # Concepts
        story.append(Paragraph("<b>Concepts étudiés :</b>", styles['Heading2']))
        story.append(Spacer(1, 10))

        concepts = [n for n in body.nodes if n.type != "central"]
        for i, node in enumerate(concepts, 1):
            story.append(Paragraph(
                f"{i}. {node.label}",
                styles['Normal']
            ))
            story.append(Spacer(1, 5))

        doc.build(story)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=mindmap.pdf"
            }
        )
    except Exception as e:
        log.error(f"PDF export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))