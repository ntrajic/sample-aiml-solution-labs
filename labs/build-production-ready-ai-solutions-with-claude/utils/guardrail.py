import uuid

def create_guardrail_if_not_exists(
    session,
    description,
    blocked_input_messaging,
    blocked_output_messaging,
    topic_policy,
    content_policy,
    guardrail_name="AmazonReturnRefundAssistantGuardrail", 
    region_name="us-west-2"
):
    """
    Create a guardrail only if it doesn't already exist by name.
    Uses list_guardrails to check for existing guardrails with the same name.
    
    Args:
        bedrock_client: Bedrock client (optional)
        guardrail_name (str): The name of the guardrail
        region_name (str): AWS region name
        
    Returns:
        str: The guardrail ID if successful, None otherwise
    """
    
    bedrock_client = session.client('bedrock', region_name=region_name)
        
    # First, check if a guardrail with this name already exists
    try:
        print(f"Checking if guardrail '{guardrail_name}' already exists...")
        
        # List all guardrails
        response = bedrock_client.list_guardrails()
        
        # The API might return guardrails under 'guardrailSummaries' or 'guardrails' key
        guardrails_key = None
        if 'guardrailSummaries' in response:
            guardrails_key = 'guardrailSummaries'
        elif 'guardrails' in response:
            guardrails_key = 'guardrails'
        
        if not guardrails_key:
            print(f"Unexpected API response format. Keys: {list(response.keys())}")
            # If we can't find any expected key, assume no guardrails exist
            guardrails = []
        else:
            print(f"Found guardrails under key: {guardrails_key}")
            guardrails = response[guardrails_key]
            
            # Handle pagination if needed
            while 'nextToken' in response:
                response = bedrock_client.list_guardrails(nextToken=response['nextToken'])
                if guardrails_key in response:
                    guardrails.extend(response[guardrails_key])
            
            # Debug information
            print(f"Found {len(guardrails)} existing guardrails")
            
            # Check if our guardrail name already exists
            for guardrail in guardrails:
                # Check different possible field names for the name
                guardrail_name_fields = ['name', 'Name']
                for field in guardrail_name_fields:
                    if field in guardrail and guardrail[field] == guardrail_name:
                        # Try different possible field names for the ID
                        for id_field in ['id', 'guardrailId', 'Id', 'GuardrailId']:
                            if id_field in guardrail:
                                guardrail_id = guardrail[id_field]
                                print(f"Guardrail '{guardrail_name}' already exists with ID: {guardrail_id}")
                                print(f"Full guardrail record: {guardrail}")
                                return guardrail_id
                        
                        # If we found the name but not the ID, print the entire record
                        print(f"Found guardrail with matching name but couldn't identify ID field")
                        print(f"Guardrail record: {guardrail}")
                        return None
            
        print(f"No existing guardrail found with name '{guardrail_name}'. Proceeding to create...")
    
    except Exception as e:
        print(f"Error checking existing guardrails: {e}")
        print("Will attempt to create a new guardrail anyway.")
    
    # If we get here, the guardrail doesn't exist or we couldn't check
    # Generate a unique client request token for each request
    client_request_token = str(uuid.uuid4())
    
    try:
        # Create the guardrail
        response = bedrock_client.create_guardrail(
            name=guardrail_name,
            description=description,
            blockedInputMessaging=blocked_input_messaging,
            blockedOutputsMessaging=blocked_output_messaging,
            topicPolicyConfig=topic_policy,
            contentPolicyConfig=content_policy,
            contextualGroundingPolicyConfig={
                'filtersConfig': [
                    {'type': 'GROUNDING', 'threshold': 0.1},
                    {'type': 'RELEVANCE', 'threshold': 0.1}
                ]
            },
            wordPolicyConfig={
                'wordsConfig': [
                    {'text': 'material weakness'},
                    {'text': 'undisclosed liabilities'},
                    {'text': 'shareholder lawsuit'},
                    {'text': 'SEC investigation'},
                    {'text': 'accounting irregularities'},
                    {'text': 'restate earnings'},
                    {'text': 'liquidity crisis'},
                    {'text': 'bankruptcy risk'},
                    {'text': 'fraudulent activity'},
                    {'text': 'insider trading'}
                ]
            },
            sensitiveInformationPolicyConfig={
                'piiEntitiesConfig': [
                    {'type': 'NAME', 'action': 'ANONYMIZE'},
                    {'type': 'EMAIL', 'action': 'ANONYMIZE'},
                    {'type': 'PHONE', 'action': 'ANONYMIZE'},
                    {'type': 'US_SOCIAL_SECURITY_NUMBER', 'action': 'ANONYMIZE'},
                    {'type': 'ADDRESS', 'action': 'ANONYMIZE'},
                    {'type': 'AGE', 'action': 'ANONYMIZE'},
                    {'type': 'AWS_ACCESS_KEY', 'action': 'ANONYMIZE'},
                    {'type': 'AWS_SECRET_KEY', 'action': 'ANONYMIZE'},
                    {'type': 'CA_HEALTH_NUMBER', 'action': 'ANONYMIZE'},
                    {'type': 'CREDIT_DEBIT_CARD_CVV', 'action': 'ANONYMIZE'},
                    {'type': 'CREDIT_DEBIT_CARD_EXPIRY', 'action': 'ANONYMIZE'},
                    {'type': 'CREDIT_DEBIT_CARD_NUMBER', 'action': 'ANONYMIZE'},
                    {'type': 'DRIVER_ID', 'action': 'ANONYMIZE'},
                    {'type': 'INTERNATIONAL_BANK_ACCOUNT_NUMBER', 'action': 'ANONYMIZE'},
                    {'type': 'IP_ADDRESS', 'action': 'ANONYMIZE'},
                    {'type': 'LICENSE_PLATE', 'action': 'ANONYMIZE'},
                    {'type': 'MAC_ADDRESS', 'action': 'ANONYMIZE'},
                    {'type': 'PASSWORD', 'action': 'ANONYMIZE'},
                    {'type': 'PIN', 'action': 'ANONYMIZE'},
                    {'type': 'SWIFT_CODE', 'action': 'ANONYMIZE'},
                    {'type': 'UK_NATIONAL_HEALTH_SERVICE_NUMBER', 'action': 'ANONYMIZE'},
                    {'type': 'UK_UNIQUE_TAXPAYER_REFERENCE_NUMBER', 'action': 'ANONYMIZE'},
                    {'type': 'URL', 'action': 'ANONYMIZE'},
                    {'type': 'USERNAME', 'action': 'ANONYMIZE'},
                    {'type': 'US_BANK_ACCOUNT_NUMBER', 'action': 'ANONYMIZE'},
                    {'type': 'US_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER', 'action': 'ANONYMIZE'},
                    {'type': 'US_PASSPORT_NUMBER', 'action': 'ANONYMIZE'},
                    {'type': 'VEHICLE_IDENTIFICATION_NUMBER', 'action': 'ANONYMIZE'},
                    {'type': 'US_BANK_ROUTING_NUMBER', 'action': 'ANONYMIZE'}
                ],
                'regexesConfig': [
                    {
                        'name': 'stock_ticker_with_price',
                        'description': 'Stock ticker with price pattern',
                        'pattern': '\\b[A-Z]{1,5}\\s*[@:]\\s*\\$?\\d+(\\.\\d{1,2})?\\b',
                        'action': 'ANONYMIZE'
                    },
                    {
                        'name': 'financial_figures',
                        'description': 'Large financial figures in billions/millions',
                        'pattern': '\\$\\s*\\d+(\\.\\d+)?\\s*(billion|million|B|M)\\b',
                        'action': 'ANONYMIZE'
                    },
                    {
                        'name': 'earnings_per_share',
                        'description': 'EPS figures',
                        'pattern': 'EPS\\s*(of)?\\s*\\$?\\d+\\.\\d{2}',
                        'action': 'ANONYMIZE'
                    },
                    {
                        'name': 'investor_relations_contact',
                        'description': 'Investor relations contact information',
                        'pattern': '(?i)investor\\s*relations\\s*[^\\n]+\\d{3}[\\.-]\\d{3}[\\.-]\\d{4}',
                        'action': 'ANONYMIZE'
                    }
                ]
            },
            tags=[
                {'key': 'Environment', 'value': 'Production'},
                {'key': 'Department', 'value': 'Finance'}
            ],
            clientRequestToken=client_request_token
        )
        
        # Try to get the guardrail ID from the response
        guardrail_id = None
        for field in ['guardrailId', 'id']:
            if field in response:
                guardrail_id = response[field]
                break
        
        print(f"Successfully created guardrail with ID: {guardrail_id}")
        print(f"Guardrail ARN: {response.get('guardrailArn')}")
        print(f"Version: {response.get('version')}")
        
        return guardrail_id
        
    except Exception as e:
        print(f"Error creating guardrail: {e}")
        # Check if it's because the guardrail already exists
        if 'ConflictException' in str(e) and 'already exists' in str(e):
            print("Guardrail with this name already exists. Please check all existing guardrails.")
            # Since we couldn't find it earlier but it exists, list all guardrails again
            try:
                response = bedrock_client.list_guardrails()
                if 'guardrailSummaries' in response:
                    print("Existing guardrails:")
                    for guardrail in response['guardrailSummaries']:
                        print(f"Name: {guardrail.get('name')}, ID: {guardrail.get('id')}")
            except:
                pass
        return None

def create_guardrail_version(
    session,
    guardrail_id, 
    description="Production version 1.0", 
    region_name="us-west-2"
):
    """
    Create a published version of a guardrail.
    
    Args:
        guardrail_id (str): The ID of the guardrail
        description (str): Description of the version
        bedrock_client: Bedrock client (optional)
        region_name (str): AWS region name
        
    Returns:
        str: The version number of the guardrail
    """
    bedrock_client = session.client('bedrock', region_name=region_name)
    
    try:
        # Create guardrail version
        response = bedrock_client.create_guardrail_version(
            guardrailIdentifier=guardrail_id,
            description=description
        )
        
        # Get the version from the response
        version = response.get('version')
        print(f"Successfully created guardrail version: {version}")
        
        return version
    
    except Exception as e:
        print(f"Error creating guardrail version: {e}")
        return None