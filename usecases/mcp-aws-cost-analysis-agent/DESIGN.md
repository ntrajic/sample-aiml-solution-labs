# AWS Cost Analysis Agent - Design Document

## Table of Contents

- [Overview](#overview)
- [Design Goals](#design-goals)
- [Architecture](#architecture)
- [Component Design](#component-design)
- [Agent Design](#agent-design)
- [Tool Design](#tool-design)
- [Data Flow](#data-flow)
- [Design Decisions](#design-decisions)
- [Scalability](#scalability)
- [Security](#security)

## Overview

The AWS Cost Analysis Agent is an AI-powered system that provides detailed AWS pricing calculations and business value analysis. It's designed as a Model Context Protocol (MCP) server running on Amazon Bedrock AgentCore Runtime, enabling integration with various AI assistants and applications.

### What It Does

The agent serves as an expert AWS cost analyst that can:

1. **Retrieve Real-Time Pricing**: Fetch current AWS pricing for Bedrock models, AgentCore components, and EMR services
2. **Calculate Costs**: Perform detailed cost calculations based on usage patterns and configurations
3. **Analyze Business Value**: Calculate ROI, cost savings, and revenue impact of AI implementations
4. **Compare Scenarios**: Run what-if analyses to compare different configurations and parameters
5. **Provide Recommendations**: Suggest optimal configurations based on workload requirements

### Target Users

- **AWS Sales Teams**: Pre-sales cost estimation and TCO analysis
- **Solution Architects**: Architecture cost planning and optimization
- **Customers**: Self-service cost estimation and planning
- **Finance Teams**: Budget planning and cost forecasting

## Design Goals

### 1. Accuracy
- Use real-time AWS Pricing API data (never cached or hardcoded prices)
- Provide detailed calculation breakdowns with step-by-step explanations
- Support all pricing dimensions (input/output tokens, memory, compute, storage)

### 2. Flexibility
- Support multiple AWS services (Bedrock, AgentCore, EMR)
- Handle various deployment modes (EC2, Serverless, EKS for EMR)
- Enable what-if analysis for scenario comparison

### 3. Usability
- Natural language interface (conversational queries)
- Structured JSON output for programmatic consumption
- Comprehensive error messages and validation

### 4. Scalability
- Serverless deployment on AgentCore Runtime
- Stateless design for horizontal scaling
- Efficient API usage with pagination support

### 5. Security
- IAM-based access control
- Optional Cognito authentication for app-to-app integration
- Principle of least privilege for AWS permissions

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  (Claude Desktop, Custom Apps, Web Interfaces, CLI Tools)        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ MCP Protocol (HTTPS)
                             │ + OAuth2 Bearer Token
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Authentication Layer                          │
│              (Amazon Cognito User Pool - Optional)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Authenticated Request
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   AgentCore Runtime Layer                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              MCP Server (FastMCP)                        │  │
│  │  • HTTP Transport (Streamable)                           │  │
│  │  • Tool Registration & Discovery                         │  │
│  │  • Request/Response Handling                             │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                      │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │           Strands Agent (Orchestration)                  │  │
│  │  • Claude Haiku 4.5 (Reasoning)                          │  │
│  │  • System Prompt (Expert Persona)                        │  │
│  │  • Tool Selection & Invocation                           │  │
│  │  • Response Formatting (Pydantic Models)                 │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                      │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │              Tool Layer (12 Tools)                       │  │
│  │                                                           │  │
│  │  Pricing Tools:                                          │  │
│  │  • get_bedrock_pricing                                   │  │
│  │  • get_agentcore_pricing                                 │  │
│  │  • get_aws_pricing                                       │  │
│  │  • get_attribute_values                                  │  │
│  │                                                           │  │
│  │  Calculator Tools:                                       │  │
│  │  • use_bedrock_calculator                                │  │
│  │  • use_agentcore_calculator                              │  │
│  │  • use_emr_calculator                                    │  │
│  │  • bva_calculator                                        │  │
│  │                                                           │  │
│  │  What-If Analysis Tools:                                 │  │
│  │  • bedrock_what_if_analysis                              │  │
│  │  • agentcore_what_if_analysis                            │  │
│  │  • emr_what_if_analysis                                  │  │
│  │  • bva_what_if_analysis                                  │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌──────▼────────┐  ┌─────▼──────────┐
│   Bedrock      │  │   Pricing     │  │  CloudWatch    │
│   Runtime      │  │     API       │  │     Logs       │
│                │  │               │  │                │
│ • Claude 4.5   │  │ • GetProducts │  │ • PutLogEvents │
│ • InvokeModel  │  │ • GetAttribs  │  │ • CreateStream │
└────────────────┘  └───────────────┘  └────────────────┘
```

### Component Layers

1. **Client Layer**: Any MCP-compatible client (Claude Desktop, custom apps)
2. **Authentication Layer**: Optional Cognito for secure access
3. **Runtime Layer**: AgentCore provides serverless execution environment
4. **MCP Server Layer**: FastMCP handles protocol implementation
5. **Agent Layer**: Strands Agent orchestrates tool usage with Claude
6. **Tool Layer**: 12 specialized tools for pricing and calculations
7. **AWS Services Layer**: Bedrock, Pricing API, CloudWatch Logs

## Component Design

### 1. MCP Server (FastMCP)

**Purpose**: Implement Model Context Protocol for tool discovery and invocation

**Key Features**:
- HTTP transport with streamable responses
- Stateless design (no session management)
- Tool registration and metadata
- Request validation and error handling

**Implementation**:
```python
from fastmcp import FastMCP

mcp = FastMCP(host="0.0.0.0", stateless_http=True)

@mcp.tool
def invoke_cost_analysis_agent_read_only(query: str):
    """Single entry point for all cost analysis queries"""
    response = invoke_strands_agent(agent, query)
    return response.message['content'][0]['text']
```

**Design Decisions**:
- Single tool exposed to MCP clients (`invoke_cost_analysis_agent_read_only`)
- Agent internally selects and invokes appropriate tools
- Simplifies client integration (one tool to call)
- Enables natural language queries

### 2. Strands Agent

**Purpose**: Orchestrate tool usage and generate responses using Claude

**Key Features**:
- Expert system prompt with cost analyst persona
- Tool selection based on query analysis
- Structured output using Pydantic models
- Retry logic with exponential backoff

**System Prompt Design**:
```python
agent_system_prompt = """
You are an expert AWS cost analyst specializing in Amazon Bedrock, 
AgentCore, and EMR pricing calculations.

PRICING DATA REQUIREMENTS:
- Use ONLY pricing retrieved from tools
- Never rely on pre-trained knowledge
- Default to us-west-2 region

QUERY ANALYSIS:
- Identify service (Bedrock/AgentCore/EMR)
- Determine if business value analysis needed
- Follow appropriate workflow

INTERACTIONS:
- Ask targeted questions for missing parameters
- Provide sensible defaults
- Enable quick progression with "Ok. Go."
"""
```

**Model Selection**:
- **Claude Haiku 4.5**: Fast, cost-effective, sufficient for structured tasks
- Temperature: 0.1 (deterministic outputs)
- Supports tool use and structured outputs

### 3. Tool Layer

#### Pricing Tools

**get_bedrock_pricing**
- Retrieves Bedrock model pricing from AWS Pricing API
- Supports fuzzy model name matching
- Handles 1P and 3P models differently
- Returns structured pricing data

**get_agentcore_pricing**
- Retrieves AgentCore component pricing
- Covers runtime, memory, tools, gateway, identity
- Region-specific pricing

**get_aws_pricing**
- Generic AWS service pricing retrieval
- Flexible filtering by service code and attributes
- Supports pagination for large result sets

**get_attribute_values**
- Discovers available attribute values
- Useful for building filters dynamically

#### Calculator Tools

**use_bedrock_calculator**
- Calculates monthly Bedrock costs
- Supports:
  - Multiple LLM models
  - Vector database token costs
  - Tool invocation costs
  - Conversation history
  - System prompts
- Returns detailed breakdowns with explanations

**use_agentcore_calculator**
- Calculates monthly AgentCore costs
- Components:
  - Runtime (vCPU + memory)
  - Browser tool
  - Code interpreter
  - Gateway (tool indexing + invocations)
  - Memory (events + records + retrievals)
- Accounts for wait time percentages

**use_emr_calculator**
- Sizes EMR clusters based on workload
- Modes:
  - EC2: Core + task nodes
  - Serverless: Worker configuration
  - EKS: Node groups + pods
- Returns node counts, resources, recommendations

**bva_calculator**
- Business value analysis
- Calculates:
  - Cost savings from time efficiency
  - Revenue growth from reallocated resources
  - Customer churn reduction impact
  - ROI over analysis period

#### What-If Analysis Tools

Each calculator has a corresponding what-if analysis tool:
- Varies 1-2 parameters while keeping others constant
- Generates cost matrices for comparison
- Supports heatmap visualization
- Enables sensitivity analysis

### 4. Data Models (Pydantic)

**Purpose**: Enforce structured outputs and validate data

**Key Models**:

```python
class BedrockCosts(BaseModel):
    models: Dict[str, LLMModelCosts]
    vector_database: Optional[VectorDatabaseCosts]
    questions_per_month: int
    total_monthly_cost: float

class AgentCoreCosts(BaseModel):
    runtime_cost: float
    browser_tool_cost: float
    code_interpreter_cost: float
    gateway_cost: float
    memory_cost: float
    total_monthly_cost: float

class BusinessValue(BaseModel):
    initial_investment: float
    key_assumptions: KeyAssumptions
    cost_savings: Optional[CostSavings]
    revenue_growth: Optional[RevenueGrowth]
    total_benefits: float
    roi_percent: float
```

**Benefits**:
- Type safety and validation
- Self-documenting schemas
- JSON serialization
- IDE autocomplete support

## Agent Design

### Query Processing Flow

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  1. Query Analysis                  │
│  • Identify service (Bedrock/AC/EMR)│
│  • Detect analysis type (cost/ROI)  │
│  • Extract parameters                │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  2. Parameter Validation             │
│  • Check required parameters         │
│  • Request missing information       │
│  • Suggest defaults                  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  3. Tool Selection                   │
│  • Choose pricing tools              │
│  • Select calculator tools           │
│  • Determine what-if needs           │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  4. Tool Invocation                  │
│  • Call pricing APIs                 │
│  • Execute calculations              │
│  • Handle errors/retries             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  5. Response Formatting              │
│  • Structure as JSON                 │
│  • Include explanations              │
│  • Add recommendations               │
└────────────┬────────────────────────┘
             │
             ▼
        JSON Response
```

### Conversation Patterns

**Pattern 1: Direct Query with All Parameters**
```
User: "Calculate Bedrock costs for 10k questions, Claude Haiku, 
       1000 input tokens, 500 output tokens"
       
Agent: [Calls get_bedrock_pricing, use_bedrock_calculator]
       Returns complete cost breakdown
```

**Pattern 2: Iterative Parameter Collection**
```
User: "Calculate Bedrock costs"

Agent: "I need details:
        1. Which model? (default: Claude Haiku 4.5)
        2. Input tokens? (default: 5,000)
        3. Questions/month? (default: 10,000)
        Type 'Ok. Go.' to use defaults"

User: "Ok. Go."

Agent: [Proceeds with defaults]
       Returns cost breakdown
```

**Pattern 3: Use Case Exploration**
```
User: "I have 100K customers with 80% backup failure rate. 
       Want to use agents to process failures."

Agent: "Let me understand cost drivers:
        1. Failures per day? (default: 80,000 from your 80% rate)
        2. Log message size? (default: 2,000 tokens)
        3. Agent actions? (default: diagnose + fix, 1,500 tokens)
        Type 'Ok. Go.' to proceed"

User: "Ok. Go."

Agent: [Calculates based on use case context]
       Returns comprehensive analysis
```

## Tool Design

### Design Principles

1. **Single Responsibility**: Each tool does one thing well
2. **Composability**: Tools can be combined for complex analyses
3. **Idempotency**: Same inputs always produce same outputs
4. **Error Handling**: Graceful degradation with informative errors
5. **Logging**: All errors logged before returning

### Tool Implementation Pattern

```python
import logging

logger = logging.getLogger(__name__)

@tool
def calculator_tool(params: dict) -> dict:
    """
    Tool description for AI assistant
    
    Args:
        params: Input parameters with validation
    
    Returns:
        Structured results with explanations
    """
    try:
        # 1. Validate inputs
        if required_param is None:
            error_msg = 'Missing required parameter'
            logger.error(error_msg)
            return {'error': error_msg}
        
        # 2. Perform calculations
        result = calculate(params)
        
        # 3. Build explanations
        explanations = [
            "Step 1: calculation details",
            "Step 2: more details"
        ]
        
        # 4. Return structured output
        return {
            'result': result,
            'explanations': explanations
        }
        
    except Exception as e:
        error_msg = f'Calculation failed: {str(e)}'
        logger.exception(error_msg)
        return {'error': error_msg}
```

### Pricing Tool Design

**Challenge**: AWS Pricing API complexity
- Different service codes for 1P vs 3P models
- Pagination for large result sets
- Complex filtering requirements
- Region-specific pricing

**Solution**: Abstraction layers
```python
def get_bedrock_pricing(model_name: str, region: str):
    # 1. Determine service code (1P vs 3P)
    service_code = determine_service_code(model_name)
    
    # 2. Build filters
    filters = build_filters(region, model_name)
    
    # 3. Paginate through results
    all_products = paginate_pricing_api(service_code, filters)
    
    # 4. Parse and structure
    return parse_pricing_data(all_products)
```

### Calculator Tool Design

**Challenge**: Complex cost calculations with many variables

**Solution**: Modular calculation with detailed explanations
```python
def use_bedrock_calculator(params: dict):
    # 1. Extract global parameters
    questions_per_month = params['questions_per_month']
    
    # 2. Calculate vector database tokens (global)
    vector_tokens = calculate_vector_tokens(params)
    
    # 3. Process each model
    for model_key, model_params in params.items():
        # Calculate base tokens
        base_input = calculate_base_input(model_params)
        base_output = calculate_base_output(model_params)
        
        # Add tool tokens
        tool_tokens = calculate_tool_tokens(model_params)
        
        # Add system prompt and history
        system_tokens = calculate_system_tokens(model_params)
        history_tokens = calculate_history_tokens(model_params)
        
        # Sum all tokens
        total_input = (base_input + vector_tokens + 
                      tool_tokens + system_tokens + history_tokens)
        
        # Calculate costs
        input_cost = (total_input / 1_000_000) * input_price
        output_cost = (total_output / 1_000_000) * output_price
        
        # Build explanations
        explanations = build_step_by_step_explanations(...)
        
        results[model_key] = {
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': input_cost + output_cost,
            'explanations': explanations
        }
    
    return results
```

## Data Flow

### Pricing Data Flow

```
User Query
    │
    ▼
Agent analyzes query
    │
    ▼
Calls get_bedrock_pricing("claude", "us-west-2")
    │
    ▼
pricing_util.py
    │
    ├─> boto3.client('pricing', region='us-east-1')
    │
    ├─> Determine service code (1P vs 3P)
    │
    ├─> Build filters (region, model, term type)
    │
    ├─> Paginate: pricing_client.get_products()
    │   │
    │   ├─> Page 1 (100 results)
    │   ├─> Page 2 (100 results)
    │   └─> Page N (remaining)
    │
    ├─> Parse JSON responses
    │
    ├─> Extract pricing dimensions
    │
    ├─> Remove duplicates
    │
    └─> Return structured pricing data
        │
        ▼
Agent receives pricing data
    │
    ▼
Calls use_bedrock_calculator(params)
    │
    ▼
Calculator performs calculations
    │
    ▼
Returns cost breakdown with explanations
    │
    ▼
Agent formats as JSON
    │
    ▼
MCP server returns to client
```

### What-If Analysis Data Flow

```
User: "Compare Claude Haiku vs Sonnet for 20k questions"
    │
    ▼
Agent calls bedrock_what_if_analysis(
    base_params={...},
    primary_variable="model1.model_name",
    primary_range=["claude-haiku", "claude-sonnet"]
)
    │
    ▼
For each value in primary_range:
    │
    ├─> Create scenario_params
    │
    ├─> Call use_bedrock_calculator(scenario_params)
    │
    ├─> Extract total_cost
    │
    └─> Store in results[]
    │
    ▼
Calculate summary metrics:
    │
    ├─> min_cost
    ├─> max_cost
    └─> cost_range
    │
    ▼
Return comparison results
    │
    ▼
Agent formats comparison
    │
    ▼
Client receives cost comparison
```

## Design Decisions

### 1. Why Strands Agent Framework?

**Decision**: Use Strands instead of raw Bedrock API

**Rationale**:
- Built-in tool orchestration
- Automatic retry logic
- Conversation management
- Structured output support
- Simplified error handling

**Trade-offs**:
- Additional dependency
- Learning curve
- Framework limitations

### 2. Why Claude Haiku 4.5?

**Decision**: Use Haiku instead of Sonnet or Opus

**Rationale**:
- Cost-effective (~5x cheaper than Sonnet)
- Fast response times
- Sufficient for structured tasks
- Good tool use capabilities

**Trade-offs**:
- Less capable for complex reasoning
- May need more explicit prompting

### 3. Why Single MCP Tool?

**Decision**: Expose one tool to MCP clients, not all 12

**Rationale**:
- Simpler client integration
- Natural language interface
- Agent handles tool selection
- Easier to maintain

**Trade-offs**:
- Less control for clients
- Can't directly call specific tools
- Requires good agent prompting

### 4. Why Pydantic Models?

**Decision**: Use Pydantic for output structure

**Rationale**:
- Type safety and validation
- Self-documenting schemas
- JSON serialization
- IDE support

**Trade-offs**:
- Additional dependency
- Schema maintenance
- Potential breaking changes

### 5. Why Detailed Explanations?

**Decision**: Include step-by-step calculation explanations

**Rationale**:
- Transparency and trust
- Debugging and validation
- Educational value
- Audit trail

**Trade-offs**:
- Larger response sizes
- More processing time
- Complexity in generation

### 6. Why Logging Before Error Returns?

**Decision**: Log all errors before returning error messages

**Rationale**:
- CloudWatch Logs for debugging
- Stack traces for exceptions
- Audit trail for issues
- Production troubleshooting

**Implementation**:
```python
try:
    result = calculate()
except Exception as e:
    error_msg = f'Calculation failed: {str(e)}'
    logger.exception(error_msg)  # Logs with stack trace
    return {'error': error_msg}
```

## Scalability

### Horizontal Scaling

**AgentCore Runtime**:
- Serverless architecture
- Automatic scaling based on load
- No state management required
- Concurrent request handling

**Stateless Design**:
- No session storage
- No caching (always fresh pricing)
- Each request independent
- Can scale to thousands of concurrent users

### Performance Optimization

**Pricing API Calls**:
- Pagination for large result sets
- Efficient filtering to reduce data transfer
- Single region (us-east-1) for Pricing API

**Model Invocation**:
- Claude Haiku for speed
- Low temperature (0.1) for consistency
- Retry logic with exponential backoff

**Response Streaming**:
- FastMCP supports streaming
- Reduces perceived latency
- Better user experience

### Limits and Quotas

**Bedrock**:
- Model invocation: 10,000 requests/minute (default)
- Can request quota increases

**Pricing API**:
- 10 requests/second (default)
- Pagination handles large datasets

**AgentCore Runtime**:
- Concurrent executions: Based on account limits
- Memory: Configurable (2GB recommended)
- Timeout: Configurable (300s recommended)

## Security

### Authentication

**Cognito Integration**:
- OAuth 2.0 client credentials flow
- Machine-to-machine authentication
- Bearer token validation
- Scope-based access control

**No-Auth Mode**:
- Available for testing
- Not recommended for production
- Use with caution

### Authorization

**IAM Role**:
- Principle of least privilege
- Bedrock: Only Claude models
- Pricing: Read-only access
- CloudWatch: Write logs only

**Resource Restrictions**:
```json
{
  "Effect": "Allow",
  "Action": "bedrock:InvokeModel",
  "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
}
```

### Data Security

**In Transit**:
- HTTPS for all communications
- TLS 1.2+ required
- Bearer token in headers

**At Rest**:
- No data persistence
- Stateless design
- Logs in CloudWatch (encrypted)

**Secrets Management**:
- Cognito credentials in Secrets Manager
- IAM role credentials managed by AWS
- No hardcoded secrets

### Audit and Monitoring

**CloudWatch Logs**:
- All requests logged
- Error tracking
- Performance metrics

**CloudTrail**:
- API call history
- IAM role usage
- Pricing API access

**Metrics**:
- Request count
- Error rate
- Latency
- Token usage

## Future Enhancements

### Potential Improvements

1. **Caching Layer**
   - Cache pricing data (with TTL)
   - Reduce Pricing API calls
   - Improve response times

2. **Additional Services**
   - SageMaker pricing
   - Lambda pricing
   - S3 pricing
   - More AWS services

3. **Advanced Analytics**
   - Cost trends over time
   - Anomaly detection
   - Budget alerts
   - Forecasting

4. **Multi-Region Support**
   - Compare costs across regions
   - Recommend optimal regions
   - Currency conversion

5. **Export Capabilities**
   - PDF reports
   - Excel spreadsheets
   - CSV exports
   - Visualization charts

6. **Integration Enhancements**
   - Slack bot
   - Teams integration
   - Email reports
   - API gateway

## Conclusion

The AWS Cost Analysis Agent demonstrates a well-architected AI system that combines:
- **Modern AI frameworks** (Strands, Claude)
- **Standard protocols** (MCP)
- **AWS services** (Bedrock, AgentCore, Pricing API)
- **Best practices** (security, scalability, observability)

The design prioritizes accuracy, usability, and maintainability while providing a foundation for future enhancements.
