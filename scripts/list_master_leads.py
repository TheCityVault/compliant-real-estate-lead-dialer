"""
Quick script to list available Master Lead items for testing
"""
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

def get_podio_token():
    """Get Podio OAuth access token"""
    response = requests.post(
        'https://podio.com/oauth/token',
        data={
            'grant_type': 'password',
            'client_id': os.getenv('PODIO_CLIENT_ID'),
            'client_secret': os.getenv('PODIO_CLIENT_SECRET'),
            'username': os.getenv('PODIO_USERNAME'),
            'password': os.getenv('PODIO_PASSWORD')
        }
    )
    
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f"Failed to get token: {response.status_code} - {response.text}")

def main():
    print("Authenticating with Podio...")
    token = get_podio_token()
    print("✓ Authentication successful\n")
    
    # Master Lead app ID
    app_id = 30549169
    
    print(f"Fetching items from Master Lead app (ID: {app_id})...")
    
    # Get items from the app using Podio API
    response = requests.post(
        f'https://api.podio.com/item/app/{app_id}/filter',
        headers={
            'Authorization': f'OAuth2 {token}',
            'Content-Type': 'application/json'
        },
        json={'limit': 10}
    )
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        
        print(f"\n✓ Found {len(items)} Master Lead items:\n")
        
        for item in items:
            item_id = item['item_id']
            title = item.get('title', 'No title')
            print(f"  - Item ID: {item_id} | Title: {title}")
        
        if items:
            print(f"\n✓ Recommended test item_id: {items[0]['item_id']}")
        else:
            print("\n⚠ Warning: No items found in Master Lead app")
    else:
        print(f"Error fetching items: {response.status_code} - {response.text}")

if __name__ == '__main__':
    main()