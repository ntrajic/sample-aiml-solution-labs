import requests
import os
import time

def call_with_your_router(bedrock_runtime_client, prompt_router_arn, query):
    """Use your custom router"""
    messages = [{"role": "user", "content": [{"text": query}]}]
    
    try:
        response = bedrock_runtime_client.converse_stream(
            modelId=prompt_router_arn,
            messages=messages
        )
        
        response_text = ""
        model_used = "unknown"
        tokens = 0
        
        for chunk in response["stream"]:
            if "contentBlockDelta" in chunk:
                response_text += chunk["contentBlockDelta"]["delta"]["text"]
            
            if "metadata" in chunk:
                if "usage" in chunk["metadata"]:
                    tokens = chunk["metadata"]["usage"].get("inputTokens", 50)
                if "trace" in chunk["metadata"]:
                    trace_data = chunk["metadata"]["trace"]
                    # Determine which model was used
                    if "haiku" in str(trace_data).lower():
                        model_used = "haiku"
                    else:
                        model_used = "sonnet"
        
        return response_text, model_used, tokens
        
    except Exception as e:
        print(f"Router error: {e}")
        return "Error", "sonnet", 50  # Fallback


def call_sonnet_directly(bedrock_runtime_client, model_id, query):
    """Always use Sonnet directly"""
    messages = [{"role": "user", "content": [{"text": query}]}]

    try:
        response = bedrock_runtime_client.converse(
            modelId=model_id,
            messages=messages
        )
        
        response_text = response["output"]["message"]["content"][0]["text"]
        tokens = response["usage"]["inputTokens"]
        
        return response_text, "sonnet", tokens
        
    except Exception as e:
        print(f"Direct call error: {e}")
        return "Error", "sonnet", 50

def get_response(bedrock, model_id, prompt):
    messages = [{"role": "user", "content": [{"text": prompt}]}]

    response = bedrock.converse(modelId=model_id, messages=messages)
    usage = response["usage"]
    response_text = response["output"]["message"]["content"][0]["text"]

    return usage["inputTokens"], usage["outputTokens"], response_text
    
# ===== UNOPTIMIZED PROMPTS (Verbose & Wasteful) =====
unoptimized_prompts = [
    """
    Hello there! I hope you're having a wonderful day. I was wondering if you could possibly help me understand something about Amazon's policies. You see, I'm a customer and I have this situation where I need to return an item that I purchased from Amazon recently. I've been thinking about this for a while now and I'm not entirely sure about the whole process. Could you please take your time and explain to me in great detail, step by step, exactly how the return process works on Amazon? I would really appreciate it if you could be very thorough and comprehensive in your explanation. Please include all the relevant information and make sure to cover every aspect of the return process that might be important for me to know. Thank you so much for your assistance and I look forward to your detailed response.
    """,
    """
    Good day! I hope this message finds you well. I am writing to inquire about Amazon Prime membership because I have been considering whether or not it would be beneficial for me to sign up for this service. I have heard many things about it from friends and family, but I would like to get official information directly from a knowledgeable source. Could you please provide me with a comprehensive overview of what Amazon Prime is all about? I would like to know about all the benefits, features, services, and everything else that comes with this membership. Please be as detailed as possible and don't leave anything out. I want to make sure I have all the information I need to make an informed decision about whether this service is right for me and my shopping habits.
    """,
    """
    Hello! I sincerely hope you can assist me today with a question I have regarding Amazon's shipping and delivery policies and procedures. You see, I placed an order on Amazon a few days ago and I'm getting a bit concerned because I haven't received any updates about where my package might be or when it might arrive at my doorstep. I'm starting to worry that something might have gone wrong with the shipment or that there might be some kind of delay that I'm not aware of. Could you please explain to me, in as much detail as possible, exactly how I can track my Amazon order? I would appreciate it if you could walk me through the entire process from start to finish, including all the different ways I can check on my order status and what all the different status updates mean when I see them in my account.
    """
]

# ===== OPTIMIZED PROMPTS (Concise & Efficient) =====
optimized_prompts = [
    "Explain Amazon's return process in steps.",
    "What are Amazon Prime benefits?",
    "How do I track my Amazon order?"
]



def process_on_demand(bedrock, model_id, query):
    """Process immediately with on-demand pricing"""
    messages = [{"role": "user", "content": [{"text": query}]}]

    response = bedrock.converse(modelId=model_id, messages=messages)
    usage = response["usage"]

    return usage["inputTokens"], usage["outputTokens"]

