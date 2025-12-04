"""
Contract v2.2 - Stacked Distress Signals Fields

This script:
1. Creates 3 Stacked Distress Signals fields in Podio Master Lead App (ID: 30549135)
2. Captures actual field IDs returned by Podio
3. Creates v4_phase2d_stacking_field_ids.json with field ID mappings
4. Validates fields after creation via Podio API

Fields Created:
- Active Distress Signals (text) - Combined signals e.g. "Tax Lien + Absentee Owner"
- Distress Signal Count (number) - Number of distress signals present
- Multi-Signal Lead (category) - Yes/No indicator for stacked leads

AUTHORIZATION: High-Level Advisor approved v2.2 with modification (3 fields, not 4)
SCOPE: Stacked Distress Signals Enhancement (3 fields)
BUSINESS IMPACT: Enables lead prioritization based on multiple distress indicators
NOTE: Field 53 (Stacking Bonus Points) was REMOVED by Advisor as redundant with existing lead_score
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
# CONTRACT v2.2 - STACKED DISTRESS SIGNALS FIELDS (3 fields)
# ============================================================================

V4_PHASE2D_STACKING_FIELDS = [
    # =========================================================================
    # Stacked Distress Signals Section (3 fields) - HIGH-LEVEL ADVISOR APPROVED
    # =========================================================================
    {
        "key": "active_distress_signals",
        "label": "Active Distress Signals",
        "type": "text",
        "size": "large",
        "section": "Stacked Distress Signals",
        "priority": 50,  # Field number per task spec
        "description": "Combined active distress signals. Example: 'Tax Lien + Absentee Owner'. Used for lead stacking prioritization.",
        "required": False
    },
    {
        "key": "distress_signal_count",
        "label": "Distress Signal Count",
        "type": "number",
        "decimals": 0,
        "section": "Stacked Distress Signals",
        "priority": 51,  # Field number per task spec
        "description": "Number of active distress signals. Higher counts indicate stronger lead priority.",
        "required": False
    },
    {
        "key": "multi_signal_lead",
        "label": "Multi-Signal Lead",
        "type": "category",
        "options": [
            {"text": "Yes", "color": "DCEDC8"},   # Light green
            {"text": "No", "color": "EEEEEE"}    # Light gray
        ],
        "multiple": False,
        "section": "Stacked Distress Signals",
        "priority": 52,  # Field number per task spec
        "description": "Indicates if this lead has multiple distress signals (2+ signals = Yes). Multi-signal leads are high priority.",
        "required": False
    }
]

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    
    print("\n" + "=" * 60)
    print("CONTRACT v2.2 - STACKED DISTRESS SIGNALS")
    print("CRM Team: 3 Stacked Distress Signals Fields")
    print("AUTHORIZATION: High-Level Advisor approved v2.2")
    print("NOTE: Field 53 (Stacking Bonus Points) REMOVED as redundant")
    print("=" * 60 + "\n")
    
    # Step 1: Get Podio token
    print(f"🔐 Authenticating with Podio...")
    token = refresh_podio_token()
    
    if not token:
        print("❌ CRITICAL: Cannot proceed without Podio token")
        return
    
    # Step 2: Create fields in priority order
    print(f"\n📋 Creating Stacked Distress Signals fields in Master Lead App (ID: {MASTER_LEAD_APP_ID})")
    print("=" * 60)
    
    field_id_mappings = {}
    success_count = 0
    failure_count = 0
    
    # Sort by priority
    sorted_fields = sorted(V4_PHASE2D_STACKING_FIELDS, key=lambda x: x.get("priority", 999))
    
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
        'v4_phase2d_stacking_field_ids.json'
    )
    
    print(f"\n💾 Saving field ID mappings to: {mappings_path}")
    
    output_data = {
        "created_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "contract_version": "2.2",
        "phase": "2d-STACKING",
        "authorization": "High-Level Advisor approved v2.2 with modification (3 fields, not 4)",
        "business_context": "Enables lead prioritization based on multiple distress indicators",
        "app_id": MASTER_LEAD_APP_ID,
        "success_count": success_count,
        "failure_count": failure_count,
        "fields": field_id_mappings,
        "example_data": {
            "active_distress_signals": "Tax Lien + Absentee Owner",
            "distress_signal_count": 2,
            "multi_signal_lead": "Yes"
        },
        "note": "Field 53 (Stacking Bonus Points) was REMOVED by Advisor as redundant with existing lead_score"
    }
    
    with open(mappings_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print("✅ Field ID mappings saved")
    
    # Step 4: Validate fields
    if success_count > 0:
        expected_labels = [f["label"] for f in V4_PHASE2D_STACKING_FIELDS]
        validation_success = validate_fields(token, MASTER_LEAD_APP_ID, expected_labels)
        
        # Print final summary
        print("\n" + "=" * 60)
        print("STACKED DISTRESS SIGNALS FIELD ID MAPPINGS")
        print("=" * 60)
        for field_key, field_id in sorted(field_id_mappings.items()):
            status = "✅" if field_id != "FAILED" else "❌"
            print(f"  {status} {field_key}: {field_id}")
        
        print("\n" + "=" * 60)
        if validation_success and failure_count == 0:
            print("✅ PHASE 2d STACKING COMPLETE - ALL 3 FIELDS VALIDATED")
        elif validation_success:
            print(f"⚠️ PHASE 2d STACKING PARTIAL - {success_count}/3 FIELDS CREATED")
        else:
            print("⚠️ PHASE 2d STACKING COMPLETE - VALIDATION WARNINGS")
        print("=" * 60)
        
        print(f"\n📋 Phase 2d Stacking Deliverables:")
        print(f"1. ✅ Script created: scripts/add_v4_phase2d_stacking_fields.py")
        print(f"2. {'✅' if success_count == 3 else '⚠️'} Fields created: {success_count}/3")
        print(f"3. ✅ Field IDs saved: scripts/archive/v4_phase2d_stacking_field_ids.json")
        print(f"4. {'✅' if validation_success else '⚠️'} Validation: {'PASSED' if validation_success else 'PARTIAL'}")
        
        print(f"\n🎯 Stacked Distress Signals Fields Created:")
        print(f"  • Active Distress Signals (text) - Combined signal names")
        print(f"  • Distress Signal Count (number) - Number of signals")
        print(f"  • Multi-Signal Lead (category) - Yes/No indicator")
        
        print(f"\n📊 Example Data Format:")
        print(f"  • Active Distress Signals: \"Tax Lien + Absentee Owner\"")
        print(f"  • Distress Signal Count: 2")
        print(f"  • Multi-Signal Lead: \"Yes\"")
        
        print(f"\n🏷️ Badge Rendering (UI):")
        print(f"  • 1 signal: Default (no badge)")
        print(f"  • 2 signals: 🟡 Yellow badge")
        print(f"  • 3+ signals: 🔥 Fire badge (high priority)")
        
        # Generate config.py update snippet
        print(f"\n" + "=" * 60)
        print("CONFIG.PY UPDATE SNIPPET")
        print("=" * 60)
        print("# V4.0 Phase 2d Fields - Stacked Distress Signals (Contract v2.2)")
        for key, field_id in field_id_mappings.items():
            const_name = key.upper() + "_FIELD_ID"
            print(f"{const_name} = {field_id}")
        
    else:
        print("\n❌ No fields were created successfully. Check API responses above.")

if __name__ == "__main__":
    main()