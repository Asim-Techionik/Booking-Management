import os
import json
import webbrowser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from django.conf import settings

# 🔹 Set Paths
CLIENT_SECRET_FILE = os.getenv('CLIENT_SECRET_FILE', r'C:\Users\Asim99x\Desktop\Booking-Management-main\gmail\client_secret.json')  # Update path if needed
TOKEN_PATH = os.getenv('TOKEN_PATH', r'C:\Users\Asim99x\Desktop\Booking-Management-main\gmail\token.json') # delete the old token.json before running this script other wise it wont work

# 🔹 Define Gmail API Scope
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def generate_token():
    """Authenticate with Google and generate token.json"""
    creds = None

    # Check if token already exists
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If there are no valid credentials, ask user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh existing token
        else:
            # Launch Google login flow
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save new credentials to token.json
        with open(TOKEN_PATH, 'w') as token_file:
            token_file.write(creds.to_json())

        print("✅ Token generated and saved to:", TOKEN_PATH)
    else:
        print("✅ Existing token is still valid.")

if __name__ == "__main__":
    generate_token()

