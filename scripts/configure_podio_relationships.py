#!/usr/bin/env python3
"""
Script to configure bi-directional relationship between Master Lead and Call Activity apps
Task: Programmatically configure Podio relationship fields via API

Critical Configuration:
1. Update Call Activity field 274769798 to reference Master Lead app (30549135)
2. Add new "Call History" field to Master Lead app to reference Call Activity (30549170)

API References:
- Update field: https://developers.podio.com/doc/applications/update-an-app-field-22356
- Add field: https://developers.podio.com/doc/applications/add-new-app-field-22354
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Podio credentials
PODIO_CLIENT_ID = os.environ.get('PODIO_CLIENT_ID')
PODIO_CLIENT_SECRET = os.environ.get('PODIO_CLIENT_SECRET')
PODIO_USERNAME = os.environ.get('PODIO_USERNAME')
PODIO_PASSWORD = os.environ.get('PODIO_PASSWORD')
PODIO_MASTER_LEAD_APP_ID = os.environ.get('PODIO_MASTER_LEAD_APP_ID')
PODIO_CALL_ACTIVITY_APP_ID = os.environ.get('PODIO_CALL_ACTIVITY_APP_ID')

# Known field IDs
CALL_ACTIVITY_RELATIONSHIP_FIELD_ID = 274769798

def get_podio_token():
    """Get Podio OAuth access token"""
    print("Authenticating with Podio...")
    
    if not all([PODIO_CLIENT_ID, PODIO_CLIENT_SECRET, PODIO_USERNAME, PODIO_PASSWORD]):
        raise Exception("Podio credentials not fully configured. Check .env file.")
    
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

def update_call_activity_relationship_field(access_token):
    """
    Update Call Activity relationship field to reference Master Lead app
    API: PUT /app/{app_id}/field/{field_id}
    """
    print("=" * 70)
    print("TASK 1: Update Call Activity Relationship Field")
    print("=" * 70)
    print(f"\nApp ID: {PODIO_CALL_ACTIVITY_APP_ID}")
    print(f"Field ID: {CALL_ACTIVITY_RELATIONSHIP_FIELD_ID}")
    print(f"Configuring to reference Master Lead app ({PODIO_MASTER_LEAD_APP_ID})")
    
    try:
        # Configuration payload - Podio requires app IDs as plain integers in array
        config_payload = {
            "label": "Relationship",
            "config": {
                "description": "Links this call to a Master Lead item",
                "settings": {
                    "referenced_apps": [int(PODIO_MASTER_LEAD_APP_ID)],
                    "multiple": False,
                    "required": True
                }
            }
        }
        
        print(f"\nPayload: {json.dumps(config_payload, indent=2)}")
        
        response = requests.put(
            f'https://api.podio.com/app/{PODIO_CALL_ACTIVITY_APP_ID}/field/{CALL_ACTIVITY_RELATIONSHIP_FIELD_ID}',
            headers={
                'Authorization': f'OAuth2 {access_token}',
                'Content-Type': 'application/json'
            },
            json=config_payload
        )
        
        print(f"\nAPI Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Call Activity relationship field updated successfully")
            print("\nConfiguration applied:")
            print(f"   - References: Master Lead app ({PODIO_MASTER_LEAD_APP_ID})")
            print(f"   - Multiple values: No (one-to-one)")
            print(f"   - Required: Yes")
            return {
                'success': True,
                'field_id': CALL_ACTIVITY_RELATIONSHIP_FIELD_ID,
                'referenced_app': PODIO_MASTER_LEAD_APP_ID,
                'message': 'Field configured successfully'
            }
        else:
            error_msg = f"API error: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    except Exception as e:
        error_msg = f"Exception updating field: {e}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def add_master_lead_call_history_field(access_token):
    """
    Add "Call History" field to Master Lead app to reference Call Activity app
    API: POST /app/{app_id}/field/
    """
    print("\n" + "=" * 70)
    print("TASK 2: Add 'Call History' Field to Master Lead App")
    print("=" * 70)
    print(f"\nApp ID: {PODIO_MASTER_LEAD_APP_ID}")
    print(f"New Field: Call History (references Call Activity app)")
    
    try:
        # Field configuration payload - POST requires app_id objects, PUT requires integers
        field_config = {
            "type": "app",
            "config": {
                "label": "Call History",
                "description": "Associated Call Activity records",
                "settings": {
                    "referenced_apps": [{"app_id": int(PODIO_CALL_ACTIVITY_APP_ID)}],
                    "multiple": True,
                    "required": False
                }
            }
        }
        
        print(f"\nPayload: {json.dumps(field_config, indent=2)}")
        
        response = requests.post(
            f'https://api.podio.com/app/{PODIO_MASTER_LEAD_APP_ID}/field/',
            headers={
                'Authorization': f'OAuth2 {access_token}',
                'Content-Type': 'application/json'
            },
            json=field_config
        )
        
        print(f"\nAPI Response Status: {response.status_code}")
        
        if response.status_code == 200:
            field_data = response.json()
            field_id = field_data.get('field_id')
            print(f"✅ 'Call History' field added successfully")
            print(f"\n🎯 NEW FIELD ID: {field_id}")
            print("\nConfiguration:")
            print(f"   - Label: Call History")
            print(f"   - References: Call Activity app ({PODIO_CALL_ACTIVITY_APP_ID})")
            print(f"   - Multiple values: Yes (one-to-many)")
            print(f"   - Required: No")
            return {
                'success': True,
                'field_id': field_id,
                'field_label': 'Call History',
                'referenced_app': PODIO_CALL_ACTIVITY_APP_ID,
                'message': 'Field created successfully'
            }
        elif response.status_code == 400 and 'already exists' in response.text.lower():
            print("⚠️  Field with label 'Call History' may already exist")
            print("   Attempting to find existing field...")
            
            # Try to get app structure to find field ID
            try:
                app_response = requests.get(
                    f'https://api.podio.com/app/{PODIO_MASTER_LEAD_APP_ID}',
                    headers={
                        'Authorization': f'OAuth2 {access_token}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if app_response.status_code == 200:
                    app_data = app_response.json()
                    for field in app_data.get('fields', []):
                        if field.get('label') == 'Call History' and field.get('type') == 'app':
                            existing_field_id = field.get('field_id')
                            print(f"   Found existing field: {existing_field_id}")
                            return {
                                'success': True,
                                'field_id': existing_field_id,
                                'field_label': 'Call History',
                                'already_existed': True,
                                'message': 'Field already exists'
                            }
            except:
                pass
            
            return {
                'success': False,
                'error': 'Field already exists but could not retrieve field ID'
            }
        else:
            error_msg = f"API error: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    except Exception as e:
        error_msg = f"Exception adding field: {e}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def verify_configuration(access_token, call_activity_result, master_lead_result):
    """Verify that both relationship fields are properly configured"""
    print("\n" + "=" * 70)
    print("VERIFICATION: Check Relationship Configuration")
    print("=" * 70)
    
    all_success = True
    
    # Verify Call Activity → Master Lead
    print("\n1. Call Activity → Master Lead:")
    if call_activity_result.get('success'):
        print(f"   ✅ CONFIGURED")
        print(f"      Field ID: {call_activity_result.get('field_id')}")
    else:
        print(f"   ❌ FAILED: {call_activity_result.get('error')}")
        all_success = False
    
    # Verify Master Lead → Call Activity
    print("\n2. Master Lead → Call Activity:")
    if master_lead_result.get('success'):
        print(f"   ✅ CONFIGURED")
        print(f"      Field ID: {master_lead_result.get('field_id')}")
        print(f"      Field Label: {master_lead_result.get('field_label')}")
        if master_lead_result.get('already_existed'):
            print(f"      Status: Already existed")
        else:
            print(f"      Status: Newly created")
    else:
        print(f"   ❌ FAILED: {master_lead_result.get('error')}")
        all_success = False
    
    print("\n" + "=" * 70)
    if all_success:
        print("🎉 BI-DIRECTIONAL RELATIONSHIP FULLY CONFIGURED!")
        print("=" * 70)
        print("\n✅ Configuration complete:")
        print(f"   - Call Activity field {CALL_ACTIVITY_RELATIONSHIP_FIELD_ID} → Master Lead app {PODIO_MASTER_LEAD_APP_ID}")
        print(f"   - Master Lead field {master_lead_result.get('field_id')} → Call Activity app {PODIO_CALL_ACTIVITY_APP_ID}")
        print("\n✅ Ready for V2.0 backend implementation")
    else:
        print("⚠️  CONFIGURATION INCOMPLETE")
        print("=" * 70)
        print("\n❌ Some operations failed. Review errors above.")
    
    return all_success

def save_results(call_activity_result, master_lead_result, success):
    """Save configuration results to JSON file"""
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'configuration_success': success,
        'call_activity_field_update': call_activity_result,
        'master_lead_field_creation': master_lead_result,
        'field_ids': {
            'call_activity_relationship_field_id': call_activity_result.get('field_id') if call_activity_result.get('success') else None,
            'master_lead_call_history_field_id': master_lead_result.get('field_id') if master_lead_result.get('success') else None,
            'master_lead_app_id': PODIO_MASTER_LEAD_APP_ID,
            'call_activity_app_id': PODIO_CALL_ACTIVITY_APP_ID
        }
    }
    
    output_file = 'scripts/relationship_configuration_results.json'
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Configuration results saved to: {output_file}")
        return output_file
    except Exception as e:
        print(f"\n⚠️  Warning: Could not save results to file: {e}")
        return None

def main():
    """Main configuration function"""
    print("=" * 70)
    print("PODIO RELATIONSHIP CONFIGURATION")
    print("Bi-Directional Master Lead ↔ Call Activity")
    print("=" * 70)
    print(f"\nMaster Lead App ID: {PODIO_MASTER_LEAD_APP_ID}")
    print(f"Call Activity App ID: {PODIO_CALL_ACTIVITY_APP_ID}")
    print(f"\nThis script will:")
    print("  1. Update Call Activity field 274769798 to reference Master Lead")
    print("  2. Add 'Call History' field to Master Lead to reference Call Activity")
    print("=" * 70 + "\n")
    
    # Validate environment variables
    if not all([PODIO_MASTER_LEAD_APP_ID, PODIO_CALL_ACTIVITY_APP_ID]):
        print("❌ Error: App IDs not properly configured in .env")
        sys.exit(1)
    
    try:
        # 1. Authenticate
        access_token = get_podio_token()
        
        # 2. Update Call Activity relationship field
        call_activity_result = update_call_activity_relationship_field(access_token)
        
        # 3. Add Master Lead call history field
        master_lead_result = add_master_lead_call_history_field(access_token)
        
        # 4. Verify configuration
        success = verify_configuration(access_token, call_activity_result, master_lead_result)
        
        # 5. Save results
        save_results(call_activity_result, master_lead_result, success)
        
        # 6. Final summary
        print("\n" + "=" * 70)
        print("CONFIGURATION COMPLETE")
        print("=" * 70)
        
        if success:
            print("\n✅ Next Steps:")
            print("   1. Run: python scripts/verify_master_lead_relationships.py")
            print("   2. Verify status shows FULLY_CONFIGURED")
            print("   3. Test creating linked items in Podio UI")
            print("   4. Update backend code to use relationship fields")
            print("   5. Proceed with V2.0 implementation")
            
            if master_lead_result.get('field_id'):
                print(f"\n📋 Important Field IDs:")
                print(f"   CALL_ACTIVITY_RELATIONSHIP_FIELD_ID = {CALL_ACTIVITY_RELATIONSHIP_FIELD_ID}")
                print(f"   MASTER_LEAD_CALL_HISTORY_FIELD_ID = {master_lead_result.get('field_id')}")
        else:
            print("\n⚠️  Configuration incomplete. Review errors and try again.")
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ Configuration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()