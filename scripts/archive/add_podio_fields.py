#!/usr/bin/env python3
"""
Script to add V2.0 schema fields to Podio Call Activity App
App ID: 30549170
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Podio credentials
PODIO_CLIENT_ID = os.environ.get('PODIO_CLIENT_ID')
PODIO_CLIENT_SECRET = os.environ.get('PODIO_CLIENT_SECRET')
PODIO_USERNAME = os.environ.get('PODIO_USERNAME')
PODIO_PASSWORD = os.environ.get('PODIO_PASSWORD')
PODIO_CALL_ACTIVITY_APP_ID = os.environ.get('PODIO_CALL_ACTIVITY_APP_ID')

def get_podio_token():
    """Get Podio OAuth access token"""
    print("Authenticating with Podio...")
    
    if not all([PODIO_CLIENT_ID, PODIO_CLIENT_SECRET, PODIO_USERNAME, PODIO_PASSWORD]):
        raise Exception("Podio credentials not fully configured. Please check environment variables.")
    
    try:
        response = requests.post(
            'https://podio.com/oauth/token',
            data={
                'grant_type': 'password',
                'client_id': PODIO_CLIENT_ID,
                'client_secret': PODIO_CLIENT_SECRET,
                'username': PODIO_USERNAME,
                'password': PODIO_PASSWORD
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            print("✅ Podio authentication successful")
            return access_token
        else:
            raise Exception(f"Error getting Podio token: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Error initializing Podio authentication: {e}")

def check_existing_fields(access_token, app_id):
    """Check what fields already exist in the app"""
    print(f"\nChecking existing fields in app {app_id}...")
    
    try:
        response = requests.get(
            f'https://api.podio.com/app/{app_id}',
            headers={
                'Authorization': f'OAuth2 {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code == 200:
            app_data = response.json()
            existing_fields = app_data.get('fields', [])
            
            print(f"Found {len(existing_fields)} existing fields:")
            for field in existing_fields:
                print(f"  - {field.get('label')} (Type: {field.get('type')}, ID: {field.get('field_id')})")
            
            return existing_fields
        else:
            print(f"Warning: Could not fetch existing fields: {response.status_code}")
            return []
    except Exception as e:
        print(f"Warning: Error checking existing fields: {e}")
        return []

def add_field(access_token, app_id, field_config):
    """Add a field to the Podio app"""
    field_name = field_config.get('config', {}).get('label', 'Unknown')
    print(f"\nAdding field: {field_name}...")
    
    try:
        response = requests.post(
            f'https://api.podio.com/app/{app_id}/field/',
            headers={
                'Authorization': f'OAuth2 {access_token}',
                'Content-Type': 'application/json'
            },
            json=field_config
        )
        
        if response.status_code == 200:
            field_data = response.json()
            field_id = field_data.get('field_id')
            print(f"✅ Field '{field_name}' added successfully (ID: {field_id})")
            return {
                'success': True,
                'field_id': field_id,
                'field_name': field_name,
                'field_type': field_config.get('type')
            }
        elif response.status_code == 400 and 'already exists' in response.text.lower():
            print(f"⚠️  Field '{field_name}' already exists. Skipping.")
            return {
                'success': False,
                'error': 'Field already exists',
                'field_name': field_name
            }
        else:
            error_msg = f"Error adding field '{field_name}': {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'field_name': field_name
            }
    except Exception as e:
        error_msg = f"Exception adding field '{field_name}': {e}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': str(e),
            'field_name': field_name
        }

def main():
    """Main function to add all V2.0 schema fields"""
    print("=" * 60)
    print("Podio Call Activity App - V2.0 Schema Field Addition")
    print("=" * 60)
    
    if not PODIO_CALL_ACTIVITY_APP_ID:
        print("❌ Error: PODIO_CALL_ACTIVITY_APP_ID not set in environment variables")
        sys.exit(1)
    
    print(f"Target App ID: {PODIO_CALL_ACTIVITY_APP_ID}")
    
    # Get Podio access token
    try:
        access_token = get_podio_token()
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)
    
    # Check existing fields
    existing_fields = check_existing_fields(access_token, PODIO_CALL_ACTIVITY_APP_ID)
    existing_field_names = [f.get('label') for f in existing_fields]
    
    # Define the 5 required fields for V2.0
    fields_to_add = [
        {
            'type': 'category',
            'config': {
                'label': 'Disposition Code',
                'description': 'Call outcome - required for all calls',
                'required': True,
                'settings': {
                    'options': [
                        {'text': 'No Answer', 'color': 'DCEBD8'},
                        {'text': 'Voicemail', 'color': 'DCEBD8'},
                        {'text': 'Not Interested', 'color': 'FFD5D2'},
                        {'text': 'Callback Scheduled', 'color': 'FFF6CC'},
                        {'text': 'Appointment Set', 'color': 'D5F3FF'},
                        {'text': 'Wrong Number', 'color': 'E4E4E4'},
                        {'text': 'Do Not Call', 'color': 'FFD5D2'}
                    ],
                    'multiple': False,
                    'display': 'dropdown'
                }
            }
        },
        {
            'type': 'text',
            'config': {
                'label': 'Agent Notes / Summary',
                'description': 'Detailed notes from the call for continuity',
                'required': False,
                'settings': {
                    'format': 'plain',
                    'size': 'large'
                }
            }
        },
        {
            'type': 'category',
            'config': {
                'label': 'Seller Motivation Level',
                'description': 'Assessed motivation level for prioritizing follow-ups',
                'required': False,
                'settings': {
                    'options': [
                        {'text': 'High', 'color': 'D5F3FF'},
                        {'text': 'Medium', 'color': 'FFF6CC'},
                        {'text': 'Low', 'color': 'FFD5D2'},
                        {'text': 'Unknown', 'color': 'E4E4E4'}
                    ],
                    'multiple': False,
                    'display': 'dropdown'
                }
            }
        },
        {
            'type': 'date',
            'config': {
                'label': 'Next Action Date',
                'description': 'Scheduled date for next touchpoint',
                'required': False,
                'settings': {
                    'calendar': True,
                    'end': 'disabled'
                }
            }
        },
        {
            'type': 'money',
            'config': {
                'label': 'Target Asking Price',
                'description': 'Property asking price for pipeline forecasting',
                'required': False,
                'settings': {
                    'allowed_currencies': ['USD']
                }
            }
        }
    ]
    
    # Add each field
    results = []
    print(f"\n{'=' * 60}")
    print("Adding fields to Podio...")
    print(f"{'=' * 60}")
    
    for field_config in fields_to_add:
        field_name = field_config.get('config', {}).get('label')
        
        # Check if field already exists
        if field_name in existing_field_names:
            print(f"\n⚠️  Field '{field_name}' already exists. Skipping creation.")
            # Find the existing field ID
            for existing_field in existing_fields:
                if existing_field.get('label') == field_name:
                    results.append({
                        'success': True,
                        'field_id': existing_field.get('field_id'),
                        'field_name': field_name,
                        'field_type': field_config.get('type'),
                        'already_existed': True
                    })
                    break
            continue
        
        result = add_field(access_token, PODIO_CALL_ACTIVITY_APP_ID, field_config)
        results.append(result)
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print(f"\n✅ Successfully processed: {len(successful)} fields")
    print(f"❌ Failed: {len(failed)} fields")
    
    if successful:
        print("\n📋 Field IDs Created/Found:")
        for result in successful:
            already_existed = result.get('already_existed', False)
            status = "(already existed)" if already_existed else "(newly created)"
            print(f"  - {result['field_name']}: {result['field_id']} {status}")
    
    if failed:
        print("\n❌ Failed Fields:")
        for result in failed:
            print(f"  - {result['field_name']}: {result.get('error', 'Unknown error')}")
    
    # Save results to JSON file
    output_file = 'scripts/podio_field_ids.json'
    try:
        with open(output_file, 'w') as f:
            json.dump({
                'app_id': PODIO_CALL_ACTIVITY_APP_ID,
                'timestamp': '2025-11-20',
                'results': results
            }, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
    except Exception as e:
        print(f"\n⚠️  Warning: Could not save results to file: {e}")
    
    print(f"\n{'=' * 60}")
    
    # Return exit code
    if failed:
        sys.exit(1)
    else:
        print("✅ All fields processed successfully!")
        sys.exit(0)

if __name__ == '__main__':
    main()