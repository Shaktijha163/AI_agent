"""
Clay API Tool - Company and contact data enrichment
"""
import requests
import time
from typing import Any, Dict, List, Optional
from utils.logger import get_logger
from utils.config_loader import get_config

logger = get_logger("clay_api")

class ClayAPI:
    """Clay API wrapper for company search and enrichment"""
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False):
        self.api_key = api_key or get_config().get_env("CLAY_API_KEY", "")
        self.mock_mode = mock_mode or get_config().get_workflow_config().enable_mock_mode
        self.base_url = "https://api.clay.com"
        self.timeout = 30
        self.max_retries = 3
        
        if not self.api_key and not self.mock_mode:
            logger.warning(" Clay API key not found, falling back to mock mode")
            self.mock_mode = True
    
    def search_companies(
        self, 
        filters: Dict[str, Any], 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for companies matching criteria
        
        Args:
            filters: Search filters (industry, location, size, etc.)
            limit: Maximum number of results
            
        Returns:
            List of company dictionaries
        """
        if self.mock_mode:
            return self._mock_search_companies(filters, limit)
        
        endpoint = f"{self.base_url}/v1/companies/search"
        
        payload = {
            "filters": filters,
            "limit": limit
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        
        try:
            response = self._make_request_with_retry(
                "POST", 
                endpoint, 
                json=payload, 
                headers=headers
            )
            
            response_time = time.time() - start_time
            logger.log_api_call("Clay", endpoint, "success", response_time)
            
            data = response.json()
            companies = data.get("results", [])
            
            logger.info(f"Found {len(companies)} companies from Clay")
            return companies
            
        except Exception as e:
            logger.error(f"Clay API search failed: {e}")
            return []
    
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
        
        endpoint = f"{self.base_url}/v1/companies/enrich"
        
        payload = {"domain": domain}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self._make_request_with_retry(
                "POST",
                endpoint,
                json=payload,
                headers=headers
            )
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Clay enrich failed for {domain}: {e}")
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
                logger.warning(f"Retry {attempt + 1}/{self.max_retries} after {wait_time}s")
                time.sleep(wait_time)
    
    def _mock_search_companies(
        self, 
        filters: Dict[str, Any], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Generate mock company search results"""
        logger.info(f"MOCK MODE: Generating {limit} mock companies")
        
        mock_companies = [
            {
                "company_name": f"TechCorp {i}",
                "domain": f"techcorp{i}.com",
                "industry": "SaaS",
                "employee_count": 250 + (i * 50),
                "revenue": 50000000 + (i * 10000000),
                "location": "San Francisco, CA",
                "description": f"Leading SaaS company #{i} in workflow automation",
                "technologies": ["Python", "React", "AWS", "PostgreSQL"],
                "growth_signal": "recent_funding" if i % 2 == 0 else "hiring_for_sales"
            }
            for i in range(1, min(limit, 10) + 1)
        ]
        
        return mock_companies
    
    def _mock_enrich_company(self, domain: str) -> Dict[str, Any]:
        """Generate mock enriched company data"""
        logger.info(f" MOCK MODE: Enriching {domain}")
        
        return {
            "domain": domain,
            "company_name": domain.split('.')[0].title(),
            "employee_count": 500,
            "revenue": 75000000,
            "technologies": ["Python", "JavaScript", "AWS", "Docker"],
            "social_profiles": {
                "linkedin": f"https://linkedin.com/company/{domain.split('.')[0]}",
                "twitter": f"https://twitter.com/{domain.split('.')[0]}"
            },
            "recent_news": [
                "Raised $20M Series B funding",
                "Expanded to European market"
            ]
        }