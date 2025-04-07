# Lesson: Retrieve Emails (all emails)
import os
import httpx
from dotenv import load_dotenv
from ms_graph import get_access_token, MS_GRAPH_BASE_URL, EMAIL_ADDRESS
import requests

def validate_token(access_token):
    """
    Validates the access token by making a test request to Microsoft Graph API.
    Returns True if the token is valid, False otherwise.
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Make a simple request to get user profile
    response = requests.get(f'{MS_GRAPH_BASE_URL}/me', headers=headers)
    return response.status_code == 200


def main(access_token):  # Modified to accept access_token as parameter
    endpoint = f'{MS_GRAPH_BASE_URL}/me/messages'
    print(f'Endpoint: {endpoint}')

    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        params = {
            '$top': 10,
            '$select': 'subject,toRecipients,from,isRead,receivedDateTime,isDraft',
            '$orderby': 'receivedDateTime desc'
        }

        print("Making request to Graph API...")
        response = httpx.get(endpoint, headers=headers, params=params)
        
        print(f'Status Code: {response.status_code}')
        
        if response.status_code != 200:
            print(f'Response Headers: {response.headers}')
            print(f'Response Body: {response.text}')
            raise Exception(f'Failed to retrieve emails: {response.status_code}')

        json_response = response.json()  # Fix indentation - this was inside the if block before

        for mail_message in json_response.get('value', []):
            if mail_message.get('isDraft'):
                print(f'Subject: {mail_message["subject"]}')
                print(f'To: {mail_message["toRecipients"]}')
                print(f'Is Read: {mail_message["isRead"]}')
                print(f'Received Date Time: {mail_message["receivedDateTime"]}')
            else:
                print(f'Subject: {mail_message["subject"]}')
                print(f'To: {mail_message["toRecipients"]}')
                print(f'From: {mail_message["from"]["emailAddress"]["name"]}, ({mail_message["from"]["emailAddress"]["address"]})')
                print(f'Is Read: {mail_message["isRead"]}')
                print(f'Received Date Time: {mail_message["receivedDateTime"]}')
            print('-' * 150)

    except httpx.HTTPStatusError as e:
        print(f'HTTP Error: {e}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    load_dotenv()
    APPLICATION_ID = os.getenv('APPLICATION_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    SCOPES = ['User.Read','Mail.Read', 'Mail.ReadWrite', 'Mail.Send']

    try:
        access_token = get_access_token(APPLICATION_ID, CLIENT_SECRET, SCOPES)
        if validate_token(access_token):
            print("Token is valid")
            main(access_token)  # Pass the validated token to main
        else:
            print("Token validation failed")
    except Exception as e:
        print(f'Error: {e}')