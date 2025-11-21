# AWS Cost Calculator Agent - User Guide

> **⚠️ IMPORTANT NOTICE**: Production Mode (AgentCore Runtime) is currently under development and NOT available for use. Please use Debug Mode (Interactive CLI) for all operations. See [Running the Agent](#running-the-agent) section for details.

## Overview

The AWS Cost Calculator Agent is an AI-powered tool that helps you calculate and analyze costs for AWS services, specifically:
- **Amazon Bedrock** (LLM models and inference)
- **Amazon Bedrock AgentCore** (Runtime, Memory, Gateway, Tools)
- **Amazon EMR** (Elastic MapReduce cluster sizing)
- **Business Value Analysis** (ROI, cost savings, revenue growth, customer churn reduction)

The agent uses AWS Pricing API to fetch real-time pricing data and provides detailed cost breakdowns with step-by-step calculations. It also performs comprehensive business value analysis to quantify the ROI of AI Agent implementations.

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Core Components](#core-components)
4. [Usage Examples](#usage-examples)
5. [Tool Reference](#tool-reference)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- Python 3.8 or higher
- AWS credentials configured (for pricing API access)
- pip or uv package manager

### Setup Steps

1. **Clone or download the repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or using uv:
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Configure AWS credentials**:
   ```bash
   aws configure
   ```
   
   The Pricing API requires access to `us-east-1` region (this is handled automatically by the tools).

---

## Quick Start

### Running the Agent

There are two modes to run the agent:

#### 1. Debug Mode (Interactive CLI) - ✅ DEFAULT & RECOMMENDED

```bash
python strands_cost_calc_agent.py
```

**This is the default mode and recommended for current use.**

This provides an interactive command-line interface for testing and development. Debug mode runs locally and uses your configured AWS credentials, so it has full access to the Pricing API.

#### 2. Production Mode (AgentCore Runtime) - ⚠️ WORK IN PROGRESS

```bash
python strands_cost_calc_agent.py --prod
```

**⚠️ IMPORTANT: Production Mode is currently NOT AVAILABLE**

Production mode is under active development. We are working on configuring the necessary IAM access policies for the AgentCore runtime role to access the AWS Pricing API (boto3 pricing client). 

**Do not use Production Mode at this time.**

**Reason**: The AgentCore runtime role needs additional permissions:
- `pricing:GetProducts` - To fetch AWS pricing data
- `pricing:DescribeServices` - To discover available services
- `pricing:GetAttributeValues` - To query service attributes

Once these IAM policies are configured and tested, Production Mode will be available for deployment.

### Example Interaction

```
You: Calculate Bedrock costs for Claude Haiku with 100K questions per month

Agent: [Fetches pricing and calculates costs with detailed breakdown]
```

---

## Core Components

### 1. Pricing Utilities (`pricing_util.py`)

Tools for fetching AWS pricing data:

- **`get_bedrock_pricing(model_name, region)`**: Get Bedrock model pricing
- **`get_agentcore_pricing(region_code)`**: Get AgentCore component pricing
- **`get_aws_pricing(service_code, filters, region)`**: Generic AWS pricing fetcher
- **`get_attribute_values(service_code, attribute_name)`**: Get available attribute values

### 2. Bedrock Calculator (`use_bedrock_calculator.py`)

Calculate costs for Bedrock LLM models:

- **`use_bedrock_calculator(params)`**: Calculate monthly Bedrock costs
- **`bedrock_what_if_analysis(base_params, ...)`**: Perform sensitivity analysis

### 3. AgentCore Calculator (`use_agentcore_calculator.py`)

Calculate costs for AgentCore components:

- **`use_agentcore_calculator(params)`**: Calculate monthly AgentCore costs
- **`agentcore_what_if_analysis(base_params, ...)`**: Perform sensitivity analysis

### 4. EMR Calculator (`use_emr_calculator.py`)

Calculate EMR cluster sizing and costs:

- **`use_emr_calculator(params)`**: Calculate EMR cluster sizing
- **`emr_what_if_analysis(base_params, ...)`**: Perform sensitivity analysis

### 5. Business Value Analysis (`bva_calculator.py`)

Calculate ROI and business value metrics:

- **`bva_calculator(params)`**: Calculate comprehensive business value analysis
- **`bva_what_if_analysis(base_params, ...)`**: Perform ROI sensitivity analysis

### 6. Service Code Discovery (`get_service_codes.py`)

Utility to discover available AWS service codes:

```bash
python get_service_codes.py --search bedrock
python get_service_codes.py --detailed
python get_service_codes.py --save
```

---

## Usage Examples

### Example 1: Calculate Bedrock Costs

**Question**: "Calculate costs for Claude Haiku processing 100,000 questions per month with 5K input tokens and 500 output tokens per question"

The agent will:
1. Fetch current pricing for Claude Haiku in your region
2. Calculate input/output token costs
3. Include system prompt and conversation history
4. Provide detailed cost breakdown

**Expected Output Structure**:
```json
{
  "models": {
    "claude_haiku": {
      "model_name": "Claude 3 Haiku",
      "input_cost": 125.00,
      "output_cost": 62.50,
      "total_cost": 187.50,
      "pricing_details": {
        "region": "us-west-2",
        "calculations": ["step-by-step breakdown"]
      }
    }
  },
  "total_monthly_cost": 187.50
}
```

### Example 2: Calculate AgentCore Costs

**Question**: "Calculate AgentCore costs for 333,333 questions per day with runtime, browser tool, and memory"

The agent will:
1. Fetch AgentCore pricing for specified region
2. Calculate costs for each component (Runtime, Browser, Gateway, Memory)
3. Account for CPU/memory usage, wait times, and API calls
4. Provide detailed explanations

**Components Calculated**:
- **Runtime**: vCPU and memory costs based on processing time
- **Browser Tool**: Additional compute for browser automation
- **Code Interpreter**: Compute for code execution
- **Gateway**: Tool invocation and search API costs
- **Memory**: Short-term and long-term memory storage/retrieval

### Example 3: Calculate EMR Cluster Sizing

**Question**: "Size an EMR EC2 cluster for 5TB of data with Spark, 10 executors"

The agent will:
1. Calculate core and task nodes needed
2. Determine executor distribution
3. Account for data size and workload type
4. Provide instance recommendations

**Output Includes**:
- Core node count and configuration
- Task node count and configuration
- Total cluster resources (vCPUs, memory, storage)
- Workload-specific recommendations

### Example 4: Business Value Analysis

**Question**: "Calculate the ROI of implementing an AI Agent that processes 100K questions per month, saves 8 minutes per question, with labor cost of $100/hour"

The agent will:
1. Calculate time and cost savings from AI efficiency
2. Estimate revenue growth from reallocated time
3. Quantify customer churn reduction benefits
4. Calculate ROI, payback period, and net value
5. Provide detailed step-by-step explanations

**Output Includes**:
- **Cost Savings**: Labor cost reductions from time savings
- **Revenue Growth**: Additional revenue from freed-up employee time
- **Customer Churn Reduction**: Value from improved customer retention
- **ROI Metrics**: Return on investment, payback period, net value

**Important Note on Double-Counting**: Time savings from AI Agents are used in both Cost Savings and Revenue Growth calculations. To avoid double-counting benefits:
- Use **Cost Savings** if the primary benefit is reducing labor costs
- Use **Revenue Growth** if the primary benefit is generating additional revenue from freed-up time
- Customer Churn Reduction benefits are independent and can be combined with either

### Example 5: What-If Analysis

**Question**: "Compare costs for different question volumes: 10K, 50K, 100K per month"

The agent will:
1. Run calculations for each scenario
2. Compare costs side-by-side
3. Show cost sensitivity to volume changes
4. Provide min/max/range metrics

---
# MISCELLANEOUS CONTENT (DONT HAVE TO READ)

## Tool Reference

### Bedrock Calculator Parameters

```python
params = {
    # Global parameters
    "questions_per_month": 100000,
    "system_prompt_tokens": 500,
    "history_qa_pairs": 3,
    
    # Vector database (optional)
    "vector_database": {
        "chunks_per_call": 10,
        "tokens_per_chunk": 300
    },
    
    # LLM model configuration
    "model1": {
        "model_name": "Claude 3 Haiku",
        "cost_per_million_input_tokens": 0.25,
        "cost_per_million_output_tokens": 1.25,
        "input_tokens_per_question": 5000,
        "output_tokens_per_question": 500,
        "percent_questions_for_model": 100,
        
        # Tools (optional, for agentic use cases)
        "tools": {
            "number_of_tools": 10,
            "tools_used_by_agent": 3,
            "tool_invocations_per_question": 1.5,
            "percent_questions_that_invoke_tools": 80
        }
    }
}
```

### AgentCore Calculator Parameters

```python
params = {
    # Global parameters
    "questions_per_day": 333333,
    "days_per_month": 30,
    
    # Runtime component
    "runtime": {
        "cost_per_vcpu_hour": 0.0895,
        "cost_per_gb_hour": 0.00945,
        "percent_wait_time": 90,
        "num_cpus": 1,
        "gb_memory": 2,
        "seconds_per_question": 120
    },
    
    # Browser tool (optional)
    "browser": {
        "cost_per_vcpu_hour": 0.0895,
        "cost_per_gb_hour": 0.00945,
        "percent_wait_time": 90,
        "seconds_per_question": 600,
        "percent_questions_using_browser": 20
    },
    
    # Gateway component
    "gateway": {
        "cost_per_invoke_tool_api": 0.00025,
        "cost_per_search_api_invocation": 0.00025,
        "cost_per_tool_indexed_per_month": 0.10,
        "tools_to_invoke_per_question": 1,
        "percent_questions_using_tools": 100
    },
    
    # Memory component
    "memory": {
        "cost_per_raw_event": 0.00025,
        "cost_per_memory_record_per_month": 0.000001,
        "cost_per_memory_retrieval": 0.00025,
        "events_per_question": 2,
        "percent_questions_storing_events": 100
    }
}
```

### EMR Calculator Parameters

```python
# EC2 Mode
params = {
    "mode": "ec2",
    "data_size_tb": 5.0,
    "job_type": "batch",  # or 'streaming', 'etl', 'ml'
    "application": "spark",  # or 'hive', 'presto'
    "num_executors": 10,
    "cores_per_executor": 4,
    "memory_per_executor_gb": 16,
    "instance_type_core": "m5.xlarge",
    "core_instance_vcpus": 4,
    "core_instance_memory_gb": 16,
    "core_instance_storage_gb": 0
}

# Serverless Mode
params = {
    "mode": "serverless",
    "job_type": "batch",
    "application": "spark",
    "worker_vcpus": 4,
    "worker_memory_gb": 16,
    "expected_workers": 10,
    "max_workers": 20
}

# EKS Mode
params = {
    "mode": "eks",
    "data_size_tb": 5.0,
    "job_type": "batch",
    "application": "spark",  # or 'trino'
    "num_workers": 10,
    "cores_per_worker": 4,
    "memory_per_worker_gb": 16,
    "node_instance_type": "m5.xlarge",
    "node_instance_vcpus": 4,
    "node_instance_memory_gb": 16
}
```

### Business Value Analysis (BVA) Parameters

```python
params = {
    # Global parameters (required)
    "questions_per_month": 100000,
    "minutes_per_question_without_ai": 10.0,
    "minutes_per_question_with_ai": 2.0,
    "percent_questions_that_save_time": 80,  # % of questions where AI helps
    "ai_agent_cost_per_month": 5000.0,  # Total monthly AI costs
    "analysis_period_months": 12,
    
    # Cost Savings component (optional)
    # Use this if primary benefit is reducing labor costs
    "cost_savings": {
        "labor_cost_per_hour": 100.0
    },
    
    # Revenue Growth component (optional)
    # Use this if primary benefit is generating new revenue
    # WARNING: Don't use both cost_savings and revenue_growth simultaneously
    # as they both use time savings (would double-count benefits)
    "revenue_growth": {
        "percent_time_to_new_projects": 60,  # % of saved time for new projects
        "revenue_per_employee_per_hour": 150.0
    },
    
    # Customer Churn Reduction component (optional)
    # Independent of time savings - can combine with either cost_savings or revenue_growth
    "customer_churn_reduction": {
        "total_customer_count": 10000,
        "customer_churn_before_ai": 1.0,  # % monthly churn before AI
        "customer_churn_after_ai": 0.5,   # % monthly churn after AI
        "average_monthly_revenue_per_customer": 100.0
    },
    
    # Implementation Costs (optional)
    "implementation_costs": {
        "one_time_implementation_cost": 100000.0,  # Setup, integration
        "one_time_training_cost": 20000.0          # Training, change management
    }
}
```

**BVA Output Structure**:
```python
{
    "global_parameters": {...},
    
    "cost_savings": {
        "monthly_labor_savings": 133333.33,
        "monthly_net_savings": 128333.33,  # After AI costs
        "total_net_savings_period": 1540000.00,
        "calculation_explanations": [...]
    },
    
    "revenue_growth": {
        "monthly_additional_revenue": 120000.00,
        "total_revenue_growth_period": 1440000.00,
        "calculation_explanations": [...]
    },
    
    "customer_churn_reduction": {
        "customers_saved_per_month": 50.0,
        "monthly_total_churn_value": 29000.00,
        "total_churn_reduction_value_period": 348000.00,
        "calculation_explanations": [...]
    },
    
    "implementation_costs": {
        "total_implementation_costs": 120000.00,
        "calculation_explanations": [...]
    },
    
    "business_value_summary": {
        "total_benefits": 1888000.00,
        "total_costs": 120000.00,
        "net_value": 1768000.00,
        "roi_percent": 1473.33,
        "payback_months": 0.93,
        "monthly_net_benefit": 157333.33,
        "calculation_explanations": [...]
    }
}
```

---

## Advanced Features

### 1. What-If Analysis

Compare multiple scenarios by varying one or two parameters:

**1D Analysis** (vary one parameter):
```python
bedrock_what_if_analysis(
    base_params=base_config,
    primary_variable="questions_per_month",
    primary_range=[10000, 50000, 100000, 500000]
)
```

**2D Analysis** (vary two parameters):
```python
bedrock_what_if_analysis(
    base_params=base_config,
    primary_variable="questions_per_month",
    primary_range=[10000, 50000, 100000],
    secondary_variable="input_tokens_per_question",
    secondary_range=[1000, 5000, 10000]
)
```

### 2. Multi-Model Comparison

Calculate costs for multiple models simultaneously:

```python
params = {
    "questions_per_month": 100000,
    "model1": {
        "model_name": "Claude 3 Haiku",
        "percent_questions_for_model": 70,
        # ... other params
    },
    "model2": {
        "model_name": "Claude 3 Sonnet",
        "percent_questions_for_model": 30,
        # ... other params
    }
}
```

### 3. Agentic Workload Modeling

Include tool usage for agentic applications:

```python
"tools": {
    "number_of_tools": 10,  # Total tools available
    "tools_used_by_agent": 3,  # Tools actually invoked
    "tool_invocations_per_question": 1.5,  # Avg invocations
    "percent_questions_that_invoke_tools": 80  # % using tools
}
```

### 4. Custom Instance Specifications

For EMR, specify custom instance specs:

```python
{
    "instance_type_core": "custom.xlarge",
    "core_instance_vcpus": 8,
    "core_instance_memory_gb": 32,
    "core_instance_storage_gb": 100
}
```

### 5. Business Value Modeling

Calculate comprehensive ROI for AI Agent implementations:

**Cost Savings Approach** (labor cost reduction):
```python
params = {
    "questions_per_month": 100000,
    "minutes_per_question_without_ai": 10,
    "minutes_per_question_with_ai": 2,
    "percent_questions_that_save_time": 80,
    "ai_agent_cost_per_month": 5000,
    "cost_savings": {
        "labor_cost_per_hour": 100
    }
}
```

**Revenue Growth Approach** (new revenue generation):
```python
params = {
    "questions_per_month": 100000,
    "minutes_per_question_without_ai": 10,
    "minutes_per_question_with_ai": 2,
    "percent_questions_that_save_time": 80,
    "ai_agent_cost_per_month": 5000,
    "revenue_growth": {
        "percent_time_to_new_projects": 60,
        "revenue_per_employee_per_hour": 150
    }
}
```

**Customer Retention Approach** (churn reduction):
```python
params = {
    "questions_per_month": 100000,
    "ai_agent_cost_per_month": 5000,
    "customer_churn_reduction": {
        "total_customer_count": 10000,
        "customer_churn_before_ai": 1.0,
        "customer_churn_after_ai": 0.5,
        "average_monthly_revenue_per_customer": 100
    }
}
```

**Combined Approach** (cost savings + churn reduction):
```python
params = {
    # ... global params ...
    "cost_savings": {...},
    "customer_churn_reduction": {...},
    "implementation_costs": {...}
}
```

**Important**: Don't combine `cost_savings` and `revenue_growth` in the same analysis as both use time savings (would double-count benefits). Choose one based on your business model.

### 6. BVA What-If Analysis

Compare ROI across different scenarios:

```python
bva_what_if_analysis(
    base_params=base_config,
    primary_variable="questions_per_month",
    primary_range=[50000, 100000, 200000, 500000]
)

# 2D Analysis: ROI sensitivity to volume and labor cost
bva_what_if_analysis(
    base_params=base_config,
    primary_variable="questions_per_month",
    primary_range=[50000, 100000, 200000],
    secondary_variable="cost_savings.labor_cost_per_hour",
    secondary_range=[75, 100, 125, 150]
)
```

---

## Troubleshooting

### Common Issues

#### 1. AWS Credentials Not Configured
**Error**: `Unable to locate credentials`

**Solution**:
```bash
aws configure
# Enter your AWS Access Key ID and Secret Access Key
```

#### 2. Pricing API Access Denied
**Error**: `AccessDeniedException`

**Solution**: Ensure your IAM user/role has the `pricing:GetProducts` permission.

#### 3. Model Not Found
**Error**: `No pricing found for model`

**Solution**: 
- Check model name spelling (use fuzzy matching, e.g., "haiku" instead of full name)
- Verify model is available in your region
- Use `get_bedrock_pricing()` to see available models

#### 4. Region Not Supported
**Error**: `Invalid region code`

**Solution**: Use standard AWS region codes (e.g., `us-west-2`, `eu-west-1`)

#### 5. Production Mode Not Working
**Error**: `AccessDeniedException` or pricing API failures in Production Mode

**Solution**: Production Mode is currently under development. Debug Mode is the default:
```bash
python strands_cost_calc_agent.py
```

To explicitly use production mode (when available), use the `--prod` flag:
```bash
python strands_cost_calc_agent.py --prod
```

The AgentCore runtime role needs additional IAM permissions for the Pricing API, which are being configured.

### Debug Mode

Debug mode is the default and provides detailed troubleshooting:

```bash
python strands_cost_calc_agent.py
```

This provides:
- Interactive prompt for testing
- Detailed error messages
- Step-by-step calculation visibility

### Getting Help

The agent is designed to be conversational. If you're unsure:

1. **Ask for clarification**: "What information do you need to calculate Bedrock costs?"
2. **Use defaults**: The agent will suggest defaults for missing parameters
3. **Request examples**: "Show me an example of AgentCore cost calculation"

---

## Best Practices

### 1. Start with Defaults

Let the agent guide you with default values:
```
You: Calculate Bedrock costs for my chatbot
Agent: I need some information. How many questions per month? (default: 100,000)
You: Ok. Go.
```

### 2. Provide Use Case Context

Share your use case for better recommendations:
```
You: I'm building a customer support chatbot that handles 50K questions per month. 
     Most questions need to search a knowledge base and sometimes invoke tools.
```

### 3. Use What-If Analysis

Explore cost sensitivity before committing:
```
You: Compare costs for 10K, 50K, and 100K questions per month
```

### 4. Verify Pricing Data

Always check that pricing is current:
```
You: What's the current pricing for Claude Haiku in us-west-2?
```

### 5. Document Assumptions

The agent provides detailed calculation explanations - save these for documentation and validation.

---

## API Integration

### Using Tools Programmatically

You can import and use the calculator tools directly:

```python
from use_bedrock_calculator import use_bedrock_calculator
from use_agentcore_calculator import use_agentcore_calculator
from use_emr_calculator import use_emr_calculator

# Calculate Bedrock costs
bedrock_result = use_bedrock_calculator({
    "questions_per_month": 100000,
    "model1": {
        "model_name": "Claude 3 Haiku",
        "cost_per_million_input_tokens": 0.25,
        "cost_per_million_output_tokens": 1.25,
        "input_tokens_per_question": 5000,
        "output_tokens_per_question": 500
    }
})

print(f"Total cost: ${bedrock_result['total_all_components']:.2f}")
```

### Fetching Pricing Data

```python
from pricing_util import get_bedrock_pricing, get_agentcore_pricing

# Get Bedrock pricing
haiku_pricing = get_bedrock_pricing("haiku", "us-west-2")

# Get AgentCore pricing
agentcore_pricing = get_agentcore_pricing("us-west-2")
```

### Business Value Analysis

```python
from bva_calculator import bva_calculator, bva_what_if_analysis

# Calculate ROI
bva_result = bva_calculator({
    "questions_per_month": 100000,
    "minutes_per_question_without_ai": 10,
    "minutes_per_question_with_ai": 2,
    "percent_questions_that_save_time": 80,
    "ai_agent_cost_per_month": 5000,
    "cost_savings": {
        "labor_cost_per_hour": 100
    },
    "implementation_costs": {
        "one_time_implementation_cost": 100000,
        "one_time_training_cost": 20000
    }
})

# Extract key metrics
summary = bva_result['business_value_summary']
print(f"ROI: {summary['roi_percent']:.1f}%")
print(f"Payback Period: {summary['payback_months']:.1f} months")
print(f"Net Value: ${summary['net_value']:,.2f}")

# Run what-if analysis
what_if_result = bva_what_if_analysis(
    base_params={...},
    primary_variable="questions_per_month",
    primary_range=[50000, 100000, 200000]
)

# Compare scenarios
for scenario in what_if_result['results']:
    print(f"{scenario['scenario']}: ROI = {scenario['roi_percent']:.1f}%")
```

---

## Appendix

### Supported AWS Regions

The tools support all AWS regions where Bedrock and AgentCore are available. Common regions:
- `us-east-1` (N. Virginia)
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)
- `ap-southeast-1` (Singapore)

### Supported Bedrock Models

Use fuzzy matching for model names:
- Claude models: "claude", "haiku", "sonnet", "opus"
- Nova models: "nova"
- Titan models: "titan"
- And more...

Use `get_bedrock_pricing()` to discover available models.

### EMR Deployment Modes

- **EC2**: Traditional cluster with core and task nodes
- **Serverless**: Fully managed, auto-scaling
- **EKS**: Kubernetes-based deployment

### Cost Components

**Bedrock**:
- Input tokens
- Output tokens
- Vector database tokens (added to input)
- Tool tokens (input and output)
- System prompt tokens
- Conversation history tokens

**AgentCore**:
- Runtime (vCPU and memory)
- Browser Tool (compute)
- Code Interpreter (compute)
- Gateway (API calls, indexing)
- Memory (events, storage, retrieval)
- Identity (authentication)

**EMR**:
- EC2 instances (core and task nodes)
- EBS storage
- Data transfer
- Managed scaling

**Business Value Analysis**:
- **Cost Savings**: Labor cost reductions from time efficiency
- **Revenue Growth**: Additional revenue from reallocated employee time
- **Customer Churn Reduction**: Value from improved retention (revenue + acquisition cost avoidance)
- **Implementation Costs**: One-time setup and training investments
- **ROI Metrics**: Return on investment, payback period, net value

### BVA Calculation Methodology

**Time Savings Calculation**:
1. Calculate questions that actually save time (not all questions benefit equally)
2. Compute time saved per question (before AI - after AI)
3. Convert to monthly hours saved
4. Apply to either cost savings or revenue growth (not both)

**Cost Savings**:
- Monthly labor savings = Hours saved × Labor cost per hour
- Net savings = Labor savings - AI agent costs

**Revenue Growth**:
- Time allocated to new projects = Hours saved × % allocated to revenue projects
- Additional revenue = Allocated hours × Revenue per employee per hour

**Customer Churn Reduction**:
- Customers saved = Total customers × (Churn before - Churn after)
- Revenue retained = Customers saved × Monthly revenue per customer
- Acquisition cost avoided = Customers saved × Cost to acquire (20% of annual revenue)
- Total value = Revenue retained + Acquisition cost avoided

**ROI Calculation**:
- Total Benefits = Sum of all value components over analysis period
- Total Costs = One-time implementation costs
- Net Value = Total Benefits - Total Costs
- ROI % = (Net Value / Total Costs) × 100
- Payback Period = Initial Investment / Monthly Net Benefit

### Avoiding Double-Counting in BVA

**Critical Rule**: Time savings from AI are used in both Cost Savings and Revenue Growth calculations. Using both simultaneously would double-count the same benefit.

**Choose Your Approach**:
- **Cost Savings**: Best for organizations focused on operational efficiency and cost reduction
- **Revenue Growth**: Best for organizations where freed-up time generates new revenue
- **Customer Churn Reduction**: Independent benefit that can be combined with either approach

**Valid Combinations**:
- ✅ Cost Savings + Customer Churn Reduction
- ✅ Revenue Growth + Customer Churn Reduction
- ✅ Cost Savings only
- ✅ Revenue Growth only
- ✅ Customer Churn Reduction only
- ❌ Cost Savings + Revenue Growth (double-counts time savings)

---

## Support and Feedback

For issues, questions, or feedback:
1. Check the troubleshooting section
2. Run in debug mode for detailed diagnostics
3. Review calculation explanations for transparency

---

## Version Information

- **Agent Model**: Claude Haiku 4.5
- **Pricing API**: AWS Pricing API (us-east-1)
- **Framework**: Strands Agents + Bedrock AgentCore
- **Python**: 3.8+

---

## License

This tool is provided as-is for AWS cost estimation purposes. Pricing data is fetched in real-time from AWS Pricing API and may change. Always verify costs with AWS billing documentation.
