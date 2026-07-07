"""Router parent — /parent/evaluations/*
Génération et correction de QCM par l'IA depuis les sessions de chat.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from accounts.parents.service import ParentService
from common.exceptions import AuthorizationError
from data.database import get_db
from data.models import Chat, Support, User
from data.models.evaluation import Evaluation
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/parent/evaluations", tags=["parent-evaluations"])


def _require_parent(u: User) -> User:
    if u.role not in ("parent", "admin"):
        raise HTTPException(status_code=403, detail="Accès réservé aux parents.")
    return u


# ── Génération QCM par l'IA ───────────────────────────────────────────────────


async def generate_qcm_with_ai(
    chat_content: str, subject: str, title: str
) -> List[Dict]:
    """Génère 10 QCM en 2 étapes pour garantir la qualité."""

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # ── ÉTAPE 1 : Extraire les faits clés de la conversation ──────────────────
    prompt_extract = f"""Lis cette conversation entre un élève et un tuteur IA sur le sujet: {subject} / {title}

CONVERSATION:
{chat_content[:3500]}

Liste les 10 points/faits importants appris dans cette conversation.
Format: une ligne par point, numéroté de 1 à 10.
Ne mets que les faits, pas de commentaires."""

    facts = []
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": "gemma3:4b",
                    "prompt": prompt_extract,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 800},
                },
            )
            r.raise_for_status()
            facts_text = r.json().get("response", "")
            print(f"[QCM] Faits extraits: {facts_text[:200]}")
            # Parser les faits numérotés
            for line in facts_text.strip().split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    fact = line.lstrip("0123456789.-) ").strip()
                    if len(fact) > 10:
                        facts.append(fact)
    except Exception as e:
        print(f"[QCM] Erreur extraction faits: {e}")

    if not facts:
        # Utiliser directement le contenu de la conversation comme base
        facts = [
            chat_content[i : i + 200]
            for i in range(0, min(len(chat_content), 2000), 200)
        ]

    # ── ÉTAPE 2 : Générer un QCM par fait ─────────────────────────────────────
    questions = []
    facts_to_use = facts[:10]

    for i, fact in enumerate(facts_to_use):
        prompt_qcm = f"""Sur la base de ce fait appris en cours de {subject}:
"{fact}"

