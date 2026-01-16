import os
import sys
import yaml
import datetime
import time
from jinja2 import Environment, FileSystemLoader
from src.gmail_client import GmailClient
from src.llm_processor import LLMProcessor
from src.search_engine import SearchEngine
from src.scraper import ContentScraper

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'settings.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def verify_pipeline():
    print("🧪 Starting Mock Verification Pipeline...")
    
    config = load_config()
    
    # 1. Initialize
    try:
        gmail = GmailClient()
        llm = LLMProcessor(config)
        search_engine = SearchEngine()
        scraper = ContentScraper()
    except Exception as e:
        print(f"❌ Init Error: {e}")
        return

    # 2. Mock Medium Topic
    # We pretend we found this topic in an email
    topic = "LangChain vs RAG agents"
    print(f"🎯 Test Topic: {topic}")

    # 3. Search
    print(f"🔎 Searching for '{topic}'...")
    search_results = search_engine.search(f"{topic} guide", max_results=2)
    
    
    if not search_results:
        print("⚠️ Search failed (possibly rate limited). Using fallback URL.")
        # Fallback to a known tech blog
        search_results = [{
            'title': 'LangChain vs LlamaIndex', 
            'href': 'https://www.llamaindex.ai/blog/llamaindex-vs-langchain-which-is-right-for-you',
            'body': 'Comparison...'
        }]
        
    print(f"✅ Found {len(search_results)} links.")

    # 4. Scrape
    print("🕸️ Scraping first result...")
    scraped_data = []
    
    # Try the first one
    res = search_results[0]
    content = scraper.fetch_content(res['href'])
    
    if content:
        print(f"✅ Scraped {len(content)} chars from {res['href']}")
        scraped_data.append({
            'title': res['title'],
            'url': res['href'],
            'content': content
        })
    else:
        print("⚠️ Failed to scrape first link, trying second...")
        if len(search_results) > 1:
            res = search_results[1]
            content = scraper.fetch_content(res['href'])
            if content:
                scraped_data.append({
                    'title': res['title'],
                    'url': res['href'],
                    'content': content
                })

    if not scraped_data:
        print("⚠️ Failed to scrape content. Using HARDCODED MOCK CONTENT for verification.")
        scraped_data = [{
            'title': 'Mock Article: LangChain Overview',
            'url': 'https://example.com/mock-article',
            'content': 'LangChain is a framework for developing applications powered by language models. It enables applications that are: Data-aware: connect a language model to other sources of data. Agentic: allow a language model to interact with its environment. The main value props of LangChain are: 1. Components: Abstractions for working with language models, along with a collection of implementations for each abstraction. Components are modular and easy-to-use, whether you are using the rest of the LangChain framework or not. 2. Off-the-shelf chains: A structured assembly of components for accomplishing specific higher-level tasks. Off-the-shelf chains make it easy to get started. For more complex applications and nuanced use-cases, components make it easy to customize existing chains or build new ones.'
        }]

    # 5. Synthesize
    print("🤖 Synthesizing report with Gemini...")
    report = llm.synthesize_report(topic, scraped_data)
    
    if not report:
        print("⚠️ Gemini failed (API Error). Using MOCK REPORT for verification.")
        report = {
            'title': 'Mock Report: LangChain vs RAG',
            'summary_ko': '<p>Gemini API 연동에 실패하여 테스트용 데이터를 표시합니다.</p><p>외부 검색과 스크래핑은 성공했으나, LLM 요약 단계에서 인증/모델 오류가 발생했습니다. 설정(settings.yaml)의 API Key와 Model 이름을 점검해주세요.</p>',
            'references': scraped_data
        }
        
    print("✅ Report Generated!")
    print(f"Title: {report.get('title')}")

    # 6. Generate HTML
    print("📝 Rendering HTML...")
    env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')))
    template = env.get_template('newsletter_template.html')
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    html_output = template.render(reports=[report], date=today)

    # 7. Send Email
    sender = config.get('email', {}).get('sender', 'me')
    subject = f"[TEST] Pipeline Verification: {topic}"
    
    print(f"📨 Sending test email to {sender}...")
    try:
        profile = gmail.service.users().getProfile(userId='me').execute()
        user_email = profile['emailAddress']
        gmail.send_email(user_email, subject, html_output)
        print("✅ Test Email Sent Successfully!")
    except Exception as e:
        print(f"❌ Email failed: {e}")

if __name__ == "__main__":
    verify_pipeline()
