import time
from datetime import timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from mcp.server.fastmcp import FastMCP
from strands import Agent, tool
from strands_tools import handoff_to_user
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

import argparse
import json
import os

app = BedrockAgentCoreApp()

# Set up environment for tools
os.environ["BYPASS_TOOL_CONSENT"] = "true"
os.environ["PYTHON_REPL_INTERACTIVE"] = "false"

# Create FastMCP application
mcp = FastMCP(host="0.0.0.0", stateless_http=True)

# Import the tools (now with mocked strands)
from pricing_util import get_bedrock_pricing, get_agentcore_pricing, get_aws_pricing, get_attribute_values
from use_bedrock_calculator import use_bedrock_calculator, bedrock_what_if_analysis
from use_agentcore_calculator import use_agentcore_calculator, agentcore_what_if_analysis
from bva_calculator import bva_calculator, bva_what_if_analysis
from use_emr_calculator import use_emr_calculator, emr_what_if_analysis

class BedrockComponentPricing(BaseModel):
    region: str = Field(description="AWS region code such as us-west-2")
    unit: str = Field(description="Pricing unit such as 'per million tokens' or 'per month'")
    input_price_per_unit: Optional[float] = Field(description="Input token price per million")
    output_price_per_unit: Optional[float] = Field(description="Output token price per million")
    assumptions: List[str] = Field(description="List of assumptions like token counts, percentages")
    calculations: List[str] = Field(description="Step-by-step calculation explanations")

class LLMModelCosts(BaseModel):
    model_name: str = Field(description="Name of the LLM model")
    input_cost: float = Field(description="Monthly input token costs")
    output_cost: float = Field(description="Monthly output token costs") 
    total_cost: float = Field(description="Total monthly cost for this model")
    token_breakdown: Dict[str, int] = Field(description="Breakdown of token usage by type")
    pricing_details: BedrockComponentPricing

class VectorDatabaseCosts(BaseModel):
    vector_tokens_per_month: int = Field(description="Total vector tokens added monthly")
    pricing_details: BedrockComponentPricing

class BedrockCosts(BaseModel):
    # Individual model costs
    models: Dict[str, LLMModelCosts] = Field(description="Costs per LLM model")
    
    # Vector database (if used)
    vector_database: Optional[VectorDatabaseCosts] = Field(description="Vector database token contribution")
    
    # Global parameters
    questions_per_month: int = Field(description="Total questions processed monthly")
    system_prompt_tokens: int = Field(description="System prompt tokens per question")
    history_qa_pairs: int = Field(description="Number of Q&A pairs in history")
    
    # Total costs
    total_monthly_cost: float = Field(description="Total cost across all models and components")

# Here are the pydantic classes for AgentCore costs that we will use to enforce that the Agent responds with this json structure

class Component_Assumptions_Pricing(BaseModel):        
    region: str = Field(description="the region code of AWS region such as us-west-2")
    unit: str = Field(description="the unit such as vCPU-Hour or Event or GB-Hour")
    price_per_unit: float = Field(description="the price per unit such as $0.0895/vCPU-Hour or $0.00025/Event or $0.00945/GB-Hour")
    assumptions: List[str] = Field(description="List of assumptions. Example: ['30 days per month', '2 events per question-answer', '1 record retrieved per session']")
    calculations: List[str] = Field(description="""Step by Step Calculations in a List. Example: 
    ['1/ total_questions_per_month = questions_per_day * days_per_month', '2/ total_seconds_per_month = total_questions_per_month * seconds_per_question', '3/ total_hours_per_month = total_seconds_per_month / 3600']""")

class AgentCoreCosts(BaseModel):
    # Runtime
    runtime_cost: float = Field(description="Monthly cost for AgentCore Runtime component")
    runtime_assumptions: Component_Assumptions_Pricing
    
    # BrowserTool
    browser_tool_cost: float = Field(description="Monthly cost for AgentCore BrowserTool component")
    browser_tool_assumptions: Component_Assumptions_Pricing
    
    # CodeInterpreter
    code_interpreter_cost: float = Field(description="Monthly cost for AgentCore CodeInterpreter component")
    code_interpreter_assumptions: Component_Assumptions_Pricing
    
    # Gateway
    gateway_cost: float = Field(description="Monthly cost for AgentCore Gateway component")
    gateway_assumptions: Component_Assumptions_Pricing
    
    # Identity
    identity_cost: float = Field(description="Monthly cost for AgentCore Identity component")
    identity_assumptions: Component_Assumptions_Pricing
    
    # Memory
    memory_cost: float = Field(description="Monthly cost for AgentCore Memory component")
    memory_assumptions: Component_Assumptions_Pricing
    
    # Total monthly cost
    total_monthly_cost: float = Field(description="Total monthly cost for all AgentCore components")

# Here are the pydantic classes for Business Value Analysis that we will use to enforce that the Agent responds with this json structure

