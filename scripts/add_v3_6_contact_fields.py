"""
Contract v1.1.3 - Create 5 New Podio Fields (Emergency Patch)

This script:
1. Creates 5 new fields in Podio Master Lead App (ID: 30549135)
2. Includes CRITICAL "Owner Phone Primary" field (enables click-to-dial)
3. Includes BLOCKING "Lead Type" field (required for V4.0)
4. Captures actual field IDs returned by Podio
5. Creates v3_6_field_ids.json with field ID mappings
6. Validates fields after creation via Podio API

BUSINESS IMPACT: Unlocks 0% → 70% dialable lead coverage
CRITICAL PATH: Field IDs must be returned to Data Team within 12 hours
"""

import os
import sys
import json
import requests
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    PODIO_CLIENT_ID,
    PODIO_CLIENT_SECRET,
    PODIO_USERNAME,
    PODIO_PASSWORD,
    MASTER_LEAD_APP_ID
)

# ============================================================================
# OAUTH TOKEN MANAGEMENT
# ============================================================================

def refresh_podio_token():
    """
    Get Podio OAuth access token
    
    Returns:
        str: Access token, or None if authentication fails
    """
    print("=" * 60)
    print("PODIO TOKEN REFRESH")
    print(f"CLIENT_ID present: {bool(PODIO_CLIENT_ID)}")
    print(f"CLIENT_SECRET present: {bool(PODIO_CLIENT_SECRET)}")
    print(f"USERNAME present: {bool(PODIO_USERNAME)}")
    print(f"PASSWORD present: {bool(PODIO_PASSWORD)}")
    print("=" * 60)
    
    if not all([PODIO_CLIENT_ID, PODIO_CLIENT_SECRET, PODIO_USERNAME, PODIO_PASSWORD]):
        print("❌ CRITICAL: Podio credentials not fully configured")
        return None
    
    try:
        # Get OAuth token from Podio
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
            print("✅ Podio token obtained successfully")
            return access_token
        else:
            print(f"❌ ERROR getting Podio token: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception during Podio authentication: {e}")
        return None

# ============================================================================
# FIELD CREATION FUNCTIONS
# ============================================================================

