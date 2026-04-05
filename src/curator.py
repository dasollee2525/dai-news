"""
Claude API를 활용한 2차 큐레이션 모듈
- 관련성 점수 1~5 스코어링
- 카테고리 분류
- 한국어 요약 생성
"""

import json
import anthropic

SYSTEM_PROMPT = """당신은 데이터 분석 AI 길드를 위한 뉴스 큐레이터입니다.

길드 소개:
- 데이터 분석가들이 모여 AI를 실무에 활용하는 방법을 연구하는 길드
- 구성원: 데이터 분석가, BI 개발자, 비즈니스 애널리스트 등
- 관심사: AI 도구 실무 활용, 데이터 분석 생산성 향상, LLM 응용 사례

평가 기준 (1~5점):
5점: 데이터 분석가의 AI 실무 활용에 직접적으로 도움 (도구 소개, 실사례, 튜토리얼)
4점: AI/데이터 분석 트렌드로 길드 활동에 참고할만한 내용
3점: 관련은 있지만 실무 적용이 간접적인 내용
2점: 약하게 관련된 일반 AI 뉴스
1점: 길드와 관련 없음

카테고리:
- AI도구활용: ChatGPT, Copilot 등 AI 도구의 실무 사용법
- 데이터분석: 분석 기법, 방법론, 인사이트 도출
- LLM응용: LLM을 활용한 데이터 분석 자동화, RAG 등
- 생산성: 업무 자동화, 워크플로우 개선
- AI트렌드: 분석가가 알아야 할 AI 업계 동향"""


def score_and_summarize(articles: list[dict], client: anthropic.Anthropic) -> list[dict]:
    """
    기사 목록을 Claude API로 스코어링 + 한국어 요약.
    API 비용 절약을 위해 배치로 처리.
    """
    if not articles:
        return []

    # 배치 처리 (한 번에 최대 10개)
    results = []
    batch_size = 10

    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        batch_results = _process_batch(batch, client)
        results.extend(batch_results)

    return results


def _process_batch(batch: list[dict], client: anthropic.Anthropic) -> list[dict]:
    """배치 단위로 Claude API 호출"""

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

각 기사에 대해 아래 JSON 형식으로 응답하세요. 반드시 유효한 JSON 배열만 반환하세요:
[
  {{
    "index": 0,
    "score": 4,
    "category": "AI도구활용",
    "summary_ko": "한국어 요약 2~3문장. 데이터 분석가 관점에서 왜 중요한지 포함.",
    "reason": "선정/탈락 이유 한 줄"
  }},
  ...
]"""

    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = message.content[0].text.strip()

        # JSON 파싱
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        scored = json.loads(raw)

        # 원본 기사에 점수/요약 병합
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
        print(f"  [경고] Claude API 배치 처리 실패: {e}")
        # 실패한 배치는 score=0으로 반환
        return [{**a, "score": 0, "category": "기타", "summary_ko": "", "reason": "처리 실패"} for a in batch]


def select_top(scored_articles: list[dict], min_count: int = 3, max_count: int = 5, min_score: int = 4) -> list[dict]:
    """
    스코어 기반으로 최종 기사 선별.
    - min_score 이상인 것만
    - 카테고리 중복 최대 2개
    - min_count ~ max_count 개 선택
    """
    # 4점 이상 필터링 후 점수 내림차순 정렬
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
