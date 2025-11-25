"""
Configuration Module - Centralized Environment Variables and Global Objects

This module handles:
- Environment variable loading
- Twilio client initialization
- Firebase/Firestore initialization
- Podio configuration
- Configuration validation
"""

import os
import json
from dotenv import load_dotenv
from twilio.rest import Client
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# TWILIO CONFIGURATION
# ============================================================================

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
TWILIO_TWIML_APP_SID = os.environ.get('TWILIO_TWIML_APP_SID')
TWILIO_API_KEY = os.environ.get('TWILIO_API_KEY')
TWILIO_API_SECRET = os.environ.get('TWILIO_API_SECRET')

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ============================================================================
# PODIO CONFIGURATION
# ============================================================================

PODIO_CLIENT_ID = os.environ.get('PODIO_CLIENT_ID')
PODIO_CLIENT_SECRET = os.environ.get('PODIO_CLIENT_SECRET')
PODIO_USERNAME = os.environ.get('PODIO_USERNAME')
PODIO_PASSWORD = os.environ.get('PODIO_PASSWORD')

# Podio Field IDs - V2.0 Agent Workspace Schema
DISPOSITION_CODE_FIELD_ID = 274851083
AGENT_NOTES_FIELD_ID = 274851084
MOTIVATION_LEVEL_FIELD_ID = 274851085
NEXT_ACTION_DATE_FIELD_ID = 274851086
ASKING_PRICE_FIELD_ID = 274851087

# Podio Field IDs - System Fields
TITLE_FIELD_ID = 274769797
RELATIONSHIP_FIELD_ID = 274851864  # "Relationship" field in Call Activity app
DATE_OF_CALL_FIELD_ID = 274769799
CALL_DURATION_FIELD_ID = 274769800
RECORDING_URL_FIELD_ID = 274769801
# Podio Field IDs - V4.0 Enriched Data (Data Pipeline Integration)
# Priority Metrics (Agent Routing)
LEAD_SCORE_FIELD_ID = 274896114
LEAD_TIER_FIELD_ID = 274896115

# Deal Qualification (Financial Intelligence)
ESTIMATED_PROPERTY_VALUE_FIELD_ID = 274896116
EQUITY_PERCENTAGE_FIELD_ID = 274896117
ESTIMATED_EQUITY_FIELD_ID = 274896118

# Property Details
YEAR_BUILT_FIELD_ID = 274896119
PROPERTY_TYPE_FIELD_ID = 274896120

# Contact & Context
APN_FIELD_ID = 274896121
VALIDATED_MAILING_ADDRESS_FIELD_ID = 274896122

# Timeline & Compliance
FIRST_PUBLICATION_DATE_FIELD_ID = 274896123
LAW_FIRM_NAME_FIELD_ID = 274896414


# Podio App IDs
CALL_ACTIVITY_APP_ID = os.environ.get('PODIO_CALL_ACTIVITY_APP_ID', '30549170')
MASTER_LEAD_APP_ID = '30549135'  # Master Lead app for item filtering
TASK_APP_ID = os.environ.get('PODIO_TASK_APP_ID', 'TASK_APP_ID_HERE')  # V3.3: Task app for automated task creation

# Initialize Podio access token (will be obtained on first use)
podio_access_token = None

# ============================================================================
# TASK AUTOMATION CONFIGURATION (V3.3)
# ============================================================================

# Map disposition codes to task creation rules
# IMPORTANT: Keys must EXACTLY match the disposition values in workspace.html
DISPOSITION_TASK_MAPPING = {
    'Voicemail': {  # Changed from 'Left Voicemail' to match form
        'create_task': True,
        'task_type': 'Follow-up Call',
        'due_date_offset_days': 2,  # Task due 2 days from now
        'task_title': 'Follow up on voicemail'
    },
    'No Answer': {
        'create_task': True,
        'task_type': 'Follow-up Call',
        'due_date_offset_days': 1,  # Task due 1 day from now
        'task_title': 'Retry call - no answer'
    },
    'Appointment Set': {  # Changed from 'Interested - Schedule Appointment' to match form
        'create_task': True,
        'task_type': 'Appointment',
        'due_date_offset_days': 0,  # Due today
        'task_title': 'Schedule appointment'
    },
    'Callback Scheduled': {  # Changed from 'Callback Requested' to match form
        'create_task': True,
        'task_type': 'Follow-up Call',
        'due_date_offset_days': 1,
        'task_title': 'Callback requested by prospect'
    },
    # Dispositions that DON'T create tasks
    'Not Interested': {
        'create_task': False
    },
    'Wrong Number': {
        'create_task': False
    },
    'Do Not Call': {
        'create_task': False
    }
}

