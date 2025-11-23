"""
Twilio Service Module - TwiML Generation and Access Token Logic

This module handles:
- TwiML response generation for voice calls
- Access Token generation for VOIP clients
- Call duration and recording URL retrieval
"""

import urllib.parse
from flask import Response
from twilio.twiml.voice_response import VoiceResponse, Dial
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from config import (
    client,
    TWILIO_ACCOUNT_SID,
    TWILIO_API_KEY,
    TWILIO_API_SECRET,
    TWILIO_TWIML_APP_SID,
    TWILIO_PHONE_NUMBER
)

# ============================================================================
# ACCESS TOKEN GENERATION
# ============================================================================

def generate_twilio_token(identity='default_agent'):
    """
    Generate Twilio Access Token for Voice SDK v2.x
    
    Args:
        identity: Agent identifier (default: 'default_agent')
        
    Returns:
        dict: Token data with 'token' and 'identity' keys
    """
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
    
    return {
        'token': jwt_token if isinstance(jwt_token, str) else jwt_token.decode('utf-8'),
        'identity': identity
    }

# ============================================================================
# TWIML GENERATION
# ============================================================================

def generate_connect_prospect_twiml(prospect_number):
    """
    Generate TwiML to connect agent to prospect
    
    Args:
        prospect_number: Prospect's phone number
        
    Returns:
        Response: Flask Response object with TwiML XML
    """
    response = VoiceResponse()
    
    # Decode and format the prospect number
    prospect_number = urllib.parse.unquote_plus(prospect_number)
    
    print(f"Generating TwiML for prospect: {prospect_number}")
    
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
        
        print(f"Final formatted prospect_number: {prospect_number}")
        
        response.say("Connecting you to the prospect.")
        dial = Dial(callerId=TWILIO_PHONE_NUMBER)
        dial.number(prospect_number)
        response.append(dial)
    else:
        print("ERROR: No prospect_number provided!")
        response.say("Sorry, I couldn't connect to the prospect. Missing phone number.")
    
    twiml_output = str(response)
    print(f"TwiML generated ({len(twiml_output)} bytes): {twiml_output}")
    
    return Response(twiml_output, mimetype='text/xml')

def generate_dial_twiml_for_agent(agent_id):
    """
    Generate TwiML to dial the agent (legacy POST flow)
    
    Args:
        agent_id: Agent identifier (client:agent_xxxxx or phone number)
        
    Returns:
        VoiceResponse: TwiML response object
    """
    response = VoiceResponse()
    response.say("Connecting you to the agent.")
    
    dial = Dial()
    if agent_id.startswith('client:'):
        # VOIP client - strip "client:" prefix
        dial.client(agent_id[7:])
    else:
        # PSTN number
        dial.number(agent_id)
    
    response.append(dial)
    
    return response

def generate_error_twiml(error_message):
    """
    Generate TwiML error response
    
    Args:
        error_message: Error message to speak
        
    Returns:
        VoiceResponse: TwiML response object
    """
    response = VoiceResponse()
    response.say(error_message)
    return response

# ============================================================================
# CALL DATA RETRIEVAL
# ============================================================================

def get_call_duration(call_sid):
    """
    Fetch call duration from Twilio API
    
    Args:
        call_sid: Twilio Call SID
        
    Returns:
        int: Call duration in seconds, or None if unavailable
    """
    if not call_sid:
        return None
    
    try:
        call = client.calls(call_sid).fetch()
        duration = call.duration
        return duration if duration is not None else None
    except Exception as e:
        print(f"Error fetching call duration: {e}")
        return None

def get_recording_url(call_sid):
    """
    Fetch recording URL from Twilio API
    
    Args:
        call_sid: Twilio Call SID
        
    Returns:
        str: Recording URL, or None if unavailable
    """
    if not call_sid:
        return None
    
    try:
        recordings = client.recordings.list(call_sid=call_sid, limit=1)
        if recordings:
            return f"https://api.twilio.com{recordings[0].uri}"
        return None
    except Exception as e:
        print(f"Error fetching recording URL: {e}")
        return None