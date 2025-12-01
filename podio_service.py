"""
Podio Service Module - Intelligence and Task Management

This module handles:
- Lead intelligence extraction (V4.0)
- Task creation (V3.3)
- Lead-type-specific field bundle definitions

Extracted modules:
- OAuth token management: services/podio/oauth.py
- Item CRUD operations: services/podio/item_service.py
- Field value extraction: services/podio/field_extraction.py

For improved modularity and security auditing.
"""
import re
import requests
from datetime import datetime, timedelta
from config import (
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
    # V3.6 Contact Fields (Contract v1.1.3)
    OWNER_NAME_FIELD_ID,
    OWNER_PHONE_FIELD_ID,
    OWNER_EMAIL_FIELD_ID,
    OWNER_MAILING_ADDRESS_FIELD_ID,
    LEAD_TYPE_FIELD_ID,
    # V4.0 Phase 1 Fields (Contract v2.0 - NED/Foreclosure Auction Bundle)
    AUCTION_DATE_FIELD_ID,
    BALANCE_DUE_FIELD_ID,
    OPENING_BID_FIELD_ID,
    AUCTION_PLATFORM_FIELD_ID,
    AUCTION_DATE_PLATFORM_FIELD_ID,
    OPENING_BID_PLATFORM_FIELD_ID,
    AUCTION_LOCATION_FIELD_ID,
    REGISTRATION_DEADLINE_FIELD_ID,
    OWNER_OCCUPIED_FIELD_ID,
    OWNER_NAME_SECONDARY_FIELD_ID,
    OWNER_PHONE_SECONDARY_FIELD_ID,
    OWNER_EMAIL_SECONDARY_FIELD_ID,
    # V4.0 Phase 2 Fields (Contract v2.0 Accelerated - Probate/Estate)
    EXECUTOR_NAME_FIELD_ID,
    PROBATE_CASE_NUMBER_FIELD_ID,
    PROBATE_FILING_DATE_FIELD_ID,
    ESTATE_VALUE_FIELD_ID,
    DECEDENT_NAME_FIELD_ID,
    COURT_JURISDICTION_FIELD_ID,
    # V4.0 Phase 2b Fields (Contract v2.0 - Tax Lien)
    TAX_DEBT_AMOUNT_FIELD_ID,
    DELINQUENCY_START_DATE_FIELD_ID,
    REDEMPTION_DEADLINE_FIELD_ID,
    LIEN_TYPE_FIELD_ID,
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

# ============================================================================
# LEAD-TYPE-SPECIFIC FIELD BUNDLES (Contract v2.0)
# ============================================================================

# Lead-type-specific field bundles per Contract v2.0
# Fields are extracted based on lead_type for optimized data retrieval
FIELD_BUNDLES = {
    "NED Listing": [
        "auction_date",        # NED auction date
        "balance_due",         # Amount owed
        "opening_bid",         # NED opening bid
        "law_firm_name",       # Already in universal fields but critical for NED
        "first_publication_date"  # Already in universal fields but critical for NED
    ],
    "Foreclosure Auction": [
        "auction_platform",      # Platform (Auction.com, Hubzu, etc.)
        "auction_date_platform", # Platform-specific auction date
        "opening_bid_platform",  # Platform-specific opening bid
        "auction_location",      # Physical or online location
        "registration_deadline"  # Deadline to register for auction
    ],
    # V4.0 Phase 2a - Probate/Estate Bundle (6 fields)
    "Probate/Estate": [
        "executor_name",        # Personal Representative (Executor/Administrator)
        "probate_case_number",  # Court case identifier for deduplication
        "probate_filing_date",  # Date probate was filed with court
        "estate_value",         # Total estate value from court filings
        "decedent_name",        # Original property owner (deceased)
        "court_jurisdiction"    # County/district court handling probate
    ],
    # V4.0 Phase 2b - Tax Lien Bundle (4 fields)
    "Tax Lien": [
        "tax_debt_amount",         # Total tax debt/lien amount owed
        "delinquency_start_date",  # Date when tax delinquency began
        "redemption_deadline",     # CRITICAL: Last date owner can redeem property
        "lien_type"                # Type of tax lien (Property Tax, IRS Federal, etc.)
    ],
    # Code Violation - Phase 2 (future)
    # Absentee Owner, Tired Landlord - Phase 3
}

# ============================================================================
# ============================================================================
# OAUTH TOKEN MANAGEMENT
# ============================================================================
# NOTE: OAuth token management has been extracted to services/podio/oauth.py
# The refresh_podio_token function is imported above for backward compatibility.
# See services/podio/oauth.py for implementation details.

# ============================================================================
# ITEM RETRIEVAL & CRUD OPERATIONS
# ============================================================================
# NOTE: Item CRUD operations have been extracted to services/podio/item_service.py
# The following functions are imported above for backward compatibility:
#   - get_podio_item(item_id) - Fetch a Podio item
#   - create_call_activity_item(...) - Create Call Activity in Podio
#   - update_call_activity_recording(...) - Update recording URL
#   - generate_title(data, item_id) - Generate Call Activity title
#   - convert_to_iso_date(date_string) - Date format conversion
# See services/podio/item_service.py for implementation details.

# ============================================================================
# FIELD VALUE EXTRACTION
# ============================================================================
# NOTE: Field extraction utilities have been extracted to services/podio/field_extraction.py
# The following functions are imported above for backward compatibility:
#   - extract_field_value(item, field_label) - Extract by field label
#   - extract_field_value_by_id(item, field_id, field_type) - Extract by field ID
# See services/podio/field_extraction.py for implementation details.

def get_lead_intelligence(item_id):
    """
    Extract all V4.0 Phase 1 enriched intelligence fields from Podio Master Lead item
    with lead-type-aware bundle extraction per Contract v2.0.
    
    Args:
        item_id: Podio Master Lead item ID to retrieve and extract from
        
    Returns:
        dict: Intelligence data with all enriched fields, or empty dict if item not found
        
    Note:
        All fields return None if not populated (graceful degradation).
        UI layer must handle None values appropriately (display "Unknown" or "N/A").
        This function retrieves the item from Podio and extracts up to 28 total fields:
        - 11 V4.0 enriched fields (Contract v1.1.2) - Universal
        - 5 V3.6 contact fields (Contract v1.1.3) - Universal
        - 12 V4.0 Phase 1 fields (Contract v2.0) - Lead-type-specific + universal compliance
        
    Lead-Type-Aware Extraction:
        - lead_type is extracted first to determine which bundle to include
        - Universal fields are always extracted
        - Lead-type-specific bundle fields are extracted based on lead_type
        - Secondary owner and owner_occupied fields are always extracted (apply to ALL lead types)
    """
    # Retrieve the lead item from Podio
    item = get_podio_item(item_id)
    
    if not item:
        print(f"WARNING: Could not retrieve item {item_id} for intelligence extraction")
        return {}
    
    # STEP 1: Extract lead_type FIRST (determines bundle extraction)
    lead_type = extract_field_value_by_id(item, LEAD_TYPE_FIELD_ID)
    
    # STEP 2: Extract Universal Fields (always included - 16 fields from v1.1.2/v1.1.3)
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
        
        # V3.6 Contact Fields (Contract v1.1.3)
        'owner_name': extract_field_value_by_id(item, OWNER_NAME_FIELD_ID),
        'owner_phone': extract_field_value_by_id(item, OWNER_PHONE_FIELD_ID),  # Click-to-dial enabled
        'owner_email': extract_field_value_by_id(item, OWNER_EMAIL_FIELD_ID),
        'owner_mailing_address': extract_field_value_by_id(item, OWNER_MAILING_ADDRESS_FIELD_ID),
        'lead_type': lead_type,  # Already extracted above
    }
    
    # STEP 3: Extract Lead-Type-Specific Bundle Fields (Contract v2.0)
    if lead_type == "NED Listing":
        # NED Foreclosure Bundle
        intelligence.update({
            'auction_date': extract_field_value_by_id(item, AUCTION_DATE_FIELD_ID),
            'balance_due': extract_field_value_by_id(item, BALANCE_DUE_FIELD_ID),
            'opening_bid': extract_field_value_by_id(item, OPENING_BID_FIELD_ID),
        })
        print(f"V4.0 Phase 1: Extracted NED Listing bundle for item {item_id}")
        
    elif lead_type == "Foreclosure Auction":
        # Foreclosure Auction Bundle
        intelligence.update({
            'auction_platform': extract_field_value_by_id(item, AUCTION_PLATFORM_FIELD_ID),
            'auction_date_platform': extract_field_value_by_id(item, AUCTION_DATE_PLATFORM_FIELD_ID),
            'opening_bid_platform': extract_field_value_by_id(item, OPENING_BID_PLATFORM_FIELD_ID),
            'auction_location': extract_field_value_by_id(item, AUCTION_LOCATION_FIELD_ID),
            'registration_deadline': extract_field_value_by_id(item, REGISTRATION_DEADLINE_FIELD_ID),
        })
        print(f"V4.0 Phase 1: Extracted Foreclosure Auction bundle for item {item_id}")
        
    elif lead_type == "Probate/Estate":
        # V4.0 Phase 2a - Probate/Estate Bundle (6 fields)
        intelligence.update({
            'executor_name': extract_field_value_by_id(item, EXECUTOR_NAME_FIELD_ID),
            'probate_case_number': extract_field_value_by_id(item, PROBATE_CASE_NUMBER_FIELD_ID),
            'probate_filing_date': extract_field_value_by_id(item, PROBATE_FILING_DATE_FIELD_ID),
            'estate_value': extract_field_value_by_id(item, ESTATE_VALUE_FIELD_ID),
            'decedent_name': extract_field_value_by_id(item, DECEDENT_NAME_FIELD_ID),
            'court_jurisdiction': extract_field_value_by_id(item, COURT_JURISDICTION_FIELD_ID),
        })
        print(f"V4.0 Phase 2a: Extracted Probate/Estate bundle for item {item_id}")
        
    elif lead_type == "Tax Lien":
        # V4.0 Phase 2b - Tax Lien Bundle (4 fields)
        intelligence.update({
            'tax_debt_amount': extract_field_value_by_id(item, TAX_DEBT_AMOUNT_FIELD_ID),
            'delinquency_start_date': extract_field_value_by_id(item, DELINQUENCY_START_DATE_FIELD_ID),
            'redemption_deadline': extract_field_value_by_id(item, REDEMPTION_DEADLINE_FIELD_ID),
            'lien_type': extract_field_value_by_id(item, LIEN_TYPE_FIELD_ID),
        })
        print(f"V4.0 Phase 2b: Extracted Tax Lien bundle for item {item_id}")
        
    else:
        # Unknown or unsupported lead type - log for Phase 2/3 development
        if lead_type:
            print(f"V4.0: Lead type '{lead_type}' not yet supported - Phase 2/3 bundle")
        else:
            print(f"V4.0: No lead_type set for item {item_id}")
    
    # STEP 4: Extract Universal Compliance & Secondary Owner Fields (apply to ALL lead types)
    # These fields are critical for compliance and apply regardless of lead type
    intelligence.update({
        # Compliance & Risk Section (CRITICAL - applies to all lead types)
        'owner_occupied': extract_field_value_by_id(item, OWNER_OCCUPIED_FIELD_ID),
        
        # Secondary Owner Contact (applies to all lead types with co-owners)
        'owner_name_secondary': extract_field_value_by_id(item, OWNER_NAME_SECONDARY_FIELD_ID),
        'owner_phone_secondary': extract_field_value_by_id(item, OWNER_PHONE_SECONDARY_FIELD_ID),
        'owner_email_secondary': extract_field_value_by_id(item, OWNER_EMAIL_SECONDARY_FIELD_ID),
    })
    
    return intelligence

# ============================================================================
# DATA TRANSFORMATION UTILITIES
# ============================================================================
# NOTE: Data transformation utilities have been extracted to services/podio/item_service.py
# The following functions are imported above for backward compatibility:
#   - convert_to_iso_date(date_string) - Convert MM/DD/YYYY to ISO 8601
#   - parse_currency(value) - Parse currency string to float
#   - generate_title(data, item_id) - Generate Call Activity title
# See services/podio/item_service.py for implementation details.

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