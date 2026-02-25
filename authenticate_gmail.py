"""
Gmail OAuth 2.0 Authentication Script
Run this once to authenticate and generate Gmail API tokens

Usage: python authenticate_gmail.py
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env.gold')

def authenticate_gmail():
    """Run Gmail OAuth 2.0 authentication flow"""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        # Configuration
        scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.readonly'
        ]
        credentials_file = 'client_secret_725259256203-a14h8ovoi908q7nv5sigh8ak6456gsnl.apps.googleusercontent.com.json'
        token_file = os.getenv('GMAIL_TOKEN_FILE', 'tokens/gmail_token.json')

        # Check if credentials file exists
        if not os.path.exists(credentials_file):
            print(f"❌ Error: Credentials file not found: {credentials_file}")
            print("\n📋 Setup Instructions:")
            print("1. Go to https://console.cloud.google.com/apis/credentials")
            print("2. Create or select your project")
            print("3. Enable Gmail API")
            print("4. Create OAuth 2.0 Client ID credentials (Desktop app)")
            print("5. Download the credentials JSON file")
            print("6. Save it as the client_secret_*.json file in this directory")
            return False

        creds = None

        # Load existing token if available
        if os.path.exists(token_file):
            print(f"📄 Found existing token file: {token_file}")
            creds = Credentials.from_authorized_user_file(token_file, scopes)

        # Check if credentials are valid
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired token...")
                try:
                    creds.refresh(Request())
                    print("✅ Token refreshed successfully!")
                except Exception as e:
                    print(f"❌ Token refresh failed: {str(e)}")
                    creds = None

            if not creds:
                print("\n🔐 Starting OAuth authentication flow...")
                print("1. A browser window will open")
                print("2. Sign in with your Google account")
                print("3. Grant permissions to the application")
                print("4. You will be redirected to a success page")

                # Run OAuth flow
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
                creds = flow.run_local_server(port=8080, open_browser=True)

                print("✅ Authentication successful!")

        # Save credentials for future use
        token_dir = Path(token_file).parent
        token_dir.mkdir(exist_ok=True)

        with open(token_file, 'w') as token:
            token.write(creds.to_json())

        print(f"💾 Token saved to: {token_file}")
        print("\n✅ Gmail authentication completed successfully!")
        print("\n📝 Next steps:")
        print("1. The MCP Server can now send emails via Gmail API")
        print("2. Token will be automatically refreshed when needed")
        print("3. Run the MCP Server: python MCP_Server_Gold.py")

        return True

    except ImportError as e:
        print(f"❌ Required libraries not installed: {str(e)}")
        print("\n📦 Install required packages:")
        print("   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return False

    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  GMAIL OAUTH 2.0 AUTHENTICATION")
    print("  Gold Tier AI Employee System")
    print("=" * 60)
    print()

    success = authenticate_gmail()

    if success:
        print("\n" + "=" * 60)
        print("  ✅ AUTHENTICATION COMPLETE")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("  ❌ AUTHENTICATION FAILED")
        print("=" * 60)
