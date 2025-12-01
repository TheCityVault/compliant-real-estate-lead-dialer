"""
Phase 4.0.3 - Create 11 Enriched Fields in Podio Master Lead App

This script:
1. Reads the approved contract from podio-schema-v1.1.json
2. Creates all 11 enriched fields in Podio using the API
3. Captures actual field IDs returned by Podio
4. Creates enriched_field_ids_v4.json with TBD_XXX → real ID mappings
5. Updates the contract with real field IDs

CRITICAL: This enables Data Team to deploy podio-sync with finalized contract
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
# OAUTH TOKEN MANAGEMENT (Pattern from podio_service.py:46-104)
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
        if field_config["type"] == "number":
            payload["config"]["settings"] = {
                "decimals": field_config.get("decimals", 0)
            }
        elif field_config["type"] == "money":
            payload["config"]["settings"] = {
                "currency": field_config.get("currency", "USD")
            }
        elif field_config["type"] == "category":
            options = [{"text": opt} for opt in field_config.get("options", [])]
            payload["config"]["settings"] = {
                "options": options,
                "multiple": field_config.get("multiple", False)
            }
        
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

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    
    print("\n" + "=" * 60)
    print("PHASE 4.0.3 - CREATE ENRICHED FIELDS IN PODIO")
    print("=" * 60 + "\n")
    
    # Step 1: Read contract
    contract_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'docs', 'integration_contracts', 'podio-schema-v1.1.json'
    )
    
    print(f"📄 Reading contract: {contract_path}")
    
    try:
        with open(contract_path, 'r') as f:
            contract = json.load(f)
        print(f"✅ Contract loaded successfully")
    except Exception as e:
        print(f"❌ Failed to read contract: {e}")
        return
    
    # Step 2: Get Podio token
    print(f"\n🔐 Authenticating with Podio...")
    token = refresh_podio_token()
    
    if not token:
        print("❌ CRITICAL: Cannot proceed without Podio token")
        return
    
    # Step 3: Create fields in priority order
    print(f"\n📋 Creating fields in Master Lead App (ID: {MASTER_LEAD_APP_ID})")
    print("=" * 60)
    
    field_id_mappings = {}
    success_count = 0
    failure_count = 0
    
    enriched_fields = sorted(
        contract.get("enriched_fields", []),
        key=lambda x: x.get("field_priority", 999)
    )
    
    for field_def in enriched_fields:
        priority = field_def.get("field_priority")
        field_name = field_def.get("podio_field_name")
        tbd_id = field_def.get("podio_field_id")
        field_type = field_def.get("field_type")
        
        print(f"\n[{priority}] Creating: {field_name}")
        print(f"    Type: {field_type}, TBD ID: {tbd_id}")
        
        # Build field configuration
        field_config = {
            "label": field_name,
            "type": field_type,
            "description": field_def.get("business_rationale", ""),
            "required": field_def.get("null_handling") == "required"
        }
        
        # Add type-specific configuration
        if field_type == "number":
            field_config["decimals"] = 0
            if "equity" in field_name.lower() and "%" in field_name:
                field_config["decimals"] = 1
        
        elif field_type == "money":
            field_config["currency"] = "USD"
        
        elif field_type == "category":
            allowed_values = field_def.get("allowed_values", [])
            field_config["options"] = allowed_values
            field_config["multiple"] = False
        
        # Create the field
        result = create_podio_field(token, MASTER_LEAD_APP_ID, field_config)
        
        if result:
            field_id = result.get("field_id")
            field_id_mappings[tbd_id] = field_id
            success_count += 1
            print(f"    ✅ SUCCESS - Field ID: {field_id}")
        else:
            failure_count += 1
            print(f"    ❌ FAILED")
    
    # Step 4: Save field ID mappings
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {success_count} succeeded, {failure_count} failed")
    print("=" * 60)
    
    if success_count > 0:
        mappings_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'enriched_field_ids_v4.json'
        )
        
        print(f"\n💾 Saving field ID mappings to: {mappings_path}")
        
        with open(mappings_path, 'w') as f:
            json.dump(field_id_mappings, f, indent=2)
        
        print("✅ Field ID mappings saved")
        
        # Step 5: Update contract with real field IDs
        print(f"\n📝 Updating contract with real field IDs...")
        
        for field_def in contract.get("enriched_fields", []):
            tbd_id = field_def.get("podio_field_id")
            if tbd_id in field_id_mappings:
                real_id = field_id_mappings[tbd_id]
                field_def["podio_field_id"] = real_id
                print(f"  {tbd_id} → {real_id}")
        
        # Save updated contract
        with open(contract_path, 'w') as f:
            json.dump(contract, f, indent=2)
        
        print("✅ Contract updated with real field IDs")
        
        # Print final summary
        print("\n" + "=" * 60)
        print("FIELD ID MAPPINGS (TBD → Real)")
        print("=" * 60)
        for tbd_id, real_id in sorted(field_id_mappings.items()):
            print(f"  {tbd_id} → {real_id}")
        
        print("\n" + "=" * 60)
        print("✅ PHASE 4.0.3 COMPLETE")
        print("=" * 60)
        print(f"\nNext Steps:")
        print(f"1. Verify all fields in Podio Master Lead App")
        print(f"2. Share updated contract with Data Team")
        print(f"3. Data Team can deploy podio-sync with real field IDs")
        
    else:
        print("\n❌ No fields were created successfully. Cannot update contract.")

if __name__ == "__main__":
    main()