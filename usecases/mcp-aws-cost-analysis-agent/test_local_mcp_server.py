#!/usr/bin/env python3
"""
Local MCP Server Test Client for Strands Cost Calculator Agent

This script tests a locally running MCP server (assumes server is already running).
It connects to the server and runs test queries against the agent.

Prerequisites:
    1. Start the MCP server first:
       python strands_cost_calc_agent.py
    
    2. Then run this test script:
       python test_local_mcp_server.py

Usage:
    python test_local_mcp_server.py
    python test_local_mcp_server.py --port 8080
    python test_local_mcp_server.py --query "Calculate Bedrock costs"
    python test_local_mcp_server.py --verbose
"""

import asyncio
import json
import sys
import argparse
from datetime import timedelta

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def test_mcp_server(mcp_url: str, verbose: bool = False):
    """
    Test the local MCP server with various queries.
    
    Args:
        mcp_url: URL of the local MCP server
        verbose: Show detailed output
    """
    headers = {"Content-Type": "application/json"}
    
    print(f"\n{'='*80}")
    print(f"🔗 Connecting to Local MCP Server")
    print(f"{'='*80}")
    print(f"URL: {mcp_url}")
    print(f"\n💡 Make sure the server is running:")
    print(f"   python strands_cost_calc_agent.py")
    
    try:
        print(f"\n🔄 Establishing connection...")
        async with streamablehttp_client(
            mcp_url,
            headers,
            timeout=timedelta(seconds=30)
        ) as (read_stream, write_stream, _):
            print("✓ HTTP connection established")
            
            async with ClientSession(read_stream, write_stream) as session:
                print("✓ MCP session created")
                
                print("🔄 Initializing MCP session...")
                await session.initialize()
                print("✓ MCP session initialized")
                
                # List available tools
                print("\n🔄 Discovering available tools...")
                tool_result = await session.list_tools()
                
                print("\n" + "="*80)
                print("📋 Available MCP Tools")
                print("="*80)
                for tool in tool_result.tools:
                    print(f"\n🔧 {tool.name}")
                    print(f"   {tool.description[:100]}...")
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        properties = tool.inputSchema.get('properties', {})
                        if properties:
                            print(f"   Parameters: {', '.join(properties.keys())}")
                
                print("\n" + "="*80)
                print(f"✅ Found {len(tool_result.tools)} tools available")
                print("="*80)
                
                # Run test queries
                await run_test_queries(session, verbose)
                
    except ConnectionRefusedError:
        print(f"\n❌ Connection refused!")
        print(f"\n💡 The server is not running. Start it first:")
        print(f"   python strands_cost_calc_agent.py")
        print(f"\n   Then run this test script again.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error connecting to MCP server: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        if "Connection refused" in str(e):
            print("\n💡 Connection refused:")
            print("   - Server is not running on the specified port")
            print("   - Start server: python strands_cost_calc_agent.py")
        elif "timeout" in str(e).lower():
            print("\n💡 Timeout:")
            print("   - Server may be overloaded or not responding")
            print("   - Check server logs for errors")
        
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()
        sys.exit(1)


async def run_test_queries(session, verbose: bool = False):
    """Run comprehensive test queries against the agent"""
    
    test_queries = [
        {
            "query": "What is the pricing for Claude Haiku in us-west-2?",
            "description": "Simple pricing lookup",
            "category": "Pricing Query"
        },
        {
            "query": "Calculate Bedrock costs for 10,000 questions per month using Claude Haiku with 1000 input tokens and 500 output tokens per question",
            "description": "Basic Bedrock cost calculation",
            "category": "Bedrock Costs"
        },
        {
            "query": "I have an AI agent that processes 50,000 questions per month. Each question uses Claude Sonnet with 2000 input tokens and 800 output tokens. I also use a vector database that retrieves 5 chunks of 400 tokens each. Calculate the total monthly cost.",
            "description": "Bedrock with vector database",
            "category": "Bedrock Costs"
        },
        {
            "query": "Calculate costs for an agentic workflow: 30,000 questions/month, Claude Haiku, 10 tools available, agent uses 3 tools per question, 80% of questions invoke tools, 50 tokens per tool description, 75 tokens per tool output",
            "description": "Agentic workflow with tools",
            "category": "Bedrock Costs"
        },
        {
            "query": "What are the AgentCore pricing components for us-west-2?",
            "description": "AgentCore pricing lookup",
            "category": "AgentCore Pricing"
        },
        {
            "query": "Calculate AgentCore costs for an agent that runs 100 hours per month with 2GB memory, handles 10,000 requests, uses browser tool 500 times, code interpreter 200 times, and stores 1000 memory records",
            "description": "Complete AgentCore cost calculation",
            "category": "AgentCore Costs"
        },
        {
            "query": "Size an EMR cluster for processing 5TB of data using Spark on EC2 for batch processing",
            "description": "EMR EC2 cluster sizing",
            "category": "EMR Sizing"
        },
        {
            "query": "Calculate EMR Serverless costs for a streaming job with 20 workers, 4 vCPUs and 16GB per worker",
            "description": "EMR Serverless sizing",
            "category": "EMR Sizing"
        },
        {
            "query": "Size an EMR on EKS cluster for 10TB data processing with Trino, 20 workers, 8 cores and 32GB per worker",
            "description": "EMR on EKS sizing",
            "category": "EMR Sizing"
        },
        {
            "query": "What's the ROI if I process 10,000 questions per month, save 10 minutes per question, and my labor cost is $50/hour? The AI agent costs $500/month.",
            "description": "Basic ROI calculation",
            "category": "Business Value"
        },
        {
            "query": "Calculate business value: 50,000 questions/month, save 15 minutes per question without AI vs 3 minutes with AI, 90% of questions save time, $60/hour labor cost, AI costs $2000/month, analyze over 12 months",
            "description": "Comprehensive business value analysis",
            "category": "Business Value"
        },
        {
            "query": "Compare costs: Claude Haiku vs Claude Sonnet for 20,000 questions with 1500 input and 600 output tokens each",
            "description": "Model comparison",
            "category": "What-If Analysis"
        }
    ]
    
    print("\n" + "="*80)
    print("🧪 Running Test Queries")
    print("="*80)
    
    passed = 0
    failed = 0
    results_by_category = {}
    
    for i, test in enumerate(test_queries, 1):
        category = test['category']
        if category not in results_by_category:
            results_by_category[category] = {'passed': 0, 'failed': 0}
        
        print(f"\n{'─'*80}")
        print(f"📝 Test {i}/{len(test_queries)}: {test['description']}")
        print(f"   Category: {category}")
        print(f"   Query: {test['query'][:80]}...")
        
        try:
            print(f"   ⏳ Processing...")
            result = await session.call_tool(
                name="invoke_cost_analysis_agent_read_only",
                arguments={"query": test['query']}
            )
            result_text = result.content[0].text
            
            # Try to parse as JSON
            try:
                result_data = json.loads(result_text)
                
                # Check for errors
                if isinstance(result_data, dict) and 'error' in result_data:
                    print(f"   ⚠️  Agent returned error: {result_data['error'][:100]}")
                    failed += 1
                    results_by_category[category]['failed'] += 1
                else:
                    # Success
                    print(f"   ✅ Success")
                    
                    # Show summary based on response type
                    if verbose:
                        print(f"\n   📊 Response Summary:")
                        if 'BEDROCK_COSTS' in result_data:
                            bedrock = result_data['BEDROCK_COSTS']
                            total = bedrock.get('total_monthly_cost', 0)
                            print(f"      Bedrock Total: ${total:,.2f}/month")
                        if 'AGENTCORE_COSTS' in result_data:
                            agentcore = result_data['AGENTCORE_COSTS']
                            total = agentcore.get('total_monthly_cost', 0)
                            print(f"      AgentCore Total: ${total:,.2f}/month")
                        if 'EMR_COSTS' in result_data:
                            emr = result_data['EMR_COSTS']
                            if 'cluster_totals' in emr:
                                nodes = emr['cluster_totals'].get('total_nodes', 0)
                                print(f"      EMR Nodes: {nodes}")
                        if 'BUSINESS_VALUE' in result_data:
                            bva = result_data['BUSINESS_VALUE']
                            roi = bva.get('roi_percent', 0)
                            print(f"      ROI: {roi:.1f}%")
                    
                    passed += 1
                    results_by_category[category]['passed'] += 1
                    
            except json.JSONDecodeError:
                # Not JSON, but still success
                print(f"   ✅ Success (non-JSON response)")
                if verbose:
                    print(f"   Response: {result_text[:200]}...")
                passed += 1
                results_by_category[category]['passed'] += 1
                
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:100]}")
            if verbose:
                import traceback
                traceback.print_exc()
            failed += 1
            results_by_category[category]['failed'] += 1
        
        # Small delay between tests
        if i < len(test_queries):
            await asyncio.sleep(1)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 Test Summary")
    print("="*80)
    print(f"\n🎯 Overall Results:")
    print(f"   Total Tests: {passed + failed}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    if passed + failed > 0:
        print(f"   Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    print(f"\n📂 Results by Category:")
    for category, results in results_by_category.items():
        total = results['passed'] + results['failed']
        rate = (results['passed'] / total * 100) if total > 0 else 0
        print(f"   {category}:")
        print(f"      ✅ {results['passed']}/{total} passed ({rate:.0f}%)")
    
    print("\n" + "="*80)
    print("✅ Local MCP Server Testing Complete!")
    print("="*80)


async def test_single_query(mcp_url: str, query: str, verbose: bool = False):
    """Test a single query against the MCP server"""
    
    headers = {"Content-Type": "application/json"}
    
    print(f"\n{'='*80}")
    print(f"🤖 Testing Single Query")
    print(f"{'='*80}")
    print(f"Query: {query}")
    
    try:
        async with streamablehttp_client(
            mcp_url,
            headers,
            timeout=timedelta(seconds=30)
        ) as (read_stream, write_stream, _):
            
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                print(f"\n⏳ Processing query...")
                result = await session.call_tool(
                    name="invoke_cost_analysis_agent_read_only",
                    arguments={"query": query}
                )
                result_text = result.content[0].text
                
                print(f"\n✅ Agent Response:")
                print(f"{'='*80}")
                
                # Try to parse and pretty print JSON
                try:
                    result_data = json.loads(result_text)
                    print(json.dumps(result_data, indent=2))
                except json.JSONDecodeError:
                    print(result_text)
                
                print(f"{'='*80}")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


async def main():
    parser = argparse.ArgumentParser(
        description='Test Local MCP Server for Strands Cost Calculator Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Prerequisites:
  Start the MCP server first:
    python strands_cost_calc_agent.py

Examples:
  # Run full test suite
  python test_local_mcp_server.py
  
  # Test with custom port
  python test_local_mcp_server.py --port 8080
  
  # Test single query
  python test_local_mcp_server.py --query "Calculate Bedrock costs for 10k questions"
  
  # Verbose output
  python test_local_mcp_server.py --verbose
        """
    )
    parser.add_argument('--port', type=int, default=8000,
                        help='Port where MCP server is running (default: 8000)')
    parser.add_argument('--host', type=str, default='localhost',
                        help='Host where MCP server is running (default: localhost)')
    parser.add_argument('--query', type=str,
                        help='Test a single query instead of running full suite')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed output including response summaries')
    
    args = parser.parse_args()
    
    mcp_url = f"http://{args.host}:{args.port}/mcp"
    
    print(f"{'='*80}")
    print(f"🚀 Local MCP Server Test Client")
    print(f"{'='*80}")
    print(f"Server: {mcp_url}")
    
    try:
        if args.query:
            # Test single query
            await test_single_query(mcp_url, args.query, args.verbose)
        else:
            # Run full test suite
            await test_mcp_server(mcp_url, args.verbose)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
