"""
Contract v2.0.0 Phase 2 - Create 10 New Podio Fields

This script:
1. Creates 10 new fields in Podio Master Lead App (ID: 30549135)
2. Supports Probate/Estate and Tax Lien sections
3. Captures actual field IDs returned by Podio
4. Creates v4_phase2_field_ids.json with field ID mappings
5. Validates fields after creation via Podio API

BUSINESS IMPACT: Enables V4.1 Probate/Tax Lien lead intelligence
PHASE DEPENDENCY: Requires High-Level Advisor approval + Data Team scraper readiness
EXECUTION DATE: Monday 2025-12-02 (post-bilateral sync)
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
        elif field_config["type"] == "date":
            # Date fields in Podio
            payload["config"]["settings"] = {
                "calendar": field_config.get("calendar", True),
                "time": field_config.get("time", "disabled")  # disabled, enabled, required
            }
        elif field_config["type"] == "money":
            # Money fields in Podio
            payload["config"]["settings"] = {
                "allowed_currencies": field_config.get("currencies", ["USD"])
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
# CONTRACT v2.0.0 PHASE 2 FIELD DEFINITIONS
# ============================================================================

V4_PHASE2_FIELDS = [
    # =========================================================================
    # Probate/Estate Section (6 fields)
    # =========================================================================
    {
        "key": "executor_name",
        "label": "Executor Name",
        "type": "text",
        "size": "large",
        "section": "Probate/Estate",
        "priority": 1,
        "description": "Personal Representative (Executor/Administrator) identification. The fiduciary party with authority to sell estate property.",
        "required": False
    },
    {
        "key": "probate_case_number",
        "label": "Probate Case Number",
        "type": "text",
        "size": "small",
        "section": "Probate/Estate",
        "priority": 2,
        "description": "Court case identifier for deduplication and legal reference. Format varies by jurisdiction.",
        "required": False
    },
    {
        "key": "probate_filing_date",
        "label": "Probate Filing Date",
        "type": "date",
        "section": "Probate/Estate",
        "priority": 3,
        "description": "Date probate was filed with court. Determines timeline urgency (6-18 month probate window).",
        "required": False,
        "calendar": True,
        "time": "disabled"
    },
    {
        "key": "estate_value",
        "label": "Estate Value",
        "type": "money",
        "currencies": ["USD"],
        "section": "Probate/Estate",
        "priority": 4,
        "description": "Total estate value from court filings. Used for deal qualification and priority scoring.",
        "required": False
    },
    {
        "key": "decedent_name",
        "label": "Decedent Name",
        "type": "text",
        "size": "large",
        "section": "Probate/Estate",
        "priority": 5,
        "description": "Original property owner (deceased). Required for title research and ownership verification.",
        "required": False
    },
    {
        "key": "court_jurisdiction",
        "label": "Court Jurisdiction",
        "type": "text",
        "size": "small",
        "section": "Probate/Estate",
        "priority": 6,
        "description": "County/district court handling probate. Enables multi-county probate lookup and scraper routing.",
        "required": False
    },
    
    # =========================================================================
    # Tax Lien Section (4 fields)
    # =========================================================================
    {
        "key": "tax_debt_amount",
        "label": "Tax Debt Amount",
        "type": "money",
        "currencies": ["USD"],
        "section": "Tax Lien",
        "priority": 7,
        "description": "Outstanding tax debt. Combined with mortgage creates dual financial pressure signal.",
        "required": False
    },
    {
        "key": "delinquency_start_date",
        "label": "Delinquency Start Date",
        "type": "date",
        "section": "Tax Lien",
        "priority": 8,
        "description": "When tax delinquency began. >2 years indicates likely abandonment or severe financial distress.",
        "required": False,
        "calendar": True,
        "time": "disabled"
    },
    {
        "key": "redemption_deadline",
        "label": "Redemption Deadline",
        "type": "date",
        "section": "Tax Lien",
        "priority": 9,
        "description": "Hard legal deadline for property redemption. Creates maximum urgency scoring when <30 days.",
        "required": False,
        "calendar": True,
        "time": "disabled",
        "critical": True  # Triggers Redemption Deadline Gate when <30 days
    },
    {
        "key": "lien_type",
        "label": "Lien Type",
        "type": "category",
        "section": "Tax Lien",
        "priority": 10,
        "description": "Type of tax lien. Different lien types have different priority and redemption rules.",
        "required": False,
        "settings": {
            "options": [
                {"text": "Property Tax", "color": "FFDADA"},       # Red - most common
                {"text": "IRS Federal", "color": "FFD5BA"},        # Orange - federal lien
                {"text": "State Tax", "color": "FFEBBA"},          # Yellow - state lien
                {"text": "HOA/Assessment", "color": "D5E8EE"},     # Blue - association lien
                {"text": "Municipal/Utility", "color": "E4DCEE"},  # Purple - utility/municipal
                {"text": "Multiple", "color": "E8E8E8"}            # Gray - multiple liens
            ],
            "multiple": False
        }
    }
]

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    
    print("\n" + "=" * 60)
    print("CONTRACT v2.0.0 PHASE 2 - CREATE 10 PODIO FIELDS")
    print("CRM Team Phase 2: Probate/Estate + Tax Lien Fields")
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
    sorted_fields = sorted(V4_PHASE2_FIELDS, key=lambda x: x.get("priority", 999))
    
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
        elif field_type == "date":
            field_config["calendar"] = field_def.get("calendar", True)
            field_config["time"] = field_def.get("time", "disabled")
        elif field_type == "money":
            field_config["currencies"] = field_def.get("currencies", ["USD"])
        
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
    
    # Step 3: Save field ID mappings
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {success_count} succeeded, {failure_count} failed")
    print("=" * 60)
    
    mappings_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'v4_phase2_field_ids.json'
    )
    
    print(f"\n💾 Saving field ID mappings to: {mappings_path}")
    
    output_data = {
        "created_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "contract_version": "2.0.0",
        "phase": "2",
        "app_id": MASTER_LEAD_APP_ID,
        "success_count": success_count,
        "failure_count": failure_count,
        "fields": field_id_mappings
    }
    
    with open(mappings_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print("✅ Field ID mappings saved")
    
    # Step 4: Validate fields
    if success_count > 0:
        expected_labels = [f["label"] for f in V4_PHASE2_FIELDS]
        validation_success = validate_fields(token, MASTER_LEAD_APP_ID, expected_labels)
        
        # Print final summary
        print("\n" + "=" * 60)
        print("FIELD ID MAPPINGS")
        print("=" * 60)
        for field_key, field_id in sorted(field_id_mappings.items()):
            status = "✅" if field_id != "FAILED" else "❌"
            print(f"  {status} {field_key}: {field_id}")
        
        print("\n" + "=" * 60)
        if validation_success and failure_count == 0:
            print("✅ CONTRACT v2.0.0 PHASE 2 COMPLETE - ALL 10 FIELDS VALIDATED")
        elif validation_success:
            print(f"⚠️ CONTRACT v2.0.0 PHASE 2 PARTIAL - {success_count}/10 FIELDS CREATED")
        else:
            print("⚠️ CONTRACT v2.0.0 PHASE 2 COMPLETE - VALIDATION WARNINGS")
        print("=" * 60)
        
        print(f"\n📋 Phase 2 Deliverables:")
        print(f"1. ✅ Script created: scripts/add_v4_phase2_fields.py")
        print(f"2. {'✅' if success_count == 10 else '⚠️'} Fields created: {success_count}/10")
        print(f"3. ✅ Field IDs saved: scripts/v4_phase2_field_ids.json")
        print(f"4. {'✅' if validation_success else '⚠️'} Validation: {'PASSED' if validation_success else 'PARTIAL'}")
        
        print(f"\n🎯 Field Sections Created:")
        print(f"  • Probate/Estate: 6 fields (executor, case#, filing_date, estate_value, decedent, jurisdiction)")
        print(f"  • Tax Lien: 4 fields (tax_debt, delinquency_date, redemption_deadline, lien_type)")
        
    else:
        print("\n❌ No fields were created successfully. Check API responses above.")

if __name__ == "__main__":
    main()