def process_batch(bedrock, model_id, queries):
    """Simulate batch processing (50% cheaper, but delayed)"""
    print("⏳ Submitting batch job...")

    delay = 0.1 * len(queries)
    # nosemgrep: arbitrary-sleep
    time.sleep(delay)
    
    results = []
    for query in queries:
        # In real batch, this would be processed together
        messages = [{"role": "user", "content": [{"text": query}]}]
        response = bedrock.converse(modelId=model_id, messages=messages)
        usage = response["usage"]
        results.append((usage["inputTokens"], usage["outputTokens"]))

    print("✅ Batch job completed!")
    return results

# Large context that will be cached (simulating a large document)
large_context = """
AMAZON COMPREHENSIVE RETURN POLICY DOCUMENTATION

ELECTRONICS RETURN POLICY GUIDE:

Standard Return Windows:
- Most electronics: 30 days from delivery
- Computers and tablets: 30 days  
- Smartphones: 30 days
- TVs over 32": 30 days
- Gaming consoles: 30 days

Detailed Return Process:
1. Sign into your Amazon account
2. Go to "Your Orders" section
3. Find the item and click "Return or replace items" 
4. Select return reason from dropdown menu
5. Choose refund, replacement, or exchange
6. Select return method (UPS pickup, drop-off, mail)
7. Print return label and authorization
8. Package item with ALL original accessories
9. Ship using prepaid label

Refund Processing:
- Processing time: 2-3 business days after receipt
- Credit card refunds: 3-5 additional business days
- Gift card refunds: Usually instant
- Debit card refunds: 5-10 business days
- Original shipping refunded for defects/errors

Electronics Requirements:
- Original packaging strongly recommended
- Include ALL accessories (chargers, cables, manuals)
- Software should remain unaltered
- Minimal wear and tear expected
- Serial numbers must be intact

Restocking Fees:
- Desktop computers: 15% if opened, not defective
- Laptops: 10% if opened, not defective
- Tablets: 15% if opened, not defective
- Large TVs: 15% if opened, not defective
- Gaming consoles: 15% if opened, not defective

Special Considerations:
- Holiday extended returns (until Jan 31)
- Prime member benefits may apply
- International shipping restrictions
- Warranty implications and transfers
- Custom/personalized items generally non-returnable

Customer Service:
Available 24/7 via phone, chat, email
Representatives can make policy exceptions
Escalation procedures available
Multi-language support provided
""" * 4  # Make it substantial for good caching demo

# Global messages array (like in the blog)
messages = []

def clear_message_history():
    messages.clear()  # Start fresh

def converse_with_context(new_message, bedrock_runtime, model_id, add_context=False, cache=False):
    """Converse function following the blog pattern"""
    
    # Add new user message if needed
    if len(messages) == 0 or messages[-1]["role"] != "user":
        messages.append({"role": "user", "content": []})

    # Add large context (simulating document) if requested
    if add_context:
        print("📄 Adding large context (simulating document)...")
        messages[-1]["content"].append({"text": large_context})

    # Add the actual question
    messages[-1]["content"].append({"text": new_message})

    # Add cache point if requested  
    if cache:
        print("🔄 Adding cache point...")
        messages[-1]["content"].append({"cachePoint": {"type": "default"}})

    # Make the API call
    response = bedrock_runtime.converse(modelId=model_id, messages=messages)

    # Extract response
    output_message = response["output"]["message"] 
    response_text = output_message["content"][0]["text"]
    usage = response["usage"]

    # Add assistant response to conversation
    messages.append(output_message)

    return response_text, usage

def generate_conversation(bedrock_client,
                          model_id,
                          system_prompts,
                          messages):
    """
    Sends messages to a model.
    Args:
        bedrock_client: The Boto3 Bedrock runtime client.
        model_id (str): The model ID to use.
        system_prompts (JSON) : The system prompts for the model to use.
        messages (JSON) : The messages to send to the model.

    Returns:
        response (JSON): The conversation that the model generated.

    """

    # Inference parameters to use.
    temperature = 0.5
    top_k = 200

    # Base inference parameters to use.
    inference_config = {"temperature": temperature}
    # Additional inference parameters to use.
    additional_model_fields = {"top_k": top_k}

    # Send the message.
    response = bedrock_client.converse(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields
    )

    # Log token usage.
    token_usage = response['usage']
    
    return response, token_usage

