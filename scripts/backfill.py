"""
백필 스크립트 — 과거 날짜에 기사를 수동으로 추가합니다.

사용법:
    python scripts/backfill.py

BACKFILL_DATA 에 날짜와 기사 목록을 직접 작성하세요.
실행하면 data/daily/{date}.json 과 docs/{date}.html 이 생성됩니다.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 프로젝트 루트를 sys.path에 추가
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from storage import save_daily
from publisher import publish

KST = timezone(timedelta(hours=9))

# ──────────────────────────────────────────────
# 여기에 백필할 기사를 직접 입력하세요
# ──────────────────────────────────────────────
BACKFILL_DATA = [
    {
        "date": "2026-04-03",
        "articles": [
            {
                "title": "What Happens Now That AI is the First Analyst On Your Team?",
                "link": "https://towardsdatascience.com/what-happens-now-that-ai-is-the-first-analyst-on-your-team/",
                "summary_ko": "AI가 팀의 첫 번째 분석가 역할을 맡게 되면 기존 데이터 분석가의 역할은 어떻게 달라질까요? AI 자동화 시대에 분석가가 어떻게 적응하고 더 높은 가치를 만들어야 하는지를 실무 관점에서 논합니다.",
                "summary_raw": "AI is the first analyst on your team. What happens now?",
                "source": "Towards Data Science",
                "lang": "en",
                "region": "international",
                "score": 5,
                "category": "AI트렌드",
                "published_at": "2026-04-01T09:00:00+09:00",
                "reason": "데이터 분석가 커리어와 AI의 관계를 정면으로 다룬 필독 아티클"
            },
            {
                "title": "Turning 127 Million Data Points Into an Industry Report",
                "link": "https://towardsdatascience.com/turning-127-million-data-points-into-an-industry-report/",
                "summary_ko": "1억 2700만 개의 데이터 포인트를 데이터 랭글링, 세그멘테이션, 스토리텔링 기법으로 산업 보고서로 변환한 실무 경험을 공유합니다. 대용량 데이터를 인사이트로 바꾸는 전 과정을 다룹니다.",
                "summary_raw": "Turning 127 million data points into an industry report.",
                "source": "Towards Data Science",
                "lang": "en",
                "region": "international",
                "score": 5,
                "category": "데이터분석+AI",
                "published_at": "2026-03-31T09:00:00+09:00",
                "reason": "대규모 데이터 분석 → 리포트 변환 실전 사례"
            },
            {
                "title": "Zero Budget, Full Stack: Building with Only Free LLMs",
                "link": "https://www.kdnuggets.com/zero-budget-full-stack-building-with-only-free-llms",
                "summary_ko": "무료 LLM만으로 AI 기반 서비스를 풀스택으로 구축하는 방법을 전체 코드와 함께 안내합니다. 비용 없이 LLM을 업무에 활용하고 싶은 분석가에게 실용적인 가이드입니다.",
                "summary_raw": "Building a full-stack AI app using only free LLMs.",
                "source": "KDnuggets",
                "lang": "en",
                "region": "international",
                "score": 4,
                "category": "AI도구활용",
                "published_at": "2026-03-31T08:00:00+09:00",
                "reason": "무료 LLM 실무 활용 가이드"
            },
            {
                "title": "LLMOps in 2026: The 10 Tools Every Team Must Have",
                "link": "https://www.kdnuggets.com/llmops-in-2026-the-10-tools-every-team-must-have",
                "summary_ko": "2026년 LLM 기반 AI 시스템 운영에 필수적인 LLMOps 툴 10가지를 정리합니다. 분석 팀에서 LLM을 안정적으로 운영하고 싶다면 참고할 만한 도구 목록입니다.",
                "summary_raw": "The 10 LLMOps tools every team must have in 2026.",
                "source": "KDnuggets",
                "lang": "en",
                "region": "international",
                "score": 4,
                "category": "AI도구활용",
                "published_at": "2026-04-02T08:00:00+09:00",
                "reason": "LLM 운영 도구 실무 정리"
            }
        ]
    },
]
# ──────────────────────────────────────────────


def backfill():
    print(f"백필 시작: {len(BACKFILL_DATA)}개 날짜")

    for entry in BACKFILL_DATA:
        date_str = entry["date"]
        articles = entry["articles"]

        print(f"\n  [{date_str}] {len(articles)}개 기사 저장 중...")
        save_daily(articles, date_str)
        publish(date_str)
        print(f"  [{date_str}] 완료 ✅")

    print("\n백필 완료! git add data/ docs/ && git push 로 업로드하세요.")


if __name__ == "__main__":
    backfill()
