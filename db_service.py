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