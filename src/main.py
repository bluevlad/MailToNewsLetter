import os
import sys
import io

# Fix Windows console encoding for emoji support
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to sys.path to ensure imports work if run from specific dirs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import datetime
import time
from jinja2 import Environment, FileSystemLoader
from src.gmail_client import GmailClient
from src.parser import parse_medium_digest
from src.llm_processor import LLMProcessor
from src.search_engine import SearchEngine
from src.scraper import ContentScraper

from dotenv import load_dotenv

def load_config():
    # Load .env file
    load_dotenv()
    
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'settings.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    # Override with environment variables
    if os.getenv('GOOGLE_API_KEY'):
        if 'gemini' not in config:
            config['gemini'] = {}
        config['gemini']['api_key'] = os.getenv('GOOGLE_API_KEY')
        
    return config

def main():
    print("🚀 Starting Medium Auto-Newsletter (External Research Mode)...")
    
    # 1. Load Config
    config = load_config()
    keywords = config.get('keywords', [])
    print(f"📋 User Keywords: {keywords}")

    # 2. Initialize Clients
    try:
        gmail = GmailClient()
        llm = LLMProcessor(config)
        search_engine = SearchEngine()
        scraper = ContentScraper()
    except Exception as e:
        print(f"❌ Initialization Error: {e}")
        return

    # 3. Fetch Medium Digest
    print("📧 Searching for Medium Daily Digest...")
    query = 'subject:"Medium Daily Digest" newer_than:2d'
    messages = gmail.search_messages(query)
    
    if not messages:
        print("⚠️ No Medium Daily Digest found in the last 2 days.")
        return

    print(f"found {len(messages)} emails. Processing the latest one.")
    latest_msg_id = messages[0]['id']
    html_content = gmail.get_message_content(latest_msg_id)
    
    if not html_content:
        print("❌ Failed to retrieve email content.")
        return

    # 4. Parse Medium Topics
    print("🔍 Extracting topics from Medium email...")
    medium_articles = parse_medium_digest(html_content)
    print(f"Found {len(medium_articles)} potential topics from Medium.")
    
    # Simple filtering: Check if any user keyword is in the title
    relevant_topics = []
    for art in medium_articles:
        title = art['title']
        # If no keywords defined, take top 3. If keywords defined, filter.
        if not keywords or any(k.lower() in title.lower() for k in keywords):
            relevant_topics.append(title)
            
    # Limit to top 3 topics to avoid long execution time
    relevant_topics = relevant_topics[:3]
    
    if not relevant_topics:
        print("⚠️ No relevant topics found matching your keywords. Taking top 1 anyway.")
        if medium_articles:
            relevant_topics.append(medium_articles[0]['title'])
        else:
            return

    print(f"🎯 Selected Topics: {relevant_topics}")

    # 5. External Research & Synthesis
    final_reports = []
    
    for topic in relevant_topics:
        print(f"\n--- Processing Topic: {topic} ---")
        
        # A. Search
        search_query = f"{topic} tech tutorial guide"
        search_results = search_engine.search(search_query, max_results=3)
        if not search_results:
            print("   -> No search results found.")
            continue
            
        print(f"   -> Found {len(search_results)} external links.")
        
        # B. Scrape
        scraped_data = []
        for res in search_results:
            content = scraper.fetch_content(res['href'])
            if content:
                scraped_data.append({
                    'title': res['title'],
                    'url': res['href'],
                    'content': content
                })
        
        if not scraped_data:
            print("   -> Failed to scrape any content.")
            continue
            
        # C. Synthesize
        print("   -> Synthesizing report with Gemini...")
        report = llm.synthesize_report(topic, scraped_data)
        if report:
            final_reports.append(report)
            print("   -> Report generated!")
        
        time.sleep(1) # Polite delay

    if not final_reports:
        print("❌ No reports generated.")
        return

    # 6. Generate Newsletter HTML
    print("\n📝 Generating newsletter HTML...")
    env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')))
    
    # We might need to update the template or use a generic one. 
    # Let's check if we need to modify the template structure match.
    # The 'report' matches the structure expected? 
    # Old template expects 'items' with 'title', 'summary_ko', 'url'.
    # New report has 'title', 'summary_ko', 'references' (list of urls).
    # We will pass 'reports' to the template.
    
    try:
        template = env.get_template('newsletter_template.html')
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        html_output = template.render(reports=final_reports, date=today) # Changed 'items' to 'reports'
    except Exception as e:
        print(f"Template Error: {e}")
        return

    # 7. Send Email
    sender = config.get('email', {}).get('sender', 'me')
    subject_prefix = config.get('email', {}).get('subject_prefix', '[Daily Research] ')
    subject = f"{subject_prefix}Deep Dive: {', '.join([r['title'] for r in final_reports])} ({today})"
    
    print(f"📨 Sending email to {sender}...")
    try:
        profile = gmail.service.users().getProfile(userId='me').execute()
        user_email = profile['emailAddress']
        gmail.send_email(user_email, subject, html_output)
        print("✅ Done! Newsletter sent.")
    except Exception as e:
        print(f"Email Error: {e}")

if __name__ == "__main__":
    main()
