"""Router parent — /parent/supports/*

Permet à un utilisateur ayant le rôle 'parent' de créer un soutien
pour l'un de ses enfants liés, en s'appuyant sur les services existants.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from accounts.parents.service import ParentService
from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from config import settings
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user, get_supports_service
from learning.supports.service import SupportsService

router = APIRouter(prefix="/parent/supports", tags=["parent-supports"])


# ── Schémas Pydantic ─────────────────────────────────────────────────────────


class ParentSupportCreateRequest(BaseModel):
    """Données du formulaire de création de soutien côté parent."""

    student_id: str
    title: str
    short_description: Optional[str] = None
    subject: Optional[str] = None
    custom_subject: Optional[str] = None
    learning_objective: Optional[str] = None
    learning_type: Optional[str] = None
    level: Optional[str] = None
    content_language: Optional[str] = "French"
    estimated_duration: Optional[str] = None
    keywords: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    # Message personnel du parent affiché à l'enfant
    parent_message: Optional[str] = None


class SupportFileInfo(BaseModel):
    id: str
    filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None

    class Config:
        from_attributes = True


class ParentSupportResponse(BaseModel):
    id: str
    user_id: str  # = student_id (le soutien appartient à l'enfant)
    title: str
    short_description: Optional[str] = None
    subject: Optional[str] = None
    custom_subject: Optional[str] = None
    learning_objective: Optional[str] = None
    learning_type: Optional[str] = None
    level: Optional[str] = None
    content_language: Optional[str] = None
    estimated_duration: Optional[str] = None
    keywords: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str
    chat_id: Optional[str] = None
    files: List[SupportFileInfo] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def _require_parent(current_user: User) -> User:
    """Lève 403 si l'utilisateur n'a pas le rôle 'parent'."""
    if current_user.role not in ("parent", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux parents.",
        )
    return current_user


def _get_parent_service(db: Session = Depends(get_db)) -> ParentService:
    return ParentService(db)


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/create", response_model=ParentSupportResponse)
async def create_support_for_child(
    data: ParentSupportCreateRequest,
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
    db: Session = Depends(get_db),
):
    """
    Crée un soutien pour l'enfant lié (student_id).

    - Vérifie que l'utilisateur a le rôle 'parent'.
    - Vérifie qu'une liaison active existe entre ce parent et l'étudiant.
    - Délègue la création à SupportsService en rattachant le soutien à l'étudiant.
    """
    _require_parent(current_user)

    payload = data.model_dump(exclude={"student_id", "parent_message"})

    try:
        # SÉCURITÉ : soutien créé pour le parent lui-même — sans lien enfant requis
        support = svc.create(user_id=current_user.id, data=payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return ParentSupportResponse(
        id=support.id,
        user_id=support.user_id,
        title=support.title,
        short_description=support.short_description,
        subject=support.subject,
        custom_subject=support.custom_subject,
        learning_objective=support.learning_objective,
        learning_type=support.learning_type,
        level=support.level,
        content_language=support.content_language,
        estimated_duration=support.estimated_duration,
        keywords=support.keywords.split(",") if support.keywords else None,
        start_date=support.start_date,
        end_date=support.end_date,
        status=support.status,
        files=[],
        created_at=support.created_at,
        updated_at=support.updated_at,
    )


@router.post("/upload-file")
async def upload_file_for_child_support(
    request: Request,
    support_id: str = Form(...),
    student_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
    db: Session = Depends(get_db),
):
    """Upload un fichier pour un soutien de l'enfant."""
    _require_parent(current_user)

    # Vérifier que le parent est bien lié à cet étudiant
    parent_svc = ParentService(db)
    try:
        parent_svc.assert_owns_student(current_user.id, student_id)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    _too_large = HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"Fichier dépasse la limite de {settings.MAX_UPLOAD_SIZE_MB} Mo",
    )

    raw_cl = request.headers.get("content-length")
    if raw_cl and raw_cl.isdigit() and int(raw_cl) > max_bytes:
        raise _too_large

    contents = await file.read()
    if len(contents) > max_bytes:
        raise _too_large

    try:
        record = svc.upload_file(
            user_id=student_id,  # le fichier appartient à l'enfant
            support_id=support_id,
            filename=file.filename or "",
            content_type=file.content_type,
            contents=contents,
            upload_dir=settings.UPLOAD_DIR,
            max_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        )
    except (NotFoundError, AuthorizationError) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValidationError:
        raise _too_large

    return {"id": record.id, "filename": record.filename, "status": "success"}


