# Medium Auto-Newsletter Project Proposal

## 🎯 목표
Gmail로 수신되는 **Medium Daily Digest** 이메일들을 자동으로 분석하여, 사용자의 관심사에 맞는 기사만 선별하고 요약한 **"나만의 뉴스레터"**를 매일 아침 받아볼 수 있도록 합니다.

## 🏗 아키텍처 (Architecture)

```mermaid
graph LR
    A[Gmail (Medium Digest)] -->|Fetch API| B(Python Script)
    B -->|Content Extraction| C{AI Filtering (Gemini)}
    C -->|Summarize & Reformat| D[Personalized Newsletter]
    D -->|Send Email| E[User Inbox]
```

## 🛠 기술 스택 (Tech Stack)
1.  **Language**: Python 3.x
    *   이유: 텍스트 처리 라이브러리가 풍부하고 Google API와의 연동이 가장 쉽습니다.
2.  **Email Source**: Gmail API
    *   `google-auth`, `google-api-python-client` 라이브러리 사용.
    *   IMAP보다 안정적이고 보안성이 높습니다.
3.  **Core Logic & Intelligence**: **Google Gemini API** (Flash or Pro model)
    *   기사 제목과 요약을 보고 사용자의 관심사(Keyword)에 맞는지 판단.
    *   선택된 기사의 내용을 한국어로 번역 및 3줄 요약.
4.  **Formatting**: Jinja2 Template
    *   깔끔한 HTML 이메일 템플릿 생성.
5.  **Automation**: GitHub Actions (추천) 또는 Local Cron
    *   별도의 서버 없이 매일 정해진 시간에 GitHub Action이 스크립트를 실행하도록 설정 가능.

## 📋 구현 단계 (Implementation Steps)

### Phase 1: 환경 설정 및 데이터 수집
- Google Cloud Console에서 Gmail API 활성화 및 `credentials.json` 발급.
- Python 프로젝트 설정 (`requirements.txt`).
- Gmail에서 지난 24시간 동안 온 'Medium Daily Digest' 메일 검색 및 본문(HTML) 가져오기.

### Phase 2: 파싱 및 데이터 추출
- `BeautifulSoup`을 사용하여 메일 본문에서 기사 제목, 링크, 썸네일, 짧은 설명 추출.
- 추출된 데이터를 구조화된 리스트(JSON 형태)로 변환.

### Phase 3: AI 필터링 및 요약 (The Core)
- Gemini API에 프롬프트 전송:
    > "다음 기사 목록 중 [사용자 관심사 키워드]와 관련된 기사를 5개 선정하고, 각 기사를 한국어로 핵심 요약해줘."
- JSON 형태로 응답을 받아 처리.

### Phase 4: 뉴스레터 생성 및 발송
- 선정된 기사들을 깔끔한 HTML 템플릿에 주입.
- Gmail API를 사용하여 사용자 본인에게 '오늘의 Medium 요약' 메일 발송.

### Phase 5: 자동화
- GitHub Repository 생성 및 Secrets 설정 (API Key 등).
- `.github/workflows/daily_digest.yml` 작성하여 매일 오전 8시(KST) 자동 실행 설정.

## 💡 주요 기능 (Features)
- **Zero-Click**: 스크립트가 알아서 메일을 읽고 정리해줍니다.
- **Personalization**: `config.yaml` 파일에 관심 키워드(예: `AI`, `React`, `System Design`)만 적어두면 관련 없는 글은 자동으로 걸러집니다.
- **Digestibility**: 영어 원문 대신 한국어 요약을 먼저 보여주어 읽을지 말지 빠르게 결정 가능합니다.