def check_field_exists(token, app_id, field_label):
    """
    Check if a field with the given label already exists in the app
    
    Args:
        token: OAuth access token
        app_id: Podio app ID
        field_label: Field label to check
    
    Returns:
        dict: Field data if exists, None otherwise
    """
    try:
        response = requests.get(
            f'https://api.podio.com/app/{app_id}',
            headers={
                'Authorization': f'OAuth2 {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code == 200:
            app_data = response.json()
            fields = app_data.get('fields', [])
            
            for field in fields:
                if field.get('label') == field_label:
                    return field
        
        return None
            
    except Exception as e:
        print(f"  ⚠️ Exception checking field existence: {e}")
        return None

def create_podio_field(token, app_id, field_config):
    """
    Create a single field in Podio app using POST /app/{app_id}/field
    
    Args:
        token: OAuth access token
        app_id: Podio app ID
        field_config: Dict containing field configuration
    
    Returns:
        dict: Response data with field_id, or None if failed
    """
    try:
        # Check if field already exists
        existing_field = check_field_exists(token, app_id, field_config["label"])
        
        if existing_field:
            print(f"  ⚠️ Field '{field_config['label']}' already exists (ID: {existing_field.get('field_id')})")
            print(f"  ℹ️ Skipping creation, using existing field ID")
            return existing_field
        
        # Build Podio API payload based on field type
        payload = {
            "type": field_config["type"],
            "config": {
                "label": field_config["label"],
                "description": field_config.get("description", ""),
                "required": field_config.get("required", False)
            }
        }
        
        # Add type-specific settings
        if field_config["type"] == "text":
            payload["config"]["settings"] = {
                "size": field_config.get("size", "large")
            }
        elif field_config["type"] == "phone":
            payload["config"]["settings"] = {
                "type": field_config.get("phone_type", "mobile")
            }
        elif field_config["type"] == "email":
            payload["config"]["settings"] = {}
        elif field_config["type"] == "category":
            payload["config"]["settings"] = field_config.get("settings", {})
        
        # Make API request
        response = requests.post(
            f'https://api.podio.com/app/{app_id}/field',
            headers={
                'Authorization': f'OAuth2 {token}',
                'Content-Type': 'application/json'
            },
            json=payload
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"  ❌ API Error: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return None

def validate_fields(token, app_id, expected_field_labels):
    """
    Validate that all expected fields exist in the app
    
    Args:
        token: OAuth access token
        app_id: Podio app ID
        expected_field_labels: List of field labels to validate
    
    Returns:
        bool: True if all fields exist, False otherwise
    """
    try:
        response = requests.get(
            f'https://api.podio.com/app/{app_id}',
            headers={
                'Authorization': f'OAuth2 {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code == 200:
            app_data = response.json()
            fields = app_data.get('fields', [])
            field_labels = [f.get('label') for f in fields]
            
            print("\n" + "=" * 60)
            print("FIELD VALIDATION")
            print("=" * 60)
            
            all_found = True
            for label in expected_field_labels:
                if label in field_labels:
                    print(f"  ✅ {label}")
                else:
                    print(f"  ❌ {label} - NOT FOUND")
                    all_found = False
            
            return all_found
        else:
            print(f"❌ Failed to validate fields: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during validation: {e}")
        return False

# ============================================================================
# CONTRACT v1.1.3 FIELD DEFINITIONS
# ============================================================================

CONTACT_FIELDS_V3_6 = [
    {
        "key": "owner_name",
        "label": "Owner Name",
        "type": "text",
        "size": "medium",
        "section": "Contact Details",
        "priority": 12,
        "description": "Property owner full name from Melissa Property API",
        "required": False
    },
    {
        "key": "owner_phone_primary",
        "label": "Owner Phone Primary",
        "type": "phone",
        "phone_type": "mobile",
        "section": "Contact Details",
        "priority": 13,
        "description": "CRITICAL: Primary phone for click-to-dial functionality. Unlocks 0% → 70% dialable coverage.",
        "required": False,
        "critical": True
    },
    {
        "key": "owner_email_primary",
        "label": "Owner Email Primary",
        "type": "email",
        "section": "Contact Details",
        "priority": 14,
        "description": "Primary email from Melissa Personator API",
        "required": False
    },
    {
        "key": "owner_mailing_address",
        "label": "Owner Mailing Address (Personator)",
        "type": "text",
        "size": "large",
        "section": "Contact Details",
        "priority": 15,
        "description": "Owner mailing address from Personator (distinct from Validated Mailing Address)",
        "required": False
    },
    {
        "key": "lead_type",
        "label": "Lead Type",
        "type": "category",
        "section": "Lead Intelligence Panel",
        "priority": 16,
        "description": "BLOCKS V4.0: Lead type categorization required for deployment",
        "required": True,
        "settings": {
            "options": [
                {"text": "NED Listing", "color": "DCEBD8"},
                {"text": "Probate/Estate", "color": "D5E8EE"},
                {"text": "Absentee Owner", "color": "FFEBBA"},
                {"text": "Tax Lien", "color": "FFD5BA"},
                {"text": "Code Violation", "color": "E4DCEE"},
                {"text": "Foreclosure Auction", "color": "FFDADA"},
                {"text": "Tired Landlord", "color": "DCEBD8"}
            ],
            "multiple": False
        },
        "critical": True
    }
]

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    
    print("\n" + "=" * 60)
    print("CONTRACT v1.1.3 - CREATE 5 CRITICAL PODIO FIELDS")
    print("Emergency Patch: Owner Contact Fields + Lead Type")
    print("=" * 60 + "\n")
    
    # Step 1: Get Podio token
    print(f"🔐 Authenticating with Podio...")
    token = refresh_podio_token()
    
    if not token:
        print("❌ CRITICAL: Cannot proceed without Podio token")
        return
    
    # Step 2: Create fields in priority order
    print(f"\n📋 Creating fields in Master Lead App (ID: {MASTER_LEAD_APP_ID})")
    print("=" * 60)
    
    field_id_mappings = {}
    success_count = 0
    failure_count = 0
    
    # Sort by priority
    sorted_fields = sorted(CONTACT_FIELDS_V3_6, key=lambda x: x.get("priority", 999))
    
    for field_def in sorted_fields:
        priority = field_def.get("priority")
        field_key = field_def.get("key")
        field_label = field_def.get("label")
        field_type = field_def.get("type")
        is_critical = field_def.get("critical", False)
        
        critical_marker = " ⭐ CRITICAL" if is_critical else ""
        print(f"\n[{priority}] Creating: {field_label}{critical_marker}")
        print(f"    Type: {field_type}")
        print(f"    Section: {field_def.get('section')}")
        
        # Build field configuration
        field_config = {
            "label": field_label,
            "type": field_type,
            "description": field_def.get("description", ""),
            "required": field_def.get("required", False)
        }
        
        # Add type-specific configuration
        if field_type == "text":
            field_config["size"] = field_def.get("size", "large")
        elif field_type == "phone":
            field_config["phone_type"] = field_def.get("phone_type", "mobile")
        elif field_type == "category":
            field_config["settings"] = field_def.get("settings", {})
        
        # Create the field
        result = create_podio_field(token, MASTER_LEAD_APP_ID, field_config)
        
        if result:
            field_id = result.get("field_id")
            field_id_mappings[field_key] = field_id
            success_count += 1
            print(f"    ✅ SUCCESS - Field ID: {field_id}")
        else:
            failure_count += 1
            print(f"    ❌ FAILED")
    
    # Step 3: Save field ID mappings
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {success_count} succeeded, {failure_count} failed")
    print("=" * 60)
    
    if success_count > 0:
        mappings_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'v3_6_field_ids.json'
        )
        
        print(f"\n💾 Saving field ID mappings to: {mappings_path}")
        
        output_data = {
            "created_at": datetime.utcnow().isoformat() + "Z",
            "contract_version": "v1.1.3",
            "app_id": MASTER_LEAD_APP_ID,
            "field_ids": field_id_mappings
        }
        
        with open(mappings_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print("✅ Field ID mappings saved")
        
        # Step 4: Validate fields
        expected_labels = [f["label"] for f in CONTACT_FIELDS_V3_6]
        validation_success = validate_fields(token, MASTER_LEAD_APP_ID, expected_labels)
        
        # Print final summary
        print("\n" + "=" * 60)
        print("FIELD ID MAPPINGS")
        print("=" * 60)
        for field_key, field_id in sorted(field_id_mappings.items()):
            print(f"  {field_key}: {field_id}")
        
        print("\n" + "=" * 60)
        if validation_success:
            print("✅ CONTRACT v1.1.3 COMPLETE - ALL FIELDS VALIDATED")
        else:
            print("⚠️ CONTRACT v1.1.3 COMPLETE - VALIDATION WARNINGS")
        print("=" * 60)
        
        print(f"\n📋 Critical Path Next Steps:")
        print(f"1. ✅ Fields created in Podio Master Lead App (30549135)")
        print(f"2. 📝 Update config.py with new field IDs")
        print(f"3. 🔧 Update podio_service.py for field access")
        print(f"4. 🎨 Update workspace.html UI components")
        print(f"5. 📤 Return field IDs to Data Team via GitHub PR comment")
        print(f"\n⏱️ Timeline: Field IDs due to Data Team within 12 hours")
        print(f"🎯 Business Impact: Unlocks 70% dialable lead coverage")
        
    else:
        print("\n❌ No fields were created successfully. Cannot proceed.")

if __name__ == "__main__":
    main()