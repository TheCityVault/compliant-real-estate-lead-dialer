import os
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Dial
from twilio.rest import Client
import json
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

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

@app.route('/dial', methods=['POST'])
def dial():
    response = VoiceResponse()
    agent_number = request.form.get('agent_number')
    prospect_number = request.form.get('prospect_number')

    if not all([agent_number, prospect_number]):
        response.say("Sorry, I couldn't initiate the call. Missing agent or prospect number.")
        return str(response)

    try:
        # Initiate the call to the agent
        call = client.calls.create(
            to=agent_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{request.url_root}connect_prospect?prospect_number={prospect_number}",
            status_callback_event=['answered', 'completed'],
            status_callback=f"{request.url_root}call_status"
        )
        response.say("Connecting you to the agent.")
        response.dial(number=agent_number) # This dial is for the initial call to the agent
        print(f"Call initiated to agent: {call.sid}")
    except Exception as e:
        print(f"Error initiating call: {e}")
        response.say("An error occurred while trying to connect the call.")

    return str(response)

@app.route('/connect_prospect', methods=['POST'])
def connect_prospect():
    response = VoiceResponse()
    prospect_number = request.args.get('prospect_number')
    if prospect_number:
        response.say("Connecting you to the prospect.")
        response.dial(number=prospect_number)
    else:
        response.say("Sorry, I couldn't connect to the prospect.")
    return str(response)

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