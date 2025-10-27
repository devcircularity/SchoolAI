# app/api/routers/mobile.py - Mobile device status API endpoints

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

from app.api.deps.auth import get_current_user
from app.api.deps.tenancy import require_school
from app.core.db import get_db
from app.models.school import MobileDeviceStatus

router = APIRouter(prefix="/mobile", tags=["Mobile Device"])

# Pydantic models for request/response
class MobileDeviceStatusRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=128, description="Unique device identifier")
    app_version: Optional[str] = Field(None, max_length=32, description="App version (e.g., '0.4.0')")
    device_model: Optional[str] = Field(None, max_length=128, description="Device model")
    android_version: Optional[str] = Field(None, max_length=32, description="Android OS version")
    
    # Permission and connection status
    notification_access: bool = Field(default=False, description="Has notification listener permission")
    sms_permission: bool = Field(default=False, description="Has SMS read permission")
    listener_connected: bool = Field(default=False, description="Notification listener is running")
    
    # Last operation status
    last_forward_ok: bool = Field(default=True, description="Last SMS forward was successful")
    last_error: Optional[str] = Field(None, description="Last error message if any")
    
    # Optional network info
    network_status: Optional[str] = Field(None, max_length=32, description="Network type: wifi/mobile/offline")
    battery_optimized: Optional[bool] = Field(None, description="Is app battery optimized")

class MobileDeviceStatusResponse(BaseModel):
    device_id: str
    app_version: Optional[str]
    device_model: Optional[str]
    android_version: Optional[str]
    
    notification_access: bool
    sms_permission: bool
    listener_connected: bool
    last_forward_ok: bool
    last_error: Optional[str]
    
    network_status: Optional[str]
    battery_optimized: Optional[bool]
    last_sms_received_at: Optional[datetime]
    
    first_seen_at: datetime
    last_update_at: datetime
    last_heartbeat_at: datetime
    
    # Computed properties
    is_online: bool
    is_healthy: bool
    status_summary: str

class MobileDeviceListResponse(BaseModel):
    devices: List[MobileDeviceStatusResponse]
    total_count: int
    connected_count: int
    healthy_count: int

