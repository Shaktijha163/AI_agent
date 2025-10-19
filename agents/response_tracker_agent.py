"""
Response Tracker Agent - Monitor email engagement and responses
"""
from typing import Any, Dict, List
from datetime import datetime
import random
from agents.base_agent import BaseAgent
from tools.apollo_api import ApolloAPI

class ResponseTrackerAgent(BaseAgent):
    """Agent for tracking email responses and engagement"""
    
    def _initialize(self):
        """Initialize Apollo API for tracking"""
        self.apollo = ApolloAPI()
        
        # Get tracking settings
        self.tracking_config = self.config_loader.get_yaml_config('tracking', {})
        self.engagement_window = self.tracking_config.get('engagement_window_days', 14)
        self.hot_lead_criteria = self.tracking_config.get('hot_lead_criteria', {})
        
        self.logger.info("ResponseTrackerAgent initialized")
    
    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input contains campaign ID"""
        if 'campaign_id' not in input_data:
            self.logger.error(" Missing required input key: campaign_id")
            return False
        
        self.logger.info(f" Input validation passed: Campaign {input_data['campaign_id']}")
        return True
    
    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute response tracking workflow
        
        ReAct Pattern:
        1. Thought: Identify tracking window and metrics
        2. Action: Query engagement data
        3. Observation: Analyze engagement patterns
        4. Action: Classify lead temperature
        5. Observation: Generate insights
        """
        campaign_id = input_data['campaign_id']
        sent_status = input_data.get('sent_status', [])
        
        # === THOUGHT 1: Define tracking strategy ===
        self._log_reasoning(
            "Define Tracking",
            f"Tracking campaign {campaign_id} with {len(sent_status)} emails sent"
        )
        
        # === ACTION 1: Track engagement ===
        self._log_action("Track Engagement", {"campaign_id": campaign_id})
        
        # Get tracking data from Apollo
        tracking_data = self.apollo.track_email_activity(campaign_id)
        
        # === OBSERVATION 1: Parse tracking data ===
        responses = []
        hot_leads = []
        warm_leads = []
        cold_leads = []
        
        for status_entry in sent_status:
            if status_entry.get('status') != 'sent':
                continue
            
            lead_email = status_entry.get('email')
            
            # Generate engagement data (mock or real)
            engagement = self._get_engagement_data(lead_email, tracking_data)
            
            response_entry = {
                "lead_id": status_entry.get('lead_id'),
                "lead_name": status_entry.get('lead_name'),
                "email": lead_email,
                "company": status_entry.get('company'),
                "message_id": status_entry.get('message_id'),
                "opened": engagement.get('opened', False),
                "open_count": engagement.get('open_count', 0),
                "clicked": engagement.get('clicked', False),
                "click_count": engagement.get('click_count', 0),
                "replied": engagement.get('replied', False),
                "reply_sentiment": engagement.get('reply_sentiment'),
                "meeting_booked": engagement.get('meeting_booked', False),
                "last_activity": engagement.get('last_activity'),
                "engagement_score": 0.0
            }
            
            # === ACTION 2: Calculate engagement score ===
            engagement_score = self._calculate_engagement_score(response_entry)
            response_entry['engagement_score'] = engagement_score
            
            # === ACTION 3: Classify lead temperature ===
            temperature = self._classify_lead_temperature(response_entry)
            response_entry['lead_temperature'] = temperature
            
            if temperature == 'hot':
                hot_leads.append(response_entry)
            elif temperature == 'warm':
                warm_leads.append(response_entry)
            else:
                cold_leads.append(response_entry)
            
            responses.append(response_entry)
            
            self._log_observation(
                f"Lead: {lead_email} - Opened: {response_entry['opened']}, "
                f"Clicked: {response_entry['clicked']}, Replied: {response_entry['replied']}, "
                f"Temp: {temperature}"
            )
        
        # === OBSERVATION 2: Calculate campaign metrics ===
        total_sent = len([r for r in responses])
        total_opened = len([r for r in responses if r['opened']])
        total_clicked = len([r for r in responses if r['clicked']])
        total_replied = len([r for r in responses if r['replied']])
        total_meetings = len([r for r in responses if r['meeting_booked']])
        
        metrics = {
            "open_rate": round(total_opened / total_sent, 3) if total_sent > 0 else 0,
            "click_rate": round(total_clicked / total_sent, 3) if total_sent > 0 else 0,
            "reply_rate": round(total_replied / total_sent, 3) if total_sent > 0 else 0,
            "meeting_rate": round(total_meetings / total_sent, 3) if total_sent > 0 else 0,
            "total_sent": total_sent,
            "total_opened": total_opened,
            "total_clicked": total_clicked,
            "total_replied": total_replied,
            "total_meetings": total_meetings
        }
        
        # === OBSERVATION 3: Identify insights ===
        self._log_observation(
            f"Campaign metrics - Open: {metrics['open_rate']:.1%}, "
            f"Click: {metrics['click_rate']:.1%}, Reply: {metrics['reply_rate']:.1%}"
        )
        
        self._log_observation(
            f"Lead temperatures - Hot: {len(hot_leads)}, Warm: {len(warm_leads)}, Cold: {len(cold_leads)}"
        )
        
        self.logger.info(f"ResponseTrackerAgent completed: {campaign_id}")
        
        return {
            "campaign_id": campaign_id,
            "responses": responses,
            "metrics": metrics,
            "lead_classification": {
                "hot_leads": hot_leads,
                "warm_leads": warm_leads,
                "cold_leads": cold_leads
            },
            "hot_lead_count": len(hot_leads),
            "warm_lead_count": len(warm_leads),
            "cold_lead_count": len(cold_leads),
            "tracking_timestamp": datetime.now().isoformat(),
            "engagement_window_days": self.engagement_window
        }
    
    def _get_engagement_data(self, email: str, tracking_data: Dict) -> Dict[str, Any]:
        """Get engagement data for a specific email"""
        # In mock mode, generate realistic engagement data
        if self._is_mock_mode():
            return self._generate_mock_engagement()
        
        # Parse real tracking data from Apollo
        # (Implementation would depend on Apollo's actual response format)
        return {}
    
    def _generate_mock_engagement(self) -> Dict[str, Any]:
        """Generate realistic mock engagement data"""
        # 50% open rate
        opened = random.random() < 0.5
        
        # 20% click rate (of those who opened)
        clicked = opened and random.random() < 0.4
        
        # 10% reply rate (of those who clicked)
        replied = clicked and random.random() < 0.25
        
        # 5% meeting booked (of those who replied)
        meeting_booked = replied and random.random() < 0.5
        
        sentiments = ['positive', 'neutral', 'negative']
        
        return {
            "opened": opened,
            "open_count": random.randint(1, 3) if opened else 0,
            "clicked": clicked,
            "click_count": random.randint(1, 2) if clicked else 0,
            "replied": replied,
            "reply_sentiment": random.choice(sentiments) if replied else None,
            "meeting_booked": meeting_booked,
            "last_activity": datetime.now().isoformat() if opened else None
        }
    
    def _calculate_engagement_score(self, response: Dict[str, Any]) -> float:
        """Calculate engagement score (0-1)"""
        score = 0.0
        
        if response['opened']:
            score += 0.2 + (min(response['open_count'], 3) * 0.1)
        
        if response['clicked']:
            score += 0.3 + (min(response['click_count'], 2) * 0.1)
        
        if response['replied']:
            score += 0.4
            if response['reply_sentiment'] == 'positive':
                score += 0.2
        
        if response['meeting_booked']:
            score += 0.5
        
        return min(round(score, 3), 1.0)
    
    def _classify_lead_temperature(self, response: Dict[str, Any]) -> str:
        """Classify lead as hot, warm, or cold"""
        engagement_score = response['engagement_score']
        
        # Hot lead criteria
        if response['meeting_booked']:
            return 'hot'
        
        if response['replied'] and response['reply_sentiment'] == 'positive':
            return 'hot'
        
        if engagement_score >= 0.6:
            return 'hot'
        
        # Warm lead criteria
        if response['clicked']:
            return 'warm'
        
        if response['opened'] and response['open_count'] >= 2:
            return 'warm'
        
        if engagement_score >= 0.3:
            return 'warm'
        
        # Cold lead
        return 'cold'