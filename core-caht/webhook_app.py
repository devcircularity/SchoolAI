# webhook_app.py - Completely separate FastAPI app for webhooks

import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup (copy your database config here)
# You'll need to import your database URL from your main app config
DATABASE_URL = "postgresql://your_db_url_here"  # Replace with your actual database URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class SMSWebhookPayload(BaseModel):
    source: str
    message: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def parse_mpesa_sms(message: str) -> Optional[Dict[str, Any]]:
    """Parse M-Pesa SMS message to extract payment details"""
    try:
        logger.info(f"Parsing SMS: {message}")
        
        # Check if this looks like an M-Pesa message
        if not any(keyword in message.lower() for keyword in ['ksh', 'm-pesa', 'mpesa', 'ref', 'received']):
            logger.info("SMS doesn't appear to be M-Pesa payment")
            return None
        
        # Extract amount
        amount_match = re.search(r'ksh\s*([0-9,]+(?:\.[0-9]{2})?)', message, re.IGNORECASE)
        if not amount_match:
            logger.warning("Could not extract amount from SMS")
            return None
        
        amount_str = amount_match.group(1).replace(',', '')
        try:
            amount = float(amount_str)
        except ValueError:
            logger.error(f"Invalid amount format: {amount_str}")
            return None
        
        # Extract M-Pesa reference
        ref_patterns = [
            r'ref[:\s]+([A-Z0-9]+)',
            r'm-pesa\s+ref[:\s]+([A-Z0-9]+)',
            r'transaction[:\s]+([A-Z0-9]+)'
        ]
        
        transaction_id = None
        for pattern in ref_patterns:
            ref_match = re.search(pattern, message, re.IGNORECASE)
            if ref_match:
                transaction_id = ref_match.group(1)
                break
        
        if not transaction_id:
            transaction_id = f"SMS_{int(datetime.now().timestamp())}"
        
        # Extract account/student info
        account_patterns = [
            r'account[:\s]+([A-Z0-9]+)',
            r'to\s+([A-Z0-9\s]+)\s+account',
        ]
        
        account_number = None
        for pattern in account_patterns:
            account_match = re.search(pattern, message, re.IGNORECASE)
            if account_match:
                account_number = account_match.group(1).strip()
                break
        
        payment_data = {
            "amount": amount,
            "transaction_id": transaction_id,
            "account_number": account_number,
            "raw_message": message
        }
        
        logger.info(f"Parsed M-Pesa payment: {payment_data}")
        return payment_data
        
    except Exception as e:
        logger.error(f"Error parsing M-Pesa SMS: {e}")
        return None

def process_sms_payment_simple(db: Session, mpesa_payment: Dict):
    """Simple payment processing without full PaymentHandler complexity"""
    try:
        logger.info(f"Processing SMS payment: {mpesa_payment}")
        
        # Basic duplicate check
        existing = db.execute(
            text("""SELECT id FROM payments 
                     WHERE txn_ref = :ref 
                     LIMIT 1"""),
            {"ref": mpesa_payment["transaction_id"]}
        ).fetchall()
        
        if existing:
            logger.info(f"Payment {mpesa_payment['transaction_id']} already exists")
            return {"success": True, "message": "Payment already processed", "duplicate": True}
        
        # Find student if account number provided
        student = None
        if mpesa_payment.get("account_number"):
            students = db.execute(
                text("""SELECT id, first_name, last_name, admission_no 
                         FROM students 
                         WHERE admission_no = :admission_no 
                         AND status = 'ACTIVE' 
                         LIMIT 1"""),
                {"admission_no": mpesa_payment["account_number"]}
            ).fetchall()
            
            if students:
                s = students[0]
                student = {
                    "id": str(s[0]),
                    "name": f"{s[1]} {s[2]}",
                    "admission_no": s[3]
                }
        
        if not student:
            logger.warning(f"Student not found for account: {mpesa_payment.get('account_number')}")
            return {
                "success": False, 
                "error": f"Student not found for account: {mpesa_payment.get('account_number')}"
            }
        
        # Log the payment attempt for manual review
        logger.info(f"SMS Payment ready for processing: Student={student['name']}, Amount={mpesa_payment['amount']}")
        
        # Here you would call your actual PaymentHandler
        # For now, just return success
        return {
            "success": True,
            "message": f"SMS payment logged for {student['name']} - KES {mpesa_payment['amount']}",
            "student": student,
            "amount": mpesa_payment['amount'],
            "reference": mpesa_payment['transaction_id']
        }
        
    except Exception as e:
        logger.error(f"SMS payment processing error: {e}")
        return {"success": False, "error": str(e)}

# Create webhook app
webhook_app = FastAPI(title="SMS Webhook Service", version="1.0.0")

webhook_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@webhook_app.post("/sms")
async def handle_sms_webhook(
    sms_data: SMSWebhookPayload,
    background_tasks: BackgroundTasks
):
    """Handle SMS webhook - NO AUTHENTICATION"""
    try:
        logger.info(f"=== SMS WEBHOOK (STANDALONE) ===")
        logger.info(f"Source: {sms_data.source}")
        logger.info(f"Message: {sms_data.message}")
        
        # Parse M-Pesa SMS
        mpesa_payment = parse_mpesa_sms(sms_data.message)
        
        if not mpesa_payment:
            return {
                "success": True,
                "message": "SMS received but not recognized as M-Pesa payment",
                "status": "ignored"
            }
        
        # Process payment in background
        db = next(get_db())
        try:
            result = process_sms_payment_simple(db, mpesa_payment)
            
            return {
                "success": True,
                "message": "M-Pesa SMS processed",
                "payment_result": result,
                "parsed_data": mpesa_payment
            }
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"SMS webhook error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@webhook_app.get("/health")
async def webhook_health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "SMS Webhook (Standalone)",
        "timestamp": datetime.utcnow().isoformat()
    }

@webhook_app.get("/")
async def webhook_root():
    """Root endpoint"""
    return {"message": "SMS Webhook Service Running"}

if __name__ == "__main__":
    import uvicorn
    # Run on a different port to avoid conflicts
    uvicorn.run(webhook_app, host="0.0.0.0", port=8001)