@router.get("/list/{student_id}", response_model=List[ParentSupportResponse])
async def list_child_supports(
    student_id: str,
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
    db: Session = Depends(get_db),
):
    """Liste tous les soutiens créés pour un enfant lié."""
    _require_parent(current_user)

    parent_svc = ParentService(db)
    try:
        parent_svc.assert_owns_student(current_user.id, student_id)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    supports = svc.list_for_user(current_user.id)
    return [
        ParentSupportResponse(
            id=s.id,
            user_id=s.user_id,
            title=s.title,
            short_description=s.short_description,
            subject=s.subject,
            custom_subject=s.custom_subject,
            learning_objective=s.learning_objective,
            learning_type=s.learning_type,
            level=s.level,
            content_language=s.content_language,
            estimated_duration=s.estimated_duration,
            keywords=s.keywords.split(",") if s.keywords else None,
            start_date=s.start_date,
            end_date=s.end_date,
            status=s.status,
            chat_id=s.chat_id,
            files=[],
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in supports
    ]


@router.get("/detail/{support_id}")
async def get_child_support_detail(
    support_id: str,
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
    db: Session = Depends(get_db),
):
    """Récupère le détail d'un soutien de l'enfant (accès parent)."""
    _require_parent(current_user)

    # Récupérer le soutien
    from data.models import Support

    support = db.query(Support).filter(Support.id == support_id).first()
    if not support:
        raise HTTPException(status_code=404, detail="Soutien introuvable")

    # Vérifier que le parent est bien lié à cet étudiant
    # ✅ FIX : le soutien appartient au parent (user_id = parent.id)
    if support.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé.")

    # Récupérer les fichiers
    from data.models import SupportFile

    files = db.query(SupportFile).filter(SupportFile.support_id == support_id).all()

    return {
        "id": support.id,
        "user_id": support.user_id,
        "title": support.title,
        "short_description": support.short_description,
        "subject": support.subject,
        "custom_subject": support.custom_subject,
        "learning_objective": support.learning_objective,
        "learning_type": support.learning_type,
        "level": support.level,
        "content_language": support.content_language,
        "estimated_duration": support.estimated_duration,
        "keywords": support.keywords,
        "start_date": support.start_date,
        "end_date": support.end_date,
        "status": support.status,
        "chat_id": support.chat_id,
        "files": [{"id": f.id, "filename": f.filename} for f in files],
        "created_at": support.created_at.isoformat() if support.created_at else None,
        "updated_at": support.updated_at.isoformat() if support.updated_at else None,
    }


@router.patch("/link-chat/{support_id}")
async def link_chat_to_support(
    support_id: str,
    chat_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
    db: Session = Depends(get_db),
):
    """Lie un chat_id à un soutien de l'enfant (appelé par le parent après création du chat)."""
    _require_parent(current_user)

    from data.models import Support

    support = db.query(Support).filter(Support.id == support_id).first()
    if not support:
        raise HTTPException(status_code=404, detail="Soutien introuvable")

    # Vérifier que le parent est lié à l'étudiant propriétaire du soutien
    # ✅ FIX : le soutien appartient au parent (user_id = parent.id)
    if support.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé.")

    updated = svc.update_chat_id(support_id, chat_id)
    return {"id": updated.id, "chat_id": updated.chat_id, "status": "success"}


@router.patch("/{support_id}/complete")
async def mark_support_completed(
    support_id: str,
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
    db: Session = Depends(get_db),
):
    """Marque un soutien comme terminé."""
    _require_parent(current_user)
    from data.models import Support

    support = db.query(Support).filter(Support.id == support_id).first()
    if not support:
        raise HTTPException(status_code=404, detail="Soutien introuvable")
    # ✅ FIX : le soutien appartient au parent (user_id = parent.id)
    if support.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé.")
    from datetime import datetime

    support.status = "completed"
    support.updated_at = datetime.utcnow()
    db.commit()
    return {"id": support.id, "status": "completed"}


@router.get("/find-student")
async def find_student_by_email(
    email: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cherche un étudiant par email pour simplifier la liaison parent-enfant."""
    _require_parent(current_user)
    from data.models import User as UserModel

    # Recherche insensible à la casse + accepter role user ET parent (enfant peut avoir rôle user)
    student = (
        db.query(UserModel)
        .filter(
            UserModel.email.ilike(email.strip()),
            UserModel.role.in_(["user", "student"]),
        )
        .first()
    )
    # Si pas trouvé avec role user/student, chercher juste par email
    if not student:
        student = (
            db.query(UserModel).filter(UserModel.email.ilike(email.strip())).first()
        )
        # Exclure les admins et parents
        if student and student.role in ("admin", "parent"):
            student = None
    if not student:
        raise HTTPException(
            status_code=404, detail="Aucun élève trouvé avec cet email."
        )
    # Créer automatiquement le lien parent-étudiant si pas encore fait
    import uuid as uuid_lib

    from accounts.parents.models import ParentStudentLink

    existing = (
        db.query(ParentStudentLink)
        .filter(
            ParentStudentLink.parent_id == current_user.id,
            ParentStudentLink.student_id == student.id,
        )
        .first()
    )
    if not existing:
        link = ParentStudentLink(
            id=str(uuid_lib.uuid4()),
            parent_id=current_user.id,
            student_id=student.id,
            status="active",
        )
        db.add(link)
        db.commit()
    return {"id": student.id, "name": student.name, "email": student.email}


@router.get("/list-mine", response_model=List[ParentSupportResponse])
async def list_my_supports(
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
    db: Session = Depends(get_db),
):
    """✅ CORRIGÉ : Liste les soutiens créés par le parent connecté (user_id = parent.id)."""
    _require_parent(current_user)
    supports = svc.list_for_user(current_user.id)
    return [
        ParentSupportResponse(
            id=s.id,
            user_id=s.user_id,
            title=s.title,
            short_description=s.short_description,
            subject=s.subject,
            custom_subject=s.custom_subject,
            learning_objective=s.learning_objective,
            learning_type=s.learning_type,
            level=s.level,
            content_language=s.content_language,
            estimated_duration=s.estimated_duration,
            keywords=s.keywords.split(",") if s.keywords else None,
            start_date=s.start_date,
            end_date=s.end_date,
            status=s.status,
            chat_id=s.chat_id,
            files=[],
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in supports
    ]


@router.get("/list-mine", response_model=List[ParentSupportResponse])
async def list_my_supports(
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
    db: Session = Depends(get_db),
):
    """✅ FIX : soutiens du parent connecté (user_id = parent.id)."""
    _require_parent(current_user)
    supports = svc.list_for_user(current_user.id)
    return [
        ParentSupportResponse(
            id=s.id,
            user_id=s.user_id,
            title=s.title,
            short_description=s.short_description,
            subject=s.subject,
            custom_subject=s.custom_subject,
            learning_objective=s.learning_objective,
            learning_type=s.learning_type,
            level=s.level,
            content_language=s.content_language,
            estimated_duration=s.estimated_duration,
            keywords=s.keywords.split(",") if s.keywords else None,
            start_date=s.start_date,
            end_date=s.end_date,
            status=s.status,
            chat_id=s.chat_id,
            files=[],
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in supports
    ]
