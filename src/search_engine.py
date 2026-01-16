import logging
import time

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

class SearchEngine:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    def search(self, query, max_results=3):
        """
        Searches using DuckDuckGo and returns a list of results.
        :param query: Search query string
        :param max_results: Max number of results to return
        :return: List of dicts {'title', 'href', 'body'}
        """
        # Force exclude medium.com to find external sources
        final_query = f"{query} -site:medium.com"

        logging.info(f"Searching for: {final_query}")

        for attempt in range(self.max_retries):
            try:
                ddgs = DDGS()
                results = list(ddgs.text(final_query, max_results=max_results))
                if results:
                    return results
            except Exception as e:
                logging.warning(f"Search attempt {attempt+1} failed: {e}")
                time.sleep(2)  # Wait a bit before retry

        return []
