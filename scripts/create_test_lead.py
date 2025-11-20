from pypodio2 import api
import os
from dotenv import load_dotenv

load_dotenv()

# Podio credentials
client_id = os.getenv('PODIO_CLIENT_ID')
client_secret = os.getenv('PODIO_CLIENT_SECRET')
username = os.getenv('PODIO_USERNAME')
password = os.getenv('PODIO_PASSWORD')
master_lead_app_id = int(os.getenv('PODIO_MASTER_LEAD_APP_ID'))  # Convert to int for API

# Initialize Podio client
p = api.OAuthClient(client_id, client_secret, username, password)

# Field IDs for Master Lead app (from earlier investigation)
# Owner Name field ID: (need to find)
# Best Contact Number field ID: (need to find)
# Full Address field ID: (need to find)

print("="*60)
print("CREATING NEW TEST MASTER LEAD ITEM")
print("="*60)

# Create new Master Lead item with test data
new_item_data = {
    'fields': {
        # We need to find the correct field IDs first
        # For now, create with minimal required fields
    }
}

try:
    # Get app schema to find field IDs
    app_data = p.Application.find(master_lead_app_id)
    
    print("\nMaster Lead App Fields:")
    field_map = {}
    for field in app_data.get('fields', []):
        field_id = field.get('field_id')
        label = field.get('label')
        field_type = field.get('type')
        print(f"  - {label} (ID: {field_id}, Type: {field_type})")
        field_map[label] = field_id
    
    # Build payload with test data
    payload = {'fields': {}}
    
    # Owner Name
    if 'Owner Name' in field_map:
        payload['fields'][str(field_map['Owner Name'])] = "V2.0 Test Lead"
    
    # Best Contact Number
    if 'Best Contact Number' in field_map:
        payload['fields'][str(field_map['Best Contact Number'])] = [{
            'type': 'mobile',
            'value': '5555551234'  # Test phone number
        }]
    
    # Full Address
    if 'Full Address' in field_map:
        payload['fields'][str(field_map['Full Address'])] = "123 Test Street, Test City, TS 12345"
    
    # Parcel ID (if exists)
    if 'Parcel ID' in field_map:
        payload['fields'][str(field_map['Parcel ID'])] = "TEST-V2-001"
    
    print("\nPayload to create:")
    import json
    print(json.dumps(payload, indent=2))
    
    # Create the item
    print("\nCreating new Master Lead item...")
    response = p.Item.create(master_lead_app_id, payload)
    
    new_item_id = response.get('item_id')
    
    print("="*60)
    print(f"✅ SUCCESS! New Master Lead Item Created")
    print(f"Item ID: {new_item_id}")
    print(f"Title/Name: V2.0 Test Lead")
    print(f"Phone: 5555551234")
    print(f"Parcel ID: TEST-V2-001")
    print("="*60)
    
    print("\n🧪 TEST URL:")
    print(f"https://compliant-real-estate-lead-git-e6910a-leadgenalchemys-projects.vercel.app/workspace?item_id={new_item_id}")
    print("\nUse this URL to test V2.0 disposition submission!")
    
except Exception as e:
    print(f"ERROR creating test item: {e}")
    import traceback
    traceback.print_exc()