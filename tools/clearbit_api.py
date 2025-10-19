"""
Clearbit API Tool - Company and person enrichment
"""
import requests
import time
from typing import Any, Dict, Optional
from utils.logger import get_logger
from utils.config_loader import get_config

logger = get_logger("clearbit_api")

class ClearbitAPI:
    """Clearbit API wrapper for data enrichment"""
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False):
        self.api_key = api_key or get_config().get_env("CLEARBIT_API_KEY", "")
        self.mock_mode = mock_mode or get_config().get_workflow_config().enable_mock_mode
        self.base_url = "https://company.clearbit.com/v2"
        self.person_url = "https://person.clearbit.com/v2"
        self.timeout = 30
        self.max_retries = 3
        
        if not self.api_key and not self.mock_mode:
            logger.warning(" Clearbit API key not found, falling back to mock mode")
            self.mock_mode = True
    
    def enrich_company(self, domain: str) -> Dict[str, Any]:
        """
        Enrich company data by domain
        
        Args:
            domain: Company domain
            
        Returns:
            Enriched company data
        """
        if self.mock_mode:
            return self._mock_enrich_company(domain)
        
        endpoint = f"{self.base_url}/companies/find"
        
        params = {"domain": domain}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        start_time = time.time()
        
        try:
            response = self._make_request_with_retry(
                "GET",
                endpoint,
                params=params,
                headers=headers
            )
            
            response_time = time.time() - start_time
            logger.log_api_call("Clearbit", endpoint, "success", response_time)
            
            data = response.json()
            logger.info(f"Enriched company data for {domain}")
            return data
            
        except Exception as e:
            logger.error(f"Clearbit company enrichment failed for {domain}: {e}")
            return {}
    
    def enrich_person(self, email: str) -> Dict[str, Any]:
        """
        Enrich person data by email
        
        Args:
            email: Person's email address
            
        Returns:
            Enriched person data
        """
        if self.mock_mode:
            return self._mock_enrich_person(email)
        
        endpoint = f"{self.person_url}/people/find"
        
        params = {"email": email}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = self._make_request_with_retry(
                "GET",
                endpoint,
                params=params,
                headers=headers
            )
            
            data = response.json()
            logger.info(f"Enriched person data for {email}")
            return data
            
        except Exception as e:
            logger.error(f"Clearbit person enrichment failed for {email}: {e}")
            return {}
    
    def combined_enrichment(self, email: str, domain: str) -> Dict[str, Any]:
        """
        Enrich both person and company data
        
        Args:
            email: Person's email
            domain: Company domain
            
        Returns:
            Combined enrichment data
        """
        person_data = self.enrich_person(email)
        company_data = self.enrich_company(domain)
        
        return {
            "person": person_data,
            "company": company_data
        }
    
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
                logger.warning(f"Retry {attempt + 1}/{self.max_retries} after {wait_time}s")
                time.sleep(wait_time)
    
    def _mock_enrich_company(self, domain: str) -> Dict[str, Any]:
        """Generate mock enriched company data"""
        logger.info(f"MOCK MODE: Enriching company {domain}")
        
        company_name = domain.split('.')[0].title()
        
        return {
            "name": company_name,
            "domain": domain,
            "description": f"{company_name} is a leading technology company specializing in innovative solutions.",
            "category": {
                "industry": "Technology",
                "sector": "Software"
            },
            "tags": ["SaaS", "B2B", "Enterprise"],
            "tech": ["Python", "React", "AWS", "PostgreSQL", "Redis"],
            "employees": 450,
            "employeesRange": "250-500",
            "foundedYear": 2015,
            "location": "San Francisco, CA, USA",
            "metrics": {
                "raised": 45000000,
                "annualRevenue": 75000000,
                "estimatedAnnualRevenue": "$50M-$100M"
            },
            "linkedin": {
                "handle": f"company/{company_name.lower()}"
            },
            "twitter": {
                "handle": company_name.lower(),
                "followers": 12500
            },
            "facebook": {
                "handle": company_name.lower()
            },
            "type": "private"
        }
    
    def _mock_enrich_person(self, email: str) -> Dict[str, Any]:
        """Generate mock enriched person data"""
        logger.info(f"MOCK MODE: Enriching person {email}")
        
        name_parts = email.split('@')[0].split('.')
        first_name = name_parts[0].title() if len(name_parts) > 0 else "John"
        last_name = name_parts[1].title() if len(name_parts) > 1 else "Doe"
        
        return {
            "name": {
                "fullName": f"{first_name} {last_name}",
                "givenName": first_name,
                "familyName": last_name
            },
            "email": email,
            "location": "San Francisco, CA, USA",
            "employment": {
                "name": email.split('@')[1].split('.')[0].title(),
                "title": "VP of Sales",
                "role": "sales",
                "seniority": "executive"
            },
            "linkedin": {
                "handle": f"in/{first_name.lower()}{last_name.lower()}"
            },
            "twitter": {
                "handle": f"{first_name.lower()}{last_name.lower()}",
                "followers": 3500
            },
            "bio": f"{first_name} is an experienced sales leader with expertise in B2B SaaS.",
            "avatar": f"https://i.pravatar.cc/150?u={email}"
        }