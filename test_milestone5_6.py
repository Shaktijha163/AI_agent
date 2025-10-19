#!/usr/bin/env python3
"""
Test script for Milestones 5 & 6
Tests complete end-to-end workflow: Search → Enrich → Score → Content → Send → Track → Feedback
"""
import json
from utils.logger import get_logger
from agents.prospect_search_agent import ProspectSearchAgent
from agents.enrichment_agent import DataEnrichmentAgent
from agents.scoring_agent import ScoringAgent
from agents.outreach_content_agent import OutreachContentAgent
from agents.outreach_executor_agent import OutreachExecutorAgent
from agents.response_tracker_agent import ResponseTrackerAgent
from agents.feedback_trainer_agent import FeedbackTrainerAgent

logger = get_logger("test_milestone5_6")

def test_complete_workflow():
    """Test complete end-to-end workflow"""
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 5 + "COMPLETE WORKFLOW TEST (Milestones 1-6)" + " " * 13 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    
    workflow_results = {}
    
    # ========== STEP 1: PROSPECT SEARCH ==========
    logger.info("\n" + "=" * 60)
    logger.info("STEP 1: Prospect Search")
    logger.info("=" * 60)
    
    search_agent = ProspectSearchAgent(agent_id="workflow_search")
    search_input = {
        "icp": {
            "industry": ["SaaS", "Technology"],
            "location": ["USA"],
            "employee_count": {"min": 100, "max": 1000}
        },
        "signals": ["recent_funding", "hiring_for_sales"],
        "max_leads": 15
    }
    
    search_output = search_agent.execute(search_input)
    workflow_results['search'] = search_output
    
    if not search_output.get('_metadata', {}).get('success'):
        logger.error("❌ Workflow failed at Search step")
        return False
    
    logger.info(f"✅ Found {search_output.get('total_found', 0)} leads")
    
    # ========== STEP 2: ENRICHMENT ==========
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Data Enrichment")
    logger.info("=" * 60)
    
    enrichment_agent = DataEnrichmentAgent(agent_id="workflow_enrichment")
    enrichment_input = {"leads": search_output['leads'][:8]}
    
    enrichment_output = enrichment_agent.execute(enrichment_input)
    workflow_results['enrichment'] = enrichment_output
    
    if not enrichment_output.get('_metadata', {}).get('success'):
        logger.error("❌ Workflow failed at Enrichment step")
        return False
    
    logger.info(f"✅ Enriched {enrichment_output.get('total_enriched', 0)} leads")
    
    # ========== STEP 3: SCORING ==========
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Lead Scoring")
    logger.info("=" * 60)
    
    scoring_agent = ScoringAgent(agent_id="workflow_scoring")
    scoring_input = {"enriched_leads": enrichment_output['enriched_leads']}
    
    scoring_output = scoring_agent.execute(scoring_input)
    workflow_results['scoring'] = scoring_output
    
    if not scoring_output.get('_metadata', {}).get('success'):
        logger.error("❌ Workflow failed at Scoring step")
        return False
    
    logger.info(f"✅ Scored {scoring_output.get('total_scored', 0)} leads")
    logger.info(f"   Qualified: {scoring_output.get('qualified_leads', 0)}, Avg Score: {scoring_output.get('avg_score', 0):.2f}")
    
    # ========== STEP 4: CONTENT GENERATION ==========
    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: Outreach Content Generation")
    logger.info("=" * 60)
    
    content_agent = OutreachContentAgent(agent_id="workflow_content")
    content_input = {
        "ranked_leads": scoring_output['ranked_leads'],
        "persona": "SDR",
        "tone": "friendly_professional",
        "value_proposition": "AI-powered workflow automation that saves 20+ hours per week",
        "max_messages": 5
    }
    
    content_output = content_agent.execute(content_input)
    workflow_results['content'] = content_output
    
    if not content_output.get('_metadata', {}).get('success'):
        logger.error("❌ Workflow failed at Content Generation step")
        return False
    
    logger.info(f"✅ Generated {content_output.get('total_generated', 0)} emails")
    
    # ========== STEP 5: EMAIL EXECUTION ==========
    logger.info("\n" + "=" * 60)
    logger.info("STEP 5: Email Execution")
    logger.info("=" * 60)
    
    executor_agent = OutreachExecutorAgent(agent_id="workflow_executor")
    executor_input = {
        "messages": content_output['messages'],
        "dry_run": False  # Set to False to test actual sending (mock mode)
    }
    
    executor_output = executor_agent.execute(executor_input)
    workflow_results['execution'] = executor_output
    
    if not executor_output.get('_metadata', {}).get('success'):
        logger.error("❌ Workflow failed at Execution step")
        return False
    
    campaign_id = executor_output.get('campaign_id')
    logger.info(f"✅ Sent {executor_output.get('total_sent', 0)} emails")
    logger.info(f"   Campaign ID: {campaign_id}")
    logger.info(f"   Success Rate: {executor_output.get('success_rate', 0):.1%}")
    
    # ========== STEP 6: RESPONSE TRACKING ==========
    logger.info("\n" + "=" * 60)
    logger.info("STEP 6: Response Tracking")
    logger.info("=" * 60)
    
    tracker_agent = ResponseTrackerAgent(agent_id="workflow_tracker")
    tracker_input = {
        "campaign_id": campaign_id,
        "sent_status": executor_output['sent_status']
    }
    
    tracker_output = tracker_agent.execute(tracker_input)
    workflow_results['tracking'] = tracker_output
    
    if not tracker_output.get('_metadata', {}).get('success'):
        logger.error("❌ Workflow failed at Tracking step")
        return False
    
    metrics = tracker_output.get('metrics', {})
    logger.info(f"✅ Tracked {len(tracker_output.get('responses', []))} responses")
    logger.info(f"   Open Rate: {metrics.get('open_rate', 0):.1%}")
    logger.info(f"   Click Rate: {metrics.get('click_rate', 0):.1%}")
    logger.info(f"   Reply Rate: {metrics.get('reply_rate', 0):.1%}")
    logger.info(f"   Hot Leads: {tracker_output.get('hot_lead_count', 0)}")
    
    # ========== STEP 7: FEEDBACK & LEARNING ==========
    logger.info("\n" + "=" * 60)
    logger.info("STEP 7: Feedback & Learning")
    logger.info("=" * 60)
    
    feedback_agent = FeedbackTrainerAgent(agent_id="workflow_feedback")
    feedback_input = {
        "campaign_id": campaign_id,
        "responses": tracker_output['responses'],
        "campaign_metrics": metrics
    }
    
    feedback_output = feedback_agent.execute(feedback_input)
    workflow_results['feedback'] = feedback_output
    
    if not feedback_output.get('_metadata', {}).get('success'):
        logger.error("❌ Workflow failed at Feedback step")
        return False
    
    logger.info(f"✅ Generated {feedback_output.get('total_recommendations', 0)} recommendations")
    logger.info(f"   Performance: {feedback_output.get('performance_summary', {}).get('overall_assessment', {}).get('rating', 'unknown')}")
    logger.info(f"   Confidence: {feedback_output.get('statistical_confidence', 'unknown')}")
    
    # Show sample recommendation
    if feedback_output.get('recommendations'):
        sample_rec = feedback_output['recommendations'][0]
        logger.info(f"\n   📋 Sample Recommendation:")
        logger.info(f"   - Category: {sample_rec.get('category')}")
        logger.info(f"   - Recommendation: {sample_rec.get('recommendation')}")
        logger.info(f"   - Priority: {sample_rec.get('priority')}")
    
    # ========== SAVE RESULTS ==========
    logger.info("\n" + "=" * 60)
    logger.info("Saving Complete Workflow Results")
    logger.info("=" * 60)
    
    try:
        with open("data/complete_workflow_results.json", "w") as f:
            json.dump(workflow_results, f, indent=2, default=str)
        logger.info("✅ Results saved to data/complete_workflow_results.json")
    except Exception as e:
        logger.error(f"❌ Failed to save results: {e}")
    
    return True

