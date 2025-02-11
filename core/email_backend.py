import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from django.conf import settings


def refresh_token_if_expired():
    """Refresh OAuth2 token if expired."""
    creds = Credentials.from_authorized_user_file(settings.TOKEN_PATH)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(settings.TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())
        print("🔄 Token refreshed successfully!")


def send_gmail_api(subject, message, to_email):
    """Send email using Gmail API with automatic token refresh."""
    refresh_token_if_expired()  # Ensure token is fresh before sending

    creds = Credentials.from_authorized_user_file(settings.TOKEN_PATH)

    try:
        service = build("gmail", "v1", credentials=creds)

        mime_message = MIMEText(message)
        mime_message["to"] = to_email
        mime_message["subject"] = subject
        raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

        message = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )

        print(f"✅ Email sent successfully! Message ID: {message['id']}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False