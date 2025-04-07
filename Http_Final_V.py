import requests
import webbrowser
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
import os

load_dotenv()

tenant_id = os.getenv('TENANT_ID')
client_id = os.getenv('APPLICATION_ID')
redirect_uri = 'http://localhost:8080'
client_secret =  os.getenv('CLIENT_SECRET')
scopes = ["User.Read", "Mail.Read"] 

def get_auth_url():
    auth_url = (
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize?"
        f"client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&response_mode=query"
        f"&scope={' '.join([f'https://graph.microsoft.com/{scope}' for scope in scopes])}"
        f"&state=12345"
    )
    return auth_url

def get_auth_code():
    print("Opening browser for authentication...")
    auth_url = get_auth_url()
    webbrowser.open(auth_url)

    print(f"After authenticating, you'll be redirected to: {redirect_uri}")
    print("Please paste the full redirect URL here:")
    redirect_response = input()
    
    parsed = urlparse(redirect_response)
    query_params = parse_qs(parsed.query)
    return query_params['code'][0]

# Step 3: Exchange authorization code for tokens
def get_tokens(auth_code):
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'client_id': client_id,
        'scope': ' '.join([f'https://graph.microsoft.com/{scope}' for scope in scopes]),
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'client_secret': client_secret
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    return response.json()

def call_graph_api(access_token, endpoint="me"):
    graph_url = f"https://graph.microsoft.com/v1.0/{endpoint}"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    if requests.get(graph_url, headers=headers).status_code != 200:
        print("Invalid access token or insufficient permissions.")
        return None
    response = requests.get(graph_url, headers=headers)
    return response.json()

if __name__ == "__main__":
    auth_code = get_auth_code()
    
    tokens = get_tokens(auth_code)
    access_token = tokens['access_token']
    
    print("\nGetting user info from Microsoft Graph...")
    user_info = call_graph_api(access_token)
    print("Answer", user_info)
