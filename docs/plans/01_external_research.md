# Implement External Research & Scraping

## Goal
Implement the "External Research" strategy described in `PROPOSAL_V3.md`. Instead of just summarizing Medium snippets, the system will:
1. Extract keywords from Medium.
2. Search for high-quality, free sources (using DuckDuckGo).
3. Scrape the full content of those sources.
4. Generate a comprehensive report using Gemini.

## Proposed Changes

### Source Code

#### [NEW] `src/search_engine.py`
- **Functionality**: `SearchEngine` class using `DDGS`.
- **Logic**: Excludes `medium.com`.

#### [NEW] `src/scraper.py`
- **Functionality**: `ContentScraper` class using `trafilatura`.

#### [MODIFY] `src/main.py`
- **New Flow**: `Gmail -> Parse -> Search -> Scrape -> LLM`.

#### [MODIFY] `src/llm_processor.py`
- **Change**: Update prompt to synthesize external articles.

## Verification
- Run `python src/main.py` and verify console logs show search/scrape activities.
