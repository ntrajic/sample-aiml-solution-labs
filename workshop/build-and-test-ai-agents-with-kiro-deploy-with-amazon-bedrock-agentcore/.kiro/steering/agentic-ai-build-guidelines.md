---
inclusion: always
---

# AgentCore Workshop Guidelines

Quick reference for developing workshop code using Amazon Bedrock AgentCore.

## Core Requirements

### Technology Stack
- **AgentCore Starter Toolkit** + **Strands Agents SDK** + **MCP Tools**
- **Python with UV** package manager 
- **AWS SDK (boto3)** - prefer AWS SDK, Bedrock AgentCore SDK over CLI commands in Python code
- **Use MCP tools** for research and validation

### Code Standards
- **Generate minimal code** that demonstrates core concepts clearly
- **Include educational comments** explaining functionality  in 1 line
- Use type hints and descriptive variable names
- Focus on essential functionality, avoid complex error handling
- When debugging or fixing issues, modify existing code files directly rather than creating new files.


### Reference AgentCore Sample code 
 - Refer below as available agentcore code samples
    - https://github.com/aws/bedrock-agentcore-starter-toolkit/blob/main/documentation/docs/examples/agentcore-quickstart-example.md
    - https://github.com/aws/bedrock-agentcore-starter-toolkit/blob/main/documentation/docs/user-guide/gateway/quickstart.md
    - https://github.com/aws/bedrock-agentcore-starter-toolkit/blob/main/documentation/docs/user-guide/identity/quickstart.md
    - https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/strands-sdk-memory.html
    - https://github.com/aws/bedrock-agentcore-starter-toolkit/blob/main/documentation/docs/user-guide/runtime/quickstart.md

### AgentCore Protocols
- **HTTP**: Port 8080, `/invocations` endpoint
- **MCP**: Port 8000, `/mcp` endpoint  
- **A2A**: Port 9000, root `/` endpoint
- Include `/ping` health check endpoints

### File Management
- **NO documentation files** unless explicitly requested
- **Delete test files** after task completion
- Use educational inline comments instead of separate docs
- Keep workspace clean and organized

### Workshop Focus
- Progressive lab structure building on previous concepts
- Practical, executable examples with clear learning objectives
- Minimal code with maximum educational value
- Real-world scenarios demonstrating AgentCore capabilities

## Quick Checklist
- [ ] Uses AWS SDK, Bedrock AgentCore SDK (not CLI)
- [ ] Includes educational comments
- [ ] Code is minimal and focused
- [ ] Follows AgentCore protocols
- [ ] No unnecessary files created
- [ ] MCP tools used for validation
