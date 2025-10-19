"""
Scoring Agent - Score and rank leads based on ICP fit
"""
from typing import Any, Dict, List
from datetime import datetime
from agents.base_agent import BaseAgent

class ScoringAgent(BaseAgent):
    """Agent for scoring and ranking leads"""
    
    def _initialize(self):
        """Initialize scoring configuration"""
        self.scoring_config = self.config_loader.get_scoring_config()
        self.weights = self.scoring_config.get('weights', {})
        self.min_threshold = self.scoring_config.get('min_score_threshold', 0.6)
        self.logger.info(f" ScoringAgent initialized with threshold: {self.min_threshold}")
    
    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input contains enriched leads"""
        if 'enriched_leads' not in input_data:
            self.logger.error(" Missing required input key: enriched_leads")
            return False
        
        enriched_leads = input_data['enriched_leads']
        if not isinstance(enriched_leads, list):
            self.logger.error(" enriched_leads must be a list")
            return False
        
        self.logger.info(f" Input validation passed: {len(enriched_leads)} leads to score")
        return True
    
    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute lead scoring workflow
        
        ReAct Pattern:
        1. Thought: Analyze scoring criteria
        2. Action: Calculate individual scores
        3. Observation: Review score distribution
        4. Action: Rank leads
        5. Observation: Identify top performers
        """
        enriched_leads = input_data['enriched_leads']
        scoring_criteria = input_data.get('scoring_criteria', self.scoring_config)
        
        if not enriched_leads:
            return {
                "ranked_leads": [],
                "avg_score": 0.0,
                "total_scored": 0,
                "scoring_timestamp": datetime.now().isoformat()
            }
        
        # === THOUGHT 1: Understand scoring strategy ===
        self._log_reasoning(
            "Analyze Criteria",
            f"Scoring {len(enriched_leads)} leads using weights: {self.weights}"
        )
        
        # === ACTION 1: Score each lead ===
        scored_leads = []
        
        for lead in enriched_leads:
            self._log_action("Score Lead", {"company": lead.get('company', 'Unknown')})
            
            # Calculate component scores
            icp_fit = self._score_icp_fit(lead)
            growth_signals = self._score_growth_signals(lead)
            engagement_potential = self._score_engagement_potential(lead)
            
            # Calculate weighted total
            total_score = (
                icp_fit * self.weights.get('industry_match', 0.25) +
                growth_signals * self.weights.get('growth_signals', 0.25) +
                engagement_potential * self.weights.get('technology_stack', 0.25) +
                self._score_company_size(lead) * self.weights.get('company_size', 0.25)
            )
            
            scored_lead = {
                "lead": lead,
                "score": round(total_score, 3),
                "score_breakdown": {
                    "icp_fit": round(icp_fit, 3),
                    "growth_signals": round(growth_signals, 3),
                    "engagement_potential": round(engagement_potential, 3),
                    "company_size_score": round(self._score_company_size(lead), 3)
                },
                "meets_threshold": total_score >= self.min_threshold
            }
            
            scored_leads.append(scored_lead)
            
            self._log_observation(
                f"Lead scored: {lead.get('company')} = {total_score:.2f} "
                f"(ICP: {icp_fit:.2f}, Growth: {growth_signals:.2f}, Engagement: {engagement_potential:.2f})"
            )
        
        # === OBSERVATION 1: Review distribution ===
        avg_score = sum(sl['score'] for sl in scored_leads) / len(scored_leads)
        qualified_count = sum(1 for sl in scored_leads if sl['meets_threshold'])
        
        self._log_observation(
            f"Score distribution - Avg: {avg_score:.2f}, "
            f"Qualified: {qualified_count}/{len(scored_leads)} ({qualified_count/len(scored_leads)*100:.1f}%)"
        )
        
        # === ACTION 2: Rank leads by score ===
        self._log_action("Rank Leads", {"total": len(scored_leads)})
        
        ranked_leads = sorted(scored_leads, key=lambda x: x['score'], reverse=True)
        
        # Add rank numbers
        for rank, lead in enumerate(ranked_leads, 1):
            lead['rank'] = rank
        
        # === OBSERVATION 2: Identify top performers ===
        top_5 = ranked_leads[:5]
        self._log_observation(
            "Top 5 leads: " + ", ".join([f"{l['lead'].get('company')} ({l['score']:.2f})" for l in top_5])
        )

        
        self.logger.info(f" ScoringAgent completed: {len(ranked_leads)} leads ranked")
        
        return {
            "ranked_leads": ranked_leads,
            "total_scored": len(ranked_leads),
            "qualified_leads": qualified_count,
            "avg_score": round(avg_score, 3),
            "min_score": round(min(sl['score'] for sl in scored_leads), 3),
            "max_score": round(max(sl['score'] for sl in scored_leads), 3),
            "scoring_timestamp": datetime.now().isoformat(),
            "scoring_criteria": scoring_criteria
        }
    
    def _score_icp_fit(self, lead: Dict[str, Any]) -> float:
        """Score how well lead matches ICP"""
        score = 0.0
        max_score = 4.0
        
        # Industry match
        icp_config = self.config_loader.get_icp_config()
        target_industries = icp_config.get('industry', [])
        lead_industry = lead.get('company_industry', lead.get('industry', ''))
        
        if any(industry.lower() in lead_industry.lower() for industry in target_industries):
            score += 1.5
        
        # Location match
        target_locations = icp_config.get('location', [])
        lead_location = lead.get('company_location', lead.get('location', ''))
        
        if any(loc in lead_location for loc in target_locations):
            score += 1.0
        
        # Enrichment quality
        if lead.get('enrichment_quality') == 'high':
            score += 1.0
        elif lead.get('enrichment_quality') == 'medium':
            score += 0.5
        
        # Has technologies
        if lead.get('technologies'):
            score += 0.5
        
        return min(score / max_score, 1.0)
    
    def _score_growth_signals(self, lead: Dict[str, Any]) -> float:
        """Score growth signals"""
        score = 0.0
        
        signal = lead.get('signal', '').lower()
        
        # Signal strength
        signal_scores = {
            'recent_funding': 1.0,
            'hiring_for_sales': 0.8,
            'rapid_growth': 0.7,
            'new_product_launch': 0.6
        }
        
        for sig, sig_score in signal_scores.items():
            if sig in signal:
                score = max(score, sig_score)
        
        # Has recent news
        if lead.get('recent_news'):
            score += 0.3
        
        return min(score, 1.0)
    
    def _score_engagement_potential(self, lead: Dict[str, Any]) -> float:
        """Score engagement potential"""
        score = 0.0
        
        # Has email
        if lead.get('email'):
            score += 0.4
        
        # Has LinkedIn
        if lead.get('linkedin'):
            score += 0.2
        
        # Has phone
        if lead.get('phone'):
            score += 0.1
        
        # Seniority level
        seniority = lead.get('seniority', '').lower()
        if 'executive' in seniority or 'vp' in lead.get('title', '').lower():
            score += 0.3
        
        return min(score, 1.0)
    
    def _score_company_size(self, lead: Dict[str, Any]) -> float:
        """Score company size fit"""
        icp_config = self.config_loader.get_icp_config()
        size_range = icp_config.get('employee_count', {})
        min_size = size_range.get('min', 0)
        max_size = size_range.get('max', 10000)
        
        company_size = lead.get('company_employees', lead.get('company_size', 0))
        
        if min_size <= company_size <= max_size:
            # Perfect fit
            return 1.0
        elif company_size < min_size:
            # Too small, but closer is better
            return max(0.0, company_size / min_size * 0.5)
        else:
            # Too large, but closer is better
            return max(0.0, 1.0 - (company_size - max_size) / max_size * 0.5)