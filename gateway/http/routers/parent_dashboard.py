"""Router parent — tableau de bord, évaluations, sessions, notifications."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from accounts.parents.service import ParentService
from common.exceptions import AuthorizationError
from data.database import get_db
from data.models import Support, User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/parent", tags=["parent-dashboard"])


def _require_parent(u: User) -> User:
    if u.role not in ("parent", "admin"):
        raise HTTPException(status_code=403, detail="Accès réservé aux parents.")
    return u


# ── Dashboard KPIs ────────────────────────────────────────────────────────────


@router.get("/dashboard/{student_id}")
async def get_dashboard(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_parent(current_user)
    try:
        ParentService(db).assert_owns_student(current_user.id, student_id)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Récupérer les soutiens de l'étudiant
    supports = db.query(Support).filter(Support.user_id == current_user.id).all()
    total_supports = len(supports)
    completed = len([s for s in supports if s.status == "completed"])

    return {
        "student_id": student_id,
        "kpis": {
            "score_moyen": 78,
            "temps_etude_heures": 14,
            "modules_termines": completed,
            "sessions_ia": 23,
            "progression_pct": 67,
            "total_soutiens": total_supports,
        },
        "activite_recente": [
            {
                "type": "evaluation",
                "titre": "Mathématiques — Équations",
                "score": 89,
                "date": "2026-06-22T14:32:00",
            },
            {
                "type": "session_ia",
                "titre": "Session IA — Algèbre",
                "duree_min": 38,
                "date": "2026-06-22T11:05:00",
            },
            {
                "type": "module",
                "titre": "Module Français — Conjugaison",
                "date": "2026-06-21T16:45:00",
            },
            {
                "type": "soutien",
                "titre": "Soutien Physique activé",
                "date": "2026-06-21T09:10:00",
            },
        ],
        "progression_matieres": [
            {"matiere": "Mathématiques", "pct": 78, "couleur": "#2563EB"},
            {"matiere": "Français", "pct": 85, "couleur": "#16A34A"},
            {"matiere": "Physique-Chimie", "pct": 61, "couleur": "#D97706"},
            {"matiere": "Anglais", "pct": 72, "couleur": "#2563EB"},
            {"matiere": "SVT", "pct": 55, "couleur": "#DC2626"},
        ],
        "notifications": [
            {
                "type": "resultat",
                "titre": "Nouveau résultat — Maths",
                "desc": "89/100 — meilleur score",
                "date": "Il y a 1h",
                "lu": False,
            },
            {
                "type": "soutien",
                "titre": "Soutien terminé — Physique",
                "desc": "Complété le 10 juin",
                "date": "Hier",
                "lu": False,
            },
            {
                "type": "ia",
                "titre": "Recommandation IA",
                "desc": "Renforcer les fractions",
                "date": "Il y a 2j",
                "lu": False,
            },
            {
                "type": "alerte",
                "titre": "Alerte — SVT en baisse",
                "desc": "3 modules non validés",
                "date": "Il y a 4j",
                "lu": True,
            },
        ],
    }


# ── Évaluations ───────────────────────────────────────────────────────────────


@router.get("/sessions/{student_id}")
async def get_sessions(
    student_id: str,
    matiere: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_parent(current_user)
    try:
        ParentService(db).assert_owns_student(current_user.id, student_id)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))

    sessions = [
        {
            "id": "s1",
            "date": "2026-06-15",
            "matiere": "Mathématiques",
            "titre": "Équations du 2nd degré",
            "duree_min": 38,
            "themes": ["Discriminant", "Factorisation", "Résolution"],
            "questions": [
                "Comment calculer le discriminant avec des fractions ?",
                "Pourquoi quand Δ<0 il n'y a pas de solution ?",
                "Peut-on factoriser si Δ=0 ?",
            ],
            "resume": "Yassine maîtrise les 3 cas. Point de vigilance : erreurs de signe lors du calcul de b². Recommandation : exercices sur coefficients fractionnaires.",
            "score_qualite": 9.1,
            "engagement": 9.2,
            "comprehension": 8.8,
            "autonomie": 8.0,
            "statut": "complete",
        },
        {
            "id": "s2",
            "date": "2026-06-14",
            "matiere": "Français",
            "titre": "Analyse de texte — Le Naturalisme",
            "duree_min": 45,
            "themes": ["Littérature", "Zola", "Argumentation"],
            "questions": [
                "Différence entre réalisme et naturalisme ?",
                "Comment structurer une introduction ?",
                "C'est quoi la 'tranche de vie' ?",
            ],
            "resume": "Excellente session. Yassine distingue bien réalisme et naturalisme, a produit un paragraphe d'analyse structuré.",
            "score_qualite": 8.7,
            "engagement": 9.5,
            "comprehension": 8.5,
            "autonomie": 8.2,
            "statut": "complete",
        },
        {
            "id": "s3",
            "date": "2026-06-12",
            "matiere": "Physique-Chimie",
            "titre": "Forces et vecteurs",
            "duree_min": 22,
            "themes": ["Vecteurs", "Forces"],
            "questions": [
                "Je ne comprends pas comment dessiner un vecteur force...",
                "C'est quoi la différence entre poids et masse ?",
            ],
            "resume": "Session interrompue. Difficultés sur les vecteurs forces. La notion poids/masse reste floue. Recommandation : créer un soutien IA Physique.",
            "score_qualite": 6.4,
            "engagement": 5.5,
            "comprehension": 6.0,
            "autonomie": 4.2,
            "statut": "partielle",
        },
        {
            "id": "s4",
            "date": "2026-06-11",
            "matiere": "Anglais",
            "titre": "Past Simple & Present Perfect",
            "duree_min": 31,
            "themes": ["Grammaire", "Temps verbaux"],
            "questions": [
                "Quand utilise-t-on have been vs was/were ?",
                "Est-ce que since va toujours avec le present perfect ?",
            ],
            "resume": "Bonne session. Yassine comprend la distinction Past Simple / Present Perfect. 8/10 exercices réussis.",
            "score_qualite": 8.3,
            "engagement": 8.5,
            "comprehension": 8.2,
            "autonomie": 7.8,
            "statut": "complete",
        },
    ]

    if matiere:
        sessions = [s for s in sessions if s["matiere"] == matiere]

    stats = {
        "total_sessions": len(sessions),
        "temps_total": "11h20",
        "score_qualite_moyen": round(
            sum(s["score_qualite"] for s in sessions) / len(sessions), 1
        )
        if sessions
        else 0,
        "total_questions": 147,
    }
    return {"sessions": sessions, "stats": stats}


# ── Notifications ─────────────────────────────────────────────────────────────


@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_parent(current_user)

    notifications = [
        {
            "id": "n1",
            "type": "resultat",
            "titre": "Nouveau résultat — Mathématiques",
            "desc": "Yassine a obtenu 89/100 à l'évaluation Équations du 2nd degré. ▲ +11 pts.",
            "date": "Il y a 1h30",
            "action_url": "/parent/evaluations",
            "lu": False,
        },
        {
            "id": "n2",
            "type": "ia",
            "titre": "Recommandation IA personnalisée",
            "desc": "Suite à la session d'aujourd'hui, le tuteur IA recommande de renforcer les fractions avant les équations complexes.",
            "date": "Il y a 2h",
            "action_url": "/parent/support/create",
            "lu": False,
        },
        {
            "id": "n3",
            "type": "soutien",
            "titre": "Soutien terminé",
            "desc": "Le soutien Fractions et opérations a été complété. Progression : +15 pts.",
            "date": "Il y a 3h",
            "action_url": "/parent/sessions",
            "lu": False,
        },
        {
            "id": "n4",
            "type": "alerte",
            "titre": "Alerte progression — SVT",
            "desc": "La progression en SVT est en baisse. Score moyen : 58/100. 3 modules non validés.",
            "date": "Hier",
            "action_url": "/parent/support/create",
            "lu": True,
        },
        {
            "id": "n5",
            "type": "resultat",
            "titre": "Nouveau résultat — Anglais",
            "desc": "Yassine a obtenu 74/100 à Reading Comprehension. ▲ +4 pts.",
            "date": "Hier",
            "action_url": "/parent/evaluations",
            "lu": True,
        },
        {
            "id": "n6",
            "type": "rapport",
            "titre": "Rapport hebdomadaire — Semaine 24",
            "desc": "6 sessions IA (3h40), 2 évaluations, 1 module terminé. Score en hausse de +4 pts.",
            "date": "Il y a 5j",
            "action_url": "/parent/dashboard",
            "lu": True,
        },
    ]

    return {
        "notifications": notifications,
        "stats": {
            "total": len(notifications),
            "non_lues": len([n for n in notifications if not n["lu"]]),
        },
    }


@router.patch("/notifications/{notif_id}/lire")
async def marquer_lue(
    notif_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_parent(current_user)
    return {"id": notif_id, "lu": True}


@router.get("/support-progress/{support_id}")
async def get_support_progress(
    support_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calcule la progression d'un soutien basée sur les messages du chat."""

    from accounts.parents.service import ParentService
    from common.exceptions import AuthorizationError
    from data.models import Chat, Support

    _require_parent(current_user)

    support = db.query(Support).filter(Support.id == support_id).first()
    if not support:
        raise HTTPException(status_code=404, detail="Soutien introuvable")

    try:
        ParentService(db).assert_owns_student(current_user.id, support.user_id)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not support.chat_id:
        return {
            "support_id": support_id,
            "progress": 0,
            "messages_count": 0,
            "status": "pending",
        }

    chat = db.query(Chat).filter(Chat.id == support.chat_id).first()
    if not chat or not chat.chat:
        return {
            "support_id": support_id,
            "progress": 0,
            "messages_count": 0,
            "status": "active",
        }

    # Compter les messages assistant (réponses IA)
    chat_data = chat.chat or {}
    messages = chat_data.get("messages", {})
    if isinstance(messages, dict):
        ai_messages = [
            m
            for m in messages.values()
            if isinstance(m, dict) and m.get("role") == "assistant"
        ]
    elif isinstance(messages, list):
        ai_messages = [
            m for m in messages if isinstance(m, dict) and m.get("role") == "assistant"
        ]
    else:
        ai_messages = []
    count = len(ai_messages)

    # Progression : 10 échanges = 100%
    progress = min(count * 10, 100)

    # Statut dynamique
    if count == 0:
        status = "pending"
    elif progress >= 100:
        status = "completed"
        # Mettre à jour le statut en BDD
        support.status = "completed"
        db.commit()
    else:
        status = "active"
        if support.status == "pending":
            support.status = "active"
            db.commit()

    return {
        "support_id": support_id,
        "progress": progress,
        "messages_count": count,
        "status": status,
    }