# Podio Task Field IDs (V3.3)
# NOTE: These will need to be configured based on your Task app schema
# Use the Podio API or browser inspector to obtain actual field IDs
TASK_TITLE_FIELD_ID = os.environ.get('TASK_TITLE_FIELD_ID', 'TASK_TITLE_FIELD_ID_HERE')
TASK_TYPE_FIELD_ID = os.environ.get('TASK_TYPE_FIELD_ID', 'TASK_TYPE_FIELD_ID_HERE')
TASK_DUE_DATE_FIELD_ID = os.environ.get('TASK_DUE_DATE_FIELD_ID', 'TASK_DUE_DATE_FIELD_ID_HERE')
TASK_MASTER_LEAD_RELATIONSHIP_FIELD_ID = os.environ.get('TASK_MASTER_LEAD_RELATIONSHIP_FIELD_ID', 'TASK_MASTER_LEAD_RELATIONSHIP_FIELD_ID_HERE')

# ============================================================================
# FIREBASE/FIRESTORE CONFIGURATION
# ============================================================================

GCP_SERVICE_ACCOUNT_JSON = os.environ.get('GCP_SERVICE_ACCOUNT_JSON')

# Initialize Firestore client
db = None

if GCP_SERVICE_ACCOUNT_JSON:
    try:
        service_account_info = json.loads(GCP_SERVICE_ACCOUNT_JSON)
        cred = credentials.Certificate(service_account_info)
        
        # Check if Firebase Admin app already exists (serverless caching)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin initialized successfully")
        else:
            print("ℹ️ Firebase Admin app already exists (using cached instance)")
        
        # Initialize Firestore client
        db = firestore.client()
        
        # Validate Firestore is working
        print(f"✅ Firestore client initialized: {type(db)}")
        print(f"✅ Firestore project: {db.project}")
        
    except Exception as e:
        print(f"❌ CRITICAL: Error initializing Firestore: {e}")
        import traceback
        traceback.print_exc()
        db = None
else:
    print("⚠️ WARNING: GCP_SERVICE_ACCOUNT_JSON not set. Firestore disabled.")
    db = None

# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

def validate_enriched_fields():
    """Validate V4.0 enriched field IDs at startup"""
    enriched_fields = {
        'LEAD_SCORE_FIELD_ID': LEAD_SCORE_FIELD_ID,
        'LEAD_TIER_FIELD_ID': LEAD_TIER_FIELD_ID,
        'ESTIMATED_PROPERTY_VALUE_FIELD_ID': ESTIMATED_PROPERTY_VALUE_FIELD_ID,
        'EQUITY_PERCENTAGE_FIELD_ID': EQUITY_PERCENTAGE_FIELD_ID,
        'ESTIMATED_EQUITY_FIELD_ID': ESTIMATED_EQUITY_FIELD_ID,
        'YEAR_BUILT_FIELD_ID': YEAR_BUILT_FIELD_ID,
        'PROPERTY_TYPE_FIELD_ID': PROPERTY_TYPE_FIELD_ID,
        'APN_FIELD_ID': APN_FIELD_ID,
        'VALIDATED_MAILING_ADDRESS_FIELD_ID': VALIDATED_MAILING_ADDRESS_FIELD_ID,
        'FIRST_PUBLICATION_DATE_FIELD_ID': FIRST_PUBLICATION_DATE_FIELD_ID,
        'LAW_FIRM_NAME_FIELD_ID': LAW_FIRM_NAME_FIELD_ID,
    }
    
    print(f"\n{'='*50}")
    print(f"=== V4.0 ENRICHED FIELD VALIDATION ===")
    all_valid = True
    for field_name, field_id in enriched_fields.items():
        if field_id is not None:
            print(f"✅ {field_name}: {field_id}")
        else:
            print(f"❌ {field_name}: NOT SET")
            all_valid = False
    
    if all_valid:
        print(f"✅ All 11 enriched field IDs validated successfully")
    else:
        print(f"⚠️ WARNING: Some enriched field IDs are missing")
    print(f"{'='*50}\n")
    
    return all_valid

def validate_environment():
    """Validate critical environment variables at startup"""
    required_vars = {
        'TWILIO_ACCOUNT_SID': TWILIO_ACCOUNT_SID,
        'TWILIO_AUTH_TOKEN': TWILIO_AUTH_TOKEN,
        'TWILIO_PHONE_NUMBER': TWILIO_PHONE_NUMBER,
        'TWILIO_API_KEY': TWILIO_API_KEY,
        'TWILIO_API_SECRET': TWILIO_API_SECRET,
        'TWILIO_TWIML_APP_SID': TWILIO_TWIML_APP_SID,
    }
    
    print(f"\n{'='*50}")
    print(f"=== V2.1 VOIP-ONLY ENVIRONMENT VALIDATION ===")
    for var_name, var_value in required_vars.items():
        if var_value:
            if 'TOKEN' in var_name or 'SID' in var_name or 'SECRET' in var_name:
                print(f"✅ {var_name}: {var_value[:8]}... (masked)")
            else:
                print(f"✅ {var_name}: {var_value}")
        else:
            print(f"❌ {var_name}: NOT SET")
    print(f"{'='*50}\n")
    
    # V4.0: Validate enriched field IDs
    validate_enriched_fields()

# Call validation on module load (for serverless)
validate_environment()
