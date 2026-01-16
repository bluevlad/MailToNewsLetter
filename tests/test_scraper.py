import unittest
from src.scraper import ContentScraper

class TestContentScraper(unittest.TestCase):
    def test_fetch_content(self):
        scraper = ContentScraper()
        # Test with a known stable URL (e.g., Python.org)
        url = "https://www.python.org/"
        content = scraper.fetch_content(url)
        
        self.assertIsNotNone(content)
        self.assertIn("Python", content) # Should contain "Python"

if __name__ == '__main__':
    unittest.main()
