"""
Outreach Executor Agent - Send emails and track delivery
"""
from typing import Any, Dict, List
from datetime import datetime
import uuid
from agents.base_agent import BaseAgent
from tools.sendgrid_tool import SendGridTool
from tools.apollo_api import ApolloAPI

class OutreachExecutorAgent(BaseAgent):
    """Agent for executing email outreach campaigns"""
    
    def _initialize(self):
        """Initialize email sending tools"""
        self.sendgrid = SendGridTool()
        self.apollo = ApolloAPI()
        
        # Get campaign settings
        self.campaign_config = self.config_loader.get_yaml_config('campaign', {})
        self.batch_size = self.campaign_config.get('batch_size', 50)
        self.send_delay = self.campaign_config.get('time_between_sends', 300) / 1000  # Convert to seconds
        
        self.logger.info(" OutreachExecutorAgent initialized")
    
    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input contains messages to send"""
        if 'messages' not in input_data:
            self.logger.error("Missing required input key: messages")
            return False
        
        messages = input_data['messages']
        if not isinstance(messages, list):
            self.logger.error("messages must be a list")
            return False
        
        # Validate each message has required fields
        for msg in messages:
            if not msg.get('lead_email'):
                self.logger.error(f"Message missing lead_email: {msg}")
                return False
            if not msg.get('subject_line'):
                self.logger.error(f"Message missing subject_line: {msg}")
                return False
            if not msg.get('email_body'):
                self.logger.error(f"Message missing email_body: {msg}")
                return False
        
        self.logger.info(f"Input validation passed: {len(messages)} messages to send")
        return True
    
    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute email sending workflow
        
        ReAct Pattern:
        1. Thought: Prepare campaign and validate recipients
        2. Action: Send emails in batches
        3. Observation: Track delivery status
        4. Action: Handle failures and retries
        5. Observation: Generate campaign report
        """
        messages = input_data['messages']
        dry_run = input_data.get('dry_run', self._is_dry_run())
        
        # Generate campaign ID
        campaign_id = f"camp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # === THOUGHT 1: Prepare campaign ===
        self._log_reasoning(
            "Prepare Campaign",
            f"Campaign ID: {campaign_id}, Messages: {len(messages)}, Dry Run: {dry_run}"
        )
        
        if dry_run:
            self.logger.warning("DRY RUN MODE - Emails will not actually be sent")
            return self._dry_run_response(messages, campaign_id)
        
        # === ACTION 1: Send emails ===
        sent_status = []
        failed_emails = []
        successful_sends = 0
        
        self._log_action("Send Emails", {"total": len(messages), "batch_size": self.batch_size})
        
        for idx, message in enumerate(messages, 1):
            lead_email = message.get('lead_email')
            lead_name = message.get('lead_name', '')
            subject = message.get('subject_line')
            body = message.get('email_body')
            
            self._log_action(
                f"Send Email {idx}/{len(messages)}",
                {"to": lead_email, "subject": subject[:50]}
            )
            
            # Send via SendGrid (or Apollo as fallback)
            result = self.sendgrid.send_email(
                to_email=lead_email,
                subject=subject,
                body=body,
                to_name=lead_name
            )
            
            # === OBSERVATION 1: Check delivery status ===
            if result.get('status') == 'sent':
                successful_sends += 1
                self._log_observation(f" Email sent to {lead_email}")
            else:
                failed_emails.append(lead_email)
                self._log_observation(f" Failed to send to {lead_email}: {result.get('error')}")
            
            # Add metadata
            status_entry = {
                "lead_id": message.get('lead_id'),
                "lead_name": lead_name,
                "email": lead_email,
                "company": message.get('company'),
                "subject": subject,
                "status": result.get('status'),
                "message_id": result.get('message_id'),
                "sent_at": result.get('sent_at'),
                "error": result.get('error')
            }
            
            sent_status.append(status_entry)
            
            # Rate limiting between sends
            if idx < len(messages):
                import time
                time.sleep(self.send_delay)
        
        # === OBSERVATION 2: Campaign summary ===
        success_rate = (successful_sends / len(messages)) * 100 if messages else 0
        
        self._log_observation(
            f"Campaign complete: {successful_sends}/{len(messages)} sent ({success_rate:.1f}% success rate)"
        )
        
        if failed_emails:
            self.logger.warning(f"  Failed emails: {failed_emails}")
        
        self.logger.info(f" OutreachExecutorAgent completed: Campaign {campaign_id}")
        
        return {
            "campaign_id": campaign_id,
            "sent_status": sent_status,
            "total_sent": successful_sends,
            "total_failed": len(failed_emails),
            "success_rate": round(success_rate / 100, 3),
            "failed_emails": failed_emails,
            "send_timestamp": datetime.now().isoformat(),
            "campaign_metadata": {
                "batch_size": self.batch_size,
                "send_delay": self.send_delay,
                "dry_run": dry_run
            }
        }
    
    def _dry_run_response(self, messages: List[Dict], campaign_id: str) -> Dict[str, Any]:
        """Generate dry run response without sending"""
        self.logger.info("DRY RUN: Simulating email sends...")
        
        sent_status = [
            {
                "lead_id": msg.get('lead_id'),
                "lead_name": msg.get('lead_name'),
                "email": msg.get('lead_email'),
                "company": msg.get('company'),
                "subject": msg.get('subject_line'),
                "status": "dry_run",
                "message_id": f"dryrun_{idx}",
                "sent_at": datetime.now().isoformat()
            }
            for idx, msg in enumerate(messages, 1)
        ]
        
        return {
            "campaign_id": campaign_id,
            "sent_status": sent_status,
            "total_sent": len(messages),
            "total_failed": 0,
            "success_rate": 1.0,
            "failed_emails": [],
            "send_timestamp": datetime.now().isoformat(),
            "campaign_metadata": {
                "dry_run": True
            }
        }