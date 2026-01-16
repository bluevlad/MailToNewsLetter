# MailToNewsLetter

Medium Daily Digest를 기반으로 외부 소스에서 정보를 수집하고, AI로 요약하여 개인화된 뉴스레터를 자동 생성하는 시스템입니다.

## 주요 기능

- **Medium 토픽 추출**: Medium Daily Digest에서 관심 키워드 기반 토픽 자동 추출
- **외부 소스 검색**: DuckDuckGo를 통해 페이월 없는 무료 기술 콘텐츠 검색
- **AI 요약**: Google Gemini API를 활용한 한국어 종합 리포트 생성
- **팩트체크**: Google Custom Search API를 통한 콘텐츠 정확성 검증
- **자동 발송**: Gmail API를 통한 뉴스레터 자동 발송

## 아키텍처

```
Gmail (Medium Digest)
    ↓
Topic Extractor (키워드 필터링)
    ↓
DuckDuckGo Search (-site:medium.com)
    ↓
Content Scraper (trafilatura)
    ↓
Gemini AI (요약 생성)
    ↓
Fact Checker (Google Search 검증)  ← NEW
    ↓
Newsletter (HTML 이메일 발송)
```

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/bluevlad/MailToNewsLetter.git
cd MailToNewsLetter
```

### 2. 가상환경 설정

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env` 파일 생성:

```env
# Gemini API Key (필수)
GOOGLE_API_KEY=your_gemini_api_key

# Google Custom Search API (팩트체크용, 선택)
GOOGLE_SEARCH_API_KEY=your_search_api_key
GOOGLE_SEARCH_CX=your_search_engine_id
```

### 5. Gmail API 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. Gmail API 활성화
3. OAuth 2.0 클라이언트 ID 생성 (Desktop app)
4. `credentials.json` 다운로드 후 프로젝트 루트에 저장
5. OAuth 동의 화면에서 테스트 사용자로 본인 이메일 추가

## 사용법

### 일일 뉴스레터 (전날 메일 기준)

```bash
python src/daily_newsletter.py
```

### 특정 날짜 지정

```bash
python src/daily_newsletter.py --date 2026-01-15
```

### 팩트체크 없이 실행

```bash
python src/daily_newsletter.py --no-factcheck
```

### 최대 토픽 수 지정

```bash
python src/daily_newsletter.py --max-topics 5
```

### 기본 파이프라인 (최근 2일)

```bash
python src/main.py
```

## 설정

`config/settings.yaml`:

```yaml
keywords:
  - "LLM"
  - "Python"
  - "System Design"
  - "React"
  - "Startup"
  - "Productivity"

gemini:
  model: "gemini-2.0-flash"

email:
  sender: "me"
  subject_prefix: "[Daily Research] "

search:
  max_results: 2
  excluded_domains:
    - "medium.com"
    - "youtube.com"
```

## 프로젝트 구조

```
MailToNewsLetter/
├── src/
│   ├── main.py              # 기본 파이프라인
│   ├── daily_newsletter.py  # 일일 뉴스레터 (팩트체크 포함)
│   ├── gmail_client.py      # Gmail API 클라이언트
│   ├── parser.py            # Medium 이메일 파서
│   ├── search_engine.py     # DuckDuckGo 검색
│   ├── scraper.py           # 콘텐츠 스크래퍼
│   ├── llm_processor.py     # Gemini AI 처리
│   └── fact_checker.py      # 팩트체크 모듈
├── templates/
│   └── newsletter_template.html
├── config/
│   └── settings.yaml
├── .env.example
├── requirements.txt
└── README.md
```

## 뉴스레터 출력 예시

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📰 Rate Limiting 시스템 설계
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[AI 요약 내용...]

📚 Reference Sources:
• GeeksforGeeks - Rate Limiting Guide
• ByteByteGo - Design A Rate Limiter

🔍 Fact-Check Report
━━━━━━━━━━━━━━━━━━━━
Confidence: 85%
✓ Token Bucket 알고리즘 - verified
✓ Redis 활용 사례 - verified
⚠ 처리량 수치 - partially_verified
```

## API 키 발급 가이드

### Gemini API

1. [Google AI Studio](https://aistudio.google.com/) 접속
2. API Key 생성

### Google Custom Search API (팩트체크용)

1. [Google Cloud Console](https://console.cloud.google.com/) → Custom Search API 활성화
2. Credentials에서 API Key 생성
3. [Programmable Search Engine](https://programmablesearchengine.google.com/) → 검색 엔진 생성
4. Search Engine ID(cx) 복사

## 문제 해결

| 문제 | 해결 방법 |
|------|----------|
| `credentials.json` not found | Google Cloud Console에서 OAuth 클라이언트 ID 다운로드 |
| Gmail API Error | `token.json` 삭제 후 재인증 |
| No Medium Digest found | 받은편지함에 Medium Daily Digest 이메일 확인 |
| Gemini 429 Error | API 할당량 초과, 잠시 후 재시도 |
| 검색 결과 없음 | `ddgs` 패키지 업데이트: `pip install -U ddgs` |

## 라이선스

MIT License

## 기여

이슈 및 PR 환영합니다.
