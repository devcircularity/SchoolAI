# app/services/whatsapp_service.py - Fixed QR code handling
import requests
import re
import os
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

class WhatsAppService:
    """WhatsApp notification service with multi-instance support and QR code management"""
    
    def __init__(self, bridge_url: str = None, timeout: int = 30, api_key: str = None, connection_token: str = None, db_session: Session = None):
        self.bridge_url = (bridge_url or os.getenv('WHATSAPP_BRIDGE_URL', 'http://localhost:3001')).rstrip('/')
        self.timeout = timeout
        self.api_key = api_key or os.getenv('WA_BRIDGE_API_KEY', 'dev-secret')
        self.connection_token = connection_token
        self.db_session = db_session
        
        print(f"WhatsApp service initialized:")
        print(f"  Bridge URL: {self.bridge_url}")
        print(f"  Connection Token: {self.connection_token}")
        print(f"  API Key: {self.api_key[:10]}..." if self.api_key else "  API Key: None")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with API key authentication and connection token"""
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key
        }
        
        if self.connection_token:
            headers['x-instance-token'] = self.connection_token
            print(f"Added connection token to headers: {self.connection_token}")
        
        return headers
    
    def _extract_school_id(self) -> Optional[str]:
        """Extract school ID from connection token"""
        if not self.connection_token:
            return None
        
        if self.connection_token.startswith('school_'):
            school_id_str = self.connection_token.replace('school_', '')
            
            # Validate it's a proper UUID
            try:
                uuid.UUID(school_id_str)
                return school_id_str
            except ValueError:
                print(f"Invalid UUID in connection token: {school_id_str}")
                return None
        
        return None
    
    @classmethod
    def for_school(cls, school_id: str, db_session: Session = None, **kwargs) -> 'WhatsAppService':
        """Create WhatsApp service instance for a specific school"""
        connection_token = f"school_{school_id}"
        return cls(connection_token=connection_token, db_session=db_session, **kwargs)
    
    def _store_qr_code(self, qr_code: str) -> None:
        """Store QR code in database for retrieval"""
        if not self.db_session or not qr_code:
            print("Cannot store QR code - no database session or QR code")
            return
        
        school_id = self._extract_school_id()
        if not school_id:
            print("Cannot store QR code - invalid school ID")
            return
        
        try:
            print(f"Storing QR code for school {school_id} (length: {len(qr_code)})")
            
            # Use proper UUID casting
            self.db_session.execute(
                text("""
                    INSERT INTO school_whatsapp_settings 
                    (school_id, qr_code, qr_generated_at, created_at, updated_at, is_enabled, bridge_connected)
                    VALUES (:school_id::uuid, :qr_code, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, true, false)
                    ON CONFLICT (school_id) 
                    DO UPDATE SET 
                        qr_code = :qr_code,
                        qr_generated_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                """),
                {"school_id": school_id, "qr_code": qr_code}
            )
            self.db_session.commit()
            print(f"QR code stored successfully for school {school_id}")
        except Exception as e:
            print(f"Failed to store QR code: {e}")
            self.db_session.rollback()
    
    def _get_stored_qr_code(self) -> Optional[str]:
        """Get stored QR code from database"""
        if not self.db_session:
            print("No database session available")
            return None
        
        school_id = self._extract_school_id()
        if not school_id:
            print("Cannot retrieve QR code - invalid school ID")
            return None
        
        try:
            result = self.db_session.execute(
                text("""
                    SELECT qr_code, qr_generated_at 
                    FROM school_whatsapp_settings 
                    WHERE school_id = :school_id::uuid
                    AND qr_code IS NOT NULL
                    AND qr_generated_at > CURRENT_TIMESTAMP - INTERVAL '10 minutes'
                """),
                {"school_id": school_id}
            ).fetchone()
            
            if result and result[0]:
                print(f"Retrieved stored QR code for school {school_id}")
                return result[0]
            
            print(f"No valid stored QR code found for school {school_id}")
            return None
        except Exception as e:
            print(f"Failed to retrieve stored QR code: {e}")
            return None
    
    def _clear_qr_code(self) -> None:
        """Clear stored QR code when connection is established"""
        if not self.db_session:
            return
        
        school_id = self._extract_school_id()
        if not school_id:
            return
        
        try:
            self.db_session.execute(
                text("""
                    UPDATE school_whatsapp_settings 
                    SET qr_code = NULL,
                        qr_generated_at = NULL,
                        updated_at = CURRENT_TIMESTAMP,
                        bridge_connected = true
                    WHERE school_id = :school_id::uuid
                """),
                {"school_id": school_id}
            )
            self.db_session.commit()
            print(f"QR code cleared for school {school_id}")
        except Exception as e:
            print(f"Failed to clear QR code: {e}")
            self.db_session.rollback()

    def get_qr_code(self) -> Dict[str, Any]:
        """Get QR code for WhatsApp authentication - always fetch fresh from bridge"""
        try:
            if not self.connection_token:
                return {
                    'qr': None,
                    'status': 'error',
                    'message': 'No connection token provided'
                }
            
            print(f"=== QR CODE REQUEST ===")
            print(f"Bridge URL: {self.bridge_url}")
            print(f"Connection Token: {self.connection_token}")
            print(f"Headers: {self._get_headers()}")
            
            # Always get fresh QR code from bridge (QR codes change frequently)
            print("Fetching QR code from bridge...")
            response = requests.get(
                f"{self.bridge_url}/qr",
                headers=self._get_headers(),
                timeout=15
            )
            
            print(f"QR Response Status: {response.status_code}")
            print(f"QR Response Text: {response.text[:200]}...")
            
            if response.status_code == 200:
                result = response.json()
                print(f"QR Response Keys: {list(result.keys())}")
                print(f"QR Status: {result.get('status', 'unknown')}")
                print(f"QR Message: {result.get('message', 'no message')}")
                
                # Check if we actually got a QR code
                if result.get("qr"):
                    qr_code = result["qr"]
                    print(f"QR Code received (length: {len(qr_code)})")
                    print(f"QR Code starts with: {qr_code[:50]}...")
                    
                    # Store QR code in database for tracking
                    self._store_qr_code(qr_code)
                    
                    return {
                        'qr': qr_code,
                        'status': result.get('status', 'qr_ready'),
                        'message': result.get('message', 'QR code ready for scanning'),
                        'source': 'bridge'
                    }
                else:
                    print(f"No QR code in response")
                    return {
                        'qr': None,
                        'status': result.get('status', 'no_qr'),
                        'message': result.get('message', 'No QR code available'),
                        'raw_response': result
                    }
                
            elif response.status_code == 404:
                print("Instance not found (404)")
                return {
                    'qr': None,
                    'status': 'not_initialized',
                    'message': 'Instance not found. Initialize connection first.'
                }
            elif response.status_code == 401:
                print("Authentication failed (401)")
                return {
                    'qr': None,
                    'status': 'auth_failed',
                    'message': 'Authentication failed - check API key'
                }
            else:
                error_text = response.text
                print(f"QR request failed: {response.status_code} - {error_text}")
                return {
                    'qr': None,
                    'status': 'error',
                    'message': f'Failed to get QR code: {response.status_code}',
                    'error_details': error_text
                }
                
        except requests.Timeout:
            print("QR request timeout")
            return {
                'qr': None,
                'status': 'timeout',
                'message': 'Request timeout while getting QR code'
            }
        except Exception as e:
            print(f"QR code fetch error: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {
                'qr': None,
                'status': 'error',
                'message': f'Error getting QR code: {str(e)}'
            }

    def check_bridge_health(self) -> Dict[str, Any]:
        """Check WhatsApp bridge health for this instance with detailed logging"""
        try:
            print(f"=== BRIDGE HEALTH CHECK ===")
            print(f"Bridge URL: {self.bridge_url}")
            print(f"Connection Token: {self.connection_token}")
            
            # First check overall bridge health
            try:
                health_response = requests.get(
                    f"{self.bridge_url}/health", 
                    headers={'x-api-key': self.api_key},
                    timeout=10
                )
                
                print(f"Bridge health status: {health_response.status_code}")
                
                if health_response.status_code != 200:
                    return {'ready': False, 'error': f'Bridge health check failed: {health_response.status_code}'}
                
                bridge_health = health_response.json()
                print(f"Bridge health response: {bridge_health}")
                
            except Exception as bridge_error:
                print(f"Bridge unreachable: {bridge_error}")
                return {'ready': False, 'error': f'Bridge unreachable: {str(bridge_error)}'}
            
            # Check instance-specific status if we have a token
            if self.connection_token:
                try:
                    status_response = requests.get(
                        f"{self.bridge_url}/status", 
                        headers=self._get_headers(),
                        timeout=10
                    )
                    
                    print(f"Instance status code: {status_response.status_code}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"Instance status response: {status_data}")
                        
                        # If instance is ready, clear any stored QR codes
                        if status_data.get('ready', False):
                            self._clear_qr_code()
                        
                        return status_data
                    else:
                        error_text = status_response.text
                        print(f"Status endpoint error: {status_response.status_code} - {error_text}")
                        return {
                            'ready': False, 
                            'status': 'not_initialized', 
                            'bridge_health': bridge_health,
                            'error': f'Status check failed: {status_response.status_code}'
                        }
                        
                except Exception as status_error:
                    print(f"Could not get instance status: {status_error}")
                    return {
                        'ready': False, 
                        'error': str(status_error), 
                        'bridge_health': bridge_health
                    }
            else:
                print("No connection token provided")
                return bridge_health
            
        except Exception as e:
            print(f"Bridge health check failed: {e}")
            return {'ready': False, 'error': str(e)}

    def initialize_connection(self) -> Dict[str, Any]:
        """Initialize WhatsApp connection for this instance"""
        try:
            print(f"Initializing WhatsApp connection for token: {self.connection_token}")
            
            if not self.connection_token:
                return {'success': False, 'error': 'No connection token provided'}
            
            response = requests.post(
                f"{self.bridge_url}/init",
                headers=self._get_headers(),
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Connection initialization result: {result}")
                return result
            else:
                error_msg = f"Failed to initialize connection: {response.status_code} - {response.text}"
                print(error_msg)
                return {'success': False, 'error': error_msg}
                
        except requests.Timeout:
            return {'success': False, 'error': 'Connection timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def clean_phone_number(self, phone: str) -> str:
        """Clean and format phone number for WhatsApp"""
        if not phone:
            return ""
        
        # Remove all non-digit characters
        cleaned = re.sub(r'\D', '', str(phone))
        print(f"After removing non-digits: '{cleaned}'")
        
        if not cleaned:
            return ""
        
        # Handle Kenyan numbers
        if cleaned.startswith('0') and len(cleaned) == 10:
            # Convert 0714179051 to 254714179051
            cleaned = '254' + cleaned[1:]
            print(f"Converted Kenyan 0-format to international: '{cleaned}'")
        elif cleaned.startswith('254'):
            print(f"Already in correct 254 format: '{cleaned}'")
        elif len(cleaned) == 9:
            # Assume Kenyan number without leading 0 (714179051)
            cleaned = '254' + cleaned
            print(f"Added Kenyan country code: '{cleaned}'")
        
        print(f"Final cleaned phone number: '{cleaned}'")
        return cleaned

    def verify_whatsapp_registration(self, phone: str) -> bool:
        """Verify WhatsApp registration using the correct endpoint"""
        try:
            cleaned_phone = self.clean_phone_number(phone)
            if not cleaned_phone:
                print("Invalid phone number format")
                return False
            
            print(f"Verifying WhatsApp registration for: '{cleaned_phone}' with token: {self.connection_token}")
            
            response = requests.get(
                f"{self.bridge_url}/number-id/{cleaned_phone}",
                headers=self._get_headers(),
                timeout=10
            )
            
            print(f"WhatsApp verification response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                is_registered = data.get('registered', False)
                print(f"WhatsApp registration check result: {is_registered}")
                return is_registered
            elif response.status_code == 503:
                print("WhatsApp bridge not ready - assuming registered")
                return True
            elif response.status_code == 401:
                print("Authentication failed - check API key")
                return False
            elif response.status_code == 404:
                print("Instance not initialized - need to initialize first")
                return False
            else:
                print(f"WhatsApp verification failed with status {response.status_code}")
                return False
                
        except requests.Timeout:
            print("WhatsApp verification timeout - assuming registered")
            return True
        except Exception as e:
            print(f"WhatsApp verification error: {e}")
            return False

    def send_whatsapp_message(self, phone: str, message: str) -> bool:
        """Send WhatsApp message using the correct endpoint"""
        try:
            cleaned_phone = self.clean_phone_number(phone)
            if not cleaned_phone:
                print("Cannot send WhatsApp - invalid phone number")
                return False
            
            print(f"Attempting to send WhatsApp message to: '{cleaned_phone}' with token: {self.connection_token}")
            
            response = requests.post(
                f"{self.bridge_url}/send",
                headers=self._get_headers(),
                json={
                    "number": cleaned_phone,
                    "message": message
                },
                timeout=self.timeout
            )
            
            print(f"Send response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"WhatsApp message sent successfully: {result}")
                return result.get('success', False)
            else:
                print(f"Send failed: {response.status_code} - {response.text}")
                return False
                
        except requests.Timeout:
            print("WhatsApp send timed out")
            return False
        except Exception as e:
            print(f"WhatsApp send failed: {e}")
            return False

    # ... [rest of the methods remain the same - payment notifications, etc.]
    
    def send_payment_notification(self, payment_data: Dict[str, Any]) -> bool:
        """Send payment notification via WhatsApp"""
        try:
            print("=== WHATSAPP PAYMENT NOTIFICATION START ===")
            print(f"Using connection token: {self.connection_token}")
            
            guardian_phone = payment_data.get('guardian_phone')
            if not guardian_phone:
                print("No guardian phone number provided")
                return False
            
            print(f"Guardian phone: '{guardian_phone}'")
            
            # Check instance health first
            health = self.check_bridge_health()
            print(f"Instance health: {health}")
            
            if not health.get('ready', False):
                print(f"Instance not ready, cannot send notification")
                return False
            
            # Format message
            message = self._format_payment_message(payment_data)
            if not message:
                print("Failed to format payment message")
                return False
            
            print("Payment message formatted successfully")
            
            # Send message
            success = self.send_whatsapp_message(guardian_phone, message)
            
            if success:
                print("=== WHATSAPP PAYMENT NOTIFICATION SUCCESS ===")
            else:
                print("=== WHATSAPP PAYMENT NOTIFICATION FAILED ===")
            
            return success
            
        except Exception as e:
            print(f"Payment notification error: {e}")
            return False
    
    def _format_payment_message(self, payment_data: Dict[str, Any]) -> Optional[str]:
        """Format payment confirmation message for WhatsApp"""
        try:
            school_name = payment_data.get('school_name', 'School')
            student_name = payment_data.get('student_name', 'Student')
            admission_no = payment_data.get('admission_no', 'N/A')
            amount_paid = payment_data.get('amount_paid', 0)
            method = payment_data.get('method', 'Payment')
            reference = payment_data.get('reference', 'N/A')
            remaining_balance = payment_data.get('remaining_balance', 0)
            
            # Build message
            message = f"*{school_name}* - Payment Received\n\n"
            message += f"*Student:* {student_name} (#{admission_no})\n"
            message += f"*Amount:* KES {float(amount_paid):,.2f}\n"
            message += f"*Method:* {method}\n"
            
            if reference and reference != 'N/A':
                message += f"*Reference:* {reference}\n"
            
            if remaining_balance and float(remaining_balance) > 0:
                message += f"*Remaining Balance:* KES {float(remaining_balance):,.2f}\n"
            else:
                message += f"*Status:* Fully Paid\n"
            
            message += f"\nPayment recorded on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n"
            message += f"\nThank you for your payment!"
            
            return message
            
        except Exception as e:
            print(f"Error formatting payment message: {e}")
            return None

    def send_invoice_notification(self, invoice_data: Dict[str, Any]) -> bool:
        """Send invoice generation notification via WhatsApp"""
        try:
            guardian_phone = invoice_data.get('guardian_phone')
            if not guardian_phone:
                return False
            
            message = self._format_invoice_message(invoice_data)
            if not message:
                return False
            
            return self.send_whatsapp_message(guardian_phone, message)
            
        except Exception as e:
            print(f"Invoice notification error: {e}")
            return False
    
    def _format_invoice_message(self, invoice_data: Dict[str, Any]) -> Optional[str]:
        """Format invoice notification message"""
        try:
            school_name = invoice_data.get('school_name', 'School')
            student_name = invoice_data.get('student_name', 'Student')
            admission_no = invoice_data.get('admission_no', 'N/A')
            outstanding_amount = invoice_data.get('outstanding_amount', 0)
            
            message = f"*{school_name}* - Fee Reminder\n\n"
            message += f"*Student:* {student_name} (#{admission_no})\n"
            message += f"*Outstanding Balance:* KES {float(outstanding_amount):,.2f}\n"
            message += f"\nPlease make payment as soon as possible.\n"
            message += f"Contact the school for payment methods.\n"
            message += f"\nThank you for your attention."
            
            return message
            
        except Exception as e:
            print(f"Error formatting invoice message: {e}")
            return None

    def logout(self) -> Dict[str, Any]:
        """Logout this WhatsApp instance"""
        try:
            if not self.connection_token:
                return {'success': False, 'error': 'No connection token provided'}
            
            # Clear stored QR code
            self._clear_qr_code()
            
            response = requests.post(
                f"{self.bridge_url}/logout",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f'Logout failed: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Logout error: {str(e)}'
            }

    def test_connection(self, test_phone: str = None) -> Dict[str, Any]:
        """Test WhatsApp connection with detailed diagnostics"""
        test_results = {
            'bridge_health': False,
            'instance_status': False,
            'auth_status': False,
            'phone_verification': False,
            'message_send': False,
            'overall_status': False,
            'errors': [],
            'connection_token': self.connection_token
        }
        
        try:
            # Test 1: Bridge Health
            print(f"Testing bridge health for token: {self.connection_token}")
            health = self.check_bridge_health()
            test_results['bridge_health'] = 'error' not in health
            test_results['instance_status'] = health.get('ready', False)
            test_results['auth_status'] = health.get('ready', False)
            
            if not test_results['instance_status']:
                status = health.get('status', 'unknown')
                if status == 'not_initialized':
                    test_results['errors'].append("Instance not initialized - call initialize_connection() first")
                elif status == 'waiting_for_scan':
                    test_results['errors'].append("QR code scan required")
                else:
                    test_results['errors'].append(f"Instance not ready: {health.get('error', status)}")
            
            # Test 2: Phone Verification (if test phone provided and instance is ready)
            if test_phone and test_results['instance_status']:
                print(f"Testing phone verification with: {test_phone}")
                test_results['phone_verification'] = self.verify_whatsapp_registration(test_phone)
                if not test_results['phone_verification']:
                    test_results['errors'].append("Phone verification failed")
                
                # Test 3: Message Send
                print("Testing message send...")
                test_message = f"WhatsApp test from {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Token: {self.connection_token})"
                test_results['message_send'] = self.send_whatsapp_message(test_phone, test_message)
                if not test_results['message_send']:
                    test_results['errors'].append("Message send failed")
            
            # Overall status
            required_tests = ['bridge_health', 'instance_status']
            if test_phone:
                required_tests.extend(['message_send'])
            
            test_results['overall_status'] = all(test_results[test] for test in required_tests)
            
            print(f"WhatsApp test results: {test_results}")
            return test_results
            
        except Exception as e:
            test_results['errors'].append(f"Test failed: {str(e)}")
            print(f"WhatsApp connection test failed: {e}")
            return test_results


# Configuration
def configure_whatsapp_service():
    """Configure WhatsApp service with environment variables"""
    import os
    
    if not os.getenv('WHATSAPP_BRIDGE_URL'):
        os.environ['WHATSAPP_BRIDGE_URL'] = 'http://localhost:3001'
    
    if not os.getenv('WHATSAPP_TIMEOUT'):
        os.environ['WHATSAPP_TIMEOUT'] = '30'
        
    if not os.getenv('WA_BRIDGE_API_KEY'):
        os.environ['WA_BRIDGE_API_KEY'] = 'dev-secret'

configure_whatsapp_service()