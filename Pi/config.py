# config.py
"""Configuration settings for the Microsoft Graph email monitor."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Azure AD and Microsoft Graph API settings
CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USER_EMAIL = os.getenv("USER_EMAIL")  # Email of the user whose mailbox to monitor
SCOPES = ["https://graph.microsoft.com/.default"]  # Use .default for client credentials flow

# Webhook settings
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "localhost")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "5000"))
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL")  # e.g., "https://your-ngrok-url.ngrok.io/webhook"
CLIENT_STATE = os.getenv("CLIENT_STATE", "YourSecretClientState")  # Secret value to validate notifications

# File paths
TOKEN_CACHE_FILE = os.getenv("TOKEN_CACHE_FILE", "token_cache.bin")
SUBSCRIPTION_INFO_FILE = os.getenv("SUBSCRIPTION_INFO_FILE", "subscription_info.json")
