import json
import time
import os
from urllib.request import urlretrieve
    

def ingest_documents_to_kb(session, kb_id, ds_id, region):
    print("🔄 Starting ingestion job...")
    bedrock_agent = session.client('bedrock-agent', region_name=region)


    job_response = bedrock_agent.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=ds_id
    )
    job_id = job_response['ingestionJob']['ingestionJobId']
    
    # Wait for ingestion to complete
    print("⏳ Waiting for ingestion to complete...")
    while True:
        job_status = bedrock_agent.get_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id,
            ingestionJobId=job_id
        )
        status = job_status['ingestionJob']['status']
        
        if status == 'COMPLETE':
            print("✅ Ingestion completed successfully")
            break
        elif status == 'FAILED':
            failure_reasons = job_status['ingestionJob'].get('failureReasons', ['Unknown error'])
            raise Exception(f"Ingestion failed: {failure_reasons}")
        elif status in ['IN_PROGRESS', 'STARTING']:
            print(f"⏳ Ingestion status: {status}")

            delay = 5 * 2.0
            # nosemgrep: arbitrary-sleep
            time.sleep(delay) # nosemgrep: python.lang.best-practice.arbitrary-sleep
        else:
            print(f"❓ Unexpected status: {status}")
            delay = 5 * 3.0
            # nosemgrep: arbitrary-sleep
            time.sleep(delay) # nosemgrep: python.lang.best-practice.arbitrary-sleep
