---
inclusion: always
---

# AgentCore MCP Workflow - Steering Template

---

## 1. CORE WORKFLOW

### Always Use MCP Tools
- **Type 1** (Strands/AgentCore): Call MCP tool from `aws-bedrock-agentcore` server (e.g., `generate_strands_agent`) → Extract `code` → Save to file
- **Type 2** (Cognito/IAM/Lambda): No MCP tool → Write boto3 script directly

### Agent Generation Rule
```
Prompt says "deploy to runtime"? 
  YES → generate_agentcore_runtime_agent (with @app.entrypoint)
  NO  → generate_strands_agent (everything else)
```

### Reference MCP Handlers
Check `agentcore-mcp-server/handlers/` for correct API methods before writing any code.

---

## 2. CRITICAL DATA STRUCTURES

### Memory Strategies (Tagged Union)
```python
# ✅ CORRECT
[{"summaryMemoryStrategy": {"name": "summary", "namespaces": ["..."]}},
 {"userPreferenceMemoryStrategy": {"name": "preferences", "namespaces": ["..."]}},
 {"semanticMemoryStrategy": {"name": "semantic", "namespaces": ["..."]}}]

# ❌ WRONG
[{"name": "summary", "namespaces": ["..."]}]  # Missing wrapper
```

### Memory Messages (Tuples)
```python
# ✅ CORRECT
[("Hello", "USER"), ("Hi", "ASSISTANT")]

# ❌ WRONG
[{"role": "USER", "content": [{"text": "Hello"}]}]  # Wrong structure
```

### Cognito Discovery URL (IDP Domain)
```python
# ✅ CORRECT
"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/openid-configuration"

# ❌ WRONG
"https://{domain}.auth.{region}.amazoncognito.com/.well-known/openid-configuration"
```

---

## 3. API VALIDATION COMMANDS

**Note:** For boto3 clients, use `hasattr()` to verify methods exist. For library classes, use `inspect.signature()` to see exact parameter names.

**Quick validation approach:**
```bash
# For boto3 - check if method exists (returns True/False)
python -c "import boto3; client = boto3.client('iam'); print(hasattr(client, 'create_role'))"

# For libraries - get exact signature with parameter names
python -c "from bedrock_agentcore.memory import MemoryClient; import inspect; print(inspect.signature(MemoryClient.create_event))"
```

**Why this approach?**
- `hasattr()` returns True/False immediately (no pagination)
- `inspect.signature()` shows exact parameter names for library methods
- Both commands complete instantly without user interaction

### Memory APIs
```bash
# MemoryManager - shows exact signatures
python -c "from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager; import inspect; print('__init__:', inspect.signature(MemoryManager.__init__))"
python -c "from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager; import inspect; print('get_or_create_memory:', inspect.signature(MemoryManager.get_or_create_memory))"
python -c "from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager; import inspect; print('delete_memory:', inspect.signature(MemoryManager.delete_memory))"

# MemoryClient - shows exact signatures
python -c "from bedrock_agentcore.memory import MemoryClient; import inspect; print('__init__:', inspect.signature(MemoryClient.__init__))"
python -c "from bedrock_agentcore.memory import MemoryClient; import inspect; print('create_event:', inspect.signature(MemoryClient.create_event))"
python -c "from bedrock_agentcore.memory import MemoryClient; import inspect; print('retrieve_memories:', inspect.signature(MemoryClient.retrieve_memories))"

# Strands Memory Integration
python -c "from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig; import inspect; print('AgentCoreMemoryConfig:', inspect.signature(AgentCoreMemoryConfig.__init__))"
python -c "from bedrock_agentcore.memory.integrations.strands.config import RetrievalConfig; import inspect; print('RetrievalConfig:', inspect.signature(RetrievalConfig.__init__))"
python -c "from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager; import inspect; print('SessionManager:', inspect.signature(AgentCoreMemorySessionManager.__init__))"
```

### Gateway APIs (boto3)
```bash
# Note: boto3 clients show (*args, **kwargs) - use these to verify methods exist
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); print(hasattr(client, 'create_gateway'))"
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); print(hasattr(client, 'create_gateway_target'))"
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); print(hasattr(client, 'list_gateway_targets'))"
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); print(hasattr(client, 'delete_gateway_target'))"
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); print(hasattr(client, 'delete_gateway'))"
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); print(hasattr(client, 'get_gateway'))"

# Key parameters (from AWS documentation):
# create_gateway: name, roleArn, authorizerConfiguration, protocolType
# create_gateway_target: gatewayIdentifier, targetName, lambdaArn, toolSchema
# list_gateway_targets: gatewayIdentifier
# delete_gateway_target: gatewayIdentifier, targetId
# delete_gateway: gatewayIdentifier
```

