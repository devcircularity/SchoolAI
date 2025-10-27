# app/api/routers/whatsapp.py - Fixed QR code endpoint with proper database session
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, validator
from typing import Optional, List
import uuid
from datetime import datetime

from app.api.deps.auth import get_current_user
from app.api.deps.tenancy import require_school
from app.core.db import get_db, set_rls_context
from app.services.whatsapp_service import WhatsAppService
from app.models.school import SchoolWhatsAppSettings

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

class WhatsAppConnectionStatus(BaseModel):
    connected: bool
    ready: bool
    error: Optional[str] = None
    status: Optional[str] = None
    connection_token: Optional[str] = None

class SendMessageRequest(BaseModel):
    phone_number: str
    message: str
    student_id: Optional[str] = None
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Phone number cannot be empty')
        
        # Remove spaces and non-digit characters for validation
        clean_phone = ''.join(filter(str.isdigit, v))
        if len(clean_phone) < 8:
            raise ValueError('Phone number too short')
        
        return v.strip()
    
    @validator('message')
    def validate_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        return v.strip()

class SendMessageResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    phone_number: str
    error: Optional[str] = None
    connection_token: Optional[str] = None

class BulkReminderRequest(BaseModel):
    reminder_type: str  # 'fee_reminder', 'attendance', 'announcement'
    message: Optional[str] = None
    student_ids: Optional[List[str]] = None  # If None, send to all

def get_school_whatsapp_service(school_id: str, db: Session) -> WhatsAppService:
    """Get WhatsApp service instance for the given school WITH database session"""
    return WhatsAppService.for_school(school_id, db_session=db)

