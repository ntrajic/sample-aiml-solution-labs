# AgentCore Workshop: Build a Returns & Refunds Agent with Vibe Coding

Welcome! In this workshop, you'll build a production-ready returns and refunds assistant using Strands Agents and Amazon Bedrock AgentCore. 

**The best part?** You'll build everything through vibe coding with Kiro - no manual coding required! Just describe what you want in natural language, and Kiro generates all the code for you. Each section teaches a concept, then you build it by chatting with Kiro. Let's get started!

---

## 🎯 How This Workshop Works

**Vibe Coding = Zero Manual Coding**

In this workshop, you won't write a single line of code manually. Instead:

1. **Copy a prompt** from this guide (they look like: "Create a script called...")
2. **Paste it into Kiro** (your AI coding assistant)
3. **Kiro generates the code** - complete, tested, production-ready
4. **Run the script** - see your agent come to life!

That's it! No syntax errors, no debugging, no googling documentation. Just natural language → working code.

**What You'll Build**

By the end, you'll have:
- A Strands agent with custom tools
- Memory to remember customers
- External API integration via gateway
- Production deployment on AWS
- Monitoring and observability

All built through conversation with Kiro!

---

## Part 1: Build Your First Agent

**What you'll learn**: Create a Strands agent with custom tools for handling returns and refunds.

**How you'll build it**: Simply copy the prompts below and paste them into Kiro. No coding required - Kiro generates everything!

---

### 📚 Learning Prompt 1: Understanding Strands Agents

**Ask Kiro** (just copy and paste this):

```
What is Strands and how do I build agents with it?
```

This helps you understand the framework before diving into code. Kiro will explain it in plain English!

---

### Prompt 1: Create Your Returns & Refunds Agent

**What to ask Kiro** (just copy and paste this):

```
Create a returns and refunds agent with these features:
- Agent name: returns_refunds_agent
- System prompt: You are a helpful returns and refunds assistant. Help customers check return eligibility, calculate refunds, and understand policies. Use the retrieve tool to access Amazon return policy documents for accurate information. Be friendly and accurate.
- Region: us-west-2
- Include the current_time tool
- Include the retrieve tool with Knowledge Base integration:
  - First, retrieve the knowledge base ID from CloudFormation stack 'knowledgebase' (OutputKey: 'KnowledgeBaseId')
  - If CloudFormation retrieval fails, use placeholder '<PLACE-YOUR-KB-ID>'
  - Save knowledge base ID to kb_config.json
  - Configure retrieve tool with the knowledge base ID
- Add 3 custom tools:
  - check_return_eligibility: checks if items can be returned based on purchase date and category
  - calculate_refund_amount: calculates refund based on price, condition, and return reason
  - format_policy_response: formats policy info in a customer-friendly way
- Save to: 01_returns_refunds_agent.py

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro generates a complete Strands agent with all the tools ready to use.

**Expected outcome**: 
- File created: `01_returns_refunds_agent.py`
- File created: `kb_config.json` with knowledge base ID
- Contains: Complete Strands agent code with @tool decorators for all 5 tools (current_time, retrieve, check_return_eligibility, calculate_refund_amount, format_policy_response)
- Knowledge Base: Configured with ID from CloudFormation stack 'knowledgebase'
- Region: All AWS operations use us-west-2
- Ready to run: Can be imported and tested immediately

**Why this matters**: This is your foundation agent with access to Amazon return policy documents. The retrieve tool lets your agent search the knowledge base for accurate policy information. You'll enhance it with memory and external tools in the next steps.

---

### Prompt 2: Test Your Agent

**What to ask Kiro** (just copy and paste this):

```
Create a test script called 02_test_agent.py that tests my returns agent with these questions:
- Import run_agent from 01_returns_refunds_agent.py using importlib
- What time is it?
- Can I return a laptop I purchased 25 days ago?
- Calculate my refund for a $500 item returned due to defect in like-new condition
- Explain the return policy for electronics in a simple way
- Use the retrieve tool to search the knowledge base for 'Amazon return policy for electronics'

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a test script that validates all your agent's tools work correctly, including the retrieve tool accessing the knowledge base.

**Expected outcome**:
- File created: `02_test_agent.py`
- When run: Displays 5 test results showing each tool working
- Output: Agent responses for each test question
- Verification: All 5 tools execute successfully (current_time, check_return_eligibility, calculate_refund_amount, format_policy_response, retrieve)
- Knowledge Base: Retrieve tool successfully queries Amazon return policy documents

**Why this matters**: Always test before moving forward. This ensures your foundation is solid and the knowledge base integration works correctly.

---

## 🚀 Run Your Test

**What to ask Kiro** (just copy and paste this):

```
Execute the test file 02_test_agent.py
```

**What happens**: Kiro runs the test script and shows you the agent's responses to all test questions.

**Expected outcome**:
- All 5 tools execute successfully
- You see real-time responses from your agent
- Knowledge base retrieval returns relevant policy information
- Any errors are displayed for troubleshooting

**Why this matters**: Seeing your agent in action validates everything works before moving to the next step.

---

## Part 2: Add Memory to Remember Customers

**What you'll learn**: Give your agent memory so it remembers customer preferences and past interactions - just like a good customer service rep would!

**How you'll build it**: Keep vibe coding! Just tell Kiro what memory features you want, and it generates the scripts.

---

