#!/usr/bin/env python3
"""
Script to delete legacy duplicate fields from Podio Call Activity App
App ID: 30549170

CRITICAL SAFETY: This script ONLY deletes the 4 legacy fields that have been
replaced by V2.0 schema fields. It will NOT delete:
- Core system fields (274769797-274769801)
- V2.0 new fields (274851083-274851087)
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
PODIO_CALL_ACTIVITY_APP_ID = os.environ.get('PODIO_CALL_ACTIVITY_APP_ID')

# CRITICAL: Legacy fields to delete (and ONLY these fields)
LEGACY_FIELDS_TO_DELETE = {
    274769802: {
        'name': 'CALL_OUTCOME',
        'replaced_by': 'Disposition Code',
        'new_field_id': 274851083
    },
    274769804: {
        'name': 'Disposition Notes',
        'replaced_by': 'Agent Notes / Summary',
        'new_field_id': 274851084
    },
    274769803: {
        'name': 'MOTIVATION_SCORE',
        'replaced_by': 'Seller Motivation Level',
        'new_field_id': 274851085
    },
    274769805: {
        'name': 'SCHEDULE CALLBACK',
        'replaced_by': 'Next Action Date',
        'new_field_id': 274851086
    }
}

# PROTECTED: Fields that must NEVER be deleted
PROTECTED_FIELD_IDS = [
    274769797,  # Title
    274769798,  # Relationship (CRITICAL - links to lead)
    274769799,  # Date of Call
    274769800,  # Call Duration (seconds)
    274769801,  # Recording URL
    274851083,  # Disposition Code (V2.0)
    274851084,  # Agent Notes / Summary (V2.0)
    274851085,  # Seller Motivation Level (V2.0)
    274851086,  # Next Action Date (V2.0)
    274851087   # Target Asking Price (V2.0)
]

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

def verify_field_before_deletion(access_token, app_id, field_id):
    """Verify field details before deletion (safety check)"""
    try:
        # Get app details to see current fields
        response = requests.get(
            f'https://api.podio.com/app/{app_id}',
            headers={
                'Authorization': f'OAuth2 {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code == 200:
            app_data = response.json()
            fields = app_data.get('fields', [])
            
            # Find the specific field
            for field in fields:
                if field.get('field_id') == field_id:
                    return {
                        'exists': True,
                        'field_id': field.get('field_id'),
                        'label': field.get('label'),
                        'type': field.get('type'),
                        'external_id': field.get('external_id')
                    }
            
            return {'exists': False}
        else:
            print(f"⚠️  Warning: Could not verify field {field_id}: {response.status_code}")
            return {'exists': False}
    except Exception as e:
        print(f"⚠️  Warning: Error verifying field {field_id}: {e}")
        return {'exists': False}

def delete_field(access_token, app_id, field_id, field_info):
    """Delete a single legacy field from Podio app"""
    field_name = field_info['name']
    print(f"\nDeleting legacy field: {field_name} (ID: {field_id})...")
    
    # CRITICAL SAFETY CHECK: Ensure we're not deleting a protected field
    if field_id in PROTECTED_FIELD_IDS:
        error_msg = f"CRITICAL ERROR: Attempted to delete PROTECTED field {field_id}. Aborting!"
        print(f"🚨 {error_msg}")
        return {
            'success': False,
            'field_id': field_id,
            'field_name': field_name,
            'error': 'Attempted to delete protected field',
            'critical_error': True
        }
    
    # Verify field exists before attempting deletion
    verification = verify_field_before_deletion(access_token, app_id, field_id)
    
    if not verification.get('exists'):
        print(f"⚠️  Field {field_id} ({field_name}) does not exist or already deleted.")
        return {
            'success': False,
            'field_id': field_id,
            'field_name': field_name,
            'error': 'Field does not exist',
            'already_deleted': True
        }
    
    # Confirm field name matches expected
    actual_label = verification.get('label', '')
    if actual_label != field_name:
        print(f"⚠️  WARNING: Field label mismatch!")
        print(f"   Expected: {field_name}")
        print(f"   Actual: {actual_label}")
        print(f"   Proceeding with deletion of field ID {field_id}...")
    
    try:
        # DELETE the field
        response = requests.delete(
            f'https://api.podio.com/app/{app_id}/field/{field_id}',
            headers={
                'Authorization': f'OAuth2 {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code == 204 or response.status_code == 200:
            print(f"✅ Field '{field_name}' (ID: {field_id}) deleted successfully")
            print(f"   → Replaced by: {field_info['replaced_by']} (ID: {field_info['new_field_id']})")
            return {
                'success': True,
                'field_id': field_id,
                'field_name': field_name,
                'replaced_by': field_info['replaced_by'],
                'new_field_id': field_info['new_field_id'],
                'timestamp': datetime.utcnow().isoformat()
            }
        elif response.status_code == 404:
            print(f"⚠️  Field '{field_name}' (ID: {field_id}) not found (may already be deleted)")
            return {
                'success': False,
                'field_id': field_id,
                'field_name': field_name,
                'error': 'Field not found (404)',
                'already_deleted': True
            }
        else:
            error_msg = f"Error deleting field '{field_name}': {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'field_id': field_id,
                'field_name': field_name,
                'error': error_msg,
                'status_code': response.status_code
            }
    except Exception as e:
        error_msg = f"Exception deleting field '{field_name}': {e}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'field_id': field_id,
            'field_name': field_name,
            'error': str(e)
        }

def main():
    """Main function to delete all legacy fields"""
    print("=" * 70)
    print("Podio Call Activity App - Legacy Field Cleanup")
    print("=" * 70)
    print("\n🗑️  DELETING 4 LEGACY DUPLICATE FIELDS")
    print("=" * 70)
    
    if not PODIO_CALL_ACTIVITY_APP_ID:
        print("❌ Error: PODIO_CALL_ACTIVITY_APP_ID not set in environment variables")
        sys.exit(1)
    
    print(f"\nTarget App ID: {PODIO_CALL_ACTIVITY_APP_ID}")
    print(f"\nLegacy fields to delete:")
    for field_id, info in LEGACY_FIELDS_TO_DELETE.items():
        print(f"  • {info['name']} ({field_id}) → {info['replaced_by']} ({info['new_field_id']})")
    
    # Safety confirmation
    print("\n" + "=" * 70)
    print("⚠️  SAFETY CHECK: Protected fields that will NOT be deleted:")
    print("=" * 70)
    print("  • Title (274769797)")
    print("  • Relationship (274769798) - CRITICAL")
    print("  • Date of Call (274769799)")
    print("  • Call Duration (274769800)")
    print("  • Recording URL (274769801)")
    print("  • Disposition Code (274851083) - V2.0")
    print("  • Agent Notes / Summary (274851084) - V2.0")
    print("  • Seller Motivation Level (274851085) - V2.0")
    print("  • Next Action Date (274851086) - V2.0")
    print("  • Target Asking Price (274851087) - V2.0")
    
    # Get Podio access token
    print("\n" + "=" * 70)
    try:
        access_token = get_podio_token()
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)
    
    # Delete each legacy field
    results = []
    print(f"\n" + "=" * 70)
    print("Deletion Process")
    print("=" * 70)
    
    for field_id, field_info in LEGACY_FIELDS_TO_DELETE.items():
        result = delete_field(access_token, PODIO_CALL_ACTIVITY_APP_ID, field_id, field_info)
        results.append(result)
        
        # Check for critical errors
        if result.get('critical_error'):
            print("\n🚨 CRITICAL ERROR DETECTED - ABORTING SCRIPT!")
            sys.exit(1)
    
    # Print summary
    print(f"\n" + "=" * 70)
    print("DELETION SUMMARY")
    print("=" * 70)
    
    successful = [r for r in results if r.get('success')]
    already_deleted = [r for r in results if r.get('already_deleted')]
    failed = [r for r in results if not r.get('success') and not r.get('already_deleted')]
    
    print(f"\n✅ Successfully deleted: {len(successful)} fields")
    print(f"⚠️  Already deleted: {len(already_deleted)} fields")
    print(f"❌ Failed: {len(failed)} fields")
    
    if successful:
        print("\n🗑️  Deleted Legacy Fields:")
        for result in successful:
            print(f"  ✓ {result['field_name']} ({result['field_id']})")
            print(f"    → Replaced by: {result['replaced_by']} ({result['new_field_id']})")
    
    if already_deleted:
        print("\n⚠️  Already Deleted:")
        for result in already_deleted:
            print(f"  - {result['field_name']} ({result['field_id']})")
    
    if failed:
        print("\n❌ Failed Deletions:")
        for result in failed:
            print(f"  ✗ {result['field_name']} ({result['field_id']})")
            print(f"    Error: {result.get('error', 'Unknown error')}")
    
    # Save results to JSON file
    output_file = 'scripts/deletion_log.json'
    try:
        with open(output_file, 'w') as f:
            json.dump({
                'app_id': PODIO_CALL_ACTIVITY_APP_ID,
                'timestamp': datetime.utcnow().isoformat(),
                'deleted_count': len(successful),
                'already_deleted_count': len(already_deleted),
                'failed_count': len(failed),
                'results': results
            }, f, indent=2)
        print(f"\n💾 Deletion log saved to: {output_file}")
    except Exception as e:
        print(f"\n⚠️  Warning: Could not save deletion log: {e}")
    
    print(f"\n" + "=" * 70)
    
    # Return appropriate exit code
    if failed:
        print("⚠️  Completed with errors. Check failed deletions above.")
        sys.exit(1)
    else:
        print("✅ Legacy field cleanup complete!")
        print("\n🎉 Call Activity app now uses clean V2.0 schema only!")
        sys.exit(0)

if __name__ == '__main__':
    main()