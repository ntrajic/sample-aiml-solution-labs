# Testing Guide for Strands Cost Calculator Agent

This guide covers three ways to test the Strands Cost Calculator Agent:

1. **Direct Testing** - Test the agent directly without MCP server
2. **Local MCP Server** - Test the MCP server running locally
3. **AgentCore Deployment** - Test the deployed agent on AWS

## Prerequisites

```bash
# Install dependencies
pip install -r ../requirements.txt

# Ensure AWS credentials are configured
aws sts get-caller-identity
```

## 1. Direct Testing (Recommended for Development)

Test the agent directly by importing and calling it. This is the fastest way to test during development.

### Basic Usage

```bash
# Run full test suite
python test_agent_direct.py

# Test specific query
python test_agent_direct.py --query "Calculate Bedrock costs for 10k questions"

# Interactive mode
python test_agent_direct.py --interactive

# Verbose output
python test_agent_direct.py --verbose
```

### Example Queries

```bash
# Pricing lookup
python test_agent_direct.py --query "What is the pricing for Claude Haiku in us-west-2?"

# Bedrock cost calculation
python test_agent_direct.py --query "Calculate Bedrock costs for 10,000 questions per month using Claude Haiku with 1000 input tokens and 500 output tokens"

# AgentCore pricing
python test_agent_direct.py --query "What are the AgentCore pricing components for us-west-2?"

# EMR sizing
python test_agent_direct.py --query "Size an EMR cluster for 5TB batch processing with Spark on EC2"

# Business value analysis
python test_agent_direct.py --query "What's the ROI if I save 10 minutes per question for 10k questions at $50/hour labor cost?"
```

### Advantages
- ✅ Fastest testing method
- ✅ No server setup required
- ✅ Easy debugging with stack traces
- ✅ Works offline (except for AWS API calls)

### Limitations
- ❌ Doesn't test MCP protocol
- ❌ Doesn't test HTTP transport

## 2. Local MCP Server Testing

Test the MCP server running locally. This validates the MCP protocol implementation.

### Basic Usage

```bash
# Start server and run tests
python test_local_mcp_server.py

# Use custom port
python test_local_mcp_server.py --port 8080

# Verbose output
python test_local_mcp_server.py --verbose
```

### What It Tests
- ✅ MCP protocol implementation
- ✅ HTTP transport layer
- ✅ Tool registration and discovery
- ✅ Tool invocation and responses
- ✅ Error handling

### Advantages
- ✅ Tests full MCP stack
- ✅ Validates protocol compliance
- ✅ No AWS deployment needed
- ✅ Fast iteration

### Limitations
- ❌ Doesn't test AgentCore integration
- ❌ Doesn't test authentication
- ❌ Doesn't test production environment

## 3. AgentCore Deployment Testing

Test the agent deployed on AWS Bedrock AgentCore. This is for production validation.

### Prerequisites

```bash
# Deploy the agent first
cd ..
python run_prerequisite.py

# Follow the deployment instructions
agentcore configure --entrypoint Bedrock-AgentCore-EMR-Calculator/strands_cost_calc_agent.py ...
agentcore launch --agent strands_cost_calc_agent

# Wait for deployment (~10-15 minutes)
agentcore status --agent strands_cost_calc_agent
```

### Basic Usage

```bash
# Test with authentication (default)
cd ..
python test_mcp_client.py

# Test without authentication
python test_mcp_client.py --no-auth

# Test with manual bearer token
python test_mcp_client.py --bearer-token <token>

# Test with specific agent ARN
python test_mcp_client.py --agent-arn <arn>
```

### What It Tests
- ✅ Full production environment
- ✅ AgentCore runtime integration
- ✅ Authentication and authorization
- ✅ Network connectivity
- ✅ Scalability and performance

### Advantages
- ✅ Production environment validation
- ✅ Tests authentication
- ✅ Tests AWS integration
- ✅ Performance testing

### Limitations
- ❌ Requires AWS deployment
- ❌ Slower iteration cycle
- ❌ Costs money to run

## Test Coverage

All three testing methods cover these scenarios:

### Pricing Queries
- Bedrock model pricing lookup
- AgentCore component pricing
- AWS service pricing (EMR, S3, etc.)
- Attribute value discovery