### 📚 Learning Prompt 2: Understanding AgentCore Memory

**Ask Kiro**:

```
What is AgentCore Memory and how does it help my agent remember things?
```

Learn about the three memory types: summaries (conversation context), preferences (what customers like), and semantic facts (important details).

---

### Prompt 3: Create Memory Storage

**What to ask Kiro**:

```
Create a script called 03_create_memory.py that sets up memory for my returns agent:
- Region: us-west-2
- Memory name: returns_refunds_memory
- Description: Stores customer interactions, preferences, and return history
- Include all three memory strategies: summary, preferences, and semantic
- Save the memory ID to memory_config.json

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script that sets up your memory storage in AWS.

**Expected outcome**:
- File created: `03_create_memory.py`
- When run: Creates AgentCore Memory resource in AWS
- Output: "✓ Memory created successfully! Memory ID: mem-xxxxx"
- File created: `memory_config.json` with memory_id saved
- Time: Takes ~3 minutes to complete

**Why this matters**: Memory lets your agent provide personalized service by remembering each customer - just like how your favorite barista remembers you like oat milk!

---

## 🚀 Run Memory Creation

**What to ask Kiro** (just copy and paste this):

```
Execute the script 03_create_memory.py
```

**What happens**: Kiro runs the script to create your memory storage in AWS.

**Expected outcome**:
- Memory resource created in AWS (takes ~3 minutes)
- Memory ID saved to memory_config.json
- Success message displayed
- Any errors are shown for troubleshooting

**Why this matters**: Verify the memory infrastructure is set up correctly before adding data.

---

### Prompt 4: Add Sample Customer Data

**What to ask Kiro**:

```
Create a script called 04_seed_memory.py that adds sample customer conversations to memory:
- Region: us-west-2
- Customer ID: user_001
- Add a conversation where the customer mentions they prefer email notifications and previously returned a defective laptop
- Add another conversation where they ask about return windows for electronics
- Wait 30 seconds after storing so the memory system can process and extract preferences

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script that populates your memory with realistic test conversations.

**Expected outcome**:
- File created: `04_seed_memory.py`
- When run: Stores sample conversations in memory
- Output: "✓ Stored 2 messages successfully!"
- Wait: Script pauses 30 seconds for memory processing
- Output: "✓ Memory processing complete!"
- Time: Takes ~40 seconds total (10s to store + 30s wait)

**Why this matters**: You need sample data to test if memory retrieval works - can't test a memory system with an empty brain!

---

## 🚀 Run Memory Seeding

**What to ask Kiro** (just copy and paste this):

```
Execute the script 04_seed_memory.py
```

**What happens**: Kiro runs the script to populate memory with sample customer conversations.

**Expected outcome**:
- Sample conversations stored successfully
- 30-second wait for memory processing
- Success confirmation displayed
- Memory system ready for retrieval testing

**Why this matters**: Confirm the data is stored correctly before testing retrieval.

---

### Prompt 5: Test Memory Retrieval

**What to ask Kiro**:

```
Create a script called 05_test_memory.py that:
- Region: us-west-2
- Loads the memory ID from memory_config.json
- Retrieves memories for user_001 from the preferences namespace
- Searches for: 'customer preferences and communication'
- Shows me what the agent remembers about this customer

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script that queries the memory to see what was learned from the conversations.

**Expected outcome**:
- File created: `05_test_memory.py`
- When run: Queries memory for user_001
- Output: "✓ Retrieved X memories from 'semantic' namespace"
- Output: Displays stored preferences and return history
- Verification: Shows the agent can recall customer information
- Time: Takes ~5 seconds

**Why this matters**: Verify memory works before integrating it with your agent.

---

## 🚀 Run Memory Retrieval Test

**What to ask Kiro** (just copy and paste this):

```
Execute the script 05_test_memory.py
```

**What happens**: Kiro runs the script to query and display stored memories.

**Expected outcome**:
- Retrieved memories displayed
- Customer preferences shown
- Return history visible
- Confirms memory retrieval works correctly

**Why this matters**: Validate the memory system can retrieve stored information before integrating with your agent.

---

### Prompt 6: Upgrade Agent with Memory

**What to ask Kiro**:

```
Create a memory-enabled version of my returns agent:
- Agent name: returns_agent_with_memory
- System prompt: You are a personalized returns assistant who remembers customer preferences and history. Use the retrieve tool to access Amazon return policy documents for accurate information.
- Region: us-west-2
- **IMPORTANT: Retain ALL the custom tools from the original agent (check_return_eligibility, calculate_refund_amount, format_policy_response) plus current_time and retrieve**
- Load memory ID from memory_config.json
- Load knowledge base ID from kb_config.json and configure retrieve tool
- Include all three memory namespaces
- Save to: 06_memory_enabled_agent.py

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates an upgraded version of your agent that remembers customers while keeping all the original return/refund tools.

**Expected outcome**:
- File created: `06_memory_enabled_agent.py`
- Contains: All 5 original tools (current_time, retrieve, check_return_eligibility, calculate_refund_amount, format_policy_response) PLUS memory integration
- Ready for: Testing with the next prompt

**Why this matters**: Your agent can now remember each customer's preferences (like "I prefer email") and past interactions (like "returned a defective laptop") while still doing all its original jobs - checking eligibility, calculating refunds, explaining policies, and searching the knowledge base for accurate policy information. It's like upgrading from a helpful assistant to a helpful assistant who actually remembers you!

