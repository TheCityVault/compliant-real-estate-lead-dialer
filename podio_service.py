"""
Podio Service Module - OAuth, Item Management, and Relationship Handling

This module handles:
- OAuth token refresh and management
- Podio item retrieval and filtering
- Call Activity item creation
- Field value extraction and parsing
- Data transformation utilities
"""
import re
import requests
from datetime import datetime, timedelta
from config import (
    PODIO_CLIENT_ID,
    PODIO_CLIENT_SECRET,
    PODIO_USERNAME,
    PODIO_PASSWORD,
    MASTER_LEAD_APP_ID,
    CALL_ACTIVITY_APP_ID,
    TASK_APP_ID,
    DISPOSITION_CODE_FIELD_ID,
    AGENT_NOTES_FIELD_ID,
    MOTIVATION_LEVEL_FIELD_ID,
    NEXT_ACTION_DATE_FIELD_ID,
    ASKING_PRICE_FIELD_ID,
    TITLE_FIELD_ID,
    RELATIONSHIP_FIELD_ID,
    DATE_OF_CALL_FIELD_ID,
    CALL_DURATION_FIELD_ID,
    RECORDING_URL_FIELD_ID,
    TASK_TITLE_FIELD_ID,
    TASK_TYPE_FIELD_ID,
    TASK_DUE_DATE_FIELD_ID,
    TASK_MASTER_LEAD_RELATIONSHIP_FIELD_ID,
    # V4.0 Enriched Data Field IDs
    LEAD_SCORE_FIELD_ID,
    LEAD_TIER_FIELD_ID,
    ESTIMATED_PROPERTY_VALUE_FIELD_ID,
    EQUITY_PERCENTAGE_FIELD_ID,
    ESTIMATED_EQUITY_FIELD_ID,
    YEAR_BUILT_FIELD_ID,
    PROPERTY_TYPE_FIELD_ID,
    APN_FIELD_ID,
    VALIDATED_MAILING_ADDRESS_FIELD_ID,
    FIRST_PUBLICATION_DATE_FIELD_ID,
    LAW_FIRM_NAME_FIELD_ID,
    podio_access_token
)

# Global variable to hold the access token
_podio_token = podio_access_token

# ============================================================================
# OAUTH TOKEN MANAGEMENT
# ============================================================================

def refresh_podio_token():
    """
    Get or refresh Podio OAuth access token
    
    Returns:
        str: Access token, or None if authentication fails
    """
    global _podio_token
    
    # Enhanced credential diagnostics
    print("="*50)
    print("PODIO TOKEN REFRESH ATTEMPT")
    print(f"CLIENT_ID present: {bool(PODIO_CLIENT_ID)} (length: {len(PODIO_CLIENT_ID) if PODIO_CLIENT_ID else 0})")
    print(f"CLIENT_SECRET present: {bool(PODIO_CLIENT_SECRET)} (length: {len(PODIO_CLIENT_SECRET) if PODIO_CLIENT_SECRET else 0})")
    print(f"USERNAME present: {bool(PODIO_USERNAME)} (value: {PODIO_USERNAME[:3] + '***' if PODIO_USERNAME and len(PODIO_USERNAME) > 3 else 'None'})")
    print(f"PASSWORD present: {bool(PODIO_PASSWORD)} (length: {len(PODIO_PASSWORD) if PODIO_PASSWORD else 0})")
    print("="*50)
    
    if not all([PODIO_CLIENT_ID, PODIO_CLIENT_SECRET, PODIO_USERNAME, PODIO_PASSWORD]):
        print("❌ CRITICAL: Podio credentials not fully configured. Podio integration will be disabled.")
        print(f"Missing credentials:")
        if not PODIO_CLIENT_ID:
            print("  - PODIO_CLIENT_ID")
        if not PODIO_CLIENT_SECRET:
            print("  - PODIO_CLIENT_SECRET")
        if not PODIO_USERNAME:
            print("  - PODIO_USERNAME")
        if not PODIO_PASSWORD:
            print("  - PODIO_PASSWORD")
        return None
    
    try:
        # Get OAuth token from Podio
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
            _podio_token = token_data.get('access_token')
            print("Podio token obtained successfully.")
            return _podio_token
        else:
            print(f"="*50)
            print(f"ERROR getting Podio token: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response text: {response.text}")
            print(f"="*50)
            return None
    except Exception as e:
        print(f"Error initializing Podio authentication: {e}")
        return None

# ============================================================================
# ITEM RETRIEVAL
# ============================================================================