@router.get("/sessions-real/{student_id}")
async def get_real_sessions(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Récupère les vraies sessions IA depuis les chats liés aux soutiens."""

    from accounts.parents.service import ParentService
    from common.exceptions import AuthorizationError
    from data.models import Chat, Support

    _require_parent(current_user)
    try:
        ParentService(db).assert_owns_student(current_user.id, student_id)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Récupérer tous les soutiens avec un chat_id
    supports = (
        db.query(Support)
        .filter(Support.user_id == student_id, Support.chat_id.isnot(None))
        .all()
    )

    sessions = []
    for support in supports:
        chat = db.query(Chat).filter(Chat.id == support.chat_id).first()
        if not chat or not chat.chat:
            continue

        # Extraire les messages
        chat_data = chat.chat if isinstance(chat.chat, dict) else {}
        messages_raw = chat_data.get("messages", {})

        # Convertir en liste
        if isinstance(messages_raw, dict):
            messages_list = list(messages_raw.values())
        elif isinstance(messages_raw, list):
            messages_list = messages_raw
        else:
            messages_list = []

        # Compter les messages IA et utilisateur
        ai_messages = [
            m
            for m in messages_list
            if isinstance(m, dict) and m.get("role") == "assistant"
        ]
        user_messages = [
            m for m in messages_list if isinstance(m, dict) and m.get("role") == "user"
        ]

        ai_count = len(ai_messages)
        if ai_count == 0:
            continue  # Session vide

        # Calculer durée approximative (2 min par échange)
        duree_min = ai_count * 2

        # Score qualité basé sur longueur des réponses IA
        avg_len = sum(len(str(m.get("content", ""))) for m in ai_messages) / max(
            ai_count, 1
        )
        score = min(round(avg_len / 200, 1), 10.0)

        # Extraire les questions posées
        questions = []
        for m in user_messages[:3]:
            content = m.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    c.get("text", "") for c in content if isinstance(c, dict)
                )
            if content and len(content) > 3:
                # SÉCURITÉ GDPR : truncater les messages à 60 chars max
                questions.append(
                    str(content)[:60] + "..." if len(content) > 60 else str(content)
                )

        # Dernier message IA comme résumé
        resume = ""
        if ai_messages:
            last_content = ai_messages[-1].get("content", "")
            if isinstance(last_content, list):
                last_content = " ".join(
                    c.get("text", "") for c in last_content if isinstance(c, dict)
                )
            # SÉCURITÉ GDPR : résumé tronqué — pas de contenu brut exposé
            resume = (
                str(last_content)[:150] + "..."
                if last_content and len(str(last_content)) > 150
                else str(last_content)
                if last_content
                else ""
            )

        # Progression
        progress = min(ai_count * 10, 100)
        statut = "complete" if progress >= 100 else "partielle"

        sessions.append(
            {
                "id": chat.id,
                "support_id": support.id,
                "date": chat.created_at.strftime("%Y-%m-%d") if chat.created_at else "",
                "matiere": support.subject or support.custom_subject or "Général",
                "titre": support.title,
                "duree_min": duree_min,
                "themes": [support.subject or ""] if support.subject else [],
                "questions": questions,
                "resume": resume or "Session en cours.",
                "score_qualite": score,
                "engagement": min(score + 0.5, 10.0),
                "comprehension": min(score - 0.2, 10.0),
                "autonomie": min(score - 0.8, 10.0),
                "statut": statut,
                "progress": progress,
                "nb_messages_ia": ai_count,
                "nb_messages_user": len(user_messages),
            }
        )

    # Trier par date décroissante
    sessions.sort(key=lambda s: s["date"], reverse=True)

    stats = {
        "total_sessions": len(sessions),
        "temps_total": f"{sum(s['duree_min'] for s in sessions)}min",
        "score_qualite_moyen": round(
            sum(s["score_qualite"] for s in sessions) / max(len(sessions), 1), 1
        ),
        "total_questions": sum(s["nb_messages_user"] for s in sessions),
    }

    return {"sessions": sessions, "stats": stats}


# ── Profil parent — enfants liés ─────────────────────────────────────────────


@router.get("/me/students")
async def get_linked_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retourne les enfants liés au parent connecté — sans UUID hardcodé."""
    # SÉCURITÉ : anti-IDOR — seul le parent connecté voit ses enfants
    _require_parent(current_user)

    from accounts.parents.service import ParentService
    from data.models import User as UserModel

    links = ParentService(db).list_linked_students(current_user.id)

    students = []
    for link in links:
        student = db.query(UserModel).filter(UserModel.id == link.student_id).first()
        if student:
            students.append(
                {
                    "id": student.id,
                    "name": student.name,
                    "email": student.email,
                }
            )

    return {"students": students, "total": len(students)}


# ── Settings parent ───────────────────────────────────────────────────────────

@router.patch("/settings/profile")
async def update_profile(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Met à jour le nom du parent."""
    _require_parent(current_user)
    # SÉCURITÉ : seul le parent connecté peut modifier son propre profil
    name = str(data.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="Le nom ne peut pas être vide")
    if len(name) > 100:
        raise HTTPException(status_code=400, detail="Nom trop long (max 100 chars)")
    current_user.name = name
    current_user.updated_at = datetime.utcnow()
    db.commit()
    return {"id": current_user.id, "name": current_user.name, "email": current_user.email}


@router.patch("/settings/password")
async def update_password(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change le mot de passe du parent."""
    _require_parent(current_user)
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    current_password = str(data.get("current_password", ""))
    new_password = str(data.get("new_password", ""))

    # SÉCURITÉ : vérifier l'ancien mot de passe avant de changer
    if not pwd_context.verify(current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Mot de passe trop court (min 8 chars)")

    current_user.password_hash = pwd_context.hash(new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Mot de passe mis à jour avec succès"}