---

### Prompt 7: Test Memory Integration

**What to ask Kiro**:

```
Create a test script called 07_test_memory_agent.py that:
- Imports the memory-enabled agent
- Sets the memory ID from memory_config.json
- Tests with user_001 asking: 'Hi! I'm thinking about returning something. What do you remember about my preferences?'
- Shows me if the agent recalls their communication preferences and past return history

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a test to verify the agent can actually access and use stored memories in conversation.

**Expected outcome**:
- File created: `07_test_memory_agent.py`
- When run: Imports and tests the memory-enabled agent
- Output: Agent response showing it remembers user_001's preferences
- Output: References to past returns and customer preferences
- Verification: Agent successfully retrieves and uses stored memories
- Time: Takes ~10 seconds

**Why this matters**: Confirm your agent can actually use the stored memories.

---

## 🚀 Run Memory Agent Test

**What to ask Kiro** (just copy and paste this):

```
Execute the script 07_test_memory_agent.py
```

**What happens**: Kiro runs the test to verify your agent can access and use stored memories in conversation.

**Expected outcome**:
- Agent responds with personalized information
- References customer preferences (email notifications)
- Recalls past interactions (defective laptop return)
- Demonstrates memory integration works correctly

**Why this matters**: See your memory-enabled agent in action and confirm it provides personalized service.

---

## Part 3: Connect External Tools via Gateway

**What you'll learn**: Add a Lambda function that looks up real order details from a database, connected securely through a gateway. This is how your agent accesses external systems!

**How you'll build it**: More vibe coding! Describe the Lambda function and gateway setup - Kiro handles all the AWS configuration code.

---

### 📚 Learning Prompt 3: Understanding AgentCore Gateway

**Ask Kiro**:

```
What is AgentCore Gateway and how does it let my agent call external services?
```

Learn how gateways securely connect agents to Lambda functions, APIs, and databases - think of it as a secure phone line between your agent and other systems.

---

### Prompt 8: Set Up Authentication

**What to ask Kiro**:

```
Create a script called 08_create_cognito.py that sets up authentication for my gateway:
- Region: us-west-2
- Create a Cognito User Pool (this is like a secure login system)
- Add a domain prefix for OAuth endpoints (required for token generation)
- Add OAuth support with read/write permissions
- Create an app client for machine-to-machine authentication (so the agent can securely call the gateway)
- Save all the credentials to cognito_config.json with these EXACT keys:
  - user_pool_id: The Cognito User Pool ID
  - domain_prefix: The domain prefix (NOT "domain")
  - client_id: The app client ID
  - client_secret: The app client secret
  - token_endpoint: The OAuth token endpoint URL
  - discovery_url: The OpenID discovery URL
- **CRITICAL**: Use the IDP-based discovery URL format: https://cognito-idp.us-west-2.amazonaws.com/{user_pool_id}/.well-known/openid-configuration (NOT the hosted UI domain format)

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script that sets up secure authentication with OAuth support - think of this as creating a secure ID badge system for your agent.

**Expected outcome**:
- File created: `08_create_cognito.py`
- When run: Creates Cognito User Pool, domain, and app client in AWS
- Output: "✓ User Pool created: pool-xxxxx"
- Output: "✓ Domain created: returns-gateway-xxxxx"
- Output: "✓ Resource server created with scopes"
- Output: "✓ App client created: client-xxxxx"
- File created: `cognito_config.json` with user_pool_id, domain_prefix, client_id, client_secret, token_endpoint, discovery_url
- Time: Takes ~20 seconds

**Why this matters**: Gateways need authentication to ensure only authorized agents can call your tools. The domain is required for OAuth token endpoints to work properly.

---

## 🚀 Run Cognito Setup

**What to ask Kiro** (just copy and paste this):

```
Execute the script 08_create_cognito.py
```

**What happens**: Kiro runs the script to create your authentication system in AWS.

**Expected outcome**:
- Cognito User Pool created (~20 seconds)
- Domain and app client configured
- Credentials saved to cognito_config.json
- Success messages displayed

**Why this matters**: Verify authentication is set up correctly before creating the gateway.

---

### Prompt 9: Create Gateway Permissions

**What to ask Kiro**:

```
Create a script called 09_create_gateway_role.py that:
- Region: us-west-2
- Creates an IAM role for the gateway
- Grants permission to invoke Lambda functions
- Saves the role ARN to gateway_role_config.json

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script that sets up the gateway's permissions.

**Expected outcome**:
- File created: `09_create_gateway_role.py`
- When run: Creates IAM role with Lambda invoke permissions
- Output: "✓ Role created: GatewayExecutionRole-xxxxx"
- Output: "✓ Policy attached: Lambda invoke permissions"
- File created: `gateway_role_config.json` with role_arn
- Time: Takes ~10 seconds

**Why this matters**: The gateway needs permission to call Lambda on behalf of your agent.

---

## 🚀 Run Gateway Role Creation

**What to ask Kiro** (just copy and paste this):

```
Execute the script 09_create_gateway_role.py
```

**What happens**: Kiro runs the script to create the IAM role with Lambda permissions.

**Expected outcome**:
- IAM role created successfully
- Lambda invoke policy attached
- Role ARN saved to gateway_role_config.json
- Ready for gateway creation

**Why this matters**: Confirm the gateway has proper permissions before proceeding.

---

### Prompt 10: Create Order Lookup Function

**What to ask Kiro**:

```
Create a script called 10_create_lambda.py that creates a Lambda function:
- Region: us-west-2
- Function name: OrderLookupFunction
- Purpose: Look up order details by order ID (like ORD-001, ORD-002)
- Returns: order_id, product_name, purchase_date, amount, and whether it's eligible for return
- Use mock data with 3 sample orders: a recent laptop, an old phone, and a defective tablet
- Save Lambda ARN and tool schema to lambda_config.json
- Tool name: lookup_order

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script that deploys a Lambda function with realistic sample orders.

