import os
import re
from dotenv import load_dotenv
from flask import Flask, request, Response, render_template, jsonify
from datetime import datetime

# Load environment variables from .env file
load_dotenv()
from twilio.twiml.voice_response import VoiceResponse, Dial
from twilio.rest import Client
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
import json
import firebase_admin
from firebase_admin import credentials, firestore
import urllib.parse
import requests

app = Flask(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
TWILIO_TWIML_APP_SID = os.environ.get('TWILIO_TWIML_APP_SID')
TWILIO_API_KEY = os.environ.get('TWILIO_API_KEY')
TWILIO_API_SECRET = os.environ.get('TWILIO_API_SECRET')
# AGENT_PHONE_NUMBER removed - V2.1 VOIP-only architecture

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Podio credentials
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
RELATIONSHIP_FIELD_ID = 274851864  # Updated: Actual "Relationship" field in Call Activity app
DATE_OF_CALL_FIELD_ID = 274769799
CALL_DURATION_FIELD_ID = 274769800
RECORDING_URL_FIELD_ID = 274769801

# Podio App IDs
CALL_ACTIVITY_APP_ID = os.environ.get('PODIO_CALL_ACTIVITY_APP_ID', '30549170')
MASTER_LEAD_APP_ID = '30549135'  # Master Lead app for item filtering

# Initialize Podio access token
podio_access_token = None

def get_podio_token():
    """Get Podio OAuth access token"""
    global podio_access_token
    
    if not all([PODIO_CLIENT_ID, PODIO_CLIENT_SECRET, PODIO_USERNAME, PODIO_PASSWORD]):
        print("Podio credentials not fully configured. Podio integration will be disabled.")
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
            podio_access_token = token_data.get('access_token')
            print("Podio token obtained successfully.")
            return podio_access_token
        else:
            print(f"Error getting Podio token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error initializing Podio authentication: {e}")
        return None

def get_podio_item(item_id):
    """Fetch a specific Podio item using app filter (workaround for direct access 404s)
    
    Args:
        item_id: The Podio item ID to fetch
        
    Returns:
        dict: Item data if found, None otherwise
        
    Note:
        Uses POST /item/app/{app_id}/filter instead of GET /item/{id}
        due to permission/access restrictions on direct item retrieval.
    """
    token = get_podio_token()
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
def extract_field_value(item, field_label):
    """Extract field value from Podio item by field label"""
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
    return ''

def convert_to_iso_date(date_string):
    """Convert MM/DD/YYYY to ISO 8601 format for Podio"""
    if not date_string:
        return None
    try:
        dt = datetime.strptime(date_string, '%m/%d/%Y')
        return dt.isoformat()
    except:
        return None

def parse_currency(value):
    """Parse currency string to float"""
    if not value:
        return None
    try:
        # Remove $ and commas
        cleaned = str(value).replace('$', '').replace(',', '').strip()
        return float(cleaned) if cleaned else None
    except:
        return None

def generate_title(data, item_id):
    """Generate Call Activity title"""
    timestamp = datetime.now().strftime('%m/%d/%Y %I:%M %p')
    return f"Call - Lead #{item_id} - {timestamp}"

def get_call_duration(call_sid):
    """Fetch call duration from Twilio API"""
    if not call_sid:
        return None
    try:
        call = client.calls(call_sid).fetch()
        duration = call.duration
        return duration if duration is not None else None
    except:
        return None

def get_recording_url(call_sid):
    """Fetch recording URL from Twilio API"""
    if not call_sid:
        return None
    try:
        recordings = client.recordings.list(call_sid=call_sid, limit=1)
        if recordings:
            return f"https://api.twilio.com{recordings[0].uri}"
        return None
    except:
        return None

def log_to_firestore(data, item_id, call_sid):
    """Log call disposition to Firestore for audit"""
    if not db:
        print("Firestore not available, skipping audit log")
        return
    
    try:
        log_entry = {
            'item_id': item_id,
            'call_sid': call_sid,
            'disposition_code': data.get('disposition_code'),
            'agent_notes': data.get('agent_notes', ''),
            'motivation_level': data.get('motivation_level', ''),
            'next_action_date': data.get('next_action_date', ''),
            'asking_price': data.get('asking_price', ''),
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        db.collection('disposition_logs').add(log_entry)
        print(f"Logged disposition to Firestore for item {item_id}")
    except Exception as e:
        print(f"Error logging to Firestore: {e}")

# Initialize Firestore
GCP_SERVICE_ACCOUNT_JSON = os.environ.get('GCP_SERVICE_ACCOUNT_JSON')
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

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/workspace', methods=['GET'])
def workspace():
    """Serve Agent Workspace interface with lead data"""
    item_id = request.args.get('item_id')
    
    print("="*50)
    print("WORKSPACE ENDPOINT DEBUG")
    print(f"item_id from URL parameter: {item_id}")
    print(f"Type: {type(item_id)}")
    print("="*50)
    
    if not item_id:
        return "Error: Missing item_id parameter", 400
    
    try:
        # Fetch Master Lead item from Podio
        lead_item = get_podio_item(item_id)
        
        # DEBUG: Check all fields in the item to find where 1112233 might be
        print("DEBUG: All fields in Master Lead item:")
        for field in lead_item.get('fields', []):
            field_label = field.get('label')
            field_id = field.get('field_id')
            field_values = field.get('values', [])
            print(f"  - {field_label} (ID: {field_id}): {field_values}")
        
        # Extract lead data for workspace
        lead_data = {
            'item_id': item_id,  # ← THIS SHOULD BE 3204110525 from URL
            'name': extract_field_value(lead_item, 'Owner Name'),
            'phone': extract_field_value(lead_item, 'Best Contact Number'),
            'address': extract_field_value(lead_item, 'Full Address'),
            'source': 'Podio Master Lead'
        }
        
        print(f"DEBUG: lead_data being passed to template:")
        print(f"  item_id: {lead_data['item_id']}")
        print(f"  name: {lead_data['name']}")
        print(f"  phone: {lead_data['phone']}")
        print(f"  address: {lead_data['address']}")
        print("="*50)
        
        # Render workspace template with lead data
        return render_template('workspace.html', lead=lead_data)
        
    except Exception as e:
        return f"Error loading workspace: {str(e)}", 500

@app.route('/token', methods=['GET'])
def token():
    """Generate Twilio Access Token for Voice SDK v2.x"""
    # Get agent identifier from query params or use a default
    identity = request.args.get('identity', 'default_agent')
    
    # Create Access Token for v2.x SDK using API Key credentials
    access_token = AccessToken(
        TWILIO_ACCOUNT_SID,
        TWILIO_API_KEY,
        TWILIO_API_SECRET,
        identity=identity
    )
    
    # Create a Voice grant and add to token
    voice_grant = VoiceGrant(
        outgoing_application_sid=TWILIO_TWIML_APP_SID,
        incoming_allow=True  # Allow incoming calls
    )
    access_token.add_grant(voice_grant)
    
    # Generate and return the token
    jwt_token = access_token.to_jwt()
    
    # Return token as JSON
    return jsonify({
        'token': jwt_token if isinstance(jwt_token, str) else jwt_token.decode('utf-8'),
        'identity': identity
    })

@app.route('/submit_call_data', methods=['POST'])
def submit_call_data():
    """Receive agent disposition and write directly to Podio Call Activity app"""
    try:
        # Parse JSON payload
        data = request.get_json()
        
        # DEBUG: Log the entire payload received
        print("="*50)
        print("SUBMIT_CALL_DATA DEBUG")
        print(f"Full payload received: {json.dumps(data, indent=2)}")
        print(f"master_lead_item_id (item_id) from payload: {data.get('item_id')}")
        print(f"Type: {type(data.get('item_id'))}")
        print("="*50)
        
        item_id = data.get('item_id')
        call_sid = data.get('call_sid')
        
        print(f"=== SUBMIT CALL DATA ===")
        print(f"Master Lead item_id: {item_id}")
        print(f"Call SID: {call_sid}")
        
        # Get Podio access token
        token = get_podio_token()
        if not token:
            return jsonify({'success': False, 'error': 'Podio authentication failed'}), 500
        
        # Log the item_id we'll use for the relationship field
        # Verification removed - workspace already confirmed item exists when loading lead data
        print(f"DEBUG: Using Master Lead item_id for relationship: {item_id}")
        print(f"DEBUG: item_id type: {type(item_id)}, value: {item_id}")
        
        # Prepare Podio item payload with all 10 fields
        podio_fields = {
            # AGENT-ENTERED FIELDS (from workspace form)
            str(DISPOSITION_CODE_FIELD_ID): data.get('disposition_code'),
            str(RELATIONSHIP_FIELD_ID): [int(item_id)],  # CRITICAL: Links to Master Lead (array format)
            str(DATE_OF_CALL_FIELD_ID): datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # DEBUG: Log what we're about to send to Podio
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
        
        # Add CALL_DURATION if we have a call_sid
        if call_sid:
            duration = get_call_duration(call_sid)
            if duration is not None and duration > 0:
                podio_fields[str(CALL_DURATION_FIELD_ID)] = duration
            
            # Add RECORDING_URL if available
            recording_url = get_recording_url(call_sid)
            if recording_url:
                podio_fields[str(RECORDING_URL_FIELD_ID)] = recording_url
        
        # DEBUG: Log the complete payload before sending to Podio
        print("="*50)
        print("FINAL PODIO PAYLOAD DEBUG")
        print(f"Full payload being sent to Podio:")
        print(json.dumps({'fields': podio_fields}, indent=2))
        print(f"Relationship field ({RELATIONSHIP_FIELD_ID}) value type: {type(podio_fields.get(str(RELATIONSHIP_FIELD_ID)))}")
        print(f"Relationship field ({RELATIONSHIP_FIELD_ID}) value: {podio_fields.get(str(RELATIONSHIP_FIELD_ID))}")
        print("="*50)
        
        # Create Call Activity Item in Podio
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
            # Log to Firestore for audit
            log_to_firestore(data, item_id, call_sid)
            
            return jsonify({
                'success': True,
                'podio_item_id': response.json().get('item_id'),
                'message': 'Data written to Podio successfully'
            }), 200
        else:
            print(f"❌ Podio API ERROR: {response.status_code}")
            print(f"Error response: {response.text}")
            # Parse and return the detailed Podio error
            try:
                error_data = response.json()
                return jsonify({
                    'success': False,
                    'error': error_data.get('error_description', 'Podio write failed'),
                    'error_details': error_data
                }), 500
            except:
                return jsonify({'success': False, 'error': f'Podio write failed: {response.text}'}), 500
            
    except Exception as e:
        print(f"Error in submit_call_data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/dial', methods=['GET', 'POST'])
def dial():
    """
    V2.1 VOIP-ONLY DIAL ENDPOINT
    
    Initiates a call using Twilio Client (browser-based VOIP).
    Requires agent_id parameter in format: client:agent_xxxxx
    
    PSTN fallback removed in V2.1 to prevent carrier blocking issues.
    All agents must use VOIP calling via the Agent Workspace.
    """
    # Add environment variable verification logging
    print(f"\n{'='*50}")
    print(f"=== V2.1 VOIP-ONLY ENVIRONMENT VERIFICATION ===")
    print(f"TWILIO_PHONE_NUMBER: {TWILIO_PHONE_NUMBER}")
    print(f"TWILIO_ACCOUNT_SID: {TWILIO_ACCOUNT_SID[:8]}... (masked)")
    print(f"TWILIO_API_KEY: {TWILIO_API_KEY[:8]}... (masked)")
    print(f"TWILIO_API_SECRET: {TWILIO_API_SECRET[:8]}... (masked)")
    print(f"{'='*50}\n")
    
    # Handle AJAX POST requests from Agent Workspace
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        item_id = data.get('item_id')
        prospect_number = data.get('phone')
        
        # VOIP-only: Require agent_id parameter
        agent_id = data.get('agent_id')
        
        if not agent_id:
            return jsonify({
                'success': False,
                'error': 'Agent ID is required for VOIP calling'
            }), 400
        
        print(f"AJAX POST to /dial - item_id: {item_id}, phone: {prospect_number}, agent_id: {agent_id}")
        
        try:
            # Build callback URLs
            base_url = request.url_root.rstrip('/')
            if not base_url.startswith('http'):
                base_url = f"https://{request.host}"
            
            connect_url = f"{base_url}/connect_prospect?prospect_number={urllib.parse.quote_plus(prospect_number)}"
            callback_url = f"{base_url}/call_status"
            
            print(f"=== AJAX DIAL DEBUG ===")
            print(f"Base URL: {base_url}")
            print(f"Connect URL: {connect_url}")
            print(f"Callback URL: {callback_url}")
            print(f"Agent ID: {agent_id}")
            print(f"Connection Type: {'VOIP' if agent_id.startswith('client:') else 'PSTN'}")
            print(f"Twilio Phone: {TWILIO_PHONE_NUMBER}")
            print(f"Prospect Number: {prospect_number}")
            print(f"=== END AJAX DIAL DEBUG ===")
            
            # Initiate call - use agent_id instead of hardcoded AGENT_PHONE_NUMBER
            call = client.calls.create(
                to=agent_id,
                from_=TWILIO_PHONE_NUMBER,
                url=connect_url,
                method='POST',
                status_callback_event=['answered', 'completed'],
                status_callback=callback_url,
                status_callback_method='POST'
            )
            
            print(f"Call initiated to agent via AJAX: {call.sid}")
            
            # Return JSON response for AJAX
            return jsonify({
                'success': True,
                'call_sid': call.sid,
                'message': 'Call initiated successfully'
            }), 200
            
        except Exception as e:
            print(f"Error initiating AJAX call: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # Handle GET requests (Link Field approach from Podio)
    if request.method == 'GET':
        prospect_number = None
        item_id = request.args.get('item_id')
        
        # VOIP-only: Require agent_id parameter
        agent_id = request.args.get('agent_id')
        
        if not agent_id:
            return """
            <html>
            <head><title>Error</title></head>
            <body>
                <h2>❌ Error</h2>
                <p>VOIP Agent ID is required. Please use the Agent Workspace.</p>
            </body>
            </html>
            """, 400
        
        print(f"\n{'='*50}")
        print(f"=== DIAL ENDPOINT CALLED ===")
        print(f"Request Args: {dict(request.args)}")
        print(f"Agent ID: {agent_id}")
        print(f"Connection Type: {'VOIP' if agent_id.startswith('client:') else 'PSTN'}")
        
        # Check if item_id is provided (Podio integration)
        if item_id:
            print(f"Item ID provided: {item_id}")
            
            try:
                # Fetch the item from Podio
                print(f"Fetching Podio item {item_id}...")
                item = get_podio_item(item_id)
                print(f"Podio item fetched successfully")
                print(f"Item fields: {[f.get('label') for f in item.get('fields', [])]}")
                
                # Extract phone number from the "Best Contact Number" field
                phone_field = None
                for field in item.get('fields', []):
                    if field.get('label') == 'Best Contact Number':
                        phone_field = field
                        break
                
                if not phone_field:
                    print("ERROR: 'Best Contact Number' field not found in item")
                    return """
                    <html>
                    <head><title>Error</title></head>
                    <body>
                        <h2>❌ Error</h2>
                        <p>The 'Best Contact Number' field was not found in this Podio item.</p>
                    </body>
                    </html>
                    """, 400
                
                # Extract phone value
                values = phone_field.get('values', [])
                if not values or len(values) == 0:
                    print("ERROR: 'Best Contact Number' field is empty")
                    return """
                    <html>
                    <head><title>Error</title></head>
                    <body>
                        <h2>❌ Error</h2>
                        <p>The 'Best Contact Number' field is empty for this lead.</p>
                    </body>
                    </html>
                    """, 400
                
                # Get the phone value - pypodio2 structures phone values as dicts
                phone_value = values[0]
                if isinstance(phone_value, dict):
                    prospect_number = phone_value.get('value', '')
                else:
                    prospect_number = str(phone_value)
                
                print(f"Phone number extracted from Podio: {prospect_number}")
                
            except Exception as e:
                print(f"ERROR fetching from Podio API: {e}")
                import traceback
                traceback.print_exc()
                
                error_message = str(e)
                if "404" in error_message or "not found" in error_message.lower():
                    return """
                    <html>
                    <head><title>Error</title></head>
                    <body>
                        <h2>❌ Error</h2>
                        <p>Podio item not found. Please check the item ID.</p>
                    </body>
                    </html>
                    """, 404
                elif "401" in error_message or "403" in error_message or "unauthorized" in error_message.lower():
                    return """
                    <html>
                    <head><title>Error</title></head>
                    <body>
                        <h2>❌ Error</h2>
                        <p>Podio authentication failed. Please contact your administrator.</p>
                    </body>
                    </html>
                    """, 500
                elif "rate limit" in error_message.lower():
                    return """
                    <html>
                    <head><title>Error</title></head>
                    <body>
                        <h2>❌ Error</h2>
                        <p>Podio API rate limit reached. Please try again in a few moments.</p>
                    </body>
                    </html>
                    """, 429
                else:
                    return f"""
                    <html>
                    <head><title>Error</title></head>
                    <body>
                        <h2>❌ Error</h2>
                        <p>An error occurred while fetching data from Podio: {error_message}</p>
                    </body>
                    </html>
                    """, 500
        else:
            # Use phone parameter if item_id not provided
            prospect_number = urllib.parse.unquote_plus(request.args.get('phone', ''))
            print(f"Phone parameter provided: {prospect_number}")
        
        print(f"Final prospect_number to dial: {prospect_number}")
        print(f"=== END DIAL ENDPOINT ===")
        print(f"{'='*50}\n")
        
        if not prospect_number:
            return """
            <html>
            <head><title>Error</title></head>
            <body>
                <h2>❌ Error</h2>
                <p>Missing phone number. Please provide either 'phone' or 'item_id' parameter.</p>
            </body>
            </html>
            """, 400
        
        try:
            # Build absolute URL for Vercel deployment
            base_url = request.url_root.rstrip('/')
            if not base_url.startswith('http'):
                base_url = f"https://{request.host}"
            
            connect_url = f"{base_url}/connect_prospect?prospect_number={urllib.parse.quote_plus(prospect_number)}"
            callback_url = f"{base_url}/call_status"
            
            print(f"=== DIAL ENDPOINT DEBUG ===")
            print(f"Base URL: {base_url}")
            print(f"Connect URL: {connect_url}")
            print(f"Callback URL: {callback_url}")
            print(f"Agent ID: {agent_id}")
            print(f"Connection Type: {'VOIP' if agent_id.startswith('client:') else 'PSTN'}")
            print(f"Twilio Phone: {TWILIO_PHONE_NUMBER}")
            print(f"Prospect Number: {prospect_number}")
            print(f"=== END DIAL DEBUG ===")
            
            # Initiate the call to the agent - use agent_id instead of hardcoded AGENT_PHONE_NUMBER
            call = client.calls.create(
                to=agent_id,
                from_=TWILIO_PHONE_NUMBER,
                url=connect_url,
                method='POST',  # Explicitly specify POST method
                status_callback_event=['answered', 'completed'],
                status_callback=callback_url,
                status_callback_method='POST'
            )
            print(f"Call initiated to agent via GET: {call.sid}")
            
            # Return HTML page showing call initiation status
            return f"""
            <html>
            <head><title>Initiating Call...</title></head>
            <body>
                <h2>📞 Initiating Call to {prospect_number}</h2>
                <p>Your phone should ring shortly...</p>
                <script>setTimeout(function(){{window.close();}}, 3000);</script>
            </body>
            </html>
            """
        except Exception as e:
            print(f"Error initiating call via GET: {e}")
            return f"""
            <html>
            <head><title>Error</title></head>
            <body>
                <h2>❌ Error</h2>
                <p>An error occurred while trying to initiate the call: {str(e)}</p>
            </body>
            </html>
            """, 500
    
    # Handle legacy POST requests (VOIP-only)
    else:
        response = VoiceResponse()
        prospect_number = request.form.get('prospect_number')
        
        # VOIP-only: Require agent_id parameter
        agent_id = request.form.get('agent_id')

        if not prospect_number:
            response.say("Sorry, I couldn't initiate the call. Missing prospect number.")
            return str(response)
        
        if not agent_id:
            response.say("Sorry, I couldn't initiate the call. VOIP agent identifier required.")
            return str(response)

        try:
            # Build absolute URL for Vercel deployment
            base_url = request.url_root.rstrip('/')
            if not base_url.startswith('http'):
                base_url = f"https://{request.host}"
            
            connect_url = f"{base_url}/connect_prospect?prospect_number={urllib.parse.quote_plus(prospect_number)}"
            callback_url = f"{base_url}/call_status"
            
            print(f"=== DIAL ENDPOINT DEBUG (POST) ===")
            print(f"Base URL: {base_url}")
            print(f"Connect URL: {connect_url}")
            print(f"Callback URL: {callback_url}")
            print(f"Agent ID: {agent_id}")
            print(f"Connection Type: {'VOIP' if agent_id.startswith('client:') else 'PSTN'}")
            print(f"=== END DIAL DEBUG (POST) ===")
            
            # Initiate the call to the agent - use agent_id instead of hardcoded AGENT_PHONE_NUMBER
            call = client.calls.create(
                to=agent_id,
                from_=TWILIO_PHONE_NUMBER,
                url=connect_url,
                method='POST',  # Explicitly specify POST method
                status_callback_event=['answered', 'completed'],
                status_callback=callback_url,
                status_callback_method='POST'
            )
            response.say("Connecting you to the agent.")
            # Note: The following dial is for the initial call to the agent (legacy TwiML flow)
            # For VOIP, this should use <Client>, for PSTN use <Number>
            dial = Dial()
            if agent_id.startswith('client:'):
                dial.client(agent_id[7:])  # Strip "client:" prefix
            else:
                dial.number(agent_id)
            response.append(dial)
            print(f"Call initiated to agent: {call.sid}")
        except Exception as e:
            print(f"Error initiating call: {e}")
            response.say("An error occurred while trying to connect the call.")

        return str(response)

@app.route('/connect_prospect', methods=['GET', 'POST'])
def connect_prospect():
    response = VoiceResponse()
    
    # Debug logging - START
    print(f"\n{'='*50}")
    print(f"=== CONNECT PROSPECT CALLED ===")
    print(f"Request Method: {request.method}")
    print(f"Request URL: {request.url}")
    print(f"Request Headers: {dict(request.headers)}")
    print(f"Request Args: {dict(request.args)}")
    print(f"Request Form: {dict(request.form)}")
    
    prospect_number = urllib.parse.unquote_plus(request.args.get('prospect_number', ''))
    
    print(f"Raw prospect_number from args: {request.args.get('prospect_number', 'MISSING')}")
    print(f"Decoded prospect_number: {prospect_number}")
    
    if prospect_number:
        # Ensure number has +1 country code if it doesn't already
        if not prospect_number.startswith('+'):
            # Remove any non-digit characters except +
            cleaned_number = ''.join(filter(str.isdigit, prospect_number))
            # Add +1 if not present
            if len(cleaned_number) == 10:
                prospect_number = f"+1{cleaned_number}"
            elif len(cleaned_number) == 11 and cleaned_number.startswith('1'):
                prospect_number = f"+{cleaned_number}"
            else:
                prospect_number = f"+{cleaned_number}"
        
        print(f"Final formatted prospect_number to dial: {prospect_number}")
        
        response.say("Connecting you to the prospect.")
        dial = Dial(callerId=TWILIO_PHONE_NUMBER)
        dial.number(prospect_number)
        response.append(dial)
        
        twiml_output = str(response)
        print(f"TwiML response generated:\n{twiml_output}")
    else:
        print("ERROR: No prospect_number received!")
        print("ERROR: No prospect_number received!")
        response.say("Sorry, I couldn't connect to the prospect. Missing phone number.")
    
    print(f"=== END CONNECT PROSPECT ===")
    print(f"{'='*50}\n")
    
    final_twiml = str(response)
    print(f"Returning TwiML ({len(final_twiml)} bytes): {final_twiml}")
    return Response(final_twiml, mimetype='text/xml')

@app.route('/call_status', methods=['POST'])
def call_status():
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    direction = request.form.get('Direction')
    from_number = request.form.get('From')
    to_number = request.form.get('To')
    timestamp = firestore.SERVER_TIMESTAMP # Use Firestore's server timestamp

    print(f"Call SID: {call_sid}, Status: {call_status}")
    
    # 🚨 ALERT: Check for "busy" status which indicates potential issues
    if call_status == 'busy':
        print(f"\n{'='*50}")
        print(f"🚨 ALERT: BUSY STATUS DETECTED")
        print(f"Call SID: {call_sid}")
        print(f"From: {from_number}")
        print(f"To: {to_number}")
        print(f"Direction: {direction}")
        print(f"This may indicate:")
        print(f"  - VOIP connection issue")
        print(f"  - Prospect phone returned busy signal")
        print(f"ACTION REQUIRED: Verify agent VOIP connection is active")
        print(f"{'='*50}\n")

    if db:
        try:
            log_entry = {
                "CallSid": call_sid,
                "CallStatus": call_status,
                "Direction": direction,
                "From": from_number,
                "To": to_number,
                "Timestamp": timestamp
            }
            db.collection("call_logs").add(log_entry)
            print(f"Logged call status for Call SID: {call_sid} to Firestore.")
        except Exception as e:
            print(f"Error logging to Firestore: {e}")
    else:
        print("Firestore client not initialized. Skipping logging.")

    return Response(status=200)

def validate_environment():
    """Validate critical environment variables at startup"""
    required_vars = {
        'TWILIO_ACCOUNT_SID': TWILIO_ACCOUNT_SID,
        'TWILIO_AUTH_TOKEN': TWILIO_AUTH_TOKEN,
        'TWILIO_PHONE_NUMBER': TWILIO_PHONE_NUMBER,
        'TWILIO_API_KEY': TWILIO_API_KEY,
        'TWILIO_API_SECRET': TWILIO_API_SECRET,
        'TWILIO_TWIML_APP_SID': TWILIO_TWIML_APP_SID,
        # AGENT_PHONE_NUMBER removed - VOIP-only architecture
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

if __name__ == '__main__':
    app.run(debug=True)