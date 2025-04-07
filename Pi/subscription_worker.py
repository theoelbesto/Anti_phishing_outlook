# subscription_worker.py
"""Background worker to handle subscription renewal and maintenance."""

import time
import os
import json
import datetime
import threading
from config import SUBSCRIPTION_INFO_FILE
from subscription import renew_subscription, create_subscription

def subscription_renewal_worker():
    """
    Background worker to periodically renew the subscription.
    """
    print("Starting subscription renewal worker...")
    
    while True:
        try:
            # Check if we have a subscription to renew
            if os.path.exists(SUBSCRIPTION_INFO_FILE):
                with open(SUBSCRIPTION_INFO_FILE, "r") as f:
                    subscription = json.load(f)
                
                # Parse expiration time
                expiration = datetime.datetime.fromisoformat(subscription['expirationDateTime'].replace('Z', '+00:00'))
                
                # If expiration is within 12 hours, renew the subscription
                if (expiration - datetime.datetime.now(datetime.timezone.utc)).total_seconds() < 12 * 3600:
                    print("Subscription expiring soon. Renewing...")
                    renewed = renew_subscription(subscription['id'])
                    if not renewed:
                        print("Renewal failed. Creating new subscription...")
                        create_subscription()
            else:
                # Create a new subscription if none exists
                print("No subscription found. Creating new subscription...")
                create_subscription()
                
        except Exception as e:
            print(f"Error in renewal worker: {e}")
        
        # Sleep for 6 hours before checking again
        print("Renewal worker sleeping for 6 hours...")
        time.sleep(6 * 3600)  # 6 hours

def start_renewal_worker():
    """
    Start the subscription renewal worker in a background thread.
    """
    thread = threading.Thread(target=subscription_renewal_worker)
    thread.daemon = True
    thread.start()
    return thread

if __name__ == '__main__':
    # Start the worker directly if this script is run directly
    subscription_renewal_worker()
