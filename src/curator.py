"""
OpenAI API를 활용한 2차 큐레이션 모듈
- 관련성 점수 1~5 스코어링
- 카테고리 분류
- 한국어 요약 생성
"""

import json
from openai import OpenAI

SYSTEM_PROMPT = """당신은 데이터 분석 AI 길드를 위한 뉴스 큐레이터입니다.

# 길드 소개
- 데이터 분석가들이 AI를 실무에 활용하는 방법을 연구하는 모임
- 구성원: 데이터 분석가, BI 개발자, 비즈니스 애널리스트
- 핵심 관심사: "AI + 데이터 분석의 결합", "분석가의 AI 실무 활용"

# 선정 원칙 (매우 중요)
아래 기준에 **모두** 해당하지 않으면 낮은 점수를 주세요.
선정 대상:
  - 데이터 분석 업무에 AI/LLM을 접목한 실사례 또는 튜토리얼
  - AI 도구(ChatGPT, Copilot, Claude 등)를 분석 업무에 활용하는 방법
  - 분석가를 위한 AI 기반 생산성 도구 소개
  - SQL/Python 분석 워크플로우에 AI를 통합하는 내용
  - 비즈니스 인사이트 도출에 AI를 활용하는 사례
  - 분석가가 알아야 할 LLM 응용 트렌드 (RAG, AI Agent 등)

탈락 대상 (다음 내용은 무조건 1~2점):
  - AI 모델 자체의 구조/훈련/벤치마크 소개 (분석가가 직접 활용 불가)
  - 딥러닝, 손실함수, 신경망 등 ML 이론 위주
  - Docker, 인프라, MLOps, 백엔드 개발자 대상 내용
  - AI 기업 뉴스, 투자, 정책, 사회적 이슈 (실무와 무관)
  - 일반적인 프로그래밍 튜토리얼 (AI 미포함)

# 점수 기준
5점: 데이터 분석가가 오늘 당장 업무에 적용 가능한 AI 활용법
4점: 분석가에게 유용한 AI 트렌드 또는 도구 (간접 활용 가능)
3점: 관련은 있으나 실무 적용이 어려운 내용
2점: AI 관련이나 분석가와 연관성 낮음
1점: 탈락 (선정 기준 미충족)

# 카테고리
- AI도구활용: ChatGPT, Copilot 등 AI 도구의 분석 실무 활용법
- 데이터분석+AI: 데이터 분석 워크플로우에 AI를 결합한 사례
- LLM응용: 분석 자동화, RAG, AI Agent 응용
- 생산성: AI 기반 분석 업무 자동화, 워크플로우 개선
- AI트렌드: 분석가가 반드시 알아야 할 AI 업계 동향"""


def score_and_summarize(articles: list[dict], client: OpenAI) -> list[dict]:
    """
    기사 목록을 OpenAI API로 스코어링 + 한국어 요약.
    API 비용 절약을 위해 배치로 처리.
    """
    if not articles:
        return []

    results = []
    batch_size = 10

    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        batch_results = _process_batch(batch, client)
        results.extend(batch_results)

    return results


def _process_batch(batch: list[dict], client: OpenAI) -> list[dict]:
    """배치 단위로 OpenAI API 호출"""

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

선정 원칙을 엄격하게 적용하세요. "데이터 분석 + AI 결합"이 핵심이며,
AI 이론, 인프라, 기업 뉴스는 낮은 점수를 주세요.

각 기사에 대해 아래 JSON 형식으로 응답하세요. 반드시 유효한 JSON 배열만 반환하세요:
[
  {{
    "index": 0,
    "score": 4,
    "category": "AI도구활용",
    "summary_ko": "데이터 분석가 관점에서 2~3문장 요약. 실무에 어떻게 활용할 수 있는지 포함.",
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

        # JSON 코드블록 제거
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        parsed = json.loads(raw)
        if isinstance(parsed, list):
            scored = parsed
        else:
            scored = next(v for v in parsed.values() if isinstance(v, list))

        enriched = []
        for item in scored:
            idx = item["index"]
            if idx < len(batch):
                article = batch[idx].copy()
                article["score"] = item.get("score", 0)
                article["category"] = item.get("category", "기타")
                article["summary_ko"] = item.get("summary_ko", "")
                article["reason"] = item.get("reason", "")
                enriched.append(article)

        return enriched

    except Exception as e:
        print(f"  [경고] OpenAI API 배치 처리 실패: {e}")
        return [{**a, "score": 0, "category": "기타", "summary_ko": "", "reason": "처리 실패"} for a in batch]


def select_top(scored_articles: list[dict], min_count: int = 3, max_count: int = 5, min_score: int = 4) -> list[dict]:
    """
    스코어 기반으로 최종 기사 선별.
    - min_score 이상인 것만
    - 카테고리 중복 최대 2개
    - min_count ~ max_count 개 선택
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

    # min_count 미달 시 점수 기준 완화해서 채우기
    if len(selected) < min_count:
        remaining = [a for a in scored_articles if a not in selected]
        remaining.sort(key=lambda x: x["score"], reverse=True)
        for article in remaining:
            if len(selected) >= min_count:
                break
            selected.append(article)

    return selected
