# app/services/sms_processor.py - Enhanced for M-Pesa payment extraction

from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone, date
from typing import Dict, Any, Optional
import logging
import re
import uuid

from app.models.user import User
from app.models.school import School
from app.models.student import Student
from app.models.guardian import Guardian
from app.models.payment import Payment, Invoice
from app.api.routers.chat.handlers.payment import PaymentHandler

logger = logging.getLogger(__name__)

class SMSProcessor:
    """Service for processing SMS messages from webhooks, especially M-Pesa payments."""
    
    def __init__(self, db: Session, user_id: uuid.UUID, school_id: str):
        self.db = db
        self.user_id = user_id
        self.school_id = school_id
    
    async def process_sms_message(
        self, 
        source: str, 
        message: str, 
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an SMS message and extract relevant information.
        Handle M-Pesa payments automatically.
        """
        try:
            # Get user and school info
            user = self.db.execute(
                select(User).where(User.id == self.user_id)
            ).scalar_one_or_none()
            
            if not user:
                raise ValueError(f"User {self.user_id} not found")
            
            school = self.db.execute(
                select(School).where(School.id == self.school_id)
            ).scalar_one_or_none()
            
            if not school:
                raise ValueError(f"School {self.school_id} not found")
            
            # Print the received message
            print(f"SMS received: {message}")
            
            # Extract information from the SMS
            sms_info = self._extract_sms_info(message)
            
            # Handle M-Pesa payment if detected
            payment_result = None
            if sms_info.get("message_type") == "mpesa_payment" and sms_info.get("student_id") and sms_info.get("amount"):
                payment_result = await self._process_mpesa_payment(sms_info)
            
            # Store the SMS record
            sms_record = {
                "id": str(uuid.uuid4()),
                "user_id": str(self.user_id),
                "school_id": self.school_id,
                "source": source,
                "content": message,
                "extracted_info": sms_info,
                "payment_result": payment_result,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "timestamp": timestamp
            }
            
            logger.info(f"Processed SMS for user {user.email} at school {school.name}")
            if payment_result and payment_result.get("success"):
                logger.info(f"Successfully processed M-Pesa payment: {payment_result}")
            
            return {
                "sms_record": sms_record,
                "extracted_info": sms_info,
                "payment_result": payment_result,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.full_name
                },
                "school": {
                    "id": str(school.id),
                    "name": school.name
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing SMS: {e}")
            raise
    
    def _extract_sms_info(self, message: str) -> Dict[str, Any]:
        """
        Extract structured information from SMS message.
        Enhanced to handle both M-Pesa payment formats with student ID extraction.
        """
        info = {
            "message_type": "unknown",
            "amount": None,
            "currency": None,
            "reference": None,
            "student_id": None,
            "account_number": None,
            "timestamp": None,
            "sender": None,
            "keywords": []
        }
        
        # Convert to lowercase for pattern matching
        msg_lower = message.lower()
        
        # Try NEW FORMAT first: "THQ42AWKZU completed. You have received KES 1 from ERIC MWIRICHIA 254722517627 for account CIRCULARITY SPACE 8014934#1738"
        new_format_pattern = r'([A-Z0-9]+)\s+completed.*?you\s+have\s+received\s+kes\s*([\d,]+(?:\.\d{2})?)\s+from.*?for\s+account.*?#(\d+)'
        new_format_match = re.search(new_format_pattern, message, re.IGNORECASE)
        
        if new_format_match:
            info["message_type"] = "mpesa_payment"
            info["sender"] = "M-PESA"
            info["currency"] = "KES"
            
            # Extract reference (transaction ID at the beginning)
            info["reference"] = new_format_match.group(1)
            
            # Extract amount
            amount_str = new_format_match.group(2).replace(',', '')
            try:
                info["amount"] = float(amount_str)
            except ValueError:
                logger.warning(f"Could not parse amount: {amount_str}")
            
            # Extract student ID (number after #)
            info["student_id"] = new_format_match.group(3)
            
            # Extract payer name and phone
            payer_match = re.search(r'from\s+([A-Z\s]+)\s+(\d{12})', message, re.IGNORECASE)
            if payer_match:
                info["payer_name"] = payer_match.group(1).strip()
                info["payer_phone"] = payer_match.group(2)
            
            # Extract account identifier before #
            account_match = re.search(r'account\s+([^#]+)#', message, re.IGNORECASE)
            if account_match:
                info["account_number"] = account_match.group(1).strip()
            
            # Extract timestamp
            time_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+at\s+(\d{1,2}:\d{2}\s*[AP]M)', message, re.IGNORECASE)
            if time_match:
                info["date"] = time_match.group(1)
                info["time"] = time_match.group(2)
            
            logger.info(f"Extracted M-Pesa payment (NEW FORMAT): Amount={info['amount']}, Student ID={info['student_id']}, Ref={info['reference']}, Payer={info.get('payer_name')}")
        
        # Try OLD FORMAT: "Ksh X.XX sent to KCB account CIRCULARITY SPACE XXXXX#STUDENT_ID"
        if not info["student_id"]:  # Only try if new format didn't match
            mpesa_payment_pattern = r'ksh\s*([\d,]+\.?\d*)\s+sent\s+to.*?#(\d+)'
            mpesa_match = re.search(mpesa_payment_pattern, message, re.IGNORECASE)
            
            if mpesa_match:
                info["message_type"] = "mpesa_payment"
                info["sender"] = "M-PESA"
                info["currency"] = "KES"
                
                # Extract amount
                amount_str = mpesa_match.group(1).replace(',', '')
                try:
                    info["amount"] = float(amount_str)
                except ValueError:
                    logger.warning(f"Could not parse amount: {amount_str}")
                
                # Extract student ID (number after #)
                info["student_id"] = mpesa_match.group(2)
                
                # Extract M-Pesa reference (e.g., "THN4KIK5Y2")
                ref_match = re.search(r'ref\s+([A-Z0-9]{8,})', message, re.IGNORECASE)
                if ref_match:
                    info["reference"] = ref_match.group(1)
                
                # Extract account number/identifier before #
                account_match = re.search(r'account\s+([^#]+)#', message, re.IGNORECASE)
                if account_match:
                    info["account_number"] = account_match.group(1).strip()
                
                # Extract timestamp
                time_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+at\s+(\d{1,2}:\d{2}\s*[AP]M)', message, re.IGNORECASE)
                if time_match:
                    info["date"] = time_match.group(1)
                    info["time"] = time_match.group(2)
                
                logger.info(f"Extracted M-Pesa payment (OLD FORMAT): Amount={info['amount']}, Student ID={info['student_id']}, Ref={info['reference']}")
        
        # Fallback: Detect general M-PESA transactions (if no specific payment pattern matched)
        if not info["student_id"] and ("m-pesa" in msg_lower or "mpesa" in msg_lower or "kes" in msg_lower):
            info["message_type"] = "mpesa_transaction"
            info["sender"] = "M-PESA"
            
            # Extract amount (e.g., "Ksh 20.00" or "KES 1")
            amount_match = re.search(r'k(?:sh|es)\s*([\d,]+\.?\d*)', msg_lower)
            if amount_match:
                amount_str = amount_match.group(1).replace(',', '')
                try:
                    info["amount"] = float(amount_str)
                    info["currency"] = "KES"
                except ValueError:
                    pass
            
            # Extract M-PESA reference (at start or with ref keyword)
            ref_patterns = [
                r'^([A-Z0-9]{8,})\s+completed',  # New format: starts with ref
                r'ref\s+([A-Z0-9]{8,})'          # Old format: "ref XXXXX"
            ]
            
            for pattern in ref_patterns:
                ref_match = re.search(pattern, message, re.IGNORECASE)
                if ref_match:
                    info["reference"] = ref_match.group(1)
                    break
        
        # Detect bank SMS (if not already identified as M-Pesa)
        elif not info["message_type"] == "mpesa_payment" and any(bank in msg_lower for bank in ["kcb", "equity", "co-op", "bank"]):
            info["message_type"] = "bank_notification"
            
            # Extract amount for bank transactions
            amount_match = re.search(r'k(?:sh|es)\s*([\d,]+\.?\d*)', msg_lower)
            if amount_match:
                amount_str = amount_match.group(1).replace(',', '')
                try:
                    info["amount"] = float(amount_str)
                    info["currency"] = "KES"
                except ValueError:
                    pass
        
        # Extract keywords
        keywords = []
        keyword_patterns = [
            "sent", "received", "paid", "transaction", "balance", 
            "deposit", "withdrawal", "transfer", "charge", "fee", "completed"
        ]
        
        for keyword in keyword_patterns:
            if keyword in msg_lower:
                keywords.append(keyword)
        
        info["keywords"] = keywords
        
        return info
    
    async def _process_mpesa_payment(self, sms_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an M-Pesa payment by creating a payment record and updating invoices.
        """
        try:
            student_id = sms_info["student_id"]
            amount = sms_info["amount"]
            reference = sms_info.get("reference", f"SMS_{int(datetime.now().timestamp())}")
            
            # Find student by admission number
            student = self.db.execute(
                select(Student).where(
                    Student.school_id == self.school_id,
                    Student.admission_no == student_id,
                    Student.status == "ACTIVE"
                )
            ).scalar_one_or_none()
            
            if not student:
                return {
                    "success": False,
                    "error": f"Student not found with admission number: {student_id}",
                    "student_id": student_id
                }
            
            # Use PaymentHandler to process the payment
            payment_handler = PaymentHandler(self.db, self.school_id, str(self.user_id))
            
            # Create payment context for SMS - this matches the expected format
            payment_context = {
                "mpesa_payment": {
                    "amount": amount,
                    "transaction_id": reference,
                    "account_number": student_id,
                    "phone_number": sms_info.get("payer_phone"),  # Available in new format
                    "payer_name": sms_info.get("payer_name")      # Available in new format
                }
            }
            
            # Process the payment using the correct handle() method
            # Format the message to match what the handler expects
            payment_message = f"Record M-Pesa payment of {amount} for student {student_id}"
            
            payment_result = payment_handler.handle(
                message=payment_message,
                context=payment_context
            )
            
            # Check if the payment was successful
            if payment_result.intent == "payment_recorded":
                logger.info(f"Successfully processed M-Pesa payment for student {student_id}: KES {amount}")
                
                # Extract payment data from the ChatResponse
                payment_data = payment_result.data if hasattr(payment_result, 'data') else {}
                
                # Notifications are already handled by PaymentHandler
                notification_result = {
                    "email_sent": True,  # Handled by PaymentHandler
                    "whatsapp_sent": True,  # Handled by PaymentHandler
                    "sms_sent": False  # Not implemented
                }
                
                return {
                    "success": True,
                    "student_id": student_id,
                    "student_name": f"{student.first_name} {student.last_name}",
                    "amount": amount,
                    "reference": reference,
                    "payment_data": payment_data,
                    "message": payment_result.response,
                    "notifications": notification_result
                }
            else:
                # Payment failed
                error_message = payment_result.response if hasattr(payment_result, 'response') else "Unknown payment processing error"
                logger.warning(f"Payment processing failed for student {student_id}: {error_message}")
                return {
                    "success": False,
                    "student_id": student_id,
                    "amount": amount,
                    "reference": reference,
                    "error": error_message
                }
                
        except Exception as e:
            logger.error(f"Error processing M-Pesa payment: {e}")
            return {
                "success": False,
                "error": f"Payment processing error: {str(e)}",
                "student_id": sms_info.get("student_id"),
                "amount": sms_info.get("amount")
            }
    
    # Note: Notification methods below are for reference but not used since
    # PaymentHandler already handles notifications successfully
    
    async def _send_payment_notifications(self, student, amount: float, reference: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        DEPRECATED: This method is not used anymore since PaymentHandler already handles notifications.
        Keeping for reference only.
        """
        return {
            "email_sent": False,
            "sms_sent": False,
            "whatsapp_sent": False,
            "note": "Notifications handled by PaymentHandler"
        }
    
    def _get_guardian_contact(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get guardian contact information for notifications."""
        try:
            # First get the student
            student = self.db.execute(
                select(Student).where(Student.id == student_id)
            ).scalar_one_or_none()
            
            if not student or not student.primary_guardian_id:
                return None
            
            # Then get the guardian separately
            guardian = self.db.execute(
                select(Guardian).where(Guardian.id == student.primary_guardian_id)
            ).scalar_one_or_none()
            
            if guardian:
                return {
                    "phone": guardian.phone,
                    "email": guardian.email,
                    "name": f"{guardian.first_name} {guardian.last_name}" if guardian.first_name and guardian.last_name else "Parent/Guardian"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting guardian contact: {e}")
            return None
    
    async def _send_email_notification(self, email: str, notification_data: Dict[str, Any], payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email notification about payment."""
        try:
            from app.services.email_service import EmailService
            
            # Create email content
            subject = f"Payment Received - {notification_data['student_name']}"
            
            # HTML email template
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #28a745; text-align: center;">Payment Received</h2>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3>Payment Details</h3>
                        <p><strong>Student:</strong> {notification_data['student_name']}</p>
                        <p><strong>Admission Number:</strong> {notification_data['admission_no']}</p>
                        <p><strong>Amount Paid:</strong> KES {notification_data['amount']:,.2f}</p>
                        <p><strong>Payment Method:</strong> M-PESA</p>
                        <p><strong>Reference:</strong> {notification_data['reference']}</p>
                        <p><strong>Date & Time:</strong> {notification_data['payment_date']}</p>
                    </div>
                    
                    <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4>Payment Applied To:</h4>
                        {"<p>Payment has been automatically applied to outstanding invoices.</p>"}
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                        <p style="color: #6c757d; font-size: 12px;">
                            This is an automated notification from your school's payment system.<br>
                            Payment was processed automatically via M-PESA SMS integration.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
Payment Received

Student: {notification_data['student_name']}
Admission Number: {notification_data['admission_no']}
Amount Paid: KES {notification_data['amount']:,.2f}
Payment Method: M-PESA
Reference: {notification_data['reference']}
Date & Time: {notification_data['payment_date']}

Payment has been automatically applied to outstanding invoices.

This is an automated notification from your school's payment system.
            """
            
            email_service = EmailService()
            result = await email_service.send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            return {"success": result.get("success", False), "error": result.get("error")}
            
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_sms_notification(self, phone: str, notification_data: Dict[str, Any], payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS notification about payment."""
        try:
            from app.services.sms_service import SMSService
            
            # Create SMS content (keep it concise for SMS)
            sms_message = f"Payment Received!\n\n"
            sms_message += f"Student: {notification_data['student_name']}\n"
            sms_message += f"Amount: KES {notification_data['amount']:,.2f}\n"
            sms_message += f"Method: M-PESA\n"
            sms_message += f"Ref: {notification_data['reference']}\n"
            sms_message += f"Date: {notification_data['payment_date']}\n\n"
            sms_message += f"Payment applied to outstanding invoices automatically.\n\n"
            sms_message += f"Thank you for your payment!"
            
            sms_service = SMSService()
            result = await sms_service.send_sms(
                phone_number=phone,
                message=sms_message,
                school_id=self.school_id
            )
            
            return {"success": result.get("success", False), "error": result.get("error")}
            
        except Exception as e:
            logger.error(f"SMS sending error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_whatsapp_notification(self, phone: str, notification_data: Dict[str, Any], payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send WhatsApp notification about payment."""
        try:
            from app.services.whatsapp_service import WhatsAppService
            
            # Prepare payment data for WhatsApp service
            whatsapp_payment_data = {
                "student_name": notification_data["student_name"],
                "admission_no": notification_data["admission_no"],
                "amount": notification_data["amount"],
                "reference": notification_data["reference"],
                "method": "M-PESA",
                "payment_type": "sms_payment",
                "allocations": payment_data.get("allocations", []) if payment_data else []
            }
            
            # Use simple instantiation instead of for_school()
            whatsapp_service = WhatsAppService(school_id=self.school_id)
            result = whatsapp_service.send_payment_notification(
                school_id=self.school_id,
                guardian_phone=phone,
                payment_data=whatsapp_payment_data
            )
            
            return {"success": result.get("success", False), "error": result.get("error")}
            
        except Exception as e:
            logger.error(f"WhatsApp sending error: {e}")
            return {"success": False, "error": str(e)}