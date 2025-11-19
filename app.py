import os
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Dial
from twilio.rest import Client
import json
import firebase_admin
from firebase_admin import credentials, firestore
import urllib.parse

app = Flask(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
AGENT_PHONE_NUMBER = os.environ.get('AGENT_PHONE_NUMBER')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Initialize Firestore
GCP_SERVICE_ACCOUNT_JSON = os.environ.get('GCP_SERVICE_ACCOUNT_JSON')
if GCP_SERVICE_ACCOUNT_JSON:
    try:
        service_account_info = json.loads(GCP_SERVICE_ACCOUNT_JSON)
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firestore initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firestore: {e}")
        db = None
else:
    print("GCP_SERVICE_ACCOUNT_JSON environment variable not set. Firestore logging will be disabled.")
    db = None

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/dial', methods=['GET', 'POST'])
def dial():
    # Handle GET requests (Link Field approach from Podio)
    if request.method == 'GET':
        prospect_number = urllib.parse.unquote_plus(request.args.get('phone', ''))
        
        if not prospect_number:
            return """
            <html>
            <head><title>Error</title></head>
            <body>
                <h2>❌ Error</h2>
                <p>Missing phone number parameter.</p>
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
            print(f"Agent Phone: {AGENT_PHONE_NUMBER}")
            print(f"Twilio Phone: {TWILIO_PHONE_NUMBER}")
            print(f"Prospect Number: {prospect_number}")
            print(f"=== END DIAL DEBUG ===")
            
            # Initiate the call to the agent
            call = client.calls.create(
                to=AGENT_PHONE_NUMBER,
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
    
    # Handle POST requests (backwards compatibility)
    else:
        response = VoiceResponse()
        prospect_number = request.form.get('prospect_number')

        if not prospect_number:
            response.say("Sorry, I couldn't initiate the call. Missing prospect number.")
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
            print(f"=== END DIAL DEBUG (POST) ===")
            
            # Initiate the call to the agent
            call = client.calls.create(
                to=AGENT_PHONE_NUMBER,
                from_=TWILIO_PHONE_NUMBER,
                url=connect_url,
                method='POST',  # Explicitly specify POST method
                status_callback_event=['answered', 'completed'],
                status_callback=callback_url,
                status_callback_method='POST'
            )
            response.say("Connecting you to the agent.")
            response.dial(number=AGENT_PHONE_NUMBER) # This dial is for the initial call to the agent
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
        dial = Dial()
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

if __name__ == '__main__':
    app.run(debug=True)