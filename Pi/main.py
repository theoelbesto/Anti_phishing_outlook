# main.py
"""
Microsoft Graph Real-Time Email Monitor
Main application entry point that orchestrates the email monitoring system.
"""
import requests
import os
import time
import sys
import json
import signal
import threading
from config import USER_EMAIL, NOTIFICATION_URL, SUBSCRIPTION_INFO_FILE
from auth import get_access_token
from webhook_server import start_webhook_server
from subscription_worker import start_renewal_worker
from subscription import create_subscription, get_current_subscription
from email_processor import get_emails

def check_configuration():
    """Check if all required configuration is set."""
    from config import CLIENT_ID, TENANT_ID, NOTIFICATION_URL
    
    missing = []
    if not CLIENT_ID:
        missing.append("CLIENT_ID")
    if not TENANT_ID:
        missing.append("TENANT_ID")
    if not NOTIFICATION_URL:
        missing.append("NOTIFICATION_URL")
    
    if missing:
        print(f"Error: Missing required configuration: {', '.join(missing)}")
        print("Please set these values in your environment or .env file.")
        return False
    
    return True

def signal_handler(sig, frame):
    """Handle Ctrl+C to exit gracefully."""
    print("\nStopping Email Monitor...")
    sys.exit(0)

def display_emails(emails, show_details=False):
    """
    Display emails with optional detailed view.
    
    Args:
        emails (list): List of email messages
        show_details (bool): Whether to show full email details
    """
    if not emails:
        print("No emails found.")
        return
    
    print("\n===== INBOX EMAILS =====")
    for i, email in enumerate(emails, 1):
        sender = email.get('sender', {}).get('emailAddress', {}).get('address', 'Unknown')
        subject = email.get('subject', 'No subject')
        received = email.get('receivedDateTime', 'Unknown time')
        
        print(f"{i}. From: {sender}")
        print(f"   Subject: {subject}")
        print(f"   Received: {received}")
        
        if show_details:
            body_preview = email.get('bodyPreview', 'No preview')
            print(f"   Preview: {body_preview[:200]}...")
            print("   " + "-"*50)

def main():
    """Main function to initialize and run the email monitoring system."""
    print("Microsoft Graph Real-Time Email Monitor")
    print("======================================")
    
    # Check configuration
    if not check_configuration():
        return
    
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Authenticate and get token
    print("\nAuthenticating with Microsoft Graph...")
    token = get_access_token()
    
    if not token:
        print("Failed to acquire token. Exiting.")
        return
    
    print("Authentication successful!")
    
    # Retrieve and display recent emails
    print("\nRetrieving recent emails from inbox...")
    recent_emails = get_emails(token, 10)  # Retrieve top 10 emails
    display_emails(recent_emails)
    if recent_emails:
        display_emails(recent_emails)
        
        # Optional: Interactive email viewing
        while True:
            try:
                choice = input("\nEnter email number to view details (or 'q' to quit): ")
                if choice.lower() == 'q':
                    break
                
                index = int(choice) - 1
                if 0 <= index < len(recent_emails):
                    selected_email = recent_emails[index]
                    print("\n===== FULL EMAIL DETAILS =====")
                    print(f"From: {selected_email.get('sender', {}).get('emailAddress', {}).get('address', 'Unknown')}")
                    print(f"Subject: {selected_email.get('subject', 'No subject')}")
                    print(f"Received: {selected_email.get('receivedDateTime', 'Unknown time')}")
                    print(f"Body Preview: {selected_email.get('bodyPreview', 'No preview')}")
                    print("===============================")
                else:
                    print("Invalid email number.")
            except ValueError:
                print("Please enter a valid number or 'q'.")
    
    # Optional: Subscription and webhook setup can remain commented out or removed
    # if not needed for simple inbox viewing
    print("\nEmail retrieval complete. Press Ctrl+C to exit.")

if __name__ == "__main__":
    main()