**Expected outcome**:
- File created: `10_create_lambda.py`
- When run: Creates and deploys Lambda function to AWS
- Output: "✓ Lambda function created: OrderLookupFunction"
- Output: "✓ Function ARN: arn:aws:lambda:..."
- File created: `lambda_config.json` with function_arn and tool_schema
- Time: Takes ~20 seconds

**Why this matters**: This external tool lets your agent access order information from a database.

---

## 🚀 Run Lambda Creation

**What to ask Kiro** (just copy and paste this):

```
Execute the script 10_create_lambda.py
```

**What happens**: Kiro runs the script to deploy your Lambda function to AWS.

**Expected outcome**:
- Lambda function deployed successfully
- Function ARN displayed
- Tool schema saved to lambda_config.json
- Ready to connect to gateway

**Why this matters**: Verify the Lambda function is deployed before connecting it to the gateway.

---

### Prompt 11: Create the Gateway

**What to ask Kiro**:

```
Create a script called 11_create_gateway.py that:
- Region: us-west-2
- Creates a gateway named ReturnsRefundsGateway
- Loads Cognito and IAM role config
- Saves gateway ID and URL to gateway_config.json

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script that sets up your gateway.

**Expected outcome**:
- File created: `11_create_gateway.py`
- When run: Creates AgentCore Gateway in AWS
- Output: "✓ Gateway created successfully!"
- Output: "Gateway ID: gw-xxxxx"
- Output: "Gateway URL: https://xxxxx.execute-api.region.amazonaws.com"
- File created: `gateway_config.json` with gateway_id and gateway_url
- Time: Takes ~10 seconds

**Why this matters**: The gateway is the secure bridge between your agent and Lambda function.

---

## 🚀 Run Gateway Creation

**What to ask Kiro** (just copy and paste this):

```
Execute the script 11_create_gateway.py
```

**What happens**: Kiro runs the script to create your AgentCore Gateway in AWS.

**Expected outcome**:
- Gateway created successfully
- Gateway ID and URL displayed
- Configuration saved to gateway_config.json
- Ready to register Lambda targets

**Why this matters**: Confirm the gateway is created before connecting Lambda functions.

---

### Prompt 12: Connect Lambda to Gateway

**What to ask Kiro**:

```
Create a script called 12_add_lambda_to_gateway.py that:
- Region: us-west-2
- Loads gateway and Lambda config
- Registers the OrderLookupFunction as a gateway target
- Names it: OrderLookup

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script that connects your Lambda to the gateway.

**Expected outcome**:
- File created: `12_add_lambda_to_gateway.py`
- When run: Registers Lambda as a gateway target
- Output: "✓ Lambda target added successfully!"
- Output: "Target ID: target-xxxxx"
- Output: "Target Name: OrderLookup"
- Time: Takes ~5 seconds

**Why this matters**: This makes your Lambda function available as a tool for your agent.

---

## 🚀 Run Lambda Registration

**What to ask Kiro** (just copy and paste this):

```
Execute the script 12_add_lambda_to_gateway.py
```

**What happens**: Kiro runs the script to register your Lambda function with the gateway.

**Expected outcome**:
- Lambda registered as gateway target
- Target ID displayed
- Connection confirmed
- Ready for verification

**Why this matters**: Verify the Lambda is connected to the gateway before testing.

---

### Prompt 13: Verify Gateway Setup

**What to ask Kiro**:

```
Create a script called 13_list_gateway_targets.py that:
- Region: us-west-2
- Loads the gateway ID
- Lists all registered targets
- Displays their status

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script to verify your gateway configuration.

**Expected outcome**:
- File created: `13_list_gateway_targets.py`
- When run: Lists all targets registered to gateway
- Output: "✓ Found 1 target(s):"
- Output: "1. OrderLookup"
- Output: "   Target ID: target-xxxxx"
- Output: "   Status: READY"
- Note: May show 0 targets initially due to AWS eventual consistency (this is normal)
- Time: Takes ~5 seconds

**Why this matters**: Always verify setup before integration - it's way easier to fix issues now than after everything's connected!

---

## 🚀 Run Gateway Verification

**What to ask Kiro** (just copy and paste this):

```
Execute the script 13_list_gateway_targets.py
```

**What happens**: Kiro runs the script to list all registered gateway targets.

**Expected outcome**:
- Gateway targets listed
- OrderLookup target displayed with status
- Confirms gateway configuration is correct
- Note: May show 0 targets initially due to AWS eventual consistency

**Why this matters**: Verify all components are connected before creating the full agent.

---

### Prompt 14: Create Full-Featured Agent

**What to ask Kiro**:

```
Create the complete returns agent with memory and gateway:
- Agent name: full_featured_returns_agent
- System prompt: You are a returns assistant with memory and order lookup capabilities. Remember customer preferences, look up order details, and use the retrieve tool to access Amazon return policy documents for accurate information.
- Region: us-west-2
- **IMPORTANT: Retain ALL the custom tools from the original agent (check_return_eligibility, calculate_refund_amount, format_policy_response) plus current_time and retrieve**
- Load configs from: memory_config.json, gateway_config.json, cognito_config.json, kb_config.json
- Include memory and gateway integration
- Configure retrieve tool with knowledge base ID
- Save to: 14_full_agent.py

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro generates your production-ready agent with all features - original tools, memory, and gateway.

