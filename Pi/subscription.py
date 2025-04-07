# subscription.py
"""Subscription management for Microsoft Graph change notifications."""

import json
import datetime
import requests
import os
from config import CLIENT_STATE, NOTIFICATION_URL, SUBSCRIPTION_INFO_FILE, USER_EMAIL
from auth import get_access_token

def create_subscription():
    """
    Create a subscription for new email notifications.
    Returns the subscription object or None if creation fails.
    """
    # Get a fresh access token
    access_token = get_access_token()
    if not access_token:
        print("Failed to acquire token for subscription creation.")
        return None
    
    # Calculate expiration time (maximum is 4230 minutes or ~3 days)
    expiration_date = datetime.datetime.utcnow() + datetime.timedelta(days=2)
    expiration_string = expiration_date.isoformat() + "Z"
    
    # Prepare the subscription request
    subscription_data = {
        "changeType": "created",
        "notificationUrl": NOTIFICATION_URL,
        "resource": f"users/{USER_EMAIL}/mailFolders('Inbox')/messages",
        "expirationDateTime": expiration_string,
        "clientState": CLIENT_STATE
    }
    
    # Send the request to Microsoft Graph
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        "https://graph.microsoft.com/v1.0/subscriptions",
        headers=headers,
        json=subscription_data
    )
    
    if response.status_code == 201:
        subscription = response.json()
        print(f"Subscription created successfully. ID: {subscription['id']}")
        print(f"Expires: {subscription['expirationDateTime']}")
        
        # Save subscription details
        with open(SUBSCRIPTION_INFO_FILE, 'w') as f:
            json.dump(subscription, f, indent=4)
        
        return subscription
    else:
        print(f"Failed to create subscription. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def renew_subscription(subscription_id):
    """
    Renew an existing subscription.
    Returns the updated subscription object or None if renewal fails.
    """
    # Get a fresh access token
    access_token = get_access_token()
    if not access_token:
        print("Failed to acquire token for subscription renewal.")
        return None
    
    # Calculate new expiration time (maximum is 4230 minutes or ~3 days)
    expiration_date = datetime.datetime.utcnow() + datetime.timedelta(days=2)
    expiration_string = expiration_date.isoformat() + "Z"
    
    # Prepare the renewal request
    renewal_data = {
        "expirationDateTime": expiration_string
    }
    
    # Send the request to Microsoft Graph
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.patch(
        f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}",
        headers=headers,
        json=renewal_data
    )
    
    if response.status_code == 200:
        subscription = response.json()
        print(f"Subscription renewed successfully. New expiration: {subscription['expirationDateTime']}")
        
        # Update the saved subscription info
        with open(SUBSCRIPTION_INFO_FILE, "w") as f:
            json.dump(subscription, f)
        
        return subscription
    else:
        print(f"Failed to renew subscription: {response.status_code}")
        print(response.text)
        return None

def delete_subscription(subscription_id):
    """
    Delete an existing subscription.
    Returns True if deletion was successful, False otherwise.
    """
    # Get a fresh access token
    access_token = get_access_token()
    if not access_token:
        print("Failed to acquire token for subscription deletion.")
        return False
    
    # Send the request to Microsoft Graph
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.delete(
        f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}",
        headers=headers
    )
    
    if response.status_code == 204:
        print(f"Subscription {subscription_id} deleted successfully.")
        
        # Remove the subscription info file if it exists
        if os.path.exists(SUBSCRIPTION_INFO_FILE):
            os.remove(SUBSCRIPTION_INFO_FILE)
        
        return True
    else:
        print(f"Failed to delete subscription: {response.status_code}")
        print(response.text)
        return False

def get_current_subscription():
    """
    Retrieve the current active subscription if it exists.
    Returns the subscription object or None if no active subscription is found.
    """
    # Check if subscription info file exists
    if not os.path.exists(SUBSCRIPTION_INFO_FILE):
        return None
    
    with open(SUBSCRIPTION_INFO_FILE, 'r') as f:
        try:
            subscription = json.load(f)
            
            # Check if subscription is still valid
            expiration_time = datetime.datetime.fromisoformat(subscription['expirationDateTime'].rstrip('Z'))
            if expiration_time > datetime.datetime.utcnow():
                return subscription
        except (json.JSONDecodeError, KeyError):
            pass
    
    return None