def get_podio_item(item_id):
    """
    Fetch a specific Podio item using app filter (workaround for direct access 404s)
    
    Args:
        item_id: The Podio item ID to fetch
        
    Returns:
        dict: Item data if found, None otherwise
        
    Note:
        Uses POST /item/app/{app_id}/filter instead of GET /item/{id}
        due to permission/access restrictions on direct item retrieval.
    """
    token = refresh_podio_token()
    if not token:
        print("ERROR: Could not obtain Podio OAuth token")
        return None
    
    try:
        # Use app-based filtering instead of direct item access
        response = requests.post(
            f'https://api.podio.com/item/app/{MASTER_LEAD_APP_ID}/filter',
            headers={
                'Authorization': f'OAuth2 {token}',
                'Content-Type': 'application/json'
            },
            json={
                'filters': {
                    'item_id': int(item_id)  # Filter by specific item_id
                },
                'limit': 1  # Only return the single matching item
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            if items:
                print(f"SUCCESS: Retrieved item {item_id} via app filter")
                return items[0]  # Return first (and only) match
            else:
                print(f"WARNING: No items found matching item_id={item_id}")
                return None
        else:
            print(f"ERROR: Podio API returned {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"EXCEPTION in get_podio_item(): {str(e)}")
        return None

# ============================================================================
# FIELD VALUE EXTRACTION
# ============================================================================

def extract_field_value(item, field_label):
    """
    Extract field value from Podio item by field label
    
    Args:
        item: Podio item dictionary
        field_label: Label of the field to extract
        
    Returns:
        str: Field value, or empty string if not found
    """
    for field in item.get('fields', []):
        if field.get('label') == field_label:
            values = field.get('values', [])
            if values:
                value = values[0]
                # Handle different field types
                if isinstance(value, dict):
                    text = value.get('value', '')
                else:
                    text = str(value)
                
                # Strip HTML tags (e.g., <p>Name</p> -> Name)
                text = re.sub(r'<[^>]+>', '', text)
                return text.strip()
    return ''

def extract_field_value_by_id(item, field_id):
    """
    Extract field value from Podio item by field ID (V4.0 Data Pipeline Integration)
    
    Args:
        item: Podio item dictionary
        field_id: Numeric field ID to extract
        
    Returns:
        Extracted value (type varies: int, float, str), or None if not found
        
    Note:
        Handles all Podio field types: number, category, money, text, date.
        Returns None for graceful degradation in UI.
    """
    if not item:
        return None
    
    for field in item.get('fields', []):
        if field.get('field_id') == int(field_id):
            values = field.get('values', [])
            if not values:
                return None
            
            value = values[0]
            field_type = field.get('type')
            
            # Handle different Podio field types
            if field_type == 'category':
                # Category fields return dict with 'text' key
                return value.get('text') if isinstance(value, dict) else str(value)
            elif field_type == 'money':
                # Money fields return dict with 'value' key (string)
                return float(value.get('value')) if isinstance(value, dict) else None
            elif field_type == 'number':
                # Number fields return string
                try:
                    return float(value) if value else None
                except (ValueError, TypeError):
                    return None
            elif field_type == 'date':
                # Date fields return dict with 'start' key (YYYY-MM-DD format)
                return value.get('start') if isinstance(value, dict) else str(value)
            elif field_type == 'text':
                # Text fields return string (strip HTML like extract_field_value does)
                text = str(value) if value else None
                if text:
                    text = re.sub(r'<[^>]+>', '', text)
                    return text.strip()
                return None
            else:
                # Default: return raw value
                return value
    return None

def get_lead_intelligence(item):
    """
    Extract all V4.0 enriched intelligence fields from Podio Master Lead item
    
    Args:
        item: Podio Master Lead item dictionary
        
    Returns:
        dict: Intelligence data with all enriched fields, or empty dict if item is None
        
    Note:
        All fields return None if not populated (graceful degradation).
        UI layer must handle None values appropriately (display "Unknown" or "N/A").
    """
    if not item:
        return {}
    
    intelligence = {
        # Priority Metrics (ui_priority 1-2) - MOST IMPORTANT
        'lead_score': extract_field_value_by_id(item, LEAD_SCORE_FIELD_ID),
        'lead_tier': extract_field_value_by_id(item, LEAD_TIER_FIELD_ID),
        
        # Deal Qualification (ui_priority 3-5) - FINANCIAL INTELLIGENCE
        'estimated_property_value': extract_field_value_by_id(item, ESTIMATED_PROPERTY_VALUE_FIELD_ID),
        'equity_percentage': extract_field_value_by_id(item, EQUITY_PERCENTAGE_FIELD_ID),
        'estimated_equity': extract_field_value_by_id(item, ESTIMATED_EQUITY_FIELD_ID),
        
        # Property Details (ui_priority 6-7) - CONTEXT
        'year_built': extract_field_value_by_id(item, YEAR_BUILT_FIELD_ID),
        'property_type': extract_field_value_by_id(item, PROPERTY_TYPE_FIELD_ID),
        
        # Contact & Context (ui_priority 9) - APN hidden, address displayed
        'validated_mailing_address': extract_field_value_by_id(item, VALIDATED_MAILING_ADDRESS_FIELD_ID),
        
        # Timeline & Compliance (ui_priority 10-11) - REGULATORY
        'first_publication_date': extract_field_value_by_id(item, FIRST_PUBLICATION_DATE_FIELD_ID),
        'law_firm_name': extract_field_value_by_id(item, LAW_FIRM_NAME_FIELD_ID),
    }
    
    return intelligence

# ============================================================================
# DATA TRANSFORMATION UTILITIES
# ============================================================================

def convert_to_iso_date(date_string):
    """
    Convert MM/DD/YYYY to ISO 8601 format for Podio
    
    Args:
        date_string: Date string in MM/DD/YYYY format
        
    Returns:
        str: ISO 8601 formatted date, or None if invalid
    """
    if not date_string:
        return None
    try:
        dt = datetime.strptime(date_string, '%m/%d/%Y')
        return dt.isoformat()
    except:
        return None

def parse_currency(value):
    """
    Parse currency string to float
    
    Args:
        value: Currency string (e.g., "$1,234.56")
        
    Returns:
        float: Parsed currency value, or None if invalid
    """
    if not value:
        return None
    try:
        # Remove $ and commas
        cleaned = str(value).replace('$', '').replace(',', '').strip()
        return float(cleaned) if cleaned else None
    except:
        return None

def generate_title(data, item_id):
    """
    Generate Call Activity title
    
    Args:
        data: Call data dictionary
        item_id: Master Lead item ID
        
    Returns:
        str: Formatted title for Call Activity item
    """
    timestamp = datetime.now().strftime('%m/%d/%Y %I:%M %p')
    return f"Call - Lead #{item_id} - {timestamp}"

# ============================================================================
# CALL ACTIVITY ITEM CREATION
# ============================================================================

def create_call_activity_item(data, item_id, call_sid, call_duration=None, recording_url=None):
    """
    Create Call Activity item in Podio with relationship to Master Lead
    
    Args:
        data: Call disposition data from agent
        item_id: Master Lead item ID to link to
        call_sid: Twilio Call SID
        call_duration: Optional call duration in seconds
        recording_url: Optional recording URL
        
    Returns:
        tuple: (success: bool, result: dict or error message)
    """
    token = refresh_podio_token()
    if not token:
        print("="*50)
        print("CRITICAL: Podio token refresh failed")
        print(f"PODIO_CLIENT_ID present: {bool(PODIO_CLIENT_ID)}")
        print(f"PODIO_CLIENT_SECRET present: {bool(PODIO_CLIENT_SECRET)}")
        print(f"PODIO_USERNAME present: {bool(PODIO_USERNAME)}")
        print(f"PODIO_PASSWORD present: {bool(PODIO_PASSWORD)}")
        print("="*50)
        return False, 'Podio authentication failed'
    
    # DEBUG logging
    print(f"=== CREATE CALL ACTIVITY ===")
    print(f"Master Lead item_id: {item_id}")
    print(f"Call SID: {call_sid}")
    print(f"DEBUG: Using Master Lead item_id for relationship: {item_id}")
    print(f"DEBUG: item_id type: {type(item_id)}, value: {item_id}")
    
    # Prepare Podio item payload with all fields
    podio_fields = {
        # AGENT-ENTERED FIELDS
        str(DISPOSITION_CODE_FIELD_ID): data.get('disposition_code'),
        str(RELATIONSHIP_FIELD_ID): [int(item_id)],  # CRITICAL: Links to Master Lead
        str(DATE_OF_CALL_FIELD_ID): datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    # DEBUG: Log relationship field
    print(f"DEBUG: Relationship field ({RELATIONSHIP_FIELD_ID}) value = {int(item_id)}")
    print(f"DEBUG: Type of relationship value = {type(int(item_id))}")
    
    # Add TITLE field - ensure it's never empty
    title = generate_title(data, item_id)
    if title:
        podio_fields[str(TITLE_FIELD_ID)] = title
    else:
        podio_fields[str(TITLE_FIELD_ID)] = f"Call Activity - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # Add optional AGENT fields - only if non-empty
    agent_notes = data.get('agent_notes', '').strip()
    if agent_notes:
        podio_fields[str(AGENT_NOTES_FIELD_ID)] = agent_notes
        
    motivation_level = data.get('motivation_level', '').strip()
    if motivation_level:
        podio_fields[str(MOTIVATION_LEVEL_FIELD_ID)] = motivation_level
    
    # Add NEXT_ACTION_DATE if provided
    next_action_date = convert_to_iso_date(data.get('next_action_date'))
    if next_action_date:
        podio_fields[str(NEXT_ACTION_DATE_FIELD_ID)] = next_action_date
    
    # Add ASKING_PRICE if provided
    asking_price = parse_currency(data.get('asking_price'))
    if asking_price is not None:
        podio_fields[str(ASKING_PRICE_FIELD_ID)] = asking_price
    
    # Add CALL_DURATION if available
    if call_duration is not None:
        try:
            duration_int = int(call_duration) if isinstance(call_duration, str) else call_duration
            if duration_int > 0:
                podio_fields[str(CALL_DURATION_FIELD_ID)] = duration_int
        except (ValueError, TypeError):
            print(f"WARNING: Invalid call_duration value: {call_duration}")
    
    # Add RECORDING_URL if available
    if recording_url:
        podio_fields[str(RECORDING_URL_FIELD_ID)] = recording_url
    
    # DEBUG: Log the complete payload
    print("="*50)
    print("FINAL PODIO PAYLOAD DEBUG")
    print(f"Full payload being sent to Podio:")
    import json
    print(json.dumps({'fields': podio_fields}, indent=2))
    print(f"Relationship field ({RELATIONSHIP_FIELD_ID}) value type: {type(podio_fields.get(str(RELATIONSHIP_FIELD_ID)))}")
    print(f"Relationship field ({RELATIONSHIP_FIELD_ID}) value: {podio_fields.get(str(RELATIONSHIP_FIELD_ID))}")
    print("="*50)
    
    # Create Call Activity Item in Podio
    try:
        response = requests.post(
            f'https://api.podio.com/item/app/{CALL_ACTIVITY_APP_ID}/',
            headers={
                'Authorization': f'OAuth2 {token}',
                'Content-Type': 'application/json'
            },
            json={'fields': podio_fields}
        )
        
        print(f"Podio API Response Status: {response.status_code}")
        print(f"Podio API Response Body: {response.text}")
        
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            print(f"❌ Podio API ERROR: {response.status_code}")
            print(f"Error response: {response.text}")
            try:
                error_data = response.json()
                return False, error_data.get('error_description', 'Podio write failed')
            except:
                return False, f'Podio write failed: {response.text}'
                
    except Exception as e:
        print(f"Exception creating Podio item: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

# ============================================================================
# CALL ACTIVITY RECORDING UPDATE (V3.1 PLACEHOLDER)
# ============================================================================

def update_call_activity_recording(call_activity_item_id, recording_url):
    """
    Update existing Call Activity item with recording URL
    
    Args:
        call_activity_item_id: Podio Call Activity item ID (if known)
        recording_url: URL to access/download the recording
        
    Returns:
        tuple: (success: bool, result: dict or error message)
        
    Note:
        For V3.1, this function is a placeholder. Full integration requires
        storing CallSid→CallActivityItemId mapping in Firestore or passing
        the Call Activity Item ID through the call flow.
        
    TODO V3.2 Enhancement:
        - Store CallSid→CallActivityItemId mapping in Firestore when creating Call Activity
        - Pass Call Activity Item ID through Twilio call flow using custom parameters
        - Update recording webhook to retrieve Call Activity Item ID from mapping
        - Enable automatic recording URL updates without manual ID tracking
    """
    token = refresh_podio_token()
    if not token:
        return False, 'Podio authentication failed'
    
    if not call_activity_item_id:
        print("WARNING: No Call Activity Item ID provided for recording URL update")
        return False, 'No Call Activity Item ID provided'
    
    try:
        # Update the Call Activity item with recording URL
        response = requests.put(
            f'https://api.podio.com/item/{call_activity_item_id}',
            headers={
                'Authorization': f'OAuth2 {token}',
                'Content-Type': 'application/json'
            },
            json={
                'fields': {
                    str(RECORDING_URL_FIELD_ID): recording_url
                }
            }
        )
        
        if response.status_code == 200:
            print(f"Updated Call Activity {call_activity_item_id} with recording URL")
            return True, response.json()
        else:
            print(f"Failed to update Call Activity {call_activity_item_id}: {response.text}")
            return False, f'Podio update failed: {response.text}'
            
    except Exception as e:
        print(f"Error updating Call Activity with recording URL: {e}")
        return False, str(e)

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