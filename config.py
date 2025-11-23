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

# Podio App IDs
CALL_ACTIVITY_APP_ID = os.environ.get('PODIO_CALL_ACTIVITY_APP_ID', '30549170')
MASTER_LEAD_APP_ID = '30549135'  # Master Lead app for item filtering

# Initialize Podio access token (will be obtained on first use)
podio_access_token = None

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

# Call validation on module load (for serverless)
validate_environment()