**Expected outcome**:
- File created: `14_full_agent.py`
- Contains: All 5 original tools (current_time, retrieve, check_return_eligibility, calculate_refund_amount, format_policy_response) + memory + gateway integration
- Ready to test: Agent can be imported and used immediately
- Capabilities: Remembers customers, looks up orders, processes returns, searches knowledge base for policies
- Ready for: Testing with next prompt

**Why this matters**: This combines everything - memory, custom tools, knowledge base access, and external services into one complete agent.

---

### Prompt 15: Test Complete Agent

**What to ask Kiro**:

```
Create a test script called 15_test_full_agent.py that:
- Loads all configuration files
- Sets up environment variables
- Tests with user_001 asking: 'Hi! Can you look up my order ORD-001 and tell me if I can return it? Remember, I prefer email updates.'
- Verifies the agent can:
  - Remember the customer prefers email (from memory)
  - Look up order ORD-001 details (from Lambda via gateway)
  - Combine both to give a personalized response

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a comprehensive test that shows all three capabilities working together.

**Expected outcome**:
- File created: `15_test_full_agent.py`
- When run: Tests agent with all capabilities
- Output: Agent response showing:
  - Recognition of user_001 (memory working)
  - Order details from Lambda (gateway working)
  - Personalized response combining both
- Verification: All systems working together
- Time: Takes ~15 seconds

**Why this matters**: Verify everything works together before deploying to production - you don't want to discover bugs when real customers are using it!

---

## 🚀 Run Full Agent Test

**What to ask Kiro** (just copy and paste this):

```
Execute the script 15_test_full_agent.py
```

**What happens**: Kiro runs the comprehensive test showing all capabilities working together.

**Expected outcome**:
- Agent responds with personalized information
- Order details retrieved from Lambda
- Memory preferences recalled
- All systems integrated successfully
- Complete response displayed

**Why this matters**: See your complete agent in action with memory, gateway, and knowledge base all working together.

---

## Part 4: Deploy to Production

**What you'll learn**: Deploy your agent to AgentCore Runtime - this is where your agent goes from a local script to a live, scalable service that can handle real customer requests 24/7!

**How you'll build it**: Vibe coding all the way to production! Tell Kiro to deploy, and it generates all the deployment scripts and configuration.

---

### 📚 Learning Prompt 4: Understanding AgentCore Runtime

**Ask Kiro**:

```
What is AgentCore Runtime and how does it deploy my agent to production?
```

Learn about serverless deployment (no servers to manage!), auto-scaling (handles traffic spikes automatically), and built-in monitoring.

---

### Prompt 16: Create Runtime Permissions

**What to ask Kiro**:

```
Create a script called 16_create_runtime_role.py that creates an IAM role for runtime with permissions for:
- Region: us-west-2
- Bedrock model access: Resource "*", Actions: InvokeModel, InvokeModelWithResponseStream
- Memory: bedrock-agentcore:GetMemory, CreateEvent, GetLastKTurns, RetrieveMemory, ListEvents
- Knowledge Base: bedrock-agent:Retrieve (for accessing the knowledge base via retrieve tool)
- CloudWatch: logs:CreateLogGroup, CreateLogStream, PutLogEvents, DescribeLogStreams
- X-Ray: xray:PutTraceSegments, PutTelemetryRecords
- Gateway: bedrock-agentcore:InvokeGateway, GetGateway, ListGatewayTargets
- ECR: ecr:GetAuthorizationToken, BatchCheckLayerAvailability, GetDownloadUrlForLayer, BatchGetImage
- Trust Policy: bedrock-agentcore.amazonaws.com
- Save role ARN to runtime_execution_role_config.json

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script that sets up runtime permissions.

**Expected outcome**:
- File created: `16_create_runtime_role.py`
- When run: Creates IAM role with all required permissions
- Output: "✓ Role created: AgentCoreRuntimeExecutionRole"
- Output: "✓ Policy created: AgentCoreRuntimeExecutionPolicy"
- Output: "✓ Policy attached to role"
- Output: "✓ Role is ready"
- File created: `runtime_execution_role_config.json` with role_arn
- Time: Takes ~20 seconds

**Why this matters**: Runtime needs these permissions to run your agent and access AWS services.

---

## 🚀 Run Runtime Role Creation

**What to ask Kiro** (just copy and paste this):

```
Execute the script 16_create_runtime_role.py
```

**What happens**: Kiro runs the script to create the IAM role with all runtime permissions.

**Expected outcome**:
- IAM role created successfully
- All policies attached (Bedrock, Memory, Knowledge Base, CloudWatch, X-Ray, Gateway, ECR)
- Role ARN saved to runtime_execution_role_config.json
- Ready for agent deployment

**Why this matters**: Verify runtime permissions are set up correctly before deploying your agent.

