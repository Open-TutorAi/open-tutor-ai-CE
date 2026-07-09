"""Knowledge router — /knowledge/* matching knowledge/index.ts UI client."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai.retrieval.knowledge.service import KnowledgeService
from common.exceptions import NotFoundError
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _svc(db: Session = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(db)


class KnowledgeCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    data: Optional[dict] = None
    access_control: Optional[dict] = None  # stored in meta column


class KnowledgeUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data: Optional[dict] = None
    access_control: Optional[dict] = None


class FileRequest(BaseModel):
    file_id: str


@router.post("/create")
def create_knowledge(
    body: KnowledgeCreateRequest,
    user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(_svc),
):
    return svc.create(user.id, body.model_dump()).to_dict()


@router.get("/")
def get_knowledge_bases(
    user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(_svc),
):
    return [kb.to_dict() for kb in svc.list_by_user(user.id)]


@router.get("/list")
def get_knowledge_list(
    user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(_svc),
):
    return [kb.to_dict() for kb in svc.list_by_user(user.id)]


@router.get("/{id}")
def get_knowledge(
    id: str,
    user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(_svc),
):
    try:
        return svc.get_with_files(id, user.id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")


@router.post("/{id}/update")
def update_knowledge(
    id: str,
    body: KnowledgeUpdateRequest,
    user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(_svc),
):
    try:
        data = {k: v for k, v in body.model_dump().items() if v is not None}
        return svc.update(id, user.id, data).to_dict()
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")


@router.post("/{id}/file/add")
def add_file(
    id: str,
    body: FileRequest,
    user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(_svc),
):
    try:
        svc.add_file(id, user.id, body.file_id)
        return svc.get_with_files(id, user.id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")


@router.post("/{id}/file/update")
def update_file(
    id: str,
    body: FileRequest,
    user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(_svc),
):
    try:
        svc.update_file(id, user.id, body.file_id)
        return svc.get_with_files(id, user.id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")


@router.post("/{id}/file/remove")
def remove_file(
    id: str,
    body: FileRequest,
    user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(_svc),
):
    try:
        svc.remove_file(id, user.id, body.file_id)
        return svc.get_with_files(id, user.id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")


@router.post("/{id}/reset")
def reset_knowledge(
    id: str,
    user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(_svc),
):
    try:
        svc.reset(id, user.id)
        return svc.get_with_files(id, user.id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")


@router.delete("/{id}/delete")
def delete_knowledge(
    id: str,
    user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(_svc),
):
    try:
        svc.delete(id, user.id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return {"id": id, "deleted": True}
