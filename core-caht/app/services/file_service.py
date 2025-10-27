# app/services/file_service.py - Fixed OCR processing method

import os
import requests
import json
from typing import Optional, Dict, Any, List
from fastapi import UploadFile, HTTPException
import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from datetime import datetime
import uuid
import tempfile

# Configure Cloudinary
cloudinary.config(
    cloud_name="dowsgqeyn",
    api_key="214339398849259",
    api_secret="7ngw-OIFYfjA99hN_H-inSS-IGg"
)

class FileService:
    """Service for handling file uploads, OCR processing, and AI interpretation"""
    
    def __init__(self):
        self.ocr_endpoint = "https://ocr.olaji.co/ocr"
        self.cloudinary_upload_preset = "olajiset"
        self.allowed_file_types = {
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
            'image/webp', 'image/bmp', 'image/tiff',
            'application/pdf'
        }
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def validate_file(self, file: UploadFile) -> bool:
        """Validate file type and size"""
        # Check file type
        if file.content_type not in self.allowed_file_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}. Supported types: images and PDFs"
            )
        
        # Check file size (this is approximate as we haven't read the full file yet)
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Seek back to beginning
        
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size} bytes. Maximum allowed: {self.max_file_size} bytes"
            )
        
        return True
    
    async def upload_to_cloudinary(self, file: UploadFile) -> Dict[str, Any]:
        """Upload file to Cloudinary and return metadata"""
        try:
            self.validate_file(file)
            
            # Read file content
            file_content = await file.read()
            
            # Generate unique public_id
            unique_id = str(uuid.uuid4())
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
            public_id = f"chat_attachments/{unique_id}"
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_content,
                public_id=public_id,
                upload_preset=self.cloudinary_upload_preset,
                resource_type="auto",  # Automatically detect if it's image, video, or raw
                overwrite=False,
                unique_filename=True,
                use_filename=True,
                filename_override=f"{unique_id}.{file_extension}" if file_extension else unique_id
            )
            
            return {
                "public_id": upload_result.get("public_id"),
                "secure_url": upload_result.get("secure_url"),
                "url": upload_result.get("url"),
                "format": upload_result.get("format"),
                "resource_type": upload_result.get("resource_type"),
                "bytes": upload_result.get("bytes"),
                "width": upload_result.get("width"),
                "height": upload_result.get("height"),
                "created_at": upload_result.get("created_at"),
                "original_filename": file.filename,
                "content_type": file.content_type
            }
            
        except CloudinaryError as e:
            print(f"Cloudinary upload error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
        except Exception as e:
            print(f"File upload error: {e}")
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    
    async def process_with_ocr(self, file: UploadFile) -> Dict[str, Any]:
        """Send file directly to OCR endpoint (not URL) and get processed data"""
        try:
            # Reset file pointer to beginning
            await file.seek(0)
            file_content = await file.read()
            await file.seek(0)  # Reset again for potential reuse
            
            # Prepare file for OCR request (send actual file, not URL)
            files = {
                'file': (file.filename, file_content, file.content_type)
            }
            
            # Optional: Add any additional parameters your OCR service expects
            data = {
                'extract_text': 'true',
                'extract_tables': 'true', 
                'language': 'eng'
            }
            
            print(f"Sending file {file.filename} ({len(file_content)} bytes) to OCR service...")
            
            response = requests.post(
                self.ocr_endpoint,
                files=files,
                data=data,
                timeout=60  # 60 seconds timeout
            )
            
            print(f"OCR response status: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text
                print(f"OCR error response: {error_detail}")
                raise HTTPException(
                    status_code=500,
                    detail=f"OCR processing failed: {response.status_code} - {error_detail}"
                )
            
            ocr_result = response.json()
            print(f"OCR processing completed successfully")
            
            return {
                "success": True,
                "ocr_data": ocr_result,
                "processed_at": datetime.utcnow().isoformat(),
                "processing_time": response.elapsed.total_seconds()
            }
            
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=408, detail="OCR processing timed out")
        except requests.exceptions.RequestException as e:
            print(f"OCR request error: {e}")
            raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
        except Exception as e:
            print(f"OCR processing error: {e}")
            raise HTTPException(status_code=500, detail=f"OCR processing error: {str(e)}")
    
    async def process_with_ocr_from_url(self, file_url: str) -> Dict[str, Any]:
        """Alternative method: Send URL to OCR endpoint if it supports URL processing"""
        try:
            # If your OCR service also supports URL input, use this format
            payload = {
                "url": file_url,
                "extract_text": True,
                "extract_tables": True,
                "extract_forms": True,
                "language": "eng"
            }
            
            response = requests.post(
                self.ocr_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"OCR processing failed: {response.status_code} - {response.text}"
                )
            
            ocr_result = response.json()
            
            return {
                "success": True,
                "ocr_data": ocr_result,
                "processed_at": datetime.utcnow().isoformat(),
                "processing_time": response.elapsed.total_seconds()
            }
            
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=408, detail="OCR processing timed out")
        except requests.exceptions.RequestException as e:
            print(f"OCR request error: {e}")
            raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
        except Exception as e:
            print(f"OCR processing error: {e}")
            raise HTTPException(status_code=500, detail=f"OCR processing error: {str(e)}")
    
    async def process_file_attachment(self, file: UploadFile) -> Dict[str, Any]:
        """Complete file processing pipeline: upload -> OCR -> return metadata"""
        try:
            # Step 1: Process with OCR first (before upload to avoid unnecessary storage if OCR fails)
            print(f"Processing file with OCR: {file.filename}")
            ocr_result = await self.process_with_ocr(file)
            print(f"OCR processing completed successfully")
            
            # Step 2: Upload to Cloudinary (after successful OCR)
            print(f"Uploading to Cloudinary: {file.filename}")
            upload_result = await self.upload_to_cloudinary(file)
            print(f"File uploaded successfully: {upload_result['secure_url']}")
            
            # Step 3: Combine results
            return {
                "file_metadata": upload_result,
                "ocr_result": ocr_result,
                "attachment_id": str(uuid.uuid4()),
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"File processing pipeline error: {e}")
            # If we uploaded to Cloudinary but OCR failed, we should clean up
            # (though in this revised flow, OCR happens first)
            raise
    
    def delete_file(self, public_id: str) -> bool:
        """Delete file from Cloudinary"""
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except Exception as e:
            print(f"Error deleting file {public_id}: {e}")
            return False