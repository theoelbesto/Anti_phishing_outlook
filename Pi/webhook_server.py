# webhook_server.py
"""Webhook server to receive Microsoft Graph change notifications."""

import json
import threading
from flask import Flask, request, Response
from config import CLIENT_STATE, WEBHOOK_HOST, WEBHOOK_PORT
from email_processor import process_new_email

# Create Flask app
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle incoming webhook notifications from Microsoft Graph.
    """
    # Check if this is a validation request
    validation_token = request.args.get('validationToken')
    if validation_token:
        print(f"Received validation request with token: {validation_token}")
        return Response(validation_token, mimetype='text/plain')
    
    # Process the notification
    data = request.get_json()
    print("Notification received:", json.dumps(data, indent=2))
    
    # Process each notification in the data
    for notification in data.get('value', []):
        # Verify the clientState for security
        client_state = notification.get('clientState')
        if client_state != CLIENT_STATE:
            print("Invalid client state! Possible security issue.")
            continue
        
        # Extract resource data
        resource = notification.get('resource')
        change_type = notification.get('changeType')
        
        if change_type == 'created' and 'messages' in resource:
            # A new email has arrived
            message_id = notification.get('resourceData', {}).get('id')
            if message_id:
                # Process in a separate thread to avoid blocking the response
                threading.Thread(target=process_new_email, args=(message_id,)).start()
    
    # Return 202 Accepted status to acknowledge receipt
    return Response(status=202)

def start_webhook_server():
    """
    Start the Flask webhook server.
    """
    print(f"Starting webhook server on {WEBHOOK_HOST}:{WEBHOOK_PORT}...")
    app.run(host=WEBHOOK_HOST, port=WEBHOOK_PORT, ssl_context='adhoc', debug=False)

if __name__ == '__main__':
    start_webhook_server()
