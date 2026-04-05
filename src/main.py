"""
메인 실행 스크립트
python src/main.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# .env 로드 (로컬 실행 시)
load_dotenv(Path(__file__).parent.parent / ".env")

# src 디렉토리를 import 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from collector import collect
from curator import score_and_summarize, select_top
from storage import save_daily
from publisher import publish


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[오류] ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("=" * 50)
    print("DAI 길드 뉴스 수집 시작")
    print("=" * 50)

    # 1단계: 수집
    print("\n[1/4] 뉴스 수집 중...")
    candidates = collect(hours=48)

    if not candidates:
        print("수집된 뉴스가 없습니다. 종료합니다.")
        sys.exit(0)

    # 2단계: Claude API 스코어링
    print(f"\n[2/4] Claude API로 {len(candidates)}개 기사 큐레이션 중...")
    scored = score_and_summarize(candidates, client)

    # 3단계: 최종 선별
    print("\n[3/4] 최종 기사 선별 중...")
    selected = select_top(scored, min_count=3, max_count=5, min_score=4)

    # 결과 출력
    print(f"\n{'=' * 50}")
    print(f"오늘의 DAI 길드 뉴스 ({len(selected)}개)")
    print("=" * 50)
    for i, a in enumerate(selected, 1):
        print(f"\n[{i}] [{a.get('category', '')}] {a['title']}")
        print(f"    출처: {a['source']} | 점수: {a.get('score', '-')}")
        print(f"    요약: {a.get('summary_ko', '')}")
        print(f"    링크: {a['link']}")

    # 4단계: 저장 + GitHub Pages 퍼블리시
    print("\n[4/4] 저장 및 페이지 생성 중...")
    save_daily(selected)
    publish()
    print("\n완료!")


if __name__ == "__main__":
    main()