def stream_conversation(bedrock_client,
                    model_id,
                    messages,
                    system_prompts,
                    inference_config,
                    additional_model_fields):
    """
    Sends messages to a model and streams the response.
    Args:
        bedrock_client: The Boto3 Bedrock runtime client.
        model_id (str): The model ID to use.
        messages (JSON) : The messages to send.
        system_prompts (JSON) : The system prompts to send.
        inference_config (JSON) : The inference configuration to use.
        additional_model_fields (JSON) : Additional model fields to use.

    Returns:
        Nothing.

    """

    response = bedrock_client.converse_stream(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields
    )

    stream = response.get('stream')
    if stream:
        for event in stream:

            if 'messageStart' in event:
                print(f"\nRole: {event['messageStart']['role']}")

            if 'contentBlockDelta' in event:
                print(event['contentBlockDelta']['delta']['text'], end="")

            if 'messageStop' in event:
                print(f"\nStop reason: {event['messageStop']['stopReason']}")

            if 'metadata' in event:
                metadata = event['metadata']
                if 'usage' in metadata:
                    print("\nToken usage")
                    print(f"Input tokens: {metadata['usage']['inputTokens']}")
                    print(
                        f":Output tokens: {metadata['usage']['outputTokens']}")
                    print(f":Total tokens: {metadata['usage']['totalTokens']}")
                if 'metrics' in event['metadata']:
                    print(
                        f"Latency: {metadata['metrics']['latencyMs']} milliseconds")

def download_to_data(url, filename):
    os.makedirs("./data", exist_ok=True)

    response = requests.get(url)
    if response.status_code == 200:
        with open(f"./data/{filename}", 'wb') as f:
            f.write(response.content)
        print(f"File '{filename}' downloaded successfully.")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

# Pricing (per 1M tokens)
HAIKU_COST = 0.25    # \$0.25 per 1M tokens
SONNET_COST = 3.00   # \$3.00 per 1M tokens

# Pricing per 1M tokens
INPUT_COST = 3.00
OUTPUT_COST = 15.00

# Pricing for Claude 3.5 Sonnet
CACHE_READ_COST = 0.30

# Pricing per 1M tokens
ON_DEMAND_INPUT = 3.00    # Regular price
ON_DEMAND_OUTPUT = 15.00  

BATCH_INPUT = 1.50        # 50% cheaper!
BATCH_OUTPUT = 7.50       # 50% cheaper!


def router_calculate_cost(model_used, tokens):
    if model_used == "haiku":
        return (tokens / 1_000_000) * HAIKU_COST
    else:
        return (tokens / 1_000_000) * SONNET_COST


def trim_prompt_calculate_cost(input_tokens, output_tokens):
    input_cost = (input_tokens / 1_000_000) * INPUT_COST
    output_cost = (output_tokens / 1_000_000) * OUTPUT_COST
    return input_cost + output_cost


def caching_calculate_cost(usage):
    input_tokens = usage.get("inputTokens", 0)
    output_tokens = usage.get("outputTokens", 0)
    cache_read_tokens = usage.get("cacheReadInputTokens", 0)

    # regular_input_tokens = input_tokens - cache_read_tokens
    # regular_input_cost = (regular_input_tokens / 1_000_000) * INPUT_COST
    regular_input_cost = (input_tokens/1_000_000) * INPUT_COST
    cache_cost = (cache_read_tokens / 1_000_000) * CACHE_READ_COST
    output_cost = (output_tokens / 1_000_000) * OUTPUT_COST
    print(f"input_tokens: {input_tokens} | output_tokens: {output_tokens} | cache_read_tokens: {cache_read_tokens}")
    print(f"regular_input_cost: {regular_input_cost} | cache_cost: {cache_cost} | output_cost: {output_cost}")
    return regular_input_cost + cache_cost + output_cost

def batch_calculate_cost(input_tokens, output_tokens, is_batch=False):
    if is_batch:
        input_cost = (input_tokens / 1_000_000) * BATCH_INPUT
        output_cost = (output_tokens / 1_000_000) * BATCH_OUTPUT
    else:
        input_cost = (input_tokens / 1_000_000) * ON_DEMAND_INPUT
        output_cost = (output_tokens / 1_000_000) * ON_DEMAND_OUTPUT

    return input_cost + output_cost

