# app/services/email_service.py

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', None)
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        self.from_email = getattr(settings, 'FROM_EMAIL', self.smtp_username)
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an email notification"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured - email notification skipped")
                return {"success": False, "error": "SMTP not configured"}
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add text part
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return {"success": False, "error": str(e)}


# app/services/sms_service.py

import requests
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class SMSService:
    """Service for sending SMS notifications via SMS gateway"""
    
    def __init__(self):
        # Configure your SMS provider settings
        self.sms_api_url = getattr(settings, 'SMS_API_URL', None)
        self.sms_api_key = getattr(settings, 'SMS_API_KEY', None)
        self.sms_sender_id = getattr(settings, 'SMS_SENDER_ID', 'SCHOOL')
    
    async def send_sms(
        self, 
        phone_number: str, 
        message: str, 
        school_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            if not self.sms_api_url or not self.sms_api_key:
                logger.warning("SMS API not configured - SMS notification skipped")
                return {"success": False, "error": "SMS API not configured"}
            
            # Format phone number (ensure it starts with country code)
            formatted_phone = self._format_phone_number(phone_number)
            
            if not formatted_phone:
                return {"success": False, "error": "Invalid phone number format"}
            
            # Prepare SMS API request (adjust based on your SMS provider)
            sms_data = {
                "to": formatted_phone,
                "message": message,
                "sender_id": self.sms_sender_id,
                "api_key": self.sms_api_key
            }
            
            # Example for Africa's Talking SMS API
            if "africastalking" in self.sms_api_url.lower():
                sms_data = {
                    "username": getattr(settings, 'AFRICASTALKING_USERNAME', 'sandbox'),
                    "to": formatted_phone,
                    "message": message,
                    "from": self.sms_sender_id
                }
                headers = {
                    "apiKey": self.sms_api_key,
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            else:
                # Generic SMS API format
                headers = {
                    "Authorization": f"Bearer {self.sms_api_key}",
                    "Content-Type": "application/json"
                }
            
            # Send SMS
            response = requests.post(
                self.sms_api_url,
                data=sms_data if "africastalking" in self.sms_api_url.lower() else None,
                json=sms_data if "africastalking" not in self.sms_api_url.lower() else None,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                
                # Check response format based on provider
                if "africastalking" in self.sms_api_url.lower():
                    if response_data.get("SMSMessageData", {}).get("Recipients"):
                        recipients = response_data["SMSMessageData"]["Recipients"]
                        if recipients and recipients[0].get("status") == "Success":
                            logger.info(f"SMS sent successfully to {formatted_phone}")
                            return {"success": True, "response": response_data}
                        else:
                            error_msg = recipients[0].get("statusCode", "Unknown error") if recipients else "No recipients"
                            return {"success": False, "error": f"SMS failed: {error_msg}"}
                    else:
                        return {"success": False, "error": "Invalid SMS API response"}
                else:
                    # Generic success check
                    logger.info(f"SMS sent successfully to {formatted_phone}")
                    return {"success": True, "response": response_data}
            else:
                error_msg = f"SMS API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except requests.RequestException as e:
            logger.error(f"SMS API request failed: {e}")
            return {"success": False, "error": f"SMS API request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_phone_number(self, phone: str) -> Optional[str]:
        """Format phone number to international format"""
        try:
            # Remove all non-digit characters
            digits_only = ''.join(filter(str.isdigit, phone))
            
            if not digits_only:
                return None
            
            # Handle Kenyan numbers
            if len(digits_only) == 10 and digits_only.startswith('07'):
                # Convert 07XXXXXXXX to +254XXXXXXXX
                return f"+254{digits_only[1:]}"
            elif len(digits_only) == 9 and digits_only.startswith('7'):
                # Convert 7XXXXXXXX to +254XXXXXXXX
                return f"+254{digits_only}"
            elif len(digits_only) == 12 and digits_only.startswith('254'):
                # Already in 254XXXXXXXX format
                return f"+{digits_only}"
            elif len(digits_only) == 13 and digits_only.startswith('+254'):
                # Already in +254XXXXXXXX format
                return digits_only
            else:
                # Return as-is with + if it looks international
                if len(digits_only) > 10:
                    return f"+{digits_only}"
                return None
                
        except Exception as e:
            logger.error(f"Phone number formatting error: {e}")
            return None

