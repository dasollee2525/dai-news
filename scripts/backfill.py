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
        "date": "2026-04-04",
        "articles": [
            {
                "title": "How to Use ChatGPT for Exploratory Data Analysis",
                "link": "https://towardsdatascience.com/how-to-use-chatgpt-for-eda",
                "summary_ko": "ChatGPT를 활용해 데이터 탐색(EDA)을 자동화하는 방법을 소개합니다. pandas 데이터프레임을 ChatGPT에 설명하고 분석 방향을 제안받는 실용적인 워크플로우를 다룹니다.",
                "summary_raw": "A practical guide to using ChatGPT for exploratory data analysis.",
                "source": "Towards Data Science",
                "lang": "en",
                "region": "international",
                "score": 5,
                "category": "AI도구활용",
                "published_at": "2026-04-04T10:00:00+09:00",
                "reason": "데이터 분석가가 바로 쓸 수 있는 ChatGPT EDA 실전 가이드"
            },
            {
                "title": "Building a RAG Pipeline for Business Intelligence",
                "link": "https://towardsdatascience.com/rag-for-bi",
                "summary_ko": "RAG(검색 증강 생성) 파이프라인을 BI 환경에 적용하는 방법을 소개합니다. 내부 데이터베이스에 자연어 질의를 가능하게 하는 실용적인 아키텍처를 다룹니다.",
                "summary_raw": "Learn how to build a RAG pipeline for business intelligence use cases.",
                "source": "Towards Data Science",
                "lang": "en",
                "region": "international",
                "score": 5,
                "category": "LLM응용",
                "published_at": "2026-04-04T09:00:00+09:00",
                "reason": "분석가 대상 RAG 실무 적용 사례"
            },
            {
                "title": "AI 기반 데이터 분석 자동화 트렌드 2026",
                "link": "https://www.aitimes.com/news/ai-data-automation-2026",
                "summary_ko": "2026년 데이터 분석 자동화의 핵심 트렌드를 정리합니다. LLM 기반 코드 생성, 자동 리포팅, AI 대시보드가 분석 업무를 어떻게 바꾸는지 살펴봅니다.",
                "summary_raw": "AI 기반 데이터 분석 자동화의 최신 트렌드를 소개합니다.",
                "source": "AI타임스",
                "lang": "ko",
                "region": "domestic",
                "score": 4,
                "category": "AI트렌드",
                "published_at": "2026-04-04T08:00:00+09:00",
                "reason": "분석가 필수 AI 자동화 트렌드 정리"
            }
        ]
    },
    # 날짜를 추가하려면 위 형식으로 계속 추가하세요:
    # {
    #     "date": "2026-04-03",
    #     "articles": [ ... ]
    # },
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
