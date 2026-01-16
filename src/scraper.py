import trafilatura
import logging

class ContentScraper:
    def __init__(self):
        pass

    def fetch_content(self, url):
        """
        Fetches the main text content from a URL.
        :param url: URL to scrape
        :return: Extracted text or None
        """
        logging.info(f"🕸️ Scraping content from: {url}")
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded)
                return text
            else:
                logging.warning(f"⚠️ Failed to download: {url}")
                return None
        except Exception as e:
            logging.error(f"❌ Scraping error for {url}: {e}")
            return None