def test_executor_agent_only():
    """Test OutreachExecutorAgent standalone"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Outreach Executor Agent (Standalone)")
    logger.info("=" * 60)
    
    agent = OutreachExecutorAgent(agent_id="test_executor")
    
    mock_messages = [
        {
            "lead_id": "test_1",
            "lead_name": "John Doe",
            "lead_email": "john.doe@example.com",
            "company": "TechCorp",
            "subject_line": "Quick question about TechCorp's workflow",
            "email_body": "Hi John, I noticed TechCorp's recent growth..."
        },
        {
            "lead_id": "test_2",
            "lead_name": "Jane Smith",
            "lead_email": "jane.smith@example.com",
            "company": "StartupCo",
            "subject_line": "Thoughts on automating your sales process?",
            "email_body": "Hi Jane, Given StartupCo's expansion..."
        }
    ]
    
    input_data = {"messages": mock_messages}
    output = agent.execute(input_data)
    
    if output.get('_metadata', {}).get('success'):
        logger.info("✅ Executor agent test passed!")
        logger.info(f"   Campaign ID: {output.get('campaign_id')}")
        logger.info(f"   Total Sent: {output.get('total_sent')}")
        logger.info(f"   Success Rate: {output.get('success_rate', 0):.1%}")
        return output
    else:
        logger.error("❌ Executor agent test failed!")
        return None

def test_tracker_agent_only():
    """Test ResponseTrackerAgent standalone"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Response Tracker Agent (Standalone)")
    logger.info("=" * 60)
    
    agent = ResponseTrackerAgent(agent_id="test_tracker")
    
    mock_sent_status = [
        {
            "lead_id": "test_1",
            "lead_name": "John Doe",
            "email": "john.doe@example.com",
            "company": "TechCorp",
            "status": "sent",
            "message_id": "msg_123"
        },
        {
            "lead_id": "test_2",
            "lead_name": "Jane Smith",
            "email": "jane.smith@example.com",
            "company": "StartupCo",
            "status": "sent",
            "message_id": "msg_456"
        }
    ]
    
    input_data = {
        "campaign_id": "test_campaign_123",
        "sent_status": mock_sent_status
    }
    
    output = agent.execute(input_data)
    
    if output.get('_metadata', {}).get('success'):
        logger.info("✅ Tracker agent test passed!")
        metrics = output.get('metrics', {})
        logger.info(f"   Open Rate: {metrics.get('open_rate', 0):.1%}")
        logger.info(f"   Reply Rate: {metrics.get('reply_rate', 0):.1%}")
        logger.info(f"   Hot Leads: {output.get('hot_lead_count', 0)}")
        return output
    else:
        logger.error("❌ Tracker agent test failed!")
        return None

