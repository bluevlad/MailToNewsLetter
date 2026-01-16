import google.generativeai as genai
import os
import json
import logging

class LLMProcessor:
    def __init__(self, config):
        self.config = config
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            # Fallback to config if not in env (though env is recommended)
            self.api_key = self.config.get('gemini', {}).get('api_key')
        
        if not self.api_key:
            raise ValueError("Google API Key not found. Set GOOGLE_API_KEY env var.")

        genai.configure(api_key=self.api_key)
        self.model_name = self.config.get('gemini', {}).get('model', 'gemini-pro')
        self.model = genai.GenerativeModel(self.model_name)
    
    def synthesize_report(self, topic, articles):
        """
        Generates a synthesis report based on external articles for a given topic.
        :param topic: The search topic (e.g., "React Server Components")
        :param articles: List of dicts {'title', 'url', 'content'}
        :return: A dict with 'summary_ko', 'title', 'references'
        """
        if not articles:
            return None

        # Limit content length to avoid token limits (approx 10k chars total)
        context_text = ""
        for i, art in enumerate(articles):
            content_preview = art.get('content', '')[:2000] # Take first 2000 chars per article
            context_text += f"\n[Article {i+1}]: {art.get('title')}\nSource: {art.get('url')}\nContent:\n{content_preview}\n{'-'*20}\n"

        prompt = f"""
        You are a smart technical news editor.
        
        Topic: "{topic}"
        
        Here are some collected articles from the web:
        {context_text}

        Task:
        1. Synthesize these articles into a comprehensive report in Korean.
        2. Explain the core concepts, why it matches the topic, and key takeaways.
        3. The tone should be professional yet easy to understand (like a tech blog).
        4. Return the result strictly in this JSON format:
        {{
            "title": "<A catchy Korean title for this report>",
            "summary_ko": "<The detailed synthesis report in Korean (Markdown supported)>",
            "references": [
                {{"title": "<Article 1 Title>", "url": "<Article 1 URL>"}},
                ...
            ]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)

        except Exception as e:
            logging.error(f"Error in Gemini processing: {e}")
            return None
