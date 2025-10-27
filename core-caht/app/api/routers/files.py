# app/api/routers/files.py - New router for immediate file uploads

import time
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import InvalidTokenError
from typing import Optional

from app.core.db import get_db, set_rls_context
from app.services.file_service import FileService
from app.schemas.chat import prepare_for_json_storage

router = APIRouter(prefix="/files", tags=["Files"])

def verify_auth_and_get_context(
    authorization: str = Header(...),
    x_school_id: str = Header(..., alias="X-School-ID"),
    db: Session = Depends(get_db)
):
    """Authentication verification and context setup"""
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        from sqlalchemy import text
        membership = db.execute(
            text("""
                SELECT sm.user_id, sm.school_id, sm.role, u.full_name
                FROM schoolmember sm
                JOIN users u ON sm.user_id = u.id
                WHERE sm.user_id = :user_id AND sm.school_id = :school_id
            """),
            {"user_id": user_id, "school_id": x_school_id}
        ).first()
        
        if not membership:
            raise HTTPException(status_code=403, detail="Access denied to this school")
        
        set_rls_context(db, user_id=user_id, school_id=x_school_id)
        
        return {
            "user_id": user_id,
            "school_id": x_school_id,
            "role": membership.role,
            "full_name": membership.full_name
        }
        
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@router.post("/upload-immediate")
async def upload_file_immediate(
    file: UploadFile = File(...),
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db),
):
    """
    Upload file immediately to Cloudinary and perform OCR processing.
    Returns file metadata and OCR results without creating a chat message.
    """
    try:
        start_time = time.time()
        
        print(f"=== IMMEDIATE UPLOAD START ===")
        print(f"File: {file.filename} ({file.size} bytes, {file.content_type})")
        print(f"User: {ctx['user_id']}, School: {ctx['school_id']}")
        
        file_service = FileService()
        
        # Process file: Upload to Cloudinary + OCR
        attachment_data = await file_service.process_file_attachment(file)
        
        processing_time = time.time() - start_time
        
        print(f"✅ Immediate upload completed in {processing_time:.2f}s")
        print(f"Attachment ID: {attachment_data['attachment_id']}")
        print(f"Cloudinary URL: {attachment_data['file_metadata']['secure_url']}")
        print(f"OCR Success: {attachment_data['ocr_result']['success']}")
        
        # Store upload record in database for tracking (optional)
        # This helps with cleanup and prevents abuse
        try:
            from sqlalchemy import text
            db.execute(
                text("""
                    INSERT INTO file_uploads (
                        attachment_id, user_id, school_id, 
                        original_filename, content_type, file_size,
                        cloudinary_url, cloudinary_public_id,
                        upload_timestamp, ocr_processed
                    ) VALUES (
                        :attachment_id, :user_id, :school_id,
                        :original_filename, :content_type, :file_size,
                        :cloudinary_url, :cloudinary_public_id,
                        NOW(), :ocr_processed
                    )
                """),
                {
                    "attachment_id": attachment_data['attachment_id'],
                    "user_id": ctx['user_id'],
                    "school_id": ctx['school_id'],
                    "original_filename": attachment_data['file_metadata']['original_filename'],
                    "content_type": attachment_data['file_metadata']['content_type'],
                    "file_size": attachment_data['file_metadata']['bytes'],
                    "cloudinary_url": attachment_data['file_metadata']['secure_url'],
                    "cloudinary_public_id": attachment_data['file_metadata']['public_id'],
                    "ocr_processed": attachment_data['ocr_result']['success']
                }
            )
            db.commit()
            print(f"✅ Upload record saved to database")
        except Exception as e:
            print(f"⚠️ Failed to save upload record: {e}")
            # Don't fail the upload if database save fails
            db.rollback()
        
        return {
            "success": True,
            "attachment_id": attachment_data['attachment_id'],
            "file_metadata": attachment_data['file_metadata'],
            "ocr_result": attachment_data['ocr_result'],
            "processed_at": attachment_data['processed_at'],
            "processing_time": processing_time
        }
        
    except Exception as e:
        print(f"❌ Immediate upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"File upload failed: {str(e)}"
        )

@router.delete("/delete/{attachment_id}")
async def delete_uploaded_file(
    attachment_id: str,
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db),
):
    """
    Delete an uploaded file from Cloudinary and database.
    This is called when user removes a file before sending the message.
    """
    try:
        print(f"=== DELETE UPLOADED FILE ===")
        print(f"Attachment ID: {attachment_id}")
        print(f"User: {ctx['user_id']}")
        
        # Get file info from database
        from sqlalchemy import text
        file_record = db.execute(
            text("""
                SELECT cloudinary_public_id, original_filename
                FROM file_uploads 
                WHERE attachment_id = :attachment_id 
                AND user_id = :user_id 
                AND school_id = :school_id
            """),
            {
                "attachment_id": attachment_id,
                "user_id": ctx['user_id'],
                "school_id": ctx['school_id']
            }
        ).first()
        
        if not file_record:
            print(f"⚠️ File not found in database: {attachment_id}")
            raise HTTPException(status_code=404, detail="File not found")
        
        cloudinary_public_id, filename = file_record
        
        # Delete from Cloudinary
        try:
            file_service = FileService()
            deletion_result = file_service.delete_from_cloudinary(cloudinary_public_id)
            print(f"✅ Deleted from Cloudinary: {deletion_result}")
        except Exception as e:
            print(f"⚠️ Failed to delete from Cloudinary: {e}")
            # Continue with database deletion even if Cloudinary fails
        
        # Delete from database
        db.execute(
            text("""
                DELETE FROM file_uploads 
                WHERE attachment_id = :attachment_id 
                AND user_id = :user_id 
                AND school_id = :school_id
            """),
            {
                "attachment_id": attachment_id,
                "user_id": ctx['user_id'],
                "school_id": ctx['school_id']
            }
        )
        db.commit()
        
        print(f"✅ File deleted successfully: {filename}")
        return {"success": True, "message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Delete file error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(e)}"
        )