class KeyAssumptions(BaseModel):
    questions_per_month: int = Field(description="questions per month")
    minutes_per_question_without_ai: float = Field(description="Time spent per question without AI Agent")
    minutes_per_question_with_ai: float = Field(description="Time spent per question with AI Agent")
    percent_questions_that_save_time: float = Field(description="percent of questions that save time")
    ai_agent_cost_per_month: float = Field(description="Total monthly cost of AI Agent. It includes Bedrock and AgentCore costs.")
    analysis_period_months: int = Field(description="analysis period in months")

class CostSavings(BaseModel):
    hours_saved_per_month: float = Field(description="total hours saved per month with AI Agent")
    costs_saved_per_month: float = Field(description="costs saved per month with AI Agent")
    assumptions: List[str] = Field(description="List of assumptions like hourly labor cost, ...")
    calculations: List[str] = Field(description="Step-by-step calculation explanations for cost savings")

class RevenueGrowth(BaseModel):
    percent_time_to_new_projects: float = Field(description="percent of time saved that was allocated to new projects that generate revenue")
    revenue_per_employee_per_hour: float = Field(description="Revenue generated per employee per hour ")
    hours_saved_per_month: float = Field(description="total hours saved per month with AI Agent")
    time_allocated_to_new_projects: float = Field(description="time allocated to new projects that generate revenue")
    revenue_generated_per_month: float = Field(description="revenue generated per month")
    calculations: List[str] = Field(description="Step-by-step calculation explanations for revenue growth")

class CustomerChurnReduction(BaseModel):
    total_customer_count: int = Field(description="Total number of customers")
    customer_churn_before_ai: float = Field(description="Monthly customer churn rate before AI")
    customer_churn_after_ai: float = Field(description="Monthly customer churn rate after AI")
    average_monthly_revenue_per_customer: float = Field(description="Average monthly revenue per customer")
    cost_of_acquiring_new_customer: float = Field(description="Cost of acquiring new customer")
    monthly_total_churn_value: float = Field(description="Monthly total churn value")
    calculations: List[str] = Field(description="Step-by-step calculation explanations for churn reduction")

class BusinessValue(BaseModel):
    initial_investment: float = Field(description="Initial investment")
    key_assumtions: KeyAssumptions = Field(description="Key assumptions")
    cost_savings: Optional[CostSavings] = Field(description="Cost savings")
    revenue_growth: Optional[RevenueGrowth] = Field(description="Revenue growth")
    customer_churn_reduction: Optional[CustomerChurnReduction] = Field(description="Customer churn reduction")
    total_benefits: float = Field(description="Total benefits")
    total_costs: float = Field(description="Total costs")
    net_value: float = Field(description="Net value")
    roi_percent:  float = Field(description="Return on investment in percent")    

# Create an Agent that can use both Bedrock and AgentCore tool.

