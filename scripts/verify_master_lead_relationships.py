#!/usr/bin/env python3
"""
Script to verify Master Lead App relationship configuration
Task: Ensure bi-directional relationship between Master Lead and Call Activity apps
Critical for V2.0: Call Activities must link back to Lead Items

Master Lead App ID: 30549135
Call Activity App ID: 30549170
Call Activity Relationship Field ID: 274769798
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
PODIO_WORKSPACE_ID = os.environ.get('PODIO_WORKSPACE_ID')

# Known Call Activity relationship field ID
CALL_ACTIVITY_RELATIONSHIP_FIELD_ID = 274769798

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

def get_app_details(access_token, app_id, app_name):
    """Get complete app structure including all fields"""
    print(f"Querying {app_name} (App ID: {app_id})...")
    
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
            print(f"✅ Retrieved {app_name} structure\n")
            return app_data
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Failed to get app details: {e}")

def analyze_relationship_fields(app_data, target_app_id):
    """Analyze all fields to find relationship/app reference fields"""
    print("=" * 70)
    print("RELATIONSHIP FIELD ANALYSIS")
    print("=" * 70)
    
    app_name = app_data.get('config', {}).get('name', 'Unknown')
    fields = app_data.get('fields', [])
    
    relationship_fields = []
    app_reference_fields = []
    other_fields = []
    
    for field in fields:
        field_id = field.get('field_id')
        field_label = field.get('label')
        field_type = field.get('type')
        field_config = field.get('config', {})
        
        if field_type == 'app':
            # This is an app reference/relationship field
            referenced_apps = field_config.get('referenced_apps', [])
            settings = field_config.get('settings', {})
            
            app_reference_fields.append({
                'field_id': field_id,
                'label': field_label,
                'type': field_type,
                'referenced_apps': referenced_apps,
                'settings': settings,
                'multiple': settings.get('multiple', False),
                'required': settings.get('required', False)
            })
            
            # Check if this references our target app
            for ref_app in referenced_apps:
                if ref_app.get('app_id') == int(target_app_id):
                    relationship_fields.append({
                        'field_id': field_id,
                        'label': field_label,
                        'referenced_app_id': ref_app.get('app_id'),
                        'referenced_app_name': ref_app.get('app_name'),
                        'multiple': settings.get('multiple', False),
                        'required': settings.get('required', False)
                    })
        else:
            other_fields.append({
                'field_id': field_id,
                'label': field_label,
                'type': field_type
            })
    
    # Report findings
    print(f"\nApp: {app_name} (ID: {app_data.get('app_id')})")
    print(f"Total Fields: {len(fields)}")
    print(f"App Reference Fields: {len(app_reference_fields)}")
    print(f"Relationship Fields to Target App ({target_app_id}): {len(relationship_fields)}\n")
    
    if relationship_fields:
        print("🎯 FOUND RELATIONSHIP FIELDS TO CALL ACTIVITY APP:")
        print("-" * 70)
        for rf in relationship_fields:
            print(f"\n✅ Field ID: {rf['field_id']}")
            print(f"   Label: {rf['label']}")
            print(f"   References: {rf['referenced_app_name']} (App ID: {rf['referenced_app_id']})")
            print(f"   Multiple Values: {'Yes' if rf['multiple'] else 'No'}")
            print(f"   Required: {'Yes' if rf['required'] else 'No'}")
    else:
        print("❌ NO RELATIONSHIP FIELDS FOUND TO CALL ACTIVITY APP")
        print(f"   Master Lead app does not have a field referencing App ID {target_app_id}")
    
    if app_reference_fields and not relationship_fields:
        print("\n📋 Other App Reference Fields Found:")
        print("-" * 70)
        for arf in app_reference_fields:
            print(f"\n   Field ID: {arf['field_id']}")
            print(f"   Label: {arf['label']}")
            print(f"   References {len(arf['referenced_apps'])} app(s):")
            for ref_app in arf['referenced_apps']:
                print(f"      - {ref_app.get('app_name')} (App ID: {ref_app.get('app_id')})")
    
    return {
        'relationship_fields': relationship_fields,
        'app_reference_fields': app_reference_fields,
        'total_fields': len(fields),
        'other_fields': other_fields
    }

def verify_call_activity_relationship(access_token):
    """Verify the Call Activity app's relationship field configuration"""
    print("\n" + "=" * 70)
    print("CALL ACTIVITY APP - RELATIONSHIP FIELD VERIFICATION")
    print("=" * 70)
    
    try:
        call_activity_data = get_app_details(
            access_token, 
            PODIO_CALL_ACTIVITY_APP_ID, 
            "Call Activity App"
        )
        
        fields = call_activity_data.get('fields', [])
        relationship_field = None
        
        for field in fields:
            if field.get('field_id') == CALL_ACTIVITY_RELATIONSHIP_FIELD_ID:
                relationship_field = field
                break
        
        if relationship_field:
            field_config = relationship_field.get('config', {})
            referenced_apps = field_config.get('referenced_apps', [])
            settings = field_config.get('settings', {})
            
            print(f"\n✅ RELATIONSHIP FIELD FOUND:")
            print(f"   Field ID: {CALL_ACTIVITY_RELATIONSHIP_FIELD_ID}")
            print(f"   Label: {relationship_field.get('label')}")
            print(f"   Type: {relationship_field.get('type')}")
            print(f"   Multiple Values: {'Yes' if settings.get('multiple', False) else 'No'}")
            print(f"   Required: {'Yes' if settings.get('required', False) else 'No'}")
            
            if referenced_apps:
                print(f"\n   Referenced Apps:")
                for ref_app in referenced_apps:
                    app_id = ref_app.get('app_id')
                    app_name = ref_app.get('app_name')
                    is_master_lead = app_id == int(PODIO_MASTER_LEAD_APP_ID)
                    status = "✅ MASTER LEAD APP" if is_master_lead else "⚠️  OTHER APP"
                    print(f"      {status}: {app_name} (App ID: {app_id})")
                
                # Check if Master Lead is referenced
                master_lead_referenced = any(
                    ref_app.get('app_id') == int(PODIO_MASTER_LEAD_APP_ID) 
                    for ref_app in referenced_apps
                )
                
                return {
                    'field_exists': True,
                    'field_id': CALL_ACTIVITY_RELATIONSHIP_FIELD_ID,
                    'label': relationship_field.get('label'),
                    'references_master_lead': master_lead_referenced,
                    'referenced_apps': referenced_apps
                }
            else:
                print("   ⚠️  No referenced apps configured")
                return {
                    'field_exists': True,
                    'field_id': CALL_ACTIVITY_RELATIONSHIP_FIELD_ID,
                    'references_master_lead': False,
                    'referenced_apps': []
                }
        else:
            print(f"\n❌ RELATIONSHIP FIELD NOT FOUND")
            print(f"   Expected Field ID: {CALL_ACTIVITY_RELATIONSHIP_FIELD_ID}")
            return {
                'field_exists': False,
                'field_id': None,
                'references_master_lead': False,
                'referenced_apps': []
            }
            
    except Exception as e:
        print(f"\n❌ Error verifying Call Activity relationship: {e}")
        return {
            'field_exists': False,
            'error': str(e)
        }

