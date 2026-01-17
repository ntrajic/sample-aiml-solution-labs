import os, time, boto3, json
from strands import tool
from typing import Optional, List, Dict, Any

# helper function. Not used.
def print_pricing_response(response, filename, mode):
    """Overwrite or append pricing response to JSON file"""
    
    # print(f"Products: {len(response.get('PriceList', []))}")
    # print(f"Next Token: {response.get('NextToken', 'None')}")
    
    # Convert response for JSON serialization
    json_response = {
        "timestamp": datetime.now().isoformat(),
        "next_token": response.get('NextToken'),
        "price_list": [json.loads(item) for item in response.get('PriceList', [])]
    }
    
    # Overwrite file
    try:
        if mode == 'w' :
            # Write directly to file (overwrite)
            with open(filename, 'w') as f:
                json.dump(json_response, f, indent=2)
            
            print(f"✅ Overwritten {filename}")
        else :
            # Append to file
            with open(filename, 'a') as f:
                json.dump(json_response, f, indent=2)
                f.write('\n')  # Add a newline for readability

            print(f"✅ Appended to {filename}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def find_descriptions(obj):
    """Generator that yields all 'description' values"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'description':
                yield value
            else:
                yield from find_descriptions(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from find_descriptions(item)


@tool
def get_bedrock_pricing(model_name: str, region: str = 'us-west-2') -> List[Dict]:
    """
    Retrieve pricing information for Amazon Bedrock models using AWS Pricing API.
    
    This function searches for Bedrock model pricing using fuzzy matching on model names
    and returns structured pricing data including input/output token costs, cache pricing,
    and usage types. Supports pagination to retrieve all available pricing data.
    
    Args:
        model_name (str): Partial or complete model name for fuzzy matching.
                         Examples: 'claude', 'haiku', 'sonnet', 'nova', 'titan', 'gpt'
                         Case-insensitive matching against AWS model identifiers. Sometimes you may have to pass a substring such as gpt instead of gpt 20B or 120B instead of oss 120B
        region (str, optional): Target AWS region for pricing lookup. 
                               Defaults to 'us-west-2'.
                               Note: Pricing API queries from us-east-1 but returns 
                               region-specific pricing.
    
    Returns:
        List[Dict]: List of dictionaries containing pricing information for matching models.
                   Each dictionary includes:                   
                   - model_name (str): Human-readable model name
                   - regionCode (str): Target AWS region                   
                   - price_per_unit (float): Cost per unit in USD
                   - unit (str): Pricing unit (e.g., '1K tokens')
                   - effective_date (str): Pricing effective date
    
    Raises:
        Exception: Captures and logs AWS API errors, returns empty list on failure.
    
    Notes:
        - Uses AWS Pricing API which only operates from us-east-1 region
        - Implements pagination to retrieve all available pricing data
        - Automatically switches between 'AmazonBedrock' and 'AmazonBedrockFoundationModels'
          service codes based on model type (Claude models use Foundation Models service)
        - Filters for On-demand Inference pricing only
        - Removes duplicate entries based on model_id, unit, and description
        - Results are sorted alphabetically by model_id
    
    Example:
        >>> # Get all Claude model pricing
        >>> claude_pricing = get_bedrock_pricing('claude', 'us-west-2')
        >>> 
        >>> # Get Nova model pricing
        >>> nova_pricing = get_bedrock_pricing('nova', 'eu-west-1')
        >>> 
        >>> # Search for specific model
        >>> haiku_pricing = get_bedrock_pricing('haiku')
    
    Dependencies:
        - boto3: AWS SDK for Python
        - json: JSON parsing for API responses
        - typing: Type hints support
    """
    # AWS Pricing API has to be targeted to us-east-1 region.
    pricing_client = boto3.client('pricing', region_name='us-east-1')
    
    next_token = None
    matching_models = []
    all_products = []

    try:
        while True: #We have to iterate of there are more than 100 results.
            params = {                
                'Filters':[
                    {
                        'Type': 'TERM_MATCH',
                        'Field': 'regionCode',
                        'Value': region #Specify the region
                    },
                    {
                        'Type': 'TERM_MATCH',
                        'Field': 'termType',
                        'Value': 'OnDemand' #Mainly interested in On-Demand pricing.
                    },                    
                ],
                'MaxResults':100
            }
            if any(term in model_name.lower() for term in ['claude', 'haiku', 'sonnet', 'opus', 'cohere', 'palmyra', 'twelvelabs', 'stable', 'command', 'diffusion', 'cohere rerank', 'luma', 'jurassic']):
                # Set the following for 3P Models
                params['ServiceCode'] = 'AmazonBedrockFoundationModels'
                model_param = 'servicename'
            else :
                # Set the following for 1P and open source Models
                params['ServiceCode'] = 'AmazonBedrock'
                model_param = 'model'

            # Add NextToken if available
            if next_token:
                params['NextToken'] = next_token
                mode = 'a' # Append to file
                # print(f"************* We hit NextToken. Get More Results... **************")
            else :
                mode = 'w' # Overwrite file

            # Get all Bedrock products
            response = pricing_client.get_products(**params)

            # #The following print function is important for debugging. It writes to a file.
            # print_pricing_response(response, f"full_response_{params['ServiceCode']}.json", mode)

            # Collect results
            all_products.extend(response['PriceList'])

            # Check for more pages
            next_token = response.get('NextToken')
            if not next_token:
                break
        
        for product_str in all_products:
            product = json.loads(product_str)
            
            # Extract product attributes
            attributes = product.get('product', {}).get('attributes', {})
            model_id = attributes.get(model_param, '')
            
            # Fuzzy matching - check if model_name is in the model_id (case insensitive)
            if model_name.lower() in model_id.lower():
                
                # Extract pricing information
                terms = product.get('terms', {})
                on_demand = terms.get('OnDemand', {})
                
                for term_key, term_data in on_demand.items():
                    price_dimensions = term_data.get('priceDimensions', {})
                    
                    for price_key, price_data in price_dimensions.items():
                        price_per_unit = price_data.get('pricePerUnit', {}).get('USD', '0')                        
                        model_info = {}                        
                        model_info['regionCode'] = attributes.get('regionCode', '')                           
                        model_info['usagetype'] = attributes.get('usagetype', '')
                        model_info['price_per_unit'] = float(price_per_unit) if price_per_unit != '0' else 0.0
                        model_info['effective_date'] = term_data.get('effectiveDate', '')
                        if params['ServiceCode'] == 'AmazonBedrock':
                            # 1P Models                      
                            model_info['model_name'] = attributes.get('model', '')
                            model_info['unit'] = price_data.get('unit', '')    
                        else :
                            # 3P Models
                            model_info['model_name'] = attributes.get('servicename', '')
                            model_info['unit'] = "1M tokens" if 'Million' in price_data.get('description', '') else price_data.get('description', '')
                        
                        if '1M' not in model_info['unit'] :
                            #Convert pricing in terms of 1M units to make it consistent.
                            model_info['price_per_unit'] = model_info['price_per_unit']*1000
                            model_info['unit'] = "1M tokens"

                        
                        matching_models.append(model_info)        
        
        # return matching_models
        # Remove duplicates and sort by model name
        unique_models = []
        seen_models = set()
        
        for model in matching_models:
            model_key = (model['model_name'], model['unit'], model['usagetype'])
            if model_key not in seen_models:
                seen_models.add(model_key)
                unique_models.append(model)
        
        return sorted(unique_models, key=lambda x: x['model_name'])
        
    except Exception as e:
        print(f"Error fetching pricing data: {str(e)}")
        return []

@tool
def get_aws_pricing(service_code: str, filters: List[Dict[str, str]] = None, region: str = None) -> List[str]:
    """
    Retrieve raw pricing information for AWS products using flexible filtering criteria.
    Before invoking this function, you would typically invoke get_all_service_codes to get the exact Service Code. You might also invoke get_attribute_values to get the attributes.
    You can then construct a filter and pass Service Code and filter to this funtion.
    
    It returns the raw PriceList elements as received from the API without any parsing or modification.
    
    Args:
        service_code (str): The AWS service code for which to retrieve pricing.
                           Examples: 'AmazonEC2', 'AmazonS3', 'AmazonBedrock', 
                           'AmazonBedrockFoundationModels', 'AmazonRDS'
        filters (List[Dict[str, str]], optional): List of filter dictionaries to narrow down results.
                                                Each filter must contain 'Type', 'Field', and 'Value' keys.
                                                If None, returns all products for the service.
        region (str, optional): AWS region code to filter by (e.g., 'us-west-2', 'eu-west-1').
                               If provided, automatically adds a regionCode filter.
    
    Filter Types:
        - TERM_MATCH: Exact match for both field and value
        - EQUALS: Field value exactly matches provided value  
        - CONTAINS: Field value contains provided value as substring
        - ANY_OF: Field value is any of the comma-separated values
        - NONE_OF: Field value is not any of the comma-separated values
    
    Common Filter Fields:
        - regionCode: AWS region (e.g., 'us-west-2')
        - usagetype: Usage type (e.g., 'BoxUsage:t2.micro')
        - instanceType: EC2 instance type (e.g., 't2.micro')
        - volumeType: EBS volume type (e.g., 'General Purpose')
        - model: Bedrock model name (e.g., 'Claude 3 Haiku')
        - termType: Pricing term (e.g., 'OnDemand', 'Reserved')
        - operation: Operation type (e.g., 'RunInstances')
    
    Returns:
        List[str]: List of raw pricing data strings as returned by AWS Pricing API.
                  Each element is a JSON string containing complete product and pricing information.
                  Returns empty list if no products found or on error.
    
    Raises:
        Exception: Captures and logs AWS API errors, returns empty list on failure.
    
    Notes:
        - Uses AWS Pricing API which only operates from us-east-1 region        
        - Returns raw JSON strings without any parsing or modification
        - Each string in the returned list can be parsed with json.loads() if needed
        - Results maintain the original order from the API response
    
    Examples:
        >>> # Get all EC2 pricing for us-west-2
        >>> ec2_pricing = get_aws_pricing('AmazonEC2', region='us-west-2')
        >>> print(f"Found {len(ec2_pricing)} EC2 products")
        >>> 
        >>> # Get specific EC2 instance pricing
        >>> filters = [
        ...     {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': 't2.micro'},
        ...     {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'}
        ... ]
        >>> t2_pricing = get_aws_pricing('AmazonEC2', filters=filters, region='us-west-2')
        >>> 
        >>> # Parse first result if needed
        >>> if t2_pricing:
        ...     import json
        ...     first_product = json.loads(t2_pricing[0])
        ...     print(first_product['product']['attributes'])
        >>> 
        >>> # Get Bedrock model pricing
        >>> bedrock_filters = [
        ...     {'Type': 'CONTAINS', 'Field': 'servicename', 'Value': 'Claude'}
        ... ]
        >>> claude_pricing = get_aws_pricing('AmazonBedrockFoundationModels', filters=bedrock_filters)
        >>> 
        >>> # Get S3 storage pricing for multiple classes
        >>> s3_filters = [
        ...     {'Type': 'ANY_OF', 'Field': 'storageClass', 'Value': 'General Purpose,Infrequent Access'}
        ... ]
        >>> s3_pricing = get_aws_pricing('AmazonS3', filters=s3_filters, region='us-east-1')
    
    Dependencies:
        - boto3: AWS SDK for Python
        - typing: Type hints support
    """
    # AWS Pricing API has to be targeted to us-east-1 region
    pricing_client = boto3.client('pricing', region_name='us-east-1')
    
    all_price_list = []
    next_token = None
    
    try:
        while True:
            # Build base parameters
            params = {
                'ServiceCode': service_code,
                # 'FormatVersion': 'aws_v1',
                'MaxResults': 100  # Maximum allowed by API
            }
            
            # Build filters list
            api_filters = []
            
            # Add region filter if specified
            if region:
                api_filters.append({
                    'Type': 'TERM_MATCH',
                    'Field': 'regionCode',
                    'Value': region
                })
            
            # Add custom filters if provided
            if filters:
                for filter_dict in filters:
                    # Validate required filter fields
                    if all(key in filter_dict for key in ['Type', 'Field', 'Value']):
                        api_filters.append({
                            'Type': filter_dict['Type'],
                            'Field': filter_dict['Field'],
                            'Value': filter_dict['Value']
                        })
                    else:
                        print(f"Warning: Invalid filter format: {filter_dict}")
            
            # Add filters to parameters if any exist
            if api_filters:
                params['Filters'] = api_filters
            
            # Add NextToken if available
            if next_token:
                params['NextToken'] = next_token
            
            # Get products
            response = pricing_client.get_products(**params)
            
            # Collect all PriceList elements as-is
            price_list = response.get('PriceList', [])
            all_price_list.extend(price_list)
            
            # Check for more pages
            next_token = response.get('NextToken')
            if not next_token:
                break
        
        cleansed_response = []

        for i in all_price_list:
            itm = json.loads(i)
            product = itm["product"]
            description = list(find_descriptions(itm))
            cleansed_response.append({
                "product": product,
                "pricing_term": description
            })
        return cleansed_response

        #return all_price_list
        
    except Exception as e:
        print(f"Error fetching pricing data for {service_code}: {str(e)}")
        return []

@tool
def get_attribute_values(service_code: str, attribute_name: str) -> List[str]:
    """
    Retrieve all possible values for a specific attribute of an AWS service.
    
    This function uses the AWS Pricing API to get all available values for a given
    attribute within a specific service. Handles pagination automatically to retrieve
    all possible values.
    
    Args:
        service_code (str): The AWS service code for which to retrieve attribute values.
                           Examples: 'AmazonEC2', 'AmazonS3', 'AmazonBedrock', 
                           'AmazonBedrockFoundationModels'
        attribute_name (str): The name of the attribute whose values you want to retrieve.
                             Examples: 'volumeType', 'location', 'usagetype', 'model',
                             'servicename', 'regionCode'
    
    Returns:
        List[str]: List of all possible values for the specified attribute.
                  Returns empty list if no values found or on error.
    
    Raises:
        Exception: Captures and logs AWS API errors, returns empty list on failure.
    
    Notes:
        - Uses AWS Pricing API which only operates from us-east-1 region
        - Implements pagination to retrieve all available attribute values
        - Automatically handles NextToken for large result sets
        - Results are sorted alphabetically for consistency
        - Removes duplicate values if any exist
    
    Examples:
        >>> # Get all EC2 volume types
        >>> volume_types = get_attribute_values('AmazonEC2', 'volumeType')
        >>> # Returns: ['Throughput Optimized HDD', 'Provisioned IOPS', 'General Purpose', ...]
        >>> 
        >>> # Get all Bedrock model names
        >>> models = get_attribute_values('AmazonBedrock', 'model')
        >>> 
        >>> # Get all available regions for S3
        >>> regions = get_attribute_values('AmazonS3', 'regionCode')
        >>> 
        >>> # Get all usage types for Bedrock Foundation Models
        >>> usage_types = get_attribute_values('AmazonBedrockFoundationModels', 'usagetype')
    
    Dependencies:
        - boto3: AWS SDK for Python
        - typing: Type hints support
    """
    # AWS Pricing API has to be targeted to us-east-1 region
    pricing_client = boto3.client('pricing', region_name='us-east-1')
    
    all_values = []
    next_token = None
    
    try:
        while True:
            # Build parameters
            params = {
                'ServiceCode': service_code,
                'AttributeName': attribute_name,
                'MaxResults': 100  # Maximum allowed by API
            }
            
            # Add NextToken if available
            if next_token:
                params['NextToken'] = next_token
            
            # Get attribute values
            response = pricing_client.get_attribute_values(**params)
            
            # Extract values from response
            attribute_values = response.get('AttributeValues', [])
            values = [item.get('Value', '') for item in attribute_values if item.get('Value')]
            all_values.extend(values)
            
            # Check for more pages
            next_token = response.get('NextToken')
            if not next_token:
                break
        
        # Remove duplicates and sort
        unique_values = list(set(all_values))
        return sorted(unique_values)
        
    except Exception as e:
        print(f"Error fetching attribute values for {service_code}.{attribute_name}: {str(e)}")
        return []

@tool
def get_agentcore_pricing(region_code: str) -> List[str] :
    """
        AgentCore helps Agents with an environment to run, use memory, invoke tools securely, use identity.
        For a given AWS region, get pricing information for various components of Bedrock AgentCore such as Runtime, Short-Term-Memory, Long-Term-Memory-Storage, Gateway, BrowserTool, CodeInterpreter, Identity.

    Args:
        region_code (str): The AWS region code for which to retrieve pricing. Example is us-west-2

    Returns:
        List[str]: List of raw pricing data strings as returned by AWS Pricing API.
                  Each element is a JSON string containing complete product and pricing information.
                  Returns empty list if no products found or on error.

    Raises:
        Exception: Captures and logs AWS API errors, returns empty list on failure.

    Notes:        
        - Returns raw JSON strings without any parsing or modification
        - Each string in the returned list can be parsed with json.loads() if needed        

    Examples:
        >>> # Get pricing for us-west-2
        >>> pricing = get_agentcore_pricing('us-west-2')
    """
    response = get_aws_pricing('AmazonBedrockAgentCore', None, region_code)
    cleansed_response = []

    for i in response:
        itm = json.loads(i)
        product = itm["product"]
        description = list(find_descriptions(itm))
        cleansed_response.append({
            "product": product,
            "pricing_term": description
        })
    return cleansed_response


if __name__ == "__main__":
    filters = [
             {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': 't2.micro'},
             {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'}
         ]
    #response = get_aws_pricing('AmazonEC2', filters=filters, region='us-west-2')
    response = get_attribute_values('AmazonEC2', 'volumeType')
    print(response)


