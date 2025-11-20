from pypodio2 import api
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Podio credentials
client_id = os.getenv('PODIO_CLIENT_ID')
client_secret = os.getenv('PODIO_CLIENT_SECRET')
username = os.getenv('PODIO_USERNAME')
password = os.getenv('PODIO_PASSWORD')
app_id = os.getenv('PODIO_MASTER_LEAD_APP_ID')

# Initialize Podio client
p = api.OAuthClient(client_id, client_secret, username, password)

# Fetch item using app filter  
response = p.Item.filter(app_id, {
    'filters': {'item_id': 3204110525},
    'limit': 1
})

items = response.get('items', [])
if items:
    item = items[0]
    
    print("="*60)
    print(f"COMPLETE ITEM STRUCTURE FOR ID: {item['item_id']}")
    print("="*60)
    print(json.dumps(item, indent=2))
    print("="*60)
    
    print("\n" + "="*60)
    print("FIELD-BY-FIELD ANALYSIS")
    print("="*60)
    
    for field in item.get('fields', []):
        field_id = field.get('field_id')
        label = field.get('label')
        values = field.get('values', [])
        
        print(f"\nField ID: {field_id}")
        print(f"Label: {label}")
        print(f"Type: {field.get('type')}")
        print(f"Values: {values}")
        
        # Check for any reference to 1112233
        if '1112233' in str(values):
            print(f"⚠️ FOUND 1112233 in this field!")
            
        # Check for app references
        if field.get('type') == 'app':
            print(f"  → App Reference Field")
            for val in values:
                if isinstance(val, dict):
                    print(f"     Referenced item_id: {val.get('item_id')}")
                    print(f"     Referenced value: {val.get('value')}")
else:
    print(f"ERROR: Item 3204110525 not found")