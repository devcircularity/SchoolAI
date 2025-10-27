# handlers/payment/handler.py - Intent-first refactor
import os
from typing import Dict, Optional
from ...base import BaseHandler, ChatResponse
from .service import PaymentService

# Import WhatsApp service
from app.services.whatsapp_service import WhatsAppService

class PaymentHandler(BaseHandler):
    """Intent-first payment handler"""
    
    def __init__(self, db, school_id: str, user_id: str):
        super().__init__(db, school_id, user_id)
        self.service = PaymentService(
            db, school_id, self.get_school_name,
            self._get_whatsapp_service, self._send_email_notification
        )
    
    def handle_intent(self, intent: str, message: str, entities: Dict, context: Dict) -> ChatResponse:
        """
        Handle payment operations based on intent classification
        
        Args:
            intent: The classified intent (e.g., 'payment_record', 'payment_history')
            message: Original user message
            entities: Extracted entities (student_name, amount, etc.)
            context: Conversation context
        """
        # Route based on intent
        if intent == 'payment_record':
            return self.service.record_payment(message, context)
        
        elif intent == 'payment_summary':
            return self.service.show_payment_summary()
        
        elif intent == 'payment_history':
            return self.service.show_payment_history(message)
        
        elif intent == 'payment_pending':
            return self.service.show_pending_payments()
        
        elif intent == 'payment_status':
            # Use entities if available for specific student lookup
            if entities.get('student_name') or entities.get('admission_no'):
                return self.service.show_payment_history(message)
            else:
                return self.service.show_payment_summary()
        
        elif intent == 'mpesa_callback':
            # Handle M-Pesa callback processing
            callback_data = context.get('callback_data', {})
            return self.service.process_mpesa_callback(callback_data)
        
        else:
            # Default to overview for unknown intents
            return self.service.show_overview()
    
    def _get_whatsapp_service(self):
        """Get WhatsApp service with proper configuration"""
        try:
            bridge_url = os.getenv('WHATSAPP_BRIDGE_URL', 'http://localhost:3001')
            timeout = int(os.getenv('WHATSAPP_TIMEOUT', '30'))
            
            return WhatsAppService.for_school(
                school_id=self.school_id,
                bridge_url=bridge_url,
                timeout=timeout
            )
        except Exception as e:
            print(f"Error initializing WhatsApp service: {e}")
            return None
    
    def _send_email_notification(self, payment_data: Dict) -> bool:
        """Send email notification via Brevo"""
        try:
            guardian_email = payment_data.get("guardian_email")
            
            if not guardian_email or guardian_email.strip() == "":
                return False
            
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from datetime import datetime
            
            # Brevo SMTP settings
            smtp_server = "smtp-relay.brevo.com"
            smtp_port = 587
            smtp_user = "844a62001@smtp-brevo.com"
            smtp_password = "Brpd1SAyVsPMRJhW"
            from_email = "no.reply@olaji.co"
            
            subject = f"Payment Confirmation - {payment_data['student_name']}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #28a745; margin-bottom: 20px;">Payment Received</h2>
                    
                    <div style="background: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                        <h3 style="color: #333; margin-top: 0;">Payment Details</h3>
                        <p><strong>Student:</strong> {payment_data['student_name']} (#{payment_data['admission_no']})</p>
                        <p><strong>Amount Paid:</strong> KES {payment_data['amount_paid']:,.2f}</p>
                        <p><strong>Payment Method:</strong> {payment_data['method']}</p>
                        <p><strong>Reference:</strong> {payment_data['reference']}</p>
                        <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-radius: 5px;">
                        <h3 style="color: #333; margin-top: 0;">Account Summary</h3>
                        <p><strong>Remaining Balance:</strong> KES {payment_data['remaining_balance']:,.2f}</p>
                        {f'<p style="color: #28a745;"><strong>Account Status:</strong> Fully Paid</p>' if payment_data['remaining_balance'] == 0 else f'<p style="color: #ffc107;"><strong>Outstanding Amount:</strong> KES {payment_data["remaining_balance"]:,.2f}</p>'}
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background: #e3f2fd; border-radius: 5px;">
                        <p style="margin: 0; font-size: 14px; color: #666;">
                            Thank you for your payment. If you have any questions, please contact the school administration.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = guardian_email.strip()
            msg.attach(MIMEText(html_body, 'html'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Email notification error: {e}")
            return False
    
    # Legacy methods for backward compatibility (can be removed later)
    def process_mpesa_callback(self, callback_data: Dict) -> ChatResponse:
        """Process M-Pesa payment callback - legacy compatibility"""
        return self.handle_intent("mpesa_callback", "", {}, {"callback_data": callback_data})
    
    def send_payment_reminders(self, student_ids: Optional[list] = None) -> ChatResponse:
        """Send bulk payment reminders - legacy compatibility"""
        return ChatResponse(
            response="Payment reminders functionality moved to service layer",
            intent="feature_moved"
        )