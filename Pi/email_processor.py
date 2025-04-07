# email_processor.py
"""Process and handle email notifications and content retrieval."""

import requests
from auth import get_access_token
from config import USER_EMAIL  # Ensure this is configured in your config

def get_email_content(message_id):
    """
    Retrieve an email's content using the Microsoft Graph API.
    Returns the message object or None if retrieval fails.
    """
    access_token = get_access_token()
    if not access_token:
        print("Failed to acquire token for message retrieval.")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"https://graph.microsoft.com/v1.0/me/messages/{message_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve message {message_id}: {response.status_code}")
        print(response.text)
        return None

def process_new_email(message_id):
    """
    Process a newly received email.
    Returns the message object or None if processing fails.
    """
    message = get_email_content(message_id)
    if not message:
        return None
    
    # Extract email details
    sender = message.get('sender', {}).get('emailAddress', {}).get('address', 'Unknown')
    subject = message.get('subject', 'No subject')
    received_time = message.get('receivedDateTime', 'Unknown time')
    body_content = message.get('body', {}).get('content', 'No content')
    is_html = message.get('body', {}).get('contentType', '') == 'html'
    
    # Display email information
    print(f"\n===== NEW EMAIL =====")
    print(f"From: {sender}")
    print(f"Subject: {subject}")
    print(f"Received: {received_time}")
    print(f"Body Preview: {body_content[:100]}..." if len(body_content) > 100 else f"Body: {body_content}")
    print("=====================\n")
    
    # Here you can implement additional processing:
    # - Store the email in a database
    # - Run AI/ML analysis on the content
    # - Forward to another system
    # - Send notifications
    
    return message

def get_emails(access_token, limit=10):
    """
    Retrieve recent emails from the inbox using application permissions.
    
    Args:
        access_token (str): Access token for authentication
        limit (int, optional): Maximum number of emails to retrieve. Defaults to 10.
    
    Returns:
        list: List of email messages or None if retrieval fails
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Use specific user email instead of /me
    # Requires Mail.Read application permission
    response = requests.get(
        f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}/mailFolders/inbox/messages?$top={limit}&$orderby=receivedDateTime desc&$select=sender,subject,receivedDateTime,bodyPreview",
        headers=headers
    )
    print(response.status_code)
    if response.status_code == 200:
        messages = response.json().get('value', [])
        print(f"Retrieved {len(messages)} recent emails.")
        return messages
    else:
        print(f"Failed to retrieve messages: {response.status_code}")
        print(f"Response: {response.text}")
        return None
