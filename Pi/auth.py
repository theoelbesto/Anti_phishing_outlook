# auth.py
"""Authentication module for Microsoft Graph API."""

import os
import msal
from msal_extensions import PersistedTokenCache, FilePersistence
from config import CLIENT_ID, TENANT_ID, CLIENT_SECRET, SCOPES, TOKEN_CACHE_FILE

def get_access_token(force_refresh=False):
    """
    Acquire an access token for Microsoft Graph API using Confidential Client Application.
    
    Args:
        force_refresh (bool, optional): Force token refresh even if a cached token exists. Defaults to False.
    
    Returns:
        str: Access token or None if acquisition fails
    """
    # Set up token cache
    cache_file_path = os.path.abspath(TOKEN_CACHE_FILE)
    cache_dir = os.path.dirname(cache_file_path)
    
    # Ensure cache directory exists
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    persistence = FilePersistence(cache_file_path)
    cache = PersistedTokenCache(persistence)

    # Create the MSAL Confidential Client Application with token cache
    try:
        app = msal.ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            token_cache=cache
        )
        
        # Attempt token acquisition
        if force_refresh:
            # Force a new token by clearing the cache
            cache.clear()
        
        result = app.acquire_token_for_client(scopes=SCOPES)
        
        if "access_token" in result:
            print("Token acquired successfully.")
            return result['access_token']
        else:
            # Detailed error logging
            error_details = {
                "error": result.get('error', 'Unknown error'),
                "error_description": result.get('error_description', 'No description'),
                "error_codes": result.get('error_codes', [])
            }
            
            print("Failed to acquire token.")
            for key, value in error_details.items():
                print(f"{key.capitalize()}: {value}")
            
            return None
    
    except Exception as e:
        print(f"Unexpected error during token acquisition: {e}")
        import traceback
        traceback.print_exc()  # Print full stack trace for debugging
        return None
