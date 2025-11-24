#!/usr/bin/env python3
"""
Script to retrieve and display all AWS service codes available in the AWS Pricing API.
"""

import boto3
import json
from typing import List, Dict


def get_all_service_codes() -> List[Dict[str, str]]:
    """
    Retrieve all AWS service codes available in the AWS Pricing API.
    
    Returns:
        List[Dict[str, str]]: List of dictionaries containing service information.
                             Each dict has 'ServiceCode' and 'AttributeNames' keys.
    """
    # AWS Pricing API has to be targeted to us-east-1 region
    pricing_client = boto3.client('pricing', region_name='us-east-1')
    
    all_services = []
    next_token = None
    
    try:
        print("🔍 Fetching all AWS service codes from Pricing API...")
        print("=" * 80)
        
        while True:
            # Build parameters
            params = {
                'MaxResults': 100  # Maximum allowed by API
            }
            
            # Add NextToken if available
            if next_token:
                params['NextToken'] = next_token
            
            # Get services
            response = pricing_client.describe_services(**params)
            
            # Extract services from response
            services = response.get('Services', [])
            all_services.extend(services)
            
            # Check for more pages
            next_token = response.get('NextToken')
            if not next_token:
                break
        
        print(f"✅ Found {len(all_services)} AWS services\n")
        return all_services
        
    except Exception as e:
        print(f"❌ Error fetching service codes: {str(e)}")
        return []


def print_service_codes(services: List[Dict[str, str]], detailed: bool = False):
    """
    Print AWS service codes in a formatted manner.
    
    Args:
        services: List of service dictionaries
        detailed: If True, also print available attributes for each service
    """
    if not services:
        print("No services found.")
        return
    
    print("📋 AWS Service Codes:")
    print("=" * 80)
    
    for idx, service in enumerate(services, 1):
        service_code = service.get('ServiceCode', 'N/A')
        
        if detailed:
            attribute_names = service.get('AttributeNames', [])
            print(f"{idx}. {service_code}")
            if attribute_names:
                print(f"   Attributes: {', '.join(attribute_names)}")
            print()
        else:
            print(f"{idx}. {service_code}")
    
    print("=" * 80)
    print(f"Total: {len(services)} services")


def save_to_file(services: List[Dict[str, str]], filename: str = "aws_service_codes.json"):
    """
    Save service codes to a JSON file.
    
    Args:
        services: List of service dictionaries
        filename: Output filename
    """
    try:
        with open(filename, 'w') as f:
            json.dump(services, f, indent=2)
        print(f"\n💾 Service codes saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving to file: {str(e)}")


def search_services(services: List[Dict[str, str]], search_term: str) -> List[Dict[str, str]]:
    """
    Search for services matching a search term.
    
    Args:
        services: List of service dictionaries
        search_term: Term to search for (case-insensitive)
    
    Returns:
        List of matching services
    """
    search_term_lower = search_term.lower()
    matching = [
        service for service in services 
        if search_term_lower in service.get('ServiceCode', '').lower()
    ]
    return matching


def main():
    """Main function to retrieve and display AWS service codes."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Retrieve and display AWS service codes from Pricing API'
    )
    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show detailed information including attributes for each service'
    )
    parser.add_argument(
        '--save', '-s',
        action='store_true',
        help='Save service codes to a JSON file'
    )
    parser.add_argument(
        '--search',
        type=str,
        help='Search for services containing the specified term'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='aws_service_codes.json',
        help='Output filename for saved service codes (default: aws_service_codes.json)'
    )
    
    args = parser.parse_args()
    
    # Get all service codes
    services = get_all_service_codes()
    
    if not services:
        print("Failed to retrieve service codes.")
        return
    
    # Search if requested
    if args.search:
        print(f"\n🔎 Searching for services matching '{args.search}'...")
        services = search_services(services, args.search)
        print(f"Found {len(services)} matching service(s)\n")
    
    # Print service codes
    print_service_codes(services, detailed=args.detailed)
    
    # Save to file if requested
    if args.save:
        save_to_file(services, args.output)
    
    # Print some useful examples
    if not args.search:
        print("\n💡 Useful Examples:")
        print("   - Search for Bedrock services: python get_service_codes.py --search bedrock")
        print("   - Search for EC2 services: python get_service_codes.py --search ec2")
        print("   - Show detailed info: python get_service_codes.py --detailed")
        print("   - Save to file: python get_service_codes.py --save")


if __name__ == "__main__":
    main()
