#!/usr/bin/env python3
"""
Script to verify V4.0 enriched data fields in Master Lead App
Validates all 11 enriched fields from Data Pipeline Integration (Phase 4.0)
App ID: 30549135 (Master Lead)
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
MASTER_LEAD_APP_ID = '30549135'

# Expected V4.0 enriched fields from config.py
EXPECTED_V4_FIELDS = {
    274896114: {
        'name': 'Lead Score',
        'type': 'number',
        'category': 'Priority Metrics',
        'ui_priority': 1,
        'description': 'Agent routing optimization'
    },
    274896115: {
        'name': 'Lead Tier',
        'type': 'category',
        'category': 'Priority Metrics',
        'ui_priority': 2,
        'description': 'A/B/C tier classification'
    },
    274896116: {
        'name': 'Estimated Property Value',
        'type': 'money',
        'category': 'Deal Qualification',
        'ui_priority': 3,
        'description': 'Financial intelligence'
    },
    274896117: {
        'name': 'Equity Percentage',
        'type': 'number',
        'category': 'Deal Qualification',
        'ui_priority': 4,
        'description': 'Deal viability metric'
    },
    274896118: {
        'name': 'Estimated Equity',
        'type': 'money',
        'category': 'Deal Qualification',
        'ui_priority': 5,
        'description': 'Deal sizing intelligence'
    },
    274896119: {
        'name': 'Year Built',
        'type': 'number',
        'category': 'Property Details',
        'ui_priority': 6,
        'description': 'Property context'
    },
    274896120: {
        'name': 'Property Type',
        'type': 'category',
        'category': 'Property Details',
        'ui_priority': 7,
        'description': 'SFR/Condo/etc classification'
    },
    274896121: {
        'name': 'APN',
        'type': 'text',
        'category': 'Contact & Context',
        'ui_priority': 8,
        'description': 'County lookup key (not displayed in UI)'
    },
    274896122: {
        'name': 'Validated Mailing Address',
        'type': 'text',
        'category': 'Contact & Context',
        'ui_priority': 9,
        'description': 'USPS-validated contact address'
    },
    274896123: {
        'name': 'First Publication Date',
        'type': 'date',
        'category': 'Timeline & Compliance',
        'ui_priority': 10,
        'description': 'TCPA compliance tracking'
    },
    274896414: {
        'name': 'Law Firm Name',
        'type': 'category',
        'category': 'Timeline & Compliance',
        'ui_priority': 11,
        'description': 'Legal context intelligence'
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
            raise Exception(f"Auth error: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Authentication failed: {e}")

def get_app_fields(access_token, app_id):
    """Get current app field structure"""
    print(f"Querying Master Lead app {app_id} for enriched fields...")
    
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
            raise Exception(f"API error: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Failed to get app fields: {e}")

def verify_v4_enriched_fields(current_fields):
    """Verify V4.0 enriched fields are present and correctly configured"""
    print("=" * 80)
    print("V4.0 ENRICHED FIELDS VALIDATION REPORT")
    print("=" * 80)
    
    # Create lookup of current fields
    current_field_map = {f.get('field_id'): f for f in current_fields}
    
    verification_results = {
        'fields_validated': [],
        'fields_missing': [],
        'type_mismatches': [],
        'all_fields_valid': True
    }
    
    print("\nVALIDATING 11 ENRICHED FIELDS FROM DATA PIPELINE INTEGRATION")
    print("-" * 80)
    
    # Group fields by category for organized output
    categories = {}
    for field_id, spec in EXPECTED_V4_FIELDS.items():
        cat = spec['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((field_id, spec))
    
    # Verify each field
    for category_name in ['Priority Metrics', 'Deal Qualification', 'Property Details', 
                          'Contact & Context', 'Timeline & Compliance']:
        if category_name in categories:
            print(f"\n{category_name}:")
            print("-" * 80)
            
            for field_id, spec in sorted(categories[category_name], key=lambda x: x[1]['ui_priority']):
                if field_id in current_field_map:
                    field = current_field_map[field_id]
                    actual_type = field.get('type')
                    expected_type = spec['type']
                    
                    # Check type match
                    type_match = actual_type == expected_type
                    status = "✅" if type_match else "⚠️"
                    
                    verification_results['fields_validated'].append({
                        'field_id': field_id,
                        'name': spec['name'],
                        'expected_type': expected_type,
                        'actual_type': actual_type,
                        'type_match': type_match,
                        'ui_priority': spec['ui_priority']
                    })
                    
                    type_info = f"Type: {actual_type}"
                    if not type_match:
                        type_info += f" (Expected: {expected_type})"
                        verification_results['type_mismatches'].append({
                            'field_id': field_id,
                            'name': spec['name'],
                            'expected': expected_type,
                            'actual': actual_type
                        })
                        verification_results['all_fields_valid'] = False
                    
                    print(f"{status} [{spec['ui_priority']:2d}] {spec['name']:<30} (ID: {field_id})")
                    print(f"         {type_info}")
                    print(f"         Purpose: {spec['description']}")
                else:
                    print(f"❌ [{spec['ui_priority']:2d}] {spec['name']:<30} (ID: {field_id})")
                    print(f"         STATUS: FIELD NOT FOUND IN APP")
                    verification_results['fields_missing'].append({
                        'field_id': field_id,
                        'name': spec['name'],
                        'type': spec['type']
                    })
                    verification_results['all_fields_valid'] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    fields_present = len(verification_results['fields_validated'])
    fields_missing = len(verification_results['fields_missing'])
    type_mismatches = len(verification_results['type_mismatches'])
    
    print(f"\n✅ Fields Present: {fields_present}/11")
    print(f"❌ Fields Missing: {fields_missing}")
    print(f"⚠️  Type Mismatches: {type_mismatches}")
    
    if verification_results['fields_missing']:
        print("\n⚠️  MISSING FIELDS:")
        for field in verification_results['fields_missing']:
            print(f"   - {field['name']} (ID: {field['field_id']}, Type: {field['type']})")
    
    if verification_results['type_mismatches']:
        print("\n⚠️  TYPE MISMATCHES:")
        for field in verification_results['type_mismatches']:
            print(f"   - {field['name']}: Expected {field['expected']}, Got {field['actual']}")
    
    # Final verdict
    if verification_results['all_fields_valid'] and fields_present == 11:
        print("\n🎉 VALIDATION PASSED!")
        print("   All 11 V4.0 enriched fields are present and correctly configured.")
        print("   ✅ DATA TEAM APPROVED TO PROCEED WITH PHASE 2")
        return True, verification_results
    else:
        print("\n❌ VALIDATION FAILED!")
        print("   V4.0 enriched fields schema is incomplete or misconfigured.")
        print("   ⚠️  DATA TEAM BLOCKED - CRM Team must fix schema issues")
        return False, verification_results

def main():
    """Main validation function"""
    print("=" * 80)
    print("Master Lead App - V4.0 Enriched Fields Validation")
    print("=" * 80)
    print(f"\nTarget App ID: {MASTER_LEAD_APP_ID}")
    print(f"Reference: docs/integration_contracts/podio-schema-v1.1.json")
    print(f"Validating: 11 enriched fields from Data Pipeline Integration\n")
    
    try:
        # Authenticate
        access_token = get_podio_token()
        
        # Get current fields
        current_fields = get_app_fields(access_token, MASTER_LEAD_APP_ID)
        
        # Verify V4.0 enriched fields
        passed, results = verify_v4_enriched_fields(current_fields)
        
        # Save results
        output_file = 'scripts/v4_enriched_fields_validation.json'
        with open(output_file, 'w') as f:
            json.dump({
                'app_id': MASTER_LEAD_APP_ID,
                'validation_passed': passed,
                'total_fields_in_app': len(current_fields),
                'enriched_fields_validated': len(results['fields_validated']),
                'enriched_fields_missing': len(results['fields_missing']),
                'type_mismatches': len(results['type_mismatches']),
                'data_team_authorization': 'APPROVED' if passed else 'BLOCKED',
                'results': results
            }, f, indent=2)
        print(f"\n💾 Validation results saved to: {output_file}")
        
        print("=" * 80)
        
        # Exit with appropriate code
        sys.exit(0 if passed else 1)
        
    except Exception as e:
        print(f"\n❌ Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()