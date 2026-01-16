# Integrated AI Newsletter Service Proposal

## 🎯 목표
기존 **네이버 뉴스 요약 서비스(Ollama 기반)**에 **Medium Daily Digest 분석 기능**을 통합하여, 국내 뉴스와 해외 기술/인사이트(Medium)를 한 번에 받아보는 **통합 AI 뉴스레터**를 구축합니다.

## 🏗 통합 아키텍처 (Integrated Architecture)

```mermaid
graph TD
    subgraph "Input Sources"
        A[Naver News Search API] -->|Search Results| D{Data Collector}
        B[Gmail (Medium Digest)] -->|Fetch & Parse HTML| D
    end

    subgraph "Processing Core (Python)"
        D -->|Raw Text| E[Text Preprocessor]
        E -->|Cleaned Text| F[Ollama LLM (Local/Server)]
        
        style F fill:#f9f,stroke:#333,stroke-width:2px
    end

    subgraph "Output"
        F -->|Summaries & Insights| G[Content Aggregator]
        G -->|Jinja2 Template| H[Unified Newsletter (HTML)]
        H -->|SMTP/Gmail API| I[User Inbox]
    end
```

## 🛠 확장된 기술 스택 (Tech Stack)
1.  **Core Language**: Python 3.x
2.  **LLM Engine**: **Ollama** (기존 활용 유지)
    *   **Model**: mistral, llama3, or gemma (한국어/영어 처리에 능한 모델 권장)
    *   **Role**:
        *   네이버 뉴스: 기존 로직 유지 (요약 및 분류)
        *   **Medium (New)**: 영어 텍스트 번역, 핵심 인사이트 추출, 사용자 관심사 매칭 점수 산정.
3.  **New Input Source**: Gmail API
    *   Medium 메일 수신 확인 및 HTML 파싱 (`BeautifulSoup`).
4.  **Template Engine**: Jinja2
    *   `Section 1: 오늘의 국내 뉴스 (Naver)`
    *   `Section 2: 해외 인사이트 (Medium)` 로 구분하여 레이아웃 구성.

## 📋 구현 및 통합 전략

### 1. 모듈화 (Modularity)
기존 코드를 건드리지 않고 확장하기 위해 각 수집기를 모듈(Class) 형태로 분리합니다.
*   `NaverNewsFetcher`: 기존 코드 활용.
*   `MediumEmailFetcher`: 새로 구현. (Gmail API 연동 -> 메일 본문 파싱 -> 기사 리스트 추출)
*   `OllamaProcessor`: LLM과의 통신 담당. 프롬프트만 다르게 적용하여 두 소스를 모두 처리.

### 2. Medium 처리 로직 (New)
Medium 메일은 내용이 길고 링크가 많으므로 전처리가 중요합니다.
1.  **Filtering**: 기사 제목과 부제목만 먼저 추출하여 Ollama에게 보냅니다.
    *   *Prompt*: "이 기사 리스트 중 [관심 키워드]와 연관성이 높은 기사 3개를 골라줘."
2.  **Deep Dive**: 선정된 3개의 기사에 대해 본문(또는 메일 내 요약문)을 상세 요약 및 한글 번역합니다.

### 3. 통합 뉴스레터 생성
*   두 모듈의 실행 결과를 하나의 Dictionary로 합칩니다 (예: `context = {'naver': [...], 'medium': [...]}`)
*   새로운 HTML 템플릿을 만들어 두 섹션을 시각적으로 구분하여 보여줍니다.

## ✅ 검토 의견 (Feasibility Review)
*   **가능 여부**: **매우 적합 (Feasible)**
    *   이미 Python + Ollama 환경이 구축되어 있으므로, Gmail API 연동 부분만 추가하면 됩니다.
    *   Ollama는 로컬에서 돌리므로 API 비용이 들지 않아, Medium의 많은 기사 텍스트를 처리하더라도 부담이 없습니다.
*   **고려 사항**:
    *   **속도**: 로컬 LLM은 외부 API보다 느릴 수 있습니다. Medium 기사가 많으면 처리 시간이 길어질 수 있으므로, **1차 필터링(제목 기반)**을 먼저 수행하여 LLM 부하를 줄이는 것이 핵심입니다.
    *   **컨텍스트 길이**: Ollama 모델의 Context Window 한계를 고려하여, 기사 내용을 적절히 잘라서 입력해야 합니다.

## 🚀 다음 단계 (Next Steps)
1.  기존 네이버 뉴스 서비스 코드가 있는 폴더 위치를 알려주시거나, 해당 코드를 공유해주시면 통합 구조를 잡아드리겠습니다.
2.  먼저 `MediumEmailFetcher` 모듈만 독립적으로 개발하여 테스트한 뒤 합칠 수 있습니다.