### Runtime APIs
```bash
# Runtime Library - shows exact signatures
python -c "from bedrock_agentcore_starter_toolkit import Runtime; import inspect; print('__init__:', inspect.signature(Runtime.__init__))"
python -c "from bedrock_agentcore_starter_toolkit import Runtime; import inspect; print('configure:', inspect.signature(Runtime.configure))"
python -c "from bedrock_agentcore_starter_toolkit import Runtime; import inspect; print('launch:', inspect.signature(Runtime.launch))"
python -c "from bedrock_agentcore_starter_toolkit import Runtime; import inspect; print('status:', inspect.signature(Runtime.status))"
python -c "from bedrock_agentcore_starter_toolkit import Runtime; import inspect; print('invoke:', inspect.signature(Runtime.invoke))"

# Runtime boto3 - verify methods exist
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); print(hasattr(client, 'delete_agent_runtime'))"
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); print(hasattr(client, 'get_agent_runtime'))"
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); print(hasattr(client, 'list_agent_runtimes'))"
```

### IAM APIs (boto3)
```bash
# Note: boto3 clients show (*args, **kwargs) - use these to verify methods exist
python -c "import boto3; client = boto3.client('iam'); print(hasattr(client, 'create_role'))"
python -c "import boto3; client = boto3.client('iam'); print(hasattr(client, 'create_policy'))"
python -c "import boto3; client = boto3.client('iam'); print(hasattr(client, 'attach_role_policy'))"
python -c "import boto3; client = boto3.client('iam'); print(hasattr(client, 'detach_role_policy'))"
python -c "import boto3; client = boto3.client('iam'); print(hasattr(client, 'delete_role'))"
python -c "import boto3; client = boto3.client('iam'); print(hasattr(client, 'delete_policy'))"
python -c "import boto3; client = boto3.client('iam'); print(hasattr(client, 'get_waiter'))"

# Key parameters (from AWS documentation):
# create_role: RoleName, AssumeRolePolicyDocument (JSON string)
# create_policy: PolicyName, PolicyDocument (JSON string)
# attach_role_policy: RoleName, PolicyArn
# detach_role_policy: RoleName, PolicyArn
# delete_role: RoleName
# delete_policy: PolicyArn
```

### STS APIs (boto3)
```bash
python -c "import boto3; client = boto3.client('sts'); print(hasattr(client, 'get_caller_identity'))"
python -c "import boto3; client = boto3.client('sts'); print(hasattr(client, 'assume_role'))"

# Key parameters:
# get_caller_identity: (no parameters)
# assume_role: RoleArn, RoleSessionName
```

### CloudWatch Logs APIs (boto3)
```bash
python -c "import boto3; client = boto3.client('logs'); print(hasattr(client, 'filter_log_events'))"
python -c "import boto3; client = boto3.client('logs'); print(hasattr(client, 'describe_log_groups'))"
python -c "import boto3; client = boto3.client('logs'); print(hasattr(client, 'describe_log_streams'))"
python -c "import boto3; client = boto3.client('logs'); print(hasattr(client, 'get_log_events'))"

# Key parameters:
# filter_log_events: logGroupName, startTime, endTime
# describe_log_groups: logGroupNamePrefix
# describe_log_streams: logGroupName
# get_log_events: logGroupName, logStreamName
```

### Cognito APIs (boto3)
```bash
python -c "import boto3; client = boto3.client('cognito-idp'); print(hasattr(client, 'create_user_pool'))"
python -c "import boto3; client = boto3.client('cognito-idp'); print(hasattr(client, 'create_user_pool_client'))"
python -c "import boto3; client = boto3.client('cognito-idp'); print(hasattr(client, 'create_user_pool_domain'))"
python -c "import boto3; client = boto3.client('cognito-idp'); print(hasattr(client, 'create_resource_server'))"
python -c "import boto3; client = boto3.client('cognito-idp'); print(hasattr(client, 'describe_user_pool'))"
python -c "import boto3; client = boto3.client('cognito-idp'); print(hasattr(client, 'describe_user_pool_domain'))"
python -c "import boto3; client = boto3.client('cognito-idp'); print(hasattr(client, 'describe_user_pool_client'))"
python -c "import boto3; client = boto3.client('cognito-idp'); print(hasattr(client, 'list_resource_servers'))"
python -c "import boto3; client = boto3.client('cognito-idp'); print(hasattr(client, 'delete_user_pool'))"
python -c "import boto3; client = boto3.client('cognito-idp'); print(hasattr(client, 'delete_user_pool_domain'))"

# Key parameters:
# create_user_pool: PoolName, Policies, Schema
# create_user_pool_client: UserPoolId, ClientName, GenerateSecret, AllowedOAuthFlows
# create_user_pool_domain: Domain, UserPoolId
# create_resource_server: UserPoolId, Identifier, Name, Scopes
# describe_user_pool: UserPoolId
# describe_user_pool_client: UserPoolId, ClientId
# delete_user_pool: UserPoolId
```

