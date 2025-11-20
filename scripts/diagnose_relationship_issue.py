#!/usr/bin/env python3
"""
Diagnose why relationship field 274769798 rejects item 3204251617
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

PODIO_CLIENT_ID = os.getenv('PODIO_CLIENT_ID')
PODIO_CLIENT_SECRET = os.getenv('PODIO_CLIENT_SECRET')
PODIO_USERNAME = os.getenv('PODIO_USERNAME')
PODIO_PASSWORD = os.getenv('PODIO_PASSWORD')

CALL_ACTIVITY_APP_ID = 30549170
MASTER_LEAD_APP_ID = 30549135
RELATIONSHIP_FIELD_ID = 274769798
TEST_ITEM_ID = 3204251617

def get_podio_token():
    """Get Podio OAuth token"""
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
    response.raise_for_status()
    return response.json()['access_token']

def check_field_configuration(token):
    """Check relationship field configuration"""
    print("=" * 60)
    print("CHECKING RELATIONSHIP FIELD CONFIGURATION")
    print("=" * 60)
    
    # Get Call Activity app details
    response = requests.get(
        f'https://api.podio.com/app/{CALL_ACTIVITY_APP_ID}',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    app_data = response.json()
    
    # Find relationship field
    relationship_field = None
    for field in app_data['fields']:
        if field['field_id'] == RELATIONSHIP_FIELD_ID:
            relationship_field = field
            break
    
    if not relationship_field:
        print(f"❌ Field {RELATIONSHIP_FIELD_ID} NOT FOUND in Call Activity app!")
        return None
    
    print(f"✅ Found field: {relationship_field['label']}")
    print(f"   Field ID: {relationship_field['field_id']}")
    print(f"   Type: {relationship_field['type']}")
    print(f"   Status: {relationship_field['status']}")
    
    # Check app reference configuration
    if relationship_field['type'] == 'app':
        config = relationship_field.get('config', {})
        settings = config.get('settings', {})
        referenced_apps = settings.get('referenced_apps', [])
        
        print(f"\n   Referenced Apps Configuration:")
        for app in referenced_apps:
            print(f"   - App ID: {app.get('app_id')}")
            print(f"     App Name: {app.get('app_name')}")
        
        # Check if Master Lead app is referenced
        master_lead_referenced = any(
            app.get('app_id') == MASTER_LEAD_APP_ID 
            for app in referenced_apps
        )
        
        if master_lead_referenced:
            print(f"\n✅ Master Lead app ({MASTER_LEAD_APP_ID}) IS referenced")
        else:
            print(f"\n❌ Master Lead app ({MASTER_LEAD_APP_ID}) NOT referenced!")
            print(f"   This is the problem - field doesn't reference correct app")
    
    return relationship_field

def check_item_exists(token, item_id):
    """Check if item exists in Master Lead app"""
    print("\n" + "=" * 60)
    print(f"CHECKING IF ITEM {item_id} EXISTS")
    print("=" * 60)
    
    try:
        # Use filter approach
        response = requests.post(
            f'https://api.podio.com/item/app/{MASTER_LEAD_APP_ID}/filter',
            headers={'Authorization': f'Bearer {token}'},
            json={'filters': {'item_id': item_id}, 'limit': 1}
        )
        response.raise_for_status()
        
        data = response.json()
        items = data.get('items', [])
        
        if items:
            item = items[0]
            print(f"✅ Item {item_id} EXISTS in Master Lead app")
            print(f"   Item ID: {item['item_id']}")
            print(f"   Title: {item.get('title', 'N/A')}")
            print(f"   App ID: {item['app']['app_id']}")
            print(f"   App Name: {item['app']['config']['name']}")
            return True
        else:
            print(f"❌ Item {item_id} NOT FOUND in Master Lead app")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking item: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False

def test_relationship_creation(token):
    """Test creating a Call Activity with relationship"""
    print("\n" + "=" * 60)
    print("TESTING RELATIONSHIP CREATION")
    print("=" * 60)
    
    test_payload = {
        "fields": {
            str(RELATIONSHIP_FIELD_ID): [TEST_ITEM_ID]
        }
    }
    
    print(f"Test payload: {test_payload}")
    
    try:
        response = requests.post(
            f'https://api.podio.com/item/app/{CALL_ACTIVITY_APP_ID}/',
            headers={'Authorization': f'Bearer {token}'},
            json=test_payload
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ Successfully created Call Activity with relationship")
            return response.json()
        else:
            print("❌ Failed to create Call Activity")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating item: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None

def main():
    print("RELATIONSHIP FIELD DIAGNOSTIC TOOL")
    print("=" * 60)
    
    token = get_podio_token()
    print("✅ OAuth token obtained\n")
    
    # Check field configuration
    field_config = check_field_configuration(token)
    
    # Check if item exists
    item_exists = check_item_exists(token, TEST_ITEM_ID)
    
    # Test relationship creation
    if field_config and item_exists:
        result = test_relationship_creation(token)
        
        if result:
            print("\n" + "=" * 60)
            print("DIAGNOSIS: SUCCESSFUL")
            print("=" * 60)
            print("The field is configured correctly and can accept the relationship")
        else:
            print("\n" + "=" * 60)
            print("DIAGNOSIS: CONFIGURATION ERROR")
            print("=" * 60)
            print("Field configuration or item reference has an issue")
    else:
        print("\n" + "=" * 60)
        print("DIAGNOSIS: PREREQUISITE FAILURE")
        print("=" * 60)
        if not field_config:
            print("- Relationship field not properly configured")
        if not item_exists:
            print("- Test item does not exist in Master Lead app")

if __name__ == '__main__':
    main()