def print_prompt_router_cost_savings(total_cost_always_sonnet, total_cost_with_router):
    # ===== SAVINGS CALCULATION =====
    savings = total_cost_always_sonnet - total_cost_with_router
    savings_percent = (savings / total_cost_always_sonnet) * 100 if total_cost_always_sonnet > 0 else 0

    print("💰 COST COMPARISON:")
    print(f"  Always Sonnet:    ${total_cost_always_sonnet:.6f}")
    print(f"  Your Router:      ${total_cost_with_router:.6f}")
    print(f"  💸 You Save:       ${savings:.6f} ({savings_percent:.1f}%)")

    print(f"\n🎯 YOUR ROUTER BENEFITS:")
    print(f"  ✅ Simple queries → Haiku (${HAIKU_COST}/1M = 88% cheaper)")
    print(f"  ✅ Complex queries → Sonnet (${SONNET_COST}/1M = Best quality)")
    print(f"  ✅ Automatic selection - no code changes needed")
    print(f"  ✅ Fallback to Sonnet if routing fails")

    print(f"\n📈 POTENTIAL ANNUAL SAVINGS:")
    annual_queries = 100000  # Example: 100K queries per year
    annual_savings = savings * annual_queries
    print(f"  With 100K queries/year: ${annual_savings:.2f} saved!")


def print_prompt_router_cost_savings(unoptimized_total, optimized_total):
    # ===== COST SAVINGS =====
    savings = unoptimized_total - optimized_total
    savings_percent = (savings / unoptimized_total) * 100

    print("💰 COST COMPARISON:")
    print(f"  Unoptimized: ${unoptimized_total:.6f}")
    print(f"  Optimized:   ${optimized_total:.6f}")
    print(f"  You Save:    ${savings:.6f} ({savings_percent:.0f}%)")
    print()

    print("🎯 OPTIMIZATION TECHNIQUES:")
    print("  ❌ Remove: Pleasantries, repetition, unnecessary details")
    print("  ✅ Keep: Clear instruction, specific request, direct language")
    print("  ✅ Result: Same quality answer, much lower cost")
    print()

    print("📈 SCALING IMPACT:")
    daily_queries = 1000
    annual_savings = savings * daily_queries * 365
    print(f"  With 1,000 queries/day: \${annual_savings:.2f}/year saved!")
    print()

    print("🔧 OPTIMIZATION TIPS:")
    print("  1. Be direct: 'Explain X' vs 'Could you please help me understand X'")
    print("  2. Remove fluff: Skip greetings and unnecessary context")
    print("  3. Use bullet points: Organize complex requests clearly")
    print("  4. Specify format: 'List 3 benefits' vs 'Tell me about benefits'")

def print_prompt_caching_results(total_cost_with_cache, total_cost_no_cache):
    # ===== RESULTS =====
    if total_cost_with_cache < total_cost_no_cache:
        savings = total_cost_no_cache - total_cost_with_cache
        savings_percent = (savings / total_cost_no_cache) * 100

        print("💰 COST SUMMARY:")
        print(f"  Without Caching: ${total_cost_no_cache:.5f}")
        print(f"  With Caching:    ${total_cost_with_cache:.5f}")
        print(f"  💸 Savings:      ${savings:.5f} ({savings_percent:.1f}%)")
    else:
        print("❌ Caching may not be working as expected")
        print("   This could indicate the feature is still in limited preview")

    print(f"\n🔍 What to look for:")
    print(f"  ✅ cacheReadInputTokens > 0 in calls 2&3")
    print(f"  ✅ Lower input token costs on cache hits")
    print(f"  ✅ 90% cost reduction: ${CACHE_READ_COST}/1M vs ${INPUT_COST}/1M")


def print_batch_results(on_demand_total, batch_total, customer_queries):
    # ===== COST COMPARISON =====
    savings = on_demand_total - batch_total
    savings_percent = (savings / on_demand_total) * 100

    print("💰 COST COMPARISON:")
    print(f"  On-Demand:  ${on_demand_total:.6f} (Immediate)")
    print(f"  Batch:      ${batch_total:.6f} (Delayed)")
    print(f"  You Save:   ${savings:.6f} ({savings_percent:.0f}%)")
    print()

    print("⚖️ TRADE-OFFS:")
    print("  ON-DEMAND:")
    print("    ✅ Instant response")
    print("    ✅ Real-time customer support")
    print("    ❌ Full price")
    print()
    print("  BATCH:")
    print("    ✅ 50% cheaper")
    print("    ✅ Perfect for bulk processing")
    print("    ❌ Not immediate (minutes/hours delay)")
    print()

    print("📊 WHEN TO USE EACH:")
    print("  On-Demand: Live chat, urgent support, real-time responses")
    print("  Batch: Email responses, daily reports, bulk analysis")
    print()

    # Show annual savings potential
    annual_queries = 50000
    annual_savings = savings * (annual_queries / len(customer_queries))
    print(f"💡 ANNUAL SAVINGS POTENTIAL:")
    print(f"  With 50,000 queries/year: ${annual_savings:.2f} saved!")    