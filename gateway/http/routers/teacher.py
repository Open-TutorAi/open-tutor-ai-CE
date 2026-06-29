from fastapi import APIRouter, Depends
from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(
    prefix="/teacher",
    tags=["teacher"]
)


@router.get("/dashboard")
async def get_teacher_dashboard(
    current_user: User = Depends(get_current_user)
):
    # Vérification du rôle
    if current_user.role != "teacher":
        return {
            "success": False,
            "message": "Access denied"
        }

    # Données temporaires (mock data)
    return {
        "success": True,
        "teacher": {
            "name": current_user.name,
            "email": current_user.email,
        },
        "stats": {
            "classes": 0,
            "students": 0,
            "sessions": 0,
        },
        "quick_actions": [
            "Create Class",
            "AI Assistant",
            "View Students"
        ]
    }