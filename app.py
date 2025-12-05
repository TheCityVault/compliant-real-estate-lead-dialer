"""
Flask Application - V2.1 VOIP Edition
Refactored to Service-Oriented Architecture (Phase 3)

This module contains ONLY:
- Flask app initialization
- Route definitions
- Request/response handling
All business logic is delegated to service modules.
"""

import urllib.parse
import requests
from flask import Flask, request, Response, render_template, jsonify

# Import configuration and validation
from config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    TWILIO_API_KEY,
    TWILIO_API_SECRET,
    TWILIO_TWIML_APP_SID,
    DISPOSITION_TASK_MAPPING,  # V3.3: Task automation mapping
    validate_environment,
    VALIDATED_MAILING_ADDRESS_FIELD_ID  # V4.0.6: Property Address field ID
)

# Import service functions
from twilio_service import (
    generate_twilio_token,
    generate_connect_prospect_twiml,
    generate_dial_twiml_for_agent,
    generate_error_twiml,
    get_call_duration,
    get_recording_url
)

from podio_service import (
    get_podio_item,
    extract_field_value,
    extract_field_value_by_id,  # V4.0.6: Field ID based extraction (robust to renames)
    create_call_activity_item,
    update_call_activity_recording,  # V3.2.3
    create_follow_up_task,  # V3.3: Automated task creation
    get_lead_intelligence  # V4.0: Add intelligence extraction
)

from db_service import (
    log_call_to_firestore,
    log_call_status_to_firestore,
    update_call_recording_metadata,  # Step 3.3c: Add recording metadata update
    store_call_sid_mapping,  # V3.2.2: Store CallSid to PodioItemId mapping
    get_podio_item_id_from_call_sid,  # V3.2.3
    get_recording_by_call_sid  # V3.2.5: Race condition fix - check for existing recording
)

# Import Twilio client for call initiation
from config import client

# Initialize Flask app
app = Flask(__name__)

# ============================================================================
# BASIC ROUTES
# ============================================================================

@app.route('/')
def hello_world():
    """Health check endpoint"""
    return 'Hello, World!'

# ============================================================================
# WORKSPACE ROUTE
# ============================================================================

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
        
        # DEBUG: Check all fields in the item
        print("DEBUG: All fields in Master Lead item:")
        for field in lead_item.get('fields', []):
            field_label = field.get('label')
            field_id = field.get('field_id')
            field_values = field.get('values', [])
            print(f"  - {field_label} (ID: {field_id}): {field_values}")
        
        # Extract lead data for workspace
        # V4.0.6 FIX: Lead Information section shows OWNER contact info (for reaching the owner)
        # - address: Owner Mailing Address (274909277) - where to send direct mail to contact owner
        # Note: Property Address (274896122) is displayed in Property Details section via intelligence data
        from config import OWNER_MAILING_ADDRESS_FIELD_ID
        lead_data = {
            'item_id': item_id,
            'name': extract_field_value(lead_item, 'Owner Name'),
            'phone': extract_field_value(lead_item, 'Owner Phone Primary'),  # V4.0.9 FIX: Corrected field label
            'address': extract_field_value_by_id(lead_item, OWNER_MAILING_ADDRESS_FIELD_ID),  # Owner Mailing Address (ID: 274909277)
            'source': 'Podio Master Lead',
            # Contract v1.1.3 fields
            'lead_type': extract_field_value(lead_item, 'Lead Type'),
            'owner_name': extract_field_value(lead_item, 'Owner Name'),
            'owner_phone': extract_field_value(lead_item, 'Owner Phone Primary'),  # V4.0.9 FIX: Corrected field label
            'owner_email': extract_field_value(lead_item, 'Owner Email'),
            'owner_mailing_address': extract_field_value(lead_item, 'Owner Mailing Address'),
            'owner_occupied': extract_field_value(lead_item, 'Owner Occupied'),
            # V4.0.9: Secondary contact fields for multi-phone support
            # V4.0.10 FIX: Use consistent parentheses in field labels (Owner Name (Secondary) not Owner Name Secondary)
            'owner_phone_secondary': extract_field_value(lead_item, 'Owner Phone (Secondary)'),
            'owner_name_secondary': extract_field_value(lead_item, 'Owner Name (Secondary)'),
            'owner_email_secondary': extract_field_value(lead_item, 'Owner Email (Secondary)')
        }
        
        # V4.0.5: Extract enriched intelligence data from Data Pipeline
        # Updated to call get_lead_intelligence(item_id) which handles retrieval internally
        intelligence = get_lead_intelligence(item_id)
        
        print(f"DEBUG: intelligence data extracted:")
        import json
        print(json.dumps(intelligence, indent=2, default=str))
        
        print(f"DEBUG: lead_data being passed to template (Contract v1.1.3):")
        print(f"  item_id: {lead_data['item_id']}")
        print(f"  name: {lead_data['name']}")
        print(f"  phone: {lead_data['phone']}")
        print(f"  address: {lead_data['address']}")
        print(f"  lead_type: {lead_data['lead_type']}")
        print(f"  owner_name: {lead_data['owner_name']}")
        print(f"  owner_phone: {lead_data['owner_phone']}")
        print(f"  owner_email: {lead_data['owner_email']}")
        print(f"  owner_mailing_address: {lead_data['owner_mailing_address']}")
        print(f"  owner_occupied: {lead_data['owner_occupied']}")
        print("="*50)
        
        # Render workspace template with lead data (pass as both 'lead' and 'lead_data' for compatibility)
        return render_template('workspace.html', lead=lead_data, lead_data=lead_data, intelligence=intelligence)
        
    except Exception as e:
        return f"Error loading workspace: {str(e)}", 500

