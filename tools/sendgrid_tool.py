"""
SendGrid API Tool - Email sending service
"""
import time
from typing import Any, Dict, List, Optional
from utils.logger import get_logger
from utils.config_loader import get_config

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

logger = get_logger("sendgrid_api")

class SendGridTool:
    """SendGrid API wrapper for email sending"""
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False):
        self.api_key = api_key or get_config().get_env("SENDGRID_API_KEY", "")
        self.mock_mode = mock_mode or get_config().get_workflow_config().enable_mock_mode
        self.from_email = get_config().get_env("SENDGRID_FROM_EMAIL", "noreply@example.com")
        self.from_name = get_config().get_env("SENDGRID_FROM_NAME", "AI Agent")
        
        if not SENDGRID_AVAILABLE:
            logger.warning("SendGrid library not installed, using mock mode")
            self.mock_mode = True
        
        if not self.api_key and not self.mock_mode:
            logger.warning("SendGrid API key not found, falling back to mock mode")
            self.mock_mode = True
        
        if not self.mock_mode and SENDGRID_AVAILABLE:
            self.client = SendGridAPIClient(self.api_key)
        else:
            self.client = None
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        to_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email via SendGrid
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            to_name: Recipient name
            
        Returns:
            Send status with message ID
        """
        if self.mock_mode:
            return self._mock_send_email(to_email, subject, body)
        
        try:
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email, to_name),
                subject=subject,
                plain_text_content=Content("text/plain", body)
            )
            
            start_time = time.time()
            response = self.client.send(message)
            response_time = time.time() - start_time
            
            logger.log_api_call("SendGrid", "send_email", "success", response_time)
            
            message_id = response.headers.get('X-Message-Id', f"sg_{int(time.time())}")
            
            logger.info(f"Email sent to {to_email} - Message ID: {message_id}")
            
            return {
                "status": "sent",
                "email": to_email,
                "subject": subject,
                "message_id": message_id,
                "status_code": response.status_code,
                "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"SendGrid email send failed to {to_email}: {e}")
            return {
                "status": "failed",
                "email": to_email,
                "error": str(e),
                "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def send_batch(
        self,
        emails: List[Dict[str, str]],
        delay_seconds: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Send multiple emails with rate limiting
        
        Args:
            emails: List of email dicts with to_email, subject, body
            delay_seconds: Delay between sends
            
        Returns:
            List of send statuses
        """
        results = []
        
        for idx, email_data in enumerate(emails, 1):
            logger.info(f"Sending email {idx}/{len(emails)}...")
            
            result = self.send_email(
                to_email=email_data.get('to_email'),
                subject=email_data.get('subject'),
                body=email_data.get('body'),
                to_name=email_data.get('to_name')
            )
            
            results.append(result)
            
            # Rate limiting
            if idx < len(emails):
                time.sleep(delay_seconds)
        
        return results
    
    def _mock_send_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Mock email sending"""
        logger.info(f"MOCK MODE: Simulating email send to {to_email}")
        logger.debug(f"   Subject: {subject}")
        logger.debug(f"   Body: {body[:100]}...")
        
        # Simulate 10% failure rate in mock mode
        import random
        if random.random() < 0.1:
            return {
                "status": "failed",
                "email": to_email,
                "error": "Mock failure: Simulated bounce",
                "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        
        return {
            "status": "sent",
            "email": to_email,
            "subject": subject,
            "message_id": f"mock_msg_{int(time.time())}_{hash(to_email) % 10000}",
            "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }