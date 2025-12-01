"""
Podio Service Module - Task Management

This module handles:
- Task creation (V3.3)

Extracted modules:
- OAuth token management: services/podio/oauth.py
- Item CRUD operations: services/podio/item_service.py
- Field value extraction: services/podio/field_extraction.py
- Lead intelligence extraction: services/podio/intelligence.py

For improved modularity and security auditing.
"""
import requests
from datetime import datetime, timedelta
from config import (
    TASK_APP_ID,
    TASK_TITLE_FIELD_ID,
    TASK_TYPE_FIELD_ID,
    TASK_DUE_DATE_FIELD_ID,
    TASK_MASTER_LEAD_RELATIONSHIP_FIELD_ID,
)

# Import OAuth token management from extracted module
# Backward compatibility: refresh_podio_token is re-exported for existing imports
from services.podio.oauth import refresh_podio_token, _podio_token

# Import Item Service from extracted module (V4.0.8)
# Backward compatibility: These functions are re-exported for existing imports
from services.podio.item_service import (
    get_podio_item,
    create_call_activity_item,
    update_call_activity_recording,
    generate_title,
    convert_to_iso_date,
    parse_currency,
)

# Import Field Extraction from extracted module (V4.0.8)
# Backward compatibility: These functions are re-exported for existing imports
from services.podio.field_extraction import (
    extract_field_value,
    extract_field_value_by_id,
)

# Import Intelligence from extracted module (V4.0.8)
# Backward compatibility: These functions are re-exported for existing imports
from services.podio.intelligence import (
    FIELD_BUNDLES,
    get_lead_intelligence,
)

# ============================================================================
# EXTRACTED MODULE NOTES
# ============================================================================
# NOTE: OAuth token management has been extracted to services/podio/oauth.py
# The refresh_podio_token function is imported above for backward compatibility.
# See services/podio/oauth.py for implementation details.

# NOTE: Item CRUD operations have been extracted to services/podio/item_service.py
# The following functions are imported above for backward compatibility:
#   - get_podio_item(item_id) - Fetch a Podio item
#   - create_call_activity_item(...) - Create Call Activity in Podio
#   - update_call_activity_recording(...) - Update recording URL
#   - generate_title(data, item_id) - Generate Call Activity title
#   - convert_to_iso_date(date_string) - Date format conversion
# See services/podio/item_service.py for implementation details.

# NOTE: Field extraction utilities have been extracted to services/podio/field_extraction.py
# The following functions are imported above for backward compatibility:
#   - extract_field_value(item, field_label) - Extract by field label
#   - extract_field_value_by_id(item, field_id, field_type) - Extract by field ID
# See services/podio/field_extraction.py for implementation details.

# NOTE: Lead intelligence extraction has been extracted to services/podio/intelligence.py
# The following functions are imported above for backward compatibility:
#   - FIELD_BUNDLES - Lead-type-specific field bundle definitions
#   - get_lead_intelligence(item_id) - Extract all V4.0 enriched intelligence fields
# See services/podio/intelligence.py for implementation details.

# ============================================================================
# TASK CREATION (V3.3)
# ============================================================================

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