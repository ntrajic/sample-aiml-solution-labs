"""
[AGENT_NAME] Agent Template

[BRIEF_DESCRIPTION]

Usage:
    python [agent_filename].py
    
    Or programmatically:
    from [agent_filename] import invoke_agent
    invoke_agent("[example query]")
"""

from strands import Agent
from strands.models import BedrockModel
from strands_tools import [TOOL_IMPORTS]  # e.g., retrieve, search, etc.

# For Bedrock Knowledge Bases, use the retrieve tool

# Configuration Constants
[CONFIG_CONSTANTS] = "[VALUES]"  # e.g., KB_ID, API_ENDPOINT, etc.

# Configure Model
model = BedrockModel(
    model_id="[MODEL_ID]",  # e.g., us.anthropic.claude-3-5-haiku-20241022-v1:0
    temperature=[TEMPERATURE],  # 0.0-1.0, lower for factual, higher for creative
)

# System Prompt
SYSTEM_PROMPT = f"""You are a [ROLE_DESCRIPTION] assistant. Your role is to [PRIMARY_OBJECTIVE].

When a [user/customer] [ACTION_TRIGGER]:
1. [STEP_1]
2. [STEP_2] - Use [tool_name] with parameters:
   - param1: [description]
   - param2: [description]
   - filters: [if applicable]
3. [STEP_3]
4. [ADDITIONAL_GUIDELINES]

Always be [TONE_ATTRIBUTES]."""

# Create Agent
agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[[TOOL_LIST]]  # e.g., [retrieve, custom_tool]
)

def main():
    """Main function to run the agent."""
    print("[AGENT_DISPLAY_NAME]")
    print("=" * 50)
    print("[WELCOME_MESSAGE]")
    print("Type 'exit' or 'quit' to end the conversation.\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['exit', 'quit']:
            print("[GOODBYE_MESSAGE]")
            break
        
        if not user_input:
            continue
        
        try:
            response = agent(user_input)
            print(f"\nAssistant: {response}\n")
        except Exception as e:
            print(f"\nError: {str(e)}\n")

if __name__ == "__main__":
    main()
