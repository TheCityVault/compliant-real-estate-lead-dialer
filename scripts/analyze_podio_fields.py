#!/usr/bin/env python3
"""
Script to analyze Call Activity App fields and identify duplicates/legacy fields
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
    if not all([PODIO_CLIENT_ID, PODIO_CLIENT_SECRET, PODIO_USERNAME, PODIO_PASSWORD]):
        raise Exception("Podio credentials not fully configured.")
    
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
            return response.json().get('access_token')
        else:
            raise Exception(f"Error getting Podio token: {response.status_code}")
    except Exception as e:
        raise Exception(f"Authentication error: {e}")

def get_app_fields(access_token, app_id):
    """Get all fields from the app"""
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
            return app_data.get('fields', [])
        else:
            raise Exception(f"Error fetching app: {response.status_code}")
    except Exception as e:
        raise Exception(f"Error getting fields: {e}")

def analyze_fields(fields):
    """Analyze fields for duplicates and categorize them"""
    
    # Define V2.0 field IDs from our script output
    v2_fields = {
        274851083: 'Disposition Code',
        274851084: 'Agent Notes / Summary',
        274851085: 'Seller Motivation Level',
        274851086: 'Next Action Date',
        274851087: 'Target Asking Price'
    }
    
    # Categorize fields
    core_fields = []
    v2_new_fields = []
    legacy_fields = []
    
    for field in fields:
        field_id = field.get('field_id')
        field_label = field.get('label')
        field_type = field.get('type')
        
        if field_id in v2_fields:
            v2_new_fields.append(field)
        elif field_label in ['Title', 'Relationship', 'Date of Call', 'Call Duration (seconds)', 'Recording URL']:
            core_fields.append(field)
        else:
            legacy_fields.append(field)
    
    return {
        'core': core_fields,
        'v2_new': v2_new_fields,
        'legacy': legacy_fields
    }

def main():
    print("=" * 80)
    print("Call Activity App - Field Analysis")
    print("=" * 80)
    
    # Authenticate
    print("\nAuthenticating with Podio...")
    try:
        access_token = get_podio_token()
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)
    
    # Get fields
    print(f"\nFetching fields from app {PODIO_CALL_ACTIVITY_APP_ID}...")
    try:
        fields = get_app_fields(access_token, PODIO_CALL_ACTIVITY_APP_ID)
        print(f"✅ Found {len(fields)} total fields")
    except Exception as e:
        print(f"❌ Error fetching fields: {e}")
        sys.exit(1)
    
    # Analyze
    categorized = analyze_fields(fields)
    
    print("\n" + "=" * 80)
    print("FIELD ANALYSIS RESULTS")
    print("=" * 80)
    
    # Core fields (should keep)
    print(f"\n📌 CORE FIELDS ({len(categorized['core'])} fields) - Essential system fields")
    print("-" * 80)
    for field in categorized['core']:
        print(f"  ✅ {field['label']:<30} | Type: {field['type']:<10} | ID: {field['field_id']}")
    
    # V2.0 new fields (newly added)
    print(f"\n🆕 V2.0 NEW FIELDS ({len(categorized['v2_new'])} fields) - Newly added for V2.0")
    print("-" * 80)
    for field in categorized['v2_new']:
        print(f"  ✅ {field['label']:<30} | Type: {field['type']:<10} | ID: {field['field_id']}")
    
    # Legacy fields (duplicates/old version)
    print(f"\n⚠️  LEGACY/DUPLICATE FIELDS ({len(categorized['legacy'])} fields) - May need cleanup")
    print("-" * 80)
    for field in categorized['legacy']:
        required = "REQUIRED" if field.get('config', {}).get('required') else "optional"
        print(f"  ⚠️  {field['label']:<30} | Type: {field['type']:<10} | ID: {field['field_id']} | {required}")
    
    # Identify specific duplicates
    print("\n" + "=" * 80)
    print("DUPLICATE FIELD MAPPING")
    print("=" * 80)
    
    duplicates = [
        {
            'legacy': 'CALL_OUTCOME',
            'legacy_id': 274769802,
            'v2': 'Disposition Code',
            'v2_id': 274851083,
            'type': 'category',
            'purpose': 'Call outcome/disposition'
        },
        {
            'legacy': 'Disposition Notes',
            'legacy_id': 274769804,
            'v2': 'Agent Notes / Summary',
            'v2_id': 274851084,
            'type': 'text',
            'purpose': 'Agent notes from call'
        },
        {
            'legacy': 'MOTIVATION_SCORE',
            'legacy_id': 274769803,
            'v2': 'Seller Motivation Level',
            'v2_id': 274851085,
            'type': 'category',
            'purpose': 'Seller motivation assessment'
        },
        {
            'legacy': 'SCHEDULE CALLBACK',
            'legacy_id': 274769805,
            'v2': 'Next Action Date',
            'v2_id': 274851086,
            'type': 'date',
            'purpose': 'Next follow-up date'
        }
    ]
    
    print("\nThe following legacy fields are duplicates of V2.0 fields:\n")
    for dup in duplicates:
        print(f"❌ LEGACY: {dup['legacy']} (ID: {dup['legacy_id']})")
        print(f"   ↓ REPLACED BY ↓")
        print(f"✅ V2.0:   {dup['v2']} (ID: {dup['v2_id']})")
        print(f"   Purpose: {dup['purpose']}")
        print()
    
    # Save analysis to file
    output = {
        'app_id': PODIO_CALL_ACTIVITY_APP_ID,
        'total_fields': len(fields),
        'categorized': {
            'core_fields': [{'id': f['field_id'], 'label': f['label'], 'type': f['type']} for f in categorized['core']],
            'v2_new_fields': [{'id': f['field_id'], 'label': f['label'], 'type': f['type']} for f in categorized['v2_new']],
            'legacy_fields': [{'id': f['field_id'], 'label': f['label'], 'type': f['type']} for f in categorized['legacy']]
        },
        'duplicates': duplicates,
        'recommendations': [
            "Delete legacy fields after confirming V2.0 fields are properly integrated",
            "Update any existing data to use V2.0 field IDs",
            "Test workspace UI with V2.0 fields before removing legacy fields"
        ]
    }
    
    output_file = 'scripts/field_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Analysis saved to: {output_file}")
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("""
1. ✅ V2.0 fields are now created and ready to use
2. ⚠️  Legacy fields (CALL_OUTCOME, MOTIVATION_SCORE, etc.) are duplicates
3. 📝 Before deletion, ensure:
   - Workspace UI is updated to use V2.0 field IDs
   - Any existing call data is migrated (if needed)
   - Backend code references V2.0 field IDs only
4. 🧹 Recommended cleanup: Delete the 4 legacy fields listed above
5. 🆕 New field added: Target Asking Price (no legacy equivalent)
""")
    
    print("=" * 80)

if __name__ == '__main__':
    main()