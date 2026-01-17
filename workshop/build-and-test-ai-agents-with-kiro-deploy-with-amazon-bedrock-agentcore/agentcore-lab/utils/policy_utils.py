"""
Policy utilities for AgentCore Gateway Policies
Provides PolicyClient functionality using boto3 directly
"""

import boto3
import time
from botocore.exceptions import ClientError


class PolicyClient:
    """Client for managing AgentCore Policy Engines and Policies"""
    
    def __init__(self, region_name='us-west-2'):
        self.region_name = region_name
        self.client = boto3.client('bedrock-agentcore-control', region_name=region_name)
    
    def create_or_get_policy_engine(self, name, description):
        """Create a new policy engine or get existing one"""
        try:
            # Try to create new policy engine
            response = self.client.create_policy_engine(
                name=name,
                description=description
            )
            
            engine_id = response['policyEngineId']
            print(f"✅ Policy Engine created: {engine_id}")
            
            # Wait for it to be ready
            self._wait_for_policy_engine_ready(engine_id)
            
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                # Engine already exists, find and return it
                print("ℹ️  Policy engine already exists, retrieving...")
                engines = self.client.list_policy_engines()
                
                for engine in engines.get('policyEngines', []):
                    if engine['name'] == name:
                        print(f"✅ Using existing policy engine: {engine['policyEngineId']}")
                        return engine
                
                raise Exception(f"Policy engine '{name}' exists but could not be found")
            else:
                raise
    
    def _wait_for_policy_engine_ready(self, engine_id, timeout=300):
        """Wait for policy engine to be ready"""
        print("⏳ Waiting for policy engine to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = self.client.get_policy_engine(policyEngineId=engine_id)
            status = response['status']
            
            if status == 'READY':
                print("✅ Policy engine is ready")
                return
            elif status in ['FAILED', 'DELETING']:
                raise Exception(f"Policy engine creation failed with status: {status}")
            
            print(f"   Status: {status}")
            time.sleep(5)
        
        raise Exception(f"Timeout waiting for policy engine to be ready")
    
    def create_or_get_policy(self, policy_engine_id, name, description, definition):
        """Create a new policy or get existing one"""
        try:
            # Try to create new policy
            response = self.client.create_policy(
                policyEngineId=policy_engine_id,
                name=name,
                description=description,
                definition=definition
            )
            
            policy_id = response['policyId']
            print(f"✅ Policy created: {policy_id}")
            
            # Wait for it to be ready
            self._wait_for_policy_ready(policy_engine_id, policy_id)
            
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                # Policy already exists, find and return it
                print("ℹ️  Policy already exists, retrieving...")
                policies = self.client.list_policies(policyEngineId=policy_engine_id)
                
                for policy in policies.get('policies', []):
                    if policy['name'] == name:
                        print(f"✅ Using existing policy: {policy['policyId']}")
                        return policy
                
                raise Exception(f"Policy '{name}' exists but could not be found")
            else:
                raise
    
    def _wait_for_policy_ready(self, engine_id, policy_id, timeout=300):
        """Wait for policy to be ready"""
        print("⏳ Waiting for policy to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = self.client.get_policy(
                policyEngineId=engine_id,
                policyId=policy_id
            )
            status = response['status']
            
            if status == 'READY':
                print("✅ Policy is ready")
                return
            elif status in ['FAILED', 'DELETING']:
                raise Exception(f"Policy creation failed with status: {status}")
            
            print(f"   Status: {status}")
            time.sleep(5)
        
        raise Exception(f"Timeout waiting for policy to be ready")
    
    def delete_policy(self, policy_engine_id, policy_id):
        """Delete a policy"""
        try:
            self.client.delete_policy(
                policyEngineId=policy_engine_id,
                policyId=policy_id
            )
            print(f"✅ Policy {policy_id} deleted")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"ℹ️  Policy {policy_id} not found")
            else:
                raise
    
    def delete_policy_engine(self, policy_engine_id):
        """Delete a policy engine"""
        try:
            self.client.delete_policy_engine(policyEngineId=policy_engine_id)
            print(f"✅ Policy engine {policy_engine_id} deleted")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"ℹ️  Policy engine {policy_engine_id} not found")
            else:
                raise
