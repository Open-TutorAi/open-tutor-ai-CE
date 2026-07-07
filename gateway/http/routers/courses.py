from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from data.database import get_db
from data.models import Course, User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/courses", tags=["courses"])

@router.post("/")
async def create_course(
    course_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sauvegarder un cours en base de données"""
    new_course = Course(
        user_id=current_user.id,
        title=course_data["title"],
        description=course_data["description"],
        chapters=course_data["chapters"],
        subject=course_data.get("subject", ""),
        level=course_data.get("level", ""),
        objective=course_data.get("objective", "")
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return {"success": True, "course": new_course.to_dict()}

@router.get("/")
async def get_user_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer tous les cours de l'utilisateur connecté"""
    courses = db.query(Course).filter(Course.user_id == current_user.id).all()
    return {"courses": [course.to_dict() for course in courses]}

@router.get("/{course_id}")
async def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un cours spécifique"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return {"course": course.to_dict()}

@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un cours"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db.delete(course)
    db.commit()
    return {"success": True, "message": "Course deleted"}