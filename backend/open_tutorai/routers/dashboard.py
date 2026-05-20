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
async def get_dashboard_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user=Depends(get_verified_user)
):
    """
    Retourne les statistiques pour le dashboard étudiant filtrées par période
    """
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    
    session = get_db_session()
    
    try:
        user_id = user.id
        
        # Parsing des dates de début et de fin si elles sont fournies
        start_dt = None
        end_dt = None
        if start_date:
            try:
                # Support du format ISO des navigateurs (ex: avec 'Z' ou offset de fuseau horaire)
                cleaned_start = start_date.replace("Z", "+00:00")
                if "T" in cleaned_start:
                    start_dt = datetime.fromisoformat(cleaned_start)
                else:
                    start_dt = datetime.strptime(cleaned_start, "%Y-%m-%d")
            except Exception as e:
                log.warning(f"Impossible de parser la date de début '{start_date}': {str(e)}")
        
        if end_date:
            try:
                cleaned_end = end_date.replace("Z", "+00:00")
                if "T" in cleaned_end:
                    end_dt = datetime.fromisoformat(cleaned_end)
                else:
                    end_dt = datetime.strptime(cleaned_end, "%Y-%m-%d")
                    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            except Exception as e:
                log.warning(f"Impossible de parser la date de fin '{end_date}': {str(e)}")
        
        # Construction des requêtes avec filtres optionnels
        total_query = session.query(Support).filter(Support.user_id == user_id)
        active_query = session.query(Support).filter(
            Support.user_id == user_id,
            Support.status.in_(["active", "pending", "in_progress"])
        )
        completed_query = session.query(Support).filter(
            Support.user_id == user_id,
            Support.status == "completed"
        )
        subjects_query = session.query(
            Support.subject,
            func.count(Support.subject).label('count')
        ).filter(Support.user_id == user_id).group_by(Support.subject)
        
        latest_query = session.query(Support).filter(Support.user_id == user_id)
        
        # Application des filtres de date sur la date de création du support
        if start_dt:
            total_query = total_query.filter(Support.created_at >= start_dt)
            active_query = active_query.filter(Support.created_at >= start_dt)
            completed_query = completed_query.filter(Support.created_at >= start_dt)
            subjects_query = subjects_query.filter(Support.created_at >= start_dt)
            latest_query = latest_query.filter(Support.created_at >= start_dt)
            
        if end_dt:
            total_query = total_query.filter(Support.created_at <= end_dt)
            active_query = active_query.filter(Support.created_at <= end_dt)
            completed_query = completed_query.filter(Support.created_at <= end_dt)
            subjects_query = subjects_query.filter(Support.created_at <= end_dt)
            latest_query = latest_query.filter(Support.created_at <= end_dt)

        # Exécution des requêtes
        total_supports = total_query.count()
        active_supports = active_query.count()
        completed_supports = completed_query.count()
        
        # 4. Calcul du taux de complétion
        completion_rate = 0
        if total_supports > 0:
            completion_rate = round((completed_supports / total_supports) * 100, 1)
        
        # 5. Sujets les plus fréquents (top 3)
        subjects_result = subjects_query.order_by(func.count(Support.subject).desc())\
            .limit(3)\
            .all()
        
        top_subjects = [
            {"name": subject, "count": count}
            for subject, count in subjects_result
        ]
        
        # 6. Support le plus récent
        latest_support = latest_query.order_by(Support.updated_at.desc()).first()
        
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