@router.get("/status", response_model=WhatsAppConnectionStatus)
async def get_whatsapp_status(
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check WhatsApp connection status for this school"""
    try:
        whatsapp_service = get_school_whatsapp_service(school_id, db)
        health_check = whatsapp_service.check_bridge_health()
        
        return WhatsAppConnectionStatus(
            connected=health_check.get("ready", False),
            ready=health_check.get("ready", False),
            error=health_check.get("error"),
            status=health_check.get("status", "unknown"),
            connection_token=whatsapp_service.connection_token
        )
    except Exception as e:
        return WhatsAppConnectionStatus(
            connected=False,
            ready=False,
            error=str(e),
            status="error"
        )

@router.post("/init")
async def initialize_whatsapp_connection(
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialize WhatsApp connection for this school"""
    try:
        whatsapp_service = get_school_whatsapp_service(school_id, db)
        
        print(f"Initializing WhatsApp connection for school: {school_id}")
        print(f"Connection token: {whatsapp_service.connection_token}")
        
        # Initialize the connection
        init_result = whatsapp_service.initialize_connection()
        
        if init_result.get("success", False):
            # Use SQLAlchemy model instead of raw SQL
            school_uuid = uuid.UUID(school_id)
            
            # Check if settings already exist
            existing_settings = db.query(SchoolWhatsAppSettings).filter(
                SchoolWhatsAppSettings.school_id == school_uuid
            ).first()
            
            if existing_settings:
                # Update existing settings
                existing_settings.is_enabled = True
                existing_settings.bridge_connected = False
                existing_settings.last_connection_check = datetime.utcnow()
                existing_settings.connection_token = whatsapp_service.connection_token
                existing_settings.updated_at = datetime.utcnow()
            else:
                # Create new settings
                new_settings = SchoolWhatsAppSettings(
                    school_id=school_uuid,
                    is_enabled=True,
                    bridge_connected=False,
                    last_connection_check=datetime.utcnow(),
                    connection_token=whatsapp_service.connection_token
                )
                db.add(new_settings)
            
            db.commit()
            
            return {
                "success": True,
                "message": init_result.get("message", "WhatsApp instance initializing"),
                "status": init_result.get("status", "initializing"),
                "connection_token": whatsapp_service.connection_token,
                "next_step": "Call /qr endpoint to get QR code for scanning"
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to initialize WhatsApp connection: {init_result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

@router.post("/connect")
async def connect_whatsapp(
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect WhatsApp for this school (alias for /init endpoint)"""
    try:
        whatsapp_service = get_school_whatsapp_service(school_id, db)
        
        print(f"Connecting WhatsApp for school: {school_id}")
        print(f"Connection token: {whatsapp_service.connection_token}")
        
        # Initialize the connection
        init_result = whatsapp_service.initialize_connection()
        
        if init_result.get("success", False):
            # Use SQLAlchemy model instead of raw SQL
            school_uuid = uuid.UUID(school_id)
            
            # Check if settings already exist
            existing_settings = db.query(SchoolWhatsAppSettings).filter(
                SchoolWhatsAppSettings.school_id == school_uuid
            ).first()
            
            if existing_settings:
                # Update existing settings
                existing_settings.is_enabled = True
                existing_settings.bridge_connected = False
                existing_settings.last_connection_check = datetime.utcnow()
                existing_settings.connection_token = whatsapp_service.connection_token
                existing_settings.updated_at = datetime.utcnow()
            else:
                # Create new settings
                new_settings = SchoolWhatsAppSettings(
                    school_id=school_uuid,
                    is_enabled=True,
                    bridge_connected=False,
                    last_connection_check=datetime.utcnow(),
                    connection_token=whatsapp_service.connection_token
                )
                db.add(new_settings)
            
            db.commit()
            
            return {
                "success": True,
                "message": init_result.get("message", "WhatsApp connection initiated"),
                "status": init_result.get("status", "connecting"),
                "connection_token": whatsapp_service.connection_token,
                "next_step": "Check /qr endpoint for QR code to scan"
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to connect WhatsApp: {init_result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

@router.get("/qr")
async def get_whatsapp_qr(
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)  # FIXED: Added database session dependency
):
    """Get current QR code for this school's WhatsApp instance"""
    try:
        print(f"=== QR CODE ENDPOINT ===")
        print(f"School ID: {school_id}")
        
        # FIXED: Pass database session to service
        whatsapp_service = get_school_whatsapp_service(school_id, db)
        print(f"Service connection token: {whatsapp_service.connection_token}")
        
        qr_result = whatsapp_service.get_qr_code()
        print(f"QR result: {qr_result}")
        
        if qr_result.get("qr"):
            return {
                "success": True,
                "qr_code": qr_result["qr"],
                "status": qr_result.get("status", "qr_ready"),
                "message": qr_result.get("message", "QR code ready for scanning"),
                "source": qr_result.get("source", "unknown"),
                "connection_token": whatsapp_service.connection_token
            }
        else:
            # Return detailed error information
            status = qr_result.get("status", "unknown")
            message = qr_result.get("message", "No QR code available")
            
            print(f"No QR code available - Status: {status}, Message: {message}")
            
            return {
                "success": False,
                "qr_code": None,
                "status": status,
                "message": message,
                "connection_token": whatsapp_service.connection_token,
                "debug_info": {
                    "bridge_url": whatsapp_service.bridge_url,
                    "school_id": school_id
                }
            }
            
    except Exception as e:
        print(f"QR endpoint error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get QR code: {str(e)}")

@router.post("/check-connection")
async def check_whatsapp_connection_status(
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if WhatsApp has been connected (QR code scanned) and update database accordingly"""
    try:
        whatsapp_service = get_school_whatsapp_service(school_id, db)
        
        print(f"Checking connection status for school: {school_id}")
        
        # Check bridge health to see if instance is ready
        health_check = whatsapp_service.check_bridge_health()
        is_ready = health_check.get("ready", False)
        
        print(f"Bridge health check - Ready: {is_ready}, Status: {health_check.get('status')}")
        
        # Update database settings
        school_uuid = uuid.UUID(school_id)
        settings = db.query(SchoolWhatsAppSettings).filter(
            SchoolWhatsAppSettings.school_id == school_uuid
        ).first()
        
        if settings:
            # Update connection status
            settings.bridge_connected = is_ready
            settings.last_connection_check = datetime.utcnow()
            settings.updated_at = datetime.utcnow()
            
            # If connected, clear QR code (it's no longer needed)
            if is_ready:
                settings.qr_code = None
                settings.qr_generated_at = None
                print(f"Connection established - QR code cleared for school {school_id}")
            
            db.commit()
        
        return {
            "connected": is_ready,
            "ready": is_ready,
            "status": health_check.get("status", "unknown"),
            "message": "Connected successfully" if is_ready else "Waiting for QR code scan",
            "connection_token": whatsapp_service.connection_token,
            "last_check": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Connection check error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check connection: {str(e)}")

@router.get("/connection-history")
async def get_connection_history(
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get WhatsApp connection history for this school"""
    try:
        school_uuid = uuid.UUID(school_id)
        settings = db.query(SchoolWhatsAppSettings).filter(
            SchoolWhatsAppSettings.school_id == school_uuid
        ).first()
        
        if not settings:
            return {
                "exists": False,
                "message": "No WhatsApp settings found for this school"
            }
        
        return {
            "exists": True,
            "is_enabled": settings.is_enabled,
            "bridge_connected": settings.bridge_connected,
            "connection_token": settings.connection_token,
            "has_qr_code": settings.qr_code is not None,
            "qr_generated_at": settings.qr_generated_at.isoformat() if settings.qr_generated_at else None,
            "last_connection_check": settings.last_connection_check.isoformat() if settings.last_connection_check else None,
            "last_successful_message": settings.last_successful_message.isoformat() if settings.last_successful_message else None,
            "created_at": settings.created_at.isoformat(),
            "updated_at": settings.updated_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connection history: {str(e)}")

@router.post("/send", response_model=SendMessageResponse)
async def send_whatsapp_message(
    request: SendMessageRequest,
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a WhatsApp message using this school's instance"""
    try:
        print(f"=== WHATSAPP SEND REQUEST ===")
        print(f"School ID: {school_id}")
        print(f"Phone: '{request.phone_number}'")
        print(f"Message: '{request.message[:50]}...'")
        print(f"Student ID: {request.student_id}")
        
        whatsapp_service = get_school_whatsapp_service(school_id, db)
        print(f"Using connection token: {whatsapp_service.connection_token}")
        
        # Verify phone number format and clean it
        clean_phone = whatsapp_service.clean_phone_number(request.phone_number)
        print(f"Cleaned phone: '{clean_phone}'")
        
        if not clean_phone:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid phone number format: {request.phone_number}"
            )
        
        # Send the message
        success = whatsapp_service.send_whatsapp_message(clean_phone, request.message)
        
        print(f"Send result: {success}")
        
        # Update last successful message time if successful
        if success:
            school_uuid = uuid.UUID(school_id)
            settings = db.query(SchoolWhatsAppSettings).filter(
                SchoolWhatsAppSettings.school_id == school_uuid
            ).first()
            
            if settings:
                settings.last_successful_message = datetime.utcnow()
                settings.updated_at = datetime.utcnow()
                db.commit()
        
        # Log the message if successful
        if success and request.student_id:
            try:
                db.execute(
                    text("""
                        INSERT INTO whatsapp_notifications 
                        (id, school_id, student_id, notification_type, recipient_phone, 
                         sent_at, status, metadata, created_at, updated_at)
                        VALUES (gen_random_uuid(), :school_id, :student_id, 'manual_message', 
                               :recipient_phone, CURRENT_TIMESTAMP, 'sent', 
                               :metadata, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """),
                    {
                        'school_id': school_id,
                        'student_id': request.student_id,
                        'recipient_phone': clean_phone,
                        'metadata': request.message
                    }
                )
                db.commit()
                print("Message logged to database successfully")
            except Exception as log_error:
                print(f"Failed to log WhatsApp message: {log_error}")
        
        return SendMessageResponse(
            success=success,
            message_id=None,  # Bridge doesn't return message ID in our implementation
            phone_number=clean_phone,
            error=None if success else "Message send failed",
            connection_token=whatsapp_service.connection_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"=== WHATSAPP SEND ERROR ===")
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@router.get("/verify/{phone_number}")
async def verify_whatsapp_number(
    phone_number: str,
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify if a phone number is registered on WhatsApp"""
    try:
        whatsapp_service = get_school_whatsapp_service(school_id, db)
        is_registered = whatsapp_service.verify_whatsapp_registration(phone_number)
        
        return {
            "registered": is_registered,
            "phone_number": phone_number,
            "connection_token": whatsapp_service.connection_token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@router.get("/debug/bridge-test")
async def test_bridge_direct(
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Direct bridge connectivity test for debugging"""
    try:
        whatsapp_service = get_school_whatsapp_service(school_id, db)
        
        # Test bridge health directly
        import requests
        
        bridge_url = whatsapp_service.bridge_url
        api_key = whatsapp_service.api_key
        connection_token = whatsapp_service.connection_token
        
        print(f"Testing bridge connectivity:")
        print(f"  URL: {bridge_url}")
        print(f"  Token: {connection_token}")
        print(f"  API Key: {api_key[:10]}...")
        
        # Test 1: Overall health
        try:
            health_resp = requests.get(f"{bridge_url}/health", 
                                     headers={'x-api-key': api_key}, 
                                     timeout=10)
            health_status = health_resp.status_code
            health_data = health_resp.json() if health_resp.status_code == 200 else {}
        except Exception as e:
            health_status = f"Error: {e}"
            health_data = {}
        
        # Test 2: Instance status
        try:
            status_resp = requests.get(f"{bridge_url}/status", 
                                     headers={
                                         'x-api-key': api_key,
                                         'x-instance-token': connection_token
                                     }, 
                                     timeout=10)
            status_status = status_resp.status_code
            status_data = status_resp.json() if status_resp.status_code == 200 else {}
        except Exception as e:
            status_status = f"Error: {e}"
            status_data = {}
        
        # Test 3: QR endpoint
        try:
            qr_resp = requests.get(f"{bridge_url}/qr", 
                                 headers={
                                     'x-api-key': api_key,
                                     'x-instance-token': connection_token
                                 }, 
                                 timeout=10)
            qr_status = qr_resp.status_code
            qr_data = qr_resp.json() if qr_resp.status_code == 200 else {}
            
            # Check if QR code exists and its length
            qr_exists = bool(qr_data.get('qr'))
            qr_length = len(qr_data.get('qr', '')) if qr_exists else 0
            
        except Exception as e:
            qr_status = f"Error: {e}"
            qr_data = {}
            qr_exists = False
            qr_length = 0
        
        return {
            "bridge_url": bridge_url,
            "connection_token": connection_token,
            "tests": {
                "health_check": {
                    "status": health_status,
                    "data": health_data
                },
                "instance_status": {
                    "status": status_status,
                    "data": status_data
                },
                "qr_endpoint": {
                    "status": qr_status,
                    "data": qr_data,
                    "qr_exists": qr_exists,
                    "qr_length": qr_length
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bridge test failed: {str(e)}")

# ... [rest of the endpoints remain the same but updated to use get_school_whatsapp_service(school_id, db)]

@router.post("/disconnect") 
async def disconnect_whatsapp(
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect WhatsApp Web session for this school"""
    try:
        whatsapp_service = get_school_whatsapp_service(school_id, db)
        disconnect_result = whatsapp_service.logout()
        
        # Update using SQLAlchemy model
        school_uuid = uuid.UUID(school_id)
        settings = db.query(SchoolWhatsAppSettings).filter(
            SchoolWhatsAppSettings.school_id == school_uuid
        ).first()
        
        if settings:
            settings.bridge_connected = False
            settings.is_enabled = False
            settings.qr_code = None  # Clear QR code on disconnect
            settings.qr_generated_at = None
            settings.last_connection_check = datetime.utcnow()
            settings.updated_at = datetime.utcnow()
            db.commit()
        
        print(f"WhatsApp disconnected for school: {school_id}")
        
        return {
            "success": disconnect_result.get("success", True),
            "message": "WhatsApp disconnected successfully",
            "connection_token": whatsapp_service.connection_token
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disconnect failed: {str(e)}")

@router.get("/debug/connection-info")
async def get_connection_debug_info(
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get connection debug information for this school"""
    try:
        whatsapp_service = get_school_whatsapp_service(school_id, db)
        health_check = whatsapp_service.check_bridge_health()
        
        return {
            "school_id": school_id,
            "connection_token": whatsapp_service.connection_token,
            "bridge_url": whatsapp_service.bridge_url,
            "health_check": health_check,
            "headers": whatsapp_service._get_headers()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug info failed: {str(e)}")

@router.get("/debug/request-format")
async def get_request_format():
    """Get the expected request format for testing multi-instance WhatsApp"""
    return {
        "workflow": {
            "1": "POST /whatsapp/init - Initialize school's WhatsApp instance",
            "2": "GET /whatsapp/qr - Get QR code for scanning",
            "3": "POST /whatsapp/check-connection - Check if QR code was scanned",
            "4": "POST /whatsapp/send - Send messages once connected"
        },
        "qr_code_lifecycle": {
            "generated": "QR code is stored in database when fetched from bridge",
            "scanned": "When scanned, connection becomes 'ready' and QR code is cleared",
            "persistent": "QR codes are cached for 10 minutes to avoid repeated bridge calls"
        }
    }