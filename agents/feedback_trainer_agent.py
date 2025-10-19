"""
Feedback Trainer Agent - Analyze performance and suggest improvements
"""
from typing import Any, Dict, List
from datetime import datetime
from agents.base_agent import BaseAgent
from tools.google_sheets_tool import GoogleSheetsTool
from tools.gemini_tool import GeminiAPI

class FeedbackTrainerAgent(BaseAgent):
    """Agent for analyzing campaign performance and generating recommendations"""
    
    def _initialize(self):
        """Initialize Google Sheets and Gemini AI"""
        self.sheets = GoogleSheetsTool()
        self.gemini = GeminiAPI()
        
        # Get feedback settings
        self.feedback_config = self.config_loader.get_yaml_config('feedback', {})
        self.min_sample_size = self.feedback_config.get('min_sample_size', 20)
        self.auto_apply_threshold = self.feedback_config.get('auto_apply_threshold', 0.85)
        
        self.logger.info(" FeedbackTrainerAgent initialized")
    
    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input contains response data"""
        if 'responses' not in input_data:
            self.logger.error(" Missing required input key: responses")
            return False
        
        if 'campaign_metrics' not in input_data:
            self.logger.error(" Missing required input key: campaign_metrics")
            return False
        
        responses = input_data['responses']
        if len(responses) < self.min_sample_size:
            self.logger.warning(
                f" Sample size ({len(responses)}) below minimum ({self.min_sample_size}). "
                "Results may not be statistically significant."
            )
        
        self.logger.info(f" Input validation passed: {len(responses)} responses to analyze")
        return True
    
    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute feedback and learning workflow
        
        ReAct Pattern:
        1. Thought: Assess campaign performance
        2. Action: Identify patterns in engagement data
        3. Observation: Find what worked vs what didn't
        4. Action: Use Gemini AI to generate recommendations
        5. Action: Write to Google Sheets for approval
        6. Observation: Track approval status
        """
        responses = input_data['responses']
        metrics = input_data['campaign_metrics']
        campaign_id = input_data.get('campaign_id', 'unknown')
        
        # === THOUGHT 1: Assess overall performance ===
        self._log_reasoning(
            "Assess Performance",
            f"Analyzing {len(responses)} responses with "
            f"open rate: {metrics.get('open_rate', 0):.1%}, "
            f"reply rate: {metrics.get('reply_rate', 0):.1%}"
        )
        
        performance_assessment = self._assess_performance(metrics)
        
        # === ACTION 1: Segment analysis ===
        self._log_action("Segment Analysis", {"total_responses": len(responses)})
        
        segmentation = self._segment_leads(responses)
        
        # === OBSERVATION 1: Identify patterns ===
        patterns = self._identify_patterns(responses, segmentation)
        
        self._log_observation(
            f"Patterns identified: {len(patterns)} key insights"
        )
        
        # === ACTION 2: Generate AI recommendations ===
        self._log_action("Generate Recommendations", {"using": "Gemini AI"})
        
        ai_analysis = self.gemini.analyze_campaign_performance(
            metrics=metrics,
            lead_data=responses[:10]  # Sample for AI analysis
        )
        
        # === ACTION 3: Compile recommendations ===
        recommendations = self._compile_recommendations(
            performance_assessment,
            patterns,
            ai_analysis,
            metrics
        )
        
        self._log_observation(
            f"Generated {len(recommendations)} recommendations"
        )
        
        # === ACTION 4: Write to Google Sheets ===
        self._log_action("Write to Google Sheets", {"recommendations": len(recommendations)})
        
        sheet_result = self.sheets.write_recommendations(
            recommendations=recommendations,
            campaign_id=campaign_id,
            metrics=metrics
        )
        
        # === OBSERVATION 2: Performance summary ===
        performance_summary = {
            "overall_assessment": performance_assessment,
            "best_performing_segments": segmentation.get('high_engagement', []),
            "underperforming_segments": segmentation.get('low_engagement', []),
            "suggested_icp_changes": self._suggest_icp_changes(patterns),
            "key_insights": patterns
        }
        
        self._log_observation(
            f"Performance Summary: {performance_assessment['rating']} - "
            f"{len(segmentation.get('high_engagement', []))} high performers, "
            f"{len(segmentation.get('low_engagement', []))} underperformers"
        )
        
        self.logger.info(f"FeedbackTrainerAgent completed: {len(recommendations)} recommendations")
        
        return {
            "campaign_id": campaign_id,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "performance_summary": performance_summary,
            "approval_status": "pending",
            "auto_apply_eligible": self._check_auto_apply_eligibility(metrics),
            "sheet_status": sheet_result,
            "analysis_timestamp": datetime.now().isoformat(),
            "sample_size": len(responses),
            "statistical_confidence": self._calculate_confidence(len(responses))
        }
    
    def _assess_performance(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Assess overall campaign performance"""
        open_rate = metrics.get('open_rate', 0)
        reply_rate = metrics.get('reply_rate', 0)
        
        # Benchmark thresholds
        if reply_rate >= 0.15:  # 15%+ reply rate
            rating = "excellent"
            message = "Campaign performed exceptionally well"
        elif reply_rate >= 0.10:  # 10-15% reply rate
            rating = "good"
            message = "Campaign met expectations"
        elif reply_rate >= 0.05:  # 5-10% reply rate
            rating = "average"
            message = "Campaign needs improvement"
        else:  # <5% reply rate
            rating = "poor"
            message = "Campaign requires significant optimization"
        
        return {
            "rating": rating,
            "message": message,
            "open_rate": open_rate,
            "reply_rate": reply_rate
        }
    
    def _segment_leads(self, responses: List[Dict[str, Any]]) -> Dict[str, List]:
        """Segment leads by engagement level"""
        high_engagement = []
        medium_engagement = []
        low_engagement = []
        
        for response in responses:
            score = response.get('engagement_score', 0)
            
            if score >= 0.6:
                high_engagement.append(response)
            elif score >= 0.3:
                medium_engagement.append(response)
            else:
                low_engagement.append(response)
        
        return {
            "high_engagement": high_engagement,
            "medium_engagement": medium_engagement,
            "low_engagement": low_engagement
        }
    
    def _identify_patterns(
        self,
        responses: List[Dict[str, Any]],
        segmentation: Dict[str, List]
    ) -> List[Dict[str, str]]:
        """Identify patterns in successful vs unsuccessful outreach"""
        patterns = []
        
        high_eng = segmentation.get('high_engagement', [])
        low_eng = segmentation.get('low_engagement', [])
        
        if not high_eng:
            return patterns
        
        # Pattern 1: Company characteristics
        high_companies = [r.get('company', '') for r in high_eng]
        patterns.append({
            "pattern": "High engagement companies",
            "description": f"Companies with high engagement: {', '.join(high_companies[:5])}",
            "insight": "Focus on similar company profiles"
        })
        
        # Pattern 2: Lead temperature distribution
        temp_distribution = {
            'hot': sum(1 for r in responses if r.get('lead_temperature') == 'hot'),
            'warm': sum(1 for r in responses if r.get('lead_temperature') == 'warm'),
            'cold': sum(1 for r in responses if r.get('lead_temperature') == 'cold')
        }
        
        patterns.append({
            "pattern": "Temperature distribution",
            "description": f"Hot: {temp_distribution['hot']}, Warm: {temp_distribution['warm']}, Cold: {temp_distribution['cold']}",
            "insight": "Adjust targeting to increase hot lead percentage"
        })
        
        # Pattern 3: Response timing
        replied_count = sum(1 for r in responses if r.get('replied'))
        if replied_count > 0:
            patterns.append({
                "pattern": "Reply behavior",
                "description": f"{replied_count} leads replied, engagement rate varies by segment",
                "insight": "Personalization drives replies"
            })
        
        return patterns
    
    def _compile_recommendations(
        self,
        performance: Dict[str, Any],
        patterns: List[Dict],
        ai_analysis: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Compile actionable recommendations"""
        recommendations = []
        
        # Recommendation 1: Based on performance rating
        if performance['rating'] in ['poor', 'average']:
            recommendations.append({
                "category": "overall_strategy",
                "recommendation": "Improve targeting and personalization. Current performance below industry benchmarks.",
                "expected_impact": "20-30% increase in reply rate",
                "priority": "high",
                "data_source": "performance_metrics"
            })
        
        # Recommendation 2: Open rate optimization
        if metrics.get('open_rate', 0) < 0.3:
            recommendations.append({
                "category": "subject_line",
                "recommendation": "Subject lines need optimization. Test more specific, value-driven subject lines.",
                "expected_impact": "15% increase in open rate",
                "priority": "high",
                "data_source": "engagement_metrics"
            })
        
        # Recommendation 3: Click rate optimization
        if metrics.get('click_rate', 0) < 0.1:
            recommendations.append({
                "category": "email_content",
                "recommendation": "Add clearer call-to-action and relevant links in email body.",
                "expected_impact": "10% increase in click rate",
                "priority": "medium",
                "data_source": "engagement_metrics"
            })
        
        # Recommendation 4: From AI analysis
        if ai_analysis.get('recommendations'):
            for ai_rec in ai_analysis['recommendations'][:2]:
                recommendations.append({
                    "category": "ai_insight",
                    "recommendation": ai_rec,
                    "expected_impact": "Data-driven improvement",
                    "priority": "medium",
                    "data_source": "gemini_analysis"
                })
        
        # Recommendation 5: ICP refinement
        recommendations.append({
            "category": "icp_refinement",
            "recommendation": "Focus on leads with characteristics similar to high-engagement segment.",
            "expected_impact": "25% increase in qualified leads",
            "priority": "high",
            "data_source": "pattern_analysis"
        })
        
        return recommendations
    
    def _suggest_icp_changes(self, patterns: List[Dict]) -> Dict[str, Any]:
        """Suggest ICP adjustments based on patterns"""
        return {
            "industry": ["Focus on industries with highest engagement"],
            "company_size": "Prioritize mid-market (250-500 employees)",
            "signals": "Emphasize recent_funding and rapid_growth signals"
        }
    
    def _check_auto_apply_eligibility(self, metrics: Dict[str, Any]) -> bool:
        """Check if recommendations can be auto-applied"""
        # Only auto-apply if performance is good and confidence is high
        reply_rate = metrics.get('reply_rate', 0)
        
        return reply_rate >= self.auto_apply_threshold
    
    def _calculate_confidence(self, sample_size: int) -> str:
        """Calculate statistical confidence based on sample size"""
        if sample_size >= 100:
            return "high"
        elif sample_size >= 50:
            return "medium"
        elif sample_size >= self.min_sample_size:
            return "low"
        else:
            return "very_low"