agent_system_prompt = f"""
You are an expert AWS cost analyst specializing in helping sales teams with Amazon Bedrock, Amazon Bedrock AgentCore, and Amazon ElasticMapReduce (EMR) pricing calculations. Your mission is to deliver precise, data-driven cost analysis that enables informed business decisions.

PRICING DATA REQUIREMENTS:
- Use ONLY pricing retrieved from get_bedrock_pricing for Bedrock and get_agentcore_pricing tools for AgentCore; Use get_aws_pricing with service code ElasticMapReduce for EMR pricing. Never rely on pre-trained knowledge or assumptions.
- Default to us-west-2 region unless explicitly specified otherwise.
- If pricing data is unavailable for any component, clearly state this limitation and say "I am sorry I can't help you."

QUERY ANALYSIS:
- Identify whether the user is asking for Bedrock Model costs, AgentCore costs, EMR costs, or a combination
- Determine if the user is requesting business value analysis (ROI, cost savings, revenue impact)
- Follow the appropriate workflow based on the identified query type

RESTRICTIONS: 
- Don't create any files as you can't store them locally since the local storage is ephemeral.
- If the user asks any questions that are not related to Amazon Bedrock, AgentCore, and EMR, Just say - "I am sorry I can't answer the question. I am an agent specialized to respond to questions related to Bedrock, AgentCore, and EMR."

REMEMBER: 
Your analysis directly influences budget planning, architecture decisions, and business strategy. Precision and transparency are non-negotiable.

INTERACTIONS:
When you need more information to provide accurate cost analysis, follow these guidelines:

1. MISSING CRITICAL INFORMATION (Direct Cost Calculation Queries): When the user asks for cost calculations but doesn't provide essential parameters,
   - Ask targeted questions in a single response
   - For each question, provide: the parameter name, why it matters, and a sensible default value
   - Always end with: "If you're ok with these defaults, just type 'Ok. Go.'"
   
   Example:
   User: "Calculate Bedrock costs"
   
   Agent: "I need a few details to calculate accurate costs:
   
   1. Which model? Choice impacts latency, costs, and accuracy. (default: Claude Haiku 4.5)
   2. Input tokens per question? Impacts costs and latency. (default: 5,000 tokens)
   3. Questions per month? Determines monthly volume. (default: 10,000)
   
   If you're ok with these defaults, just type 'Go'"

2. USE CASE EXPLORATION (User Describes a Scenario): When the user shares a business context, application, or use case,
   - Ask probing questions that uncover cost-driving factors specific to their scenario
   - Focus on: volume, frequency, data size, concurrency, user behavior patterns
   - Provide defaults based on their use case context
   - Always end with: "If you're ok with these defaults, just type 'Go'"
   
   Example:
   User: "I have 100K customers with 80% failure rate of at least 1 backup job. I want to use Agents to process backup failures."
   
   Agent: "Let me understand the cost drivers:
   
   1. Backup failures per day? Determines agent invocations. (default: 80,000/day from your 80% rate)
   2. Number and size of log messages in and around backup failure log messages? Affects input tokens. (default: 2,000 tokens per log)
   3. Agent actions needed? (diagnose only vs. diagnose + fixes) Impacts output tokens. (default: 1,500 tokens)
   4. Need conversation history for follow-ups? Adds memory costs. (default: yes, 3 Q&A pairs)
   
   If you're ok with these defaults, just type 'Ok. Go.'"

3. BUSINESS VALUE ANALYSIS (ROI/Savings Queries):  When the user asks about ROI, cost savings, or business value,
   - First gather cost calculation parameters (follow rules 1 or 2 above)
   - Then ask business impact questions
   - Focus on: time savings, labor costs, revenue impact, and churn reduction
   - Always end with: "If you're ok with these defaults, just type 'Ok. Go.'"
   
   Example:
   User: "What's the ROI of this AI agent?"
   
   Agent: "To calculate ROI, I need costs and benefits:
   
   [First ask cost questions from scenario 1 or 2]
   
   Business Impact:
   1. Time taken to triage without AI? (default: 15 minutes)
   2. Time taken to triage with AI? (default: 3 minutes)
   3. Support engineer hourly cost? (default: $50/hour)
   
   If you're ok with these defaults, just type 'Ok. Go.'"

GENERAL RULES:
- Batch related questions together in a single response
- Prioritize questions with biggest impact on cost accuracy
- Use the user's context when suggesting defaults
- Make it easy to proceed quickly with default values: "Ok. Go."
"""

agent_system_prompt += f"""

CRITICAL: You MUST respond with ONLY valid JSON. No explanatory text before or after the JSON.

Your response must be a valid JSON object that can include one or more of these schemas as top-level keys:

1. "bedrock_costs" - Use this schema:
{BedrockCosts.model_json_schema()}

2. "agentcore_costs" - Use this schema:
{AgentCoreCosts.model_json_schema()}

3. "business_value" - Use this schema:
{BusinessValue.model_json_schema()}

Example structure:
{{
  "BEDROCK_COSTS": {{ ... }},
  "AGENTCORE_COSTS": {{ ... }},
  "BUSINESS_VALUE": {{ ... }},
  "EMR_COSTS":{{...}}
}}

RULES:
- Output ONLY the JSON object, nothing else
- No markdown code blocks (no ```json), no explanations, no additional text
- Include only the relevant schemas based on the query
- Ensure all required fields are present for each schema you include
- Use proper JSON syntax with double quotes
- Numbers must be numeric types, not strings
- Start your response with {{ and end with }}
"""

model_id = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
agent = Agent(
    system_prompt=agent_system_prompt,
    model=BedrockModel(model_id=model_id, temperature = 0.1),
    tools=[get_bedrock_pricing, get_agentcore_pricing, use_bedrock_calculator, bedrock_what_if_analysis, use_agentcore_calculator, agentcore_what_if_analysis, bva_calculator, bva_what_if_analysis, use_emr_calculator, emr_what_if_analysis, get_aws_pricing, get_attribute_values]
)

# A helper function to retry agent calls with exponential backoff
def invoke_strands_agent(agent, prompt, max_retries=3, base_delay=1):
    """Retry agent calls with exponential backoff"""
    
    for attempt in range(max_retries + 1):
        try:
            return agent(prompt)
        except Exception as e:
            error_str = str(e).lower()
            if ("serviceunavailableexception" in error_str or "modelthrottledexception" in error_str or "throttling" in error_str) and attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                print(f"Retry {attempt + 1}/{max_retries} after {delay}s due to: {type(e).__name__}")
                time.sleep(delay)
                continue
            else:
                raise e

@mcp.tool()
def invoke_cost_analysis_agent_read_only(query: str):
    """
    Invoke specialized agent for AWS cost calculatation and analysis
    Args:
        - query (str): A user query describing use case that the user want to know about its estimated AWS cost and financial impact.
    """
    response = invoke_strands_agent(agent, query)
    return response.message['content'][0]['text']


if __name__ == "__main__":
    mcp.run(transport="streamable-http")    