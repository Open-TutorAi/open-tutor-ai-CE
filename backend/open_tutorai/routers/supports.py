from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import List, Optional
from pydantic import BaseModel
import logging
import uuid
from datetime import datetime
import os
import json
from fastapi.responses import JSONResponse

from open_webui.utils.auth import get_verified_user
from open_tutorai.models.database import Support, SupportFile, Base
from sqlalchemy.orm import sessionmaker
from open_webui.internal.db import engine

# Setup logging
log = logging.getLogger(__name__)
log.setLevel("INFO")

router = APIRouter()

# Make sure upload directory exists
UPLOAD_DIR = os.path.join("uploads", "support_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Models for request and response
class SupportCreateRequest(BaseModel):
    title: str
    short_description: Optional[str] = None
    subject: str
    custom_subject: Optional[str] = None
    course_id: Optional[str] = None
    learning_objective: Optional[str] = None
    learning_type: Optional[str] = None
    level: Optional[str] = None
    content_language: Optional[str] = "English"
    estimated_duration: Optional[str] = None
    access_type: Optional[str] = "Private"
    keywords: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    avatar_id: Optional[str] = None
    chat_id: Optional[str] = None

# Support response model
class SupportResponse(BaseModel):
    id: str
    user_id: str
    title: str
    short_description: Optional[str] = None
    subject: str
    custom_subject: Optional[str] = None
    course_id: Optional[str] = None
    learning_objective: Optional[str] = None
    learning_type: Optional[str] = None
    level: Optional[str] = None
    content_language: Optional[str] = None
    estimated_duration: Optional[str] = None
    access_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    avatar_id: Optional[str] = None
    status: str
    chat_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

def get_db_session():
    """Get a database session using the same engine as OpenWebUI"""
    # Log for debugging
    print("Using OpenWebUI database engine for supports")
    
    # Create session
    Session = sessionmaker(bind=engine)
    return Session()

@router.post("/supports/create")
async def create_support(
    support_data: SupportCreateRequest,
    user = Depends(get_verified_user)
):
    """
    Create a new support request
    """
    try:
        # Generate a unique ID for the support request itself
        support_id = str(uuid.uuid4())
        
        # The chat_id is now optional - will be updated later
        chat_id = support_data.chat_id 
        
        # Use default user ID if user object is None
        user_id = user.id if user else "anonymous"
        
        # Prepare keywords
        keywords_str = ",".join(support_data.keywords) if support_data.keywords else None
        
        # Create support object
        support = Support(
            id=support_id,
            user_id=user_id,
            title=support_data.title,
            short_description=support_data.short_description,
            subject=support_data.subject,
            custom_subject=support_data.custom_subject,
            course_id=support_data.course_id,
            learning_objective=support_data.learning_objective,
            learning_type=support_data.learning_type,
            level=support_data.level,
            content_language=support_data.content_language,
            estimated_duration=support_data.estimated_duration,
            access_type=support_data.access_type,
            keywords=keywords_str,
            start_date=support_data.start_date,
            end_date=support_data.end_date,
            avatar_id=support_data.avatar_id,
            status="pending",
            chat_id=chat_id,  # This can be null now
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Save to database
        session = get_db_session()
        
        try:
            session.add(support)
            session.commit()
            
            # Create response object
            response = SupportResponse(
                id=support.id,
                user_id=support.user_id,
                title=support.title,
                short_description=support.short_description,
                subject=support.subject,
                custom_subject=support.custom_subject,
                course_id=support.course_id,
                learning_objective=support.learning_objective,
                learning_type=support.learning_type,
                level=support.level,
                content_language=support.content_language,
                estimated_duration=support.estimated_duration,
                access_type=support.access_type,
                keywords=support.keywords.split(",") if support.keywords else None,
                start_date=support.start_date,
                end_date=support.end_date,
                avatar_id=support.avatar_id,
                status=support.status,
                chat_id=support.chat_id,
                created_at=support.created_at,
                updated_at=support.updated_at
            )
            
            return response
        finally:
            session.close()
            
    except Exception as e:
        log.error(f"Error creating support request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create support request: {str(e)}")

@router.post("/supports/upload-file")
async def upload_support_file(
    support_id: str = Form(...),
    file: UploadFile = File(...),
    user = Depends(get_verified_user)
):
    """
    Upload a file for a support request
    """
    try:
        # Generate a unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        save_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_extension}")
        
        # Save the file
        with open(save_path, "wb") as f:
            contents = await file.read()
            f.write(contents)
        
        # Save file info to database
        file_record = SupportFile(
            id=file_id,
            support_id=support_id,
            filename=file.filename,
            file_path=save_path,
            file_type=file.content_type,
            file_size=len(contents),
            created_at=datetime.now()
        )
        
        # Save to database
        session = get_db_session()
        
        try:
            session.add(file_record)
            session.commit()
            return {"id": file_id, "filename": file.filename, "status": "success"}
        finally:
            session.close()
            
    except Exception as e:
        log.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@router.get("/supports/list")
async def get_support_requests(
    status: Optional[str] = None,
    user = Depends(get_verified_user)
):
    """
    Get list of support requests for the current user
    """
    try:
        session = get_db_session()
        
        try:
            # Use default filter if user is None
            if user:
                query = session.query(Support).filter(Support.user_id == user.id)
            else:
                # For anonymous users, show only public records or none
                query = session.query(Support).filter(Support.access_type == "Public")
            
            if status:
                query = query.filter(Support.status == status)
                
            supports = query.order_by(Support.created_at.desc()).all()
            
            results = []
            for support in supports:
                results.append({
                    "id": support.id,
                    "user_id": support.user_id,
                    "title": support.title,
                    "short_description": support.short_description,
                    "subject": support.subject,
                    "custom_subject": support.custom_subject,
                    "course_id": support.course_id,
                    "learning_objective": support.learning_objective,
                    "learning_type": support.learning_type,
                    "level": support.level,
                    "content_language": support.content_language,
                    "estimated_duration": support.estimated_duration,
                    "access_type": support.access_type,
                    "keywords": support.keywords.split(",") if support.keywords else None,
                    "start_date": support.start_date,
                    "end_date": support.end_date,
                    "avatar_id": support.avatar_id,
                    "status": support.status,
                    "chat_id": support.chat_id,
                    "created_at": support.created_at.isoformat() if support.created_at else None,
                    "updated_at": support.updated_at.isoformat() if support.updated_at else None
                })
            
            return results
        finally:
            session.close()
            
    except Exception as e:
        log.error(f"Error getting support requests: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get support requests: {str(e)}")

@router.get("/supports/{support_id}")
async def get_support_by_id(
    support_id: str,
    user = Depends(get_verified_user)
):
    """
    Get a support request by ID
    """
    try:
        session = get_db_session()
        
        try:
            # Build query based on user
            if user:
                support = session.query(Support).filter(
                    Support.id == support_id,
                    Support.user_id == user.id
                ).first()
            else:
                # For anonymous users, only get public records
                support = session.query(Support).filter(
                    Support.id == support_id,
                    Support.access_type == "Public"
                ).first()
            
            if not support:
                raise HTTPException(status_code=404, detail="Support request not found")
                
            return {
                "id": support.id,
                "user_id": support.user_id,
                "title": support.title,
                "short_description": support.short_description,
                "subject": support.subject,
                "custom_subject": support.custom_subject,
                "course_id": support.course_id,
                "learning_objective": support.learning_objective,
                "learning_type": support.learning_type,
                "level": support.level,
                "content_language": support.content_language,
                "estimated_duration": support.estimated_duration,
                "access_type": support.access_type,
                "keywords": support.keywords.split(",") if support.keywords else None,
                "start_date": support.start_date,
                "end_date": support.end_date,
                "avatar_id": support.avatar_id,
                "status": support.status,
                "chat_id": support.chat_id,
                "created_at": support.created_at.isoformat() if support.created_at else None,
                "updated_at": support.updated_at.isoformat() if support.updated_at else None
            }
        finally:
            session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting support request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get support request: {str(e)}")

@router.patch("/supports/{support_id}/update-chat")
async def update_support_chat_id(
    support_id: str,
    chat_id: Optional[str] = None,
    user = Depends(get_verified_user)
):
    """
    Update the chat_id of a support request.
    This endpoint receives chat_id as a query parameter.
    """
    log.info(f"Received update request for support {support_id} with chat_id {chat_id}")
    
    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id query parameter is required")
    
    try:
        session = get_db_session()
        
        try:
            # First check if the support exists and belongs to the user
            if user:
                support = session.query(Support).filter(
                    Support.id == support_id,
                    Support.user_id == user.id
                ).first()
            else:
                # For anonymous users, only update public records
                support = session.query(Support).filter(
                    Support.id == support_id,
                    Support.access_type == "Public"
                ).first()
            
            if not support:
                log.warning(f"Support {support_id} not found for user {user.id if user else 'anonymous'}")
                raise HTTPException(status_code=404, detail="Support request not found")
            
            # Log current values
            log.info(f"Updating support {support_id} - Current chat_id: {support.chat_id}, New chat_id: {chat_id}")
            
            # Update the chat_id
            support.chat_id = chat_id
            support.updated_at = datetime.now()
            session.commit()
            
            log.info(f"Successfully updated support {support_id} with chat_id {chat_id}")
            
            return {
                "id": support.id,
                "chat_id": support.chat_id,
                "status": "success",
                "message": "Chat ID updated successfully"
            }
        finally:
            session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error updating support chat ID: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update support chat ID: {str(e)}") 