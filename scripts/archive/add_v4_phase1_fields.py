"""
Contract v2.0.0 Phase 1 - Create 12 New Podio Fields

This script:
1. Creates 12 new fields in Podio Master Lead App (ID: 30549135)
2. Supports NED Foreclosure, Foreclosure Auction, Compliance & Risk, and Contact Details sections
3. Captures actual field IDs returned by Podio
4. Creates v4_phase1_field_ids.json with field ID mappings
5. Validates fields after creation via Podio API

BUSINESS IMPACT: Enables V4.0 Contract v2.0 implementation
CRITICAL PATH: Phase 1 of CRM Team deliverables
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
# CONTRACT v2.0.0 PHASE 1 FIELD DEFINITIONS
# ============================================================================

V4_PHASE1_FIELDS = [
    # =========================================================================
    # NED Foreclosure Section (3 fields)
    # =========================================================================
    {
        "key": "auction_date",
        "label": "Auction Date",
        "type": "date",
        "section": "NED Foreclosure",
        "priority": 1,
        "description": "Critical for NED/Foreclosure urgency scoring. Determines timeline urgency for lead prioritization.",
        "required": False,
        "calendar": True,
        "time": "disabled"
    },
    {
        "key": "balance_due",
        "label": "Balance Due",
        "type": "money",
        "currencies": ["USD"],
        "section": "NED Foreclosure",
        "priority": 2,
        "description": "Primary debt amount for LTV calculation. Used in MAO formula and equity analysis.",
        "required": False
    },
    {
        "key": "opening_bid",
        "label": "Opening Bid",
        "type": "money",
        "currencies": ["USD"],
        "section": "NED Foreclosure",
        "priority": 3,
        "description": "Minimum floor price for MAO calculation. Starting bid amount from NED notice.",
        "required": False
    },
    
    # =========================================================================
    # Foreclosure Auction Section (5 fields)
    # =========================================================================
    {
        "key": "auction_platform",
        "label": "Auction Platform",
        "type": "category",
        "section": "Foreclosure Auction",
        "priority": 4,
        "description": "Platform where auction is conducted. Determines registration/bidding process.",
        "required": False,
        "settings": {
            "options": [
                {"text": "GovEase", "color": "DCEBD8"},
                {"text": "Zeus Auction", "color": "D5E8EE"},
                {"text": "RealAuction", "color": "FFEBBA"},
                {"text": "Bid4Assets", "color": "FFD5BA"},
                {"text": "Auction.com", "color": "E4DCEE"},
                {"text": "County Courthouse", "color": "FFDADA"},
                {"text": "Other", "color": "E8E8E8"}
            ],
            "multiple": False
        }
    },
    {
        "key": "auction_date_platform",
        "label": "Auction Date (Platform)",
        "type": "date",
        "section": "Foreclosure Auction",
        "priority": 5,
        "description": "Platform-specific auction date. May differ from NED notice date due to postponements.",
        "required": False,
        "calendar": True,
        "time": "disabled"
    },
    {
        "key": "opening_bid_platform",
        "label": "Opening Bid (Platform)",
        "type": "money",
        "currencies": ["USD"],
        "section": "Foreclosure Auction",
        "priority": 6,
        "description": "Platform-published opening bid. May differ from NED notice opening bid.",
        "required": False
    },
    {
        "key": "auction_location",
        "label": "Auction Location",
        "type": "text",
        "size": "large",
        "section": "Foreclosure Auction",
        "priority": 7,
        "description": "Online vs physical auction location. URL for online auctions, address for courthouse sales.",
        "required": False
    },
    {
        "key": "registration_deadline",
        "label": "Registration Deadline",
        "type": "date",
        "section": "Foreclosure Auction",
        "priority": 8,
        "description": "Bidder registration deadline. Critical for auction participation planning.",
        "required": False,
        "calendar": True,
        "time": "disabled"
    },
    
    # =========================================================================
    # Compliance & Risk Section (1 field)
    # =========================================================================
    {
        "key": "owner_occupied",
        "label": "Owner Occupied",
        "type": "category",
        "section": "Compliance & Risk",
        "priority": 9,
        "description": "CRITICAL: CFPA compliance gate. Determines outreach restrictions and script requirements.",
        "required": False,
        "critical": True,
        "settings": {
            "options": [
                {"text": "Yes", "color": "FFDADA"},      # Red - requires compliance review
                {"text": "No", "color": "DCEBD8"},       # Green - investor property
                {"text": "Unknown", "color": "FFEBBA"}   # Yellow - needs verification
            ],
            "multiple": False
        }
    },
    
    # =========================================================================
    # Contact Details Section (3 fields)
    # =========================================================================
    {
        "key": "owner_name_secondary",
        "label": "Owner Name (Secondary)",
        "type": "text",
        "size": "small",  # Podio only accepts 'small' or 'large'
        "section": "Contact Details",
        "priority": 10,
        "description": "Secondary/joint owner name. For properties with multiple owners or spouse information.",
        "required": False
    },
    {
        "key": "owner_phone_secondary",
        "label": "Owner Phone (Secondary)",
        "type": "phone",
        "phone_type": "mobile",
        "section": "Contact Details",
        "priority": 11,
        "description": "Secondary owner phone for dual-contact strategy. Increases contact rate.",
        "required": False
    },
    {
        "key": "owner_email_secondary",
        "label": "Owner Email (Secondary)",
        "type": "email",
        "section": "Contact Details",
        "priority": 12,
        "description": "Secondary owner email for multi-channel outreach.",
        "required": False
    }
]

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    
    print("\n" + "=" * 60)
    print("CONTRACT v2.0.0 PHASE 1 - CREATE 12 PODIO FIELDS")
    print("CRM Team Phase 1.1: NED, Auction, Compliance & Contact Fields")
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
    sorted_fields = sorted(V4_PHASE1_FIELDS, key=lambda x: x.get("priority", 999))
    
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
        'v4_phase1_field_ids.json'
    )
    
    print(f"\n💾 Saving field ID mappings to: {mappings_path}")
    
    output_data = {
        "created_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "contract_version": "2.0.0",
        "phase": "1",
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
        expected_labels = [f["label"] for f in V4_PHASE1_FIELDS]
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
            print("✅ CONTRACT v2.0.0 PHASE 1 COMPLETE - ALL 12 FIELDS VALIDATED")
        elif validation_success:
            print(f"⚠️ CONTRACT v2.0.0 PHASE 1 PARTIAL - {success_count}/12 FIELDS CREATED")
        else:
            print("⚠️ CONTRACT v2.0.0 PHASE 1 COMPLETE - VALIDATION WARNINGS")
        print("=" * 60)
        
        print(f"\n📋 Phase 1.1 Deliverables:")
        print(f"1. ✅ Script created: scripts/add_v4_phase1_fields.py")
        print(f"2. {'✅' if success_count == 12 else '⚠️'} Fields created: {success_count}/12")
        print(f"3. ✅ Field IDs saved: scripts/v4_phase1_field_ids.json")
        print(f"4. {'✅' if validation_success else '⚠️'} Validation: {'PASSED' if validation_success else 'PARTIAL'}")
        
        print(f"\n🎯 Field Sections Created:")
        print(f"  • NED Foreclosure: 3 fields (auction_date, balance_due, opening_bid)")
        print(f"  • Foreclosure Auction: 5 fields (platform, date, bid, location, deadline)")
        print(f"  • Compliance & Risk: 1 field (owner_occupied - CFPA gate)")
        print(f"  • Contact Details: 3 fields (secondary owner name, phone, email)")
        
    else:
        print("\n❌ No fields were created successfully. Check API responses above.")

if __name__ == "__main__":
    main()