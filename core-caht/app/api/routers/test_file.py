# app/api/routers/test_file.py - Test endpoints for file functionality

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.services.file_service import FileService
from app.services.ollama_service import OllamaService
from typing import List
import asyncio

router = APIRouter(prefix="/test", tags=["Testing"])

@router.post("/upload-file")
async def test_file_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Test file upload and OCR processing without chat integration"""
    try:
        file_service = FileService()
        
        print(f"Testing upload of: {file.filename}")
        
        # Process the file
        result = await file_service.process_file_attachment(file)
        
        return {
            "success": True,
            "message": f"Successfully processed {file.filename}",
            "data": {
                "attachment_id": result["attachment_id"],
                "file_url": result["file_metadata"]["secure_url"],
                "file_size": result["file_metadata"]["bytes"],
                "ocr_success": result["ocr_result"]["success"],
                "processed_at": result["processed_at"]
            }
        }
        
    except Exception as e:
        print(f"Test upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-ollama")
async def test_ollama_interpretation(
    file: UploadFile = File(...),
    message: str = "What is this document about?",
    db: Session = Depends(get_db)
):
    """Test complete pipeline: file upload → OCR → AI interpretation"""
    try:
        file_service = FileService()
        ollama_service = OllamaService()
        
        print(f"Testing complete pipeline with: {file.filename}")
        
        # Step 1: Process file (upload + OCR)
        attachment_result = await file_service.process_file_attachment(file)
        print("✓ File uploaded and OCR processed")
        
        # Step 2: AI interpretation
        interpretation_result = await ollama_service.interpret_document(
            ocr_data=attachment_result['ocr_result'],
            user_message=message,
            file_metadata=attachment_result['file_metadata']
        )
        print("✓ AI interpretation completed")
        
        return {
            "success": True,
            "file_info": {
                "filename": attachment_result["file_metadata"]["original_filename"],
                "size_mb": round(attachment_result["file_metadata"]["bytes"] / (1024*1024), 2),
                "url": attachment_result["file_metadata"]["secure_url"]
            },
            "ocr_result": {
                "success": attachment_result["ocr_result"]["success"],
                "processing_time": attachment_result["ocr_result"].get("processing_time", 0)
            },
            "ai_interpretation": {
                "success": interpretation_result["success"],
                "response": interpretation_result["interpretation"],
                "model": interpretation_result["model_used"]
            },
            "total_processing_time_seconds": round(
                attachment_result["ocr_result"].get("processing_time", 0), 2
            )
        }
        
    except Exception as e:
        print(f"Test pipeline error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/services")
async def check_all_services():
    """Check health of all external services"""
    health_status = {
        "timestamp": "2025-01-01T00:00:00Z",  # Will be set dynamically
        "services": {}
    }
    
    # Test OCR service
    try:
        import requests
        ocr_response = requests.get("https://ocr.olaji.co/health", timeout=10)
        health_status["services"]["ocr"] = {
            "status": "healthy" if ocr_response.status_code == 200 else "unhealthy",
            "endpoint": "https://ocr.olaji.co/ocr",
            "response_time_ms": ocr_response.elapsed.total_seconds() * 1000
        }
    except Exception as e:
        health_status["services"]["ocr"] = {
            "status": "unhealthy",
            "endpoint": "https://ocr.olaji.co/ocr",
            "error": str(e)
        }
    
    # Test Ollama service
    try:
        ollama_service = OllamaService()
        is_healthy = await ollama_service.health_check()
        health_status["services"]["ollama"] = {
            "status": "healthy" if is_healthy else "unhealthy",
            "endpoint": ollama_service.base_url,
            "model": ollama_service.model
        }
    except Exception as e:
        health_status["services"]["ollama"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Test Cloudinary
    try:
        import cloudinary
        # Simple check by attempting to get account details
        result = cloudinary.api.ping()
        health_status["services"]["cloudinary"] = {
            "status": "healthy",
            "cloud_name": "dowsgqeyn"
        }
    except Exception as e:
        health_status["services"]["cloudinary"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Set timestamp
    from datetime import datetime
    health_status["timestamp"] = datetime.utcnow().isoformat()
    
    # Overall status
    all_healthy = all(
        service["status"] == "healthy" 
        for service in health_status["services"].values()
    )
    health_status["overall_status"] = "healthy" if all_healthy else "degraded"
    
    return health_status

@router.post("/cleanup-test-files")
async def cleanup_test_files():
    """Clean up test files from Cloudinary (use with caution)"""
    try:
        import cloudinary
        import cloudinary.api
        
        # List files with test prefix
        result = cloudinary.api.resources(
            prefix="chat_attachments/",
            max_results=100,
            resource_type="auto"
        )
        
        deleted_count = 0
        for resource in result.get("resources", []):
            try:
                cloudinary.uploader.destroy(resource["public_id"])
                deleted_count += 1
            except Exception as e:
                print(f"Failed to delete {resource['public_id']}: {e}")
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} test files",
            "total_found": len(result.get("resources", []))
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }