import sys
import os
import io
import time
import datetime
import yaml
import re

# Change to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, script_dir)

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from src.gmail_client import GmailClient
from src.parser import parse_medium_digest
from src.llm_processor import LLMProcessor
from src.search_engine import SearchEngine
from src.scraper import ContentScraper

def load_config():
    load_dotenv()
    config_path = os.path.join(script_dir, 'config', 'settings.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    if os.getenv('GOOGLE_API_KEY'):
        if 'gemini' not in config:
            config['gemini'] = {}
        config['gemini']['api_key'] = os.getenv('GOOGLE_API_KEY')
    return config

def extract_keywords_from_title(title):
    """Extract main keywords from a title for better search"""
    stop_words = {'i', 'the', 'a', 'an', 'is', 'was', 'were', 'be', 'been', 'being',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
                  'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'up',
                  'about', 'into', 'through', 'during', 'before', 'after', 'above',
                  'below', 'between', 'under', 'again', 'further', 'then', 'once',
                  'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each',
                  'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
                  'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'or',
                  'and', 'but', 'if', 'because', 'as', 'until', 'while', 'this',
                  'that', 'these', 'those', 'am', 'are', 'my', 'your', 'his', 'her',
                  'its', 'our', 'their', 'what', 'which', 'who', 'whom', 'both',
                  'you', 'me', 'him', 'them', 'we', 'they', 'it', 'he', 'she',
                  'don', 'dont', 'didn', 'doesn', 'won', 'wouldn', 'couldn', 'shouldn',
                  'isn', 'aren', 'wasn', 'weren', 'haven', 'hasn', 'hadn',
                  'ever', 'never', 'also', 'even', 'still', 'already', 'yet',
                  'tested', 'months', 'production', 'tracks', 'real', 'deep', 'dive',
                  'bombed', 'interview', 'explain', 'concepts', 'clear', 'round',
                  'lessons', 'learned', 'extracting', 'complex', 'documents'}

    clean = re.sub(r'[^\w\s]', ' ', title.lower())
    words = clean.split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return ' '.join(keywords[:4])

def clean_topic(title):
    """Clean topic title for better search results"""
    patterns = [
        r'^(.+?)(?:Have you ever|Recently|Then I|Startup time|Here)',
        r'^(.+?)(?:\s{2,})',
    ]

    for pattern in patterns:
        match = re.match(pattern, title)
        if match:
            return match.group(1).strip()

    if len(title) > 80:
        return title[:80].rsplit(' ', 1)[0]

    return title

def main():
    print("=" * 60)
    print("January 2026 Medium Newsletter Generator")
    print("=" * 60)

    # 1. Load Config
    config = load_config()
    keywords = config.get('keywords', [])
    print(f"User Keywords: {keywords}")

    # 2. Initialize Clients
    try:
        gmail = GmailClient()
        llm = LLMProcessor(config)
        search_engine = SearchEngine()
        scraper = ContentScraper()
    except Exception as e:
        print(f"Initialization Error: {e}")
        return

    # 3. Fetch all January 2026 Medium emails
    print("\nSearching for January 2026 Medium Daily Digest emails...")
    query = 'from:noreply@medium.com after:2026/01/01 before:2026/02/01'
    messages = gmail.search_messages(query)

    if not messages:
        print("No Medium Daily Digest found for January 2026.")
        return

    print(f"Found {len(messages)} emails. Processing all...")

    # 4. Collect all topics from all January emails
    all_topics = []

    for i, msg in enumerate(messages):
        print(f"\nProcessing email {i+1}/{len(messages)}...")
        html_content = gmail.get_message_content(msg['id'])

        if not html_content:
            print(f"  Failed to retrieve email content for {msg['id']}")
            continue

        medium_articles = parse_medium_digest(html_content)
        print(f"  Found {len(medium_articles)} topics in this email")

        for art in medium_articles:
            title = art['title']
            if not keywords or any(k.lower() in title.lower() for k in keywords):
                cleaned = clean_topic(title)
                all_topics.append(cleaned)

    # Remove duplicates while preserving order
    seen = set()
    unique_topics = []
    for t in all_topics:
        t_lower = t.lower()
        if t_lower not in seen and len(t) > 15:
            seen.add(t_lower)
            unique_topics.append(t)

    print(f"\nTotal unique topics collected: {len(unique_topics)}")

    print("\nAll topics:")
    for i, t in enumerate(unique_topics[:20]):
        print(f"  {i+1}. {t}")

    selected_topics = unique_topics[:5]
    print(f"\nSelected Topics (top 5):")
    for i, t in enumerate(selected_topics):
        print(f"  {i+1}. {t}")

    if not selected_topics:
        print("No relevant topics found matching your keywords.")
        return

    # 5. External Research & Synthesis
    final_reports = []

    for idx, topic in enumerate(selected_topics):
        print(f"\n--- [{idx+1}/{len(selected_topics)}] Processing Topic: {topic} ---")

        # A. Search with keyword extraction
        search_keywords = extract_keywords_from_title(topic)
        search_query = f"{search_keywords} tutorial"
        print(f"   Search query: {search_query}")

        search_results = search_engine.search(search_query, max_results=3)

        if not search_results:
            simpler_keywords = ' '.join(search_keywords.split()[:2])
            print(f"   Retrying with: {simpler_keywords}")
            search_results = search_engine.search(simpler_keywords, max_results=3)

        if not search_results:
            print("   -> No search results found.")
            continue

        print(f"   -> Found {len(search_results)} external links.")
        for r in search_results:
            print(f"      - {r.get('title', 'No title')[:60]}...")

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

        print(f"   -> Scraped {len(scraped_data)} articles successfully.")

        # C. Synthesize with retry logic for rate limiting
        print("   -> Synthesizing report with Gemini...")
        report = None
        for attempt in range(3):
            report = llm.synthesize_report(topic, scraped_data)
            if report:
                break
            print(f"   -> Retry {attempt + 1}/3, waiting 15 seconds...")
            time.sleep(15)

        if report:
            final_reports.append(report)
            print(f"   -> Report generated: {report.get('title', 'No title')}")
        else:
            print("   -> Failed to generate report after retries.")

        time.sleep(3)

    if not final_reports:
        print("\nNo reports generated.")
        return

    print(f"\n{'=' * 60}")
    print(f"Total reports generated: {len(final_reports)}")
    print('=' * 60)

    # 6. Generate Newsletter HTML
    print("\nGenerating newsletter HTML...")
    env = Environment(loader=FileSystemLoader(os.path.join(script_dir, 'templates')))

    try:
        template = env.get_template('newsletter_template.html')
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        html_output = template.render(reports=final_reports, date=f"January 2026 Monthly Digest ({today})")
    except Exception as e:
        print(f"Template Error: {e}")
        return

    # 7. Send Email
    subject_prefix = config.get('email', {}).get('subject_prefix', '[Daily Research] ')
    subject = f"{subject_prefix}January 2026 Monthly Tech Digest - {len(final_reports)} Topics"

    try:
        profile = gmail.service.users().getProfile(userId='me').execute()
        user_email = profile['emailAddress']
        print(f"\nSending email to {user_email}...")
        gmail.send_email(user_email, subject, html_output)
        print("\n" + "=" * 60)
        print("SUCCESS! Newsletter sent.")
        print("=" * 60)
    except Exception as e:
        print(f"Email Error: {e}")

if __name__ == "__main__":
    main()
