"""
Daily Newsletter Generator with Fact-Checking

This script processes Medium Daily Digest emails from the previous day,
generates AI summaries, verifies content accuracy, and sends a newsletter.

Usage:
    python src/daily_newsletter.py
    python src/daily_newsletter.py --date 2026-01-15  # Specific date
    python src/daily_newsletter.py --no-factcheck     # Skip fact-checking
"""

import sys
import os
import io
import time
import datetime
import yaml
import re
import argparse

# Change to script directory
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
from src.fact_checker import FactChecker


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
                  'ever', 'never', 'also', 'even', 'still', 'already', 'yet'}

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
    parser = argparse.ArgumentParser(description='Daily Newsletter Generator with Fact-Checking')
    parser.add_argument('--date', type=str, help='Target date (YYYY-MM-DD), defaults to yesterday')
    parser.add_argument('--no-factcheck', action='store_true', help='Skip fact-checking')
    parser.add_argument('--max-topics', type=int, default=3, help='Maximum topics to process (default: 3)')
    args = parser.parse_args()

    # Determine target date
    if args.date:
        target_date = datetime.datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        target_date = datetime.date.today() - datetime.timedelta(days=1)

    print("=" * 60)
    print(f"Daily Newsletter Generator - {target_date}")
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
        fact_checker = FactChecker()

        if not args.no_factcheck and fact_checker.is_configured():
            print("✓ Fact-checking enabled (Google Custom Search API)")
        else:
            print("⚠ Fact-checking disabled")

    except Exception as e:
        print(f"Initialization Error: {e}")
        return

    # 3. Fetch Medium emails for target date
    print(f"\nSearching for Medium Daily Digest from {target_date}...")

    # Search for emails from the target date
    next_day = target_date + datetime.timedelta(days=1)
    query = f'from:noreply@medium.com after:{target_date.strftime("%Y/%m/%d")} before:{next_day.strftime("%Y/%m/%d")}'

    messages = gmail.search_messages(query)

    if not messages:
        print(f"No Medium Daily Digest found for {target_date}.")
        return

    print(f"Found {len(messages)} email(s).")

    # 4. Collect topics from emails
    all_topics = []

    for i, msg in enumerate(messages):
        print(f"\nProcessing email {i+1}/{len(messages)}...")
        html_content = gmail.get_message_content(msg['id'])

        if not html_content:
            print(f"  Failed to retrieve email content")
            continue

        medium_articles = parse_medium_digest(html_content)
        print(f"  Found {len(medium_articles)} topics")

        for art in medium_articles:
            title = art['title']
            if not keywords or any(k.lower() in title.lower() for k in keywords):
                cleaned = clean_topic(title)
                if len(cleaned) > 15:
                    all_topics.append(cleaned)

    # Remove duplicates
    seen = set()
    unique_topics = []
    for t in all_topics:
        t_lower = t.lower()
        if t_lower not in seen:
            seen.add(t_lower)
            unique_topics.append(t)

    print(f"\nTotal unique topics: {len(unique_topics)}")

    # Limit topics
    selected_topics = unique_topics[:args.max_topics]
    print(f"Selected Topics ({len(selected_topics)}):")
    for i, t in enumerate(selected_topics):
        print(f"  {i+1}. {t}")

    if not selected_topics:
        print("No relevant topics found.")
        return

    # 5. External Research, Synthesis & Fact-Check
    final_reports = []

    for idx, topic in enumerate(selected_topics):
        print(f"\n{'='*50}")
        print(f"[{idx+1}/{len(selected_topics)}] {topic}")
        print('='*50)

        # A. Search
        search_keywords = extract_keywords_from_title(topic)
        search_query = f"{search_keywords} tutorial"
        print(f"Searching: {search_query}")

        search_results = search_engine.search(search_query, max_results=3)

        if not search_results:
            simpler = ' '.join(search_keywords.split()[:2])
            print(f"Retrying: {simpler}")
            search_results = search_engine.search(simpler, max_results=3)

        if not search_results:
            print("  ✗ No search results")
            continue

        print(f"  ✓ Found {len(search_results)} external links")

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
            print("  ✗ Failed to scrape content")
            continue

        print(f"  ✓ Scraped {len(scraped_data)} articles")

        # C. Synthesize with Gemini
        print("  → Synthesizing with Gemini...")
        report = None
        for attempt in range(3):
            report = llm.synthesize_report(topic, scraped_data)
            if report:
                break
            print(f"    Retry {attempt + 1}/3, waiting 20 seconds...")
            time.sleep(20)

        if not report:
            print("  ✗ Failed to generate report")
            continue

        print(f"  ✓ Report: {report.get('title', topic)}")

        # D. Fact-Check (if enabled)
        if not args.no_factcheck and fact_checker.is_configured():
            print("  → Fact-checking...")
            summary_text = report.get('summary_ko', '')

            fact_report = fact_checker.verify_content(topic, summary_text)
            report['fact_check_html'] = fact_checker.format_report_html(fact_report)

            confidence = int(fact_report.overall_confidence * 100)
            print(f"  ✓ Fact-check complete (Confidence: {confidence}%)")

            if fact_report.warnings:
                for warning in fact_report.warnings:
                    print(f"    ⚠ {warning}")

        final_reports.append(report)
        time.sleep(3)  # Rate limiting

    if not final_reports:
        print("\n✗ No reports generated.")
        return

    print(f"\n{'='*60}")
    print(f"Total reports: {len(final_reports)}")
    print('='*60)

    # 6. Generate Newsletter HTML
    print("\nGenerating newsletter...")
    env = Environment(loader=FileSystemLoader(os.path.join(script_dir, 'templates')))

    try:
        template = env.get_template('newsletter_template.html')
        html_output = template.render(
            reports=final_reports,
            date=target_date.strftime("%Y-%m-%d")
        )
    except Exception as e:
        print(f"Template Error: {e}")
        return

    # 7. Send Email
    subject_prefix = config.get('email', {}).get('subject_prefix', '[Daily Research] ')
    subject = f"{subject_prefix}{target_date.strftime('%Y-%m-%d')} Tech Digest ({len(final_reports)} topics)"

    try:
        profile = gmail.service.users().getProfile(userId='me').execute()
        user_email = profile['emailAddress']
        print(f"\nSending to {user_email}...")
        gmail.send_email(user_email, subject, html_output)
        print("\n" + "=" * 60)
        print("✓ SUCCESS! Newsletter sent.")
        print("=" * 60)
    except Exception as e:
        print(f"Email Error: {e}")


if __name__ == "__main__":
    main()
