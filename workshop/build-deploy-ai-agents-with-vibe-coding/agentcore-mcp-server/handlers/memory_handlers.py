"""
AgentCore Memory Handlers

Implementation of Memory tool handlers for generating memory operation scripts.
"""

from typing import Dict
import json


async def handle_memory_create(args: Dict) -> Dict:
    """Generate script to create AgentCore Memory with strategies"""
    
    region = args.get("region", "us-west-2")
    name = args["name"]
    description = args.get("description", "")
    strategies = args["strategies"]
    
    # Transform strategies to boto3 tagged union format
    # Input format: [{"name": "summary", "namespaces": [...]}]
    # Output format: [{"summaryMemoryStrategy": {"name": "summary", "namespaces": [...]}}]
    transformed_strategies = []
    for strategy in strategies:
        strategy_name = strategy.get("name", "").lower()
        
        if strategy_name == "summary":
            transformed_strategies.append({
                "summaryMemoryStrategy": strategy
            })
        elif strategy_name == "preferences":
            transformed_strategies.append({
                "userPreferenceMemoryStrategy": strategy
            })
        elif strategy_name == "semantic":
            transformed_strategies.append({
                "semanticMemoryStrategy": strategy
            })
        else:
            # Unknown strategy type - pass through as-is
            transformed_strategies.append(strategy)
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to create AgentCore Memory.

This script creates an AgentCore Memory resource with memory strategies.
"""

import json
from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager

# Define memory strategies in boto3 tagged union format
strategies = {json.dumps(transformed_strategies, indent=4)}

# Create memory manager
memory_manager = MemoryManager(region_name='{region}')

# Create memory
print("Creating AgentCore Memory...")
memory = memory_manager.get_or_create_memory(
    name="{name}",
    description="{description}",
    strategies=strategies
)

# Extract memory_id
memory_id = memory["id"]

# Save memory_id to config file
config = {{
    "memory_id": memory_id,
    "name": "{name}",
    "region": "{region}"
}}

with open('memory_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"✓ Memory created successfully!")
print(f"  Memory ID: {{memory_id}}")
print(f"✓ Configuration saved to memory_config.json")
'''
    
    return {
        "code": code,
        "filename": f"{name.replace(' ', '_')}_create.py",
        "instructions": f"Run this script to create the AgentCore Memory resource '{name}'"
    }


async def handle_memory_create_event(args: Dict) -> Dict:
    """Generate script to store conversation messages in Memory"""
    
    region = args.get("region", "us-west-2")
    memory_id = args["memory_id"]
    actor_id = args["actor_id"]
    session_id = args["session_id"]
    messages = args["messages"]
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to store conversation messages in AgentCore Memory.
"""

import json
import time

try:
    from bedrock_agentcore.memory import MemoryClient
except ImportError:
    print("✗ Error: bedrock_agentcore package not found")
    print("  Install with: pip install bedrock-agentcore")
    exit(1)

# Load memory_id from config
with open('memory_config.json') as f:
    config = json.load(f)
    memory_id = config['memory_id']

print(f"Using Memory ID: {{memory_id}}")

# Create memory client
memory_client = MemoryClient(region_name='{region}')

# Define messages
messages = {json.dumps(messages, indent=4)}

# Normalize message format to match notebook expectations
for m in messages:
    if isinstance(m.get("content"), str):
        m["content"] = [{{"text": m["content"]}}]

# Store messages
print("Storing messages in memory...")
memory_client.create_event(
    memory_id=memory_id,
    actor_id="{actor_id}",
    session_id="{session_id}",
    messages=messages
)

