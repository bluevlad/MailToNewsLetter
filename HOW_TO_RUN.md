# How to Run the Medium Auto-Newsletter

## 1. Prerequisites (사전 준비)

### A. Google Cloud Project Setup (Gmail API)
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the **Gmail API**.
4. Go to **APIs & Services > Credentials**.
5. Click **Create Credentials > OAuth client ID**.
   - Application type: **Desktop app**.
6. Download the JSON file and save it as `credentials.json` in this project folder (`c:\Gemini\MailToNesLetter\credentials.json`).
7. **Important**: Since this is a testing app, go to **OAuth consent screen** and add your email as a **Test User**.

### B. Gemini API Key
1. Get your API Key from [Google AI Studio](https://aistudio.google.com/).
2. Set it as an environment variable:
   ```powershell
   $env:GOOGLE_API_KEY="your_api_key_here"
   ```

## 2. Installation

Install the required Python packages:

```powershell
pip install -r requirements.txt
```

## 3. Configuration

Edit `config/settings.yaml` if needed:
- Update `keywords` to match your interests.
- Ensure `gemini.model` is set to `gemini-3.0-pro`.

## 4. Usage

Run the main script:

```powershell
python src/main.py
```

### What happens next?
1. The script will open a browser window for you to log in to your Google account (for Gmail access).
2. It will search your Gmail for the latest "Medium Daily Digest".
3. It extracts articles, sends them to Gemini to find the best matches for your keywords.
4. It generates a summary and sends a new email to you with the subject `[Daily Research] ...`.

## Troubleshooting
- **No Medium Digest found**: Ensure you actually have a "Medium Daily Digest" email in your inbox from the last 2 days.
- **Gmail API Error**: Delete `token.json` and try running the script again to re-authenticate.