def test_relationship_configuration(master_lead_analysis, call_activity_verification):
    """Determine if bi-directional relationship is properly configured"""
    print("\n" + "=" * 70)
    print("BI-DIRECTIONAL RELATIONSHIP CONFIGURATION TEST")
    print("=" * 70)
    
    # Check Call Activity → Master Lead
    call_activity_ok = (
        call_activity_verification.get('field_exists') and
        call_activity_verification.get('references_master_lead')
    )
    
    # Check Master Lead → Call Activity
    master_lead_ok = len(master_lead_analysis['relationship_fields']) > 0
    
    print(f"\n1. Call Activity → Master Lead:")
    if call_activity_ok:
        print(f"   ✅ CONFIGURED")
        print(f"      Field ID: {call_activity_verification.get('field_id')}")
        print(f"      Label: {call_activity_verification.get('label')}")
    else:
        print(f"   ❌ NOT CONFIGURED or MISSING")
    
    print(f"\n2. Master Lead → Call Activity:")
    if master_lead_ok:
        print(f"   ✅ CONFIGURED")
        for rf in master_lead_analysis['relationship_fields']:
            print(f"      Field ID: {rf['field_id']}")
            print(f"      Label: {rf['label']}")
            print(f"      Allows Multiple: {'Yes' if rf['multiple'] else 'No'}")
    else:
        print(f"   ❌ NOT CONFIGURED or MISSING")
    
    # Overall status
    print(f"\n" + "=" * 70)
    print("CONFIGURATION STATUS")
    print("=" * 70)
    
    if call_activity_ok and master_lead_ok:
        print("\n🎉 BI-DIRECTIONAL RELATIONSHIP FULLY CONFIGURED!")
        print("   ✅ Call Activities can link to Leads")
        print("   ✅ Leads can view associated Call Activities")
        print("\n   Ready for V2.0 backend implementation")
        return True, "FULLY_CONFIGURED"
    elif call_activity_ok and not master_lead_ok:
        print("\n⚠️  PARTIAL CONFIGURATION - ONE-WAY ONLY")
        print("   ✅ Call Activities can link to Leads")
        print("   ❌ Master Lead app lacks reverse relationship field")
        print("\n   RECOMMENDATION: Add app reference field in Master Lead app")
        return False, "PARTIAL_CALL_TO_LEAD_ONLY"
    elif not call_activity_ok and master_lead_ok:
        print("\n⚠️  PARTIAL CONFIGURATION - ONE-WAY ONLY")
        print("   ❌ Call Activity relationship field not properly configured")
        print("   ✅ Master Lead has reference field")
        print("\n   RECOMMENDATION: Fix Call Activity relationship field")
        return False, "PARTIAL_LEAD_TO_CALL_ONLY"
    else:
        print("\n❌ NO BI-DIRECTIONAL RELATIONSHIP CONFIGURED")
        print("   Both apps lack proper relationship configuration")
        print("\n   CRITICAL: Must configure before V2.0 implementation")
        return False, "NOT_CONFIGURED"