print(f"✓ Stored {{len(messages)}} messages successfully!")
print("\\nNote: Memory processing takes 20-30 seconds to extract preferences, facts, and summaries.")
print("Waiting 30 seconds for memory processing...")
time.sleep(30)
print("✓ Memory processing complete!")
'''
    
    return {
        "code": code,
        "filename": f"store_memory_event_{actor_id}.py",
        "instructions": f"Run this script to store conversation messages for {actor_id}"
    }


async def handle_memory_retrieve(args: Dict) -> Dict:
    """Generate script to retrieve memories from Memory"""
    
    region = args.get("region", "us-west-2")
    memory_id = args["memory_id"]
    namespace = args["namespace"]
    query = args["query"]
    top_k = args.get("top_k", 3)
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to retrieve memories from AgentCore Memory.
"""

import json

try:
    from bedrock_agentcore.memory import MemoryClient
except ImportError:
    print("✗ Error: bedrock_agentcore package not found")
    print("  Install with: pip install bedrock-agentcore")
    exit(1)

# Load memory_id from config
with open('memory_config.json') as f:
    config = json.load(f)
    memory_id = config['memory_id']

print(f"Using Memory ID: {{memory_id}}")

# Create memory client
memory_client = MemoryClient(region_name='{region}')

# Retrieve memories using the correct API method
print(f"Retrieving memories from namespace: {namespace}")
print(f"Search query: {query}")
print(f"Top K: {top_k}")
print()

try:
    # Use retrieve_memories() method with correct parameters
    memories = memory_client.retrieve_memories(
        memory_id=memory_id,
        namespace="{namespace}",
        query="{query}",
        top_k={top_k}
    )
    
    if memories:
        print(f"✓ Retrieved {{len(memories)}} memories from '{namespace}' namespace")
        print()
        
        for i, memory in enumerate(memories, 1):
            print(f"Memory {{i}}:")
            print(f"─────────────────────────────────────────")
            content = memory.get('content', {{}})
            if isinstance(content, dict):
                text = content.get('text', 'N/A')
            else:
                text = str(content)
            print(f"Content: {{text}}")
            
            # Safe formatting for relevance score
            relevance = memory.get('relevanceScore', 'N/A')
            if isinstance(relevance, (int, float)):
                print(f"Relevance Score: {{relevance:.3f}}")
            else:
                print(f"Relevance Score: {{relevance}}")
            print()
    else:
        print("⚠️  No memories found")
        print("Memory extraction may still be processing (takes 20-30 seconds)")
        
except Exception as e:
    print(f"❌ Error retrieving memories: {{e}}")
    exit(1)
'''
    
    return {
        "code": code,
        "filename": "retrieve_memories.py",
        "instructions": f"Run this script to retrieve memories from namespace '{namespace}'"
    }


async def handle_memory_delete(args: Dict) -> Dict:
    """Generate script to delete AgentCore Memory"""
    
    region = args.get("region", "us-west-2")
    memory_id = args["memory_id"]
    
    # Generate Python script code
    code = f'''#!/usr/bin/env python3
"""
Script to delete AgentCore Memory.

WARNING: This permanently deletes the memory and all stored data.
RERUNNABLE: Safe to run multiple times - handles missing resources gracefully.
"""

import json
import os
from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager

print("Deleting AgentCore Memory...")

# Check if memory config exists
if not os.path.exists('memory_config.json'):
    print("⚠️  Memory config not found - nothing to delete")
    print("✓ Script completed successfully (no resources to delete)")
    exit(0)

# Load memory_id from config
try:
    with open('memory_config.json') as f:
        config = json.load(f)
        memory_id = config['memory_id']
except Exception as e:
    print(f"⚠️  Failed to load memory config: {{e}}")
    print("✓ Script completed successfully (no resources to delete)")
    exit(0)

# Create memory manager
memory_manager = MemoryManager(region_name='{region}')

# Delete memory
try:
    print(f"  Memory ID: {{memory_id}}")
    memory_manager.delete_memory(memory_id=memory_id)
    print("✓ Memory deleted successfully!")
except Exception as e:
    error_msg = str(e).lower()
    if "not found" in error_msg or "does not exist" in error_msg or "resourcenotfound" in error_msg:
        print("⚠️  Memory already deleted or not found")
        print("✓ Script completed successfully (resource already removed)")
    else:
        print(f"✗ Error deleting memory: {{e}}")
        exit(1)

print("\\n✓ Memory deletion completed successfully")
print("✓ This script is RERUNNABLE - you can safely run it multiple times.")
'''
    
    return {
        "code": code,
        "filename": "delete_memory.py",
        "instructions": f"Run this script to delete the AgentCore Memory resource"
    }