### Lambda APIs (boto3)
```bash
python -c "import boto3; client = boto3.client('lambda'); print(hasattr(client, 'create_function'))"
python -c "import boto3; client = boto3.client('lambda'); print(hasattr(client, 'add_permission'))"
python -c "import boto3; client = boto3.client('lambda'); print(hasattr(client, 'remove_permission'))"
python -c "import boto3; client = boto3.client('lambda'); print(hasattr(client, 'delete_function'))"
python -c "import boto3; client = boto3.client('lambda'); print(hasattr(client, 'get_function'))"
python -c "import boto3; client = boto3.client('lambda'); print(hasattr(client, 'update_function_code'))"
python -c "import boto3; client = boto3.client('lambda'); print(hasattr(client, 'invoke'))"

# Key parameters:
# create_function: FunctionName, Runtime, Role, Handler, Code
# add_permission: FunctionName, StatementId, Action, Principal
# remove_permission: FunctionName, StatementId
# delete_function: FunctionName
# get_function: FunctionName
# update_function_code: FunctionName, ZipFile or S3Bucket/S3Key
# invoke: FunctionName, Payload
```

---

## 4. MCP TOOLS & TASK MAPPING

| Task | Type | MCP Tool |
|------|------|----------|
| Create agent (testing/dev) | 1 | `generate_strands_agent` |
| Create agent (runtime deploy) | 1 | `generate_agentcore_runtime_agent` |
| Create memory | 1 | `memory_create` |
| Store conversation | 1 | `memory_create_event` |
| Retrieve memories | 1 | `memory_retrieve` |
| Delete memory | 1 | `memory_delete` |
| Create gateway | 1 | `gateway_create` |
| Add Lambda to gateway | 1 | `gateway_add_lambda_target` |
| List gateway targets | 1 | `gateway_list_targets` |
| Delete gateway target | 1 | `gateway_delete_target` |
| Delete gateway | 1 | `gateway_delete` |
| Create IAM role | 1 | `create_runtime_execution_rol` |
| Configure runtime | 1 | `runtime_configure` |
| Launch to runtime | 1 | `runtime_launch` |
| Check runtime status | 1 | `runtime_status` |
| Invoke runtime agent | 1 | `runtime_invoke` |
| Delete runtime | 1 | `runtime_delete` |
| Get dashboard URL | 1 | `observability_get_dashboard_` |
| Get logs info | 1 | `observability_get_logs_info` |
| Get recent logs | 1 | `observability_get_recent_log` |
| Create Cognito | 2 | No MCP - use boto3 |
| Create Lambda | 2 | No MCP - use boto3 |
| Test agent locally | 2 | No MCP - import & test |

---

## 5. REFERENCE TABLES

### Service Clients
| Service | Client/Library |
|---------|---------------|
| Memory (create/delete) | `MemoryManager` from `bedrock_agentcore_starter_toolkit` |
| Memory (store/retrieve) | `MemoryClient` from `bedrock_agentcore.memory` |
| Gateway | `boto3.client('bedrock-agentcore-control')` |
| Runtime (deploy) | `Runtime` from `bedrock_agentcore_starter_toolkit` |
| Runtime (delete) | `boto3.client('bedrock-agentcore-control')` |
| IAM | `boto3.client('iam')` |
| STS | `boto3.client('sts')` |
| CloudWatch Logs | `boto3.client('logs')` |
| Cognito | `boto3.client('cognito-idp')` |
| Lambda | `boto3.client('lambda')` |

### Configuration Files
| File | Contains |
|------|----------|
| `memory_config.json` | memory_id |
| `cognito_config.json` | client_id, client_secret, discovery_url |
| `gateway_config.json` | gateway_id, gateway_url |
| `lambda_config.json` | function_arn, tool_schema |
| `gateway_role_config.json` | role_arn |
| `runtime_execution_role_config.json` | role_arn |
| `runtime_config.json` | agent_arn |

