from pypodio2 import api
import os
import json
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv('PODIO_CLIENT_ID')
client_secret = os.getenv('PODIO_CLIENT_SECRET')
username = os.getenv('PODIO_USERNAME')
password = os.getenv('PODIO_PASSWORD')
call_activity_app_id = os.getenv('PODIO_CALL_ACTIVITY_APP_ID')

p = api.OAuthClient(client_id, client_secret, username, password)

# Get app schema
app_data = p.Application.find(call_activity_app_id)

print("="*60)
print(f"CALL ACTIVITY APP SCHEMA")
print("="*60)

for field in app_data.get('fields', []):
    if field.get('field_id') == 274769798:
        print(f"\nRELATIONSHIP FIELD FOUND:")
        print(json.dumps(field, indent=2))
        
        print(f"\nField ID: {field.get('field_id')}")
        print(f"Label: {field.get('label')}")
        print(f"Type: {field.get('type')}")
        print(f"Config: {field.get('config', {})}")
        
        # Check which apps it references
        settings = field.get('config', {}).get('settings', {})
        referenced_apps = settings.get('referenced_apps', [])
        print(f"\nReferenced Apps: {referenced_apps}")
        
        for ref_app in referenced_apps:
            print(f"  - App ID: {ref_app.get('app_id')}")
            print(f"    App Name: {ref_app.get('name')}")