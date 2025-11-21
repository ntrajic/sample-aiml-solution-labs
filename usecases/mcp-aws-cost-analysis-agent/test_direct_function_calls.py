#!/usr/bin/env python3
"""
Direct Test for Strands Cost Calculator Agent

This script tests the agent directly by importing and calling it,
without requiring MCP server setup or AgentCore deployment.

Usage:
    python test_agent_direct.py
    python test_agent_direct.py --query "Calculate Bedrock costs for 10k questions"
"""

import sys
import json
import argparse
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import the agent and tools
from strands_cost_calc_agent import agent, invoke_strands_agent


def test_agent_query(query: str, verbose: bool = False):
    """
    Test the agent with a specific query
    
    Args:
        query: User query to send to the agent
        verbose: Show detailed output
    """
    print(f"\n{'='*80}")
    print(f"🤖 Testing Agent Query")
    print(f"{'='*80}")
    print(f"Query: {query}")
    print(f"\n⏳ Processing...")
    
    try:
        # Invoke the agent
        response = invoke_strands_agent(agent, query)
        
        # Extract response text
        if hasattr(response, 'message') and 'content' in response.message:
            result_text = response.message['content'][0]['text']
        else:
            result_text = str(response)
        
        print(f"\n✅ Agent Response:")
        print(f"{'='*80}")
        
        # Try to parse as JSON for pretty printing
        try:
            result_data = json.loads(result_text)
            print(json.dumps(result_data, indent=2))
        except json.JSONDecodeError:
            # Not JSON, print as-is
            print(result_text)
        
        print(f"{'='*80}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def run_test_suite(verbose: bool = False):
    """Run a suite of test queries"""
    
    test_queries = [
        {
            "query": "What is the pricing for Claude Haiku in us-west-2?",
            "description": "Simple pricing lookup"
        },
        {
            "query": "Calculate Bedrock costs for 10,000 questions per month using Claude Haiku with 1000 input tokens and 500 output tokens per question",
            "description": "Basic Bedrock cost calculation"
        },
        {
            "query": "I have an AI agent that processes 50,000 questions per month. Each question uses Claude Sonnet with 2000 input tokens and 800 output tokens. I also use a vector database that retrieves 5 chunks of 400 tokens each. Calculate the total monthly cost.",
            "description": "Bedrock with vector database"
        },
        {
            "query": "What are the AgentCore pricing components for us-west-2?",
            "description": "AgentCore pricing lookup"
        },
        {
            "query": "Calculate AgentCore costs for an agent that runs 100 hours per month with 2GB memory and handles 10,000 requests",
            "description": "AgentCore cost calculation"
        },
        {
            "query": "Size an EMR cluster for processing 5TB of data using Spark on EC2 for batch processing",
            "description": "EMR EC2 sizing"
        },
        {
            "query": "What's the ROI if I process 10,000 questions per month, save 10 minutes per question, and my labor cost is $50/hour? The AI agent costs $500/month.",
            "description": "Business value analysis"
        },
        {
            "query": "Compare costs: Claude Haiku vs Claude Sonnet for 20,000 questions with 1500 input and 600 output tokens",
            "description": "Model comparison"
        }
    ]
    
    print(f"\n{'='*80}")
    print(f"🧪 Running Test Suite ({len(test_queries)} tests)")
    print(f"{'='*80}")
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n\n📝 Test {i}/{len(test_queries)}: {test['description']}")
        print(f"{'─'*80}")
        
        success = test_agent_query(test['query'], verbose=verbose)
        
        if success:
            passed += 1
        else:
            failed += 1
        
    # Summary
    print(f"\n\n{'='*80}")
    print(f"📊 Test Suite Summary")
    print(f"{'='*80}")
    print(f"   Total Tests: {passed + failed}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    if passed + failed > 0:
        print(f"   Success Rate: {(passed/(passed+failed)*100):.1f}%")
    print(f"{'='*80}")
    
    return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description='Test Strands Cost Calculator Agent Directly',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full test suite
  python test_agent_direct.py
  
  # Test specific query
  python test_agent_direct.py --query "Calculate Bedrock costs for 10k questions"
  
  # Run with verbose output
  python test_agent_direct.py --verbose
  
  # Interactive mode
  python test_agent_direct.py --interactive
        """
    )
    parser.add_argument('--query', type=str,
                        help='Single query to test')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed output including errors')
    parser.add_argument('--interactive', action='store_true',
                        help='Interactive mode - enter queries manually')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print(f"🚀 Strands Cost Calculator Agent - Direct Test")
    print(f"{'='*80}")
    
    try:
        if args.interactive:
            # Interactive mode
            print("\n💡 Interactive Mode - Enter queries (Ctrl+C to exit)")
            print("   Example: Calculate Bedrock costs for 10k questions\n")
            
            while True:
                try:
                    query = input("\n🤔 Your query: ").strip()
                    if not query:
                        continue
                    
                    test_agent_query(query, verbose=args.verbose)
                    
                except KeyboardInterrupt:
                    print("\n\n👋 Exiting interactive mode")
                    break
        
        elif args.query:
            # Single query mode
            success = test_agent_query(args.query, verbose=args.verbose)
            sys.exit(0 if success else 1)
        
        else:
            # Test suite mode
            success = run_test_suite(verbose=args.verbose)
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
