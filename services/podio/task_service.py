"""
Podio Task Service - Automated Task Creation

Handles creation of follow-up tasks based on call disposition outcomes.
Supports V3.3 disposition-based task automation.

Business Justification:
    Pillar 4 (Disposition Funnel): Task creation isolated enables future enhancements 
        like multi-task workflows, task templates, and escalation rules
    Pillar 5 (Scalability): Completes the podio_service.py refactoring - 
        original 832 lines → 5 focused domain services
"""
from datetime import datetime, timedelta
import requests

from services.podio.oauth import refresh_podio_token
from config import (
    TASK_APP_ID,
    TASK_TITLE_FIELD_ID,
    TASK_TYPE_FIELD_ID,
    TASK_DUE_DATE_FIELD_ID,
    TASK_MASTER_LEAD_RELATIONSHIP_FIELD_ID,
)


def create_follow_up_task(master_lead_item_id, task_properties, agent_specified_date=None):
    """
    Create a follow-up task in Podio linked to Master Lead
    
    Args:
        master_lead_item_id: Master Lead item ID to link task to
        task_properties: Dict containing task configuration
            - task_type: Type of task
            - due_date_offset_days: Days from now for due date
            - task_title: Title of the task
        agent_specified_date: (optional) Agent-specified date in YYYY-MM-DD format
            
    Returns:
        tuple: (success: bool, result: dict or error message)
    """
    token = refresh_podio_token()
    if not token:
        print("❌ V3.3: Podio token refresh failed for task creation")
        return False, 'Podio authentication failed'
    
    # V3.3 Enhancement: Prioritize agent-specified date over default offset
    if agent_specified_date:
        # Agent specified a date - use it (it's already in YYYY-MM-DD format from the HTML date input)
        try:
            # Convert YYYY-MM-DD to ISO datetime format for Podio
            due_date = datetime.strptime(agent_specified_date, '%Y-%m-%d')
            due_date_iso = due_date.strftime("%Y-%m-%d %H:%M:%S")
            print(f"V3.3: Using agent-specified due date: {agent_specified_date}")
        except ValueError:
            # Fallback to default if date parsing fails
            print(f"V3.3: Invalid agent date format, using default offset")
            due_date_offset = task_properties.get('due_date_offset_days', 1)
            due_date = datetime.now() + timedelta(days=due_date_offset)
            due_date_iso = due_date.strftime("%Y-%m-%d %H:%M:%S")
            agent_specified_date = None  # Mark as not used due to parse error
    else:
        # No agent date - use default offset from config
        due_date_offset = task_properties.get('due_date_offset_days', 1)
        due_date = datetime.now() + timedelta(days=due_date_offset)
        due_date_iso = due_date.strftime("%Y-%m-%d %H:%M:%S")
        print(f"V3.3: Using default offset: {due_date_offset} days")
    
    # Prepare task fields
    task_fields = {
        str(TASK_TITLE_FIELD_ID): task_properties.get('task_title', 'Follow-up Task'),
        str(TASK_TYPE_FIELD_ID): task_properties.get('task_type', 'Follow-up Call'),
        str(TASK_DUE_DATE_FIELD_ID): due_date_iso,
        str(TASK_MASTER_LEAD_RELATIONSHIP_FIELD_ID): [int(master_lead_item_id)]  # Link to Master Lead
    }
    
    print(f"=== V3.3: CREATE FOLLOW-UP TASK ===")
    print(f"Master Lead ID: {master_lead_item_id}")
    print(f"Task Title: {task_properties.get('task_title')}")
    print(f"Task Type: {task_properties.get('task_type')}")
    print(f"Due Date: {due_date_iso} ({'agent-specified' if agent_specified_date else f'offset: {due_date_offset} days'})")
    print(f"======================================")
    
    try:
        # Create Task item in Podio
        response = requests.post(
            f'https://api.podio.com/item/app/{TASK_APP_ID}/',
            headers={
                'Authorization': f'OAuth2 {token}',
                'Content-Type': 'application/json'
            },
            json={'fields': task_fields}
        )
        
        if response.status_code in [200, 201]:
            task_data = response.json()
            task_item_id = task_data.get('item_id')
            print(f"✅ V3.3: Task created successfully - Item ID: {task_item_id}")
            return True, task_data
        else:
            print(f"❌ V3.3: Task creation failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            try:
                error_data = response.json()
                return False, error_data.get('error_description', 'Task creation failed')
            except:
                return False, f'Task creation failed: {response.text}'
                
    except Exception as e:
        print(f"❌ V3.3: Exception creating task: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)