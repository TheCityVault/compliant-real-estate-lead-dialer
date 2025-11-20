#!/usr/bin/env python3
"""
Script to delete duplicate 'Call History' fields from Master Lead app
Keep only the most recent one (274851784)
Delete: 274851740, 274851741
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

# Podio credentials
PODIO_CLIENT_ID = os.environ.get('PODIO_CLIENT_ID')
PODIO_CLIENT_SECRET = os.environ.get('PODIO_CLIENT_SECRET')
PODIO_USERNAME = os.environ.get('PODIO_USERNAME')
PODIO_PASSWORD = os.environ.get('PODIO_PASSWORD')
PODIO_MASTER_LEAD_APP_ID = os.environ.get('PODIO_MASTER_LEAD_APP_ID')

# Duplicate fields to delete
FIELDS_TO_DELETE = [274851740, 274851741]
FIELD_TO_KEEP = 274851784

def get_podio_token():
    """Get Podio OAuth access token"""
    print("Authenticating with Podio...")
    
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
            print("✅ Authentication successful\n")
            return token_data.get('access_token')
        else:
            raise Exception(f"Auth error: {response.status_code}")
    except Exception as e:
        raise Exception(f"Authentication failed: {e}")

def delete_field(access_token, app_id, field_id):
    """Delete a field from Podio app"""
    print(f"Deleting field {field_id}...")
    
    try:
        response = requests.delete(
            f'https://api.podio.com/app/{app_id}/field/{field_id}',
            headers={
                'Authorization': f'OAuth2 {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code in [200, 204]:
            print(f"✅ Field {field_id} deleted successfully")
            return True
        else:
            print(f"❌ Error deleting field {field_id}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception deleting field {field_id}: {e}")
        return False

def main():
    print("=" * 70)
    print("DELETE DUPLICATE CALL HISTORY FIELDS")
    print("=" * 70)
    print(f"\nMaster Lead App ID: {PODIO_MASTER_LEAD_APP_ID}")
    print(f"Fields to delete: {FIELDS_TO_DELETE}")
    print(f"Field to keep: {FIELD_TO_KEEP}")
    print("=" * 70 + "\n")
    
    try:
        access_token = get_podio_token()
        
        success_count = 0
        for field_id in FIELDS_TO_DELETE:
            if delete_field(access_token, PODIO_MASTER_LEAD_APP_ID, field_id):
                success_count += 1
        
        print("\n" + "=" * 70)
        print(f"Deleted {success_count} of {len(FIELDS_TO_DELETE)} duplicate fields")
        print(f"Keeping field {FIELD_TO_KEEP} as the active 'Call History' field")
        print("=" * 70)
        
        sys.exit(0 if success_count == len(FIELDS_TO_DELETE) else 1)
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()