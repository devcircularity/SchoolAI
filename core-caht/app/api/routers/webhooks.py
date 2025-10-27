# app/api/routers/webhooks.py

from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
import hmac
import hashlib
import json
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone

from app.core.db import get_db
from app.api.deps.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Webhooks"])

# CRITICAL: This MUST match your Android HttpForwarder.kt SHARED_SECRET exactly
WEBHOOK_SHARED_SECRET = "super-long-random-string"

def verify_webhook_signature(body: bytes, signature_header: str) -> bool:
    """
    Verify HMAC-SHA256 signature from X-Webhook-Signature header.
    
    Args:
        body: Raw request body as bytes
        signature_header: The X-Webhook-Signature header value (e.g., "sha256=abc123...")
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        if not signature_header.startswith("sha256="):
            return False
        
        received_signature = signature_header[7:]  # Remove "sha256=" prefix
        
        # Compute HMAC-SHA256 of the raw body
        mac = hmac.new(
            key=WEBHOOK_SHARED_SECRET.encode('utf-8'),
            msg=body,
            digestmod=hashlib.sha256
        )
        expected_signature = mac.hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, received_signature)
        
    except Exception:
        return False

@router.post("/sms")
async def receive_sms_webhook(
    request: Request,
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint to receive SMS notifications from Android app.
    
    Expected payload:
    {
        "source": "android_notification", 
        "message": "SMS message content..."
    }
    
    Security:
    - Requires valid JWT token in Authorization header
    - Requires valid HMAC-SHA256 signature in X-Webhook-Signature header
    """
    try:
        # Get raw request body for signature verification
        raw_body = await request.body()
        
        # Get signature from header
        signature_header = request.headers.get("X-Webhook-Signature")
        if not signature_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing signature"
            )
        
        # Verify signature
        if not verify_webhook_signature(raw_body, signature_header):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        
        # Parse the JSON payload
        try:
            payload = json.loads(raw_body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # Validate payload structure
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payload must be a JSON object"
            )
        
        source = payload.get("source")
        message = payload.get("message")
        
        if not source or not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'source' or 'message' fields"
            )
        
        # Print the received message
        print(f"SMS received: {message}")
        
        # Get user info from JWT context
        user = ctx["user"]
        claims = ctx["claims"]
        school_id = claims.get("active_school_id")
        
        # Process the SMS message with enhanced processor
        try:
            from app.services.sms_processor import SMSProcessor
            
            sms_processor = SMSProcessor(db, user.id, school_id)
            processing_result = await sms_processor.process_sms_message(source, message)
            
            sms_record = processing_result["sms_record"]
            payment_result = processing_result.get("payment_result")
            
            # Log payment processing result
            if payment_result:
                if payment_result.get("success"):
                    print(f"M-Pesa payment processed: Student {payment_result.get('student_name')} paid KES {payment_result.get('amount')}")
                else:
                    print(f"M-Pesa payment failed: {payment_result.get('error')}")
            
        except Exception as e:
            print(f"SMS processing error: {e}")
            # Fallback to basic processing
            sms_record = {
                "id": f"sms_{int(datetime.now(timezone.utc).timestamp())}",
                "user_id": str(user.id),
                "school_id": school_id,
                "source": source,
                "message": message,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "user_email": user.email,
                "user_name": user.full_name,
                "processing_error": str(e)
            }
        
        # Build response based on processing results
        response_data = {
            "success": True,
            "message": "SMS processed successfully",
            "record_id": sms_record["id"],
            "user_id": str(user.id),
            "school_id": school_id
        }
        
        # Add payment processing info if available
        if payment_result:
            response_data["payment_processed"] = payment_result.get("success", False)
            if payment_result.get("success"):
                response_data["payment_info"] = {
                    "student_id": payment_result.get("student_id"),
                    "student_name": payment_result.get("student_name"),
                    "amount": payment_result.get("amount"),
                    "reference": payment_result.get("reference")
                }
                
                # Add notification status
                notifications = payment_result.get("notifications", {})
                if notifications:
                    response_data["notifications"] = {
                        "email_sent": notifications.get("email_sent", False),
                        "sms_sent": notifications.get("sms_sent", False),
                        "whatsapp_sent": notifications.get("whatsapp_sent", False)
                    }
                    
                    # Log notification summary
                    sent_channels = []
                    if notifications.get("email_sent"): sent_channels.append("Email")
                    if notifications.get("sms_sent"): sent_channels.append("SMS")
                    if notifications.get("whatsapp_sent"): sent_channels.append("WhatsApp")
                    
                    if sent_channels:
                        print(f"Parent notifications sent via: {', '.join(sent_channels)}")
                    else:
                        print("No parent notifications were sent")
                        
            else:
                response_data["payment_error"] = payment_result.get("error")
        
        return response_data
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/sms/test")
async def test_sms_webhook(
    request: Request,
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test endpoint for SMS webhooks - same signature verification but with detailed logging.
    Useful for debugging signature issues.
    """
    try:
        # Get raw request body for signature verification
        raw_body = await request.body()
        
        # Get signature from header
        signature_header = request.headers.get("X-Webhook-Signature")
        
        if not signature_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing signature"
            )
        
        # Verify signature
        if not verify_webhook_signature(raw_body, signature_header):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        
        # Parse the JSON payload
        try:
            payload = json.loads(raw_body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # Print the test message
        if "message" in payload:
            print(f"Test SMS: {payload['message']}")
        
        user = ctx["user"]
        claims = ctx["claims"]
        school_id = claims.get("active_school_id")
        
        return {
            "success": True,
            "message": "Test SMS webhook received successfully",
            "payload": payload,
            "user_id": str(user.id),
            "user_email": user.email,
            "school_id": school_id,
            "signature_verified": True,
            "body_length": len(raw_body)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/sms/debug")
async def debug_webhook(request: Request):
    """
    Debug endpoint to see exactly what's being received.
    No authentication required - use only for debugging!
    """
    try:
        raw_body = await request.body()
        signature_header = request.headers.get("X-Webhook-Signature", "")
        auth_header = request.headers.get("Authorization", "")
        
        # Test signature computation
        if raw_body and signature_header:
            mac = hmac.new(WEBHOOK_SHARED_SECRET.encode(), raw_body, hashlib.sha256)
            expected = f"sha256={mac.hexdigest()}"
            
            return {
                "received_signature": signature_header,
                "expected_signature": expected,
                "signature_match": expected == signature_header,
                "body_length": len(raw_body),
                "has_auth": bool(auth_header)
            }
        else:
            return {
                "error": "Missing body or signature header",
                "body_length": len(raw_body),
                "has_signature": bool(signature_header),
                "has_auth": bool(auth_header)
            }
            
    except Exception as e:
        return {
            "error": str(e)
        }