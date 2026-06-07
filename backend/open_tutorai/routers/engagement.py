"""
Engagement Tracking Router
Roadmap v1.1.0 — Personalization & UX
Track: clicks, feedback, drop-off, session time
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid
import json

from open_webui.utils.auth import get_verified_user
from open_tutorai.models.database import Activity, Support
from sqlalchemy.orm import sessionmaker
from open_webui.internal.db import engine

router = APIRouter()

def get_db_session():
    Session = sessionmaker(bind=engine)
    return Session()


# ============================================================================
# ENDPOINT 1 : TRACKER UNE ACTIVITÉ (appelé par le frontend)
# ============================================================================

@router.post("/engagement/track")
async def track_activity(
    activity_type: str,  # 'session_start', 'session_end', 'click', 'drop_off', 'feedback', 'page_view'
    duration: Optional[int] = 0,  # en secondes (pour session_end)
    metadata: Optional[str] = None,  # JSON string
    user=Depends(get_verified_user)
):
    """
    Enregistre une activité utilisateur pour le tracking d'engagement
    Appelé automatiquement par le frontend lors des interactions
    """
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    
    session = get_db_session()
    
    try:
        activity = Activity(
            id=str(uuid.uuid4()),
            user_id=user.id,
            type=activity_type,
            duration=duration,
            metadata_json=metadata,
            created_at=datetime.utcnow()
        )
        
        session.add(activity)
        session.commit()
        
        return {
            "status": "tracked",
            "activity_id": activity.id,
            "type": activity_type,
            "timestamp": activity.created_at.isoformat()
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur tracking: {str(e)}")
    finally:
        session.close()


# ============================================================================
# ENDPOINT 2 : MÉTRIQUES D'ENGAGEMENT GLOBALES
# ============================================================================

@router.get("/dashboard/engagement")
async def get_engagement_metrics(
    period_days: int = 7,  # période d'analyse (défaut: 7 jours)
    user=Depends(get_verified_user)
):
    """
    Retourne les métriques d'engagement de l'étudiant
    - Temps total d'étude
    - Nombre de sessions
    - Taux d'abandon
    - Score d'engagement global
    """
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    
    session = get_db_session()
    
    try:
        # Date de début de la période
        period_start = datetime.utcnow() - timedelta(days=period_days)
        
        # 1. TEMPS TOTAL D'ÉTUDE (somme des durations des sessions terminées)
        total_time_seconds = session.query(func.sum(Activity.duration))\
            .filter(
                Activity.user_id == user.id,
                Activity.type == 'session_end',
                Activity.created_at >= period_start
            )\
            .scalar() or 0
        
        total_time_minutes = int(total_time_seconds / 60)
        
        # 2. NOMBRE DE SESSIONS
        sessions_started = session.query(Activity)\
            .filter(
                Activity.user_id == user.id,
                Activity.type == 'session_start',
                Activity.created_at >= period_start
            )\
            .count()
        
        sessions_completed = session.query(Activity)\
            .filter(
                Activity.user_id == user.id,
                Activity.type == 'session_end',
                Activity.created_at >= period_start
            )\
            .count()
        
        # 3. CLICS ET INTERACTIONS
        total_clicks = session.query(Activity)\
            .filter(
                Activity.user_id == user.id,
                Activity.type == 'click',
                Activity.created_at >= period_start
            )\
            .count()
        
        page_views = session.query(Activity)\
            .filter(
                Activity.user_id == user.id,
                Activity.type == 'page_view',
                Activity.created_at >= period_start
            )\
            .count()
        
        # 4. FEEDBACKS
        feedbacks_given = session.query(Activity)\
            .filter(
                Activity.user_id == user.id,
                Activity.type == 'feedback',
                Activity.created_at >= period_start
            )\
            .count()
        
        # 5. ABANDONS (sessions commencées mais pas terminées)
        # + sessions marquées explicitement comme drop_off
        explicit_dropoffs = session.query(Activity)\
            .filter(
                Activity.user_id == user.id,
                Activity.type == 'drop_off',
                Activity.created_at >= period_start
            )\
            .count()
        
        # Sessions sans fin = commencées il y a > 30min sans session_end
        recent_starts = session.query(Activity)\
            .filter(
                Activity.user_id == user.id,
                Activity.type == 'session_start',
                Activity.created_at >= period_start
            )\
            .all()
        
        incomplete_sessions = 0
        for start in recent_starts:
            # Chercher si session_end existe pour cette session
            end_exists = session.query(Activity)\
                .filter(
                    Activity.user_id == user.id,
                    Activity.type == 'session_end',
                    Activity.created_at > start.created_at
                )\
                .first()
            if not end_exists:
                incomplete_sessions += 1
        
        total_dropoffs = explicit_dropoffs + incomplete_sessions
        
        # 6. SCORE D'ENGAGEMENT (0-100)
        # Formule : 
        # - Base: 50 points
        # + Temps étudié (max 20 pts) : 1 pt par 10 min, plafond 20
        # + Sessions complétées (max 15 pts) : 3 pts par session, plafond 15
        # - Abandons (malus max -15 pts) : -5 pts par abandon, plafond -15
        # + Feedbacks (max 10 pts) : 2 pts par feedback, plafond 10
        
        time_score = min(total_time_minutes / 10, 20)
        completion_score = min(sessions_completed * 3, 15)
        dropoff_penalty = min(total_dropoffs * 5, 15)
        feedback_score = min(feedbacks_given * 2, 10)
        
        engagement_score = int(50 + time_score + completion_score - dropoff_penalty + feedback_score)
        engagement_score = max(0, min(100, engagement_score))  # Clamp 0-100
        
        # 7. TENDANCE (comparaison avec période précédente)
        previous_period_start = period_start - timedelta(days=period_days)
        previous_time = session.query(func.sum(Activity.duration))\
            .filter(
                Activity.user_id == user.id,
                Activity.type == 'session_end',
                Activity.created_at >= previous_period_start,
                Activity.created_at < period_start
            )\
            .scalar() or 0
        
        trend = "up" if total_time_seconds > previous_time else "down" if total_time_seconds < previous_time else "stable"
        
        return {
            "period": {
                "days": period_days,
                "start": period_start.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "metrics": {
                "totalTimeSpent": total_time_minutes,  # minutes
                "totalTimeSpentFormatted": f"{total_time_minutes // 60}h {total_time_minutes % 60}min",
                "sessionsStarted": sessions_started,
                "sessionsCompleted": sessions_completed,
                "sessionsCompletionRate": round((sessions_completed / sessions_started * 100), 1) if sessions_started > 0 else 0,
                "totalClicks": total_clicks,
                "pageViews": page_views,
                "feedbacksGiven": feedbacks_given,
                "dropOffs": total_dropoffs,
                "engagementScore": engagement_score,
                "trend": trend,
                "trendPercentage": round(abs(total_time_seconds - previous_time) / max(previous_time, 1) * 100, 1) if previous_time > 0 else (100 if total_time_seconds > 0 else 0)
            },
            "interpretation": {
                "level": "excellent" if engagement_score >= 80 else "good" if engagement_score >= 60 else "average" if engagement_score >= 40 else "low",
                "message": _get_engagement_message(engagement_score, total_dropoffs)
            },
            "lastUpdated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur calcul engagement: {str(e)}")
    finally:
        session.close()


def _get_engagement_message(score: int, dropoffs: int) -> str:
    """Message personnalisé selon le score"""
    if score >= 80:
        return "🔥 Excellent ! Tu es très assidu. Continue comme ça !"
    elif score >= 60:
        return "👍 Bon travail ! Tu progresses bien."
    elif score >= 40:
        return "💡 Tu es sur la bonne voie. Essaie de te connecter un peu plus régulièrement."
    else:
        if dropoffs > 2:
            return "⚠️ Tu abandonnes souvent tes sessions. Essaie des sessions plus courtes (10-15 min) !"
        return "🌱 Objectif : 10 minutes d'étude par jour pour commencer !"


# ============================================================================
# ENDPOINT 3 : TIMELINE JOUR PAR JOUR (pour graphique)
# ============================================================================

@router.get("/dashboard/engagement/timeline")
async def get_engagement_timeline(
    days: int = 7,
    user=Depends(get_verified_user)
):
    """
    Retourne l'engagement jour par jour pour un graphique temporel
    """
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    
    session = get_db_session()
    
    try:
        timeline = []
        now = datetime.utcnow()
        
        for i in range(days - 1, -1, -1):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            # Temps d'étude ce jour-là
            day_time = session.query(func.sum(Activity.duration))\
                .filter(
                    Activity.user_id == user.id,
                    Activity.type == 'session_end',
                    Activity.created_at >= day_start,
                    Activity.created_at < day_end
                )\
                .scalar() or 0
            
            # Sessions ce jour-là
            day_sessions = session.query(Activity)\
                .filter(
                    Activity.user_id == user.id,
                    Activity.type == 'session_end',
                    Activity.created_at >= day_start,
                    Activity.created_at < day_end
                )\
                .count()
            
            # Clics ce jour-là
            day_clicks = session.query(Activity)\
                .filter(
                    Activity.user_id == user.id,
                    Activity.type == 'click',
                    Activity.created_at >= day_start,
                    Activity.created_at < day_end
                )\
                .count()
            
            # Score du jour (0-100)
            day_score = min(int((day_time / 60) / 10 * 20 + day_sessions * 10 + day_clicks * 2), 100)
            
            timeline.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "dayOfWeek": day_start.strftime("%a"),  # Lun, Mar, Mer...
                "dayShort": day_start.strftime("%d/%m"),
                "timeSpent": int(day_time / 60),  # minutes
                "sessions": day_sessions,
                "clicks": day_clicks,
                "score": day_score,
                "color": _get_score_color(day_score)
            })
        
        return {
            "days": days,
            "timeline": timeline,
            "summary": {
                "averageScore": round(sum(d["score"] for d in timeline) / len(timeline), 1),
                "bestDay": max(timeline, key=lambda x: x["score"])["date"] if timeline else None,
                "totalTime": sum(d["timeSpent"] for d in timeline)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur timeline: {str(e)}")
    finally:
        session.close()


def _get_score_color(score: int) -> str:
    """Couleur selon le score pour le frontend"""
    if score >= 70:
        return "#10B981"  # vert
    elif score >= 40:
        return "#F59E0B"  # orange
    else:
        return "#EF4444"  # rouge


# ============================================================================
# ENDPOINT 4 : ALERTES INTELLIGENTES
# ============================================================================

@router.get("/dashboard/engagement/alerts")
async def get_engagement_alerts(
    user=Depends(get_verified_user)
):
    """
    Retourne des alertes personnalisées basées sur l'engagement
    """
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    
    session = get_db_session()
    
    try:
        alerts = []
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        # Vérifier dernière connexion
        last_activity = session.query(Activity)\
            .filter(
                Activity.user_id == user.id,
                Activity.created_at >= week_ago
            )\
            .order_by(Activity.created_at.desc())\
            .first()
        
        if not last_activity:
            alerts.append({
                "type": "warning",
                "priority": "high",
                "title": "Inactivité détectée",
                "message": "Tu n'as pas été actif depuis plus d'une semaine. Reviens nous voir !",
                "action": "Continuer un support",
                "actionLink": "/student/supports"
            })
        elif (now - last_activity.created_at).days >= 3:
            alerts.append({
                "type": "info",
                "priority": "medium",
                "title": "Tu nous manques !",
                "message": f"Ta dernière activité remonte à {(now - last_activity.created_at).days} jours.",
                "action": "Reprendre l'apprentissage",
                "actionLink": "/student/dashboard"
            })
        
        # Vérifier abandons fréquents
        recent_dropoffs = session.query(Activity)\
            .filter(
                Activity.user_id == user.id,
                Activity.type == 'drop_off',
                Activity.created_at >= week_ago
            )\
            .count()
        
        if recent_dropoffs >= 3:
            alerts.append({
                "type": "warning",
                "priority": "medium",
                "title": "Trop d'abandons",
                "message": "Tu as abandonné plusieurs sessions récemment. Essaie des sessions de 10-15 minutes !",
                "action": "Voir mes supports courts",
                "actionLink": "/student/supports"
            })
        
        # Vérifier temps d'étude
        week_time = session.query(func.sum(Activity.duration))\
            .filter(
                Activity.user_id == user.id,
                Activity.type == 'session_end',
                Activity.created_at >= week_ago
            )\
            .scalar() or 0
        
        week_time_minutes = int(week_time / 60)
        
        if week_time_minutes < 30 and last_activity:
            alerts.append({
                "type": "encouragement",
                "priority": "low",
                "title": "Objectif : 30 min/semaine",
                "message": f"Tu as étudié {week_time_minutes} min cette semaine. Objectif : 30 min !",
                "action": "Commencer une session",
                "actionLink": "/student/chat"
            })
        elif week_time_minutes >= 120:
            alerts.append({
                "type": "success",
                "priority": "low",
                "title": "🎉 Super assiduité !",
                "message": f"{week_time_minutes} minutes d'étude cette semaine. Bravo !",
                "action": None,
                "actionLink": None
            })
        
        return {
            "alerts": alerts,
            "hasUnread": len(alerts) > 0,
            "lastCheck": now.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur alerts: {str(e)}")
    finally:
        session.close()