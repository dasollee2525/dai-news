"""
OpenAI API를 활용한 2차 큐레이션 모듈
"""

import json
from openai import OpenAI

SYSTEM_PROMPT = """당신은 데이터 분석 AI 길드를 위한 뉴스 큐레이터입니다.

# 길드 소개
데이터 분석가들이 AI를 실무에 활용하는 방법을 연구하는 모임.
구성원: 데이터 분석가, BI 개발자, 비즈니스 애널리스트

# 핵심 선정 기준: 반드시 "데이터 분석 + AI의 결합"이어야 합니다

✅ 선정 대상 (4~5점):
- AI 도구(ChatGPT, Copilot, Claude 등)를 데이터 분석 업무에 활용하는 구체적 방법
- LLM으로 SQL 작성, 데이터 탐색(EDA), 리포트 자동화 등 분석 워크플로우 개선
- 분석가를 위한 AI 기반 생산성 도구 실사용 사례 또는 튜토리얼
- 비즈니스 인사이트 도출에 AI를 실제 활용한 사례
- RAG, AI Agent를 데이터 분석에 접목한 실용적 내용

❌ 탈락 대상 (1~2점, 아무리 유명해도 예외 없음):
- AI/ML 모델 이론, 구조, 학습 방법 (Loss function, Transformer, 신경망 등)
- Docker, Kubernetes, MLOps, 인프라, 백엔드 개발
- AI 기업 뉴스, 신모델 출시, 투자, 정책, 사회 이슈
- 데이터 분석이 없는 순수 프로그래밍 튜토리얼
- 분석가가 직접 사용할 수 없는 연구자/개발자 대상 콘텐츠

# 점수 기준 (엄격하게 적용)
5점: 데이터 분석가가 오늘 당장 업무에 쓸 수 있는 AI 활용 방법 (실사례/튜토리얼)
4점: 분석가에게 실질적으로 유용한 AI 도구 또는 트렌드
3점: 관련은 있으나 분석가가 직접 쓰기엔 간접적
2점: AI 관련이지만 분석 업무와 거의 무관
1점: 선정 기준 미충족, 탈락

4점 미만이면 반드시 낮은 점수를 주세요. 억지로 높이지 마세요.
오늘 수집된 기사 중 적합한 것이 없으면 모두 낮은 점수를 주어도 됩니다.

# 카테고리
- AI도구활용: ChatGPT, Copilot 등 AI 도구의 분석 실무 활용법
- 데이터분석+AI: 데이터 분석 워크플로우에 AI를 결합한 사례
- LLM응용: 분석 자동화, RAG, AI Agent 응용
- 생산성: AI 기반 분석 업무 자동화, 워크플로우 개선
- AI트렌드: 분석가가 반드시 알아야 할 AI 업계 동향"""


def score_and_summarize(articles: list[dict], client: OpenAI) -> list[dict]:
    if not articles:
        return []

    results = []
    batch_size = 10
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        results.extend(_process_batch(batch, client))
    return results


def _process_batch(batch: list[dict], client: OpenAI) -> list[dict]:
    articles_text = ""
    for idx, a in enumerate(batch):
        articles_text += f"""
[{idx}]
제목: {a['title']}
출처: {a['source']} ({a['region']})
원문 요약: {a['summary_raw'][:300]}
---"""

    user_prompt = f"""다음 {len(batch)}개 기사를 평가해주세요.

{articles_text}

핵심 판단 기준: "데이터 분석가가 AI를 실무에 쓰는 방법"에 해당하지 않으면 낮은 점수를 주세요.
기사 중 적합한 것이 없으면 전부 낮은 점수를 줘도 됩니다. 억지로 올리지 마세요.

JSON 배열만 반환하세요:
[
  {{
    "index": 0,
    "score": 4,
    "category": "AI도구활용",
    "summary_ko": "데이터 분석가 관점 2~3문장. 실무에 어떻게 쓸 수 있는지 포함.",
    "reason": "선정/탈락 이유 한 줄"
  }}
]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=2048,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        parsed = json.loads(raw)
        scored = parsed if isinstance(parsed, list) else next(v for v in parsed.values() if isinstance(v, list))

        enriched = []
        for item in scored:
            idx = item["index"]
            if idx < len(batch):
                article = batch[idx].copy()
                article["score"]       = item.get("score", 0)
                article["category"]    = item.get("category", "기타")
                article["summary_ko"]  = item.get("summary_ko", "")
                article["reason"]      = item.get("reason", "")
                enriched.append(article)
        return enriched

    except Exception as e:
        print(f"  [경고] OpenAI API 배치 처리 실패: {e}")
        return [{**a, "score": 0, "category": "기타", "summary_ko": "", "reason": "처리 실패"} for a in batch]


def select_top(
    scored_articles: list[dict],
    min_count: int = 3,
    max_count: int = 5,
    min_score: int = 4,
) -> list[dict]:
    """
    4점 이상만 선정. 기준 충족하는 기사가 없으면 빈 리스트 반환.
    min_count 미달이어도 억지로 채우지 않음.
    """
    qualified = [a for a in scored_articles if a.get("score", 0) >= min_score]
    qualified.sort(key=lambda x: x["score"], reverse=True)

    selected = []
    category_count: dict[str, int] = {}

    for article in qualified:
        if len(selected) >= max_count:
            break
        cat = article.get("category", "기타")
        if category_count.get(cat, 0) >= 2:
            continue
        selected.append(article)
        category_count[cat] = category_count.get(cat, 0) + 1

    if len(selected) < min_count:
        print(f"  [안내] 기준 충족 기사 {len(selected)}개 — 오늘은 적합한 뉴스가 부족합니다.")

    return selected