Génère UNE question QCM avec 4 choix (A, B, C, D).
Réponds UNIQUEMENT avec ce format JSON exact, une seule ligne:
{{"question": "...", "A": "...", "B": "...", "C": "...", "D": "...", "correct": "A", "explanation": "..."}}"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": "gemma3:4b",
                        "prompt": prompt_qcm,
                        "stream": False,
                        "options": {"temperature": 0.3, "num_predict": 300},
                    },
                )
                r.raise_for_status()
                raw = r.json().get("response", "").strip()
                print(f"[QCM Q{i+1}] raw: {raw[:150]}")

                # Extraire le JSON de la réponse
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start >= 0 and end > start:
                    q_data = json.loads(raw[start:end])
                    # Construire les choices
                    choices = {
                        "A": str(q_data.get("A", "Option A")),
                        "B": str(q_data.get("B", "Option B")),
                        "C": str(q_data.get("C", "Option C")),
                        "D": str(q_data.get("D", "Option D")),
                    }
                    correct = str(q_data.get("correct", "A")).strip().upper()
                    if correct not in ("A", "B", "C", "D"):
                        correct = "A"

                    questions.append(
                        {
                            "id": len(questions) + 1,
                            "question": str(
                                q_data.get("question", f"Question sur {fact[:50]}")
                            ),
                            "choices": choices,
                            "correct": correct,
                            "explanation": str(q_data.get("explanation", fact[:100])),
                        }
                    )
        except Exception as e:
            print(f"[QCM Q{i+1}] Erreur: {e}")
            # Question de secours basée sur le fait
            questions.append(
                {
                    "id": len(questions) + 1,
                    "question": f"Concernant {subject}: {fact[:80]}..., quelle affirmation est correcte ?",
                    "choices": {
                        "A": fact[:60],
                        "B": "Aucune des réponses",
                        "C": "Toutes les réponses",
                        "D": "Cela dépend du contexte",
                    },
                    "correct": "A",
                    "explanation": fact[:150],
                }
            )

    print(f"[QCM] Total: {len(questions)} questions générées")
    return (
        questions[:10]
        if questions
        else [
            {
                "id": 1,
                "question": "Quel est le sujet principal de cette session ?",
                "choices": {
                    "A": title,
                    "B": "Mathématiques",
                    "C": "Histoire",
                    "D": "Géographie",
                },
                "correct": "A",
                "explanation": f"Cette session portait sur: {title}",
            }
        ]
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


class GenerateEvalRequest(BaseModel):
    chat_id: str
    support_id: Optional[str] = None
    student_id: str


class SubmitAnswersRequest(BaseModel):
    answers: Dict[str, str]  # {"1": "A", "2": "C", ...}


@router.post("/generate")
async def generate_evaluation(
    data: GenerateEvalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Génère un QCM de 10 questions basé sur une session de chat."""
    _require_parent(current_user)

    # Vérifier liaison parent-enfant
    try:
        ParentService(db).assert_owns_student(current_user.id, data.student_id)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Récupérer le chat
    chat = db.query(Chat).filter(Chat.id == data.chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Session introuvable")

    # Récupérer le soutien pour avoir le titre et la matière
    support = None
    if data.support_id:
        support = db.query(Support).filter(Support.id == data.support_id).first()

    subject = support.subject if support else "Général"
    title = support.title if support else chat.title

    # Extraire le texte de la conversation
    chat_data = chat.chat if isinstance(chat.chat, dict) else {}
    messages_raw = chat_data.get("messages", {})
    if isinstance(messages_raw, dict):
        messages_list = list(messages_raw.values())
    else:
        messages_list = messages_raw if isinstance(messages_raw, list) else []

    conversation_text = ""
    for m in messages_list:
        if not isinstance(m, dict):
            continue
        role = m.get("role", "")
        content = m.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                c.get("text", "") for c in content if isinstance(c, dict)
            )
        if role == "user":
            conversation_text += f"Élève: {content}\n"
        elif role == "assistant":
            conversation_text += f"Tuteur: {content}\n"

    if len(conversation_text) < 50:
        raise HTTPException(
            status_code=400,
            detail="La session est trop courte pour générer une évaluation.",
        )

    # Générer les QCM avec l'IA
    questions = await generate_qcm_with_ai(conversation_text, subject, title)

    if not questions:
        raise HTTPException(
            status_code=500, detail="L'IA n'a pas pu générer les questions."
        )

    # Sauvegarder en BDD
    evaluation = Evaluation(
        id=str(uuid.uuid4()),
        created_by=current_user.id,
        student_id=data.student_id,
        support_id=data.support_id,
        chat_id=data.chat_id,
        title=f"Évaluation — {title}",
        subject=subject,
        questions=questions,
        status="pending",
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return evaluation.to_dict()


@router.get("/by-student/{student_id}")
async def list_evaluations(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste toutes les évaluations d'un enfant."""
    _require_parent(current_user)
    try:
        ParentService(db).assert_owns_student(current_user.id, student_id)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))

    evals = (
        db.query(Evaluation)
        .filter(Evaluation.student_id == student_id)
        .order_by(Evaluation.created_at.desc())
        .all()
    )

    return [e.to_dict() for e in evals]


@router.get("/{eval_id}")
async def get_evaluation(
    eval_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Récupère une évaluation (sans les bonnes réponses si pending)."""
    ev = db.query(Evaluation).filter(Evaluation.id == eval_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Évaluation introuvable")

    # Vérifier accès : créateur (parent) ou étudiant concerné
    if ev.created_by != current_user.id and ev.student_id != current_user.id:
        if current_user.role not in ("admin",):
            raise HTTPException(status_code=403, detail="Accès refusé")

    data = ev.to_dict()
    # Masquer les réponses correctes si l'évaluation n'est pas encore soumise
    if ev.status == "pending":
        for q in data.get("questions", []):
            q.pop("correct", None)
            q.pop("explanation", None)
    return data


@router.post("/{eval_id}/submit")
async def submit_answers(
    eval_id: str,
    body: SubmitAnswersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soumet les réponses et calcule la note automatiquement."""
    ev = db.query(Evaluation).filter(Evaluation.id == eval_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Évaluation introuvable")
    if ev.status == "completed":
        raise HTTPException(status_code=400, detail="Évaluation déjà soumise.")

    # Corriger automatiquement
    correct_count = 0
    results = []
    for q in ev.questions:
        q_id = str(q["id"])
        student_answer = body.answers.get(q_id, "")
        is_correct = student_answer.upper() == q["correct"].upper()
        if is_correct:
            correct_count += 1
        results.append(
            {
                **q,
                "student_answer": student_answer,
                "is_correct": is_correct,
            }
        )

    nb_total = len(ev.questions)
    score = round((correct_count / max(nb_total, 1)) * 100, 1)

    # Mettre à jour en BDD
    ev.student_answers = body.answers
    ev.score = score
    ev.nb_correct = correct_count
    ev.nb_total = nb_total
    ev.status = "completed"
    ev.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(ev)

    return {
        **ev.to_dict(),
        "results": results,
        "message": f"🎉 {correct_count}/{nb_total} correctes — Score : {score}/100",
    }
