# Medium Topic-Based External Research Newsletter

## 🎯 목표
**Medium Daily Digest**를 "주제 발견(Topic Discovery)"의 도구로만 활용하고, 실제 콘텐츠는 **외부의 무료/공개된 소스(Tech Blogs, Forums, News)**에서 검색하여 확보합니다. 이를 통해 페이월(유료 구독 제한) 문제를 해결하고, 더 폭넓은 시각의 정보를 Ollama로 요약해 받아보는 **나만의 심층 리서치 뉴스레터**를 구축합니다.

## 🏗 변경된 아키텍처 (Revised Architecture)

```mermaid
graph TD
    A[Gmail (Medium Digest)] -->|Title & Keywords| B(Topic Extractor)
    B -->|Search Query| C{Web Search Engine}
    
    subgraph "External Research Strategy"
        C -->|Query: 'Topic -site:medium.com'| D[Free Tech Sources]
        D -->|Dev.to, HackerNews, Corp Blogs| E[Content Scraper]
    end

    E -->|Raw Content| F[Ollama (Local LLM)]
    F -->|Summarize & Translate| G[Report Generator]
    G -->|Send Email| H[User Inbox]
```

## 🗝 핵심 전략: "Medium as a Compass" (나침반으로서의 Medium)
Medium은 현재 가장 핫한 트렌드가 무엇인지만 알려주는 용도로 씁니다. 상세 내용은 무료 소스에서 찾습니다.

### 1단계: 주제 추출 (Extraction)
*   Medium 메일에서 기사 제목(Header)과 짧은 설명(Snippet)만 파싱합니다.
*   예: "*Understanding React Server Components*"라는 제목이 있다면, **키워드: "React Server Components tutorial guide"**를 추출합니다.

### 2단계: 외부 소스 검색 (Cross-Referencing)
*   **Search Engine**: Google Custom Search API 또는 DuckDuckGo (무료 라이브러리 활용)
*   **Search Query**: `"{Topic Keyword}" -site:medium.com`
    *   Medium 도메인을 제외하고 검색하여 무료이면서 양질의 글이 많은 사이트(Dev.to, FreeCodeCamp, 기업 기술 블로그 등)를 타겟팅합니다.

### 3단계: 콘텐츠 수집 및 요약 (Harvest & Digest)
*   **Scraper**: `newspaper3k` 또는 `BeautifulSoup` 라이브러리를 사용하여 검색된 상위 1~2개 글의 본문을 긁어옵니다.
*   **Ollama Intelligence**:
    *   수집된 외부 글들의 내용을 바탕으로 종합 리포트를 작성합니다.
    *   Prompt: *"이 주제에 대해 수집된 다음 글들을 읽고, 핵심 기술 트렌드와 사용법을 초보자도 알기 쉽게 한국어로 설명해줘."*

## 🛠 기술 스택 (Tech Stack)
1.  **Language**: Python 3.x
2.  **LLM**: **Ollama** (Local) - 비용 0원, 무제한 텍스트 처리.
3.  **Search**: `duckduckgo-search` (Python Lib) - 별도 API Key 없이 간편 사용 가능.
4.  **Scraping**: `trafilatura` 또는 `newspaper3k` - 뉴스/블로그 본문 텍스트 추출에 특화됨.
5.  **Email**: Gmail API (OAuth 2.0) - 메일 수신 및 발송 통합.

## 📋 구현 워크플로우 (Implementation Workflow)

1.  **Initialization**:
    *   Gmail API 연동 및 Ollama 모델 로드.
2.  **Monitor**:
    *   오늘 도착한 Medium Digest 메일 찾기.
3.  **Analytic Loop** (각 토픽별 반복):
    *   토픽 선정 -> 웹 검색(DuckDuckGo) -> 상위 2개 링크 방문 및 본문 추출 -> Ollama 요약.
4.  **Composition**:
    *   "오늘의 Medium 토픽을 바탕으로 찾아본 심층 리포트" 형식의 뉴스레터 생성.
5.  **Delivery**:
    *   최종 HTML 이메일 발송.

## 💡 장점
*   **No Paywall**: 유료 구독 없이도 해당 주제에 대한 깊이 있는 지식을 얻을 수 있습니다.
*   **Cross-Check**: 한 작가의 의견(Medium)뿐만 아니라, 공신력 있는 여러 소스를 종합하므로 편향되지 않은 정보를 얻습니다.
*   **Automation**: 이 모든 과정(주제 선정 -> 검색 -> 읽기 -> 요약)이 자동으로 수행됩니다.