---

### Prompt 17: Prepare Agent for Runtime

**What to ask Kiro**:

```
Create the runtime-ready version of my agent:
- Agent name: returns_agent_runtime
- System prompt: Production returns assistant with full memory and gateway capabilities. Use the retrieve tool to access Amazon return policy documents for accurate information.
- Region: us-west-2
- **IMPORTANT: Retain ALL the custom tools from the original agent (check_return_eligibility, calculate_refund_amount, format_policy_response) plus current_time and retrieve**
- Load all configs: memory, gateway, cognito, kb_config
- Include memory and gateway integration
- Configure retrieve tool with knowledge base ID
- Add comprehensive error handling to catch and log any failures
- Save to: 17_runtime_agent.py

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro generates a production-optimized agent with all original tools plus memory and gateway.

**Expected outcome**:
- File created: `17_runtime_agent.py`
- Contains: All 5 original tools (current_time, retrieve, check_return_eligibility, calculate_refund_amount, format_policy_response) + memory + gateway + @app.entrypoint decorator
- Structure: BedrockAgentCoreApp format for runtime deployment
- Knowledge Base: Configured with ID from kb_config.json
- Ready for: Deployment to AgentCore Runtime
- Note: This file is NOT run directly - it's deployed by the next script

**Why this matters**: Runtime agents need specific structure and configuration while maintaining all functionality including knowledge base access.

---

### Prompt 18: Create Dependencies File

**What to ask Kiro**:

```
Create a requirements.txt file for my agent with these packages:
- strands-agents (latest version)
- strands-agents-tools (latest version)
- bedrock-agentcore (latest version)
- boto3 (latest version)
- Any other dependencies needed for the runtime agent

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates the dependencies file that tells AWS which Python packages to install.

**Expected outcome**:
- Output: "✓ Requirements file created"
- File created: `requirements.txt` with all dependencies
- Contains: strands, bedrock-agentcore, boto3, etc.
- Time: Takes ~5 seconds

**Why this matters**: Runtime needs to know which packages to install.

---

### Prompt 19: Deploy to Production

**What to ask Kiro**:

```
Create a script called 19_deploy_agent.py that:
- Loads all configuration files (memory, gateway, cognito, runtime execution role, kb_config)
- Configures runtime deployment settings:
  - Entrypoint: 17_runtime_agent.py
  - Agent name: returns_refunds_agent
  - Execution role from config
  - Cognito authentication
  - Region: us-west-2
- Sets environment variables for memory, gateway, cognito, and knowledge base (KNOWLEDGE_BASE_ID from kb_config.json)
- Deploys to AgentCore Runtime
- Saves agent ARN to runtime_config.json

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script that configures and deploys your agent to AWS in one step.

**Expected outcome**:
- File created: `19_deploy_agent.py`
- When run: Starts deployment process
- Output: "LAUNCHING AGENT TO AGENTCORE RUNTIME"
- Output: "⏱️ Expected time: 5-10 minutes"
- Output: "☕ Grab a coffee while the deployment runs..."
- Process: Creates CodeBuild project, builds Docker container, pushes to ECR, deploys
- Output: "✓ Agent deployment initiated!"
- Output: "Agent ARN: arn:aws:bedrock-agentcore:..."
- File created: `runtime_config.json` with agent_arn
- Time: Takes ~5 minutes

**Why this matters**: This is the moment your agent goes live!

---

## 🚀 Run Agent Deployment

**What to ask Kiro** (just copy and paste this):

```
Execute the script 19_deploy_agent.py
```

**What happens**: Kiro runs the deployment script to launch your agent to production (takes 5-10 minutes).

**Expected outcome**:
- Deployment initiated successfully
- CodeBuild project created
- Docker container built and pushed to ECR
- Agent deployed to AgentCore Runtime
- Agent ARN saved to runtime_config.json
- Time: ~5-10 minutes (grab a coffee!)

**Why this matters**: Your agent is now going live in production - this is the big moment!

---

### Prompt 20: Monitor Deployment

**What to ask Kiro**:

```
Create a script called 20_check_status.py that:
- Region: us-west-2
- Checks deployment status
- Monitors until READY or FAILED
- Displays current state

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script to monitor your deployment.

**Expected outcome**:
- File created: `20_check_status.py`
- When run: Checks agent deployment status
- Output (if still deploying): "⏳ Agent deployment in progress..."
- Output (if ready): "✓ Agent is READY to receive requests!"
- Output (if failed): "✗ Agent deployment failed! Check CloudWatch logs"
- Shows: Endpoint details and status
- Time: Takes ~5 seconds per check
- Note: Run multiple times until status shows READY

**Why this matters**: Deployment takes 5-10 minutes - this script lets you track progress instead of wondering if it's working!

---

## 🚀 Run Status Check

**What to ask Kiro** (just copy and paste this):

```
Execute the script 20_check_status.py
```

**What happens**: Kiro runs the script to check your agent's deployment status.

**Expected outcome**:
- Current deployment status displayed
- If still deploying: "⏳ Agent deployment in progress..."
- If ready: "✓ Agent is READY to receive requests!"
- If failed: Error details displayed
- Note: Run multiple times until status shows READY

**Why this matters**: Monitor deployment progress and know when your agent is ready to test.

---

### Prompt 21: Test Production Agent

**What to ask Kiro**:

