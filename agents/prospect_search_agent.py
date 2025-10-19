"""
Prospect Search Agent - Find leads using Clay and Apollo APIs
"""
from typing import Any, Dict, List
from datetime import datetime
from agents.base_agent import BaseAgent
from tools.clay_api import ClayAPI
from tools.apollo_api import ApolloAPI

class ProspectSearchAgent(BaseAgent):
    """Agent for searching and identifying prospect leads"""
    
    def _initialize(self):
        """Initialize Clay and Apollo API clients"""
        self.clay_client = ClayAPI()
        self.apollo_client = ApolloAPI()
        self.logger.info(" ProspectSearchAgent initialized")
    
    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input contains ICP criteria"""
        required_keys = ['icp']
        
        for key in required_keys:
            if key not in input_data:
                self.logger.error(f" Missing required input key: {key}")
                return False
        
        icp = input_data['icp']
        if not isinstance(icp, dict):
            self.logger.error(" ICP must be a dictionary")
            return False
        
        self.logger.info(" Input validation passed")
        return True
    
    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute prospect search workflow
        
        ReAct Pattern:
        1. Thought: Analyze ICP criteria
        2. Action: Search Clay for companies
        3. Observation: Review company matches
        4. Action: Search Apollo for contacts
        5. Observation: Combine and format results
        """
        icp = input_data['icp']
        signals = input_data.get('signals', [])
        max_leads = input_data.get('max_leads', 50)
        
        # === THOUGHT 1: Analyze search criteria ===
        self._log_reasoning(
            "Analyze ICP",
            f"Searching for companies in {icp.get('industry', [])} with {icp.get('employee_count', {})} employees"
        )
        
        # === ACTION 1: Search companies in Clay ===
        self._log_action("Search Clay", {"filters": icp, "limit": max_leads})
        
        companies = self.clay_client.search_companies(
            filters=icp,
            limit=max_leads
        )
        
        # === OBSERVATION 1: Review companies ===
        self._log_observation(f"Found {len(companies)} companies from Clay")
        
        if not companies:
            self.logger.warning("  No companies found, returning empty results")
            return {
                "leads": [],
                "total_found": 0,
                "search_timestamp": datetime.now().isoformat()
            }
        
        # === THOUGHT 2: Need to find contacts at these companies ===
        self._log_reasoning(
            "Find Contacts",
            f"Searching for decision makers at {len(companies)} companies"
        )
        
        # === ACTION 2: Search contacts in Apollo ===
        all_leads = []
        
        for company in companies[:max_leads]:
            company_name = company.get('company_name', '')
            
            self._log_action(
                "Search Apollo Contacts",
                {"company": company_name, "titles": ["VP", "Director", "Head"]}
            )
            
            contacts = self.apollo_client.search_people(
                company_name=company_name,
                titles=["VP of Sales", "Head of Sales", "Sales Director", "VP of Marketing"],
                limit=3  # Get top 3 contacts per company
            )
            
            # === OBSERVATION 2: Combine company + contact data ===
            for contact in contacts:
                lead = {
                    "company": company_name,
                    "company_domain": company.get('domain', ''),
                    "contact_name": contact.get('name', ''),
                    "contact_first_name": contact.get('first_name', ''),
                    "contact_last_name": contact.get('last_name', ''),
                    "email": contact.get('email', ''),
                    "linkedin": contact.get('linkedin_url', ''),
                    "phone": contact.get('phone', ''),
                    "title": contact.get('title', ''),
                    "signal": company.get('growth_signal', 'general_outreach'),
                    "company_size": company.get('employee_count', 0),
                    "revenue": company.get('revenue', 0),
                    "industry": company.get('industry', ''),
                    "location": company.get('location', ''),
                    "technologies": company.get('technologies', [])
                }
                all_leads.append(lead)
        
        # === OBSERVATION 3: Final results ===
        self._log_observation(f"Created {len(all_leads)} qualified leads from search")
        
        self.logger.info(f" ProspectSearchAgent completed: {len(all_leads)} leads")
        
        return {
            "leads": all_leads,
            "total_found": len(all_leads),
            "companies_searched": len(companies),
            "search_timestamp": datetime.now().isoformat(),
            "icp_criteria": icp,
            "signals_used": signals
        }