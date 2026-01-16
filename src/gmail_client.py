import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

class GmailClient:
    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        self.creds = None
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.authenticate()
        self.service = build('gmail', 'v1', credentials=self.creds)

    def authenticate(self):
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"'{self.credentials_path}' not found. Please download it from Google Cloud Console.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())

    def search_messages(self, query):
        """Search for messages matching the query."""
        try:
            results = self.service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            return messages
        except Exception as e:
            print(f"An error occurred while searching messages: {e}")
            return []

    def get_message_content(self, msg_id):
        """Get the content of a specific message."""
        try:
            message = self.service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            payload = message.get('payload', {})
            parts = payload.get('parts', [])
            data = None
            
            if not parts:
                # If there are no parts, the body might be in the payload directly
                data = payload.get('body', {}).get('data')
            else:
                for part in parts:
                    if part['mimeType'] == 'text/html':
                        data = part['body']['data']
                        break
            
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
            return None
        except Exception as e:
            print(f"An error occurred getting message content: {e}")
            return None

    def send_email(self, to, subject, html_content):
        """Send an HTML email."""
        try:
            message = MIMEText(html_content, 'html')
            message['to'] = to
            message['subject'] = subject
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            body = {'raw': raw_message}
            
            message = self.service.users().messages().send(userId='me', body=body).execute()
            print(f"Email sent! Message Id: {message['id']}")
            return message
        except Exception as e:
            print(f"An error occurred sending email: {e}")
            return None
