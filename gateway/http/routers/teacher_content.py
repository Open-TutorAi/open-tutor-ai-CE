from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from gateway.http.dependencies import get_db, get_current_user
from data.repositories.content_resource_repository import ContentResourceRepository
from data.models.content_resources import ContentResource, QuestionItem, ResourceType
from ai.retrieval.vector_store import VectorStore  # Service RAG existant
import json
import os
import shutil

router = APIRouter(prefix="/api/v1/teacher/content", tags=["Teacher Content"])

# ─── Schémas Pydantic ───

class TranscriptSummaryRequest(BaseModel):
    transcription: str
    title: Optional[str] = "Résumé IA"
    subject: Optional[str] = "Général"
    model_id: str = ""

class ScenarioRequest(BaseModel):
    theme: str
    objectives: List[str]
    estimated_hours: Optional[int] = 2
    model_id: str = ""

class QuestionCreate(BaseModel):
    question_text: str
    question_type: str  # qcm, short_answer, essay
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    points: int = 1
    difficulty: str = "medium"
    tags: List[str] = []

class ResourceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    resource_type: ResourceType
    classroom_id: Optional[int] = None
    course_id: Optional[int] = None
    subject: Optional[str] = None
    level: Optional[str] = None
    tags: List[str] = []
    external_url: Optional[str] = None
    content_json: Optional[dict] = None

class ResourceResponse(BaseModel):
    id: int
    title: str
    resource_type: str
    subject: Optional[str]
    level: Optional[str]
    created_at: str
    is_indexed: bool
    
    class Config:
        from_attributes = True

# ─── Endpoints ───

