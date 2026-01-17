"""Test [AGENT_NAME] agent

Instructions for using this template:
1. Replace [AGENT_NAME] with your agent's descriptive name (e.g., "product recommendations", "customer support")
2. Replace [agent_module_name] with the actual Python module name containing your agent
3. Update the test_prompt with a relevant example for your use case
4. Optionally add multiple test cases by duplicating the test execution block
5. Customize the output formatting as needed
"""

from [agent_module_name] import agent

# Test configuration
test_prompt = "[INSERT_TEST_PROMPT_HERE]"

# Execute test
print("\n" + "="*70)
print("Testing [AGENT_NAME] Agent")
print("="*70)
print(f"\nPrompt: {test_prompt}\n")

response = agent(test_prompt)

print(f"Response:\n{response}\n")
print("="*70 + "\n")
