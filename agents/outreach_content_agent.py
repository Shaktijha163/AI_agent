"""
Outreach Content Agent - Generate personalized emails using Gemini AI
"""
from typing import Any, Dict, List
from datetime import datetime
from agents.base_agent import BaseAgent
from tools.gemini_tool import GeminiAPI

class OutreachContentAgent(BaseAgent):
    """Agent for generating personalized outreach content"""
    
    def _initialize(self):
        """Initialize Gemini API client"""
        try:
            self.gemini_client = GeminiAPI()
            self.logger.info("OutreachContentAgent initialized with Gemini AI")
        except Exception as e:
            self.logger.error(f" Failed to initialize Gemini: {e}")
            raise
    
    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input contains ranked leads"""
        if 'ranked_leads' not in input_data:
            self.logger.error(" Missing required input key: ranked_leads")
            return False
        
        ranked_leads = input_data['ranked_leads']
        if not isinstance(ranked_leads, list):
            self.logger.error("ranked_leads must be a list")
            return False
        
        self.logger.info(f" Input validation passed: {len(ranked_leads)} leads for content generation")
        return True
    
    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute outreach content generation workflow
        
        ReAct Pattern:
        1. Thought: Analyze lead characteristics
        2. Action: Generate personalized email for each lead
        3. Observation: Review personalization quality
        4. Action: Apply tone and formatting
        5. Observation: Validate output quality
        """
        ranked_leads = input_data['ranked_leads']
        persona = input_data.get('persona', 'SDR')
        tone = input_data.get('tone', 'friendly_professional')
        value_prop = input_data.get('value_proposition', 'AI-powered workflow automation')
        
        # Get config
        outreach_config = self.config_loader.get_yaml_config('outreach', {})
        max_leads = input_data.get('max_messages', 20)  # Limit for cost control
        
        if not ranked_leads:
            return {
                "messages": [],
                "total_generated": 0,
                "generation_timestamp": datetime.now().isoformat()
            }
        
        # === THOUGHT 1: Prioritize high-scoring leads ===
        self._log_reasoning(
            "Prioritize Leads",
            f"Generating content for top {min(max_leads, len(ranked_leads))} leads (persona: {persona}, tone: {tone})"
        )
        
        # Filter qualified leads and take top N
        qualified_leads = [
            lead for lead in ranked_leads 
            if lead.get('meets_threshold', True) and lead.get('lead', {}).get('email')
        ][:max_leads]
        
        self._log_observation(f"Selected {len(qualified_leads)} qualified leads for outreach")
        
        # === ACTION 1: Generate content for each lead ===
        messages = []
        successful_generations = 0
        
        for idx, ranked_lead in enumerate(qualified_leads, 1):
            lead = ranked_lead['lead']
            score = ranked_lead['score']
            
            self._log_action(
                "Generate Email",
                {
                    "lead_num": idx,
                    "company": lead.get('company'),
                    "score": score,
                    "signal": lead.get('signal')
                }
            )
            
            # === ACTION 2: Call Gemini AI for personalization ===
            try:
                email_content = self.gemini_client.generate_personalized_email(
                    lead_data={
                        "contact_name": lead.get('contact', lead.get('contact_name', 'there')),
                        "company": lead.get('company', 'your company'),
                        "role": lead.get('role', lead.get('title', '')),
                        "signal": lead.get('signal', ''),
                        "technologies": lead.get('technologies', []),
                        "industry": lead.get('company_industry', lead.get('industry', ''))
                    },
                    value_proposition=value_prop,
                    tone=tone
                )
                
                # === OBSERVATION 1: Review generated content ===
                subject = email_content.get('subject', '')
                body = email_content.get('body', '')
                
                if subject and body:
                    # Calculate personalization score
                    personalization_score = self._assess_personalization_quality(
                        email_content, lead
                    )
                    
                    message = {
                        "lead_id": f"{lead.get('company', 'unknown')}_{idx}",
                        "lead_name": lead.get('contact', lead.get('contact_name', 'Unknown')),
                        "lead_email": lead.get('email', ''),
                        "company": lead.get('company', ''),
                        "lead_score": score,
                        "subject_line": subject,
                        "email_body": body,
                        "personalization_score": personalization_score,
                        "tone": tone,
                        "persona": persona
                    }
                    
                    messages.append(message)
                    successful_generations += 1
                    
                    self._log_observation(
                        f" Generated email {idx}/{len(qualified_leads)} - "
                        f"Personalization: {personalization_score:.2f}, "
                        f"Subject: {subject[:50]}..."
                    )
                else:
                    self.logger.warning(f" Empty content generated for lead {idx}")
                    
            except Exception as e:
                self.logger.error(f" Failed to generate content for lead {idx}: {e}")
                continue
        
        # === FINAL OBSERVATION ===
        success_rate = (successful_generations / len(qualified_leads) * 100) if qualified_leads else 0
        avg_personalization = (
            sum(m['personalization_score'] for m in messages) / len(messages)
            if messages else 0
        )
        
        self._log_observation(
            f"Content generation complete: {successful_generations}/{len(qualified_leads)} "
            f"({success_rate:.1f}% success rate), Avg personalization: {avg_personalization:.2f}"
        )
        
        self.logger.info(f"OutreachContentAgent completed: {len(messages)} emails generated")
        
        return {
            "messages": messages,
            "total_generated": len(messages),
            "successful_generations": successful_generations,
            "failed_generations": len(qualified_leads) - successful_generations,
            "avg_personalization_score": round(avg_personalization, 3),
            "generation_timestamp": datetime.now().isoformat(),
            "generation_config": {
                "persona": persona,
                "tone": tone,
                "value_proposition": value_prop
            }
        }
    
    def _assess_personalization_quality(
        self,
        email_content: Dict[str, str],
        lead: Dict[str, Any]
    ) -> float:
        """Assess how personalized the email is"""
        score = 0.0
        
        subject = email_content.get('subject', '').lower()
        body = email_content.get('body', '').lower()
        
        # Check if contact name is used
        contact_name = lead.get('contact', lead.get('contact_name', '')).split()[0].lower()
        if contact_name and contact_name in body:
            score += 0.3
        
        # Check if company name is mentioned
        company = lead.get('company', '').lower()
        if company and company in (subject + body):
            score += 0.2
        
        # Check if signal is referenced
        signal = lead.get('signal', '').lower().replace('_', ' ')
        if signal and any(word in (subject + body) for word in signal.split()):
            score += 0.2
        
        # Check if industry/tech is mentioned
        industry = lead.get('company_industry', lead.get('industry', '')).lower()
        if industry and industry in body:
            score += 0.15
        
        # Check email length (not too short, not too long)
        body_length = len(email_content.get('body', ''))
        if 100 <= body_length <= 250:
            score += 0.15
        
        return min(score, 1.0)