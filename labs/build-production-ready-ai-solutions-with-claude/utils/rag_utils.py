
def retrieve_and_converse(session, query, model_id, kb_id, region, num_docs = 3, filter=None, reranking=False):

    # Initialize clients
    kb_runtime = session.client("bedrock-agent-runtime", region_name=region)
    bedrock = session.client("bedrock-runtime", region_name=region)

    vectorSearchConfiguration = {
                    "numberOfResults": num_docs if not reranking else num_docs*3
                }
    if filter:
        vectorSearchConfiguration['filter']={
                        'equals':{
                            'key':'country',
                            'value':filter['country']
                        }
                    }
    
    if reranking:
        vectorSearchConfiguration['rerankingConfiguration'] = {
            "bedrockRerankingConfiguration": {
                    "modelConfiguration": {"modelArn": f"arn:aws:bedrock:{region}::foundation-model/cohere.rerank-v3-5:0"},
                    "numberOfRerankedResults": num_docs
                },
                "type": "BEDROCK_RERANKING_MODEL"
        }

    try:
        # Step 1: Retrieve relevant documents from Knowledge Base
        resp = kb_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": vectorSearchConfiguration
            }
        )

        print("=== Retrieved Context ===")
        if "retrievalResults" in resp and resp["retrievalResults"]:
            for i, doc in enumerate(resp["retrievalResults"], 1):
                print(f"\n--- Result {i} ---")
                print(f"Content: {doc['content']['text'][:200]}...")
                print(f"Score: {doc.get('score', 'N/A')}")
                if 'location' in doc:
                    print(f"Source: {doc['location'].get('s3Location', {}).get('uri', 'Unknown')}")
            
            # Step 2: Combine retrieved context for RAG
            context_text = "\n".join([doc['content']['text'] for doc in resp["retrievalResults"]])
            
            # Step 3: Create system prompt with context
            system_prompt = f"""You are an Amazon Returns & Refunds assistant.
    Use the following context to answer questions:
    {context_text}

    DO NOT ANSER BAED ON YOUR KNOWLEDGE. USE THE PROVIDED CONTEXT ONLY.
    """

            # Step 4: Generate response using RAG
            print("\n=== RAG Response ===")
            rag_resp = bedrock.converse(
                modelId=model_id,
                system=[{"text": system_prompt}],
                messages=[
                    {"role": "user", "content": [{"text": query}]}
                ],
                inferenceConfig={"maxTokens": 200}
            )

            for msg in rag_resp["output"]["message"]["content"]:
                print(msg["text"])
                
        else:
            print("No results found in Knowledge Base")

    except Exception as e:
        print(f"An error occurred: {e}")