@router.post("/upload", response_model=ResourceResponse)
async def upload_resource(
    file: UploadFile = File(...),
    title: str = Form(...),
    resource_type: ResourceType = Form(...),
    classroom_id: Optional[int] = Form(None),
    course_id: Optional[int] = Form(None),
    subject: Optional[str] = Form(None),
    level: Optional[str] = Form(None),
    tags: str = Form("[]"),  # JSON string
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Upload un fichier (PDF, vidéo) et l'indexe pour le RAG"""
    
    # 1. Sauvegarde du fichier
    upload_dir = os.getenv("UPLOAD_DIR", "./var/uploads")
    teacher_dir = os.path.join(upload_dir, f"teacher_{user.id}")
    os.makedirs(teacher_dir, exist_ok=True)
    
    file_path = os.path.join(teacher_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 2. Création en base
    repo = ContentResourceRepository(db)
    resource = ContentResource(
        title=title,
        resource_type=resource_type,
        teacher_id=user.id,
        classroom_id=classroom_id,
        course_id=course_id,
        file_path=file_path,
        subject=subject,
        level=level,
        tags=json.loads(tags),
        is_indexed=False
    )
    resource = repo.create(resource)
    
    # 3. Indexation RAG (async en production)
    if resource_type == ResourceType.RAG_DOCUMENT:
        vector_store = VectorStore()
        collection_name = f"classroom_{classroom_id}_course_{course_id}"
        vector_store.index_document(file_path, collection_name, metadata={
            "teacher_id": user.id,
            "resource_id": resource.id,
            "subject": subject
        })
        resource.is_indexed = True
        resource.vector_collection = collection_name
        db.commit()
    
    return resource

@router.post("/questions", response_model=ResourceResponse)
async def create_question_bank(
    resource: ResourceCreate,
    questions: List[QuestionCreate],
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Créer une banque de questions (Fonctionnalité O)"""
    
    repo = ContentResourceRepository(db)
    
    # Créer la ressource parent
    content = ContentResource(
        title=resource.title,
        description=resource.description,
        resource_type=ResourceType.QUESTION_BANK,
        teacher_id=user.id,
        classroom_id=resource.classroom_id,
        course_id=resource.course_id,
        subject=resource.subject,
        level=resource.level,
        tags=resource.tags
    )
    content = repo.create(content)
    
    # Ajouter les questions
    vector_store = VectorStore()
    
    for q in questions:
        question = QuestionItem(
            resource_id=content.id,
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options,
            correct_answer=q.correct_answer,
            explanation=q.explanation,
            points=q.points,
            difficulty=q.difficulty,
            tags=q.tags,
            created_by=user.id
        )
        question = repo.add_question(question)
        
        # Indexer la question dans le Vector DB pour la recherche sémantique
        metadata = {
            "subject": resource.subject,
            "level": resource.level,
            "difficulty": q.difficulty,
            "question_type": q.question_type
        }
        vector_store.index_question(question.id, q.question_text, metadata)
    
    return content

@router.get("/questions/search")
async def search_question_bank(
    q: Optional[str] = None,
    subject: Optional[str] = None,
    level: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Recherche sémantique dans la banque de questions (Fonctionnalité O)"""
    repo = ContentResourceRepository(db)
    
    if q:
        # Véritable recherche sémantique RAG via ChromaDB
        vector_store = VectorStore()
        filter_meta = {}
        if subject: filter_meta["subject"] = subject
        if level: filter_meta["level"] = level
        if difficulty: filter_meta["difficulty"] = difficulty
        
        vec_results = vector_store.search_questions(q, n_results=10, filter_meta=filter_meta)
        question_ids = [res["id"] for res in vec_results]
        
        if not question_ids:
            return {"total": 0, "questions": []}
            
        results = [repo.db.query(QuestionItem).filter(QuestionItem.id == qid).first() for qid in question_ids]
        results = [r for r in results if r is not None]
    else:
        # Fallback classique si pas de requête textuelle (juste des filtres)
        results = repo.search_questions(q, subject, level, difficulty)
    
    return {
        "total": len(results),
        "questions": [
            {
                "id": r.id,
                "text": r.question_text,
                "type": r.question_type,
                "difficulty": r.difficulty,
                "points": r.points,
                "votes": r.votes_up - r.votes_down,
                "subject": r.resource.subject if r.resource else None
            }
            for r in results
        ]
    }

from pydantic import BaseModel

class RevisionSheetRequest(BaseModel):
    frequent_errors: str
    model_id: str = ""

@router.post("/revision-sheet")
async def generate_revision_sheet(
    classroom_id: int,
    request: RevisionSheetRequest,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Génère une fiche de révision basée sur les erreurs fréquentes (Fonctionnalité P)"""
    from system.configs.service import ConfigsService
    from ai.providers.service import ProvidersService, build_llm_body
    from ai.providers.proxy import proxy_json
    
    # Get model ID, fallback to system default
    model_id = request.model_id
    if not model_id:
        models_cfg = ConfigsService(db).get("models") or {}
        default_models = models_cfg.get("DEFAULT_MODELS", "")
        if default_models:
            model_id = default_models.split(",")[0]
            
    if not model_id:
        raise HTTPException(status_code=400, detail="No model_id provided and no default model configured.")

    base_url, api_key, path = await ProvidersService(db).resolve_provider(model_id)
    
    prompt = f"""
En tant qu'enseignant, crée une fiche de révision ciblée.
Concentre-toi particulièrement sur le contexte et les erreurs fréquentes suivantes observées chez les élèves :
{request.frequent_errors}

Structure de la fiche :
1. Rappel des concepts clés
2. Exemples détaillés et corrigés illustrant les erreurs à éviter
3. Mini-exercices ciblés
Retourne UNIQUEMENT le contenu Markdown de la fiche, sans commentaire supplémentaire.
"""
    
    llm_body = build_llm_body({
        "model": model_id,
        "messages": [
            {"role": "system", "content": "Tu es un professeur expert en pédagogie."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    })
    
    response = await proxy_json(base_url, api_key, "POST", path, body=llm_body)
    
    # Extraire le texte de la réponse (OpenAI/Ollama)
    if "choices" in response and len(response["choices"]) > 0:
        sheet_content = response["choices"][0]["message"].get("content", "")
    elif "message" in response: # Ollama fallback format
        sheet_content = response["message"].get("content", "")
    elif "response" in response:
        sheet_content = response.get("response", "")
    else:
        sheet_content = str(response)
    
    # 3. Sauvegarder comme ressource
    repo = ContentResourceRepository(db)
    resource = ContentResource(
        title="Fiche de révision",
        resource_type=ResourceType.REVISION_SHEET,
        teacher_id=user.id,
        classroom_id=classroom_id,
        subject=None,
        content_json={"content": sheet_content, "generated_by": "ai", "based_on_errors": request.frequent_errors},
        is_indexed=False
    )
    resource = repo.create(resource)
    
    return {"id": resource.id, "title": resource.title, "content": sheet_content}

@router.post("/extract-text")
async def extract_document_text(
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """Extrait le texte d'un document PDF ou TXT uploadé (Adaptation Fonctionnalité Q)"""
    content_type = file.content_type
    filename = file.filename.lower() if file.filename else ""
    
    text = ""
    try:
        content_bytes = await file.read()
        
        if filename.endswith(".pdf") or content_type == "application/pdf":
            import io
            import pypdf
            
            pdf_file = io.BytesIO(content_bytes)
            reader = pypdf.PdfReader(pdf_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        else:
            # Fallback to text reading
            try:
                text = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = content_bytes.decode("latin-1", errors="replace")
                
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'extraction: {str(e)}")
        
    if not text.strip():
        raise HTTPException(status_code=400, detail="Aucun texte n'a pu être extrait de ce document.")
        
    return {"text": text.strip()}

@router.post("/transcript-summary")
async def generate_transcript_summary(
    classroom_id: int,
    request: TranscriptSummaryRequest,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Génère un résumé de cours à partir d'une transcription (Fonctionnalité Q)"""
    from system.configs.service import ConfigsService
    from ai.providers.service import ProvidersService, build_llm_body
    from ai.providers.proxy import proxy_json

    model_id = request.model_id
    if not model_id:
        models_cfg = ConfigsService(db).get("models") or {}
        default_models = models_cfg.get("DEFAULT_MODELS", "")
        if default_models:
            model_id = default_models.split(",")[0]
            
    if not model_id:
        raise HTTPException(status_code=400, detail="No model_id provided and no default model configured.")

    base_url, api_key, path = await ProvidersService(db).resolve_provider(model_id)
    
    prompt = f"""Voici un texte extrait d'un document de {request.subject}.
Titre original (s'il y en a un) : {request.title}

Veuillez lire ce texte et générer un résumé de cours clair, bien structuré et pédagogique pour les élèves.
Le résumé doit commencer par donner un Titre approprié au document.
Ensuite, il doit inclure :
- Une brève introduction
- Les concepts clés expliqués simplement
- S'il y a lieu, des exemples mentionnés dans le document
- Une conclusion ou un rappel des éléments à retenir

Texte du document :
{request.transcription}
"""

    llm_body = build_llm_body({
        "model": model_id,
        "messages": [
            {"role": "system", "content": "Tu es un professeur expert en pédagogie et en synthèse d'informations."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    })
    
    response = await proxy_json(base_url, api_key, "POST", path, body=llm_body)
    
    # Extraire le texte de la réponse (OpenAI/Ollama/Gemini)
    if "choices" in response and len(response["choices"]) > 0:
        summary_content = response["choices"][0]["message"].get("content", "")
    elif "message" in response:
        summary_content = response["message"].get("content", "")
    elif "response" in response:
        summary_content = response.get("response", "")
    else:
        summary_content = str(response)

    # Sauvegarder la ressource en BDD
    repo = ContentResourceRepository(db)
    resource = ContentResource(
        title=f"Résumé - {request.title}",
        resource_type=ResourceType.COURSE_TRANSCRIPT,
        teacher_id=user.id,
        classroom_id=classroom_id,
        subject=request.subject,
        content_json={
            "transcription": request.transcription,
            "summary": summary_content,
            "generated_by": "ai"
        },
        is_indexed=False
    )
    resource = repo.create(resource)
    
    return {
        "id": resource.id, 
        "title": resource.title, 
        "transcription": request.transcription,
        "summary": summary_content
    }

@router.get("/classroom/{classroom_id}/rag")
async def get_classroom_rag(
    classroom_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Liste les documents RAG d'une classe (Fonctionnalité R)"""
    repo = ContentResourceRepository(db)
    resources = repo.get_by_classroom(classroom_id)
    
    # Filtrer uniquement les RAG documents
    rag_docs = [r for r in resources if r.resource_type == ResourceType.RAG_DOCUMENT]
    
    return [
        {
            "id": r.id,
            "title": r.title,
            "is_indexed": r.is_indexed,
            "vector_collection": r.vector_collection,
            "subject": r.subject,
            "created_at": r.created_at.isoformat()
        }
        for r in rag_docs
    ]
@router.post("/curriculum/generate")
async def generate_curriculum(
    file: UploadFile = File(...),
    model_id: str = Form(...),
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Génère un calendrier pédagogique à partir du programme officiel."""
    content_type = file.content_type
    filename = file.filename.lower() if file.filename else ""
    
    text = ""
    try:
        content_bytes = await file.read()
        if filename.endswith(".pdf") or content_type == "application/pdf":
            import io
            import pypdf
            pdf_file = io.BytesIO(content_bytes)
            reader = pypdf.PdfReader(pdf_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        else:
            try:
                text = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = content_bytes.decode("latin-1", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'extraction: {str(e)}")
        
    if not text.strip():
        raise HTTPException(status_code=400, detail="Aucun texte extrait du document.")
        
    from system.configs.service import ConfigsService
    from ai.providers.service import ProvidersService, build_llm_body
    from ai.providers.proxy import proxy_json

    if not model_id:
        models_cfg = ConfigsService(db).get("models") or {}
        default_models = models_cfg.get("DEFAULT_MODELS", "")
        if default_models:
            model_id = default_models.split(",")[0]
            
    if not model_id:
        raise HTTPException(status_code=400, detail="No model_id provided and no default model configured.")

    base_url, api_key, path = await ProvidersService(db).resolve_provider(model_id)
    
    prompt = f"""Voici le programme officiel d'une matière.
Tu dois découper ce programme en une planification annuelle (séquences par semaine).
Renvoie le résultat UNIQUEMENT sous forme de JSON strict, sans aucun bloc markdown comme ```json, sans préfixe, ni texte avant ou après.

Structure attendue :
{{
  "title": "Nom du cours/programme",
  "weeks": [
    {{
      "week_number": 1,
      "theme": "Thème de la séquence",
      "objectives": ["Objectif 1", "Objectif 2"],
      "estimated_hours": 2
    }}
  ]
}}

Texte du programme :
{text}
"""
    
    llm_body = build_llm_body({
        "model": model_id,
        "messages": [
            {"role": "system", "content": "Tu es un assistant pédagogique expert. Tu renvoies TOUJOURS du JSON pur et valide, sans formattage markdown."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    })
    
    response = await proxy_json(base_url, api_key, "POST", path, body=llm_body)
    
    if "choices" in response and len(response["choices"]) > 0:
        content = response["choices"][0]["message"].get("content", "")
    elif "message" in response:
        content = response["message"].get("content", "")
    elif "response" in response:
        content = response.get("response", "")
    else:
        content = str(response)

    # Nettoyage du JSON (si le LLM rajoute quand même ```json)
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    import json
    try:
        data = json.loads(content)
        return {"curriculum": data}
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw content: {content}")
        raise HTTPException(status_code=500, detail="Le modèle n'a pas renvoyé un format JSON valide.")

@router.post("/curriculum/scenario/generate")
async def generate_scenario(
    request: ScenarioRequest,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Génère un scénario pédagogique (fiche de préparation) pour une séquence."""
    from system.configs.service import ConfigsService
    from ai.providers.service import ProvidersService, build_llm_body
    from ai.providers.proxy import proxy_json

    model_id = request.model_id
    if not model_id:
        models_cfg = ConfigsService(db).get("models") or {}
        default_models = models_cfg.get("DEFAULT_MODELS", "")
        if default_models:
            model_id = default_models.split(",")[0]
            
    if not model_id:
        raise HTTPException(status_code=400, detail="No model_id provided.")

    base_url, api_key, path = await ProvidersService(db).resolve_provider(model_id)

    objectives_list = "\n".join([f"- {obj}" for obj in request.objectives])
    prompt = f"""Tu es un expert en pédagogie et en didactique.
Ton rôle est de rédiger une "Fiche de préparation" (Scénario pédagogique) complète et détaillée pour une séquence de cours.

THÈME DE LA SÉQUENCE : {request.theme}
DURÉE ESTIMÉE : {request.estimated_hours} heures
OBJECTIFS D'APPRENTISSAGE :
{objectives_list}

Rédige cette fiche au format Markdown. Structure ta réponse avec les sections suivantes :
# Fiche de préparation : {request.theme}
## 1. Introduction & Contexte
## 2. Prérequis & Matériel nécessaire
## 3. Déroulement de la séquence (Utilise une liste chronologique détaillée. IMPORTANT : NE FAIS PAS DE TABLEAU pour éviter les problèmes de formatage Markdown)
## 4. Traces écrites / Synthèse pour l'élève
## 5. Modalités d'évaluation

Sois concret, professionnel et propose des activités engageantes. Évite l'utilisation de balises HTML comme <br>.
"""

    llm_body = build_llm_body({
        "model": model_id,
        "messages": [
            {"role": "system", "content": "Tu es un expert pédagogique. Tu réponds uniquement en Markdown structuré et professionnel."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    })

    response = await proxy_json(base_url, api_key, "POST", path, body=llm_body)

    if "choices" in response and len(response["choices"]) > 0:
        content = response["choices"][0]["message"].get("content", "")
    elif "message" in response:
        content = response["message"].get("content", "")
    elif "response" in response:
        content = response.get("response", "")
    else:
        content = str(response)

    return {"scenario": content.strip()}
