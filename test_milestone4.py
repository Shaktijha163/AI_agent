#!/usr/bin/env python3
"""
Test script for Milestone 4
Tests full pipeline: Search → Enrich → Score → Generate Content
"""
import json
from utils.logger import get_logger
from agents.prospect_search_agent import ProspectSearchAgent
from agents.enrichment_agent import DataEnrichmentAgent
from agents.scoring_agent import ScoringAgent
from agents.outreach_content_agent import OutreachContentAgent

logger = get_logger("test_milestone4")

def test_full_pipeline():
    """Test complete workflow through content generation"""
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 10 + "MILESTONE 4 FULL PIPELINE TEST" + " " * 18 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    
    # Step 1: Prospect Search
    logger.info("\n" + "=" * 60)
    logger.info("STEP 1: Prospect Search")
    logger.info("=" * 60)
    
    search_agent = ProspectSearchAgent(agent_id="pipeline_search")
    search_input = {
        "icp": {
            "industry": ["SaaS", "Technology"],
            "location": ["USA"],
            "employee_count": {"min": 100, "max": 1000},
            "revenue": {"min": 20000000, "max": 200000000}
        },
        "signals": ["recent_funding", "hiring_for_sales"],
        "max_leads": 10
    }
    
    search_output = search_agent.execute(search_input)
    
    if not search_output.get('_metadata', {}).get('success'):
        logger.error(" Search agent failed!")
        return False
    
    logger.info(f" Found {search_output.get('total_found', 0)} leads")
    
    # Step 2: Enrichment
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Data Enrichment")
    logger.info("=" * 60)
    
    enrichment_agent = DataEnrichmentAgent(agent_id="pipeline_enrichment")
    enrichment_input = {
        "leads": search_output['leads'][:5]  # Enrich top 5
    }
    
    enrichment_output = enrichment_agent.execute(enrichment_input)
    
    if not enrichment_output.get('_metadata', {}).get('success'):
        logger.error(" Enrichment agent failed!")
        return False
    
    logger.info(f" Enriched {enrichment_output.get('total_enriched', 0)} leads")
    
    # Step 3: Scoring
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Lead Scoring")
    logger.info("=" * 60)
    
    scoring_agent = ScoringAgent(agent_id="pipeline_scoring")
    scoring_input = {
        "enriched_leads": enrichment_output['enriched_leads']
    }
    
    scoring_output = scoring_agent.execute(scoring_input)
    
    if not scoring_output.get('_metadata', {}).get('success'):
        logger.error("Scoring agent failed!")
        return False
    
    logger.info(f" Scored {scoring_output.get('total_scored', 0)} leads")
    logger.info(f"   Avg Score: {scoring_output.get('avg_score', 0):.2f}")
    logger.info(f"   Qualified: {scoring_output.get('qualified_leads', 0)}")
    
    # Show top 3 scored leads
    logger.info("\n   Top 3 Leads:")
    for lead in scoring_output['ranked_leads'][:3]:
        logger.info(f"   {lead['rank']}. {lead['lead'].get('company')} - Score: {lead['score']:.2f}")
    
    # Step 4: Content Generation
    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: Outreach Content Generation")
    logger.info("=" * 60)
    
    content_agent = OutreachContentAgent(agent_id="pipeline_content")
    content_input = {
        "ranked_leads": scoring_output['ranked_leads'],
        "persona": "SDR",
        "tone": "friendly_professional",
        "value_proposition": "AI-powered workflow automation that saves 20+ hours per week",
        "max_messages": 3  # Generate only 3 for testing
    }
    
    content_output = content_agent.execute(content_input)
    
    if not content_output.get('_metadata', {}).get('success'):
        logger.error(" Content generation failed!")
        return False
    
    logger.info(f" Generated {content_output.get('total_generated', 0)} emails")
    logger.info(f"   Avg Personalization: {content_output.get('avg_personalization_score', 0):.2f}")
    
    # Show sample email
    if content_output.get('messages'):
        sample = content_output['messages'][0]
        logger.info("\n   📧 Sample Email:")
        logger.info(f"   To: {sample.get('lead_name')} ({sample.get('company')})")
        logger.info(f"   Subject: {sample.get('subject_line')}")
        logger.info(f"\n   Body:\n   {sample.get('email_body')[:200]}...")
        logger.info(f"\n   Personalization Score: {sample.get('personalization_score', 0):.2f}")
    
    # Save complete pipeline results
    logger.info("\n" + "=" * 60)
    logger.info("Saving Pipeline Results")
    logger.info("=" * 60)
    
    pipeline_results = {
        "search": search_output,
        "enrichment": enrichment_output,
        "scoring": scoring_output,
        "content": content_output
    }
    
    try:
        with open("data/test_results_milestone4.json", "w") as f:
            json.dump(pipeline_results, f, indent=2, default=str)
        logger.info("Results saved to data/test_results_milestone4.json")
    except Exception as e:
        logger.error(f" Failed to save results: {e}")
    
    return True

