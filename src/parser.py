from bs4 import BeautifulSoup
import re

def parse_medium_digest(html_content):
    """
    Parses the Medium Daily Digest HTML to extract articles.
    Returns a list of dictionaries: {'title', 'url', 'snippet', 'thumbnail'}
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = []
    
    # Heuristic: distinct articles in emails are often in tables or divs with specific styles.
    # But usually, the title is an <a> tag with bold text or headers.
    
    # Strategy: Find all <a> tags that look like story links.
    # Exclude system links (Unsubscribe, Settings, etc.)
    
    links = soup.find_all('a', href=True)
    
    seen_urls = set()

    for link in links:
        url = link['href']
        text = link.get_text(strip=True)
        
        # Filter logic
        if 'medium.com' not in url and 'link.medium.com' not in url:
            continue
        if any(x in text.lower() for x in ['unsubscribe', 'subscribe', 'help', 'status', 'manage', 'upgrade', 'open in app']):
            continue
        if len(text) < 10: # Title too short
            continue
        
        # Clean URL (remove tracking params if possible, though medium links are messy)
        # For uniqueness, we might just strip query params, but Medium sometimes uses them for routing?
        # Let's keep the full URL for safety but check duplicates by a vague match.
        
        if url in seen_urls:
            continue
        
        # Attempt to find snippet
        # Snippets are often in a sibling element or parent's sibling.
        snippet = ""
        # Look at the parent container
        parent = link.parent
        # Go up a few levels to find the "card"
        card = parent
        for _ in range(3):
            if card and card.name in ['td', 'div', 'tr']:
                # extracting potential snippet from this card
                full_text = card.get_text(separator=' ', strip=True)
                if len(full_text) > len(text) + 20: # If there is more text than just the title
                    snippet = full_text.replace(text, '').strip()
                    # Truncate snippet
                    snippet = snippet[:300] + "..." if len(snippet) > 300 else snippet
                    break
            card = card.parent if card else None
            
        seen_urls.add(url)
        
        articles.append({
            'title': text,
            'url': url,
            'snippet': snippet,
            # 'thumbnail': ... # Thumbnails are harder to associate without specific classes. skipping for MVP.
        })

    return articles