@router.post("/status", response_model=MobileDeviceStatusResponse)
async def update_device_status(
    request: MobileDeviceStatusRequest,
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update mobile device status - called by Android app to report current state.
    Creates new record if device doesn't exist, otherwise updates existing.
    """
    try:
        user = ctx["user"]
        current_time = datetime.utcnow()
        
        print(f"=== MOBILE STATUS UPDATE ===")
        print(f"School: {school_id}")
        print(f"User: {user.email} ({user.id})")
        print(f"Device: {request.device_id}")
        print(f"Status: notifications={request.notification_access}, sms={request.sms_permission}, listener={request.listener_connected}")
        
        # Check if device already exists
        existing_device = db.execute(
            select(MobileDeviceStatus).where(
                and_(
                    MobileDeviceStatus.school_id == school_id,
                    MobileDeviceStatus.user_id == user.id,
                    MobileDeviceStatus.device_id == request.device_id
                )
            )
        ).scalar_one_or_none()
        
        if existing_device:
            # Update existing device
            existing_device.app_version = request.app_version
            existing_device.device_model = request.device_model
            existing_device.android_version = request.android_version
            existing_device.notification_access = request.notification_access
            existing_device.sms_permission = request.sms_permission
            existing_device.listener_connected = request.listener_connected
            existing_device.last_forward_ok = request.last_forward_ok
            existing_device.last_error = request.last_error
            existing_device.network_status = request.network_status
            existing_device.battery_optimized = request.battery_optimized
            existing_device.last_update_at = current_time
            existing_device.last_heartbeat_at = current_time
            
            device = existing_device
            print("Updated existing device record")
        else:
            # Create new device record
            device = MobileDeviceStatus(
                school_id=uuid.UUID(school_id),
                user_id=user.id,
                device_id=request.device_id,
                app_version=request.app_version,
                device_model=request.device_model,
                android_version=request.android_version,
                notification_access=request.notification_access,
                sms_permission=request.sms_permission,
                listener_connected=request.listener_connected,
                last_forward_ok=request.last_forward_ok,
                last_error=request.last_error,
                network_status=request.network_status,
                battery_optimized=request.battery_optimized,
                first_seen_at=current_time,
                last_update_at=current_time,
                last_heartbeat_at=current_time
            )
            db.add(device)
            print("Created new device record")
        
        # Commit the changes
        db.commit()
        db.refresh(device)
        
        print(f"Device status updated successfully: {device.status_summary}")
        
        # Return response
        return MobileDeviceStatusResponse(
            device_id=device.device_id,
            app_version=device.app_version,
            device_model=device.device_model,
            android_version=device.android_version,
            notification_access=device.notification_access,
            sms_permission=device.sms_permission,
            listener_connected=device.listener_connected,
            last_forward_ok=device.last_forward_ok,
            last_error=device.last_error,
            network_status=device.network_status,
            battery_optimized=device.battery_optimized,
            last_sms_received_at=device.last_sms_received_at,
            first_seen_at=device.first_seen_at,
            last_update_at=device.last_update_at,
            last_heartbeat_at=device.last_heartbeat_at,
            is_online=device.is_online,
            is_healthy=device.is_healthy,
            status_summary=device.status_summary
        )
        
    except Exception as e:
        print(f"Error updating device status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update device status: {str(e)}")

@router.get("/status", response_model=MobileDeviceListResponse)
async def get_device_statuses(
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all mobile device statuses for the current school and user.
    Frontend uses this to show connection status.
    """
    try:
        user = ctx["user"]
        
        # Get all devices for this user in this school
        devices = db.execute(
            select(MobileDeviceStatus).where(
                and_(
                    MobileDeviceStatus.school_id == school_id,
                    MobileDeviceStatus.user_id == user.id
                )
            ).order_by(MobileDeviceStatus.last_heartbeat_at.desc())
        ).scalars().all()
        
        # Convert to response objects
        device_responses = []
        connected_count = 0
        healthy_count = 0
        
        for device in devices:
            device_response = MobileDeviceStatusResponse(
                device_id=device.device_id,
                app_version=device.app_version,
                device_model=device.device_model,
                android_version=device.android_version,
                notification_access=device.notification_access,
                sms_permission=device.sms_permission,
                listener_connected=device.listener_connected,
                last_forward_ok=device.last_forward_ok,
                last_error=device.last_error,
                network_status=device.network_status,
                battery_optimized=device.battery_optimized,
                last_sms_received_at=device.last_sms_received_at,
                first_seen_at=device.first_seen_at,
                last_update_at=device.last_update_at,
                last_heartbeat_at=device.last_heartbeat_at,
                is_online=device.is_online,
                is_healthy=device.is_healthy,
                status_summary=device.status_summary
            )
            device_responses.append(device_response)
            
            if device.is_online:
                connected_count += 1
            if device.is_healthy:
                healthy_count += 1
        
        print(f"Retrieved {len(devices)} devices for user {user.email}: {connected_count} connected, {healthy_count} healthy")
        
        return MobileDeviceListResponse(
            devices=device_responses,
            total_count=len(devices),
            connected_count=connected_count,
            healthy_count=healthy_count
        )
        
    except Exception as e:
        print(f"Error getting device statuses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get device statuses: {str(e)}")

@router.delete("/status/{device_id}")
async def remove_device(
    device_id: str,
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a mobile device record.
    Useful for cleaning up old/unused devices.
    """
    try:
        user = ctx["user"]
        
        # Find the device
        device = db.execute(
            select(MobileDeviceStatus).where(
                and_(
                    MobileDeviceStatus.school_id == school_id,
                    MobileDeviceStatus.user_id == user.id,
                    MobileDeviceStatus.device_id == device_id
                )
            )
        ).scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Delete the device
        db.delete(device)
        db.commit()
        
        print(f"Removed device {device_id} for user {user.email}")
        
        return {"success": True, "message": f"Device {device_id} removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error removing device: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove device: {str(e)}")

@router.post("/heartbeat/{device_id}")
async def device_heartbeat(
    device_id: str,
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simple heartbeat endpoint for Android app to indicate it's still running.
    Updates last_heartbeat_at without changing other fields.
    """
    try:
        user = ctx["user"]
        current_time = datetime.utcnow()
        
        # Find the device
        device = db.execute(
            select(MobileDeviceStatus).where(
                and_(
                    MobileDeviceStatus.school_id == school_id,
                    MobileDeviceStatus.user_id == user.id,
                    MobileDeviceStatus.device_id == device_id
                )
            )
        ).scalar_one_or_none()
        
        if not device:
            # Create a basic device record if it doesn't exist
            device = MobileDeviceStatus(
                school_id=uuid.UUID(school_id),
                user_id=user.id,
                device_id=device_id,
                notification_access=False,
                sms_permission=False,
                listener_connected=False,
                last_forward_ok=True,
                first_seen_at=current_time,
                last_update_at=current_time,
                last_heartbeat_at=current_time
            )
            db.add(device)
            print(f"Created basic device record for heartbeat: {device_id}")
        else:
            # Just update heartbeat
            device.last_heartbeat_at = current_time
        
        db.commit()
        
        return {
            "success": True,
            "device_id": device_id,
            "heartbeat_at": current_time.isoformat(),
            "is_online": True
        }
        
    except Exception as e:
        print(f"Error updating heartbeat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update heartbeat: {str(e)}")

@router.post("/sms-received/{device_id}")
async def record_sms_received(
    device_id: str,
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record that an SMS was received and processed by this device.
    Called by Android app after successfully forwarding an SMS.
    """
    try:
        user = ctx["user"]
        current_time = datetime.utcnow()
        
        # Find the device
        device = db.execute(
            select(MobileDeviceStatus).where(
                and_(
                    MobileDeviceStatus.school_id == school_id,
                    MobileDeviceStatus.user_id == user.id,
                    MobileDeviceStatus.device_id == device_id
                )
            )
        ).scalar_one_or_none()
        
        if device:
            device.last_sms_received_at = current_time
            device.last_forward_ok = True
            device.last_error = None
            device.last_heartbeat_at = current_time
            db.commit()
            
            print(f"Recorded SMS received for device {device_id}")
            
            return {
                "success": True,
                "device_id": device_id,
                "last_sms_received_at": current_time.isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Device not found")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error recording SMS received: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record SMS: {str(e)}")

@router.get("/debug/all-devices")
async def get_all_school_devices(
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Debug endpoint to see all devices for the school (admin only).
    Useful for troubleshooting and monitoring.
    """
    try:
        user = ctx["user"]
        claims = ctx["claims"]
        
        # Check if user is admin/owner (optional - remove if not needed)
        # school_role = claims.get("school_role", "")
        # if school_role not in ["OWNER", "ADMIN"]:
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get all devices for this school
        devices = db.execute(
            select(MobileDeviceStatus).where(
                MobileDeviceStatus.school_id == school_id
            ).order_by(MobileDeviceStatus.last_heartbeat_at.desc())
        ).scalars().all()
        
        device_info = []
        for device in devices:
            device_info.append({
                "device_id": device.device_id,
                "user_id": str(device.user_id),
                "app_version": device.app_version,
                "device_model": device.device_model,
                "status_summary": device.status_summary,
                "is_online": device.is_online,
                "is_healthy": device.is_healthy,
                "last_heartbeat_at": device.last_heartbeat_at.isoformat() if device.last_heartbeat_at else None,
                "last_sms_received_at": device.last_sms_received_at.isoformat() if device.last_sms_received_at else None,
                "last_error": device.last_error
            })
        
        return {
            "school_id": school_id,
            "total_devices": len(devices),
            "devices": device_info,
            "summary": {
                "online": sum(1 for d in devices if d.is_online),
                "healthy": sum(1 for d in devices if d.is_healthy),
                "with_errors": sum(1 for d in devices if d.last_error),
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting all devices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get devices: {str(e)}")