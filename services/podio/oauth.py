"""
Podio OAuth Service - Token Management

Handles OAuth token refresh and credential validation for Podio API access.
This module provides the foundation for all Podio API operations.

Business Justification:
    Pillar 1 (Compliance): OAuth logic isolation enables security audits 
                           without reviewing 800+ lines of service code
    Pillar 5 (Scalability): Foundation module for subsequent Podio service extractions

Dependencies:
    - config: PODIO_CLIENT_ID, PODIO_CLIENT_SECRET, PODIO_USERNAME, PODIO_PASSWORD
    - requests: HTTP client for OAuth token endpoint

Used By:
    - All other Podio service modules (item_service, intelligence, task_service)
    - podio_service.py (backward compatibility)
"""

import requests
from config import (
    PODIO_CLIENT_ID,
    PODIO_CLIENT_SECRET,
    PODIO_USERNAME,
    PODIO_PASSWORD,
    podio_access_token
)

# Module-level token cache
# Initialized from config's podio_access_token (typically None at startup)
_podio_token = podio_access_token


def refresh_podio_token():
    """
    Get or refresh Podio OAuth access token.
    
    Uses the Password Grant flow with stored credentials to obtain
    an access token from Podio's OAuth endpoint.
    
    Returns:
        str: Access token if authentication succeeds
        None: If credentials are missing or authentication fails
        
    Side Effects:
        Updates module-level _podio_token cache
        
    Security Notes:
        - All credential values are masked in log output
        - Failed authentication attempts are logged with error details
        - Token is cached in memory (not persisted to disk)
    """
    global _podio_token
    
    # Enhanced credential diagnostics
    print("="*50)
    print("PODIO TOKEN REFRESH ATTEMPT")
    print(f"CLIENT_ID present: {bool(PODIO_CLIENT_ID)} (length: {len(PODIO_CLIENT_ID) if PODIO_CLIENT_ID else 0})")
    print(f"CLIENT_SECRET present: {bool(PODIO_CLIENT_SECRET)} (length: {len(PODIO_CLIENT_SECRET) if PODIO_CLIENT_SECRET else 0})")
    print(f"USERNAME present: {bool(PODIO_USERNAME)} (value: {PODIO_USERNAME[:3] + '***' if PODIO_USERNAME and len(PODIO_USERNAME) > 3 else 'None'})")
    print(f"PASSWORD present: {bool(PODIO_PASSWORD)} (length: {len(PODIO_PASSWORD) if PODIO_PASSWORD else 0})")
    print("="*50)
    
    if not all([PODIO_CLIENT_ID, PODIO_CLIENT_SECRET, PODIO_USERNAME, PODIO_PASSWORD]):
        print("❌ CRITICAL: Podio credentials not fully configured. Podio integration will be disabled.")
        print(f"Missing credentials:")
        if not PODIO_CLIENT_ID:
            print("  - PODIO_CLIENT_ID")
        if not PODIO_CLIENT_SECRET:
            print("  - PODIO_CLIENT_SECRET")
        if not PODIO_USERNAME:
            print("  - PODIO_USERNAME")
        if not PODIO_PASSWORD:
            print("  - PODIO_PASSWORD")
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
            _podio_token = token_data.get('access_token')
            print("Podio token obtained successfully.")
            return _podio_token
        else:
            print(f"="*50)
            print(f"ERROR getting Podio token: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response text: {response.text}")
            print(f"="*50)
            return None
    except Exception as e:
        print(f"Error initializing Podio authentication: {e}")
        return None


def get_token():
    """
    Get current token, refreshing if needed.
    
    Convenience wrapper around refresh_podio_token() for cleaner API.
    Always attempts to refresh to ensure token validity.
    
    Returns:
        str: Valid access token, or None if authentication fails
    """
    return refresh_podio_token()