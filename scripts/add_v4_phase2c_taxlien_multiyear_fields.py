"""
Contract v2.1 - Tax Lien Multi-Year Enhancement Fields

This script:
1. Creates 2 Tax Lien Multi-Year fields in Podio Master Lead App (ID: 30549135)
2. Captures actual field IDs returned by Podio
3. Creates v4_phase2c_taxlien_multiyear_field_ids.json with field ID mappings
4. Validates fields after creation via Podio API

Fields Created:
- Tax Delinquency Summary (text) - Multi-year summary e.g. "$12,740 total (2023: $6,501, 2024: $6,239)"
- Delinquent Years Count (number) - Number of years with delinquent taxes

AUTHORIZATION: Data Team PR #6 approved
SCOPE: Tax Lien Multi-Year Enhancement (2 fields)
BUSINESS IMPACT: Supports Douglas County Tax Lien API multi-year data integration
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
        elif field_config["type"] == "number":
            # Number fields in Podio
            payload["config"]["settings"] = {
                "decimals": field_config.get("decimals", 0)
            }
        elif field_config["type"] == "date":
            # Date fields in Podio
            payload["config"]["settings"] = {
                "calendar": field_config.get("calendar", True),
                "time": field_config.get("time", "disabled")
            }
        elif field_config["type"] == "money":
            # Money fields in Podio
            payload["config"]["settings"] = {
                "allowed_currencies": field_config.get("currencies", ["USD"])
            }
        elif field_config["type"] == "category":
            # Category fields in Podio
            payload["config"]["settings"] = {
                "options": field_config.get("options", []),
                "multiple": field_config.get("multiple", False)
            }
        
        # Log the payload for debugging
        print(f"  📤 API Payload: {json.dumps(payload, indent=2)}")
        
        # Make API request
        response = requests.post(
            f'https://api.podio.com/app/{app_id}/field',
            headers={
                'Authorization': f'OAuth2 {token}',
                'Content-Type': 'application/json'
            },
            json=payload
        )
        
        # Log full response for debugging
        print(f"  📥 API Response Status: {response.status_code}")
        print(f"  📥 API Response: {response.text[:500] if response.text else 'No response body'}")
        
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
# CONTRACT v2.1 - TAX LIEN MULTI-YEAR ENHANCEMENT FIELDS (2 fields)
# ============================================================================

V4_PHASE2C_TAXLIEN_MULTIYEAR_FIELDS = [
    # =========================================================================
    # Tax Lien Multi-Year Section (2 fields) - DATA TEAM PR #6 APPROVED
    # =========================================================================
    {
        "key": "tax_delinquency_summary",
        "label": "Tax Delinquency Summary",
        "type": "text",
        "size": "large",
        "section": "Tax Lien Fields",
        "priority": 48,  # Field number per task spec
        "description": "Multi-year tax delinquency summary. Example: '$12,740 total (2023: $6,501, 2024: $6,239)'. Supports Douglas County Tax Lien API multi-year data.",
        "required": False
    },
    {
        "key": "delinquent_years_count",
        "label": "Delinquent Years Count",
        "type": "number",
        "decimals": 0,
        "section": "Tax Lien Fields",
        "priority": 49,  # Field number per task spec
        "description": "Number of years with delinquent taxes. Used for lead prioritization and urgency assessment.",
        "required": False
    }
]

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    
    print("\n" + "=" * 60)
    print("CONTRACT v2.1 - TAX LIEN MULTI-YEAR ENHANCEMENT")
    print("CRM Team: 2 Tax Lien Multi-Year Fields")
    print("AUTHORIZATION: Data Team PR #6 approved")
    print("=" * 60 + "\n")
    
    # Step 1: Get Podio token
    print(f"🔐 Authenticating with Podio...")
    token = refresh_podio_token()
    
    if not token:
        print("❌ CRITICAL: Cannot proceed without Podio token")
        return
    
    # Step 2: Create fields in priority order
    print(f"\n📋 Creating Tax Lien Multi-Year fields in Master Lead App (ID: {MASTER_LEAD_APP_ID})")
    print("=" * 60)
    
    field_id_mappings = {}
    success_count = 0
    failure_count = 0
    
    # Sort by priority
    sorted_fields = sorted(V4_PHASE2C_TAXLIEN_MULTIYEAR_FIELDS, key=lambda x: x.get("priority", 999))
    
    for field_def in sorted_fields:
        priority = field_def.get("priority")
        field_key = field_def.get("key")
        field_label = field_def.get("label")
        field_type = field_def.get("type")
        
        print(f"\n[{priority}] Creating: {field_label}")
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
        elif field_type == "number":
            field_config["decimals"] = field_def.get("decimals", 0)
        elif field_type == "date":
            field_config["calendar"] = field_def.get("calendar", True)
            field_config["time"] = field_def.get("time", "disabled")
        elif field_type == "money":
            field_config["currencies"] = field_def.get("currencies", ["USD"])
        elif field_type == "category":
            field_config["options"] = field_def.get("options", [])
            field_config["multiple"] = field_def.get("multiple", False)
        
        # Create the field
        result = create_podio_field(token, MASTER_LEAD_APP_ID, field_config)
        
        if result:
            field_id = result.get("field_id")
            field_id_mappings[field_key] = field_id
            success_count += 1
            print(f"    ✅ SUCCESS - Field ID: {field_id}")
        else:
            failure_count += 1
            field_id_mappings[field_key] = "FAILED"
            print(f"    ❌ FAILED")
    
    # Step 3: Save field ID mappings to archive directory
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {success_count} succeeded, {failure_count} failed")
    print("=" * 60)
    
    # Save to archive directory
    archive_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'archive'
    )
    
    # Create archive directory if it doesn't exist
    os.makedirs(archive_dir, exist_ok=True)
    
    mappings_path = os.path.join(
        archive_dir,
        'v4_phase2c_taxlien_multiyear_field_ids.json'
    )
    
    print(f"\n💾 Saving field ID mappings to: {mappings_path}")
    
    output_data = {
        "created_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "contract_version": "2.1",
        "phase": "2c-TAXLIEN-MULTIYEAR",
        "authorization": "Data Team PR #6 approved",
        "business_context": "Douglas County Tax Lien API multi-year data support",
        "app_id": MASTER_LEAD_APP_ID,
        "success_count": success_count,
        "failure_count": failure_count,
        "fields": field_id_mappings,
        "example_data": {
            "tax_delinquency_summary": "$12,740 total (2023: $6,501, 2024: $6,239)",
            "delinquent_years_count": 2
        }
    }
    
    with open(mappings_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print("✅ Field ID mappings saved")
    
    # Step 4: Validate fields
    if success_count > 0:
        expected_labels = [f["label"] for f in V4_PHASE2C_TAXLIEN_MULTIYEAR_FIELDS]
        validation_success = validate_fields(token, MASTER_LEAD_APP_ID, expected_labels)
        
        # Print final summary
        print("\n" + "=" * 60)
        print("TAX LIEN MULTI-YEAR FIELD ID MAPPINGS")
        print("=" * 60)
        for field_key, field_id in sorted(field_id_mappings.items()):
            status = "✅" if field_id != "FAILED" else "❌"
            print(f"  {status} {field_key}: {field_id}")
        
        print("\n" + "=" * 60)
        if validation_success and failure_count == 0:
            print("✅ PHASE 2c TAX LIEN MULTI-YEAR COMPLETE - ALL 2 FIELDS VALIDATED")
        elif validation_success:
            print(f"⚠️ PHASE 2c TAX LIEN MULTI-YEAR PARTIAL - {success_count}/2 FIELDS CREATED")
        else:
            print("⚠️ PHASE 2c TAX LIEN MULTI-YEAR COMPLETE - VALIDATION WARNINGS")
        print("=" * 60)
        
        print(f"\n📋 Phase 2c Tax Lien Multi-Year Deliverables:")
        print(f"1. ✅ Script created: scripts/add_v4_phase2c_taxlien_multiyear_fields.py")
        print(f"2. {'✅' if success_count == 2 else '⚠️'} Fields created: {success_count}/2")
        print(f"3. ✅ Field IDs saved: scripts/archive/v4_phase2c_taxlien_multiyear_field_ids.json")
        print(f"4. {'✅' if validation_success else '⚠️'} Validation: {'PASSED' if validation_success else 'PARTIAL'}")
        
        print(f"\n🎯 Tax Lien Multi-Year Fields Created:")
        print(f"  • Tax Delinquency Summary (text) - Multi-year breakdown")
        print(f"  • Delinquent Years Count (number) - Years of delinquency")
        
        print(f"\n📊 Example Data Format:")
        print(f"  • Summary: \"$12,740 total (2023: $6,501, 2024: $6,239)\"")
        print(f"  • Years Count: 2")
        
        # Generate config.py update snippet
        print(f"\n" + "=" * 60)
        print("CONFIG.PY UPDATE SNIPPET")
        print("=" * 60)
        print("# V4.0 Phase 2c Fields - Tax Lien Multi-Year (Contract v2.1)")
        for key, field_id in field_id_mappings.items():
            const_name = key.upper() + "_FIELD_ID"
            print(f"{const_name} = {field_id}")
        
    else:
        print("\n❌ No fields were created successfully. Check API responses above.")

if __name__ == "__main__":
    main()