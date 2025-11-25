#!/usr/bin/env python3
"""
V4.0 Field Type Correction: Law Firm Name (text → category)
Converts field 274896124 from text to category to match contract specification
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

PODIO_CLIENT_ID = os.environ.get('PODIO_CLIENT_ID')
PODIO_CLIENT_SECRET = os.environ.get('PODIO_CLIENT_SECRET')
PODIO_USERNAME = os.environ.get('PODIO_USERNAME')
PODIO_PASSWORD = os.environ.get('PODIO_PASSWORD')
MASTER_LEAD_APP_ID = '30549135'

# Current text field to be deleted
OLD_LAW_FIRM_FIELD_ID = 274896124

# Law firm options from contract analysis (common foreclosure attorneys)
LAW_FIRM_OPTIONS = [
    'McCarthy & Holthus, LLP',
    'Janeway Law Firm PC',
    'The Sayer Law Group, P.C.',
    'Altitude Community Law',
    'Castle Stawiarski, LLC',
    'Other'
]

def get_podio_token():
    """Get Podio OAuth access token"""
    print("Authenticating with Podio...")
    
    if not all([PODIO_CLIENT_ID, PODIO_CLIENT_SECRET, PODIO_USERNAME, PODIO_PASSWORD]):
        raise ValueError("Missing Podio credentials in environment variables")
    
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
        print("✅ Authentication successful")
        return token_data['access_token']
    else:
        raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
    
def delete_field(access_token, field_id):
    """Delete the incorrectly typed field"""
    print(f"\nDeleting text field {field_id}...")
    response = requests.delete(
        f'https://api.podio.com/app/{MASTER_LEAD_APP_ID}/field/{field_id}',
        headers={'Authorization': f'OAuth2 {access_token}'}
    )
    if response.status_code in [200, 204]:
        print(f"✅ Field {field_id} deleted successfully (status: {response.status_code})")
        return True
    elif response.status_code == 400 and "already deleted" in response.text.lower():
        print(f"✅ Field {field_id} was already deleted (skipping)")
        return True
    else:
        print(f"❌ Delete failed: {response.status_code} - {response.text}")
        return False

def create_category_field(access_token):
    """Create Law Firm Name as category field"""
    print("\nCreating Law Firm Name as category field...")
    
    payload = {
        'type': 'category',
        'config': {
            'label': 'Law Firm Name',
            'description': 'Foreclosure attorney firm (Pillar #1: TCPA Compliance)',
            'required': False,
            'settings': {
                'multiple': False,
                'options': [{'text': option} for option in LAW_FIRM_OPTIONS]
            }
        }
    }
    
    response = requests.post(
        f'https://api.podio.com/app/{MASTER_LEAD_APP_ID}/field',
        headers={
            'Authorization': f'OAuth2 {access_token}',
            'Content-Type': 'application/json'
        },
        json=payload
    )
    
    if response.status_code == 200:
        field_data = response.json()
        new_field_id = field_data.get('field_id')
        print(f"✅ Category field created successfully - New ID: {new_field_id}")
        return new_field_id
    else:
        print(f"❌ Create failed: {response.status_code} - {response.text}")
        return None

def main():
    try:
        access_token = get_podio_token()
        
        # Step 1: Delete old text field
        if not delete_field(access_token, OLD_LAW_FIRM_FIELD_ID):
            sys.exit(1)
        
        # Step 2: Create new category field
        new_field_id = create_category_field(access_token)
        if not new_field_id:
            sys.exit(1)
        
        # Step 3: Document the new field ID
        result = {
            'old_field_id': OLD_LAW_FIRM_FIELD_ID,
            'old_field_type': 'text',
            'new_field_id': new_field_id,
            'new_field_type': 'category',
            'law_firm_options': LAW_FIRM_OPTIONS
        }
        
        with open('scripts/law_firm_field_correction.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n✅ Field conversion complete!")
        print(f"   Old ID (text): {OLD_LAW_FIRM_FIELD_ID}")
        print(f"   New ID (category): {new_field_id}")
        print(f"\nNEXT STEPS:")
        print(f"   1. Update config.py: LAW_FIRM_NAME_FIELD_ID = {new_field_id}")
        print(f"   2. Update contract TBD_011 → {new_field_id}")
        print(f"   3. Re-run scripts/verify_v4_enriched_fields.py")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()