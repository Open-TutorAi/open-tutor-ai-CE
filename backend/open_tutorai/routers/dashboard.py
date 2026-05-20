from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from datetime import datetime
from typing import List, Optional, Dict, Any

from open_webui.utils.auth import get_verified_user
from open_tutorai.models.database import Support, Base
from sqlalchemy.orm import sessionmaker
from open_webui.internal.db import engine

import logging

router = APIRouter()
log = logging.getLogger(__name__)

# Connexion à la base de données
def get_db_session():
    Session = sessionmaker(bind=engine)
    return Session()


@router.get("/dashboard/stats")
async def get_dashboard_stats(user=Depends(get_verified_user)):
    """
    Retourne les statistiques globales pour le dashboard étudiant
    """
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    
    session = get_db_session()
    
    try:
        user_id = user.id
        
        # 1. Nombre total de supports de l'étudiant
        total_supports = session.query(Support)\
            .filter(Support.user_id == user_id)\
            .count()
        
        # 2. Supports actifs (en cours)
        active_supports = session.query(Support)\
            .filter(
                Support.user_id == user_id,
                Support.status.in_(["active", "pending", "in_progress"])
            )\
            .count()
        
        # 3. Supports terminés
        completed_supports = session.query(Support)\
            .filter(
                Support.user_id == user_id,
                Support.status == "completed"
            )\
            .count()
        
        # 4. Calcul du taux de complétion
        completion_rate = 0
        if total_supports > 0:
            completion_rate = round((completed_supports / total_supports) * 100, 1)
        
        # 5. Sujets les plus fréquents (top 3)
        subjects_query = session.query(
            Support.subject,
            func.count(Support.subject).label('count')
        )\
            .filter(Support.user_id == user_id)\
            .group_by(Support.subject)\
            .order_by(func.count(Support.subject).desc())\
            .limit(3)\
            .all()
        
        top_subjects = [
            {"name": subject, "count": count}
            for subject, count in subjects_query
        ]
        
        # 6. Support le plus récent
        latest_support = session.query(Support)\
            .filter(Support.user_id == user_id)\
            .order_by(Support.updated_at.desc())\
            .first()
        
        latest_activity = None
        if latest_support:
            latest_activity = {
                "id": latest_support.id,
                "title": latest_support.title,
                "subject": latest_support.subject,
                "status": latest_support.status,
                "updatedAt": latest_support.updated_at.isoformat() if latest_support.updated_at else None
            }
        
        return {
            "totalSupports": total_supports,
            "activeSupports": active_supports,
            "completedSupports": completed_supports,
            "completionRate": completion_rate,
            "topSubjects": top_subjects,
            "latestActivity": latest_activity,
            "lastUpdated": datetime.now().isoformat()
        }
        
    except Exception as e:
        log.error(f"Erreur lors du calcul des stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
    
    finally:
        session.close()


@router.get("/dashboard/recent-activity")
async def get_recent_activity(
    limit: int = 5,
    user=Depends(get_verified_user)
):
    """
    Retourne les supports récemment modifiés par l'étudiant
    """
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    
    session = get_db_session()
    
    try:
        supports = session.query(Support)\
            .filter(Support.user_id == user.id)\
            .order_by(Support.updated_at.desc())\
            .limit(limit)\
            .all()
        
        return [
            {
                "id": s.id,
                "title": s.title,
                "subject": s.subject,
                "status": s.status,
                "shortDescription": s.short_description,
                "updatedAt": s.updated_at.isoformat() if s.updated_at else None,
                "createdAt": s.created_at.isoformat() if s.created_at else None
            }
            for s in supports
        ]
        
    except Exception as e:
        log.error(f"Erreur lors de la récupération de l'activité: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
    
    finally:
        session.close()


@router.get("/dashboard/subjects-distribution")
async def get_subjects_distribution(user=Depends(get_verified_user)):
    """
    Retourne la répartition des supports par matière (pour un graphique)
    """
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    
    session = get_db_session()
    
    try:
        distribution = session.query(
            Support.subject,
            func.count(Support.subject).label('count')
        )\
            .filter(Support.user_id == user.id)\
            .group_by(Support.subject)\
            .all()
        
        return [
            {"subject": subject, "count": count}
            for subject, count in distribution
        ]
        
    except Exception as e:
        log.error(f"Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
    
    finally:
        session.close()