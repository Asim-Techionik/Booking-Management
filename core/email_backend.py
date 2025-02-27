import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from django.conf import settings
from google.auth.exceptions import RefreshError
import django


# def refresh_token_if_expired():
#     """Refresh OAuth2 token if expired."""
#     creds = Credentials.from_authorized_user_file(settings.TOKEN_PATH)
#
#     if creds.expired and creds.refresh_token:
#         creds.refresh(Request())
#         with open(settings.TOKEN_PATH, "w") as token_file:
#             token_file.write(creds.to_json())
#         print("🔄 Token refreshed successfully!")


#

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'building.settings')  # Replace 'your_project_name' with your actual project name


# def refresh_token_if_expired():
#     """Refresh OAuth2 token if expired."""
#     creds = None
#
#     # Try to load the existing credentials
#     try:
#         creds = Credentials.from_authorized_user_file(settings.TOKEN_PATH)
#     except Exception as e:
#         print(f"❌ Failed to load credentials: {e}")
#         return False
#
#     if creds and creds.expired and creds.refresh_token:
#         try:
#             creds.refresh(Request())  # Try to refresh the token
#             with open(settings.TOKEN_PATH, "w") as token_file:
#                 token_file.write(creds.to_json())
#             print("🔄 Token refreshed successfully!")
#             return True
#         except RefreshError:
#             print("❌ Failed to refresh token. Token may be revoked or expired.")
#             return False
#     else:
#         print("❌ Token is invalid or expired. Please re-authenticate.")
#         return False

def refresh_token_if_expired():
    """Always refresh OAuth2 token."""
    creds = None

    # Try to load the existing credentials
    try:
        creds = Credentials.from_authorized_user_file(settings.TOKEN_PATH)
    except Exception as e:
        print(f"❌ Failed to load credentials: {e}")
        return False

    # Attempt to refresh the token every time it's called
    try:
        creds.refresh(Request())  # Refresh the token unconditionally
        with open(settings.TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())
        print("🔄 Token refreshed successfully!")
        return True
    except RefreshError:
        print("❌ Failed to refresh token. Token may be revoked or expired.")
        return False


def send_gmail_api(subject, message, to_email):
    """Send email using Gmail API with automatic token refresh."""
    refresh_token_if_expired()  # Ensure token is fresh before sending

    creds = Credentials.from_authorized_user_file(settings.TOKEN_PATH)

    try:
        service = build("gmail", "v1", credentials=creds)

        # mime_message = MIMEText(message)
        mime_message = MIMEText(message, "html")
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