def test_feedback_agent_only():
    """Test FeedbackTrainerAgent standalone"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Feedback Trainer Agent (Standalone)")
    logger.info("=" * 60)
    
    agent = FeedbackTrainerAgent(agent_id="test_feedback")
    
    # Generate mock responses with varied engagement
    mock_responses = [
        {
            "lead_id": f"lead_{i}",
            "email": f"user{i}@example.com",
            "company": f"Company{i}",
            "opened": True if i % 2 == 0 else False,
            "clicked": True if i % 3 == 0 else False,
            "replied": True if i % 5 == 0 else False,
            "engagement_score": 0.7 if i % 2 == 0 else 0.3,
            "lead_temperature": "hot" if i % 5 == 0 else "warm" if i % 3 == 0 else "cold"
        }
        for i in range(1, 21)
    ]
    
    mock_metrics = {
        "open_rate": 0.50,
        "click_rate": 0.20,
        "reply_rate": 0.10,
        "total_sent": 20
    }
    
    input_data = {
        "campaign_id": "test_campaign_feedback",
        "responses": mock_responses,
        "campaign_metrics": mock_metrics
    }
    
    output = agent.execute(input_data)
    
    if output.get('_metadata', {}).get('success'):
        logger.info("✅ Feedback agent test passed!")
        logger.info(f"   Recommendations: {output.get('total_recommendations', 0)}")
        logger.info(f"   Performance: {output.get('performance_summary', {}).get('overall_assessment', {}).get('rating', 'unknown')}")
        
        if output.get('recommendations'):
            logger.info("\n   Sample Recommendations:")
            for i, rec in enumerate(output['recommendations'][:3], 1):
                logger.info(f"   {i}. [{rec['priority'].upper()}] {rec['recommendation'][:80]}...")
        
        return output
    else:
        logger.error("❌ Feedback agent test failed!")
        return None

def main():
    """Run all Milestone 5 & 6 tests"""
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 7 + "MILESTONES 5 & 6 TEST SUITE" + " " * 23 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    
    results = []
    
    # Test individual agents
    executor_result = test_executor_agent_only()
    results.append(("Executor Agent", executor_result is not None))
    
    tracker_result = test_tracker_agent_only()
    results.append(("Tracker Agent", tracker_result is not None))
    
    feedback_result = test_feedback_agent_only()
    results.append(("Feedback Agent", feedback_result is not None))
    
    # Test complete workflow
    results.append(("Complete Workflow", test_complete_workflow()))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\n🎯 Results: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED! Milestones 5 & 6 complete!")
        logger.info("\n📋 What you've built:")
        logger.info("   ✓ Complete lead generation pipeline")
        logger.info("   ✓ AI-powered email personalization")
        logger.info("   ✓ Email execution with tracking")
        logger.info("   ✓ Engagement monitoring & lead classification")
        logger.info("   ✓ AI-powered feedback & recommendations")
        logger.info("   ✓ Human-in-the-loop approval system")
        logger.info("\n📂 Results saved in:")
        logger.info("   - data/complete_workflow_results.json")
        logger.info("   - logs/test_milestone5_6_*.log")
        logger.info("\n🚀 Ready for Milestone 7: LangGraph Orchestration!")
    else:
        logger.warning("\n⚠️  Some tests failed. Review errors above.")

if __name__ == "__main__":
    main()