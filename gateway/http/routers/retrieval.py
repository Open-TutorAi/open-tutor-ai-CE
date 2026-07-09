"""Retrieval router — /retrieval/* matching retrieval/index.ts UI client.

Admin-only: config read/write, embedding, reranking, reset.
Verified user: template, query settings, process/*, query/*.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai.retrieval.service import RetrievalService
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


def _svc(db: Session = Depends(get_db)) -> RetrievalService:
    return RetrievalService(db)


def _require_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


class ChunkConfig(BaseModel):
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    text_splitter: Optional[str] = None


class ContentExtractionConfig(BaseModel):
    engine: Optional[str] = None
    tika_server_url: Optional[str] = None


class YoutubeConfig(BaseModel):
    language: Optional[list] = None
    translation: Optional[str] = None
    proxy_url: Optional[str] = None


class FileConfig(BaseModel):
    max_size: Optional[int] = None
    max_count: Optional[int] = None


class RAGConfigUpdateRequest(BaseModel):
    pdf_extract_images: Optional[bool] = None
    RAG_FULL_CONTEXT: Optional[bool] = None
    enable_google_drive_integration: Optional[bool] = None
    web_loader_ssl_verification: Optional[bool] = None
    chunk: Optional[ChunkConfig] = None
    content_extraction: Optional[ContentExtractionConfig] = None
    youtube: Optional[YoutubeConfig] = None
    file: Optional[FileConfig] = None


class QuerySettingsRequest(BaseModel):
    k: Optional[int] = None
    r: Optional[float] = None
    template: Optional[str] = None
    hybrid: Optional[bool] = None


class EmbeddingUpdateRequest(BaseModel):
    embedding_engine: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_batch_size: Optional[int] = None
    openai_config: Optional[dict] = None
    ollama_config: Optional[dict] = None


class RerankingUpdateRequest(BaseModel):
    reranking_model: Optional[str] = None
    enabled: Optional[bool] = None


# ── Admin-only: config, embedding, reranking ─────────────────────────────────


@router.get("/config")
def get_config(
    user: User = Depends(get_current_user), svc: RetrievalService = Depends(_svc)
):
    _require_admin(user)
    return svc.get_config()


@router.post("/config/update")
def update_config(
    body: RAGConfigUpdateRequest,
    user: User = Depends(get_current_user),
    svc: RetrievalService = Depends(_svc),
):
    _require_admin(user)
    data = body.model_dump(exclude_none=True)
    for key in ("chunk", "content_extraction", "youtube", "file"):
        if key in data and hasattr(data[key], "model_dump"):
            data[key] = data[key].model_dump(exclude_none=True)
    return svc.update_config(data)


@router.get("/embedding")
def get_embedding(
    user: User = Depends(get_current_user), svc: RetrievalService = Depends(_svc)
):
    _require_admin(user)
    return svc.get_embedding()


@router.post("/embedding/update")
def update_embedding(
    body: EmbeddingUpdateRequest,
    user: User = Depends(get_current_user),
    svc: RetrievalService = Depends(_svc),
):
    _require_admin(user)
    return svc.update_embedding(body.model_dump(exclude_none=True))


@router.get("/reranking")
def get_reranking(
    user: User = Depends(get_current_user), svc: RetrievalService = Depends(_svc)
):
    _require_admin(user)
    return svc.get_reranking()


@router.post("/reranking/update")
def update_reranking(
    body: RerankingUpdateRequest,
    user: User = Depends(get_current_user),
    svc: RetrievalService = Depends(_svc),
):
    _require_admin(user)
    return svc.update_reranking(body.model_dump(exclude_none=True))


@router.post("/reset/uploads")
def reset_uploads(user: User = Depends(get_current_user)):
    _require_admin(user)
    return {"status": "ok"}


@router.post("/reset/db")
def reset_vector_db(user: User = Depends(get_current_user)):
    _require_admin(user)
    return {"status": "ok"}


# ── Verified user: template, query settings, process, query ──────────────────


@router.get("/template")
def get_template(
    user: User = Depends(get_current_user), svc: RetrievalService = Depends(_svc)
):
    return {"template": svc.get_template()}


@router.get("/query/settings")
def get_query_settings(
    user: User = Depends(get_current_user), svc: RetrievalService = Depends(_svc)
):
    return svc.get_query_settings()


@router.post("/query/settings/update")
def update_query_settings(
    body: QuerySettingsRequest,
    user: User = Depends(get_current_user),
    svc: RetrievalService = Depends(_svc),
):
    return svc.update_query_settings(body.model_dump(exclude_none=True))


@router.post("/process/file")
def process_file(body: dict, user: User = Depends(get_current_user)):
    return {"status": "ok", "file_id": body.get("file_id")}


@router.post("/process/youtube")
def process_youtube(body: dict, user: User = Depends(get_current_user)):
    return {"status": "ok", "url": body.get("url")}


@router.post("/process/web")
def process_web(body: dict, user: User = Depends(get_current_user)):
    return {"status": "ok", "url": body.get("url")}


@router.post("/process/web/search")
def process_web_search(body: dict, user: User = Depends(get_current_user)):
    return {"status": "ok", "query": body.get("query")}


@router.post("/query/doc")
def query_doc(body: dict, user: User = Depends(get_current_user)):
    return {"results": []}


@router.post("/query/collection")
def query_collection(body: dict, user: User = Depends(get_current_user)):
    return {"results": []}