# ============================================================================
# TWILIO TOKEN ROUTE
# ============================================================================

@app.route('/token', methods=['GET'])
def token():
    """Generate Twilio Access Token for Voice SDK v2.x"""
    # Get agent identifier from query params or use a default
    identity = request.args.get('identity', 'default_agent')
    
    # Generate token using service
    token_data = generate_twilio_token(identity)
    
    return jsonify(token_data)

# ============================================================================
# CALL DATA SUBMISSION ROUTE
# ============================================================================

@app.route('/submit_call_data', methods=['POST'])
def submit_call_data():
    """Receive agent disposition and write directly to Podio Call Activity app"""
    try:
        # Parse JSON payload
        data = request.get_json()
        
        # DEBUG: Log the entire payload received
        print("="*50)
        print("SUBMIT_CALL_DATA DEBUG")
        import json
        print(f"Full payload received: {json.dumps(data, indent=2)}")
        print(f"master_lead_item_id (item_id) from payload: {data.get('item_id')}")
        print(f"Type: {type(data.get('item_id'))}")
        print("="*50)
        
        item_id = data.get('item_id')
        call_sid = data.get('call_sid')
        
        print(f"=== SUBMIT CALL DATA (V3.2.5) ===")
        print(f"Master Lead item_id: {item_id}")
        print(f"Call SID: {call_sid}")
        
        # Get call duration and recording URL if call_sid is provided
        call_duration = None
        recording_url = None
        if call_sid:
            call_duration = get_call_duration(call_sid)
            
            # V3.2.5 FIX: Check if recording already arrived via webhook (race condition fix)
            # The recording_status webhook may arrive BEFORE the user submits the form
            # If so, the recording is already in Firestore and we can use it
            existing_recording = get_recording_by_call_sid(call_sid)
            if existing_recording:
                recording_url = existing_recording.get('recording_url')
                print(f"✅ V3.2.5: Found existing recording in Firestore: {recording_url}")
            else:
                # Fall back to original behavior (try Twilio API, returns None per V3.2.3 design)
                recording_url = get_recording_url(call_sid)
                print(f"V3.2.5: No existing recording found, will be added via webhook later")
        
        # Create Call Activity item in Podio
        success, result = create_call_activity_item(
            data, 
            item_id, 
            call_sid, 
            call_duration, 
            recording_url
        )
        if success:
            podio_item_id = result.get('item_id')
            
            # V3.2.2: Store CallSid mapping if call_sid is provided
            if call_sid and podio_item_id:
                store_call_sid_mapping(call_sid, podio_item_id)
            
            # V3.3: Check if disposition requires automated task creation
            disposition_code = data.get('disposition_code')
            if disposition_code and disposition_code in DISPOSITION_TASK_MAPPING:
                task_config = DISPOSITION_TASK_MAPPING[disposition_code]
                if task_config.get('create_task'):
                    print(f"V3.3: Disposition '{disposition_code}' triggers task creation")
                    
                    # V3.3 Enhancement: Allow agent to override default due date
                    task_success, task_result = create_follow_up_task(
                        master_lead_item_id=item_id,
                        task_properties=task_config,
                        agent_specified_date=data.get('next_action_date')  # From form field
                    )
                    
                    if task_success:
                        task_item_id = task_result.get('item_id')
                        print(f"✅ V3.3: Created follow-up task {task_item_id} for disposition '{disposition_code}'")
                    else:
                        print(f"⚠️ V3.3: Task creation failed: {task_result}")
                        # Don't fail the entire request if task creation fails
                else:
                    print(f"V3.3: Disposition '{disposition_code}' does not require task creation")
            else:
                print(f"V3.3: Disposition '{disposition_code}' not found in task mapping or no disposition provided")
            
            # Log to Firestore for audit
            log_call_to_firestore(data, item_id, call_sid)
            
            return jsonify({
                'success': True,
                'podio_item_id': podio_item_id,
                'message': 'Data written to Podio successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 500
            
    except Exception as e:
        print(f"Error in submit_call_data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# DIAL ROUTE
# ============================================================================

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
                method='POST',
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
        prospect_number = request.form.get('prospect_number')
        
        # VOIP-only: Require agent_id parameter
        agent_id = request.form.get('agent_id')

        if not prospect_number:
            response = generate_error_twiml("Sorry, I couldn't initiate the call. Missing prospect number.")
            return str(response)
        
        if not agent_id:
            response = generate_error_twiml("Sorry, I couldn't initiate the call. VOIP agent identifier required.")
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
                method='POST',
                status_callback_event=['answered', 'completed'],
                status_callback=callback_url,
                status_callback_method='POST'
            )
            
            # Generate TwiML response for agent
            response = generate_dial_twiml_for_agent(agent_id)
            print(f"Call initiated to agent: {call.sid}")
            
        except Exception as e:
            print(f"Error initiating call: {e}")
            response = generate_error_twiml("An error occurred while trying to connect the call.")

        return str(response)

# ============================================================================
# CONNECT PROSPECT ROUTE
# ============================================================================

@app.route('/connect_prospect', methods=['GET', 'POST'])
def connect_prospect():
    """TwiML endpoint to connect agent to prospect"""
    # Debug logging
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
    print(f"=== END CONNECT PROSPECT ===")
    print(f"{'='*50}\n")
    
    # Generate TwiML using service
    return generate_connect_prospect_twiml(prospect_number)

# ============================================================================
# CALL STATUS ROUTE
# ============================================================================

@app.route('/call_status', methods=['POST'])
def call_status():
    """Handle call status callbacks from Twilio"""
    call_sid = request.form.get('CallSid')
    call_status_value = request.form.get('CallStatus')
    direction = request.form.get('Direction')
    from_number = request.form.get('From')
    to_number = request.form.get('To')

    print(f"Call SID: {call_sid}, Status: {call_status_value}")
    
    # 🚨 ALERT: Check for "busy" status which indicates potential issues
    if call_status_value == 'busy':
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

    # Log to Firestore
    log_call_status_to_firestore(
        call_sid, 
        call_status_value, 
        direction, 
        from_number, 
        to_number
    )

    return Response(status=200)
# ============================================================================
# RECORDING STATUS ROUTE
# ============================================================================
@app.route('/recording_status', methods=['POST'])
def recording_status():
    """Handle recording status callbacks from Twilio - V3.2.4 Parent CallSid Resolution"""
    recording_sid = request.form.get('RecordingSid')
    recording_url = request.form.get('RecordingUrl')
    call_sid = request.form.get('CallSid')
    recording_duration = request.form.get('RecordingDuration')
    
    print(f"=== RECORDING STATUS CALLBACK (V3.2.4) ===")
    print(f"Recording SID: {recording_sid}")
    print(f"Recording URL: {recording_url}")
    print(f"Call SID (from webhook): {call_sid}")
    print(f"Duration: {recording_duration} seconds")
    print(f"==========================================")
    
    # Update Firestore with recording metadata
    if call_sid and recording_sid and recording_url:
        # Build base URL for proxy endpoint
        base_url = request.url_root.rstrip('/')
        if not base_url.startswith('http'):
            base_url = f"https://{request.host}"
        
        # Build proxy URL for authentication-free playback
        proxy_url = f"{base_url}/play_recording/{recording_sid}"
        
        # Update call log in Firestore
        update_call_recording_metadata(
            call_sid=call_sid,
            recording_sid=recording_sid,
            recording_url=recording_url,
            recording_duration=int(recording_duration) if recording_duration else 0,
            base_url=base_url
        )
        
        # V3.2.4 FIX: Try direct lookup first, then resolve parent CallSid if needed
        # The recording webhook receives the CHILD CallSid (prospect leg created by <Dial>)
        # But the mapping stores the PARENT CallSid (agent leg from /dial endpoint)
        podio_item_id = get_podio_item_id_from_call_sid(call_sid)
        
        if not podio_item_id:
            # No direct mapping found - this is likely a child call from <Dial> TwiML
            # Query Twilio API to find the parent CallSid
            print(f"🔍 V3.2.4: No direct mapping for {call_sid}, checking for parent CallSid...")
            try:
                child_call = client.calls(call_sid).fetch()
                parent_call_sid = child_call.parent_call_sid
                
                if parent_call_sid:
                    print(f"🔗 V3.2.4: Found parent CallSid: {parent_call_sid}")
                    # Now lookup using parent CallSid
                    podio_item_id = get_podio_item_id_from_call_sid(parent_call_sid)
                    if podio_item_id:
                        print(f"✅ V3.2.4: Resolved via parent - Podio Item: {podio_item_id}")
                    else:
                        print(f"⚠️ V3.2.4: Parent CallSid {parent_call_sid} also has no mapping")
                else:
                    print(f"⚠️ V3.2.4: Call {call_sid} has no parent (is itself a parent call)")
            except Exception as e:
                print(f"❌ V3.2.4 ERROR: Failed to query Twilio for parent CallSid: {e}")
        
        if podio_item_id:
            print(f"V3.2.4: Found Podio mapping - Updating item {podio_item_id}")
            
            # Update Podio Call Activity with recording URL
            success, result = update_call_activity_recording(
                call_activity_item_id=podio_item_id,
                recording_url=proxy_url
            )
            
            if success:
                print(f"✅ V3.2.4 SUCCESS: Updated Podio Call Activity {podio_item_id} with recording URL")
            else:
                print(f"❌ V3.2.4 ERROR: Failed to update Podio: {result}")
        else:
            print("⚠️ V3.2.4 WARNING: No Podio mapping found for this CallSid (even after parent resolution) - skipping Podio update")
    else:
        print("WARNING: Missing required recording parameters")
    
    return Response(status=200)
# ============================================================================
# RECORDING PROXY ROUTE
# ============================================================================

@app.route('/play_recording/<recording_sid>', methods=['GET'])
def play_recording(recording_sid):
    """
    Proxy endpoint to stream Twilio recordings without client authentication
    
    Args:
        recording_sid: Twilio Recording SID (e.g., RE1234567890)
        
    Returns:
        Audio stream or error message
    """
    try:
        # Construct authenticated Twilio API URL
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Recordings/{recording_sid}.mp3"
        
        # Fetch recording with server-side authentication
        response = requests.get(
            url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            stream=True
        )
        
        if response.status_code == 200:
            # Stream audio to client
            return Response(
                response.iter_content(chunk_size=1024),
                mimetype='audio/mpeg',
                headers={
                    'Content-Disposition': f'inline; filename="{recording_sid}.mp3"',
                    'Accept-Ranges': 'bytes'
                }
            )
        else:
            return f"Recording not found: {response.status_code}", 404
            
    except Exception as e:
        print(f"Error streaming recording: {e}")
        return f"Error: {str(e)}", 500

    return Response(status=200)


# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True)