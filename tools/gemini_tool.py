"""
Gemini API Tool - AI-powered content generation
"""
import google.generativeai as genai
from typing import Any, Dict, List, Optional
from utils.logger import get_logger
from utils.config_loader import get_config

logger = get_logger("gemini_api")

class GeminiAPI:
    """Google Gemini API wrapper for AI content generation"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or get_config().get_env("GEMINI_API_KEY", "")
        self.model_name = model or get_config().get_env("GEMINI_MODEL", "gemini-2.5-flash")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required and not found")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f" Gemini API initialized with model: {self.model_name}")
    
    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate content using Gemini
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            generated_text = response.text
            logger.info(f" Generated {len(generated_text)} characters")
            return generated_text
            
        except Exception as e:
            logger.error(f"Gemini content generation failed: {e}")
            return ""
    
    def generate_personalized_email(
        self,
        lead_data: Dict[str, Any],
        value_proposition: str,
        tone: str = "friendly_professional"
    ) -> Dict[str, str]:
        """
        Generate personalized outreach email
        
        Args:
            lead_data: Lead information (name, company, role, etc.)
            value_proposition: Product/service value prop
            tone: Email tone
            
        Returns:
            Dict with subject and body
        """
        contact_name = lead_data.get("contact_name", "there")
        company_name = lead_data.get("company", "your company")
        role = lead_data.get("role", "")
        signal = lead_data.get("signal", "")
        
        prompt = f"""
You are an expert SDR writing a personalized outreach email.

CONTEXT:
- Contact Name: {contact_name}
- Company: {company_name}
- Role: {role}
- Growth Signal: {signal}
- Value Proposition: {value_proposition}
- Tone: {tone}

INSTRUCTIONS:
1. Write a compelling subject line (max 60 characters)
2. Write a personalized email body (max 150 words)
3. Reference their growth signal naturally
4. Clearly state the value proposition
5. Include a soft call-to-action
6. Keep it conversational and authentic

FORMAT YOUR RESPONSE EXACTLY AS:
SUBJECT: [your subject line here]

BODY:
[your email body here]

Do not include any other text or formatting.
"""
        
        try:
            response = self.generate_content(prompt, temperature=0.8)
            
            # Parse response
            parts = response.split("BODY:")
            if len(parts) == 2:
                subject_part = parts[0].replace("SUBJECT:", "").strip()
                body_part = parts[1].strip()
                
                return {
                    "subject": subject_part,
                    "body": body_part
                }
            else:
                logger.warning("Failed to parse Gemini response, using fallback")
                return self._fallback_email(contact_name, company_name, value_proposition)
                
        except Exception as e:
            logger.error(f"Email generation failed: {e}")
            return self._fallback_email(contact_name, company_name, value_proposition)
    
    def analyze_campaign_performance(
        self,
        metrics: Dict[str, Any],
        lead_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze campaign performance and suggest improvements
        
        Args:
            metrics: Campaign metrics (open rate, reply rate, etc.)
            lead_data: List of leads with engagement data
            
        Returns:
            Analysis and recommendations
        """
        prompt = f"""
You are a campaign optimization expert analyzing outbound email performance.

METRICS:
- Open Rate: {metrics.get('open_rate', 0):.1%}
- Click Rate: {metrics.get('click_rate', 0):.1%}
- Reply Rate: {metrics.get('reply_rate', 0):.1%}
- Total Sent: {metrics.get('total_sent', 0)}

LEAD DATA SAMPLE:
{lead_data[:5]}

TASK:
Analyze the campaign performance and provide:
1. Overall performance assessment (Good/Average/Poor)
2. 3 specific recommendations to improve metrics
3. Suggested ICP adjustments based on who engaged
4. Subject line and messaging improvements

FORMAT AS JSON:
{{
  "assessment": "...",
  "recommendations": ["rec1", "rec2", "rec3"],
  "icp_adjustments": {{"industry": [], "size": ""}},
  "messaging_improvements": ["imp1", "imp2"]
}}
"""
        
        try:
            response = self.generate_content(prompt, temperature=0.5)
            
            # Try to parse as JSON (Gemini sometimes returns valid JSON)
            import json
            try:
                return json.loads(response)
            except:
                # Fallback: extract key insights
                return {
                    "assessment": "Needs improvement",
                    "recommendations": self._extract_recommendations(response),
                    "raw_analysis": response
                }
                
        except Exception as e:
            logger.error(f"Campaign analysis failed: {e}")
            return {
                "assessment": "Unable to analyze",
                "error": str(e)
            }
    
    def _fallback_email(
        self,
        contact_name: str,
        company_name: str,
        value_prop: str
    ) -> Dict[str, str]:
        """Fallback email template"""
        return {
            "subject": f"Quick question about {company_name}'s workflow",
            "body": f"""Hi {contact_name},

I noticed {company_name}'s recent growth and thought you might be interested in {value_prop}.

Would you be open to a quick 15-minute chat next week to explore if this could help your team?

Best,
[Your Name]"""
        }
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from unstructured text"""
        lines = text.split('\n')
        recommendations = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider']):
                recommendations.append(line.strip())
        
        return recommendations[:3] if recommendations else ["Improve subject lines", "Refine targeting", "Test new messaging"]