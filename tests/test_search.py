import unittest
from src.search_engine import SearchEngine

class TestSearchEngine(unittest.TestCase):
    def test_search_execution(self):
        engine = SearchEngine(max_retries=1)
        # Search for something very common to ensure results
        results = engine.search("Python tutorial", max_results=2)
        
        self.assertIsInstance(results, list)
        if results:
            first = results[0]
            self.assertIn('title', first)
            self.assertIn('href', first)
            
if __name__ == '__main__':
    unittest.main()