def generate_documentation(master_lead_data, master_lead_analysis, 
                          call_activity_verification, relationship_status, config_type):
    """Generate comprehensive documentation"""
    doc_content = f"""# Podio Relationship Configuration

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Task:** Verify Master Lead ↔ Call Activity Relationship Configuration

---

## Executive Summary

**Configuration Status:** `{config_type}`

### Apps Analyzed
- **Master Lead App:** {master_lead_data.get('config', {}).get('name')} (ID: {PODIO_MASTER_LEAD_APP_ID})
- **Call Activity App:** App ID {PODIO_CALL_ACTIVITY_APP_ID}
- **Workspace ID:** {PODIO_WORKSPACE_ID}

### Relationship Status
{"✅ **FULLY CONFIGURED** - Ready for V2.0 backend implementation" if relationship_status else "❌ **NOT FULLY CONFIGURED** - Requires attention before backend work"}

---

## 1. Master Lead App Analysis

### App Details
- **App ID:** {PODIO_MASTER_LEAD_APP_ID}
- **App Name:** {master_lead_data.get('config', {}).get('name')}
- **Total Fields:** {master_lead_analysis['total_fields']}
- **App Reference Fields:** {len(master_lead_analysis['app_reference_fields'])}

### Relationship Fields to Call Activity App
"""
    
    if master_lead_analysis['relationship_fields']:
        doc_content += f"\n**Found {len(master_lead_analysis['relationship_fields'])} relationship field(s):**\n\n"
        for rf in master_lead_analysis['relationship_fields']:
            doc_content += f"""
#### Field: {rf['label']}
- **Field ID:** `{rf['field_id']}`
- **References:** {rf['referenced_app_name']} (App ID: {rf['referenced_app_id']})
- **Allow Multiple Values:** {'Yes' if rf['multiple'] else 'No'}
- **Required:** {'Yes' if rf['required'] else 'No'}
- **Type:** One-to-{"Many" if rf['multiple'] else "One"}
"""
    else:
        doc_content += "\n**❌ NO relationship fields found that reference Call Activity App**\n"
    
    if master_lead_analysis['app_reference_fields'] and not master_lead_analysis['relationship_fields']:
        doc_content += f"\n### Other App Reference Fields\n\n"
        for arf in master_lead_analysis['app_reference_fields']:
            doc_content += f"""
#### Field: {arf['label']} (ID: {arf['field_id']})
- **Type:** {arf['type']}
- **Referenced Apps:** {len(arf['referenced_apps'])}
"""
            for ref_app in arf['referenced_apps']:
                doc_content += f"  - {ref_app.get('app_name')} (App ID: {ref_app.get('app_id')})\n"
    
    doc_content += f"""

---

## 2. Call Activity App Relationship Field

### Field Configuration
"""
    
    if call_activity_verification.get('field_exists'):
        doc_content += f"""
- **Field ID:** `{call_activity_verification.get('field_id')}`
- **Label:** {call_activity_verification.get('label')}
- **References Master Lead:** {'✅ Yes' if call_activity_verification.get('references_master_lead') else '❌ No'}
"""
        if call_activity_verification.get('referenced_apps'):
            doc_content += "\n**Referenced Apps:**\n"
            for ref_app in call_activity_verification['referenced_apps']:
                doc_content += f"- {ref_app.get('app_name')} (App ID: {ref_app.get('app_id')})\n"
    else:
        doc_content += "\n**❌ Relationship field not found or not properly configured**\n"
    
    doc_content += f"""

---

## 3. Bi-Directional Relationship Test

### Call Activity → Master Lead
"""
    
    call_activity_ok = (
        call_activity_verification.get('field_exists') and
        call_activity_verification.get('references_master_lead')
    )
    
    if call_activity_ok:
        doc_content += f"""
✅ **CONFIGURED**
- Field ID: `{call_activity_verification.get('field_id')}`
- Call Activities can link to Master Lead items
"""
    else:
        doc_content += "❌ **NOT CONFIGURED**\n"
    
    doc_content += "\n### Master Lead → Call Activity\n"
    
    if master_lead_analysis['relationship_fields']:
        doc_content += "✅ **CONFIGURED**\n"
        for rf in master_lead_analysis['relationship_fields']:
            doc_content += f"- Field ID: `{rf['field_id']}`\n"
            doc_content += f"- Lead items can view associated Call Activities\n"
    else:
        doc_content += "❌ **NOT CONFIGURED**\n"
    
    doc_content += f"""

---

## 4. Recommendations

"""
    
    if relationship_status:
        doc_content += """
### ✅ Configuration is Complete

The bi-directional relationship between Master Lead and Call Activity apps is properly configured. You can proceed with:

1. **Backend Implementation**
   - Create API endpoints to link Call Activities to Leads
   - Implement relationship field updates during call logging
   
2. **Frontend Integration**
   - Display Call Activity history on Lead detail pages
   - Show linked Lead information in Call Activity items

3. **Testing**
   - Test creating Call Activities linked to Leads
   - Verify relationship appears in both apps
   - Validate data integrity
"""
    else:
        doc_content += f"""
### ⚠️ Configuration Requires Attention

**Status:** `{config_type}`

"""
        if config_type == "PARTIAL_CALL_TO_LEAD_ONLY":
            doc_content += """
#### Action Required: Add Relationship Field in Master Lead App

1. **Manual Configuration via Podio UI:**
   - Navigate to Master Lead app settings
   - Add new field: Type = "App Reference"
   - Configure to reference Call Activity app (ID: """ + PODIO_CALL_ACTIVITY_APP_ID + """)
   - Allow multiple values (one-to-many relationship)
   - Label suggestion: "Call History" or "Call Activities"

2. **Programmatic Configuration (Alternative):**
   - Use Podio API: `POST /app/{app_id}/field/`
   - Create app reference field programmatically
   - See Podio API documentation for field creation
"""
        elif config_type == "PARTIAL_LEAD_TO_CALL_ONLY":
            doc_content += """
#### Action Required: Fix Call Activity Relationship Field

1. **Verify Field Configuration:**
   - Check field ID """ + str(CALL_ACTIVITY_RELATIONSHIP_FIELD_ID) + """ exists
   - Ensure it references Master Lead app (ID: """ + PODIO_MASTER_LEAD_APP_ID + """)
   
2. **If Missing, Recreate Field:**
   - Add app reference field in Call Activity app
   - Reference Master Lead app
   - Label: "Relationship" or "Lead"
"""
        else:
            doc_content += """
#### Action Required: Configure Both Relationship Fields

**CRITICAL:** Neither app has proper relationship configuration.

1. **Call Activity App:**
   - Add/verify relationship field (ID: """ + str(CALL_ACTIVITY_RELATIONSHIP_FIELD_ID) + """)
   - Must reference Master Lead app

2. **Master Lead App:**
   - Add app reference field
   - Reference Call Activity app
   - Allow multiple values

**DO NOT proceed with V2.0 backend until this is resolved.**
"""
    
    doc_content += """

---

## 5. Technical Details

### Field IDs for Backend Implementation

```python
# Master Lead App
MASTER_LEAD_APP_ID = """ + PODIO_MASTER_LEAD_APP_ID + """
"""
    
    if master_lead_analysis['relationship_fields']:
        for rf in master_lead_analysis['relationship_fields']:
            doc_content += f"MASTER_LEAD_CALL_HISTORY_FIELD_ID = {rf['field_id']}  # {rf['label']}\n"
    
    doc_content += f"""
# Call Activity App
CALL_ACTIVITY_APP_ID = {PODIO_CALL_ACTIVITY_APP_ID}
CALL_ACTIVITY_RELATIONSHIP_FIELD_ID = {CALL_ACTIVITY_RELATIONSHIP_FIELD_ID}  # Links to Lead
```

### API Usage Example

```python
# When creating a Call Activity item, link it to a Lead:
podio_client.Item.create(
    app_id=CALL_ACTIVITY_APP_ID,
    fields={{
        CALL_ACTIVITY_RELATIONSHIP_FIELD_ID: [lead_item_id],
        # ... other fields
    }}
)
```

---

## Appendix: Complete Field Inventory

### Master Lead App Fields ({master_lead_analysis['total_fields']} total)

"""
    
    for field in master_lead_analysis['other_fields'][:10]:  # Limit to prevent huge doc
        doc_content += f"- {field['label']} (ID: {field['field_id']}) - Type: {field['type']}\n"
    
    if len(master_lead_analysis['other_fields']) > 10:
        doc_content += f"\n_(Showing first 10 of {len(master_lead_analysis['other_fields'])} fields)_\n"
    
    doc_content += "\n---\n\n**End of Report**\n"
    
    return doc_content

