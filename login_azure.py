from azure.identity import ClientSecretCredential, DeviceCodeCredential
from msgraph.graph_service_client import GraphServiceClient
from dotenv import load_dotenv
import os
import json
import asyncio


def application_registration(tenant_id, client_id, client_secret,scopes):
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )

    # Create the Graph client
    graph_client = GraphServiceClient(credential, scopes)
    print("Graph client created successfully.")
    return graph_client

def delegated_registration(tenant_id, client_id, scopes):
    credential = DeviceCodeCredential(
        tenant_id=tenant_id,
        client_id=client_id,
    )

    # Create the Graph client
    graph_client = GraphServiceClient(credential, scopes)
    print("Graph client created successfully.")
    return graph_client

async def main():
    load_dotenv()

    tenant_id = os.getenv('TENANT_ID')
    client_id = os.getenv('APPLICATION_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    user_id = os.getenv('USER_ID')

    scopes = ['Mail.Read', 'Mail.ReadWrite', 'Mail.Send']
    # graph_client = application_registration(tenant_id, client_id, client_secret, scopes)
    graph_client = delegated_registration(tenant_id, client_id, scopes)
    emails = await graph_client.me.messages.get()
    print(emails)

asyncio.run(main())