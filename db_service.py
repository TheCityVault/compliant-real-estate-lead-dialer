"""
Database Service Module - Firestore Logging and Audit Trail

This module handles:
- Call disposition logging to Firestore
- Call status logging
- Audit trail creation
"""

from firebase_admin import firestore
from config import db

# ============================================================================
# CALL DISPOSITION LOGGING
# ============================================================================

def log_call_to_firestore(data, item_id, call_sid):
    """
    Log call disposition to Firestore for audit
    
    Args:
        data: Call disposition data from agent
        item_id: Master Lead item ID
        call_sid: Twilio Call SID
        
    Returns:
        bool: True if logged successfully, False otherwise
    """
    if not db:
        print("Firestore not available, skipping audit log")
        return False
    
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
        return True
    except Exception as e:
        print(f"Error logging to Firestore: {e}")
        return False

# ============================================================================
# CALL SID MAPPING STORAGE (V3.2.2)
# ============================================================================

def store_call_sid_mapping(call_sid, podio_item_id):
    """
    Store CallSid to PodioItemId mapping for webhook lookups
    
    This temporary mapping enables the /recording_status webhook to link
    the asynchronous Twilio callback to the correct Podio Call Activity item.
    
    Args:
        call_sid: Twilio Call SID (the key for lookup)
        podio_item_id: Podio Call Activity Item ID (the value to retrieve)
        
    Returns:
        bool: True if stored successfully, False otherwise
    """
    if not db:
        print("Firestore not available, skipping CallSid mapping")
        return False
    
    try:
        mapping_entry = {
            'call_sid': call_sid,
            'podio_item_id': podio_item_id,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        # Use call_sid as document ID for direct lookup
        db.collection('call_sid_mappings').document(call_sid).set(mapping_entry)
        print(f"Stored CallSid mapping: {call_sid} → Podio Item {podio_item_id}")
        return True
    except Exception as e:
        print(f"Error storing CallSid mapping: {e}")
        return False

def get_podio_item_id_from_call_sid(call_sid):
    """
    Retrieve Podio Call Activity Item ID from CallSid mapping
    
    This function enables the /recording_status webhook to link the
    asynchronous Twilio callback back to the correct Podio Call Activity item.
    
    Args:
        call_sid: Twilio Call SID (used as document ID for lookup)
        
    Returns:
        str: Podio Call Activity Item ID if found, None otherwise
    """
    if not db:
        print("Firestore not available, cannot retrieve CallSid mapping")
        return None
    
    try:
        # Direct document lookup using call_sid as document ID
        doc_ref = db.collection('call_sid_mappings').document(call_sid)
        doc = doc_ref.get()
        
        if doc.exists:
            mapping_data = doc.to_dict()
            podio_item_id = mapping_data.get('podio_item_id')
            print(f"Retrieved mapping: {call_sid} → Podio Item {podio_item_id}")
            return podio_item_id
        else:
            print(f"WARNING: No mapping found for CallSid {call_sid}")
            return None
            
    except Exception as e:
        print(f"Error retrieving CallSid mapping: {e}")
        return None

# ============================================================================
# CALL STATUS LOGGING
# ============================================================================

def log_call_status_to_firestore(call_sid, call_status, direction, from_number, to_number):
    """
    Log call status updates to Firestore for monitoring
    
    Args:
        call_sid: Twilio Call SID
        call_status: Call status (e.g., 'answered', 'completed', 'busy')
        direction: Call direction
        from_number: Caller phone number
        to_number: Recipient phone number
        
    Returns:
        bool: True if logged successfully, False otherwise
    """
    if not db:
        print("Firestore client not initialized. Skipping logging.")
        return False
    
    try:
        log_entry = {
            "CallSid": call_sid,
            "CallStatus": call_status,
            "Direction": direction,
            "From": from_number,
            "To": to_number,
            "Timestamp": firestore.SERVER_TIMESTAMP
        }
        db.collection("call_logs").add(log_entry)
        print(f"Logged call status for Call SID: {call_sid} to Firestore.")
        return True
    except Exception as e:
        print(f"Error logging to Firestore: {e}")
        return False

# ============================================================================
# RECORDING LOOKUP BY CALLSID (V3.2.5)
# ============================================================================

def get_recording_by_call_sid(call_sid):
    """
    Retrieve recording info from Firestore by CallSid
    
    This function supports the race condition fix where the recording webhook
    may arrive before the disposition form is submitted. When creating the
    Podio Call Activity, we check if a recording already exists.
    
    Args:
        call_sid: Twilio Call SID
        
    Returns:
        dict: Recording metadata if found, None otherwise
        Contains: recording_sid, recording_url, recording_duration
    """
    if not db:
        print("Firestore not available, cannot retrieve recording")
        return None
    
    try:
        # Query for call log entry with matching CallSid
        call_logs_ref = db.collection('call_logs')
        query = call_logs_ref.where('CallSid', '==', call_sid).limit(1)
        docs = query.stream()
        
        for doc in docs:
            data = doc.to_dict()
            recording_sid = data.get('RecordingSid')
            recording_url = data.get('RecordingUrl')
            
            if recording_sid and recording_url:
                print(f"V3.2.5: Found existing recording for CallSid {call_sid}")
                return {
                    'recording_sid': recording_sid,
                    'recording_url': recording_url,
                    'recording_duration': data.get('RecordingDuration', 0)
                }
        
        print(f"V3.2.5: No recording found yet for CallSid {call_sid}")
        return None
        
    except Exception as e:
        print(f"Error retrieving recording by CallSid: {e}")
        return None

# ============================================================================
# RECORDING METADATA UPDATE
# ============================================================================

def update_call_recording_metadata(call_sid, recording_sid, recording_url, recording_duration, base_url=None):
    """
    Update existing call log with recording metadata
    
    Args:
        call_sid: Twilio Call SID (used to locate existing log)
        recording_sid: Unique recording identifier
        recording_url: URL to access/download the recording (from Twilio)
        recording_duration: Length of recording in seconds
        base_url: Base URL of the Flask app (optional, for proxy URL generation)
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    if not db:
        print("Firestore not available, skipping recording metadata update")
        return False
    
    try:
        # Query for call log entry with matching CallSid
        call_logs_ref = db.collection('call_logs')
        query = call_logs_ref.where('CallSid', '==', call_sid).limit(1)
        docs = query.stream()
        
        # Create proxy URL that points to OUR endpoint (authentication-free playback)
        # Instead of storing Twilio's URL, store our proxy endpoint URL
        if base_url:
            media_url = f"{base_url}/play_recording/{recording_sid}"
        else:
            # Fallback to localhost if base_url not provided
            media_url = f"http://localhost:5000/play_recording/{recording_sid}"
        
        # Update the first matching document
        updated = False
        for doc in docs:
            doc.reference.update({
                'RecordingSid': recording_sid,
                'RecordingUrl': media_url,  # Now points to OUR proxy endpoint
                'RecordingDuration': recording_duration,
                'RecordingTimestamp': firestore.SERVER_TIMESTAMP
            })
            print(f"Updated call log {doc.id} with recording metadata for CallSid {call_sid}")
            print(f"Proxy URL: {media_url}")
            updated = True
            break
        
        if not updated:
            print(f"WARNING: No call log found for CallSid {call_sid}")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error updating call log with recording metadata: {e}")
        return False