def main():
    """Main verification function"""
    print("=" * 70)
    print("MASTER LEAD APP - RELATIONSHIP CONFIGURATION VERIFICATION")
    print("=" * 70)
    print(f"\nMaster Lead App ID: {PODIO_MASTER_LEAD_APP_ID}")
    print(f"Call Activity App ID: {PODIO_CALL_ACTIVITY_APP_ID}")
    print(f"Call Activity Relationship Field ID: {CALL_ACTIVITY_RELATIONSHIP_FIELD_ID}")
    print(f"\nObjective: Verify bi-directional relationship for V2.0")
    print("=" * 70 + "\n")
    
    if not all([PODIO_MASTER_LEAD_APP_ID, PODIO_CALL_ACTIVITY_APP_ID]):
        print("❌ Error: App IDs not properly configured in .env")
        sys.exit(1)
    
    try:
        # 1. Authenticate
        access_token = get_podio_token()
        
        # 2. Get Master Lead app structure
        master_lead_data = get_app_details(
            access_token, 
            PODIO_MASTER_LEAD_APP_ID, 
            "Master Lead App"
        )
        
        # 3. Analyze relationship fields in Master Lead app
        master_lead_analysis = analyze_relationship_fields(
            master_lead_data,
            PODIO_CALL_ACTIVITY_APP_ID
        )
        
        # 4. Verify Call Activity relationship field
        call_activity_verification = verify_call_activity_relationship(access_token)
        
        # 5. Test bi-directional configuration
        relationship_status, config_type = test_relationship_configuration(
            master_lead_analysis,
            call_activity_verification
        )
        
        # 6. Generate documentation
        doc_content = generate_documentation(
            master_lead_data,
            master_lead_analysis,
            call_activity_verification,
            relationship_status,
            config_type
        )
        
        # Save documentation
        doc_file = 'docs/podio_relationship_configuration.md'
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        print(f"\n💾 Documentation saved to: {doc_file}")
        
        # Save JSON results
        results_file = 'scripts/relationship_verification.json'
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'master_lead_app_id': PODIO_MASTER_LEAD_APP_ID,
                'call_activity_app_id': PODIO_CALL_ACTIVITY_APP_ID,
                'relationship_status': relationship_status,
                'configuration_type': config_type,
                'master_lead_analysis': {
                    'total_fields': master_lead_analysis['total_fields'],
                    'relationship_fields': master_lead_analysis['relationship_fields'],
                    'app_reference_count': len(master_lead_analysis['app_reference_fields'])
                },
                'call_activity_verification': call_activity_verification
            }, f, indent=2)
        print(f"💾 JSON results saved to: {results_file}")
        
        print("\n" + "=" * 70)
        print("VERIFICATION COMPLETE")
        print("=" * 70)
        
        if relationship_status:
            print("\n✅ Ready to proceed with V2.0 backend implementation")
        else:
            print(f"\n⚠️  Configuration incomplete ({config_type})")
            print("   Review documentation for required actions")
        
        # Exit with appropriate code
        sys.exit(0 if relationship_status else 1)
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()