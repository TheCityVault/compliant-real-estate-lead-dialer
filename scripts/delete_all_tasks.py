"""
Delete All Task Items from Podio

Purpose: Clean slate approach - clear all task items before syncing production leads.
Part of the 3-app cleanup sequence:
  1. Master Lead App (30549135) - 44 items ✅
  2. Call Activity App (30549170) - 27 items ✅
  3. Tasks App (30559290) - this script

This script:
1. Authenticates with Podio using environment credentials
2. Fetches all items from Tasks App (30559290) with pagination
3. Deletes each item with progress logging
4. Includes safety confirmation prompt before mass delete

Usage:
    python scripts/delete_all_tasks.py
"""

import os
import sys
import time
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Task App ID (from scripts/archive/task_app_creation_results.json)
TASK_APP_ID = 30559290


def get_podio_token():
    """Get Podio OAuth access token using password grant"""
    print("Authenticating with Podio...")
    
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
        token = response.json().get('access_token')
        print("✓ Authentication successful")
        return token
    else:
        raise Exception(f"Failed to get token: {response.status_code} - {response.text}")


def get_all_items(token, app_id):
    """
    Fetch all items from app using pagination.
    Podio filter endpoint returns max 500 items per request.
    """
    all_items = []
    offset = 0
    limit = 500  # Max per request
    
    print(f"\nFetching items from Tasks app (ID: {app_id})...")
    
    while True:
        response = requests.post(
            f'https://api.podio.com/item/app/{app_id}/filter',
            headers={
                'Authorization': f'OAuth2 {token}',
                'Content-Type': 'application/json'
            },
            json={
                'limit': limit,
                'offset': offset
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch items: {response.status_code} - {response.text}")
        
        data = response.json()
        items = data.get('items', [])
        total = data.get('total', 0)
        
        all_items.extend(items)
        
        # Progress update
        print(f"  Fetched {len(all_items)}/{total} items...")
        
        # Check if we've fetched all items
        if len(all_items) >= total or len(items) == 0:
            break
            
        offset += limit
        time.sleep(0.5)  # Rate limiting
    
    return all_items


def delete_item(token, item_id):
    """Delete a single Podio item"""
    response = requests.delete(
        f'https://api.podio.com/item/{item_id}',
        headers={
            'Authorization': f'OAuth2 {token}'
        }
    )
    
    return response.status_code in [200, 204]


def main():
    print("=" * 60)
    print("PODIO TASKS APP - MASS DELETION TOOL")
    print("=" * 60)
    print(f"\nTarget App ID: {TASK_APP_ID}")
    print("Authorization: User request (clean slate before production sync)")
    print("Sequence: Step 3 of 3 (Master Lead ✅, Call Activity ✅, Tasks)")
    print()
    
    # Validate environment
    required_vars = ['PODIO_CLIENT_ID', 'PODIO_CLIENT_SECRET', 'PODIO_USERNAME', 'PODIO_PASSWORD']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    try:
        # Get authentication token
        token = get_podio_token()
        
        # Fetch all items
        items = get_all_items(token, TASK_APP_ID)
        total_items = len(items)
        
        if total_items == 0:
            print("\n✓ No items found in Tasks App. Nothing to delete.")
            return
        
        print(f"\n{'=' * 60}")
        print(f"Found {total_items} items in Tasks App")
        print(f"{'=' * 60}")
        
        # Safety confirmation prompt
        print("\n⚠️  WARNING: This action is IRREVERSIBLE!")
        print("    All task records will be permanently deleted.")
        print()
        
        confirmation = input("Confirm deletion? (yes/no): ").strip().lower()
        
        if confirmation != 'yes':
            print("\n❌ Deletion cancelled by user.")
            sys.exit(0)
        
        print("\n" + "=" * 60)
        print("Starting deletion...")
        print("=" * 60 + "\n")
        
        # Delete each item with progress
        deleted_count = 0
        error_count = 0
        errors = []
        
        for i, item in enumerate(items, 1):
            item_id = item['item_id']
            title = item.get('title', 'Untitled')[:40]  # Truncate long titles
            
            print(f"Deleting item {i}/{total_items} (ID: {item_id} | {title})...", end=" ")
            
            try:
                if delete_item(token, item_id):
                    print("✓")
                    deleted_count += 1
                else:
                    print("✗ Failed")
                    error_count += 1
                    errors.append(item_id)
            except Exception as e:
                print(f"✗ Error: {e}")
                error_count += 1
                errors.append(item_id)
            
            # Rate limiting - Podio has request limits
            if i % 10 == 0:
                time.sleep(1)  # 1 second pause every 10 deletions
            else:
                time.sleep(0.2)  # 200ms between individual deletions
        
        # Summary
        print("\n" + "=" * 60)
        print("DELETION COMPLETE!")
        print("=" * 60)
        print(f"  Total items found: {total_items}")
        print(f"  Successfully deleted: {deleted_count}")
        print(f"  Errors: {error_count}")
        
        if errors:
            print(f"\n  Failed item IDs: {errors[:10]}{'...' if len(errors) > 10 else ''}")
        
        print(f"\n✓ Complete! Deleted {deleted_count} items from Tasks App ({TASK_APP_ID})")
        print("\n🎉 ALL 3 APPS CLEANED - Ready for production sync!")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()