import os
import webbrowser
import msal
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

load_dotenv()
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
MS_GRAPH_BASE_URL = 'https://graph.microsoft.com/v1.0'

def get_access_token(application_id, client_secret, scopes):
    client = msal.ConfidentialClientApplication(
        client_id=application_id,
        client_credential=client_secret,
        authority=f'https://login.microsoftonline.com/{os.getenv("TENANT_ID")}/'
    )

    # Check if there is a refresh token stored
    refresh_token = None
    if os.path.exists('refresh_token.txt'):
        with open('refresh_token.txt', 'r') as file:
            refresh_token = file.read().strip()

    if refresh_token:
        # Try to acquire a new access token using the refresh token
        token_response = client.acquire_token_by_refresh_token(refresh_token, scopes=scopes)
    else:
        # No refresh token, proceed with the authorization code flow
        auth_request_url = client.get_authorization_request_url(
            scopes,
            redirect_uri="http://localhost:8080"
        )
        webbrowser.open(auth_request_url)
        # Update the prompt to be more specific
        print("Please paste the entire redirect URL you received:")
        redirect_url = input()
        
        # Extract the authorization code from the URL
        parsed_url = urlparse(redirect_url)
        authorization_code = parse_qs(parsed_url.query)['code'][0]

        if not authorization_code:
            raise ValueError("Authorization code is empty")

        token_response = client.acquire_token_by_authorization_code(
            code=authorization_code,
            scopes=scopes,
            redirect_uri="http://localhost:8080"
        )

    if 'access_token' in token_response:
        # Store the refresh token securely
        if 'refresh_token' in token_response:
            with open('refresh_token.txt', 'w') as file:
                file.write(token_response['refresh_token'])

        return token_response['access_token']
    else:
        raise Exception('Failed to acquire access token: ' + str(token_response))

if __name__ == "__main__":
    load_dotenv()
    APPLICATION_ID = os.getenv('APPLICATION_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    SCOPES = ['User.Read','Mail.Read', 'Mail.ReadWrite', 'Mail.Send']

    try:
        access_token = get_access_token(APPLICATION_ID, CLIENT_SECRET, SCOPES)
        headers = {
            'Authorization': 'Bearer ' + access_token
        }
        print(headers)
    except Exception as e:
        print(f'Error: {e}')