### Default Values
| Parameter | Value |
|-----------|-------|
| Region | `us-west-2` |
| Model | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| Temperature | `0.3` |
| Memory Namespaces | `["semantic", "preferences", "summary"]` |

### Common Mistakes
| ❌ Wrong | ✅ Correct |
|---------|-----------|
| `generate_agentcore_runtime_agent` for testing | `generate_strands_agent` |
| Manually write agent code | Call MCP tool |
| Guess API methods | Check MCP handlers |
| Strategies without wrapper | Use tagged union format |
| Hosted UI domain for OIDC | Use IDP domain |
| Auto-create README files | Only when requested |
| Auto-run tests | Wait for user instruction |

---

## 6. WORKFLOW RULES

### DO NOT
- Manually create Strands agent code or AgentCore scripts
- Execute operations directly
- Guess API method names or parameters
- Create extra documentation files automatically
- Run tests automatically

### ALWAYS
- Call MCP tools for Type 1 tasks
- Extract `code` from tool response and save to file
- Reference MCP handler files for API methods
- Save results to config JSON files
- Use exact parameter names from API validation

### Learning Resources
- **Strands questions** → Use `strands-agents` MCP server
- **AgentCore questions** → Use `bedrock-agentcore-mcp-server` MCP server

---

## 7. EXAMPLE WORKFLOWS

### Example 1: Generate Strands Agent (Type 1)
```
Prompt: "Create a file called 01_generate_agent.py"
Step 1: Call mcp_aws_bedrock_agentcore_generate_strands_agent
Step 2: Extract code from tool response
Step 3: Save code to 01_generate_agent.py
Result: File contains generated Strands agent code
```

### Example 2: Create Cognito (Type 2)
```
Prompt: "Create a script called 08_create_cognito_user_pool.py"
Step 1: No MCP tool available
Step 2: Create Python script using boto3 directly
Step 3: Script creates AWS resource and saves config to JSON
Result: Python script that user will run
```

### Example 3: Deploy to Runtime (Type 1)
```
Prompt: "Deploy to AgentCore Runtime"
Step 1: Call mcp_aws_bedrock_agentcore_generate_agentcore_runtime_agent
Step 2: Extract code from tool response
Step 3: Save code to 17_runtime_agent.py
Result: Agent with @app.entrypoint decorator
```

---

## 8. SUCCESS CHECKLIST

### For Type 1 (MCP-Generated)
- [ ] Called appropriate MCP tool
- [ ] Extracted `code` from response
- [ ] Saved to correct filename
- [ ] File contains generated code (NOT a script that calls MCP)
- [ ] For Strands agents: Code has `from strands import Agent, tool`, `@tool` decorators
- [ ] For AgentCore scripts: Script uses bedrock_agentcore libraries and saves to config files

### For Type 2 (boto3 Direct)
- [ ] Created Python script using boto3
- [ ] Script saves configuration to JSON files
- [ ] Handled errors gracefully
- [ ] Made script rerunnable

---

## 9. API VALIDATION WORKFLOW

**Before writing ANY code that uses APIs:**

1. **Identify the service** (Memory, Gateway, Runtime, etc.)
2. **Find the validation command** in Section 3
3. **Run the command** to see the actual API signature (no pagination!)
4. **Copy exact parameter names** from the signature output
5. **Write your code** using the validated parameters

**Example:**
```bash
# Step 1: Check the API signature
python -c "from bedrock_agentcore.memory import MemoryClient; import inspect; print(inspect.signature(MemoryClient.create_event))"

# Step 2: Output shows: (self, memory_id, actor_id, session_id, messages)
# Step 3: See it expects List[Tuple[str, str]] for messages
# Step 4: Write code with correct format
messages = [("text", "USER"), ("response", "ASSISTANT")]
```

**Why use `inspect.signature()` instead of `help()`?**
- No pagination - output displays immediately
- Shows exact parameter names and types
- No user interaction required
- Perfect for quick API validation

**Key Parameters to Remember:**
- Gateway: `gatewayIdentifier` (not `gateway_id`), `targetId` (not `target_id`)
- Runtime: `agentRuntimeId` (not `agent_id`)
- IAM: `RoleName` (not `role_name`), `PolicyArn` (not `policy_arn`)
- IAM Trust Policy: `AssumeRolePolicyDocument` (JSON string)
- IAM Permissions: `PolicyDocument` (JSON string)

---

**Version**: 1.1 | **Updated**: 2026-02-02
