# DAI 길드 뉴스 수집 시스템

데이터 분석 AI 길드를 위한 일일 뉴스 자동 큐레이션 시스템.

## 구조

```
DAI_NEWS/
├── config/
│   └── sources.json    # ✏️ 소스 추가/수정/비활성화는 여기서
├── src/
│   ├── main.py         # 메인 실행 스크립트
│   ├── collector.py    # RSS 수집 + 1차 키워드 필터
│   ├── curator.py      # Claude API 스코어링 + 한국어 요약
│   ├── storage.py      # JSON 저장
│   ├── publisher.py    # GitHub Pages 마크다운 생성
│   └── sources.py      # sources.json 로더 (수정 불필요)
├── data/
│   ├── daily/          # YYYY-MM-DD.json (일별 결과)
│   └── archive/        # index.json (날짜별 인덱스)
├── docs/               # GitHub Pages 서빙 루트
│   ├── index.md        # 최신 뉴스 (항상 덮어씀)
│   ├── YYYY-MM-DD.md   # 날짜별 아카이브 페이지
│   ├── archive.md      # 전체 날짜 목록
│   └── _config.yml     # Jekyll 테마 설정
├── .github/
│   └── workflows/
│       └── daily_news.yml  # GitHub Actions 스케줄
├── requirements.txt
└── .env.example
```

## 뉴스 소스 관리

소스 추가/수정/비활성화는 **`config/sources.json`** 만 편집하면 됩니다. 코드 변경 불필요.

### 소스 추가
```json
{
  "name": "GeekNews",
  "url": "https://feeds.feedburner.com/geeknews-feed",
  "lang": "ko",
  "region": "domestic",
  "active": true
}
```

### 소스 비활성화 (삭제 없이 끄기)
```json
{ "name": "블로터", "active": false }
```

### 키워드 추가/제거
`filters.include_keywords` 또는 `filters.exclude_keywords` 배열을 직접 편집

### 현재 소스 목록
- **국내 (30~40%)**: 블로터, AI타임스, 동아사이언스
- **해외 (60~70%)**: Towards Data Science, HuggingFace Blog, The Batch, MIT Tech Review, Analytics Vidhya, KDnuggets

## 큐레이션 흐름

```
RSS 수집 (하루 50~100개)
    ↓
1차 키워드 필터 (포함/제외 키워드)
    ↓
Claude API 스코어링 (1~5점) + 한국어 요약
    ↓
최종 선별 (4점 이상, 카테고리 중복 제한, 3~5개)
    ↓
data/daily/YYYY-MM-DD.json 저장
    ↓
docs/ 마크다운 생성 → GitHub Pages 웹사이트 자동 반영
```

## 로컬 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 입력

# 3. 실행
python src/main.py
```

## GitHub Actions + Pages 설정

### 1. API 키 등록
GitHub 저장소 `Settings > Secrets and variables > Actions`에서 `ANTHROPIC_API_KEY` 추가

### 2. GitHub Pages 활성화
GitHub 저장소 `Settings > Pages`에서
- Source: `Deploy from a branch`
- Branch: `main` / `docs` 폴더 선택 후 Save

### 3. 완료
- 매일 오전 7시(KST) 자동 실행 → `docs/` 자동 업데이트 → 웹사이트 반영
- 웹사이트 주소: `https://[유저명].github.io/[레포명]/`

수동 실행: Actions 탭 → `DAI 길드 일일 뉴스 수집` → `Run workflow`

## 출력 형식 (data/daily/YYYY-MM-DD.json)

```json
{
  "date": "2024-01-15",
  "generated_at": "2024-01-15T07:05:12+09:00",
  "count": 4,
  "articles": [
    {
      "title": "기사 제목",
      "link": "https://...",
      "source": "Towards Data Science",
      "lang": "en",
      "region": "international",
      "score": 5,
      "category": "AI도구활용",
      "summary_ko": "한국어 요약 2~3문장",
      "published_at": "2024-01-15T03:00:00+09:00"
    }
  ]
}
```
