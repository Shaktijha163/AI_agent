"""
Apollo API Tool - Contact search and outreach
"""
import requests
import time
from typing import Any, Dict, List, Optional
from utils.logger import get_logger
from utils.config_loader import get_config

logger = get_logger("apollo_api")

class ApolloAPI:
    """Apollo.io API wrapper for contact search and engagement"""
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False):
        self.api_key = api_key or get_config().get_env("APOLLO_API_KEY", "")
        self.mock_mode = mock_mode or get_config().get_workflow_config().enable_mock_mode
        self.base_url = "https://api.apollo.io/v1"
        self.timeout = 30
        self.max_retries = 3
        
        if not self.api_key and not self.mock_mode:
            logger.warning("Apollo API key not found, falling back to mock mode")
            self.mock_mode = True
    
    def search_people(
        self, 
        company_name: Optional[str] = None,
        titles: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for contacts/people
        
        Args:
            company_name: Filter by company name
            titles: List of job titles to search for
            limit: Maximum number of results
            
        Returns:
            List of contact dictionaries
        """
        if self.mock_mode:
            return self._mock_search_people(company_name, titles, limit)
        
        endpoint = f"{self.base_url}/mixed_people/search"
        
        payload = {
            "q_keywords": company_name if company_name else "",
            "person_titles": titles or ["VP of Sales", "Head of Sales", "Sales Director"],
            "per_page": limit,
            "api_key": self.api_key
        }
        
        start_time = time.time()
        
        try:
            response = self._make_request_with_retry(
                "POST",
                endpoint,
                json=payload
            )
            
            response_time = time.time() - start_time
            logger.log_api_call("Apollo", endpoint, "success", response_time)
            
            data = response.json()
            contacts = data.get("people", [])
            
            logger.info(f"Found {len(contacts)} contacts from Apollo")
            return contacts
            
        except Exception as e:
            logger.error(f"Apollo people search failed: {e}")
            return []
    
    def mixed_search(
        self,
        filters: Dict[str, Any],
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Combined company and contact search
        
        Args:
            filters: Search filters
            limit: Maximum results
            
        Returns:
            Combined search results
        """
        if self.mock_mode:
            return self._mock_mixed_search(filters, limit)
        
        endpoint = f"{self.base_url}/mixed_search"
        
        payload = {
            **filters,
            "per_page": limit,
            "api_key": self.api_key
        }
        
        try:
            response = self._make_request_with_retry(
                "POST",
                endpoint,
                json=payload
            )
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Apollo mixed search failed: {e}")
            return {"people": [], "organizations": []}
    
    def send_email(
        self,
        email_address: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email through Apollo
        
        Args:
            email_address: Recipient email
            subject: Email subject
            body: Email body
            from_email: Sender email
            
        Returns:
            Send status
        """
        if self.mock_mode:
            return self._mock_send_email(email_address, subject)
        
        endpoint = f"{self.base_url}/emailer_campaigns/send_email"
        
        payload = {
            "email_address": email_address,
            "subject": subject,
            "body": body,
            "from_email": from_email,
            "api_key": self.api_key
        }
        
        try:
            response = self._make_request_with_retry(
                "POST",
                endpoint,
                json=payload
            )
            
            logger.info(f"Email sent to {email_address}")
            return response.json()
            
        except Exception as e:
            logger.error(f" Apollo email send failed to {email_address}: {e}")
            return {"status": "failed", "error": str(e)}
    
    def track_email_activity(
        self,
        campaign_id: str
    ) -> Dict[str, Any]:
        """
        Track email campaign activity
        
        Args:
            campaign_id: Campaign ID to track
            
        Returns:
            Campaign metrics
        """
        if self.mock_mode:
            return self._mock_track_activity(campaign_id)
        
        endpoint = f"{self.base_url}/emailer_campaigns/{campaign_id}/email_statuses"
        
        params = {"api_key": self.api_key}
        
        try:
            response = self._make_request_with_retry(
                "GET",
                endpoint,
                params=params
            )
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Apollo tracking failed for campaign {campaign_id}: {e}")
            return {}
    
    def _make_request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """Make HTTP request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                
                wait_time = 2 ** attempt
                logger.warning(f" Retry {attempt + 1}/{self.max_retries} after {wait_time}s")
                time.sleep(wait_time)
    
    def _mock_search_people(
        self,
        company_name: Optional[str],
        titles: Optional[List[str]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Generate mock contact search results"""
        logger.info(f"MOCK MODE: Generating {limit} mock contacts for {company_name}")
        
        mock_contacts = [
            {
                "id": f"apollo_{i}",
                "first_name": f"John",
                "last_name": f"Doe{i}",
                "name": f"John Doe{i}",
                "title": "VP of Sales" if i % 2 == 0 else "Head of Marketing",
                "email": f"john.doe{i}@{company_name.lower().replace(' ', '')}.com" if company_name else f"john.doe{i}@example.com",
                "linkedin_url": f"https://linkedin.com/in/johndoe{i}",
                "company_name": company_name or f"Company {i}",
                "phone": f"+1 (555) {100 + i:03d}-{1000 + i:04d}"
            }
            for i in range(1, min(limit, 5) + 1)
        ]
        
        return mock_contacts
    
    def _mock_mixed_search(
        self,
        filters: Dict[str, Any],
        limit: int
    ) -> Dict[str, Any]:
        """Generate mock mixed search results"""
        logger.info(f"MOCK MODE: Mixed search with {limit} results")
        
        return {
            "people": self._mock_search_people(None, None, limit // 2),
            "organizations": [
                {
                    "name": f"Company {i}",
                    "domain": f"company{i}.com",
                    "industry": "SaaS"
                }
                for i in range(1, (limit // 2) + 1)
            ]
        }
    
    def _mock_send_email(
        self,
        email_address: str,
        subject: str
    ) -> Dict[str, Any]:
        """Mock email send"""
        logger.info(f"MOCK MODE: Simulating email send to {email_address}")
        
        return {
            "status": "sent",
            "email": email_address,
            "subject": subject,
            "message_id": f"msg_{int(time.time())}",
            "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _mock_track_activity(
        self,
        campaign_id: str
    ) -> Dict[str, Any]:
        """Mock campaign tracking"""
        logger.info(f"MOCK MODE: Tracking campaign {campaign_id}")
        
        return {
            "campaign_id": campaign_id,
            "total_sent": 50,
            "opened": 25,
            "clicked": 10,
            "replied": 5,
            "bounced": 2,
            "metrics": {
                "open_rate": 0.50,
                "click_rate": 0.20,
                "reply_rate": 0.10
            }
        }