from sqlalchemy.orm import Session
from data.models.content_resources import ContentResource, QuestionItem, ResourceType
from typing import List, Optional

class ContentResourceRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, resource: ContentResource) -> ContentResource:
        self.db.add(resource)
        self.db.commit()
        self.db.refresh(resource)
        return resource
    
    def get_by_id(self, resource_id: int) -> Optional[ContentResource]:
        return self.db.query(ContentResource).filter(ContentResource.id == resource_id).first()
    
    def get_by_teacher(self, teacher_id: int, resource_type: Optional[ResourceType] = None) -> List[ContentResource]:
        query = self.db.query(ContentResource).filter(ContentResource.teacher_id == teacher_id)
        if resource_type:
            query = query.filter(ContentResource.resource_type == resource_type)
        return query.order_by(ContentResource.created_at.desc()).all()
    
    def get_by_classroom(self, classroom_id: int) -> List[ContentResource]:
        return self.db.query(ContentResource).filter(
            ContentResource.classroom_id == classroom_id
        ).order_by(ContentResource.created_at.desc()).all()
    
    def search_questions(self, query_text: str, subject: Optional[str] = None, 
                        level: Optional[str] = None, difficulty: Optional[str] = None) -> List[QuestionItem]:
        """Recherche sémantique dans la banque de questions"""
        db_query = self.db.query(QuestionItem).join(ContentResource)
        
        if query_text:
            db_query = db_query.filter(
                QuestionItem.question_text.ilike(f"%{query_text}%") |
                QuestionItem.explanation.ilike(f"%{query_text}%") |
                ContentResource.tags.contains([query_text])
            )
        
        if subject:
            db_query = db_query.filter(ContentResource.subject == subject)
        if level:
            db_query = db_query.filter(ContentResource.level == level)
        if difficulty:
            db_query = db_query.filter(QuestionItem.difficulty == difficulty)
        
        return db_query.order_by(QuestionItem.votes_up.desc()).all()
    
    def add_question(self, question: QuestionItem) -> QuestionItem:
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question
    
    def delete(self, resource_id: int) -> bool:
        resource = self.get_by_id(resource_id)
        if resource:
            self.db.delete(resource)
            self.db.commit()
            return True
        return False