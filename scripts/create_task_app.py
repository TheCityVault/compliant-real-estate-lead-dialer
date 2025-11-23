#!/usr/bin/env python3
"""
Script to create Task App in Podio with V3.3 schema
This app will be used for automated task creation based on call dispositions
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Podio credentials
PODIO_CLIENT_ID = os.environ.get('PODIO_CLIENT_ID')
PODIO_CLIENT_SECRET = os.environ.get('PODIO_CLIENT_SECRET')
PODIO_USERNAME = os.environ.get('PODIO_USERNAME')
PODIO_PASSWORD = os.environ.get('PODIO_PASSWORD')
MASTER_LEAD_APP_ID = '30549135'  # Master Lead app to get workspace info

def get_podio_token():
    """Get Podio OAuth access token"""
    print("Authenticating with Podio...")
    
    if not all([PODIO_CLIENT_ID, PODIO_CLIENT_SECRET, PODIO_USERNAME, PODIO_PASSWORD]):
        raise Exception("Podio credentials not fully configured. Please check environment variables.")
    
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
            access_token = token_data.get('access_token')
            print("✅ Podio authentication successful")
            return access_token
        else:
            raise Exception(f"Error getting Podio token: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Error initializing Podio authentication: {e}")

def get_workspace_id(access_token, app_id):
    """Get workspace/space ID from an existing app"""
    print(f"\nGetting workspace information from app {app_id}...")
    
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
            space_id = app_data.get('space_id')
            space_name = app_data.get('space', {}).get('name', 'Unknown')
            print(f"✅ Found workspace: '{space_name}' (ID: {space_id})")
            return space_id
        else:
            raise Exception(f"Error fetching app: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Error getting workspace ID: {e}")

def create_task_app(access_token, space_id):
    """Create the Task app in Podio"""
    print("\nCreating Task app in Podio...")
    
    app_config = {
        'space_id': space_id,
        'config': {
            'name': 'Tasks',
            'item_name': 'Task',
            'description': 'Automated follow-up tasks created from call dispositions',
            'icon': '331.png',  # Task/checklist icon
            'allow_edit': True,
            'allow_create': True,
            'allow_comments': True,
            'allow_attachments': False,
            'silent_creates': False,
            'silent_edits': False
        }
    }
    
    try:
        response = requests.post(
            'https://api.podio.com/app/',
            headers={
                'Authorization': f'OAuth2 {access_token}',
                'Content-Type': 'application/json'
            },
            json=app_config
        )
        
        if response.status_code == 200:
            app_data = response.json()
            app_id = app_data.get('app_id')
            print(f"✅ Task app created successfully (ID: {app_id})")
            return app_id
        else:
            raise Exception(f"Error creating app: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Error creating Task app: {e}")

def add_field(access_token, app_id, field_config):
    """Add a field to the Task app"""
    field_name = field_config.get('config', {}).get('label', 'Unknown')
    print(f"  Adding field: {field_name}...")
    
    try:
        response = requests.post(
            f'https://api.podio.com/app/{app_id}/field/',
            headers={
                'Authorization': f'OAuth2 {access_token}',
                'Content-Type': 'application/json'
            },
            json=field_config
        )
        
        if response.status_code == 200:
            field_data = response.json()
            field_id = field_data.get('field_id')
            print(f"  ✅ Field '{field_name}' added (ID: {field_id})")
            return {
                'success': True,
                'field_id': field_id,
                'field_name': field_name,
                'field_type': field_config.get('type')
            }
        else:
            error_msg = f"Error adding field '{field_name}': {response.status_code} - {response.text}"
            print(f"  ❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'field_name': field_name
            }
    except Exception as e:
        error_msg = f"Exception adding field '{field_name}': {e}"
        print(f"  ❌ {error_msg}")
        return {
            'success': False,
            'error': str(e),
            'field_name': field_name
        }

def create_task_fields(access_token, app_id):
    """Create all required fields for the Task app"""
    print("\nAdding fields to Task app...")
    
    # Define all required fields for V3.3 Task App
    fields_to_add = [
        {
            'type': 'text',
            'config': {
                'label': 'Title',
                'description': 'Task title/description',
                'required': True,
                'settings': {
                    'format': 'plain',
                    'size': 'large'
                }
            }
        },
        {
            'type': 'category',
            'config': {
                'label': 'Task Type',
                'description': 'Type of follow-up task',
                'required': True,
                'settings': {
                    'options': [
                        {'text': 'Follow-up Call', 'color': 'D5F3FF'},
                        {'text': 'Appointment', 'color': 'FFF6CC'},
                        {'text': 'Send Information', 'color': 'E4DFF8'},
                        {'text': 'Property Visit', 'color': 'DCEBD8'},
                        {'text': 'Other', 'color': 'E4E4E4'}
                    ],
                    'multiple': False,
                    'display': 'dropdown'
                }
            }
        },
        {
            'type': 'date',
            'config': {
                'label': 'Due Date',
                'description': 'When this task should be completed',
                'required': True,
                'settings': {
                    'calendar': True,
                    'end': 'disabled'
                }
            }
        },
        {
            'type': 'app',
            'config': {
                'label': 'Related Lead',
                'description': 'Master Lead this task is related to',
                'required': True,
                'settings': {
                    'referenced_apps': [
                        {'app_id': int(MASTER_LEAD_APP_ID)}
                    ],
                    'multiple': False
                }
            }
        },
        {
            'type': 'category',
            'config': {
                'label': 'Status',
                'description': 'Task completion status',
                'required': False,
                'settings': {
                    'options': [
                        {'text': 'Pending', 'color': 'FFF6CC'},
                        {'text': 'In Progress', 'color': 'D5F3FF'},
                        {'text': 'Completed', 'color': 'DCEBD8'},
                        {'text': 'Cancelled', 'color': 'E4E4E4'}
                    ],
                    'multiple': False,
                    'display': 'dropdown'
                }
            }
        }
    ]
    
    results = []
    for field_config in fields_to_add:
        result = add_field(access_token, app_id, field_config)
        results.append(result)
    
    return results

def generate_env_config(app_id, field_results):
    """Generate .env file configuration snippet"""
    print("\n" + "=" * 80)
    print("ENVIRONMENT VARIABLE CONFIGURATION")
    print("=" * 80)
    
    # Find field IDs by name
    field_map = {result['field_name']: result['field_id'] for result in field_results if result['success']}
    
    print("\nAdd these lines to your .env file:")
    print("\n# V3.3: Task App Configuration")
    print(f"PODIO_TASK_APP_ID={app_id}")
    print(f"TASK_TITLE_FIELD_ID={field_map.get('Title', 'NOT_FOUND')}")
    print(f"TASK_TYPE_FIELD_ID={field_map.get('Task Type', 'NOT_FOUND')}")
    print(f"TASK_DUE_DATE_FIELD_ID={field_map.get('Due Date', 'NOT_FOUND')}")
    print(f"TASK_MASTER_LEAD_RELATIONSHIP_FIELD_ID={field_map.get('Related Lead', 'NOT_FOUND')}")
    print(f"TASK_STATUS_FIELD_ID={field_map.get('Status', 'NOT_FOUND')}")
    
    return field_map

def main():
    """Main function to create Task app and fields"""
    print("=" * 80)
    print("Podio Task App Creation - V3.3 Automated Task Creation")
    print("=" * 80)
    
    # Get Podio access token
    try:
        access_token = get_podio_token()
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)
    
    # Get workspace ID from Master Lead app
    try:
        space_id = get_workspace_id(access_token, MASTER_LEAD_APP_ID)
    except Exception as e:
        print(f"❌ Failed to get workspace ID: {e}")
        sys.exit(1)
    
    # Create Task app
    try:
        task_app_id = create_task_app(access_token, space_id)
    except Exception as e:
        print(f"❌ Failed to create Task app: {e}")
        sys.exit(1)
    
    # Create all required fields
    try:
        field_results = create_task_fields(access_token, task_app_id)
    except Exception as e:
        print(f"❌ Failed to create fields: {e}")
        sys.exit(1)
    
    # Print summary
    print("\n" + "=" * 80)
    print("CREATION SUMMARY")
    print("=" * 80)
    
    successful = [r for r in field_results if r.get('success')]
    failed = [r for r in field_results if not r.get('success')]
    
    print(f"\n✅ Task App Created: ID {task_app_id}")
    print(f"✅ Fields Created: {len(successful)}/{len(field_results)}")
    
    if failed:
        print(f"❌ Failed Fields: {len(failed)}")
        for result in failed:
            print(f"  - {result['field_name']}: {result.get('error', 'Unknown error')}")
    
    # Generate env configuration
    field_map = generate_env_config(task_app_id, field_results)
    
    # Save results to JSON file
    output = {
        'app_id': task_app_id,
        'app_name': 'Tasks',
        'workspace_id': space_id,
        'fields': field_results,
        'field_map': field_map,
        'timestamp': '2025-11-23'
    }
    
    output_file = 'scripts/task_app_creation_results.json'
    try:
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
    except Exception as e:
        print(f"\n⚠️  Warning: Could not save results to file: {e}")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("""
1. ✅ Update your .env file with the environment variables shown above
2. 🔄 Restart your Flask application to load the new configuration
3. 🧪 Test task creation by making a call with a disposition that triggers tasks
4. 📝 Verify tasks are created and linked to the correct Master Lead items
5. ✨ V3.3 Task Automation is now ready to use!
""")
    
    print("=" * 80)
    
    if failed:
        print("\n⚠️  Warning: Some fields failed to create. Please review errors above.")
        sys.exit(1)
    else:
        print("\n✅ Task app created successfully with all fields!")
        sys.exit(0)

if __name__ == '__main__':
    main()