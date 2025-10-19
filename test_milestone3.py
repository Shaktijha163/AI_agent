#!/usr/bin/env python3
"""
Test script for Milestone 3
Tests ProspectSearchAgent and DataEnrichmentAgent
"""
import json
from utils.logger import get_logger
from utils.config_loader import get_config
from utils.json_validator import validate_workflow_file
from agents.prospect_search_agent import ProspectSearchAgent
from agents.enrichment_agent import DataEnrichmentAgent

logger = get_logger("test_milestone3")

def test_workflow_validation():
    """Test 1: Validate workflow.json"""
    logger.info("=" * 60)
    logger.info("TEST 1: Workflow JSON Validation")
    logger.info("=" * 60)
    
    try:
        workflow = validate_workflow_file("workflow.json")
        logger.info(f"Workflow validated: {workflow.workflow_name}")
        logger.info(f"   Total steps: {len(workflow.steps)}")
        logger.info(f"   Steps: {[step.id for step in workflow.steps]}")
        return True
    except Exception as e:
        logger.error(f" Workflow validation failed: {e}")
        return False

def test_config_loader():
    """Test 2: Config loader"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Configuration Loading")
    logger.info("=" * 60)
    
    try:
        config = get_config()
        
        # Test environment variables
        gemini_key = config.get_env("GEMINI_API_KEY", "NOT_FOUND")
        logger.info(f"Gemini API Key: {gemini_key[:20]}..." if len(gemini_key) > 20 else f"  Gemini API Key: {gemini_key}")
        
        # Test workflow config
        workflow_config = config.get_workflow_config()
        logger.info(f"Mock Mode: {workflow_config.enable_mock_mode}")
        logger.info(f"Max Leads: {workflow_config.max_leads_per_run}")
        
        # Test ICP config
        icp = config.get_icp_config()
        logger.info(f"ICP Industries: {icp.get('industry', [])}")
        
        return True
    except Exception as e:
        logger.error(f" Config loading failed: {e}")
        return False

def test_prospect_search_agent():
    """Test 3: ProspectSearchAgent"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Prospect Search Agent")
    logger.info("=" * 60)
    
    try:
        agent = ProspectSearchAgent(agent_id="test_prospect_search")
        
        # Test input
        input_data = {
            "icp": {
                "industry": ["SaaS", "Technology"],
                "location": ["USA"],
                "employee_count": {"min": 100, "max": 1000},
                "revenue": {"min": 20000000, "max": 200000000}
            },
            "signals": ["recent_funding", "hiring_for_sales"],
            "max_leads": 10
        }
        
        logger.info(" Executing ProspectSearchAgent...")
        output = agent.execute(input_data)
        
        if output.get('_metadata', {}).get('success'):
            logger.info(f"Agent executed successfully!")
            logger.info(f"   Leads found: {output.get('total_found', 0)}")
            logger.info(f"   Companies searched: {output.get('companies_searched', 0)}")
            
            # Show sample lead
            if output.get('leads'):
                sample_lead = output['leads'][0]
                logger.info(f"\n   Sample Lead:")
                logger.info(f"   - Company: {sample_lead.get('company')}")
                logger.info(f"   - Contact: {sample_lead.get('contact_name')}")
                logger.info(f"   - Email: {sample_lead.get('email')}")
                logger.info(f"   - Title: {sample_lead.get('title')}")
            
            return output
        else:
            logger.error(f" Agent execution failed: {output.get('error')}")
            return None
            
    except Exception as e:
        logger.error(f" ProspectSearchAgent test failed: {e}")
        return None

def test_enrichment_agent(leads_data):
    """Test 4: DataEnrichmentAgent"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Data Enrichment Agent")
    logger.info("=" * 60)
    
    if not leads_data or not leads_data.get('leads'):
        logger.warning("  No leads to enrich, skipping test")
        return None
    
    try:
        agent = DataEnrichmentAgent(agent_id="test_enrichment")
        
        # Test input (use leads from previous agent)
        input_data = {
            "leads": leads_data['leads'][:5]  # Enrich first 5 leads
        }
        
        logger.info(f" Executing DataEnrichmentAgent with {len(input_data['leads'])} leads...")
        output = agent.execute(input_data)
        
        if output.get('_metadata', {}).get('success'):
            logger.info(f"Agent executed successfully!")
            logger.info(f"   Total enriched: {output.get('total_enriched', 0)}")
            logger.info(f"   Successful enrichments: {output.get('successful_enrichments', 0)}")
            logger.info(f"   Enrichment rate: {output.get('enrichment_rate', 0):.1%}")
            
            # Show sample enriched lead
            if output.get('enriched_leads'):
                sample = output['enriched_leads'][0]
                logger.info(f"\n   Sample Enriched Lead:")
                logger.info(f"   - Company: {sample.get('company')}")
                logger.info(f"   - Description: {sample.get('company_description', 'N/A')[:80]}...")
                logger.info(f"   - Technologies: {sample.get('technologies', [])[:3]}")
                logger.info(f"   - Enrichment Quality: {sample.get('enrichment_quality')}")
            
            return output
        else:
            logger.error(f" Agent execution failed: {output.get('error')}")
            return None
            
    except Exception as e:
        logger.error(f" DataEnrichmentAgent test failed: {e}")
        return None

def test_agent_stats():
    """Test 5: Agent statistics"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Agent Statistics")
    logger.info("=" * 60)
    
    try:
        agent = ProspectSearchAgent(agent_id="stats_test")
        
        # Execute multiple times
        input_data = {
            "icp": {"industry": ["SaaS"]},
            "max_leads": 5
        }
        
        for i in range(3):
            agent.execute(input_data)
        
        stats = agent.get_stats()
        logger.info(f"Agent Stats:")
        logger.info(f"   - Execution count: {stats['execution_count']}")
        logger.info(f"   - Total time: {stats['total_execution_time']:.2f}s")
        logger.info(f"   - Average time: {stats['average_execution_time']:.2f}s")
        logger.info(f"   - Last execution: {stats['last_execution_time']:.2f}s")
        
        return True
    except Exception as e:
        logger.error(f" Stats test failed: {e}")
        return False

def save_test_results(prospect_output, enrichment_output):
    """Save test results to file"""
    logger.info("\n" + "=" * 60)
    logger.info("Saving Test Results")
    logger.info("=" * 60)
    
    try:
        results = {
            "prospect_search": prospect_output,
            "enrichment": enrichment_output
        }
        
        with open("data/test_results_milestone3.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("Test results saved to data/test_results_milestone3.json")
        return True
    except Exception as e:
        logger.error(f" Failed to save results: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 10 + "MILESTONE 3 TEST SUITE" + " " * 26 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    
    results = []
    
    # Run tests
    results.append(("Workflow Validation", test_workflow_validation()))
    results.append(("Config Loader", test_config_loader()))
    
    prospect_output = test_prospect_search_agent()
    results.append(("Prospect Search Agent", prospect_output is not None))
    
    enrichment_output = test_enrichment_agent(prospect_output)
    results.append(("Enrichment Agent", enrichment_output is not None))
    
    results.append(("Agent Statistics", test_agent_stats()))
    
    # Save results
    if prospect_output and enrichment_output:
        save_test_results(prospect_output, enrichment_output)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else " FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\n Results: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
    
    if passed == total:
        logger.info("\n ALL TESTS PASSED! Milestone 3 complete!")
    else:
        logger.warning("\n  Some tests failed. Review errors above.")

if __name__ == "__main__":
    main()