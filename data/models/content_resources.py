from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from data.database import Base
from datetime import datetime
import enum

class ResourceType(str, enum.Enum):
    QUESTION_BANK = "question_bank"      # Fonctionnalité O
    REVISION_SHEET = "revision_sheet"    # Fonctionnalité P
    COURSE_TRANSCRIPT = "transcript"     # Fonctionnalité Q
    RAG_DOCUMENT = "rag_document"      # Fonctionnalité R
    VIDEO = "video"
    PDF = "pdf"
    LINK = "link"

class ContentResource(Base):
    __tablename__ = "content_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    resource_type = Column(Enum(ResourceType), nullable=False)
    
    # Propriétaire et scope
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    classroom_id = Column(Integer, nullable=True) # ForeignKey("classrooms.id") removed as table does not exist yet
    course_id = Column(Integer, nullable=True)    # ForeignKey("courses.id") removed as table does not exist yet
    
    # Métadonnées
    file_path = Column(String(500), nullable=True)  # Pour uploads (PDF, vidéo)
    external_url = Column(String(500), nullable=True)  # Pour liens externes
    content_json = Column(JSON, nullable=True)  # Pour questions, fiches, etc.
    
    # RAG / Vector DB
    is_indexed = Column(Boolean, default=False)
    vector_collection = Column(String(100), nullable=True)  # Nom collection ChromaDB
    
    # Métadonnées pédagogiques
    subject = Column(String(100), nullable=True)
    level = Column(String(50), nullable=True)  # Tronc commun, 1ère bac, etc.
    tags = Column(JSON, default=list)
    difficulty = Column(String(20), nullable=True)  # easy, medium, hard
    
    # Statistiques
    download_count = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    teacher = relationship("User")
    questions = relationship("QuestionItem", back_populates="resource")
    # classroom = relationship("Classroom", back_populates="resources")
    # course = relationship("Course", back_populates="resources")

# Modèle pour la banque de questions (Fonctionnalité O)
class QuestionItem(Base):
    __tablename__ = "question_items"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("content_resources.id"), nullable=False)
    
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))  # qcm, short_answer, essay, true_false
    options = Column(JSON, nullable=True)  # Pour QCM : ["A", "B", "C", "D"]
    correct_answer = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    points = Column(Integer, default=1)
    difficulty = Column(String(20), default="medium")
    tags = Column(JSON, default=list)
    
    # Pour la collaboration
    votes_up = Column(Integer, default=0)
    votes_down = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)  # Modération enseignant
    
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    resource = relationship("ContentResource", back_populates="questions")