def test_scoring_agent_only():
    """Test scoring agent with mock data"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Scoring Agent (Standalone)")
    logger.info("=" * 60)
    
    agent = ScoringAgent(agent_id="test_scoring")
    
    # Mock enriched leads
    mock_leads = [
        {
            "company": "TechCorp A",
            "contact": "John Doe",
            "email": "john@techcorpa.com",
            "company_industry": "SaaS",
            "company_location": "San Francisco, USA",
            "company_employees": 500,
            "signal": "recent_funding",
            "technologies": ["Python", "React", "AWS"],
            "enrichment_quality": "high",
            "linkedin": "https://linkedin.com/in/johndoe",
            "phone": "+1-555-1234"
        },
        {
            "company": "StartupB",
            "contact": "Jane Smith",
            "email": "jane@startupb.com",
            "company_industry": "FinTech",
            "company_location": "New York, USA",
            "company_employees": 150,
            "signal": "hiring_for_sales",
            "technologies": ["Node.js", "MongoDB"],
            "enrichment_quality": "medium",
            "linkedin": "https://linkedin.com/in/janesmith"
        }
    ]
    
    input_data = {"enriched_leads": mock_leads}
    output = agent.execute(input_data)
    
    if output.get('_metadata', {}).get('success'):
        logger.info(" Scoring agent test passed!")
        logger.info(f"   Scored: {output.get('total_scored')} leads")
        logger.info(f"   Avg Score: {output.get('avg_score'):.2f}")
        
        for lead in output['ranked_leads']:
            logger.info(f"\n   {lead['rank']}. {lead['lead']['company']}")
            logger.info(f"      Score: {lead['score']:.2f}")
            logger.info(f"      Breakdown: ICP={lead['score_breakdown']['icp_fit']:.2f}, "
                       f"Growth={lead['score_breakdown']['growth_signals']:.2f}, "
                       f"Engagement={lead['score_breakdown']['engagement_potential']:.2f}")
        return True
    else:
        logger.error(" Scoring agent test failed!")
        return False

def test_content_agent_only():
    """Test content generation with mock data"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Content Agent (Standalone)")
    logger.info("=" * 60)
    
    agent = OutreachContentAgent(agent_id="test_content")
    
    # Mock ranked leads
    mock_ranked = [
        {
            "rank": 1,
            "score": 0.85,
            "meets_threshold": True,
            "lead": {
                "company": "TechCorp Inc",
                "contact": "John Doe",
                "contact_name": "John Doe",
                "email": "john.doe@techcorp.com",
                "title": "VP of Sales",
                "company_industry": "SaaS",
                "signal": "recent_funding",
                "technologies": ["Python", "React"]
            }
        }
    ]
    
    input_data = {
        "ranked_leads": mock_ranked,
        "persona": "SDR",
        "tone": "friendly_professional",
        "value_proposition": "AI-powered workflow automation",
        "max_messages": 1
    }
    
    output = agent.execute(input_data)
    
    if output.get('_metadata', {}).get('success'):
        logger.info(" Content agent test passed!")
        logger.info(f"   Generated: {output.get('total_generated')} emails")
        
        if output.get('messages'):
            msg = output['messages'][0]
            logger.info(f"\n    Generated Email:")
            logger.info(f"   Subject: {msg.get('subject_line')}")
            logger.info(f"   Body:\n{msg.get('email_body')}")
            logger.info(f"   Personalization: {msg.get('personalization_score', 0):.2f}")
        return True
    else:
        logger.error(" Content agent test failed!")
        return False

def main():
    """Run all Milestone 4 tests"""
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 10 + "MILESTONE 4 TEST SUITE" + " " * 26 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    
    results = []
    
    # Test individual agents first
    results.append(("Scoring Agent", test_scoring_agent_only()))
    results.append(("Content Agent", test_content_agent_only()))
    
    # Test full pipeline
    results.append(("Full Pipeline", test_full_pipeline()))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = " PASSED" if result else " FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\n Results: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
    
    if passed == total:
        logger.info("\n ALL TESTS PASSED! Milestone 4 complete!")
        logger.info("\n Next Steps:")
        logger.info("   1. Review generated emails in data/test_results_milestone4.json")
        logger.info("   2. Ready for Milestone 5: Email Execution & Tracking")
    else:
        logger.warning("\n Some tests failed. Review errors above.")

if __name__ == "__main__":
    main()