```
Create a script called 21_invoke_agent.py that:
- Loads Cognito credentials from cognito_config.json
- Gets an OAuth token for authentication
- Invokes the deployed agent with user_001 asking: 'Can you look up my order ORD-001 and help me with a return?'
- Displays the full response

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script to test your live production agent with a realistic customer query.

**Expected outcome**:
- File created: `21_invoke_agent.py`
- When run: Invokes production agent
- Output: "✓ OAuth token obtained"
- Output: "Invoking agent..."
- Output: "✓ AGENT RESPONSE"
- Shows: Complete agent response with refund policy information
- Verification: Production agent is working correctly
- Time: Takes ~10 seconds

**Why this matters**: Verify your production agent works correctly.

---

## 🚀 Run Production Test

**What to ask Kiro** (just copy and paste this):

```
Execute the script 21_invoke_agent.py
```

**What happens**: Kiro runs the script to test your live production agent with a real customer query.

**Expected outcome**:
- OAuth token obtained successfully
- Agent invoked in production
- Complete response displayed
- Shows memory, gateway, and knowledge base working together
- Confirms production agent is fully operational

**Why this matters**: Validate your production agent handles real requests correctly before going live to customers.

---

## Part 5: Monitor and Debug

**What you'll learn**: Access monitoring dashboards and logs to track performance and debug issues - because even the best agents need health checkups!

---

### 📚 Learning Prompt 5: Understanding Observability

**Ask Kiro**:

```
How do I monitor my deployed agent and view its logs?
```

Learn about CloudWatch dashboards (your agent's health monitor), traces (see exactly what your agent is doing), and log analysis (debug when things go wrong).

---

### Prompt 22: Access Monitoring Dashboard

**What to ask Kiro**:

```
Create a script called 22_get_dashboard.py that:
- Region: us-west-2
- Gets the CloudWatch GenAI Observability dashboard URL
- Displays the link to access monitoring

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script that gives you the dashboard URL.

**Expected outcome**:
- File created: `22_get_dashboard.py`
- When run: Retrieves dashboard URL
- Output: "CloudWatch GenAI Observability Dashboard"
- Output: "URL: https://console.aws.amazon.com/cloudwatch/..."
- Shows: Direct link to monitoring dashboard
- Time: Takes ~2 seconds

**Why this matters**: The dashboard shows performance metrics, request traces, and usage patterns - it's like a fitness tracker for your agent!

---

## 🚀 Run Dashboard Access

**What to ask Kiro** (just copy and paste this):

```
Execute the script 22_get_dashboard.py
```

**What happens**: Kiro runs the script to retrieve your monitoring dashboard URL.

**Expected outcome**:
- Dashboard URL displayed
- Direct link to CloudWatch GenAI Observability
- Ready to view performance metrics
- Access to request traces and usage patterns

**Why this matters**: Get quick access to your agent's health monitoring dashboard.

---

### Prompt 23: Access Agent Logs

**What to ask Kiro**:

```
Create a script called 23_get_logs_info.py that:
- Region: us-west-2
- Loads agent ARN from runtime_config.json
- Gets the CloudWatch log group information
- Displays the log group name and AWS CLI commands for viewing logs

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script that gives you the log group information and commands to view logs.

**Expected outcome**:
- File created: `23_get_logs_info.py`
- When run: Retrieves log group information
- Output: "CloudWatch Log Group Information"
- Output: "Log Group: /aws/bedrock-agentcore/..."
- Output: "Agent ARN: arn:aws:..."
- Shows: AWS CLI commands for tailing and viewing logs
- Time: Takes ~2 seconds

**Why this matters**: Logs help you debug issues and understand agent behavior - this gives you the log group name and commands to access them whenever you need!

---

## 🚀 Run Log Info Retrieval

**What to ask Kiro** (just copy and paste this):

```
Execute the script 23_get_logs_info.py
```

**What happens**: Kiro runs the script to get your log group information and CLI commands.

**Expected outcome**:
- Log group name displayed
- Agent ARN shown
- AWS CLI commands provided for viewing logs
- Ready to tail and search logs

**Why this matters**: Get the information you need to access and search your agent's logs for debugging.

---

## Part 6: Clean Up

**What you'll learn**: Remove all AWS resources to avoid ongoing costs - because nobody likes surprise bills!

---

### Prompt 24: Delete AWS Resources

**What to ask Kiro**:

```
Create a script called 24_cleanup_aws.py that safely deletes all the AWS resources we created:
- Region: us-west-2
- Runtime agent (the deployed agent)
- Gateway targets FIRST, then wait 5 seconds before deleting the gateway (proper deletion order)
- Memory resource (stored customer data)
- Lambda function and its IAM roles (the order lookup function)
- Cognito domain FIRST, then user pool (proper deletion order)
- IAM roles (all permissions we created)
- ECR repository (Docker container storage)
- Include a 5-second warning before deletion so I don't accidentally delete everything
- Handle missing resources gracefully (don't error if something's already gone)

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a comprehensive cleanup script that removes everything in the proper order.