### Cost Calculations
- Bedrock LLM costs (single/multiple models)
- Vector database token costs
- Tool invocation costs
- AgentCore runtime costs
- EMR cluster sizing and costs

### Business Value Analysis
- Cost savings calculations
- Revenue growth projections
- Customer churn reduction
- ROI calculations

### What-If Analysis
- Parameter sensitivity analysis
- Multi-dimensional comparisons
- Scenario planning

## Troubleshooting

### Direct Testing Issues

**Import errors:**
```bash
# Make sure you're in the correct directory
cd usecases/mcp-aws-cost-analysis/Bedrock-AgentCore-EMR-Calculator

# Check Python path
python -c "import sys; print(sys.path)"
```

**AWS credential errors:**
```bash
# Configure AWS credentials
aws configure

# Verify credentials
aws sts get-caller-identity
```

### Local MCP Server Issues

**Port already in use:**
```bash
# Use different port
python test_local_mcp_server.py --port 8080

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

**Server won't start:**
```bash
# Check for errors
python test_local_mcp_server.py --verbose

# Test server directly
python strands_cost_calc_agent.py
```

**Connection refused:**
```bash
# Check if server is running
curl http://localhost:8000/mcp

# Check server logs
python test_local_mcp_server.py --verbose
```

### AgentCore Testing Issues

**Agent not found:**
```bash
# Check deployment status
agentcore status --agent strands_cost_calc_agent

# Check agent ARN
cat ../.bedrock_agentcore.yaml
```

**Authentication errors:**
```bash
# For no-auth deployments
python test_mcp_client.py --no-auth

# Check Cognito credentials
aws secretsmanager get-secret-value --secret-id strands_cost_calc_agent/cognito/credentials
```

**Timeout errors:**
```bash
# Wait for server to warm up (2-3 minutes)
sleep 180

# Check server logs
aws logs tail /aws/bedrock-agentcore/runtimes/strands_cost_calc_agent --follow

# Skip status check
python test_mcp_client.py --skip-status-check
```

## Best Practices

### Development Workflow
1. Start with **direct testing** for rapid iteration
2. Use **local MCP server** to validate protocol
3. Deploy to **AgentCore** for final validation

### Testing Strategy
1. Test individual tools first
2. Test complex queries with multiple tools
3. Test error handling and edge cases
4. Test performance with realistic workloads

### Debugging Tips
1. Use `--verbose` flag for detailed output
2. Check AWS CloudWatch logs for AgentCore
3. Use interactive mode for exploratory testing
4. Add print statements in agent code for debugging

## Example Test Scenarios

### Scenario 1: Basic Bedrock Cost Calculation
```bash
python test_agent_direct.py --query "Calculate Bedrock costs for 10,000 questions per month using Claude Haiku with 1000 input tokens and 500 output tokens per question"
```

### Scenario 2: Multi-Model Comparison
```bash
python test_agent_direct.py --query "Compare costs for 20,000 questions: Claude Haiku vs Claude Sonnet with 1500 input and 600 output tokens"
```

### Scenario 3: Agentic Workflow with Tools
```bash
python test_agent_direct.py --query "I have an agent with 10 tools, uses 3 tools per question, 80% of questions invoke tools. Calculate costs for 50k questions with Claude Sonnet."
```

### Scenario 4: Complete Solution Cost
```bash
python test_agent_direct.py --query "Calculate total monthly cost for: 100k questions, Claude Haiku, vector database with 5 chunks, AgentCore runtime 200 hours, 2GB memory"
```

### Scenario 5: ROI Analysis
```bash
python test_agent_direct.py --query "ROI analysis: 50k questions/month, save 15 min/question, $60/hour labor, AI costs $2000/month, 12 month period"
```

## Performance Benchmarks

Expected response times:

- **Direct Testing**: 2-5 seconds per query
- **Local MCP Server**: 3-7 seconds per query
- **AgentCore Deployment**: 5-15 seconds per query (includes cold start)

## Next Steps

After testing:

1. Review test results and fix any issues
2. Optimize agent prompts based on test feedback
3. Add custom test cases for your use cases
4. Deploy to production AgentCore
5. Monitor performance and costs

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review agent logs and error messages
3. Consult the main README.md for deployment details
4. Check AWS documentation for service-specific issues
