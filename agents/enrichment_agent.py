"""
Data Enrichment Agent - Enrich lead data using Clearbit
"""
from typing import Any, Dict, List
from datetime import datetime
from agents.base_agent import BaseAgent
from tools.clearbit_api import ClearbitAPI

class DataEnrichmentAgent(BaseAgent):
    """Agent for enriching lead data with additional context"""
    
    def _initialize(self):
        """Initialize Clearbit API client"""
        self.clearbit_client = ClearbitAPI()
        self.logger.info(" DataEnrichmentAgent initialized")
    
    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input contains leads to enrich"""
        if 'leads' not in input_data:
            self.logger.error(" Missing required input key: leads")
            return False
        
        leads = input_data['leads']
        if not isinstance(leads, list):
            self.logger.error(" Leads must be a list")
            return False
        
        if len(leads) == 0:
            self.logger.warning("  Empty leads list provided")
            return True  # Not an error, just no work to do
        
        self.logger.info(f" Input validation passed: {len(leads)} leads to enrich")
        return True
    
    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute data enrichment workflow
        
        ReAct Pattern:
        1. Thought: Identify what data needs enrichment
        2. Action: Enrich company data from Clearbit
        3. Observation: Review enriched data quality
        4. Action: Enrich person data from Clearbit
        5. Observation: Combine and structure results
        """
        leads = input_data['leads']
        
        if not leads:
            return {
                "enriched_leads": [],
                "enrichment_timestamp": datetime.now().isoformat(),
                "total_enriched": 0
            }
        
        # === THOUGHT 1: Plan enrichment strategy ===
        self._log_reasoning(
            "Plan Enrichment",
            f"Enriching {len(leads)} leads with company and person data"
        )
        
        enriched_leads = []
        successful_enrichments = 0
        
        for idx, lead in enumerate(leads, 1):
            company_domain = lead.get('company_domain', '')
            email = lead.get('email', '')
            
            self._log_action(
                "Enrich Lead",
                {"lead_num": idx, "company": lead.get('company', ''), "contact": lead.get('contact_name', '')}
            )
            
            # === ACTION 1: Enrich company data ===
            company_enriched = {}
            if company_domain:
                self._log_action("Clearbit Company Lookup", {"domain": company_domain})
                company_enriched = self.clearbit_client.enrich_company(company_domain)
            
            # === ACTION 2: Enrich person data ===
            person_enriched = {}
            if email:
                self._log_action("Clearbit Person Lookup", {"email": email})
                person_enriched = self.clearbit_client.enrich_person(email)
            
            # === OBSERVATION: Combine enriched data ===
            enriched_lead = {
                # Original lead data
                "company": lead.get('company', ''),
                "company_domain": company_domain,
                "contact": lead.get('contact_name', ''),
                "email": email,
                "linkedin": lead.get('linkedin', ''),
                "phone": lead.get('phone', ''),
                "title": lead.get('title', ''),
                "signal": lead.get('signal', ''),
                
                # Enriched company data
                "company_description": company_enriched.get('description', ''),
                "company_industry": company_enriched.get('category', {}).get('industry', lead.get('industry', '')),
                "company_employees": company_enriched.get('employees', lead.get('company_size', 0)),
                "company_revenue": company_enriched.get('metrics', {}).get('annualRevenue', lead.get('revenue', 0)),
                "company_founded": company_enriched.get('foundedYear', ''),
                "company_location": company_enriched.get('location', lead.get('location', '')),
                
                # Technologies
                "technologies": company_enriched.get('tech', lead.get('technologies', [])),
                
                # Social profiles
                "social_profiles": {
                    "linkedin": company_enriched.get('linkedin', {}).get('handle', ''),
                    "twitter": company_enriched.get('twitter', {}).get('handle', ''),
                    "facebook": company_enriched.get('facebook', {}).get('handle', '')
                },
                
                # Person enrichment
                "role": person_enriched.get('employment', {}).get('title', lead.get('title', '')),
                "seniority": person_enriched.get('employment', {}).get('seniority', ''),
                "person_location": person_enriched.get('location', ''),
                "person_bio": person_enriched.get('bio', ''),
                
                # Recent news/signals (mock for now)
                "recent_news": company_enriched.get('recent_news', []),
                
                # Enrichment metadata
                "enrichment_source": "clearbit",
                "enrichment_quality": self._assess_enrichment_quality(company_enriched, person_enriched)
            }
            
            enriched_leads.append(enriched_lead)
            
            if company_enriched or person_enriched:
                successful_enrichments += 1
            
            self._log_observation(
                f"Enriched lead {idx}/{len(leads)} - Quality: {enriched_lead['enrichment_quality']}"
            )
        
        # === FINAL OBSERVATION ===
        enrichment_rate = (successful_enrichments / len(leads)) * 100 if leads else 0
        self._log_observation(
            f"Enrichment complete: {successful_enrichments}/{len(leads)} leads ({enrichment_rate:.1f}%)"
        )
        
        self.logger.info(f" DataEnrichmentAgent completed: {len(enriched_leads)} leads enriched")
        
        return {
            "enriched_leads": enriched_leads,
            "total_enriched": len(enriched_leads),
            "successful_enrichments": successful_enrichments,
            "enrichment_rate": enrichment_rate / 100,
            "enrichment_timestamp": datetime.now().isoformat()
        }
    
    def _assess_enrichment_quality(
        self,
        company_data: Dict[str, Any],
        person_data: Dict[str, Any]
    ) -> str:
        """Assess quality of enriched data"""
        score = 0
        
        # Company data quality
        if company_data:
            score += 1
            if company_data.get('description'):
                score += 1
            if company_data.get('tech'):
                score += 1
            if company_data.get('metrics'):
                score += 1
        
        # Person data quality
        if person_data:
            score += 1
            if person_data.get('employment'):
                score += 1
        
        if score >= 5:
            return "high"
        elif score >= 3:
            return "medium"
        else:
            return "low"