**Expected outcome**:
- File created: `24_cleanup_aws.py`
- When run: Shows 5-second warning countdown
- Output: "⚠️ WARNING: This will delete all AWS resources"
- Output: "Deleting runtime agent..."
- Output: "✓ Runtime agent deleted"
- Output: "Deleting gateway targets..."
- Output: "✓ Gateway targets deleted"
- Output: "Waiting 5 seconds before deleting gateway..."
- Output: "✓ Gateway deleted"
- Output: "Deleting memory..."
- Output: "✓ Memory deleted"
- Output: "Deleting Lambda..."
- Output: "✓ Lambda deleted"
- Output: "Deleting Cognito domain..."
- Output: "✓ Cognito domain deleted"
- Output: "Deleting Cognito user pool..."
- Output: "✓ Cognito user pool deleted"
- Output: "Deleting IAM roles..."
- Output: "✓ All AWS resources cleaned up"
- Time: Takes ~70 seconds (includes wait times for proper deletion)
- Note: Handles missing resources gracefully (no errors if already deleted)

**Why this matters**: Avoid unexpected AWS charges by cleaning up workshop resources - AWS bills can add up fast if you leave things running! Proper deletion order prevents errors.

**WARNING**: This permanently deletes everything. Make sure you've saved any important data!

---

## 🚀 Run AWS Cleanup

**What to ask Kiro** (just copy and paste this):

```
Execute the script 24_cleanup_aws.py
```

**What happens**: Kiro runs the cleanup script to delete all AWS resources (with a 5-second warning).

**Expected outcome**:
- 5-second warning countdown displayed
- All AWS resources deleted in proper order
- Runtime agent, gateway, memory, Lambda, Cognito, IAM roles removed
- Success confirmations for each deletion
- Time: ~70 seconds (includes wait times)
- No ongoing AWS charges

**Why this matters**: Avoid unexpected AWS bills by removing all workshop resources.

---

### Prompt 25: Clean Up Local Files

**What to ask Kiro**:

```
Create a script called 25_cleanup_files.py that deletes:
- All Python scripts (01-25)
- All config JSON files
- Runtime configuration files
- Docker files
- Requirements file
- Generated agent files
- .bedrock_agentcore.yaml file
- Include a 5-second warning
- Handle missing files gracefully

⚠️ VALIDATION:
1. Identify task type and determine which MCP tool to use (or boto3 if Type 2)
2. Call MCP tool FIRST - extract and save the generated code
3. Validate APIs: Check method signatures using help() before using any boto3/library APIs
4. If MCP fails, STOP and ask user for permission - do NOT create code manually
```

**What happens**: Kiro creates a script to clean up your workspace.

**Expected outcome**:
- File created: `25_cleanup_files.py`
- When run: Shows 5-second warning countdown
- Output: "⚠️ WARNING: This will delete all local files"
- Output: "Deleting Python scripts..."
- Output: "✓ Deleted 25 Python files"
- Output: "Deleting config files..."
- Output: "✓ Deleted 8 JSON files"
- Output: "Deleting runtime files..."
- Output: "✓ Workspace cleaned up"
- Time: Takes ~5 seconds
- Result: Clean workspace ready for next workshop

**Why this matters**: Return your workspace to a clean state after the workshop - start fresh next time without old files cluttering things up!

---

## 🚀 Run File Cleanup

**What to ask Kiro** (just copy and paste this):

```
Execute the script 25_cleanup_files.py
```

**What happens**: Kiro runs the cleanup script to delete all local workshop files (with a 5-second warning).

**Expected outcome**:
- 5-second warning countdown displayed
- All Python scripts deleted (01-25)
- All config JSON files removed
- Runtime and Docker files cleaned up
- Clean workspace ready for next time
- Time: ~5 seconds

**Why this matters**: Clean workspace means no confusion when you start your next project.

---

## 🎉 Congratulations!

You've built a complete, production-ready returns and refunds agent with:
- ✅ Custom tools for returns processing
- ✅ Memory to remember customers
- ✅ External order lookup via gateway
- ✅ Production deployment on AgentCore Runtime
- ✅ Monitoring and observability

**And you did it all through vibe coding!** No manual coding, no wrestling with syntax errors, no debugging cryptic error messages. Just natural language conversations with Kiro that generated production-ready code.

Your agent can now:
- Check return eligibility
- Calculate refunds
- Look up order details
- Remember customer preferences
- Provide personalized service

---

## Quick Reference

**Configuration Files Created**:
- `memory_config.json` - Memory ID
- `cognito_config.json` - Authentication
- `gateway_role_config.json` - Gateway permissions
- `lambda_config.json` - Lambda details
- `gateway_config.json` - Gateway connection
- `runtime_execution_role_config.json` - Runtime permissions
- `runtime_config.json` - Deployed agent ARN

**Key Concepts**:
- **Strands**: Framework for building AI agents
- **Memory**: Stores customer preferences and history
- **Gateway**: Secure bridge to external services
- **Runtime**: Serverless production deployment
- **Observability**: Monitoring and debugging tools

---

## Need Help?

- **Learning prompts**: Ask Kiro to explain concepts in plain English
- **Documentation**: Use MCP servers to search docs
- **Debugging**: Check logs and monitoring dashboard
- **Issues**: Review error messages and retry
- **Stuck?**: Just ask Kiro "Can you help me with [problem]?" - it's that simple!

## What You Just Experienced

This workshop showcased **vibe coding** - a new way to build software where you describe what you want in natural language, and AI generates production-ready code. No syntax to memorize, no boilerplate to write, no stack traces to debug. Just ideas to working code.

You went from zero to a production AI agent in 25 prompts, all through conversation. That's the power of vibe coding with Kiro!

Happy building! 🚀
