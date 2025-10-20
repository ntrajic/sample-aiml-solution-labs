from bedrock_agentcore.runtime import (
    BedrockAgentCoreApp,
)  #### AGENTCORE RUNTIME - LINE 1 ####
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import retrieve, current_time
from utils.identity_ssm_utils import get_ssm_parameter
import os

MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"

bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    temperature=0.3,

)


kb_id = get_ssm_parameter("/app/customersupport/agentcore/knowledge_base_id")


system_prompt=f"""
You are an Amazon Returns & Refunds assistant.

Do not answer based on your own knowledge.  
You have access to relevant policy from retrieve from a knowledge base. (KNOWLEDGE_BASE_ID={kb_id})
Retrieve and check the relevant policies firstly.
Use metadata filtering to get policies for proper country where customer had transactions.
[Metadata]
{{
    "country": <ISO2 Country Code> // e.g. "US", "UK", "IN"
}}

When a user asks about returns or refunds, use the content to give accurate advice.
Always be accurate, concise, and do not deviate from known policies.
"""
# Add Memory
from utils.agent_memory import (
    CustomerSupportMemoryHooks,
    memory_client,
    ACTOR_ID,
    SESSION_ID,
)
# Initialize memory via hooks
memory_id = get_ssm_parameter("/app/customersupport/agentcore/memory_id")
memory_hooks = CustomerSupportMemoryHooks(
    memory_id, memory_client, ACTOR_ID, SESSION_ID
)

# Create the agent with all customer support tools and memory
agent = Agent(
    model=bedrock_model,
    tools=[retrieve, current_time],
    system_prompt=system_prompt,
    hooks=[memory_hooks]
)

# Initialize the AgentCore Runtime App
app = BedrockAgentCoreApp()  #### AGENTCORE RUNTIME - LINE 2 ####

@app.entrypoint  #### AGENTCORE RUNTIME - LINE 3 ####
def invoke(payload):
    """AgentCore Runtime entrypoint function"""
    user_input = payload.get("prompt", "")

    # Invoke the agent
    response = agent(user_input)
    return response.message["content"][0]["text"]


if __name__ == "__main__":
    app.run()  #### AGENTCORE RUNTIME - LINE 4 ####
