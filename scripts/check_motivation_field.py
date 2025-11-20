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

app_data = p.Application.find(call_activity_app_id)

print("="*80)
print("CHECKING CRITICAL DROPDOWN FIELDS IN CALL ACTIVITY APP")
print("="*80)

for field in app_data.get('fields', []):
    field_id = field.get('field_id')
    
    # Check Seller Motivation Level (274851085)
    if field_id == 274851085:
        print("\n" + "="*80)
        print("SELLER MOTIVATION LEVEL FIELD (274851085)")
        print("="*80)
        print(json.dumps(field, indent=2))
        
        # Check the allowed options
        config = field.get('config', {})
        settings = config.get('settings', {})
        options = settings.get('options', [])
        
        print("\n" + "="*80)
        print("VALID OPTIONS FOR SELLER MOTIVATION LEVEL:")
        print("="*80)
        for opt in options:
            print(f"ID: {opt.get('id')} | Text: {opt.get('text')} | Status: {opt.get('status')}")
    
    # Check Disposition Code (274851083)
    if field_id == 274851083:
        print("\n" + "="*80)
        print("DISPOSITION CODE FIELD (274851083)")
        print("="*80)
        print(json.dumps(field, indent=2))
        
        # Check the allowed options
        config = field.get('config', {})
        settings = config.get('settings', {})
        options = settings.get('options', [])
        
        print("\n" + "="*80)
        print("VALID OPTIONS FOR DISPOSITION CODE:")
        print("="*80)
        for opt in options:
            print(f"ID: {opt.get('id')} | Text: {opt.get('text')} | Status: {opt.get('status')}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)