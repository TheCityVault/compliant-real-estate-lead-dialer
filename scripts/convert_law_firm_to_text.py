#!/usr/bin/env python3
"""
Amendment v1.1.3-A2: LAW_FIRM_NAME Field Type Change (CATEGORY → TEXT)

CRM PM Approved: 2025-11-29
Priority: HIGH (Blocking Data Team sync pipeline)

Issue: Data Team's Podio sync is failing with error:
  "attribute-law-firm-name" has an invalid option "Barrett, Frappier & Weisserman, LLP"

Solution: 
  - Delete existing CATEGORY field (274896414)
  - Create new TEXT field with same label
  - Document new field ID for config.py update
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PODIO_CLIENT_ID = os.environ.get('PODIO_CLIENT_ID')
PODIO_CLIENT_SECRET = os.environ.get('PODIO_CLIENT_SECRET')
PODIO_USERNAME = os.environ.get('PODIO_USERNAME')
PODIO_PASSWORD = os.environ.get('PODIO_PASSWORD')

MASTER_LEAD_APP_ID = '30549135'

# Current CATEGORY field to be deleted
CURRENT_LAW_FIRM_FIELD_ID = 274896414


def get_podio_token():
    """Get Podio OAuth access token"""
    print("=" * 60)
    print("PODIO AUTHENTICATION")
    print("=" * 60)
    
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


def verify_field_exists(access_token, field_id):
    """Verify the field exists before attempting deletion"""
    print(f"\nVerifying field {field_id} exists...")
    
    response = requests.get(
        f'https://api.podio.com/app/{MASTER_LEAD_APP_ID}',
        headers={'Authorization': f'OAuth2 {access_token}'}
    )
    
    if response.status_code == 200:
        app_data = response.json()
        fields = app_data.get('fields', [])
        
        for field in fields:
            if field.get('field_id') == field_id:
                print(f"✅ Found field: {field.get('label')} (ID: {field_id})")
                print(f"   Type: {field.get('type')}")
                return field
        
        print(f"⚠️ Field {field_id} not found in app")
        return None
    else:
        print(f"❌ Failed to get app info: {response.status_code}")
        return None


def delete_field(access_token, field_id):
    """Delete the CATEGORY field"""
    print("\n" + "=" * 60)
    print("STEP 1: DELETE CATEGORY FIELD")
    print("=" * 60)
    print(f"Deleting field {field_id}...")
    
    response = requests.delete(
        f'https://api.podio.com/app/{MASTER_LEAD_APP_ID}/field/{field_id}',
        headers={'Authorization': f'OAuth2 {access_token}'}
    )
    
    if response.status_code in [200, 204]:
        print(f"✅ Field {field_id} deleted successfully (HTTP {response.status_code})")
        return True
    elif response.status_code == 404:
        print(f"⚠️ Field {field_id} not found (already deleted?)")
        return True  # Consider success if already deleted
    else:
        print(f"❌ Delete failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def create_text_field(access_token):
    """Create Law Firm Name as TEXT field"""
    print("\n" + "=" * 60)
    print("STEP 2: CREATE TEXT FIELD")
    print("=" * 60)
    print("Creating 'Law Firm Name' as TEXT field...")
    
    payload = {
        'type': 'text',
        'config': {
            'label': 'Law Firm Name',
            'description': 'Foreclosure attorney firm name (TEXT type for Data Team sync - Amendment v1.1.3-A2)',
            'required': False,
            'settings': {
                'size': 'small'  # single-line text
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
        print(f"✅ TEXT field created successfully")
        print(f"   New Field ID: {new_field_id}")
        return new_field_id, field_data
    else:
        print(f"❌ Create failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None, None


def main():
    print("\n")
    print("=" * 60)
    print("AMENDMENT v1.1.3-A2: LAW_FIRM_NAME FIELD TYPE CHANGE")
    print("CATEGORY → TEXT")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"App ID: {MASTER_LEAD_APP_ID}")
    print(f"Field to delete: {CURRENT_LAW_FIRM_FIELD_ID}")
    print("=" * 60)
    
    try:
        access_token = get_podio_token()
        
        # Verify the field exists first
        existing_field = verify_field_exists(access_token, CURRENT_LAW_FIRM_FIELD_ID)
        
        # Step 1: Delete existing CATEGORY field
        if not delete_field(access_token, CURRENT_LAW_FIRM_FIELD_ID):
            print("\n❌ FAILED: Could not delete existing field")
            sys.exit(1)
        
        # Step 2: Create new TEXT field
        new_field_id, field_data = create_text_field(access_token)
        if not new_field_id:
            print("\n❌ FAILED: Could not create new TEXT field")
            sys.exit(1)
        
        # Step 3: Document results
        print("\n" + "=" * 60)
        print("STEP 3: DOCUMENTING RESULTS")
        print("=" * 60)
        
        result = {
            'amendment': 'v1.1.3-A2',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action': 'CATEGORY → TEXT field type change',
            'app_id': int(MASTER_LEAD_APP_ID),
            'old_field': {
                'field_id': CURRENT_LAW_FIRM_FIELD_ID,
                'type': 'category',
                'status': 'deleted'
            },
            'new_field': {
                'field_id': new_field_id,
                'type': 'text',
                'label': 'Law Firm Name',
                'status': 'created'
            },
            'reason': 'Data Team sync failing - CATEGORY type cannot accept arbitrary law firm names',
            'error_fixed': '"attribute-law-firm-name" has an invalid option "Barrett, Frappier & Weisserman, LLP"'
        }
        
        with open('scripts/law_firm_field_correction.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print("✅ Results saved to scripts/law_firm_field_correction.json")
        
        # Final summary
        print("\n" + "=" * 60)
        print("✅ FIELD CONVERSION COMPLETE")
        print("=" * 60)
        print(f"   Old Field ID (CATEGORY): {CURRENT_LAW_FIRM_FIELD_ID} [DELETED]")
        print(f"   New Field ID (TEXT):     {new_field_id} [CREATED]")
        print("=" * 60)
        print("\n📋 DELIVERABLES FOR CRM PM:")
        print(f"   1. Update config.py: LAW_FIRM_NAME_FIELD_ID = {new_field_id}")
        print(f"   2. Post to Data Team GitHub PR #2: New field ID = {new_field_id}")
        print(f"   3. Update bilateral contract with new field ID")
        print("=" * 60)
        
        # Return the new field ID for easy capture
        return new_field_id
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    new_id = main()
    print(f"\n🎯 NEW LAW_FIRM_NAME_FIELD_ID = {new_id}")