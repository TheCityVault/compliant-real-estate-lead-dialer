#!/usr/bin/env python3
"""
Script to verify the Call Activity App schema matches V2.0 specifications
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

# Expected V2.0 schema from workspace_schema_development_plan.md
EXPECTED_SCHEMA = {
    'v2_fields': {
        274851083: {
            'name': 'Disposition Code',
            'type': 'category',
            'required': True,
            'description': 'Primary reporting metric'
        },
        274851084: {
            'name': 'Agent Notes / Summary',
            'type': 'text',
            'required': False,
            'description': 'Continuity context for follow-up'
        },
        274851085: {
            'name': 'Seller Motivation Level',
            'type': 'category',
            'required': False,
            'description': 'Lead prioritization metric'
        },
        274851086: {
            'name': 'Next Action Date',
            'type': 'date',
            'required': False,  # Conditional based on disposition
            'description': 'Schedules next touchpoint'
        },
        274851087: {
            'name': 'Target Asking Price',
            'type': 'money',
            'required': False,
            'description': 'Pipeline revenue forecasting'
        }
    },
    'core_fields': {
        274769797: 'Title',
        274769798: 'Relationship',  # CRITICAL - links to lead
        274769799: 'Date of Call',
        274769800: 'Call Duration (seconds)',
        274769801: 'Recording URL'
    },
    'deleted_legacy_fields': {
        274769802: 'CALL_OUTCOME',
        274769803: 'MOTIVATION_SCORE',
        274769804: 'Disposition Notes',
        274769805: 'SCHEDULE CALLBACK'
    }
}

def get_podio_token():
    """Get Podio OAuth access token"""
    print("Authenticating with Podio...")
    
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
            token_data = response.json()
            print("✅ Authentication successful\n")
            return token_data.get('access_token')
        else:
            raise Exception(f"Auth error: {response.status_code}")
    except Exception as e:
        raise Exception(f"Authentication failed: {e}")

def get_app_fields(access_token, app_id):
    """Get current app field structure"""
    print(f"Querying app {app_id} for current fields...")
    
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
            print(f"✅ Retrieved app data\n")
            return app_data.get('fields', [])
        else:
            raise Exception(f"API error: {response.status_code}")
    except Exception as e:
        raise Exception(f"Failed to get app fields: {e}")

def verify_schema(current_fields):
    """Verify current schema matches V2.0 specifications"""
    print("=" * 70)
    print("SCHEMA VERIFICATION REPORT")
    print("=" * 70)
    
    # Create lookup of current fields
    current_field_map = {f.get('field_id'): f for f in current_fields}
    
    verification_results = {
        'v2_fields_present': [],
        'v2_fields_missing': [],
        'core_fields_present': [],
        'core_fields_missing': [],
        'legacy_fields_found': [],
        'unexpected_fields': []
    }
    
    # Check V2.0 fields
    print("\n1. V2.0 SCHEMA FIELDS (from workspace_schema_development_plan.md)")
    print("-" * 70)
    for field_id, spec in EXPECTED_SCHEMA['v2_fields'].items():
        if field_id in current_field_map:
            field = current_field_map[field_id]
            status = "✅ PRESENT"
            verification_results['v2_fields_present'].append({
                'field_id': field_id,
                'name': field.get('label'),
                'type': field.get('type'),
                'required': spec['required']
            })
            print(f"{status} | {spec['name']} ({field_id})")
            print(f"         Type: {field.get('type')} | Required: {spec['required']}")
            print(f"         Purpose: {spec['description']}")
        else:
            status = "❌ MISSING"
            verification_results['v2_fields_missing'].append(spec['name'])
            print(f"{status} | {spec['name']} ({field_id}) - CRITICAL ERROR!")
    
    # Check core system fields
    print(f"\n2. CORE SYSTEM FIELDS")
    print("-" * 70)
    for field_id, name in EXPECTED_SCHEMA['core_fields'].items():
        if field_id in current_field_map:
            status = "✅ PRESENT"
            verification_results['core_fields_present'].append(name)
            critical = " (CRITICAL - Links to Lead)" if field_id == 274769798 else ""
            print(f"{status} | {name} ({field_id}){critical}")
        else:
            status = "❌ MISSING"
            verification_results['core_fields_missing'].append(name)
            print(f"{status} | {name} ({field_id}) - ERROR!")
    
    # Check legacy fields are deleted
    print(f"\n3. LEGACY FIELDS (Should be DELETED)")
    print("-" * 70)
    legacy_found = False
    for field_id, name in EXPECTED_SCHEMA['deleted_legacy_fields'].items():
        if field_id in current_field_map:
            status = "🚨 STILL EXISTS"
            verification_results['legacy_fields_found'].append({
                'field_id': field_id,
                'name': name
            })
            legacy_found = True
            print(f"{status} | {name} ({field_id}) - SHOULD BE DELETED!")
        else:
            status = "✅ DELETED"
            print(f"{status} | {name} ({field_id})")
    
    if not legacy_found:
        print("   🎉 All legacy fields successfully removed!")
    
    # Check for unexpected fields
    print(f"\n4. CURRENT FIELD INVENTORY")
    print("-" * 70)
    print(f"Total fields in app: {len(current_fields)}")
    
    expected_field_ids = set(
        list(EXPECTED_SCHEMA['v2_fields'].keys()) +
        list(EXPECTED_SCHEMA['core_fields'].keys())
    )
    
    for field in current_fields:
        field_id = field.get('field_id')
        if field_id not in expected_field_ids:
            verification_results['unexpected_fields'].append({
                'field_id': field_id,
                'name': field.get('label'),
                'type': field.get('type')
            })
    
    if verification_results['unexpected_fields']:
        print("\n⚠️  Unexpected fields found:")
        for field in verification_results['unexpected_fields']:
            print(f"   - {field['name']} ({field['field_id']}) - Type: {field['type']}")
    
    # Final verdict
    print(f"\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    all_v2_present = len(verification_results['v2_fields_missing']) == 0
    all_core_present = len(verification_results['core_fields_missing']) == 0
    no_legacy = len(verification_results['legacy_fields_found']) == 0
    
    print(f"\n✅ V2.0 Fields: {len(verification_results['v2_fields_present'])}/5 present")
    print(f"✅ Core Fields: {len(verification_results['core_fields_present'])}/5 present")
    print(f"✅ Legacy Fields Removed: {no_legacy}")
    
    if all_v2_present and all_core_present and no_legacy:
        print("\n🎉 SCHEMA VERIFICATION PASSED!")
        print("   App structure matches workspace_schema_development_plan.md")
        return True, verification_results
    else:
        print("\n❌ SCHEMA VERIFICATION FAILED!")
        if verification_results['v2_fields_missing']:
            print(f"   Missing V2.0 fields: {', '.join(verification_results['v2_fields_missing'])}")
        if verification_results['core_fields_missing']:
            print(f"   Missing core fields: {', '.join(verification_results['core_fields_missing'])}")
        if verification_results['legacy_fields_found']:
            legacy_names = [f['name'] for f in verification_results['legacy_fields_found']]
            print(f"   Legacy fields still present: {', '.join(legacy_names)}")
        return False, verification_results

def main():
    """Main verification function"""
    print("=" * 70)
    print("Call Activity App - V2.0 Schema Verification")
    print("=" * 70)
    print(f"\nTarget App ID: {PODIO_CALL_ACTIVITY_APP_ID}")
    print(f"Reference: docs/workspace_schema_development_plan.md\n")
    
    if not PODIO_CALL_ACTIVITY_APP_ID:
        print("❌ Error: PODIO_CALL_ACTIVITY_APP_ID not set")
        sys.exit(1)
    
    try:
        # Authenticate
        access_token = get_podio_token()
        
        # Get current fields
        current_fields = get_app_fields(access_token, PODIO_CALL_ACTIVITY_APP_ID)
        
        # Verify schema
        passed, results = verify_schema(current_fields)
        
        # Save results
        output_file = 'scripts/schema_verification.json'
        with open(output_file, 'w') as f:
            json.dump({
                'app_id': PODIO_CALL_ACTIVITY_APP_ID,
                'verification_passed': passed,
                'field_count': len(current_fields),
                'results': results
            }, f, indent=2)
        print(f"\n💾 Verification results saved to: {output_file}")
        
        print("=" * 70)
        
        # Exit with appropriate code
        sys.exit(0 if passed else 1)
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()